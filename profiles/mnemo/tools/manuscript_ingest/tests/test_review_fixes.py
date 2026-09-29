from test_publication import Publication, MemoryTransport
from manuscript_ingest import workflow as w, archive, sources, requests
from article_archive_compat import reader
from unittest.mock import patch
from pathlib import Path
import importlib.util
import json
import os


class ReviewFixes(Publication):
    def test_start_snapshot_binds_exact_bytes(self):
        original=self.page.read_bytes(); parse=w.page_metadata
        def edit_after_read(text):
            self.page.write_bytes(original+b'Human note added during start.\n')
            return parse(text)
        with patch.object(w,'page_metadata',side_effect=edit_after_read):
            j=w.start(self.page,runtime_root=self.runtime)['job_id']
        job=w.load_job(j,self.runtime); snapshot=w.job_path(j,self.runtime)/'original.md'
        self.assertEqual(snapshot.read_bytes(),original)
        self.assertEqual(job['original_sha256'],w.sha(snapshot))
        self.assertNotEqual(job['original_sha256'],w.sha(self.page))

    def test_reconcile_concurrent_edit_before_and_after_apply(self):
        for applied in (False,True):
            with self.subTest(applied=applied):
                if applied:
                    self.tearDown(); self.setUp()
                j=self.staged()
                with patch.object(archive.pa,'RcloneTransport',MemoryTransport),patch.object(w,'integration_check',side_effect=lambda *a,**k: ['missing edge'] if k.get('canonical',True) else []):
                    if applied:w.publish(j,1,runtime_root=self.runtime)
                    self.page.write_text(self.page.read_text()+'Human note to preserve.\n')
                    held=w.publish(j,1,runtime_root=self.runtime)
                    self.assertEqual(held['status'],'held')
                    snapshot=held['artifacts']['live_snapshot']
                    self.assertEqual(Path(snapshot['path']).read_bytes(),self.page.read_bytes())
                    candidate=self.page.read_text()+'\nBibliography: reviewed.\n'
                    revision=w.stage(j,candidate,'Reviewed manuscript and preserved the human note.',base_revision=snapshot['token'],runtime_root=self.runtime)['artifacts']['revision']
                    with patch.object(w,'integration_check',return_value=[]):
                        self.assertEqual(w.publish(j,revision,runtime_root=self.runtime)['status'],'complete')
                    self.assertIn('Human note to preserve.',self.page.read_text())
                    self.assertEqual(w.load_job(j,self.runtime)['job_id'],j)

    def test_reconciliation_rejects_stale_token(self):
        j=self.staged(); self.page.write_text(self.page.read_text()+'First edit\n')
        held=w.status(j,runtime_root=self.runtime)
        snapshot=held['artifacts']['live_snapshot']
        self.page.write_text(self.page.read_text()+'Second edit\n')
        with self.assertRaisesRegex(ValueError,'stale-live-snapshot'):
            w.stage(j,self.draft(),'Reviewed source and first edit.',base_revision=snapshot['token'],runtime_root=self.runtime)

    def test_stage_recovers_interrupted_revision(self):
        j,sid=self.ready(); save=w.save
        def interrupt(path,value):
            if Path(path).name=='revision.json':raise OSError('interrupted')
            return save(path,value)
        with patch.object(w,'save',side_effect=interrupt):
            with self.assertRaises(OSError):w.stage(j,self.draft(),'Reviewed manuscript page 1.',runtime_root=self.runtime)
        staged=w.stage(j,self.draft(),'Reviewed manuscript page 1.',runtime_root=self.runtime)
        self.assertEqual(staged['status'],'ready')
        # Also recover a completed draft whose job-state commit was interrupted.
        with patch.object(w,'store_job',side_effect=OSError('interrupted state save')):
            with self.assertRaises(OSError):w.stage(j,self.draft(),'Reviewed manuscript page 1 again.',runtime_root=self.runtime)
        preserved={p:w.sha(p) for p in (w.job_path(j,self.runtime)/'drafts').glob('*/revision.json')}
        staged=w.stage(j,self.draft(),'Reviewed manuscript page 1 again.',runtime_root=self.runtime)
        self.assertEqual(staged['status'],'ready')
        self.assertTrue(all(w.sha(p)==h for p,h in preserved.items()))

    def test_focused_inspection_is_not_full_read(self):
        j=w.start(self.page,runtime_root=self.runtime)['job_id']
        out=sources.prepare(j,self.inputs(),runtime_root=self.runtime); sid=out['artifacts']['sources'][0]['source_id']
        job=w.load_job(j,self.runtime); job['authorization']['max_requests']=1; w.store_job(job,self.runtime)
        cfg=w.config(self.runtime); cfg['vision']={'model':'fixture','prompt':'Inspect only supplied pages.'}; w.save(self.runtime/'config.json',cfg)
        with patch.object(requests,'inspect_once',return_value={'status':'success','text':'Axis: 12%'}):
            sources.inspect(j,[dict(source_id=sid,page=1)],'Read only the axis label',runtime_root=self.runtime)
        with self.assertRaisesRegex(ValueError,'read-entire-manuscript'):
            w.stage(j,self.draft(),'Central result checked against page 1.',runtime_root=self.runtime)

    def test_scanned_manuscript_uses_explicit_full_page_transcription(self):
        j=w.start(self.page,runtime_root=self.runtime)['job_id']
        out=sources.prepare(j,self.inputs(scanned=True),runtime_root=self.runtime); sid=out['artifacts']['sources'][0]['source_id']
        job=w.load_job(j,self.runtime); job['authorization']['max_requests']=1; w.store_job(job,self.runtime)
        cfg=w.config(self.runtime); cfg['vision']={'model':'fixture','prompt':'Read supplied pages.'}; w.save(self.runtime/'config.json',cfg)
        with patch.object(requests,'inspect_once',return_value={'status':'success','text':'Synthetic manuscript complete transcription: measured effect 12 percent.'}) as call:
            sources.read(j,[dict(source_id=sid,page=1)],transcribe=True,runtime_root=self.runtime)
            self.assertIn('entire',call.call_args.kwargs['question'])
        self.assertEqual(w.stage(j,self.draft(),'Reviewed central result against full-page transcription.',runtime_root=self.runtime)['status'],'ready')

    def test_restore_recovers_interrupted_download(self):
        j=self.staged(); manifest=archive.build(j,1,runtime_root=self.runtime)
        with patch.object(archive.pa,'RcloneTransport',MemoryTransport):
            pub=archive.publish(manifest,destination=w.config(self.runtime)['archive'])
        receipt=self.root/'receipt.json'; w.save(receipt,pub); target=self.root/'restored'
        class Interrupted(MemoryTransport):
            def download(self,key,target,*args,**kwargs):
                target.write_bytes(b'partial'); raise OSError('interrupted')
        with patch.object(archive.pa,'RcloneTransport',Interrupted):
            with self.assertRaises(OSError):archive.open_sources(receipt,target,transport=w.config(self.runtime)['archive'])
        with patch.object(archive.pa,'RcloneTransport',MemoryTransport):
            result=archive.open_sources(receipt,target,transport=w.config(self.runtime)['archive'])
        self.assertEqual(result['identity']['doi'],'10.1234/synthetic')
        # Completed corruption is evidence, not a reason to silently replace it.
        Path(result['inputs'][0]['path']).write_text('corrupt retained original')
        with patch.object(archive.pa,'RcloneTransport',side_effect=AssertionError('no redownload of completed corruption')):
            with self.assertRaisesRegex(ValueError,'corrupt-restored-source'):
                archive.open_sources(receipt,target,transport=w.config(self.runtime)['archive'])

    def test_source_retention_recovers_interrupted_copy(self):
        j=w.start(self.page,runtime_root=self.runtime)['job_id']; inputs=self.inputs()
        def interrupted(source,target):
            Path(target).write_bytes(b'partial'); raise OSError('interrupted')
        with patch.object(sources.shutil,'copyfile',side_effect=interrupted):
            with self.assertRaises(OSError):sources.prepare(j,inputs,runtime_root=self.runtime)
        out=sources.prepare(j,inputs,runtime_root=self.runtime)
        self.assertEqual(out['status'],'working')

    def test_real_transport_never_exposes_partial_download(self):
        target=self.root/'object'
        def broken(argv,output=None,**kwargs):
            output.write(b'partial'); raise OSError('interrupted')
        transport=archive.pa.RcloneTransport('fixture','fixture',runner=broken)
        with self.assertRaises(OSError):transport.download('object',target)
        self.assertFalse(target.exists())

    def test_historical_restore_retries_without_exposing_partial_directory(self):
        receipt=self.root/'legacy.json'; w.save(receipt,{'schema':'portable-article-manifest-v3'})
        target=self.root/'historical'
        def interrupted(receipt,destination):
            destination.mkdir(); (destination/'partial').write_text('partial'); raise OSError('interrupted')
        with patch.object(reader.pa,'restore',side_effect=interrupted):
            with self.assertRaises(OSError):reader.restore(receipt,target)
        self.assertFalse(target.exists())

    def test_replacement_inputs_preserve_prior_history(self):
        j=self.staged()
        with patch.object(archive.pa,'RcloneTransport',MemoryTransport),patch.object(w,'integration_check',return_value=[]):
            w.publish(j,1,runtime_root=self.runtime)
            prior=w.load_job(j,self.runtime); prior_manifest=w.job_path(j,self.runtime)/'archives/1/manifest.json'
            refresh=w.start(self.page,runtime_root=self.runtime)['job_id']
            replacement=self.root/'replacement.txt'; replacement.write_text('Replacement native manuscript body. The measured effect was 12 percent.')
            out=sources.prepare(refresh,[dict(path=str(replacement),role='manuscript',identity={'doi':'10.1234/synthetic'},basis='Verified same article and version against manuscript.')],runtime_root=self.runtime)
            sid=out['artifacts']['sources'][0]['source_id']; sources.read(refresh,[dict(source_id=sid,page=1)],runtime_root=self.runtime)
            w.stage(refresh,self.draft(),'Reviewed source replacement against manuscript identity and original claims.',runtime_root=self.runtime)
            manifest=archive.build(refresh,1,runtime_root=self.runtime)
        provenance=json.loads((manifest.parent/'provenance.json').read_text())
        self.assertEqual(provenance['history']['manifest_sha256'],w.sha(prior_manifest))
        self.assertEqual((manifest.parent/'original.md').read_text(),(w.job_path(refresh,self.runtime)/'original.md').read_text())

    def test_real_integration_checker_requires_edges_not_page_bookkeeping(self):
        import subprocess
        self.page.write_text(self.page.read_text().replace('needs-ingest: true','needs-ingest: true\nvenue: Synthetic journal\nyear: 2026\nstatus: published\nauthors: [people/synthetic-author]\nfulltext_source: native-pdf')+
            ''.join('\n## '+name+'\nSource-backed fixture.\n' for name in ('Abstract','Context','Approach','Findings','Limitations','Analysis','Citation','Ingest log'))+'\nBibliography: no new references.\n')
        j=w.start(self.page,runtime_root=self.runtime)['job_id']; job=w.load_job(j,self.runtime)
        (self.brain/'people').mkdir(); ledger=self.brain/'people/_ledger.yaml'
        ledger.write_text('entries:\n  - slug: synthetic-author\n    citations: [papers/paper]\n')
        inbox=self.brain/'docs/rem-cycle/inbox.yaml'; inbox.parent.mkdir(parents=True)
        inbox.write_text('items:\n  - page: papers/paper\n    event: ingest\n')
        # Only canonical network verification is doubled; run real contract/edge checks.
        with patch.object(subprocess,'run',return_value=subprocess.CompletedProcess([],0,stdout='',stderr='')) as canonical:
            self.assertEqual(w.integration_check(job,w.config(self.runtime)),[])
            self.assertIn('--instance',canonical.call_args.args[0])
            ledger.write_text('entries: []\n'); inbox.write_text('items: []\n')
            self.assertEqual(w.integration_check(job,w.config(self.runtime)),[])
            issues=w.graph_follow_up(job,w.config(self.runtime))
            self.assertIn('author-edge-missing:people/synthetic-author',issues)
            self.assertNotIn('propagation-event-missing',issues)
            self.assertFalse(any('bibliograph' in issue for issue in issues))

    def test_encoded_credentials_are_not_retained(self):
        client_path=Path(requests.__file__).resolve().parents[2]/'skills/paper-ingest/scripts/paper-vision/client.py'
        spec=importlib.util.spec_from_file_location('_fixture_transport',client_path); client=importlib.util.module_from_spec(spec); spec.loader.exec_module(client)
        secret='fixture-secret'; escaped=''.join('\\u%04x'%ord(c) for c in secret)
        raw=json.dumps({'model':'fixture','choices':[{'message':{'content':secret},'finish_reason':'stop'}],'usage':{'echo':secret}}).replace(secret,escaped).encode()
        client.post=lambda *a:(200,raw)
        with patch.dict(os.environ,TEST_INSPECTION_KEY=secret),patch.object(importlib.util,'module_from_spec',return_value=client),patch.object(spec.loader.__class__,'exec_module',return_value=None):
            result=requests.inspect_once(images=[],question='Read page',configuration={'credential_env':'TEST_INSPECTION_KEY','model':'fixture','prompt':'Read','endpoint':'https://invalid.example'},output=self.root/'response')
        self.assertNotIn(secret,json.dumps(result))
        for path in (self.root/'response').iterdir():
            if path.suffix=='.json':self.assertNotIn(secret,json.dumps(json.loads(path.read_text())))
        self.assertEqual(result['text'],'[REDACTED]')

from test_jobs import only_local_tests
def load_tests(loader,tests,pattern):return only_local_tests(__name__)
