"""Initial-route decisions survive page drafting and never authorize requests."""
import os
from pathlib import Path
import tempfile
import unittest
import portable_articles as pa
import reenrich as rr

class InitialIngest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=os.environ['SOURCE_PACKAGE_TEST_ROOT']);self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.page=self.root/'paper.md';self.work=self.root/'work'

    def test_stub_route_survives_draft_and_returns_acquisition_template(self):
        self.page.write_text('---\nkind: paper\nslug: synthetic\ntags: [stub]\nneeds-ingest: true\n---\n## Citation\nSource citation.\n')
        result=rr.route('synthetic',page=self.page,work_root=self.work)
        self.assertEqual(result['route'],'initial-ingest')
        self.assertTrue(Path(result['next_operation']['artifacts']['acquisition_template']).is_file())
        self.page.write_text('---\nkind: paper\nslug: synthetic\nneeds-ingest: true\n---\n## Findings\nDraft science.\n')
        self.assertEqual(rr.execute(work_root=self.work)['route'],'initial-ingest')
        self.assertEqual(rr.route('synthetic',page=self.page,work_root=self.work)['completion_verifier'],'final_products.verify_ingest')

    def test_absent_initial_rich_refresh_and_ambiguous_stub_hold(self):
        self.assertEqual(rr.route('synthetic',page=self.page,work_root=self.work)['route'],'initial-ingest')
        self.page.write_text('---\nkind: paper\nslug: synthetic\nneeds-ingest: true\n---\n## Findings\nExisting science.\n')
        self.assertEqual(rr.route('synthetic',page=self.page,work_root=self.root/'rich')['route'],'legacy-refresh')
        self.page.write_text('---\nkind: paper\nslug: synthetic\ntags: [stub]\n---\nUnknown state.\n')
        with self.assertRaisesRegex(ValueError,'ambiguous-stub'):
            rr.route('synthetic',page=self.page,work_root=self.root/'ambiguous')

    def test_attempt_registration_requires_current_workflow(self):
        import initial_ingest as ii
        ii.plan('synthetic',page=self.page,work_root=self.work,identity=None)
        outside=self.root/'outside';outside.mkdir();pa.save(outside/'initial-plan.json',dict(requests=[]))
        with self.assertRaises(ValueError): ii.record_attempt(self.work,kind='source',path=outside)
        source=self.work/'source';source.mkdir();pa.save(source/'initial-plan.json',dict(requests=[]))
        with self.assertRaisesRegex(ValueError,'attempt-source-binding'):
            ii.record_attempt(self.work,kind='source',path=source)

    def test_source_continuations_use_bound_scope_and_never_approve(self):
        import initial_ingest as ii
        import pymupdf
        from unittest.mock import patch
        from pdf_source_package import preparation, gates, workflow
        ii.plan('synthetic',page=self.page,work_root=self.work,identity=None)
        pdf=self.root/'main.pdf'
        with pymupdf.open() as doc:
            doc.new_page().insert_text((40,40),'Synthetic manuscript');doc.save(pdf)
        source=dict(id='main',role='manuscript',format='pdf',path=str(pdf),sha256=pa.sha(pdf),filename='main.pdf',
            source_url='https://example.invalid/main.pdf',discovery_url='https://example.invalid/article',article_slug='synthetic',
            identity_verification=dict(status='operator-verified',basis='Synthetic test source'))
        pa.save(self.work/'acquisition.json',dict(schema='acquired-sources-v2',article=dict(slug='synthetic',title='Synthetic',doi=None,pmid=None,version='v1'),
            files=[source],attempts=[],obligations=dict(manuscript=dict(status='retrieved',file_ids=['main']),body=dict(status='missing',disposition='Unavailable',attempt_ids=[])),
            attachments=dict(status='none-listed',inspected_url='https://example.invalid/article',items=[]),
            processing=dict(policy='manuscript-only-v1',manuscript=dict(source_id='main',pages=[1],basis='Whole manuscript'))))
        value=ii.operate('initial-retain',self.work,application_endpoint='https://example.invalid/v1/chat/completions',max_application_posts=3)
        self.assertEqual(value['next_operation']['tool'],'paper_workflow')
        self.assertEqual(value['next_operation']['scope_path'],str(self.work/'retention/scope.json'))
        package=self.work/'source'
        with patch.object(preparation.classification,'reporting_disposition',return_value=dict(disposition='policy-excluded')):
            preparation.prepare(self.work/'retention/scope.json',package,fixture=True)
        gates.prepare_phase(package,'initial',None)
        for phase in ('classification','association'):
            value=ii.status(self.work)
            self.assertEqual(value['next_operation']['phase'],phase)
            self.assertEqual(value['next_operation']['operation'],'prepare-stage')
            self.assertNotIn('authorize_posts',value['next_operation'])
            workflow.prepare_stage(package,phase);gates.prepare_phase(package,phase,None)
        self.assertEqual(ii.status(self.work)['next_operation']['operation'],'report')
        self.assertEqual(ii.attempts(self.work)['source'],[str(package)])
        import shutil
        other=self.work/'other-source';shutil.copytree(package,other)
        changed=pa.load(other/'manifest.json');changed['documents'][0]['sha256']='0'*64
        (other/'manifest.json').write_text(__import__('json').dumps(changed))
        with self.assertRaisesRegex(ValueError,'attempt-source-binding'):
            ii.record_attempt(self.work,kind='source',path=other)
        self.assertEqual(ii.attempts(self.work)['source'],[str(package)])

    def test_remaining_continuations_keep_review_publication_and_active_job_gates(self):
        # Artifact boundaries are doubles here; source preparation and final archive
        # validation have separate real synthetic tests. No fixture is production.
        from unittest.mock import patch
        import initial_ingest as ii
        import operation_jobs as jobs
        from qualified_enrichment import runtime,reviews
        ii.plan('synthetic',page=self.page,work_root=self.work,identity=None)
        pa.save(self.work/'retention/retention.json',{})
        pa.save(self.work/'source/manifest.json',{})
        pa.save(self.work/'source-handoff/handoff.json',{})
        value=ii.status(self.work)
        self.assertEqual(value['next_step'],'enrichment-prepare')
        self.assertEqual(value['next_operation']['source_handoff'],str(self.work/'source-handoff/handoff.json'))
        pa.save(self.work/'enrichment-job/selection.json',{})
        with patch.object(runtime,'read_job',return_value=dict(selection=dict(selected=['synthetic']))),patch.object(ii,'record_attempt'):
            with patch.dict(os.environ,{'REENRICH_PROCESSOR_CACHE':str(self.root/'cache')}):
                value=ii.status(self.work)
                self.assertEqual(value['next_step'],'enrichment-seal')
                self.assertEqual(value['next_operation']['processor_cache'],str(self.root/'cache'))
            pa.save(self.work/'enrichment-job/enrichment/seal.json',{})
            value=ii.status(self.work)
            self.assertEqual(value['next_operation']['missing_inputs'],['approval','authorize_posts'])
            self.assertNotIn('authorize_posts',value['next_operation'])
            pa.save(self.work/'enrichment-job/enrichment/execution-start.json',{})
            self.assertEqual(ii.status(self.work)['next_step'],'review-create')
        review=self.work/'review';pa.save(review/'dossier.json',{})
        packet=dict(elements=['synthetic']);pa.save(review/'packet-1.json',packet)
        pa.save(review/'packets.json',dict(packets=[dict(path='packet-1.json')],source_inspection_required=[]))
        with patch.object(reviews,'verify',return_value={}),patch.object(reviews,'decisions',return_value=[]):
            value=ii.status(self.work)
            self.assertEqual(value['next_operation']['packet'],str(review/'packet-1.json'))
            self.assertEqual(value['next_operation']['missing_inputs'],['submission'])
        with patch.object(reviews,'verify',return_value={}),patch.object(reviews,'decisions',return_value=[dict(packet=packet)]),patch.object(ii.ae,'review_complete',return_value=True):
            self.assertEqual(ii.status(self.work)['next_step'],'export')
        pa.save(self.work/'export/handoff.json',{})
        self.assertEqual(ii.status(self.work)['next_step'],'initial-enriched-handoff')
        pa.save(self.work/'enriched-handoff/handoff.json',{})
        self.assertEqual(ii.status(self.work)['next_step'],'initial-finalize')
        pa.save(self.work/'final-products/manifest.json',{})
        value=ii.status(self.work)
        self.assertEqual(value['next_step'],'initial-publish')
        self.assertTrue(value['next_operation']['background'])
        attempt=Path(value['next_operation']['attempt_dir'])
        self.assertFalse(attempt.is_relative_to(self.work))
        pa.save(attempt/'job.json',{})
        for state in ('running','uncertain'):
            with patch.object(jobs,'status',return_value=dict(status=state)),patch.object(jobs,'load_job',return_value=(None,dict(identity=dict(kind='enrichment')))):
                self.assertEqual(ii.status(self.work)['next_operation']['operation'],'status')
        pa.save(attempt/'terminal.json',{})
        pa.save(self.work/'publication.json',{})
        value=ii.status(self.work)
        self.assertEqual(value['next_step'],'verify-ingest')
        self.assertFalse(value['production_complete'])
