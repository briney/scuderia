"""Offline count/seal progression over a real prepared fixture; no paid execution."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from pdf_enrichment import requests, live, bindings
from pdf_source_package import counting
from qualified_enrichment import runtime, storage, launcher


class EnrichmentBookkeeping(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=os.environ['UNCERTAINTY_SCRATCH']); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); self.job=self.root/'job'; self.run=self.job/'v7'
        self.state=dict(selection=dict(selected=['fixture'],code=storage.code_hashes()),execution_holds=[])
        self.cache=Path(os.environ['PDF_PROCESSOR_CACHE'])

    def prepare(self):
        requests.prepare(Path(os.environ['PDF_ENRICHMENT_FIXTURES'])/'current',self.run,kinds=['figure'],fixture=True)

    def fake_count(self, wire):
        return dict(prompt_tokens_local=42,reserved_completion_tokens=65536,context_limit=262144,fits=True)

    def test_count_seal_resume_and_detect_mutation(self):
        self.prepare()
        with patch.object(runtime,'read_job',return_value=self.state), patch.object(counting,'processor',return_value=None), patch.object(counting.Counter,'count',self.fake_count):
            self.assertEqual(runtime.prepare_for_approval(self.job,self.cache),'review-and-author-approval')
        before=storage.tree(self.job)
        with patch.object(runtime,'read_job',return_value=self.state), patch.object(live,'count',side_effect=AssertionError('recount')):
            self.assertEqual(runtime.prepare_for_approval(self.job,self.cache),'review-and-author-approval')
        self.assertEqual(before,storage.tree(self.job))
        self.assertFalse(storage.load(self.run/'approval.template.json')['approved'])
        path=self.run/'seal.json'; sealed=storage.load(path); sealed['files']['counts.json']='bad'; storage.save(path,sealed,replace=True)
        with patch.object(runtime,'read_job',return_value=self.state), self.assertRaisesRegex(ValueError,'seal'):
            runtime.prepare_for_approval(self.job,self.cache)

    def test_zero_eligible_does_not_create_fake_run(self):
        self.state['selection']['selected']=[]
        with patch.object(runtime,'read_job',return_value=self.state), patch.object(live,'count') as count:
            self.assertEqual(runtime.prepare_for_approval(self.job,None),'review-create')
            count.assert_not_called()
        self.assertFalse(self.run.exists())

    def test_interrupted_count_and_uncertain_post_do_not_repeat(self):
        self.prepare(); storage.save(self.run/'count-session.json',{})
        with patch.object(runtime,'read_job',return_value=self.state), patch.object(live,'count') as count:
            with self.assertRaisesRegex(ValueError,'partial-count'): runtime.prepare_for_approval(self.job,self.cache)
            count.assert_not_called()
        storage.save(self.run/'execution-session.json',{})
        self.state['execution_holds']=['execution-pending-or-possibly-posted']
        with patch.object(runtime,'read_job',return_value=self.state), patch.object(live,'count') as count:
            self.assertEqual(runtime.prepare_for_approval(self.job,self.cache),'hold-inspect-evidence-no-retry')
            count.assert_not_called()

    def test_nested_directory_creation_and_retention_guards(self):
        self.assertTrue(storage.new(self.root/'new'/'nested').is_dir())
        retained=self.root/'retained'; retained.mkdir(); storage.save(retained/'retention.json',{})
        with self.assertRaisesRegex(ValueError,'retention'): storage.new(retained/'bad')
        scripts=Path(__file__).resolve().parents[2]
        import sys
        deployment=launcher.Deployment(scripts,scripts,scripts,scripts,Path(sys.executable))
        for output,attempt in ((retained/'bad',self.root/'attempt'),(self.root/'new-job',retained/'attempt')):
            with self.assertRaisesRegex(ValueError,'retention'):
                launcher.launch(dict(operation='prepare',source_handoff=str(self.root/'handoff.json'),output=str(output),attempt_dir=str(attempt)),deployment)
            self.assertFalse(output.exists()); self.assertFalse(attempt.exists())

    def test_insufficient_approval_budget_cannot_post(self):
        self.prepare()
        with patch.object(runtime,'read_job',return_value=self.state), patch.object(counting,'processor',return_value=None), patch.object(counting.Counter,'count',self.fake_count):
            runtime.prepare_for_approval(self.job,self.cache)
        approval=storage.load(self.run/'approval.template.json')
        approval.update(approved=True,approved_by='offline-fixture',source_and_payload_reviewed=True,
            counts_and_route_reviewed=True,endpoint='https://example.invalid/v1/chat/completions',credential_env='OFFLINE_TEST_KEY',maximum_posts=0)
        path=self.root/'approval.json';storage.save(path,approval)
        with patch.object(live,'execute',side_effect=AssertionError('live forbidden')), patch('builtins.print'):
            with self.assertRaisesRegex(ValueError,'post-budget'):
                live.execute_fixture(self.run,path,lambda *args: self.fail('must not post'))
        self.assertFalse((self.run/'execution-session.json').exists())



class PortableNewIngest(unittest.TestCase):
    def test_real_source_prepares_portable_default_roster(self):
        from test_portable_articles import real_archive
        import portable_articles as pa
        import article_enrichment as ae
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            root=Path(tmp); manifest,m,mapping=real_archive(root)
            handoff=root/'handoff/handoff.json'; storage.save(handoff,dict(fixture=True))
            accepted=dict(package=str(root/'package'),retention=str(root/'retention/retention.json'))
            with patch.object(runtime,'source_handoff',return_value=accepted):
                selection=runtime.prepare(handoff,root/'job',Path(__file__).resolve().parents[2],root)
                self.assertEqual(selection['schema'],'qualified-selection-v2')
                selected,manifest,binding=runtime.portable_job(root/'job')
                prepared=ae.verify(root/'job',binding,manifest)
                self.assertEqual(prepared['roster'],selected['selected'])
                self.assertFalse((root/'job/v7').exists())
                state=runtime.read_job(root/'job')
                self.assertEqual(state['request_accounting']['counts']['pending'],len(selected['selected']))
                import entry
                scripts=Path(__file__).resolve().parents[2]; receipt=root/'seal-receipt.json'
                with patch.object(counting,'processor',return_value=None), patch.object(counting.Counter,'count',EnrichmentBookkeeping.fake_count):
                    result=entry.main(['--enrichment-root',str(scripts),'--adapter-dir',str(scripts),'--method',str(scripts),
                        '--receipt',str(receipt),'--offline','seal','--job',str(root/'job'),
                        '--processor-cache',os.environ['PDF_PROCESSOR_CACHE']])
                self.assertEqual(result,0)
                self.assertEqual(storage.load(receipt)['next_step'],'review-and-author-approval')
                self.assertFalse(storage.load(root/'job/enrichment/approval.template.json')['approved'])
                before=storage.tree(root/'job')
                with patch.object(ae,'count',side_effect=AssertionError('recount')):
                    self.assertEqual(runtime.prepare_for_approval(root/'job'), 'review-and-author-approval')
                self.assertEqual(before,storage.tree(root/'job'))
