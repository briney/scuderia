"""Archive tests built from real retained acquisition and accepted extraction.

The supplied donor is READ ONLY. Every changed file belongs to this test's
new scratch directory; historical embedded paths are never followed for writes.
"""
import copy
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

import portable_articles as pa
import source_package as sp
from test_article_corrections import FakeRclone


def real_archive(base):
    donor=Path(os.environ['PORTABLE_ARTICLES_DONOR'])
    donor_manifest=pa.load(donor/'manifest.json')
    inputs=base/'inputs'; inputs.mkdir()
    article=dict(slug='portable-fixture',title='Synthetic identity for offline byte-preservation tests',doi=None,pmid=None,version='fixture-v1')
    files=[]; bindings={}
    for i,doc in enumerate(donor_manifest['documents']):
        source=inputs/('source-'+str(i)+'.pdf'); shutil.copyfile(donor/doc['raw'],source)
        ident='source-'+str(i); role='manuscript' if i==0 else 'supplement'
        files.append(dict(id=ident,path=str(source),sha256=pa.sha(source),filename=source.name,role=role,format='pdf',
            source_url='https://example.invalid/source',discovery_url='https://example.invalid/article',article_slug=article['slug'],
            identity_verification=dict(status='operator-verified',basis='Explicit synthetic fixture label on copied donor bytes; never a scientific assertion.')))
        bindings[doc['identity']]=ident
    body=inputs/'body.txt'; body.write_text('Synthetic body, not scientific evidence.')
    files.append(dict(id='body',path=str(body),sha256=pa.sha(body),filename='body.txt',role='body',format='other',
        source_url='https://example.invalid/body',discovery_url='https://example.invalid/article',article_slug=article['slug'],
        identity_verification=dict(status='operator-verified',basis='Synthetic fixture body.')))
    attachments=[dict(id=f['id'],observed_link=f['source_url'],filename=f['filename'],status='retrieved',file_id=f['id'])
                 for f in files if f['role']=='supplement']
    value=dict(schema='acquired-sources-v1',article=article,files=files,attempts=[],
        obligations=dict(body=dict(status='retrieved',file_ids=['body']),manuscript=dict(status='retrieved',file_ids=['source-0'])),
        attachments=dict(status='advertised' if attachments else 'none-listed',inspected_url='https://example.invalid/article',items=attachments))
    pa.save(base/'acquired.json',value)
    sp.prepare(base/'acquired.json',base/'retention','https://example.invalid/v1/chat/completions',120)
    shutil.copytree(donor,base/'package',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    m=pa.build_manifest(base/'retention'/'retention.json',base/'package',base/'archive',package_id='fixture-01',document_bindings=bindings)
    return base/'archive'/'manifest.json',m,bindings


class RealArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT'],prefix='real-archive-')
        cls.base=Path(cls.tmp.name)
        cls.path,cls.m,cls.bindings=real_archive(cls.base)
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def directory(self):
        t=tempfile.TemporaryDirectory(dir=self.base,prefix='test-'); self.addCleanup(t.cleanup); return Path(t.name)
    def test_real_manifest_retains_source_bindings_and_identity(self):
        m,paths=pa.verify_local(self.path)
        self.assertIn('retention/retention.json',paths)
        self.assertTrue(m['elements'])
        self.assertNotIn('sources',m)
        for d in m['documents']:
            original=next(r for r in m['files'] if r.get('binds',{}).get('source_id')==d['source_id'])
            self.assertEqual(original['sha256'],d['source_sha256'])
        self.assertIn('attempts',[r['kind'] for r in m['dispositions']])
    def test_full_restore_all_bytes(self):
        root=self.directory(); result=pa.restore(self.path,root/'restored')
        self.assertEqual(result['completed'],'full-package'); self.assertEqual(result['restored_count'],self.m['total_objects'])
        pa.verify_local(root/'restored'/'manifest.json')
    def test_selected_restore_native_caption_context(self):
        root=self.directory(); e=self.m['elements'][0]
        result=pa.restore(self.path,root/'selected',elements=[e['element_id']])
        self.assertLess(result['restored_count'],self.m['total_objects'])
        for cap in e['evidence']['captions']: self.assertIn(cap['crop'],result['restored'])
        for key in e['context']['native_text_keys']: self.assertIn(key,result['restored'])
        pa.consume(root/'selected'/'manifest.json',[e['element_id']])
    def test_publish_reuse_readback_and_manifest_last(self):
        fake=FakeRclone(); result=pa.publish(self.path,'fake','bucket','gate',runner=fake)
        self.assertEqual(result['objects'],self.m['total_objects'])
        uploads=[c for c in fake.calls if c[1]=='copyto']; self.assertIn('/manifests/',uploads[-1][3])
        self.assertTrue(all('--immutable' in c and '--ignore-existing' in c for c in uploads))
        result=pa.publish(self.path,'fake','bucket','gate',runner=fake); self.assertEqual(result['uploaded'],0)
    def test_corrupt_remote_manifest(self):
        fake=FakeRclone(); pub=pa.publish(self.path,'fake','bucket','gate',runner=fake)
        fake.store[pub['manifest_key']]+=b'x'; root=self.directory()
        with self.assertRaises(ValueError): pa.restore_remote(pub['manifest_key'],pub['manifest_sha256'],root/'bad',
            remote='fake',bucket='bucket',prefix='gate',article_key=self.m['article_key'],runner=fake)
        self.assertFalse((root/'bad').exists())
    def test_wrong_trusted_prefix_rejected(self):
        fake=FakeRclone(); root=self.directory()
        with self.assertRaises(ValueError): pa.restore_remote('untrusted/manifests/'+'0'*64+'.json','0'*64,root/'bad',
            remote='fake',bucket='bucket',prefix='gate',article_key=self.m['article_key'],runner=fake)
        self.assertEqual(fake.calls,[])
    def test_interrupted_publish_never_announces(self):
        fake=FakeRclone(); fake.fail_after=2
        with self.assertRaisesRegex(ValueError,'interruption'): pa.publish(self.path,'fake','bucket','gate',runner=fake)
        self.assertFalse(any('/manifests/' in k for k in fake.store))
    def test_empty_unknown_selection_refused(self):
        root=self.directory()
        for elements in ([],['missing-element']):
            with self.assertRaises(ValueError): pa.restore(self.path,root/'bad',elements=elements)
    def test_missing_body_and_supplement_preserve_partial_source_readiness(self):
        root=self.directory()
        acquired=pa.load(self.base/'acquired.json')
        acquired['files']=[f for f in acquired['files'] if f['role']!='body']
        acquired['obligations']['body']=dict(status='missing',attempt_ids=[],disposition='Redundant body endpoint deferred; manuscript retained.')
        acquired['attachments']['status']='advertised'
        acquired['attachments']['items'].append(dict(id='unavailable',status='missing',attempt_ids=[],
            disposition='Explicitly deferred in this offline test.',filename='supplement.csv',observed_link='https://example.invalid/supplement'))
        pa.save(root/'acquired.json',acquired)
        sp.prepare(root/'acquired.json',root/'retention','https://example.invalid/v1/chat/completions',120)
        from pdf_source_package import preparation
        preparation.prepare(root/'retention/scope.json',root/'full-package')
        m=pa.build_manifest(root/'retention/retention.json',root/'full-package',root/'archive',package_id='partial-source')
        self.assertFalse(m['source_status']['complete'])
        self.assertIn('acquisition-body-missing',m['source_status']['holds'])
        self.assertIn('advertised-attachments-missing',m['source_status']['holds'])
        self.assertNotIn('acquisition-body-missing',m['source_status']['readiness']['holds'])
        self.assertEqual(pa.verify_source(root/'archive/manifest.json'),m['source_status'])
        restored=root/'restored'
        pa.restore(root/'archive/manifest.json',restored)
        self.assertEqual(pa.verify_source(restored/'manifest.json'),m['source_status'])
        # Real retained bytes, offline preparation/review only: no model POSTs.
        import reenrich as rr
        import article_enrichment as ae
        from test_reenrich import reviewer, fixture_profile
        from article_runtime import digest
        work=root/'refresh'; manifest=restored/'manifest.json'
        rr.plan(rr.Request(m['article']['slug']),manifest=manifest,work_root=work,model_profile=fixture_profile())
        rr.advance(work,'prepare'); rr.advance(work,'review-create')
        packet=pa.load(work/'review/packet.json')
        prepared=pa.load(work/'enrichment/prepared.json')
        _,paths=pa.verify_local(manifest)
        source=next(f for f in m['files'] if f['key'].endswith('native-text.txt') and paths[f['key']].read_text().strip())
        pending={r['id']:'Visual requests deliberately deferred in offline verification.' for r in prepared['requests']}
        pending.update({key:'Remaining extraction explicitly deferred; native evidence reviewed.' for key in m['source_status']['readiness']['pending']})
        assessment=dict(usable_evidence=True,reason='Native manuscript text is available despite missing acquisition representations.',
                        source_refs=[{k:source[k] for k in ('key','sha256')}],unattempted=pending,
                        source_limitations=['Advertised supplement unavailable in this synthetic acquisition record.'])
        pa.save(root/'review.json',dict(schema='contextual-review-v2',packet_sha256=digest(packet),reviewer=reviewer(),
                findings=[],coverage=[],resolutions=[],assessment=assessment))
        rr.advance(work,'review-import',submission=root/'review.json'); rr.advance(work,'export')
        exported=pa.load(work/'export/handoff.json')
        self.assertTrue(rr.page_ready(exported))
        self.assertFalse(exported['source_status']['complete'])
        self.assertEqual(exported['assessment']['source_limitations'],assessment['source_limitations'])
        self.assertFalse((work/'enrichment/execution-start.json').exists())

        # The initial-ingest adapter must reach the same result with real receipts.
        import sys
        from pdf_source_package import launcher as source_launcher
        from qualified_enrichment import runtime, reviews, launcher
        scripts=Path(sp.__file__).parent
        result=source_launcher.launch(dict(operation='summary',package_dir=str(root/'full-package'),
            output_dir=str(root/'summary'),attempt_dir=str(root/'summary-attempt'),offline=True),
            source_launcher.Deployment(scripts,Path(sys.executable)))
        self.assertTrue(result['success'])
        source_handoff=sp.build_handoff(root/'retention/retention.json',root/'full-package',root/'summary-attempt/result.json',scripts)
        handoff=root/'source-handoff'; handoff.mkdir()
        pa.save(handoff/'handoff.json',source_handoff); (handoff/'summary.txt').write_text(source_handoff['summary'])
        self.assertEqual(sp.verify_handoff(handoff/'handoff.json',scripts),source_handoff)
        archive_with_reports=root/'archive-with-reports'
        report_manifest=pa.build_manifest(root/'retention/retention.json',root/'full-package',archive_with_reports,
                                         package_id='source-reports',handoff_dir=handoff)
        reports=[f for f in report_manifest['files'] if f['key'].startswith('source-report/')]
        self.assertTrue(reports)
        self.assertTrue(all(f['role']=='source-package' and f['key'] not in report_manifest['common_dependencies'] for f in reports))
        with self.assertRaisesRegex(ValueError,'requires enriched'):
            sp.verify_handoff(handoff/'handoff.json',scripts,require_enriched=True)
        runtime.prepare(handoff/'handoff.json',root/'native-job',scripts)
        review=root/'native-review'; reviews.create(root/'native-job','qualified-job',review)
        packet_path=root/'native-packet.json'; packet=reviews.packet(review,[],packet_path)
        dossier=pa.load(review/'dossier.json')
        native_manifest=root/'native-job/source/manifest.json'
        nm,npaths=pa.verify_local(native_manifest)
        src=next(f for f in nm['files'] if f['key'].endswith('native-text.txt') and npaths[f['key']].read_text().strip())
        native_assessment=dict(assessment,source_refs=[{k:src[k] for k in ('key','sha256')}],
            unattempted={key:'Explicitly deferred; retained native evidence reviewed.' for key in dossier['snapshot']['source_readiness']['pending']})
        pa.save(root/'native-input.json',dict(schema='contextual-review-v2',packet_sha256=digest(packet),reviewer=reviewer(),
                findings=[],coverage=[],resolutions=[],assessment=native_assessment))
        reviews.import_review(review,packet_path,root/'native-input.json')
        receipt=launcher.launch(dict(operation='export',review_root=str(review),output=str(root/'native-export'),
            attempt_dir=str(root/'native-export-attempt'),offline=True),launcher.Deployment(scripts,scripts,scripts,scripts,Path(sys.executable)))
        self.assertTrue(receipt['success'])
        final=sp.build_enriched_handoff(root/'retention/retention.json',root/'full-package',root/'summary-attempt/result.json',scripts,
            root/'native-export/handoff.json',root/'native-export-attempt/result.json',scripts,scripts)
        self.assertEqual(final['schema'],'source-package-handoff-v5')
        self.assertTrue(final['production_complete'])
        self.assertFalse(final['source_complete'])
        completed=root/'completed'; completed.mkdir()
        pa.save(completed/'handoff.json',final)
        (completed/'summary.txt').write_text(final['summary']); (completed/'qualifications.txt').write_text(final['qualifications'])
        self.assertEqual(sp.verify_handoff(completed/'handoff.json',scripts,integration=scripts,enrichment_root=scripts,require_enriched=True),final)
        # Durable initial-ingest verification no longer needs the runtime tree.
        import final_products as fp
        compact=root/'final-products'
        fm=fp.from_ingest(completed/'handoff.json',compact,method=scripts,integration=scripts,enrichment_root=scripts)
        self.assertEqual(fm['schema'],pa.FINAL_SCHEMA)
        self.assertFalse(fm['source_status']['complete'])
        self.assertTrue(fm['initial_ingest']['production_complete'])
        body='Source package: '+str(compact/'manifest.json')+'\n'+final['qualifications']
        fp.verify_ingest(compact/'manifest.json',fm['article'],body)
        shutil.rmtree(root/'native-job'); shutil.rmtree(completed)
        fp.verify_ingest(compact/'manifest.json',fm['article'],body)


    def test_source_association_cannot_be_overridden(self):
        root=self.directory()
        wrong={k:'not-the-acquired-source' for k in self.bindings}
        with self.assertRaisesRegex(ValueError,'association'): pa.build_manifest(self.base/'retention'/'retention.json',self.base/'package',root/'bad',
            package_id='wrong',document_bindings=wrong)
        with self.assertRaisesRegex(ValueError,'identity'): pa.build_manifest(self.base/'retention'/'retention.json',self.base/'package',root/'bad',
            package_id='wrong',article=dict(slug='other'),document_bindings=self.bindings)
    def test_local_map_escape_refused(self):
        root=self.directory(); shutil.copyfile(self.path,root/'manifest.json')
        mapping=pa.load(self.path.parent/'local-map.json'); first=next(iter(mapping['sources']))
        mapping['sources'][first]['path']='/absolute/escape'
        pa.save(root/'local-map.json',mapping)
        with self.assertRaises(ValueError): pa.restore(root/'manifest.json',root/'bad')
        self.assertFalse((root/'bad').exists())

if __name__=='__main__': unittest.main(verbosity=2)
