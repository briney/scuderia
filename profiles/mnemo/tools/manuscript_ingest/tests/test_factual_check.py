from test_publication import Publication
from test_jobs import only_local_tests
from manuscript_ingest import workflow as w, requests, archive
from unittest.mock import patch
import json

class FactualCheck(Publication):
    def configure(self):
        cfg=w.config(self.runtime);cfg['factual_check']={'model':'fast-fixture','endpoint':'https://example.invalid','settings':{'max_tokens':131072}}
        w.save(self.runtime/'config.json',cfg)
    def test_one_independent_check_then_correction_without_legacy_context(self):
        self.page.write_text(self.page.read_text()+'\nLEGACY INTERPRETATION\n');j,_=self.ready();self.configure()
        draft=self.draft().replace('LEGACY INTERPRETATION','').replace('12 percent','120 percent')
        with patch.object(requests,'inspect_once',return_value={'status':'success','text':'Claim: 120 percent. Source: 12 percent. Fix: 12 percent.'}) as checker:
            out=w.stage(j,draft,'Central manuscript findings checked.',runtime_root=self.runtime)
            self.assertEqual(out['blocking_reason'],'factual-review-pending')
            self.assertNotIn('LEGACY INTERPRETATION',checker.call_args.kwargs['question'])
            self.assertEqual(checker.call_args.kwargs['images'],[])
            self.assertIn('P1:L1',checker.call_args.kwargs['question'])
            with self.assertRaisesRegex(ValueError,'factual-review-pending'):w.publish(j,1,runtime_root=self.runtime)
            out=w.stage(j,draft.replace('120 percent','12 percent'),'Assessed independent finding against source; corrected 120 to 12 percent.',runtime_root=self.runtime)
            self.assertEqual(out['status'],'ready');self.assertEqual(checker.call_count,1)
        manifest=archive.build(j,2,runtime_root=self.runtime)
        self.assertTrue((manifest.parent/'factual-check/outcome.json').exists())
        self.assertEqual(json.loads((manifest.parent/'factual-check/binding.json').read_text())['draft_sha256'],w.digest(draft))

    def test_failed_checker_is_reported_not_retried_or_clean(self):
        j,_=self.ready();self.configure()
        with patch.object(requests,'inspect_once',side_effect=TimeoutError) as checker:
            out=w.stage(j,self.draft(),'Manuscript checked; no known material issues.',runtime_root=self.runtime)
            again=w.stage(j,self.draft(),'Retained manuscript self-check; independent check unavailable.',runtime_root=self.runtime)
        self.assertEqual(checker.call_count,1)
        self.assertEqual(out['status'],'ready');self.assertEqual(again['status'],'ready')
        self.assertTrue(any('incomplete' in warning for warning in out['warnings']))
        self.assertEqual(out['artifacts']['factual_check']['status'],'uncertain')

def load_tests(loader,tests,pattern):return only_local_tests(__name__)

class ScannedEvidence(FactualCheck):
    def test_retained_transcription_reaches_checker_with_binding(self):
        from manuscript_ingest import sources
        import pymupdf
        path=self.root/'scan.pdf';doc=pymupdf.open();doc.new_page();doc.save(path);doc.close()
        j=w.start(self.page,runtime_root=self.runtime)['job_id']
        out=sources.prepare(j,[dict(path=str(path),role='manuscript',identity={'doi':'10.1234/synthetic'},basis='Verified manuscript identity')],runtime_root=self.runtime)
        sid=out['artifacts']['sources'][0]['source_id'];cfg=w.config(self.runtime)
        cfg['vision']={'model':'fixture','prompt':'Read','settings':{}};w.save(self.runtime/'config.json',cfg)
        job=w.load_job(j,self.runtime);job['authorization']['max_requests']=1;w.store_job(job,self.runtime)
        with patch.object(requests,'inspect_once',return_value={'status':'success','text':'Scanned result: measured effect was 12 percent.'}):
            sources.read(j,[dict(source_id=sid,page=1)],transcribe=True,runtime_root=self.runtime)
        self.configure()
        with patch.object(requests,'inspect_once',return_value={'status':'success','text':'No objective errors found.'}) as checker:
            w.stage(j,self.draft(),'Checked central claim against retained transcription.',runtime_root=self.runtime)
        self.assertIn('Scanned result: measured effect was 12 percent.',checker.call_args.kwargs['question'])
        self.assertIn('MODEL TRANSCRIPTION',checker.call_args.kwargs['question'])
