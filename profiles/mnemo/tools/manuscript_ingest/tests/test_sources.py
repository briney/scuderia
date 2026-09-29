from test_jobs import Jobs
from manuscript_ingest import workflow, sources
import json

class Sources(Jobs):
    def inputs(self, scanned=False):
        import pymupdf
        pdf=self.root/'Manuscript α with spaces.pdf'; doc=pymupdf.open(); page=doc.new_page()
        if not scanned: page.insert_text((40,40),'Synthetic experiment. The measured effect was 12 percent.')
        doc.save(pdf); doc.close()
        supplement=self.root/'Supplement.txt'; supplement.write_text('DO NOT PROCESS THIS SUPPLEMENT')
        return [dict(path=str(pdf),role='manuscript',identity={'doi':'10.1234/synthetic'},basis='Title and DOI verified against the manuscript.'),dict(path=str(supplement),role='supplement')]
    def test_retention_read_and_scope(self):
        j=workflow.start(self.page,runtime_root=self.runtime)['job_id']
        r=sources.prepare(j,self.inputs(),runtime_root=self.runtime)
        index=r['artifacts']['sources']; main=next(x for x in index if x['role']=='manuscript'); supp=next(x for x in index if x['role']=='supplement')
        self.assertEqual(main['pages'],1); self.assertNotIn('pages',supp)
        read=sources.read(j,[dict(source_id=main['source_id'],page=1)],runtime_root=self.runtime)
        self.assertIn('12 percent',read['artifacts']['locations'][0]['text'])
        with self.assertRaisesRegex(ValueError,'out-of-scope'):
            sources.read(j,[dict(source_id=supp['source_id'],page=1)],runtime_root=self.runtime)
        self.assertFalse((self.runtime/'requests.sqlite').exists())
        again=sources.prepare(j,None,runtime_root=self.runtime)
        self.assertEqual(again['artifacts']['sources'],index)
    def test_scan_and_missing_optional_source(self):
        j=workflow.start(self.page,runtime_root=self.runtime)['job_id']; rows=self.inputs(True)
        rows.append(dict(path=str(self.root/'missing.pdf'),role='supplement'))
        r=sources.prepare(j,rows,runtime_root=self.runtime)
        self.assertTrue(r['warnings']); self.assertEqual(r['artifacts']['sources'][0]['deficient_pages'],[1])
    def test_wrong_identity_blocks(self):
        j=workflow.start(self.page,runtime_root=self.runtime)['job_id']; rows=self.inputs(); rows[0]['identity']['doi']='10.9999/wrong'
        with self.assertRaisesRegex(ValueError,'identity'):
            sources.prepare(j,rows,runtime_root=self.runtime)
    def test_bounded_read_continuation(self):
        j=workflow.start(self.page,runtime_root=self.runtime)['job_id']; r=sources.prepare(j,self.inputs(),runtime_root=self.runtime)
        sid=r['artifacts']['sources'][0]['source_id']
        a=sources.read(j,[dict(source_id=sid,page=1,max_chars=10)],runtime_root=self.runtime)['artifacts']['locations'][0]
        self.assertTrue(a['partial']); self.assertEqual(a['next_start'],10)

from test_jobs import only_local_tests
def load_tests(loader,tests,pattern):return only_local_tests(__name__)

class SupplementAppend(Sources):
    def test_retention_only_append_preserves_reads_and_is_idempotent(self):
        from unittest.mock import patch
        j=workflow.start(self.page,runtime_root=self.runtime)['job_id']; sources.prepare(j,self.inputs(),runtime_root=self.runtime)
        job=workflow.load_job(j,self.runtime); sid=job['sources'][0]['source_id']
        sources.read(j,[dict(source_id=sid,page=1)],runtime_root=self.runtime)
        before=workflow.load_job(j,self.runtime)['reads']; extra=self.root/'extra.xml'; extra.write_text('<extra>retention only</extra>')
        with patch.object(sources,'text_pages',side_effect=AssertionError('no extraction')):
            for _ in range(2):out=sources.prepare(j,runtime_root=self.runtime,supplement_inputs=[dict(path=str(extra),role='supplement')])
        self.assertEqual(len(out['artifacts']['sources']),3)
        self.assertEqual(workflow.load_job(j,self.runtime)['reads'],before)
        with self.assertRaisesRegex(ValueError,'supplement'):
            sources.prepare(j,runtime_root=self.runtime,supplement_inputs=[dict(path=str(extra),role='manuscript')])
