from test_sources import Sources
from manuscript_ingest import workflow as w, sources, requests
from unittest.mock import patch
import json

class Review(Sources):
    def ready(self):
        j=w.start(self.page,runtime_root=self.runtime)['job_id']; out=sources.prepare(j,self.inputs(),runtime_root=self.runtime)
        sid=out['artifacts']['sources'][0]['source_id']; sources.read(j,[dict(source_id=sid,page=1)],runtime_root=self.runtime)
        return j,sid
    def draft(self):
        return self.page.read_text()+'\n## Findings\nThe measured effect was 12 percent.\n\n## Limitations\nOnly a synthetic experiment.\n'
    def test_revisions_preserve_evidence_and_live_page(self):
        j,sid=self.ready(); original=self.page.read_bytes()
        a=w.stage(j,self.draft(),'Checked central finding and 12 percent against manuscript page 1. No material issues; optional figure not used.',runtime_root=self.runtime)
        b=w.stage(j,self.draft().replace('12 percent','approximately 12 percent'),'Checked the qualified value against manuscript page 1; no contradictions.',runtime_root=self.runtime)
        self.assertEqual(a['status'],'ready'); self.assertEqual(b['artifacts']['revision'],2)
        self.assertEqual(self.page.read_bytes(),original); self.assertFalse((self.runtime/'requests.sqlite').exists())
    def test_identity_and_material_hold(self):
        j,sid=self.ready()
        with self.assertRaisesRegex(ValueError,'identity'):
            w.stage(j,self.draft().replace('10.1234/synthetic','10.1234/other'),'Reviewed page 1.',runtime_root=self.runtime)
        held=w.stage(j,self.draft().replace('12 percent','120 percent'),'HOLD: 120 percent is unsupported by manuscript page 1, which reports 12 percent.',runtime_root=self.runtime)
        self.assertEqual(held['status'],'held')
        corrected=w.stage(j,self.draft(),'Corrected central number to 12 percent from manuscript page 1. No remaining material issue.',runtime_root=self.runtime)
        self.assertEqual(corrected['status'],'ready')
    def test_optional_truncation_and_no_repeat(self):
        j,sid=self.ready(); job=w.load_job(j,self.runtime); job['authorization']['max_requests']=1; w.store_job(job,self.runtime)
        cfg=w.config(self.runtime); cfg['vision']={'model':'fixture','settings':{},'prompt':'Inspect only supplied pages.'}; w.save(self.runtime/'config.json',cfg)
        raw={'status':'partial','text':'Legible axis reads 12%. Incomplete annotation {','usage':{'total_tokens':10}}
        with patch.object(requests,'inspect_once',return_value=raw) as post:
            a=sources.inspect(j,[dict(source_id=sid,page=1)],'Read the axis',runtime_root=self.runtime)
            b=sources.inspect(j,[dict(source_id=sid,page=1)],'Read the axis',runtime_root=self.runtime)
            self.assertEqual(post.call_count,1); self.assertEqual(a['artifacts']['inspection']['status'],'partial')
            self.assertEqual(a['artifacts']['inspection'],b['artifacts']['inspection'])
        staged=w.stage(j,self.draft(),'Central finding checked against native page 1. Incomplete optional annotation omitted.',runtime_root=self.runtime)
        self.assertEqual(staged['status'],'ready')
