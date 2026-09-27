"""Offline mechanical progression; no authorization or model responses fabricated."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pymupdf
from pdf_source_package import preparation, gates, cli, launcher, workflow
from pdf_source_package.association import label_key
from pdf_source_package.io import save, load, sha, SETTINGS
from pdf_source_package.phase_evidence import operation_evidence


class AppendixLabelNamespace(unittest.TestCase):
    def test_appendix_letter_dot_number_labels_parse(self):
        self.assertEqual(label_key('Table D.1'), ('', 'table', 'd.1'))
        self.assertEqual(label_key('Figure C.1'), ('', 'figure', 'c.1'))
        self.assertEqual(label_key('Table K.3'), ('', 'table', 'k.3'))

    def test_main_text_labels_still_parse(self):
        self.assertEqual(label_key('Table 15a'), ('', 'table', '15a'))
        self.assertEqual(label_key('Fig. 3'), ('', 'figure', '3'))
        self.assertEqual(label_key('Table S2'), ('', 'table', 's2'))

    def test_decimal_and_partial_numbers_still_rejected(self):
        with self.assertRaises(ValueError):
            label_key('Table 1.5')
        with self.assertRaises(ValueError):
            label_key('Table A.B')


class ClassificationLabelMerge(unittest.TestCase):
    def test_collection_preserves_headings_without_association_labels(self):
        with tempfile.TemporaryDirectory(dir=os.environ['PDF_TEST_WORK']) as tmp:
            root = Path(tmp)
            save(root/'manifest.json', dict(fixture=True, documents=[dict(identity='synthetic')]))
            labels = ['Figure 3', 'Equation 19', 'KEY RESOURCES TABLE', 'Table S2']
            candidates = [dict(id=f'c{i}', source_document='synthetic', page=1,
                regions=[dict(page=1, bbox=[0, i, 10, i+1])], observed_labels=[])
                for i in range(len(labels))]
            observations = [dict(candidate_id=c['id'], content_type='other', source_label=label,
                label_evidence='native-text', uncertainty=[]) for c, label in zip(candidates, labels)]
            for phase in ('initial', 'classification'):
                directory = 'requests/'+phase
                save(root/directory/'request-wire.json', {})
                digest = sha(root/directory/'request-wire.json')
                save(root/directory/'call.json', dict(request_sha256=digest,
                    transport_origin='offline-fixture', selection_status='validated'))
                save(root/directory/'reservation.json', dict(transport_origin='offline-fixture'))
                save(root/directory/'candidates.json', candidates)
                save(root/directory/'validation.json', {})
                save(root/directory/'raw-selection.json', dict(classifications=observations))
                save(root/directory/'output-bindings.json', workflow.output_bindings(root, directory))
                save(root/f'{phase}-plan.json', dict(requests=[dict(document='synthetic',
                    directory=directory, request_sha256=digest)]))
            result = workflow.collect(root)['synthetic']
            self.assertEqual([c['classification_observation']['source_label'] for c in result], labels)
            self.assertEqual([[v['label'] for v in c['observed_labels']] for c in result],
                             [['Figure 3'], [], [], ['Table S2']])
            with patch.object(workflow.association, 'label_key', side_effect=RuntimeError('unexpected')):
                with self.assertRaisesRegex(RuntimeError, 'unexpected'):
                    workflow.collect(root)


class AssociationContinuation(unittest.TestCase):
    def test_continuation_label_needs_a_retained_labeled_candidate(self):
        import copy
        from pdf_source_package import association as a
        def candidate(ident,page,role,labels=()):
            return dict(id=ident,source_document='synthetic',source_sha256='a'*64,page=page,role=role,
                content_type='figure',type_origin='synthetic',native_text='Continuation text',
                observed_labels=[dict(label=label,origin='native-text') for label in labels],
                regions=[dict(id=ident+'-region',page=page,bbox=[0,0,10,10],lines=[])])
        cs=[candidate('body',1,'body'),candidate('continued',2,'caption')]
        value=dict(status='ok',groups=[dict(source_document='synthetic',body_refs=['body'],caption_note_refs=['continued'],label='Figure S7')],unassociated=[],conflicts=[])
        with self.assertRaisesRegex(ValueError,'unsupported-label'):a.validate(value,cs)
        value['groups'][0]['label']=None
        self.assertEqual(a.validate(value,cs)['candidate_count'],2)
        cs.append(candidate('heading',1,'caption',['Figure S7']))
        value['groups'][0].update(label='Figure S7',caption_note_refs=['heading','continued'])
        self.assertEqual(a.validate(value,cs)['candidate_count'],3)
        wrong=copy.deepcopy(cs);wrong[1]['source_document']='another'
        with self.assertRaisesRegex(ValueError,'cross-document'):a.validate(value,wrong)
        value['groups'][0]['caption_note_refs'].append('invented-line-id')
        with self.assertRaisesRegex(ValueError,'unknown-reference'):a.validate(value,cs)


class Bookkeeping(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ['PDF_TEST_WORK'])
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.pdf = self.root/'source.pdf'
        with pymupdf.open() as doc:
            page = doc.new_page(); page.insert_text((40,40),'Synthetic source text.')
            doc.save(self.pdf)
        self.scope = self.root/'scope.json'; self.job = self.root/'jobs'/'source'
        save(self.scope, dict(application_endpoint='https://example.invalid/v1/chat/completions',max_application_posts=4,
            documents=[dict(identity='synthetic',source=str(self.pdf),sha256=sha(self.pdf),channels=['caption'])]))

    def prepare(self, empty=False):
        if empty:
            value=load(self.scope); value['documents'][0]['channels']=['structured','classification','association']; save(self.scope,value,replace=True)
        if empty:
            with patch.object(preparation.classification, "reporting_disposition", return_value=dict(disposition="policy-excluded")):
                preparation.prepare(self.scope,self.job,fixture=True)
        else:
            preparation.prepare(self.scope,self.job,fixture=True)

    def counted(self, root, phase, cache):
        plan=load(root/f'{phase}-plan.json')
        for row in plan['requests']:
            count=dict(prompt_tokens_local=12,reserved_completion_tokens=65536,context_limit=262144,fits=True,request_sha256=row['request_sha256'])
            row.update(status='ready',count=count); save(root/row['directory']/'count.json',count)
        save(root/f'{phase}-plan.json',plan,replace=True)

    def test_prepare_counts_seals_and_receipts_without_approval(self):
        receipt=self.root/'receipt.json'
        with patch.object(gates,'count_phase',side_effect=self.counted) as count:
            self.assertEqual(cli.main(['--workflow-evidence',str(receipt),'prepare','--scope',str(self.scope),'--output',str(self.job),'--offline-fixture','--processor-cache',str(self.root)]),0)
        self.assertEqual(count.call_count,1)
        self.assertFalse(load(self.job/'initial-approval.template.json')['approved'])
        self.assertFalse((self.job/'initial-session.json').exists())
        self.assertEqual(load(receipt)['next_step'],'review-and-author-approval')
        before=(self.job/'initial-seal.json').read_bytes()
        with patch.object(gates,'count_phase',side_effect=AssertionError('must not recount')):
            self.assertEqual(gates.prepare_phase(self.job,'initial',self.root),'review-and-author-approval')
        self.assertEqual((self.job/'initial-seal.json').read_bytes(),before)

    def test_resume_after_count_and_reject_changed_seal(self):
        self.prepare(); self.counted(self.job,'initial',self.root)
        with patch.object(gates,'count_phase',side_effect=AssertionError('must not recount')):
            gates.prepare_phase(self.job,'initial',self.root)
        plan=load(self.job/'initial-plan.json'); plan['requests'][0]['status']='uncounted'
        save(self.job/'initial-plan.json',plan,replace=True)
        with self.assertRaises(ValueError): gates.prepare_phase(self.job,'initial',self.root)

    def test_empty_phases_complete_without_processor_or_approval(self):
        self.prepare(empty=True)
        with patch.object(gates,'count_phase',side_effect=AssertionError('empty must not count')):
            self.assertEqual(gates.prepare_phase(self.job,'initial',None),'prepare-stage:classification')
            for phase in ('classification','association'):
                workflow.prepare_stage(self.job,phase); gates.prepare_phase(self.job,phase,None)
        self.assertTrue(workflow.final_state(self.job)['requested_work_complete'])
        self.assertFalse(list(self.job.glob('*-approval.json')))
        self.assertFalse(list(self.job.glob('*-session.json')))
        self.assertEqual(operation_evidence(self.job,'seal','association')['next_step'],'finalize')

    def test_partial_count_and_uncertain_execution_are_holds(self):
        self.prepare(); row=load(self.job/'initial-plan.json')['requests'][0]
        save(self.job/row['directory']/'count.json',{})
        with self.assertRaisesRegex(ValueError,'partial-count'): gates.prepare_phase(self.job,'initial',self.root)
        (self.job/row['directory']/'count.json').unlink()
        save(self.job/'initial-session.json',{})
        with patch.object(gates,'count_phase') as count:
            with self.assertRaisesRegex(ValueError,'execution'): gates.prepare_phase(self.job,'initial',self.root)
            count.assert_not_called()

    def test_retention_output_or_attempt_rejected_before_writes(self):
        retained=self.root/'retained'; retained.mkdir(); save(retained/'retention.json',{'schema':'source-retention-v1'})
        for output,attempt in ((retained/'work',self.root/'attempt'),(self.job,retained/'attempt')):
            with self.assertRaisesRegex(ValueError,'retention'):
                launcher.validated(dict(operation='prepare',scope_path=str(self.scope),output_dir=str(output),attempt_dir=str(attempt)))
            self.assertFalse(output.exists()); self.assertFalse(attempt.exists())
        with self.assertRaisesRegex(ValueError,'retention'): preparation.prepare(self.scope,retained/'direct')

    def test_nested_parents_created_and_attempt_never_reused(self):
        args=dict(operation='prepare',scope_path=str(self.scope),output_dir=str(self.job),attempt_dir=str(self.root/'attempts'/'new'))
        launcher.validated(args)
        import sys
        attempt=Path(args['attempt_dir'])
        self.assertEqual(launcher.run_child([sys.executable,'-c','pass'],self.root,attempt,5)['exit_code'],0)
        with self.assertRaises(ValueError): launcher.validated(args)

    def test_insufficient_scope_budget_never_seals(self):
        value=load(self.scope); value['max_application_posts']=0; save(self.scope,value,replace=True)
        with self.assertRaisesRegex(ValueError,'budget'): self.prepare()
        self.assertFalse((self.job/'initial-seal.json').exists())

    def test_public_launcher_empty_phase_receipt(self):
        value=load(self.scope); value['documents'][0]['channels']=['association']; save(self.scope,value,replace=True)
        import sys
        result=launcher.launch(dict(operation='prepare',scope_path=str(self.scope),output_dir=str(self.job),
            processor_cache=str(self.root),offline=True,offline_fixture=True,attempt_dir=str(self.root/'attempts'/'prepare')),
            launcher.Deployment(Path(preparation.__file__).parents[1],Path(sys.executable)))
        self.assertTrue(result['success'],result)
        self.assertEqual(result['next_step'],'prepare-stage:association')
        self.assertFalse((self.job/'initial-approval.json').exists())

    def test_retention_cannot_receive_direct_count_or_receipt(self):
        retained=self.root/'retained'; retained.mkdir(); save(retained/'retention.json',{})
        with self.assertRaisesRegex(ValueError,'retention'): save(retained/'receipt.json',{})
        self.assertFalse((retained/'receipt.json').exists())

    def test_completed_empty_phase_cannot_be_executed_or_replayed(self):
        from pdf_source_package import execution
        self.prepare(empty=True); gates.prepare_phase(self.job,'initial')
        approval=load(self.job/'initial-approval.template.json')
        approval.update(approved=True,approved_by='offline-fixture',source_and_candidates_reviewed=True,
                        payload_counts_reviewed=True,current_route_reviewed=True)
        path=self.root/'approval.json'; save(path,approval)
        before={str(p.relative_to(self.job)):sha(p) for p in self.job.rglob('*') if p.is_file()}
        replay=self.root/'empty-replay.json'; save(replay,dict(provenance='historical-saved-response-replay',responses=[]))
        for kwargs in (dict(replay=replay),dict(authorize=True)):
            with self.assertRaisesRegex(ValueError,'phase-already-complete'):
                execution.run_phase(self.job,'initial',path,**kwargs)
            self.assertEqual(before,{str(p.relative_to(self.job)):sha(p) for p in self.job.rglob('*') if p.is_file()})
        self.assertEqual(operation_evidence(self.job,'seal','initial')['phase_status']['status'],'complete')

    def test_resume_reports_existing_downstream_state(self):
        self.prepare(empty=True); gates.prepare_phase(self.job,'initial')
        workflow.prepare_stage(self.job,'classification')
        self.assertEqual(gates.prepare_phase(self.job,'initial'),'seal-with-processor-cache:classification')
        gates.prepare_phase(self.job,'classification')
        self.assertEqual(gates.prepare_phase(self.job,'initial'),'prepare-stage:association')
        workflow.prepare_stage(self.job,'association'); gates.prepare_phase(self.job,'association')
        self.assertEqual(gates.prepare_phase(self.job,'initial'),'finalize')


class SubpanelPreludeLabels(unittest.TestCase):
    def test_multipanel_caption_prelude_skipped(self):
        from pdf_source_package.association import leading_labels
        t = ('(a) Generative Perplexity (↓) vs. Sampling Iterations.\n'
             '(b) Generated Text (small models)\n'
             'Figure 1: Quality evaluation of unconditionally generated text.')
        self.assertEqual(leading_labels(t), [dict(label='Figure 1', origin='native-text')])

    def test_roman_numeral_prelude_skipped(self):
        from pdf_source_package.association import leading_labels
        self.assertEqual(leading_labels('i. first\nii. second\nTable 2: data'),
                         [dict(label='Table 2', origin='native-text')])

    def test_plain_captions_unchanged(self):
        from pdf_source_package.association import leading_labels
        self.assertEqual(leading_labels('Table 1: Zero-shot')[0]['label'], 'Table 1')
        self.assertEqual(leading_labels('(a) only panel text here'), [])
