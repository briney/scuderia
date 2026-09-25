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
