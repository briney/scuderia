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

class FileStage(Publication):
    def test_long_markdown_file_stages_exact_annotated_bytes(self):
        from manuscript_ingest.cli import dispatch
        j,sid=self.ready()
        raw=self.draft()+('\nQuoted "value", backslash \\, unicode µL.\n'*2000)
        path=self.root/'draft.md'; path.write_text(raw)
        out=dispatch(dict(operation='stage',job_id=j,markdown_path=str(path),review_note='Checked central findings against page 1.'),runtime_root=self.runtime)
        self.assertEqual(__import__('pathlib').Path(out['artifacts']['annotated_draft']).read_text(),raw)
        self.assertEqual(out['artifacts']['revision'],1)

    def test_file_stage_rejects_ambiguous_and_unsafe_inputs(self):
        from manuscript_ingest.cli import dispatch
        j,sid=self.ready(); path=self.root/'draft.md'; path.write_text(self.draft())
        base=dict(operation='stage',job_id=j,review_note='Checked central findings against page 1.')
        link=self.root/'link.md'; link.symlink_to(path)
        big=self.root/'big.md'; big.write_text('a'*2_000_001)
        for args in ({},dict(markdown=self.draft(),markdown_path=str(path)),dict(markdown_path=str(self.page)),
                     dict(markdown_path=str(link)),dict(markdown_path=str(self.root)),dict(markdown_path=str(big)),dict(markdown_path=str(self.root/'missing'))):
            with self.subTest(args=list(args)):
                with self.assertRaises((ValueError,OSError)):dispatch(dict(base,**args),runtime_root=self.runtime)
        self.assertEqual(w.load_job(j,self.runtime)['revision'],0)

class SourceReuse(Publication):
    def test_reuse_restores_sources_not_old_enrichment_or_page_products(self):
        j=self.staged(); manifest=archive.build(j,1,runtime_root=self.runtime)
        with patch.object(archive.pa,'RcloneTransport',MemoryTransport):
            pub=archive.publish(manifest,destination=w.config(self.runtime)['archive']); receipt=self.root/'receipt.json'; w.save(receipt,pub)
            restored=archive.open_sources(receipt,self.root/'selected',transport=w.config(self.runtime)['archive'])
            self.assertEqual(len(restored['inputs']),2)
            self.assertFalse((self.root/'selected/page.md').exists())
            self.assertFalse((self.root/'selected/review.txt').exists())
            with patch.object(MemoryTransport,'download',side_effect=AssertionError('repeat download')):
                archive.open_sources(receipt,self.root/'selected',transport=w.config(self.runtime)['archive'])
            first=__import__('pathlib').Path(restored['inputs'][0]['path']); first.write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError,'corrupt'):
                archive.open_sources(receipt,self.root/'selected',transport=w.config(self.runtime)['archive'])

class CachedRecovery(Publication):
    def test_interrupted_cached_copy_retries_without_completed_corruption(self):
        import shutil
        j=self.staged(); manifest=archive.build(j,1,runtime_root=self.runtime); target=self.root/'cached'
        real=shutil.copyfile
        def fail(source,destination,*args,**kwargs):
            __import__('pathlib').Path(destination).write_bytes(b'partial');raise OSError('interrupted copy')
        with patch.object(shutil,'copyfile',side_effect=fail):
            with self.assertRaises(OSError):archive.open_sources(manifest,target)
        self.assertEqual(len(archive.open_sources(manifest,target)['inputs']),2)
        other=self.root/'cached-source'
        def fail_object(source,destination,*args,**kwargs):
            if __import__('pathlib').Path(source).name!='manifest.json':return fail(source,destination)
            return real(source,destination,*args,**kwargs)
        with patch.object(shutil,'copyfile',side_effect=fail_object):
            with self.assertRaises(OSError):archive.open_sources(manifest,other)
        self.assertEqual(len(archive.open_sources(manifest,other)['inputs']),2)

class ExactFileBytes(Publication):
    def test_crlf_annotated_file_bytes_are_preserved(self):
        from manuscript_ingest.cli import dispatch
        j,sid=self.ready();raw=self.draft().replace('\n','\r\n').encode();path=self.root/'windows.md';path.write_bytes(raw)
        out=dispatch(dict(operation='stage',job_id=j,markdown_path=str(path),review_note='Checked central findings against page 1.'),runtime_root=self.runtime)
        self.assertEqual(__import__('pathlib').Path(out['artifacts']['annotated_draft']).read_bytes(),raw)
