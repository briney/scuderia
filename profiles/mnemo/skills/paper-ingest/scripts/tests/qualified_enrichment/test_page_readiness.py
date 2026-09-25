"""Evidence-supported ordinary-page readiness, distinct from request success."""
import copy
import unittest
import article_enrichment as ae
from qualified_enrichment import exports, records
from test_reviews import element, omission


class PageReadiness(unittest.TestCase):
    def accounting(self,status='failed'):
        return dict(requests={'r1':dict(status=status)},counts={s:int(s==status) for s in ('pending','uncertain','failed','completed')},
                    complete=status=='completed',integrity_hold=False)
    def assessment(self):
        return dict(usable_evidence=True,reason='Manuscript text supports a useful distillation.',
                    source_refs=[dict(key='body.txt',sha256='a'*64)],unattempted={})
    def test_failed_visuals_can_be_page_ready(self):
        result=ae.readiness(self.accounting(),self.assessment())
        self.assertTrue(result['page_ready']); self.assertTrue(result['requests_accounted_for'])
        self.assertFalse(result['requests_successful'])
    def test_pending_hold_and_missing_evidence(self):
        a=self.assessment(); state=self.accounting('pending')
        self.assertFalse(ae.readiness(state,a)['page_ready'])
        a['unattempted']={'r1':'Visual description unavailable; proceed from source text.'}
        self.assertTrue(ae.readiness(state,a)['page_ready'])
        state['integrity_hold']=True
        self.assertFalse(ae.readiness(state,a)['page_ready'])
        self.assertFalse(ae.readiness(self.accounting(),None)['page_ready'])
        a['usable_evidence']=False
        self.assertFalse(ae.readiness(self.accounting(),a)['page_ready'])
    def test_clean_unreviewed_content_needs_no_qualification(self):
        v=records.project(element(),policy='observed-limitations-v1')
        result=exports.page_view(v,'/record/cells/0/raw_value')
        self.assertEqual(result['content'],'Distance (angstrom)')
        self.assertFalse(result['unresolved_findings'])
    def test_material_conflict_requires_qualification(self):
        from qualified_enrichment import reviews
        dossier,decision=omission(); v=reviews.apply(dossier,[decision])[0]
        with self.assertRaisesRegex(ValueError,'qualification'):
            exports.page_view(v,'/record/cells/0/raw_value')
        self.assertTrue(exports.page_view(v,'/record/cells/0/raw_value',qualification='Native heading includes a unit.')['unresolved_findings'])
    def test_generic_unverified_status_is_metadata(self):
        e=element();e['outcome']['record']['text_verification']='unverified-model-reading'
        self.assertTrue(records.project(e)['findings'])
        self.assertFalse(records.project(e,policy='observed-limitations-v1')['findings'])

    def test_historical_coverage_is_not_a_new_page_warning(self):
        import reenrich as rr
        self.assertFalse(rr._material_history(dict(metadata_target='/elements/0/coverage/0',metadata=dict(target='/record',aspect='content',reason='Checked'))))
        self.assertTrue(rr._material_history(dict(metadata_target='/elements/0/coverage/0',metadata=dict(warning='Substantive retained warning'))))

    def test_current_history_omits_only_known_automatic_baseline(self):
        import reenrich as rr
        import portable_articles as pa
        import tempfile
        from pathlib import Path
        e=element();e['outcome']['record']['text_verification']='unverified-legacy-prose'
        legacy=records.project(e);finding=next(f for f in legacy['findings'] if f['target']=='/record')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'old-export.json';pa.save(path,dict(elements=[legacy]))
            self.assertFalse(rr._material_finding(finding,{'old':path},dict(key='old')))
            proposal=dict(finding,resolutions=[{'reason':'Substantive attributed correction'}])
            self.assertTrue(rr._material_finding(proposal,{'old':path},dict(key='old')))
            legacy['outcome']['record']['unreadable']=True;path=Path(folder)/'substantive-export.json';pa.save(path,dict(elements=[legacy]))
            self.assertTrue(rr._material_finding(finding,{'old':path},dict(key='old')))


class PortableReview(unittest.TestCase):
    def setUp(self):
        import test_reenrich as fixtures
        fixtures.ReenrichTests.setUp(self)
    def test_all_visual_failures_use_source_without_false_success(self):
        import test_reenrich as fixtures
        import reenrich as rr
        import portable_articles as pa
        from article_runtime import digest
        fixtures.ReenrichTests.plan(self,selected=False)
        rr.advance(self.work,'prepare'); approval=fixtures.count_and_approve(self.work,self.base)
        state=rr.advance(self.work,'approved-execute',approval=approval,
                         fixture_transport=fixtures.inference_double(self.work,interrupt=True))
        rr.advance(self.work,'review-create'); packet=pa.load(self.work/'review/packet.json')
        self.assertEqual(len(packet['elements']),2)
        evidence=next(f for f in self.m['files'] if f['key']=='package/main/page.txt')
        assessment=dict(usable_evidence=True,reason='Native text supports the retained summary.',
                        source_refs=[{k:evidence[k] for k in ('key','sha256')}],unattempted={})
        value=dict(schema='contextual-review-v2',packet_sha256=digest(packet),reviewer=fixtures.reviewer(),
                   findings=[],coverage=[],resolutions=[],assessment=assessment)
        path=self.base/'review-input.json';pa.save(path,value)
        rr.advance(self.work,'review-import',submission=path)
        result=rr.advance(self.work,'export')
        self.assertTrue(result['readiness']['page_ready'])
        self.assertFalse(result['execution_complete'])
        self.assertEqual(result['request_accounting']['counts']['uncertain'],2)
        _,_,manifest,_,_,binding,_=rr.context(self.work)
        self.assertEqual(ae.verify_export(self.work,binding,manifest),result)
        bad=copy.deepcopy(assessment);bad['source_refs'][0]['sha256']='0'*64
        from qualified_enrichment import reviews
        with self.assertRaisesRegex(ValueError,'source-binding'):
            reviews.validate_assessment(pa.load(self.work/'review/dossier.json'),bad)


class InitialHandoff(unittest.TestCase):
    def test_current_qualification_text_has_no_coverage_warning(self):
        import source_package as sp
        v=records.project(element(),policy='observed-limitations-v1')
        exported=dict(schema='qualified-enrichment-export-v2',elements=[v],eligibility=dict(
            element_accounting=[dict(element_id=v['element_id'],disposition='enriched')],zero_eligible=False))
        self.assertEqual(sp.qualification_text(exported),'')
        exported['eligibility']['element_accounting'][0]['disposition']='failed'
        self.assertIn('failed',sp.qualification_text(exported))
        exported['schema']='qualified-enrichment-export-v1'
        self.assertIn('unreviewed',sp.qualification_text(exported))


class PartialRefresh(unittest.TestCase):
    def setUp(self):
        import test_reenrich as fixtures
        fixtures.ReenrichTests.setUp(self)
    def test_partial_native_page_applies_and_publishes(self):
        import test_reenrich as fixtures
        import reenrich as rr
        import portable_articles as pa
        from article_runtime import digest
        from test_article_corrections import FakeRclone
        fixtures.ReenrichTests.plan(self,selected=False)
        rr.advance(self.work,'prepare'); approval=fixtures.count_and_approve(self.work,self.base)
        rr.advance(self.work,'approved-execute',approval=approval,fixture_transport=fixtures.inference_double(self.work,interrupt=True))
        fixtures.review_and_export(self.work,self.base)
        _,p,manifest,m,roster,binding,_=rr.context(self.work)
        exported=pa.load(self.work/'export/handoff.json')
        before=self.page.read_text();start,end=rr._sections(before)['## Results']
        key='package/main/page.txt';path=pa.verify_local(manifest)[1][key]
        submission=dict(schema='reenrich-page-candidate-v3',binding=binding,export_sha256=pa.sha(self.work/'export/handoff.json'),
            reviewer=fixtures.reviewer(),qualification='',full_distillation_reviewed=True,
            replacements=[dict(heading='## Results',old_sha256=rr.hashlib_sha(before[start:end]),
                new_text=before[start:end].replace('Old scientific prose.','Native manuscript text supports this synthetic summary.'),
                elements=roster,evidence=[dict(kind='source',key=key,sha256=pa.sha(path),pointer='',quote=path.read_text(),qualification='')])])
        inp=self.base/'current-candidate.json';pa.save(inp,submission)
        rr.candidate_import(self.work,inp);rr.apply(self.work,authorize=True)
        self.assertIn('<!-- Human annotation -->',self.page.read_text())
        self.assertIn('[[preserved-link]]',self.page.read_text())
        self.assertIn('uncertain',self.page.read_text())
        self.assertNotIn('Unreviewed aspects:',self.page.read_text())
        fake=FakeRclone()
        result=rr.publish(self.work,'fake','bucket','gate',runner=fake)
        self.assertTrue(result['page_refresh_complete'])
        receipt=pa.load(self.work/'completion.json')
        self.assertFalse(receipt['requests_successful'])
        pub=receipt['publication']
        verified=rr.verify_completion(self.work/'completion.json',self.work/'archive/manifest.json',
            manifest_key=pub['manifest_key'],manifest_sha256=pub['manifest_sha256'],article_key=pub['article_key'],page=self.page)
        self.assertTrue(verified['page_refresh_complete'])
        restored=self.base/'restored'
        pa.restore_remote(pub['manifest_key'],pub['manifest_sha256'],restored,remote='fake',bucket='bucket',prefix='gate',article_key=pub['article_key'],runner=fake)
        receipt_path=self.base/'saved-completion.json';pa.save(receipt_path,receipt)
        import shutil
        shutil.rmtree(self.work);shutil.rmtree(self.base/'source');shutil.rmtree(self.base/'archive')
        self.assertTrue(rr.verify_completion(receipt_path,restored/'manifest.json',manifest_key=pub['manifest_key'],
            manifest_sha256=pub['manifest_sha256'],article_key=pub['article_key'],page=self.page)['page_refresh_complete'])

    def pending_export(self):
        import test_reenrich as fixtures
        import reenrich as rr
        import portable_articles as pa
        from article_runtime import digest
        fixtures.ReenrichTests.plan(self,selected=False)
        rr.advance(self.work,'prepare'); approval=fixtures.count_and_approve(self.work,self.base)
        rr.advance(self.work,'review-create'); packet=pa.load(self.work/'review/packet.json')
        key='package/main/page.txt'; source=next(f for f in self.m['files'] if f['key']==key)
        _,_,manifest,_,roster,binding,_=rr.context(self.work)
        state=ae.execution_state(self.work,binding,manifest)
        inp=self.base/'assessment.json';pa.save(inp,dict(schema='contextual-review-v2',packet_sha256=digest(packet),reviewer=fixtures.reviewer(),
            findings=[],coverage=[],resolutions=[],assessment=dict(usable_evidence=True,reason='Native text supports this source-based page.',
            source_refs=[{k:source[k] for k in ('key','sha256')}],unattempted={rid:'Proceed from native text.' for rid in state['accounting']['requests']})))
        rr.advance(self.work,'review-import',submission=inp);rr.advance(self.work,'export')
        before=self.page.read_text();start,end=rr._sections(before)['## Results'];path=pa.verify_local(manifest)[1][key]
        candidate=self.base/'pending-candidate.json';pa.save(candidate,dict(schema='reenrich-page-candidate-v3',binding=binding,
            export_sha256=pa.sha(self.work/'export/handoff.json'),reviewer=fixtures.reviewer(),qualification='',full_distillation_reviewed=True,
            reconciliation_outcome='reviewed-no-scientific-text-change',replacements=[dict(heading='## Results',old_sha256=rr.hashlib_sha(before[start:end]),
            new_text=before[start:end],elements=roster,evidence=[dict(kind='source',key=key,sha256=pa.sha(path),pointer='',quote=path.read_text(),qualification='')])]))
        return approval,candidate,manifest,binding

    def test_pending_assessed_export_has_page_continuation(self):
        import reenrich as rr
        self.pending_export()
        self.assertEqual(rr.execute(work_root=self.work)['next_step'],'candidate-import')

    def test_later_fatal_hold_blocks_frozen_page_export(self):
        import reenrich as rr
        from test_article_corrections import FakeRclone
        approval,candidate,manifest,binding=self.pending_export()
        rr.candidate_import(self.work,candidate)
        with self.assertRaises(ValueError):
            rr.advance(self.work,'approved-execute',approval=approval,fixture_transport=lambda *a:dict(http_status=401,raw=b'{}'))
        self.assertTrue(ae.verify_export(self.work,binding,manifest)['readiness']['page_ready'])
        self.assertEqual(rr.execute(work_root=self.work)['next_step'],'hold-inspect-evidence-no-retry')
        for operation in (lambda:rr.candidate_import(self.work,candidate),lambda:rr.apply(self.work,authorize=True),
                          lambda:rr.publish(self.work,'fake','bucket','gate',runner=FakeRclone())):
            with self.assertRaisesRegex(ValueError,'execution-integrity-hold'): operation()
        self.assertFalse((self.work/'apply-start.json').exists())

    def test_diagnostic_completion_does_not_use_page_readiness(self):
        import reenrich as rr
        from unittest.mock import patch
        self.pending_export()
        context=list(rr.context(self.work))
        # Status-layer test: an already verified diagnostic context never uses page readiness.
        context[1]=dict(context[1],schema=rr.DIAGNOSTIC_PLAN,mode='selected-diagnostic',page_path=None)
        with patch.object(rr,'context',return_value=tuple(context)):
            status=rr.execute(work_root=self.work)
        self.assertEqual(status['completion'],'pending')
        self.assertEqual(status['status'],'partial-diagnostic-export')
