"""Offline mechanical progression; no authorization or model responses fabricated."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pymupdf
from pdf_source_package import preparation, gates, cli, launcher, workflow
from pdf_source_package.io import save, load, sha, SETTINGS
from pdf_source_package.phase_evidence import operation_evidence


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
