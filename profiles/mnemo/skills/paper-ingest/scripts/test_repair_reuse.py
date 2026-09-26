"""Selected repairs and conservative phase reuse, synthetic evidence only."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import article_enrichment as ae
import portable_articles as pa
import reenrich as rr
from test_article_corrections import synthetic,FakeRclone
from test_reenrich import fixture_profile,count_and_approve,inference_double,review_and_export


class RepairTests(unittest.TestCase):
    def test_repair_preserves_successes_and_selects_only_failed_elements(self):
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            root=Path(tmp); manifest,m=synthetic(root); work=root/'work'
            rr.plan(rr.Request('synthetic'),manifest=manifest,work_root=work,fixture=True,model_profile=fixture_profile())
            rr.advance(work,'prepare'); ap=count_and_approve(work,root); good=inference_double(work)
            def transport(payload,row):
                if row['id']=='r000001': raise TimeoutError('synthetic uncertain delivery')
                return good(payload,row)
            rr.advance(work,'approved-execute',approval=ap,fixture_transport=transport)
            review_and_export(work,root)
            rr.publish(work,'fake','bucket','gate',runner=FakeRclone())
            final=work/'archive/manifest.json'; repair=root/'repair'
            result=rr.repair_plan(final,work_root=repair,fixture=True,model_profile=fixture_profile())
            self.assertEqual(result['elements'],['main::table-1'])
            rr.advance(repair,'prepare')
            requests=pa.load(repair/'enrichment/prepared.json')['requests']
            self.assertEqual([r['element_id'] for r in requests],['main::table-1'])
            self.assertEqual(pa.load(final)['elements'],pa.load(work/'archive/manifest.json')['elements'])

    def test_phase_bindings_retain_shared_code_and_exclude_only_downstream_assets(self):
        from pdf_source_package import io
        all_code=io.code_hashes()
        initial=io.phase_code_hashes('initial'); classification=io.phase_code_hashes('classification')
        association=io.phase_code_hashes('association')
        self.assertNotIn('assets/association-prompt.txt',initial)
        self.assertNotIn('assets/classifier-prompt.txt',initial)
        self.assertIn('assets/classifier-prompt.txt',classification)
        self.assertIn('assets/association-prompt.txt',association)
        for phase in (initial,classification,association):
            self.assertEqual(phase['association.py'],all_code['association.py'])
            self.assertEqual(phase['execution.py'],all_code['execution.py'])

    def test_source_fork_reuses_only_verified_upstream_and_rejects_shared_change(self):
        import pymupdf
        from pdf_source_package import preparation,gates,workflow,io
        with tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']) as tmp:
            root=Path(tmp); pdf=root/'source.pdf'
            with pymupdf.open() as doc:
                doc.new_page().insert_text((40,40),'Synthetic evidence'); doc.save(pdf)
            scope=root/'scope.json'
            io.save(scope,dict(application_endpoint='https://example.invalid/v1/chat/completions',max_application_posts=3,
                documents=[dict(identity='synthetic',source=str(pdf),sha256=io.sha(pdf),channels=['structured','classification','association'])]))
            old=root/'old'
            with patch.object(preparation.classification,'reporting_disposition',return_value=dict(disposition='policy-excluded')):
                preparation.prepare(scope,old,fixture=True)
            gates.prepare_phase(old,'initial')
            workflow.prepare_stage(old,'classification'); gates.prepare_phase(old,'classification')
            original=io.code_hashes(); changed=dict(original,**{'assets/association-prompt.txt':'a'*64})
            with patch.object(io,'code_hashes',return_value=changed):
                result=workflow.fork_source(old,root/'new','association')
            self.assertEqual(result['reused_phases'],['initial','classification'])
            self.assertFalse((root/'new/association-plan.json').exists())
            self.assertEqual((old/'initial-seal.json').read_bytes(),(root/'new/initial-seal.json').read_bytes())
            changed=dict(original,**{'association.py':'b'*64})
            with patch.object(io,'code_hashes',return_value=changed):
                with self.assertRaisesRegex(ValueError,'upstream-code-changed'):
                    workflow.fork_source(old,root/'wrong','association')
            self.assertFalse((root/'wrong').exists())
            manifest=io.load(old/'manifest.json'); source=old/manifest['documents'][0]['raw']; source.write_bytes(b'tampered')
            with self.assertRaises((ValueError,RuntimeError)):
                workflow.fork_source(old,root/'tampered','association')
