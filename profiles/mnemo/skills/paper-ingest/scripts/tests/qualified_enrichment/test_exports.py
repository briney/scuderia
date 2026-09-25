"""Read-only retained outcomes and explicitly synthetic variant controls."""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT)]
from qualified_enrichment import exports,reviews
from qualified_enrichment.records import project
from test_records import retained
from test_reviews import element,omission,ref,reviewer


class Propagation(unittest.TestCase):
    def test_saved_table_and_native_and_raster_algorithm(self):
        paths=[
            ('table','v6/table/requests/e0030-table'),
            ('native','v7/algorithm-native/requests/e0085-algorithm'),
            ('raster','v4/algorithm-raster/requests/e0055-algorithm')]
        for kind,path in paths:
            with self.subTest(kind=kind):
                e=retained(path); original=copy.deepcopy(e); v=project(e)
                self.assertTrue(v['findings']); self.assertEqual(e,original)
                text=exports.render_record(v,v['outcome']['record'])
                self.assertIn('warning',text)
                for f in v['findings']:
                    if f['target'] in ('','/record') or any(t in f['target'] for t in ('/lines/','/cells/')):
                        self.assertIn(f['id'],text)

    def test_embedded_table_flags_stay_at_cell(self):
        e=element(); table=e['outcome']['record']
        table['cells'][1]['notation']=dict(status='unresolved',unresolved=['Synthetic ambiguous superscript'])
        e['outcome']['record']=dict(kind='figure',shown={},observations=[],caption_context={},limitations=[],embedded_tables=[table])
        v=project(e); f=v['findings'][0]
        self.assertIn('/embedded_tables/0/cells/1',f['target'])
        html=exports.render_record(v,e['outcome']['record'])
        self.assertIn('<table>',html); self.assertIn(f['id'],html)
        with self.assertRaises(ValueError): exports.exact_view(v,'/record/embedded_tables/0/cells/1/raw_value',purpose='exact')

    def test_disagreement_and_missing_evidence_do_not_resolve(self):
        dossier,entry=omission()
        entry['submission']['findings'][0]['competing_readings']=[dict(text='Ambiguous mapping',evidence=[ref()])]
        f=reviews.apply(dossier,[entry])[0]['findings'][0]
        second=copy.deepcopy(entry); second['submission']['findings']=[]
        second['submission']['resolutions']=[dict(finding_id=f['id'],reason='Unproven association',basis='literal-copy',
            evidence=[ref()],agreement='unambiguous',proposed_value='Distance (angstrom)',aspect='units')]
        result=reviews.apply(dossier,[entry,second])[0]
        self.assertEqual(result['findings'][0]['status'],'unresolved')
        self.assertEqual(len(result['findings'][0]['resolutions']),1)
        second['submission']['resolutions'][0]['evidence']=[]
        with self.assertRaisesRegex(ValueError,'no-evidence'): reviews.apply(dossier,[entry,second])

    def test_layout_uncertainty_attaches_to_affected_statement(self):
        e=element()
        e['outcome']['record']=dict(kind='algorithm',lines=[dict(text='synthetic statement',indent=None,
            grouping='unresolved',layout_version='native-layout-v2',source_refs=['f1'])])
        findings=project(e)['findings']
        self.assertTrue(any(f['target']=='/record/lines/0' and 'grouping' in f['reason'] and 'indent' in f['reason'] for f in findings),
                        'Saved native statement layout uncertainty must retain its exact statement scope')

    def test_failed_record_not_accepted(self):
        e=element(); e['outcome']['status']='failed'
        with self.assertRaisesRegex(ValueError,'failed-outcome'): project(e)
        e['outcome'].pop('record'); self.assertTrue(project(e)['findings'])

    def test_algorithm_specification_stricter_than_summary(self):
        e=element(); e['outcome']['record']['kind']='algorithm'; v=project(e)
        self.assertTrue(exports.exact_view(v,'/record/cells/0/raw_value',purpose='summary')['unreviewed_aspects'])
        with self.assertRaisesRegex(ValueError,'always-requires-source-inspection'):
            exports.exact_view(v,'/record/cells/0/raw_value',purpose='algorithm-specification',qualification='Discovery only')

    def test_qualified_partial_failed_unknown_and_zero_accounting(self):
        base=dict(kind='qualified-job',execution_holds=[],fixture=False,
                  documents=[dict(source_status='complete',source_complete=True)],elements=[])
        result=exports.eligibility(base)
        self.assertTrue(result['qualified_production_eligible']); self.assertTrue(result['zero_eligible'])
        for status in ('partial','failed','unsupported','unknown-type','skipped-after-failure'):
            e=element(); e.update(content_type='table',document='doc',eligible_default=True,source_pdf='/synthetic/source.pdf')
            e['outcome']=dict(status=status,complete=False)
            base['elements'].append(e)
        e=copy.deepcopy(e); e.update(element_id='algorithm',content_type='algorithm',eligible_default=False)
        e['outcome']['status']='not-selected'; base['elements'].append(e)
        result=exports.eligibility(base)
        self.assertTrue(result['qualified_production_eligible']); self.assertEqual(result['total_elements'],6)
        self.assertEqual(result['element_accounting'][-1]['disposition'],'algorithm-deferred-not-selected')
        for hold in ('pending-or-possibly-posted','route-mismatch','broken-source-evidence'):
            base['execution_holds']=[hold]; self.assertFalse(exports.eligibility(base)['qualified_production_eligible'])
        base['execution_holds']=[]; base['fixture']=True
        self.assertFalse(exports.eligibility(base)['qualified_production_eligible'])
        base['fixture']=False; base['elements'][0]['outcome']['variant']='caption-only'
        self.assertIn('caption-only-not-image-enriched',exports.eligibility(base)['holds'])


if __name__=='__main__':
    sys.addaudithook(lambda event,args: (_ for _ in ()).throw(RuntimeError('offline-network-blocked')) if event.startswith('socket.') else None)
    unittest.main(verbosity=2)
