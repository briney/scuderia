"""Final products survive without operational inputs; synthetic sources only."""
import copy
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

import portable_articles as pa
from test_article_corrections import synthetic, FakeRclone
import final_products as fp


class FinalProducts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT'])
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path, self.manifest = synthetic(self.root)
        mapping = pa.local_sources(self.path)
        for key, role, data in [
            ('job/request-wire.json', 'enrichment-job', b'x' * 100000),
            ('package/documents/main/pages/p0002/native-text.json', 'source-package', b'[{"id":"line-2","text":"Text without figures","bbox":[0,0,1,1]}]'),
            ('retention/data.csv', 'source-original', b'a,b\n1,2\n'),
            ('retention/duplicate.pdf', 'source-original', (self.root/'source/main-original.pdf').read_bytes()),
        ]:
            local = self.root/'source'/key.replace('/', '-')
            local.write_bytes(data)
            self.manifest['files'].append(pa.file_record(role, key, local))
            if role.startswith('enrichment-'):
                self.manifest['common_dependencies'].append(key)
            mapping[key] = dict(root=str(local.parent), path=local.name)
        self.manifest['total_objects'] = len(self.manifest['files'])
        self.path.write_text(json.dumps(self.manifest))
        (self.path.parent/'local-map.json').write_text(json.dumps(dict(
            schema='portable-article-local-map-v2', manifest_sha256=pa.sha(self.path), sources=mapping)))

    def test_final_sources_text_crops_and_results_survive_deleted_job(self):
        view = dict(element_id='main::table-1', source_sha256=self.manifest['documents'][0]['source_sha256'],
                    outcome=dict(record=dict(cells=[dict(raw_value='1.2', units='mg')],filename='package/main/crop.png')),
                    findings=[dict(id='f1', status='unresolved', reason='Native and raster values disagree', resolutions=[])], coverage=[])
        exported = dict(elements=[view], profile=dict(model='synthetic'), assessment=dict(source_limitations=['Figure interpretation failed']), fixture=True)
        out = self.root/'final'
        m = fp.build(self.path, out, exports=[exported])
        self.assertEqual(m['schema'], pa.FINAL_SCHEMA)
        self.assertEqual(len(m['files']), len({f['sha256'] for f in m['files']}))
        self.assertFalse(any('request-wire' in f['key'] for f in m['files']))
        self.assertEqual(len(m['source_documents']), 4)  # two PDF identities, CSV, duplicate PDF identity
        paths = pa.verify_local(out/'manifest.json')[1]
        self.assertTrue(any(b'Text without figures' in p.read_bytes() for p in paths.values()))
        products = pa.load(paths[m['products_key']])
        self.assertEqual(products['elements'][0]['outcome'], view['outcome'])
        self.assertEqual(products['source_limitations'], ['Figure interpretation failed'])
        shutil.rmtree(self.root/'source'); shutil.rmtree(self.path.parent)
        self.assertEqual(fp.verify(out/'manifest.json')['article'], self.manifest['article'])
        fake = FakeRclone(); receipt = pa.publish(out/'manifest.json', 'fake', 'bucket', 'gate', runner=fake)
        pa.restore_remote(receipt['manifest_key'], receipt['manifest_sha256'], self.root/'restored',
                          remote='fake', bucket='bucket', prefix='gate', article_key=m['article_key'], runner=fake)
        fp.verify(self.root/'restored/manifest.json')
        paths[m['documents'][0]['raw_key']].write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'corrupt'):
            fp.verify(out/'manifest.json')

    def test_frozen_refresh_rejects_changed_qualifications(self):
        work = self.root/'work'; (work/'export').mkdir(parents=True)
        exported = dict(elements=[])
        pa.save(work/'export/handoff.json', exported)
        import article_enrichment as ae
        ae._seal_file(work/'enrichment/prepared.json', dict(prepared_at='2026-09-25T12:00:00Z', code={}))
        plan = dict(page_path=None)
        original = [dict(reason='Table values disagree', scope='table-1')]
        fp.prepare_refresh(work, plan, self.path, exported, original)
        fp.prepare_refresh(work, plan, self.path, exported)  # publication reuses the frozen input
        with self.assertRaisesRegex(ValueError, 'final-products-qualifications-changed'):
            fp.prepare_refresh(work, plan, self.path, exported, [])

    def test_full_refresh_preserves_uncited_prior_correction(self):
        import article_enrichment as ae
        old = dict(element_id='main::table-1', source_sha256=self.manifest['documents'][0]['source_sha256'],
                   outcome=dict(record='obsolete'), findings=[dict(id='human',status='unresolved',reason='Value mismatch',
                   resolutions=[dict(proposed='1.2', reviewer='Scientist')])])
        prior = self.root/'prior'
        fp.build(self.path, prior, exports=[dict(elements=[old])])
        work = self.root/'refresh'; (work/'export').mkdir(parents=True)
        exported = dict(elements=[dict(old, outcome=dict(record='current'), findings=[])])
        pa.save(work/'export/handoff.json', exported)
        ae._seal_file(work/'enrichment/prepared.json', dict(prepared_at='2026-09-26T12:00:00Z', code={}))
        final = fp.prepare_refresh(work, dict(page_path=None,source_archive=str(prior/'manifest.json')),
                                   self.path, exported)
        products = pa.load(work/'final-products'/final['products_key'])
        self.assertEqual(products['elements'][0]['outcome']['record'], 'current')
        self.assertTrue(any(isinstance(q.get('metadata'),dict) and q['metadata'].get('resolutions')==old['findings'][0]['resolutions'] for q in products['qualifications']))
        self.assertEqual(products['elements'][0]['provenance']['processing']['prepared_at'], '2026-09-26T12:00:00Z')

    def test_wrong_source_result_rejected_before_output(self):
        out = self.root/'bad'
        with self.assertRaisesRegex(ValueError, 'result-source-binding'):
            fp.build(self.path, out, exports=[dict(elements=[dict(element_id='main::table-1',source_sha256='0'*64)])])
        self.assertFalse(out.exists())

    def test_second_finalization_does_not_accumulate_history(self):
        first = self.root/'first'; second = self.root/'second'
        fp.build(self.path, first)
        before = fp.verify(first/'manifest.json')
        fp.build(first/'manifest.json', second)
        after = fp.verify(second/'manifest.json')
        self.assertEqual({f['sha256'] for f in before['files']}, {f['sha256'] for f in after['files']})
        self.assertEqual(before['source_documents'], after['source_documents'])

    def test_refresh_publication_verifies_without_replay_tree(self):
        from test_reenrich import ReenrichTests, candidate
        import reenrich as rr
        fixture = ReenrichTests('runTest'); fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.final_products = True
        fixture.ready()
        rr.candidate_import(fixture.work, candidate(fixture.work, fixture.base))
        rr.apply(fixture.work, authorize=True)
        fake = FakeRclone(); rr.publish(fixture.work, 'fake', 'bucket', 'gate', runner=fake)
        receipt = pa.load(fixture.work/'completion.json')
        archive = fixture.work/'archive/manifest.json'
        self.assertEqual(pa.load(archive)['schema'], pa.FINAL_SCHEMA)
        finalized = pa.load(archive)
        products = pa.load(archive.parent/finalized['products_key'])
        prepared = pa.load(fixture.work/'enrichment/prepared.json')
        self.assertEqual(products['elements'][0]['provenance']['processing']['prepared_at'], prepared['prepared_at'])
        restored = fixture.base/'final-restored'
        pa.restore(archive, restored)
        saved_receipt = fixture.base/'saved-completion.json'; pa.save(saved_receipt, receipt)
        shutil.rmtree(fixture.work); shutil.rmtree(fixture.base/'source')
        rr.verify_completion(saved_receipt, restored/'manifest.json', manifest_key=receipt['publication']['manifest_key'],
                             manifest_sha256=receipt['publication']['manifest_sha256'], article_key=fixture.m['article_key'], page=fixture.page)
        register = rr.read_register(fixture.page.read_text())
        self.assertEqual(register['schema'], 'portable-page-qualification-register-v4')
        self.assertTrue(register['qualifications'])

    def test_final_package_requires_fresh_extraction_before_reenrichment(self):
        import reenrich as rr
        out = self.root/'final'
        fp.build(self.path, out)
        plan = rr.plan(rr.Request('synthetic'), manifest=out/'manifest.json', work_root=self.root/'new-run', fixture=True)
        self.assertIsNone(plan['manifest'])
        self.assertEqual(plan['source_archive'], str(out/'manifest.json'))
        self.assertEqual(rr.execute(work_root=self.root/'new-run')['next_step'], 'adopt')
        with self.assertRaises(ValueError):
            rr.advance(self.root/'new-run', 'prepare')
