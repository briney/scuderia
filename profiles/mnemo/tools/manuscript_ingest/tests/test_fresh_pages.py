from test_integration import Integration
from test_jobs import only_local_tests
from manuscript_ingest import workflow as w, archive, sources
from unittest.mock import patch
import subprocess

class FreshPages(Integration):
    def test_legacy_prose_metadata_and_malformed_edges_are_replaceable(self):
        self.page.write_text(self.page.read_text().replace('needs-ingest: true',
            'needs-ingest: true\ncited_by: ["papers/first - papers/second"]\nstub_source: old\ningest_attempts: 9')+'\n## Personal notes\nOld interpretation\n')
        j,_=self.ready(); original=self.page.read_bytes()
        fresh=self.complete_draft().replace('cited_by: ["papers/first - papers/second"]\n','').replace('stub_source: old\n','').replace('ingest_attempts: 9\n','').replace('\n## Personal notes\nOld interpretation\n','')
        out=w.stage(j,fresh,'Fresh manuscript synthesis; central claims checked.',runtime_root=self.runtime)
        self.assertEqual(out['status'],'ready')
        self.assertNotIn('old',w.page_metadata(__import__('pathlib').Path(out['artifacts']['draft']).read_text()).values())
        self.assertEqual((w.job_path(j,self.runtime)/'original.md').read_bytes(),original)

    def test_graph_work_does_not_block_page_publication(self):
        j,_=self.ready()
        draft=self.complete_draft().replace('authors: []','author_names: [Alice Example]\nauthors: []\nlinks: [methods/missing]')
        out=w.stage(j,draft,'Full author list and manuscript checked.',runtime_root=self.runtime)
        self.assertEqual(out['artifacts']['integration_obligations'],[])
        self.assertTrue(out['artifacts']['graph_follow_up'])
        with patch.object(archive.pa,'RcloneTransport',__import__('test_publication').MemoryTransport),patch('subprocess.run',return_value=subprocess.CompletedProcess([],0,stdout='')) as check:
            out=w.publish(j,out['artifacts']['revision'],runtime_root=self.runtime)
        self.assertEqual(out['status'],'complete')
        self.assertIn('--identity-only',check.call_args.args[0])
        self.assertIn('--candidate',check.call_args.args[0])
        self.assertIn(out['artifacts']['draft'],check.call_args.args[0])
        self.assertFalse((self.brain/'methods/missing.md').exists())
        self.assertTrue(out['artifacts']['graph_follow_up'])

    def test_backlinks_are_rebuilt_from_citation_fields_not_legacy_or_topic_links(self):
        (self.brain/'papers/citing.md').write_text('---\nkind: paper\ncites: [papers/paper]\n---\n')
        (self.brain/'papers/topic.md').write_text('---\nkind: paper\nlinks: [papers/paper]\n---\n')
        j,_=self.ready()
        out=w.stage(j,self.complete_draft(),'Fresh manuscript synthesis checked.',runtime_root=self.runtime)
        meta=w.page_metadata(__import__('pathlib').Path(out['artifacts']['draft']).read_text())
        self.assertEqual(meta['cited_by'],['papers/citing'])

    def test_no_ingest_log_required(self):
        j,_=self.ready()
        out=w.stage(j,self.complete_draft().split('\n## Ingest log')[0],'Manuscript central claims checked.',runtime_root=self.runtime)
        self.assertEqual(out['artifacts']['integration_obligations'],[])

    def test_xml_table_preserves_column_relationships(self):
        path=self.root/'table.xml'
        path.write_text('<article><body><p>Result <italic>one</italic>.</p><table-wrap><label>Table 1</label><table><thead><tr><th>Model</th><th>Fold AUC</th><th>Family AUC</th></tr></thead><tbody><tr><td>Example</td><td>0.70</td><td>0.90</td></tr></tbody></table></table-wrap></body></article>')
        text=sources.text_pages(path)[0]
        self.assertIn('Model | Fold AUC | Family AUC',text)
        self.assertIn('Example | 0.70 | 0.90',text)
        self.assertIn('Result one.',text)

def load_tests(loader,tests,pattern):return only_local_tests(__name__)

class StandaloneVerifier(Integration):
    def test_verifier_imports_cache_support_without_caller_pythonpath(self):
        import os,sys
        from pathlib import Path
        helper=Path(w.__file__).resolve().parents[2]/'skills/paper-ingest/scripts/verify_ingest.py'
        script=self.root/'check-import.py'
        script.write_text('import runpy\nrunpy.run_path('+repr(str(helper))+')\nfrom article_archive_compat.article_runtime import outside_instance\n')
        env=dict(os.environ);env.pop('PYTHONPATH',None)
        checked=subprocess.run([sys.executable,'-B',str(script)],env=env,capture_output=True,text=True)
        self.assertEqual(checked.returncode,0,checked.stderr)

class GraphDefaults(Integration):
    def test_absent_optional_graph_lists_are_filled_without_model_repair(self):
        j,_=self.ready()
        text=self.complete_draft().replace('authors: []\n','').replace('venue: Journal','author_names: [Alice Example]\nvenue: Journal')
        out=w.stage(j,text,'Complete source names and manuscript claims checked.',runtime_root=self.runtime)
        from pathlib import Path
        fm=w.page_metadata(Path(out['artifacts']['draft']).read_text())
        self.assertEqual(fm['authors'],[])
        self.assertEqual(fm['links'],[])
        self.assertEqual(out['artifacts']['integration_obligations'],[])

    def test_invalid_optional_importance_is_omitted_without_inventing_a_score(self):
        j,_=self.ready()
        out=w.stage(j,self.complete_draft().replace('venue: Journal','venue: Journal\nimportance: minor'),'Source-grounded draft; program relevance uncalibrated.',runtime_root=self.runtime)
        from pathlib import Path
        self.assertNotIn('importance',w.page_metadata(Path(out['artifacts']['draft']).read_text()))
        self.assertIn('Invalid optional importance omitted; scoring deferred.',out['warnings'])

class IdentityBeforeApplication(Integration):
    def test_canonical_identity_hold_leaves_old_page_intact(self):
        from test_publication import MemoryTransport
        j,_=self.ready();original=self.page.read_bytes()
        w.stage(j,self.complete_draft(),'Central manuscript claims checked.',runtime_root=self.runtime)
        with patch.object(archive.pa,'RcloneTransport',MemoryTransport),patch.object(w,'integration_check',side_effect=lambda *a,**k: ['canonical identity contradiction'] if k.get('canonical',True) else []):
            out=w.publish(j,1,runtime_root=self.runtime)
        self.assertEqual(out['status'],'integration-pending')
        self.assertEqual(self.page.read_bytes(),original)
        self.assertFalse((self.brain/'docs/rem-cycle/inbox.yaml').exists())

class SupplementDefaults(Integration):
    def test_supplement_inputs_imply_role_but_cannot_rebind_manuscript(self):
        j,_=self.ready();path=self.root/'table.xlsx'
        import zipfile
        with zipfile.ZipFile(path,'w') as z:z.writestr('table.xml','<table/>')
        out=sources.prepare(j,supplement_inputs=[dict(path=str(path))],runtime_root=self.runtime)
        row=out['artifacts']['sources'][-1]
        self.assertEqual(row['role'],'supplement')
        self.assertNotIn('pages',row)
        with self.assertRaisesRegex(ValueError,'supplement-inputs-only'):
            sources.prepare(j,supplement_inputs=[dict(path=str(path),role='manuscript')],runtime_root=self.runtime)

class TitleCorrection(Integration):
    def test_explicit_title_correction_before_staging_reuses_sources_and_reads(self):
        j,_=self.ready();before=w.load_job(j,self.runtime)
        draft=self.complete_draft().replace('Synthetic experiment','Corrected experiment title')
        with self.assertRaisesRegex(ValueError,'call start with identity.title'):
            w.stage(j,draft,'Corrected title verified against source.',runtime_root=self.runtime)
        out=w.start(self.page,runtime_root=self.runtime,identity={'title':'Corrected experiment title'})
        self.assertEqual(out['job_id'],j)
        after=w.load_job(j,self.runtime)
        self.assertEqual(after['identity']['title'],'Corrected experiment title')
        self.assertEqual(after['sources'],before['sources'])
        self.assertEqual(after['reads'],before['reads'])
        self.assertEqual(after['history']['title_corrections'][0]['from'],'Synthetic experiment')
        self.assertEqual(w.start(self.page,runtime_root=self.runtime)['job_id'],j)
        draft=self.complete_draft().replace('Synthetic experiment','Corrected experiment title')
        staged=w.stage(j,draft,'Corrected title verified against the same source identifiers.',runtime_root=self.runtime)
        self.assertEqual(staged['status'],'ready')
        self.assertIn('Synthetic experiment',(w.job_path(j,self.runtime)/'original.md').read_text())
        manifest=archive.build(j,staged['artifacts']['revision'],runtime_root=self.runtime)
        self.assertEqual(archive.pa.load(manifest.parent/'provenance.json')['history']['title_corrections'][0]['to'],'Corrected experiment title')

    def test_title_recovery_cannot_change_identifiers_or_staged_identity(self):
        j,_=self.ready()
        for field,value in [('doi','10.1234/other'),('pmid','99999'),('version','other')]:
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'identity-conflict'):
                w.start(self.page,runtime_root=self.runtime,identity={'title':'Corrected experiment title',field:value})
        w.stage(j,self.complete_draft(),'Checked the central manuscript claims.',runtime_root=self.runtime)
        with self.assertRaisesRegex(ValueError,'title-correction-before-staging-only'):
            w.start(self.page,runtime_root=self.runtime,identity={'title':'Corrected experiment title'})
