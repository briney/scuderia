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

    def test_scoped_final_retains_unprocessed_originals_after_restore(self):
        m=self.manifest
        m['processing']=dict(policy='manuscript-only-v1',manuscript=dict(source_id='main', pages=[1,2], basis='Verified manuscript pages'))
        # The intermediate fixture already has retained bytes; only main is processed.
        other=m['documents'].pop()
        for row in m['files']:
            if row['key']==other['raw_key']: row['role']='source-original'
        m['elements']=[e for e in m['elements'] if e['document']=='main']
        m['native_text_keys']=[k for k in m['native_text_keys'] if '/supplement/' not in k]
        self.path.write_text(json.dumps(m))
        mapping=pa.load(self.path.parent/'local-map.json'); mapping['manifest_sha256']=pa.sha(self.path)
        (self.path.parent/'local-map.json').write_text(json.dumps(mapping))
        out=self.root/'scoped'; final=fp.build(self.path,out)
        self.assertEqual(final['schema'], 'portable-article-manifest-v5')
        self.assertEqual(final['processing'],m['processing'])
        self.assertEqual([d['identity'] for d in final['documents']], ['main'])
        originals={r['sha256'] for r in final['source_documents']}
        fake=FakeRclone(); receipt=pa.publish(out/'manifest.json','fake','bucket','gate',runner=fake)
        shutil.rmtree(self.root/'source'); shutil.rmtree(self.path.parent); shutil.rmtree(out)
        dest=self.root/'restored'
        pa.restore_remote(receipt['manifest_key'],receipt['manifest_sha256'],dest,
            remote='fake',bucket='bucket',prefix='gate',article_key=final['article_key'],runner=fake)
        restored=fp.verify(dest/'manifest.json')
        self.assertEqual({r['sha256'] for r in restored['source_documents']},originals)
        broken=copy.deepcopy(restored); broken['processing']['manuscript']['source_id']='missing'
        with self.assertRaises(ValueError): pa.validate_manifest(broken)
        del broken['processing']
        with self.assertRaises(ValueError): pa.validate_manifest(broken)

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

    def test_manuscript_refresh_preserves_prior_supplement_products(self):
        import article_enrichment as ae
        prior=self.root/'prior'
        view=dict(element_id='supplement::table-1',source_sha256=self.manifest['documents'][1]['source_sha256'],
                  outcome=dict(record=dict(cells=[dict(raw_value='007')])), findings=[])
        fp.build(self.path,prior,exports=[dict(elements=[view])])
        m=self.manifest
        m['processing']=dict(policy='manuscript-only-v1',manuscript=dict(source_id='main',pages=[1,2],basis='Verified boundary'))
        other=m['documents'].pop()
        for row in m['files']:
            if row['key']==other['raw_key']: row['role']='source-original'
        m['elements']=[e for e in m['elements'] if e['document']=='main']
        m['native_text_keys']=[k for k in m['native_text_keys'] if '/supplement/' not in k]
        self.path.write_text(json.dumps(m)); mapping=pa.load(self.path.parent/'local-map.json')
        mapping['manifest_sha256']=pa.sha(self.path); (self.path.parent/'local-map.json').write_text(json.dumps(mapping))
        work=self.root/'refresh'; (work/'export').mkdir(parents=True)
        exported=dict(elements=[]); pa.save(work/'export/handoff.json',exported)
        ae._seal_file(work/'enrichment/prepared.json',dict(prepared_at='2026-09-26T12:00:00Z',code={}))
        final=fp.prepare_refresh(work,dict(page_path=None,source_archive=str(prior/'manifest.json')), self.path,exported)
        products=pa.load(work/'final-products'/final['products_key'])
        self.assertEqual(products['elements'][0]['outcome'],view['outcome'])
        self.assertEqual(final['preserved_documents'],['supplement'])
        old=fp.verify(prior/'manifest.json')
        old_si=next(e for e in old['elements'] if e['document']=='supplement')
        new_si=next(e for e in final['elements'] if e['document']=='supplement')
        self.assertEqual(old_si['fragments'],new_si['fragments'])
        fp.verify(work/'final-products/manifest.json')

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
        self.assertEqual(pa.load(restored/'manifest.json')['completion']['timing'],receipt['timing'])
        self.assertEqual(receipt['timing']['counts']['successful'],1)
        self.assertIsNotNone(receipt['timing']['request_wall_seconds'])
        self.assertIsNone(rr.read_register(fixture.page.read_text()))
        register = receipt['page_register']
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

    def test_review_correction_preserves_outcomes_and_survives_refresh(self):
        old_finding=dict(id='false-empty',category='empty-table-extraction',status='unresolved',reason='All cells empty',resolutions=[])
        view=dict(element_id='main::table-1',source_sha256=self.manifest['documents'][0]['source_sha256'],
            outcome=dict(record=dict(cells=[dict(raw_value='007')])),findings=[old_finding])
        exported=dict(elements=[view],assessment=dict(source_limitations=['All cells empty','Unrelated caveat']))
        original=self.root/'original';fp.build(self.path,original,exports=[exported])
        manifest=original/'manifest.json';m=fp.verify(manifest);products=pa.load(original/m['products_key'])
        reviewer=dict(kind='orchestrator-import',identity='Synthetic reviewer',model=None,provider=None,check='Record inspection',timestamp='2026-01-01T00:00:00Z')
        evidence=dict(element_id='main::table-1',key=m['products_key'],sha256=next(f['sha256'] for f in m['files'] if f['key']==m['products_key']),pointer='/elements/0/outcome/record/cells')
        changes=[dict(target='/elements/0/findings/0',old_sha256=pa.digest(products['elements'][0]['findings'][0]),replacement=None,source_refs=[evidence]),
                 dict(target='/source_limitations/0',old_sha256=pa.digest('All cells empty'),replacement=None,source_refs=[evidence])]
        submission=dict(schema='article-review-correction-v1',manifest_sha256=pa.sha(manifest),reviewer=reviewer,reason='Values are populated',changes=changes)
        correction=self.root/'correction.json';pa.save(correction,submission)
        out=self.root/'corrected';new=fp.correct_review(manifest,correction,out)
        data=pa.load(out/new['products_key'])
        self.assertEqual(data['schema'],'article-scientific-products-v2')
        self.assertEqual(data['elements'][0]['outcome'],view['outcome'])
        self.assertEqual(data['elements'][0]['findings'],[])
        self.assertEqual(data['source_limitations'],['Unrelated caveat'])
        self.assertEqual(data['amendments'][0]['changes'][0]['original'],old_finding)
        again=self.root/'again';fresh=fp.build(out/'manifest.json',again,exports=[exported])
        reread=pa.load(again/fresh['products_key'])
        self.assertEqual(reread['elements'][0]['findings'],[])
        self.assertEqual(reread['source_limitations'],['Unrelated caveat'])
        self.assertEqual({s['sha256'] for s in new['source_documents']},{s['sha256'] for s in m['source_documents']})
        for bad in ('stale','outcome','evidence','attribution'):
            value=copy.deepcopy(submission)
            if bad=='stale':value['changes'][0]['old_sha256']='0'*64
            if bad=='outcome':value['changes'][0]['target']='/elements/0/outcome'
            if bad=='evidence':value['changes'][0]['source_refs'][0]['element_id']='supplement::table-1'
            if bad=='attribution':value['reviewer']['identity']=''
            path=self.root/(bad+'.json');pa.save(path,value)
            with self.assertRaises(ValueError):fp.correct_review(manifest,path,self.root/(bad+'-out'))
            self.assertFalse((self.root/(bad+'-out')).exists())

    def test_initial_timing_includes_current_source_and_fails_before_output(self):
        from unittest.mock import patch
        import article_enrichment as ae
        source=self.root/'source-run';source.mkdir()
        for phase in ('initial','classification','association'):
            pa.save(source/(phase+'-plan.json'),dict(requests=[]))
        job=self.root/'job';(job/'enrichment').mkdir(parents=True)
        ae._seal_file(job/'enrichment/prepared.json',dict(requests=[],profile={},fixture=True,code={},prepared_at='2026-01-01T00:00:00Z'))
        review=self.root/'review';review.mkdir();pa.save(review/'dossier.json',dict(snapshot=dict(path=str(job))))
        handoff=self.root/'handoff.json';pa.save(handoff,{})
        value=dict(schema='source-package-handoff-v5',package=str(source),production_complete=True,qualifications='',
            enrichment=dict(schema='qualified-enrichment-export-v2',review_root=str(review),manifest=str(self.path),elements=[],readiness={}))
        out=self.root/'timed'
        with patch('source_package.verify_handoff',return_value=value):
            with self.assertRaisesRegex(ValueError,'timing-attempt'):
                fp.from_ingest(handoff,out,method=self.root,integration=self.root,enrichment_root=self.root,source_attempts=[self.root/'missing'])
            self.assertFalse(out.exists())
            final=fp.from_ingest(handoff,out,method=self.root,integration=self.root,enrichment_root=self.root)
        phases=[phase['phase'] for attempt in final['initial_ingest']['timing']['attempts'] for phase in attempt['phases']]
        self.assertEqual(phases,['initial','classification','association','enrichment'])

    def test_initial_ingest_requires_verified_publication(self):
        from unittest.mock import patch
        out = self.root/'final'
        m = fp.build(self.path, out)
        manifest = out/'manifest.json'
        # Isolate the publication gate from the independently tested source gate.
        accepted = copy.deepcopy(m)
        accepted['source_status']['fixture'] = False
        accepted['initial_ingest'] = dict(production_complete=True,
            readiness=dict(page_ready=True, holds=[]), qualifications='Archived qualification; do not dump into Markdown.')
        receipt = self.root/'publication.json'
        with patch.object(fp, 'verify', return_value=accepted):
            with self.assertRaisesRegex(ValueError, 'publication-receipt-required'):
                fp.verify_ingest(manifest, m['article'], '')
            fp.verify_ingest(manifest, m['article'], '', require_publication=False)
            pub = pa.publish(manifest, 'fake', 'bucket', 'gate', runner=FakeRclone())
            pa.save(receipt, pub)
            with self.assertRaisesRegex(ValueError, 'offline-publication-not-production'):
                fp.verify_ingest(manifest, m['article'], '', publication_receipt=receipt)
            with patch.object(pa, '_run_rclone', FakeRclone()):
                receipt.unlink()
                fp.publish_ingest(manifest, receipt, 'fake', 'bucket', 'gate')
            fp.verify_ingest(manifest, m['article'], '', publication_receipt=receipt)
            saved = pa.load(receipt)
            for field in ('manifest_sha256', 'article_key'):
                receipt.write_text(json.dumps(dict(saved, **{field: '0'*64})))
                with self.assertRaises(ValueError):
                    fp.verify_ingest(manifest, m['article'], '', publication_receipt=receipt)
            receipt.write_text(json.dumps(dict(saved, receipts=saved['receipts'][:-1])))
            with self.assertRaisesRegex(ValueError, 'publication-readback-inventory'):
                fp.verify_ingest(manifest, m['article'], '', publication_receipt=receipt)

    def test_failed_initial_publication_does_not_create_receipt(self):
        from unittest.mock import patch
        out = self.root/'final'; m = fp.build(self.path, out)
        m['source_status']['fixture'] = False
        m['initial_ingest'] = dict(production_complete=True)
        receipt = self.root/'publication.json'
        failed = FakeRclone(); failed.fail_after = 1
        with patch.object(fp, 'verify', return_value=m), patch.object(pa, '_run_rclone', failed):
            with self.assertRaisesRegex(ValueError, 'injected-transfer-interruption'):
                fp.publish_ingest(out/'manifest.json', receipt, 'fake', 'bucket', 'gate')
        self.assertFalse(receipt.exists())

    def test_historical_embedded_register_receipt_still_verifies(self):
        from test_reenrich import ReenrichTests, candidate
        import reenrich as rr
        fixture = ReenrichTests('runTest'); fixture.setUp(); self.addCleanup(fixture.doCleanups)
        fixture.ready()
        rr.candidate_import(fixture.work, candidate(fixture.work, fixture.base))
        rr.apply(fixture.work, authorize=True)
        rr.publish(fixture.work, 'fake', 'bucket', 'gate', runner=FakeRclone())
        receipt = pa.load(fixture.work/'completion.json')
        archive = fixture.work/'archive/manifest.json'
        m = pa.load(archive); facts = m['completion']
        register = facts.pop('page_register'); facts.pop('page_register_location')
        fixture.page.write_text(rr.install_register(fixture.page.read_text(), register))
        facts['page_sha256'] = pa.sha(fixture.page)
        m['package_id'] = 'synthetic-historical-register'
        archive.write_text(json.dumps(m))
        mapping = pa.load(archive.parent/'local-map.json'); mapping['manifest_sha256'] = pa.sha(archive)
        (archive.parent/'local-map.json').write_text(json.dumps(mapping))
        receipt.pop('page_register'); receipt.pop('page_register_location'); receipt.update(facts)
        receipt['publication'] = pa.publish(archive, 'fake', 'bucket', 'gate', runner=FakeRclone())
        path = rr.page_receipt_path(fixture.page, facts['binding']); path.write_text(json.dumps(receipt))
        pub = receipt['publication']
        rr.verify_completion(path, archive, manifest_key=pub['manifest_key'], manifest_sha256=pub['manifest_sha256'],
                             article_key=m['article_key'], page=fixture.page)
        # A new candidate may migrate the old embedded register only with its evidence present.
        _, paths = pa.verify_local(archive)
        rr._register_archive(rr.read_register(fixture.page.read_text()), paths)

    def _rewrite_manifest(self, path, value):
        path.write_text(json.dumps(value))
        mapping=pa.load(path.parent/'local-map.json');mapping['manifest_sha256']=pa.sha(path)
        (path.parent/'local-map.json').write_text(json.dumps(mapping))

    def test_incomplete_preserved_supplement_does_not_block_current_scope(self):
        self.test_manuscript_refresh_preserves_prior_supplement_products()
        prior=self.root/'prior/manifest.json';m=pa.load(prior)
        supplement=next(d for d in m['documents'] if d['identity']=='supplement')
        supplement.update(complete=False,gaps=['Historical extraction failed'])
        m['source_status']['complete']=False;self._rewrite_manifest(prior,m);fp.verify(prior)
        out=self.root/'preserved-incomplete'
        final=fp._preserve_unprocessed(self.root/'refresh/current-final-products/manifest.json',prior,out)
        self.assertTrue(final['source_status']['complete'])
        old=next(d for d in final['documents'] if d['identity']=='supplement')
        self.assertFalse(old['complete']);self.assertEqual(old['gaps'],supplement['gaps'])
        fp.verify(out/'manifest.json')

    def test_compact_preserves_historical_document_roster(self):
        self.test_manuscript_refresh_preserves_prior_supplement_products()
        source=self.root/'refresh/final-products/manifest.json';out=self.root/'recompact'
        before=fp.verify(source);after=fp.build(source,out)
        self.assertEqual(after['preserved_documents'],before['preserved_documents'])
        self.assertEqual(after['documents'],before['documents']);fp.verify(out/'manifest.json')

    def test_correction_qualification_text_is_owner_scoped(self):
        self.test_review_correction_preserves_outcomes_and_survives_refresh()
        manifest=self.root/'original/manifest.json';m=pa.load(manifest)
        lines=['Element main::table-1; target : All cells empty',
               'Element supplement::table-1; target : All cells empty',
               'Source limitation: All cells empty in a separate unreadable table']
        m['initial_ingest']=dict(qualifications='\n'.join(lines));self._rewrite_manifest(manifest,m)
        request=pa.load(self.root/'correction.json');request['manifest_sha256']=pa.sha(manifest)
        request['changes']=request['changes'][:1];submission=self.root/'owner-correction.json';pa.save(submission,request)
        result=fp.correct_review(manifest,submission,self.root/'owner-corrected')
        self.assertEqual(result['initial_ingest']['qualifications'],'\n'.join(lines[1:]))
        self.assertEqual(result['initial_ingest']['recorded_qualifications'],'\n'.join(lines))

    def test_renamed_manuscript_is_not_preserved_as_supplement(self):
        self.test_manuscript_refresh_preserves_prior_supplement_products()
        prior=self.root/'prior/manifest.json';old=pa.load(prior)
        for source in old['source_documents']:
            if source['identity'] in ('main','supplement'):
                source['role']='manuscript' if source['identity']=='main' else 'supplement'
        self._rewrite_manifest(prior,old)
        current=self.root/'refresh/current-final-products/manifest.json'
        def rename(value):
            if isinstance(value,dict):return {k:rename(v) for k,v in value.items()}
            if isinstance(value,list):return [rename(v) for v in value]
            if isinstance(value,str):return 'renamed-main' if value=='main' else value.replace('main::','renamed-main::')
            return value
        self._rewrite_manifest(current,rename(pa.load(current)));fp.verify(current)
        result=fp._preserve_unprocessed(current,prior,self.root/'renamed')
        self.assertEqual(result['preserved_documents'],['supplement'])
        self.assertEqual([d['identity'] for d in result['documents']],['renamed-main','supplement'])
        repeated=fp._preserve_unprocessed(current,self.root/'renamed/manifest.json',self.root/'renamed-again')
        self.assertEqual(repeated['preserved_documents'],['supplement'])
        for source in old['source_documents']:source['role']=None
        self._rewrite_manifest(prior,old)
        with self.assertRaisesRegex(ValueError,'prior-manuscript-identity-ambiguous'):
            fp._preserve_unprocessed(current,prior,self.root/'ambiguous')

    def test_corrected_findings_do_not_return_as_metadata_or_hide_new_findings(self):
        self.test_review_correction_preserves_outcomes_and_survives_refresh()
        corrected=self.root/'corrected/manifest.json';m=fp.verify(corrected)
        products=pa.load(corrected.parent/m['products_key']);change=products['amendments'][0]['changes'][0]
        old=change['original'];scope={k:change[k] for k in ('element_id','source_sha256')}
        revised=dict(old,reason='New source-backed concern using the same local finding ID')
        export=dict(elements=[dict(scope,outcome=products['elements'][0]['outcome'],findings=[revised])])
        qualifications=[dict(scope=scope,metadata=old),dict(scope=scope,metadata=revised),
                        dict(scope=dict(element_id='supplement::table-1',source_sha256=m['documents'][1]['source_sha256']),metadata=old)]
        out=self.root/'metadata-refresh';fresh=fp.build(corrected,out,exports=[export],qualifications=qualifications)
        result=pa.load(out/fresh['products_key'])
        with self.subTest('new-finding'): self.assertEqual(result['elements'][0]['findings'],[revised])
        with self.subTest('old-metadata'): self.assertNotIn(qualifications[0],result['qualifications'])
        self.assertIn(qualifications[1],result['qualifications'])
        self.assertIn(qualifications[2],result['qualifications'])
