from test_review import Review
from manuscript_ingest import workflow as w, archive
from unittest.mock import patch
from pathlib import Path
import shutil

class MemoryTransport:
    objects={}; uploads=0; fail=False
    def __init__(self,*args):pass
    def upload(self,path,key,h,size):
        if self.fail:raise ValueError('synthetic-archive-outage')
        if key not in self.objects:self.objects[key]=path.read_bytes(); type(self).uploads+=1
        assert w.digest if self.objects[key]==path.read_bytes() else False
        return dict(key=key,sha256=h,size=size,method='read_back_sha256')
    def download(self,key,target,expected_hash=None,expected_size=None,**kwargs):
        target.write_bytes(self.objects[key]); assert not expected_hash or w.sha(target)==expected_hash
        return target

class Publication(Review):
    def setUp(self):
        super().setUp(); MemoryTransport.objects={}; MemoryTransport.uploads=0; MemoryTransport.fail=False
        cfg=w.config(self.runtime); cfg['archive']=dict(remote='fixture',bucket='fixture',prefix='article-packages'); w.save(self.runtime/'config.json',cfg)
    def staged(self):
        j,sid=self.ready(); w.stage(j,self.draft(),'Reviewed central finding against native manuscript page 1; no unresolved material issues.',runtime_root=self.runtime); return j
    def test_failure_retry_integration_and_refresh(self):
        j=self.staged(); original=self.page.read_bytes()
        with patch.object(archive.pa,'RcloneTransport',MemoryTransport),patch.object(w,'integration_check',return_value=['author-edge-missing']):
            MemoryTransport.fail=True
            r=w.publish(j,1,runtime_root=self.runtime); self.assertEqual(r['status'],'publication-pending'); self.assertEqual(self.page.read_bytes(),original)
            MemoryTransport.fail=False
            r=w.publish(j,1,runtime_root=self.runtime); self.assertEqual(r['status'],'integration-pending'); self.assertIn('needs-ingest: true',self.page.read_text())
            n=MemoryTransport.uploads
            with patch.object(w,'integration_check',return_value=[]): r=w.publish(j,1,runtime_root=self.runtime)
            self.assertEqual(r['status'],'complete'); self.assertEqual(MemoryTransport.uploads,n)
            self.assertIn('needs-ingest: false',self.page.read_text()); self.assertFalse((self.runtime/'requests.sqlite').exists())
            self.assertEqual(w.publish(j,1,runtime_root=self.runtime)['status'],'complete')
            refresh=w.start(self.page,runtime_root=self.runtime)['job_id']
            from manuscript_ingest import sources
            restored=sources.prepare(refresh,None,runtime_root=self.runtime)
            self.assertEqual(len(restored['artifacts']['sources']),2)
            self.assertIn('history',w.load_job(refresh,self.runtime))
    def test_stale_page_and_archive_snapshot(self):
        j=self.staged(); self.page.write_text(self.page.read_text()+'Human edit\n')
        with patch.object(archive.pa,'RcloneTransport',MemoryTransport),patch.object(w,'integration_check',return_value=[]):
            r=w.publish(j,1,runtime_root=self.runtime)
        self.assertEqual(r['status'],'held'); self.assertIn('Human edit',self.page.read_text())
        manifest=w.job_path(j,self.runtime)/'archives/1/manifest.json'; m=archive.verify(manifest)
        self.assertEqual(m['schema'],archive.SCHEMA)
        self.assertNotIn(w.sha(manifest),(manifest.parent/'page.md').read_text())
    def test_corrupt_candidate_refused(self):
        j=self.staged(); (w.job_path(j,self.runtime)/'drafts/1/page.md').write_text('bad edit')
        with self.assertRaisesRegex(ValueError,'changed'):
            archive.build(j,1,runtime_root=self.runtime)

from test_jobs import only_local_tests
def load_tests(loader,tests,pattern):return only_local_tests(__name__)

class Amendments(Publication):
    def test_completed_amendment_preserves_citations_and_old_archive(self):
        j,sid=self.ready(); annotated=self.draft()+'\nEvidence [P1:L1].\n'
        w.stage(j,annotated,'Checked the central result against page 1.',runtime_root=self.runtime)
        with patch.object(archive.pa,'RcloneTransport',MemoryTransport),patch.object(w,'integration_check',return_value=[]):
            w.publish(j,1,runtime_root=self.runtime)
            old=self.page.read_bytes(); manifest=w.job_path(j,self.runtime)/'archives/1/manifest.json'; before=w.sha(manifest)
            out=w.status(j,runtime_root=self.runtime)
            self.assertIn('live_snapshot',out['artifacts'])
            token=out['artifacts']['live_snapshot']['token']
            out=w.stage(j,annotated+'\nA qualified limitation.\n','Checked the amendment against page 1.',runtime_root=self.runtime,amend_revision=1,base_revision=token)
            self.assertEqual(out['status'],'ready'); self.assertEqual(self.page.read_bytes(),old)
            MemoryTransport.fail=True
            self.assertEqual(w.publish(j,2,runtime_root=self.runtime)['status'],'publication-pending')
            self.assertEqual(self.page.read_bytes(),old)
            MemoryTransport.fail=False
            self.assertEqual(w.publish(j,2,runtime_root=self.runtime)['status'],'complete')
            self.assertEqual(w.sha(manifest),before)
            evidence=__import__('json').loads(__import__('pathlib').Path(out['artifacts']['citations']).read_text())
            self.assertEqual(len(evidence['citations']),1)
            self.assertEqual(w.load_job(j,self.runtime)['published_revision'],2)

    def test_amendment_rejects_stale_snapshot_and_unacknowledged_publication(self):
        j=self.staged()
        with patch.object(archive.pa,'RcloneTransport',MemoryTransport),patch.object(w,'integration_check',return_value=[]):w.publish(j,1,runtime_root=self.runtime)
        out=w.status(j,runtime_root=self.runtime)
        self.assertIn('live_snapshot',out['artifacts']); token=out['artifacts']['live_snapshot']['token']
        with self.assertRaisesRegex(ValueError,'amend'):
            w.stage(j,self.draft(),'Checked against page 1.',runtime_root=self.runtime,base_revision=token)
        self.page.write_text(self.page.read_text()+'Human annotation\n')
        with self.assertRaisesRegex(ValueError,'stale'):
            w.stage(j,self.draft(),'Checked against page 1.',runtime_root=self.runtime,amend_revision=1,base_revision=token)
        out=w.status(j,runtime_root=self.runtime)
        self.assertEqual(out['status'],'held')
        with self.assertRaisesRegex(ValueError,'amend'):
            w.stage(j,self.draft(),'Checked against page 1.',runtime_root=self.runtime,amend_revision=2,base_revision=out['artifacts']['live_snapshot']['token'])
