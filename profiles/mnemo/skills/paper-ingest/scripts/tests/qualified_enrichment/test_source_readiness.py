"""Source success stays factual; page completion requires explicit accounting."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import source_package as sp
import article_enrichment as ae
from pdf_source_package import gates


class SourceReadiness(unittest.TestCase):
    def setUp(self):
        self.acquisition = dict(obligations={k:dict(status='retrieved') for k in ('body','manuscript')},
                                attachments=dict(status='none-listed',items=[]))
        self.facts = dict(phases={p:dict(status='complete',uncertain_reservations=0,fixture_or_replay_calls=0)
                                 for p in ('initial','classification','association')}, requests=[],
                          inspection=dict(status='not-supplied',uncertain_reservations=None,fixture_or_replay_calls=None))
    def ready(self, **kwargs):
        return sp.source_readiness(self.acquisition,self.facts,fixture=False,**kwargs)
    def test_local_failure_is_not_integrity_failure(self):
        self.facts['phases']['initial']['status']='incomplete'
        self.facts['requests']=[dict(id='r1',attempted=True,uncertain_reservation=False)]
        r=self.ready()
        self.assertEqual(r['holds'],[]); self.assertEqual(r['pending'],[])
    def test_unattempted_source_work_requires_disposition(self):
        self.facts['phases']['association']['status']='not-prepared'
        self.facts['requests']=[dict(id='r1',attempted=False,uncertain_reservation=False)]
        r=self.ready()
        self.assertEqual(r['pending'],['source:phase:association','source:request:r1'])
        accounting=dict(requests={},complete=True,integrity_hold=False)
        assessment=dict(usable_evidence=True,unattempted={})
        self.assertFalse(ae.readiness(accounting,assessment,r)['page_ready'])
        assessment['unattempted']={key:'Deferred after extraction failure; native text supports the page.' for key in r['pending']}
        self.assertTrue(ae.readiness(accounting,assessment,r)['page_ready'])
    def test_missing_source_with_disposition_is_accounted_for(self):
        self.acquisition['obligations']['body']=dict(status='missing',disposition='Redundant text endpoint failed; PDF retained.')
        self.acquisition['attachments']=dict(status='advertised',items=[dict(id='supp',status='missing',disposition='Observed 403.')])
        self.assertEqual(self.ready()['pending'],[])
        self.acquisition['attachments']=dict(status='not-inspected',items=[])
        self.assertEqual(self.ready()['pending'],['source:attachments'])
    def test_fixture_stop_and_invalid_inspection_stay_blocking(self):
        self.assertEqual(self.ready(stopped=True)['holds'],['workflow-stop-record'])
        self.facts['phases']['initial']['fixture_or_replay_calls']=1
        self.assertIn('fixture-or-replay-initial',self.ready()['holds'])
        self.facts['inspection']['status']='directory-missing'
        self.assertIn('inspection-evidence-incomplete',self.ready()['holds'])
    def test_possibly_consumed_is_accounted_not_success_or_retry(self):
        self.facts['requests']=[dict(id='r1',attempted=False,uncertain_reservation=True)]
        self.assertFalse(self.ready()['pending'])
    def test_new_source_policy_does_not_relax_legacy_manifest(self):
        manifest=dict(schema='portable-article-manifest-v3',source_status=dict(complete=False,fixture=False))
        with self.assertRaisesRegex(ValueError,'source-not-production-eligible'):
            ae.source_scope(manifest,[],False,'production')
        manifest['source_status']['readiness']=self.ready()
        ae.source_scope(manifest,[],False,'production')
        manifest['source_status']['readiness']['holds']=['workflow-stop-record']
        with self.assertRaisesRegex(ValueError,'source-not-production-eligible'):
            ae.source_scope(manifest,[],False,'production')

    def test_refresh_checks_the_same_source_readiness_as_export(self):
        import reenrich as rr
        source=self.ready()
        source['pending']=['source:phase:association']
        accounting=dict(requests={},complete=True,integrity_hold=False)
        assessment=dict(usable_evidence=True,unattempted={})
        exported=dict(schema='portable-qualified-export-v4',request_accounting=accounting,assessment=assessment,
                      source_status=dict(readiness=source),readiness=ae.readiness(accounting,assessment,source))
        self.assertFalse(rr.page_ready(exported))
        assessment['unattempted']={'source:phase:association':'Deferred; native evidence reviewed.'}
        exported['readiness']=ae.readiness(accounting,assessment,source)
        self.assertTrue(rr.page_ready(exported))

    def test_later_assessment_cannot_silently_erase_observed_source_limitations(self):
        from qualified_enrichment import reviews
        first=dict(usable_evidence=True,source_refs=[dict(key='body.txt',sha256='a'*64)],unattempted={},reason='Reviewed body.',
                   source_limitations=['Figure extraction failed; the page uses manuscript text.'])
        later=dict(first); later.pop('source_limitations')
        with patch.object(reviews,'validate_assessment',side_effect=lambda dossier,value,**kwargs:value):
            result=reviews.assessment({},[dict(submission=dict(assessment=first)),dict(submission=dict(assessment=later))])
        self.assertEqual(result['source_limitations'],first['source_limitations'])
        self.assertNotIn('source_limitations',later)

    def test_source_limitations_reach_both_page_registers(self):
        import reenrich as rr
        limitation='Figure extraction failed; the page uses manuscript text.'
        exported=dict(schema='qualified-enrichment-export-v2',assessment=dict(source_limitations=[limitation]),
                      elements=[],eligibility=dict(element_accounting=[]))
        self.assertIn(limitation,sp.qualification_text(exported))
        exported.update(binding='a'*64,source_status={},request_accounting=dict(counts={}),execution_complete=False)
        register=rr._current_register(exported,dict(replacements=[],export_sha256='b'*64,reviewer={},qualification=''),
                    dict(elements=[],documents=[],article={},article_key='c'*64),dict(page_path='/private/tmp/paper.md'),'d'*64,{},None)
        self.assertIn(limitation,rr.register_text(register))

    def test_source_limitations_survive_archive_history_without_elements(self):
        import portable_articles as pa
        import reenrich as rr
        limitation='Advertised supplement unavailable; the page uses manuscript evidence.'
        archived=dict(schema='portable-qualified-export-v4',elements=[],assessment=dict(source_limitations=[limitation]))
        with patch.object(pa,'trusted_modules'):
            projected=pa.qualification_projection(archived)
        self.assertTrue(any(limitation in str(x) for x in projected))
        exported=dict(binding='a'*64,assessment={},elements=[],source_status={},request_accounting=dict(counts={}),execution_complete=False,
                      inherited_history=[dict(key='old/handoff.json',sha256='e'*64,qualifications=projected)])
        register=rr._current_register(exported,dict(replacements=[],export_sha256='b'*64,reviewer={},qualification=''),
                    dict(elements=[],documents=[],article={},article_key='c'*64),dict(page_path='/private/tmp/paper.md'),'d'*64,{},None)
        self.assertIn(limitation,rr.register_text(register))

    def test_fixture_simulation_can_be_ready_without_production_promotion(self):
        source=self.ready()
        source['holds']=['fixture-not-production','fixture-or-replay-initial']
        result=ae.readiness(dict(requests={},complete=True,integrity_hold=False),dict(usable_evidence=True,unattempted={}),source)
        self.assertTrue(result['page_ready'])
        with self.assertRaisesRegex(ValueError,'source-not-production-eligible'):
            ae.source_scope(dict(schema='portable-article-manifest-v3',source_status=dict(complete=False,fixture=True,readiness=source)),[],False,'production')

    def test_current_source_handoffs_project_observed_limitations_only(self):
        import portable_articles as pa
        source=dict(schema='source-package-handoff-v4',holds=['acquisition-body-missing'],
                    limitations=['Mechanical completion is not scientific acceptance.'])
        self.assertEqual(pa.qualification_projection(source),[])
        final=dict(source,schema='source-package-handoff-v5',enrichment=dict(schema='qualified-enrichment-export-v2',elements=[],
                   assessment=dict(source_limitations=['Supplement retrieval failed.'])))
        with patch.object(pa,'trusted_modules'):
            projection=pa.qualification_projection(final)
        self.assertEqual(projection[0]['target'],'/enrichment/assessment/source_limitations')
        self.assertNotIn('acquisition-body-missing',str(projection))


class PartialProgression(unittest.TestCase):
    def test_finished_failed_phase_advances_but_shared_stop_does_not(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'initial-complete.json').write_text('{}')
            status=dict(status='incomplete',failed=1,uncertain_reservations=0,attempted=1)
            with patch.object(gates,'load',return_value=dict(documents=[dict(channels=['classification','association'])])):
                self.assertEqual(gates.next_step(root,'initial',status),'prepare-stage:classification')
                (root/'stop.json').write_text('{}')
                self.assertEqual(gates.next_step(root,'initial',status),'hold-inspect-evidence-no-retry')
    def test_unfinished_phase_never_advances(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(gates.next_step(Path(folder),'initial',dict(status='incomplete',failed=1,uncertain_reservations=0,attempted=1)),
                             'hold-inspect-evidence-no-retry')

if __name__=='__main__': unittest.main()
