from test_publication import Publication, MemoryTransport
from manuscript_ingest import workflow as w, archive, sources
from unittest.mock import patch

class Boundaries(Publication):
    def test_restage_after_integration_hold(self):
        j=self.staged()
        with patch.object(archive.pa,'RcloneTransport',MemoryTransport),patch.object(w,'integration_check',return_value=['bibliography decision missing']):
            w.publish(j,1,runtime_root=self.runtime)
            revised=w.stage(j,self.draft()+'\nBibliography: no new load-bearing references.\n','Reviewed page 1; added explicit bibliography disposition.',runtime_root=self.runtime)
            self.assertEqual(revised['artifacts']['revision'],2)
            with patch.object(w,'integration_check',return_value=[]):out=w.publish(j,2,runtime_root=self.runtime)
            self.assertEqual(out['status'],'complete')
    def test_restart_between_archive_and_apply(self):
        j=self.staged(); original=self.page.read_bytes()
        with patch.object(archive.pa,'RcloneTransport',MemoryTransport),patch.object(w,'integration_check',return_value=[]):
            with patch.object(w,'apply_bytes',side_effect=OSError('interrupted')):
                with self.assertRaises(OSError):w.publish(j,1,runtime_root=self.runtime)
            self.assertEqual(original,self.page.read_bytes()); uploads=MemoryTransport.uploads
            self.assertEqual(w.publish(j,1,runtime_root=self.runtime)['status'],'complete')
            self.assertEqual(MemoryTransport.uploads,uploads)
    def test_preserve_original_citation_and_provenance(self):
        self.page.write_text(self.page.read_text().replace('needs-ingest: true','needs-ingest: true\ncited_by: [papers/citing]\nstub_source: source-seed\ningest_attempts: 2'))
        j,sid=self.ready()
        bad=self.draft().replace('cited_by: [papers/citing]','cited_by: []')
        with self.assertRaisesRegex(ValueError,'citing'):
            w.stage(j,bad,'Reviewed the central finding against page 1.',runtime_root=self.runtime)
    def test_unresolved_source_alias_is_not_guessed(self):
        j,sid=self.ready()
        with self.assertRaisesRegex(ValueError,'unresolved-source'):
            w.stage(j,self.draft()+'[source:unknown:1]','Checked central result against manuscript page 1.',runtime_root=self.runtime)
    def test_refresh_reuses_pinned_local_archive(self):
        j=self.staged(); manifest=archive.build(j,1,runtime_root=self.runtime)
        with patch.object(archive.pa,'RcloneTransport',MemoryTransport):
            pub=archive.publish(manifest,destination=w.config(self.runtime)['archive'])
        receipt=self.root/'receipt.json'; w.save(receipt,pub)
        with patch.object(archive.pa,'RcloneTransport',side_effect=AssertionError('network not needed')):
            restored=archive.open_sources(receipt,self.root/'restored',cache={w.sha(manifest):str(manifest)})
        self.assertEqual(restored['identity']['doi'],'10.1234/synthetic')

from test_jobs import only_local_tests
def load_tests(loader,tests,pattern):return only_local_tests(__name__)
