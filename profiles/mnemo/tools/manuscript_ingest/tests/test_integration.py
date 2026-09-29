from test_publication import Publication, MemoryTransport
from manuscript_ingest import workflow as w, archive
from unittest.mock import patch
from pathlib import Path
import yaml

class Integration(Publication):
    def complete_draft(self):
        return self.draft().replace('needs-ingest: true','needs-ingest: true\nvenue: Journal\nyear: 2026\nstatus: published\nauthors: []\nfulltext_source: native-pdf')+''.join('\n## '+s+'\nSource-backed fixture.\n' for s in ('Abstract','Context','Approach','Analysis','Citation','Ingest log'))

    def test_stage_returns_missing_fields_and_edges_without_network(self):
        j,_=self.ready()
        draft=self.complete_draft().replace('fulltext_source: native-pdf\n','').replace('authors: []','authors: [people/missing]')
        with patch('subprocess.run',side_effect=AssertionError('staging must stay local')):
            out=w.stage(j,draft,'Central facts checked against manuscript.',runtime_root=self.runtime)
        issues=out['artifacts'].get('integration_obligations',[])
        self.assertTrue(any('fulltext_source' in i for i in issues))
        self.assertTrue(any('people/missing' in i for i in issues))
        self.assertTrue(all('bibliograph' not in i for i in issues))

    def test_one_publish_records_event_and_retry_does_not_duplicate(self):
        j,_=self.ready();w.stage(j,self.complete_draft(),'Central facts checked against manuscript.',runtime_root=self.runtime)
        with patch.object(archive.pa,'RcloneTransport',MemoryTransport),patch.object(w,'integration_check',return_value=[]):
            out=w.publish(j,1,runtime_root=self.runtime)
            self.assertEqual(out['status'],'complete')
            inbox=self.brain/'docs/rem-cycle/inbox.yaml'
            self.assertTrue(inbox.exists())
            before=inbox.read_bytes();w.publish(j,1,runtime_root=self.runtime)
            self.assertEqual(inbox.read_bytes(),before)
            rows=yaml.safe_load(before)['items'];self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]['page'],'papers/paper')
            self.assertIn(j,rows[0]['id'])

    def test_missing_provenance_stops_before_upload(self):
        j,_=self.ready();w.stage(j,self.complete_draft().replace('fulltext_source: native-pdf\n',''),'Central facts checked against manuscript.',runtime_root=self.runtime)
        with patch.object(archive.pa,'RcloneTransport',MemoryTransport):out=w.publish(j,1,runtime_root=self.runtime)
        self.assertEqual(MemoryTransport.uploads,0)
        self.assertEqual(out['status'],'ready')
        self.assertTrue(any('fulltext_source' in i for i in out['artifacts']['integration_obligations']))

    def test_failed_archive_does_not_emit_event(self):
        j,_=self.ready();w.stage(j,self.complete_draft(),'Central facts checked against manuscript.',runtime_root=self.runtime)
        MemoryTransport.fail=True
        with patch.object(archive.pa,'RcloneTransport',MemoryTransport):out=w.publish(j,1,runtime_root=self.runtime)
        self.assertEqual(out['status'],'publication-pending')
        self.assertFalse((self.brain/'docs/rem-cycle/inbox.yaml').exists())

    def test_interrupted_event_retries_without_upload_and_preserves_inbox(self):
        j,_=self.ready();w.stage(j,self.complete_draft(),'Central facts checked against manuscript.',runtime_root=self.runtime)
        inbox=self.brain/'docs/rem-cycle/inbox.yaml';inbox.parent.mkdir(parents=True)
        before='# Human note\nversion: 1\nitems:\n  - id: existing\n    page: papers/other\n    event: ingest\n# Keep this comment\nother: retained\n'
        inbox.write_text(before)
        with patch.object(archive.pa,'RcloneTransport',MemoryTransport),patch.object(w,'integration_check',return_value=[]):
            with patch.object(w,'record_event',side_effect=OSError('interrupted')):
                out=w.publish(j,1,runtime_root=self.runtime)
            self.assertEqual(out['status'],'integration-pending')
            self.assertTrue(w.page_metadata(self.page.read_text())['needs-ingest'])
            self.assertEqual(inbox.read_text(),before)
            uploads=MemoryTransport.uploads
            self.assertEqual(w.publish(j,1,runtime_root=self.runtime)['status'],'complete')
            self.assertEqual(MemoryTransport.uploads,uploads)
            self.assertIn('# Human note',inbox.read_text());self.assertIn('# Keep this comment',inbox.read_text())
            data=yaml.safe_load(inbox.read_text());self.assertEqual(data['other'],'retained');self.assertEqual(len(data['items']),2)

    def test_concurrent_edit_during_verification_emits_no_event(self):
        j,_=self.ready();w.stage(j,self.complete_draft(),'Central facts checked against manuscript.',runtime_root=self.runtime)
        def check(*a,**k):
            if k.get('canonical',True):self.page.write_text(self.page.read_text()+'Human edit\n')
            return []
        with patch.object(archive.pa,'RcloneTransport',MemoryTransport),patch.object(w,'integration_check',side_effect=check):
            with self.assertRaisesRegex(ValueError,'concurrent-page-edit'):w.publish(j,1,runtime_root=self.runtime)
        self.assertIn('Human edit',self.page.read_text());self.assertFalse((self.brain/'docs/rem-cycle/inbox.yaml').exists())


    def test_external_links_are_not_missing_local_targets(self):
        j,_=self.ready()
        out=w.stage(j,self.complete_draft().replace('authors: []','authors: []\nlinks: [https://example.org/source]'),'Checked manuscript and external attribution.',runtime_root=self.runtime)
        self.assertEqual(out['artifacts']['integration_obligations'],[])


from test_jobs import only_local_tests
def load_tests(loader,tests,pattern):return only_local_tests(__name__)

class FlowInbox(Integration):
    def test_flow_sequence_comments_survive_append(self):
        j,_=self.ready();job=w.load_job(j,self.runtime);job['revision']=1
        inbox=self.brain/'docs/rem-cycle/inbox.yaml';inbox.parent.mkdir(parents=True)
        for trailing in ('',','):
            inbox.write_text('items: [\n {id: old, page: papers/old, event: ingest}'+trailing+' # Human rationale\n]\n')
            w.record_event(job,w.config(self.runtime),self.runtime)
            self.assertIn('# Human rationale',inbox.read_text())
            self.assertEqual(len(yaml.safe_load(inbox.read_text())['items']),2)
