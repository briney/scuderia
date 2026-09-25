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

    def fake_count(self, wire):
        return dict(prompt_tokens_local=42,reserved_completion_tokens=65536,context_limit=262144,fits=True)

    def test_historical_bookkeeping_is_read_only(self):
        with patch.object(runtime,'read_job',return_value=self.state):
            with self.assertRaisesRegex(ValueError,'historical-job-read-only'):
                runtime.prepare_for_approval(self.job,self.cache)
        self.assertFalse(self.run.exists())

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

                # The same native job remains reviewable with no successful visuals.
                from qualified_enrichment import reviews, exports
                from test_reenrich import reviewer
                from article_runtime import digest
                review=root/'review'; reviews.create(root/'job','qualified-job',review)
                packet_path=root/'packet.json'
                packet=reviews.packet(review,selected['selected'],packet_path)
                dossier=storage.load(review/'dossier.json')
                _,paths=pa.verify_local(manifest)
                source=next(f for f in dossier['snapshot']['source_files']
                            if f['key'].endswith('native-text.txt') and paths[f['key']].read_text().strip())
                assessment=dict(usable_evidence=True,reason='Retained text is usable for this offline contract test.',
                    source_refs=[source],unattempted={r['id']:'Explicitly deferred; native text is available.' for r in prepared['requests']})
                inp=root/'review-input.json'; storage.save(inp,dict(schema='contextual-review-v2',packet_sha256=digest(packet),
                    reviewer=reviewer(),findings=[],coverage=[],resolutions=[],assessment=assessment))
                reviews.import_review(review,packet_path,inp)
                exported=exports.export(review,root/'export')
                self.assertFalse(exported['readiness']['page_ready'])  # Source fixture cannot be production-ready.
                self.assertFalse(exported['execution_complete'])
                self.assertIn('fixture-not-production',exported['eligibility']['holds'])
                self.assertEqual(exports.verify_export(root/'export/handoff.json',production=False),exported)
                import source_package as sp
                source_handoff=dict(holds=['fixture-not-production'],source_readiness=dossier['snapshot']['source_readiness'])
                deployment=dict(integration_dir=str(scripts),enrichment_root=str(scripts),method_dir=str(scripts))
                launcher_result=root/'attempt/result.json'; storage.save(launcher_result,{})
                with patch.object(sp,'build_handoff',return_value=source_handoff), patch.object(launcher,'verify_result',return_value=dict(deployment=deployment)):
                    final=sp.build_enriched_handoff(root/'retention/retention.json',root/'package',root/'source-result.json',scripts,
                        root/'export/handoff.json',launcher_result,scripts,scripts,root)
                self.assertEqual(final['schema'],'source-package-handoff-v5')
                self.assertFalse(final['production_complete'])
                self.assertEqual(final['enrichment']['request_accounting'],exported['request_accounting'])

                # Completing untouched siblings must not invalidate or enlarge a saved native review.
                from test_reenrich import inference_double
                approval=storage.load(root/'job/enrichment/approval.template.json')
                approval.update(approved=True,approved_by='Offline operator',source_payload_counts_reviewed=True,
                    endpoint='https://example.invalid/v1/chat/completions',credential_env='UNUSED_FIXTURE_KEY')
                approval_path=root/'approval.json'; storage.save(approval_path,approval)
                ae.execute(root/'job',binding,manifest,approval_path,fixture_transport=inference_double(root/'job'))
                self.assertEqual(reviews.verify(review),dossier)
                self.assertEqual(exports.verify_export(root/'export/handoff.json',production=False),exported)
