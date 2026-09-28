from test_jobs import Jobs, only_local_tests
from manuscript_ingest import workflow as w
import importlib
from pathlib import Path
import json

class Campaign(Jobs):
    def module(self):
        return importlib.import_module('manuscript_ingest.campaign')
    def test_scan_uses_frontmatter_and_reports_parse_errors(self):
        c=self.module()
        self.page.write_text(self.page.read_text().replace('needs-ingest: true','needs-ingest: false')+'needs-ingest: true\n')
        stub=self.page.parent/'stub.md'; stub.write_text(self.page.read_text().replace('needs-ingest: false','needs-ingest: true'))
        bad=self.page.parent/'broken.md'; bad.write_text('---\ntags: [unterminated\n---\n')
        before={p:p.read_bytes() for p in self.page.parent.iterdir()}
        result=c.scan_queue(self.brain)
        self.assertEqual([r['path'] for r in result['items']],[str(stub)])
        self.assertEqual([r['path'] for r in result['diagnostics']],[str(bad)])
        self.assertEqual(before,{p:p.read_bytes() for p in self.page.parent.iterdir()})

def load_tests(loader,tests,pattern):return only_local_tests(__name__)

class Inventory(Campaign):
    def test_inventory_freezes_nonstubs_and_holds_identity(self):
        c=self.module(); (self.brain/'papers/stub.md').write_text(self.page.read_text().replace('needs-ingest: true','tags: [stub]'))
        (self.brain/'papers/unknown.md').write_text(self.page.read_text().replace('doi: 10.1234/synthetic\n',''))
        root=self.root/'campaign'; before=self.page.read_bytes()
        result=c.initialize(root,self.brain)
        self.assertEqual(result['counts'],{'pending':1,'excluded-stub':1,'blocked':1})
        frozen=(root/'inventory.json').read_bytes()
        self.assertEqual(self.page.read_bytes(),before)
        self.assertEqual(len(json.loads(frozen)['items']),3)
        with self.assertRaises(ValueError): c.initialize(root,self.brain)
        self.assertEqual((root/'inventory.json').read_bytes(),frozen)
        with self.assertRaises(ValueError): c.initialize(self.brain/'campaign',self.brain)

    def test_priority_and_archive_are_not_automatic_completion(self):
        c=self.module(); (self.brain/'projects').mkdir()
        (self.brain/'projects/active.md').write_text('---\nstatus: active\n---\n[[papers/other]]\n')
        (self.brain/'papers/other.md').write_text(self.page.read_text()+'Article archive: r2://unverified\n')
        data=c.inventory(self.brain)
        self.assertEqual(Path(data['items'][0]['path']).stem,'other')
        self.assertEqual(data['items'][0]['classification'],'archive-candidate')
        self.assertEqual(data['items'][0]['priority']['active_references'],['projects/active.md'])

from test_publication import Publication, MemoryTransport
from manuscript_ingest import archive
from unittest.mock import patch

class Recovery(Publication):
    def campaign(self):
        from manuscript_ingest import campaign as c
        root=self.root/'campaign'; c.initialize(root,self.brain)
        return c,root,next(iter(c.load(root)[1]['items']))

    def test_recover_stage_apply_complete_and_missing_summary(self):
        c,root,item=self.campaign(); j=self.staged()
        c.reconcile(root,self.runtime)
        self.assertEqual(c.load(root)[1]['items'][item]['status'],'ready')
        with patch.object(archive.pa,'RcloneTransport',MemoryTransport),patch.object(w,'integration_check',return_value=['missing-author']):
            w.publish(j,1,runtime_root=self.runtime)
        c.reconcile(root,self.runtime)
        self.assertEqual(c.load(root)[1]['items'][item]['status'],'integration-pending')
        with patch.object(archive.pa,'RcloneTransport',MemoryTransport),patch.object(w,'integration_check',return_value=[]):
            w.publish(j,1,runtime_root=self.runtime)
        c.reconcile(root,self.runtime); c.reconcile(root,self.runtime)
        state=c.load(root)[1]['items'][item]
        self.assertEqual(state['status'],'complete'); self.assertFalse(state['git']['pushed'])
        self.assertEqual(len(list((self.runtime/'jobs').iterdir())),1)
        self.page.write_text(self.page.read_text()+'Human note\n')
        c.reconcile(root,self.runtime)
        self.assertEqual(c.load(root)[1]['items'][item]['status'],'blocked')

    def test_source_recovery_and_inventory_edit_hold(self):
        c,root,item=self.campaign(); j,sid=self.ready()
        c.reconcile(root,self.runtime)
        self.assertEqual(c.load(root)[1]['items'][item]['job_id'],j)
        self.assertEqual(c.load(root)[1]['items'][item]['status'],'working')
        self.page.write_text(self.page.read_text()+'## Personal notes\nHuman annotation\n')
        c.reconcile(root,self.runtime)
        self.assertEqual(c.load(root)[1]['items'][item]['reason'],'concurrent-page-edit')

    def test_stale_locator_and_annotation_before_start(self):
        self.page.write_text(self.page.read_text()+'Article archive: r2://stale\n## Personal notes\nRetain this\n')
        c,root,item=self.campaign(); c.reconcile(root,self.runtime)
        state=c.load(root)[1]['items'][item]
        self.assertEqual(state['status'],'blocked'); self.assertEqual(state['reason'],'human-annotation-review')
        self.assertFalse((self.runtime/'jobs').exists())

class Runner(Campaign):
    def setup_run(self,n=3):
        c=self.module()
        for i in range(n-1):(self.page.parent/f'paper-{i}.md').write_text(self.page.read_text())
        root=self.root/'campaign'; c.initialize(root,self.brain)
        profile=self.root/'profile'; profile.mkdir(); (profile/'config.yaml').write_text('delegation:\n  max_concurrent_children: 2\n')
        w.save(root/'run-config.json',dict(hermes_command=['fake-hermes'],hermes_python='fake-python',hermes_repo=str(self.root),
            exclusive_window_until='2999-01-01T00:00:00+00:00',selection=list(c.load(root)[1]['items']),git_closeout='hold-for-review'))
        return c,root,profile

    def test_bounded_waves_missing_returns_and_exact_remainder(self):
        c,root,profile=self.setup_run(); calls=[]
        def launch(argv,**kwargs):
            frozen,state=c.load(root); reserved=[v for v in state['items'].values() if v['status']=='reserved']
            calls.append(len(reserved)); self.assertEqual(kwargs['env']['HERMES_HOME'],str(profile))
            self.assertIn('--query-file',argv)
            return 0
        with patch.object(c,'cron_window'),patch.object(c,'launch',side_effect=launch):
            result=c.run(root,self.runtime,profile,3,99,300)
        self.assertEqual(calls,[2,1]); self.assertEqual(result['counts'],{'interrupted':3})
        self.assertEqual(len(result['runs'][0]['items']),3)
        self.assertEqual(result['runs'][0]['concurrency'],2)
        with patch.object(c,'cron_window'),patch.object(c,'launch') as again:
            c.run(root,self.runtime,profile,3,2,300); again.assert_not_called()

    def test_systemic_exit_stops_admission_and_lock_is_exclusive(self):
        c,root,profile=self.setup_run()
        with c.exclusive(root):
            with self.assertRaisesRegex(ValueError,'already-running'):c.run(root,self.runtime,profile,3,2,300)
        with patch.object(c,'cron_window'),patch.object(c,'launch',return_value=1):
            result=c.run(root,self.runtime,profile,3,2,300)
        self.assertEqual(result['counts'],{'interrupted':2,'pending':1})
        self.assertEqual(result['runs'][0]['stop_reason'],'coordinator-failed')

    def test_crash_requires_recovery_before_new_admission(self):
        c,root,profile=self.setup_run()
        w.save(root/'window.json',dict(profile_home=str(profile),jobs=[]))
        with patch.object(c,'cron_window') as control,patch.object(c,'launch') as launch:
            with self.assertRaisesRegex(ValueError,'recovered-window'):c.run(root,self.runtime,profile,1,1,300)
            launch.assert_not_called();self.assertEqual(control.call_args.args[2],'restore')

class Cron(Campaign):
    def test_restore_keeps_paused_jobs_and_skips_overdue_catchup(self):
        c=self.module(); root=self.root/'campaign';root.mkdir();w.save(root/'run-config.json',{})
        profile=self.root/'profile'; profile.mkdir()
        rows={'a':dict(id='a',enabled=True,state='scheduled',schedule={'kind':'cron','expr':'0 7 * * *'},next_run_at='2000-01-01T00:00:00+00:00'),
              'b':dict(id='b',enabled=False,state='paused',paused_reason='human')}
        class FakeJobs:
            updates=[]
            def list_jobs(self,**kw):return list(rows.values())
            def get_job(self,id):return rows[id]
            def pause_job(self,id,reason):rows[id]={**rows[id],'enabled':False,'state':'paused','paused_reason':reason};return rows[id]
            def update_job(self,id,updates):self.updates.append(updates); rows[id].update(updates)
        jobs=FakeJobs()
        c.window_control(root,profile,'pause',jobs=jobs,gateway={'active_agents':0})
        self.assertEqual(rows['b']['paused_reason'],'human')
        c.window_control(root,profile,'restore',jobs=jobs)
        self.assertIn('schedule',jobs.updates[0]);self.assertTrue(rows['a']['enabled']);self.assertFalse(rows['b']['enabled'])
        self.assertFalse((root/'window.json').exists())

class Mapping(Campaign):
    def test_many_inputs_map_to_one_target_without_rebinding_job(self):
        c=self.module(); other=self.page.parent/'duplicate.md';other.write_text(self.page.read_text())
        root=self.root/'campaign';c.initialize(root,self.brain); frozen,state=c.load(root)
        item=next(r['id'] for r in frozen['items'] if r['path']==str(other)); (root/'originals').mkdir(); (root/'originals'/(item+'.md')).write_bytes(other.read_bytes());other.unlink()
        c.map_item(root,item,self.page,'Verified identical source identity; preserved edges; no inbound links.')
        self.assertEqual(len({e['canonical_path'] for e in c.load(root)[1]['items'].values()}),1)
        self.assertEqual(c.report(root)['total'],2)

    def test_retry_resumes_job_without_replacing_it(self):
        c=self.module(); root=self.root/'campaign';c.initialize(root,self.brain)
        item=next(iter(c.load(root)[1]['items'])); j=w.start(self.page,runtime_root=self.runtime)['job_id']
        c.reconcile(root,self.runtime);c.retry(root,item,'Continue retained source job after provider recovered.')
        c.reconcile(root,self.runtime)
        state=c.load(root)[1]['items'][item];self.assertTrue(state['admit']);self.assertEqual(state['job_id'],j)

class Admission(Runner):
    def test_merged_inputs_dispatch_once(self):
        c,root,profile=self.setup_run(2); frozen,state=c.load(root)
        old=Path(frozen['items'][0]['path']); target=Path(frozen['items'][1]['path']); (root/'originals').mkdir(); (root/'originals'/(frozen['items'][0]['id']+'.md')).write_bytes(old.read_bytes());old.unlink()
        c.map_item(root,frozen['items'][0]['id'],target,'Verified identity and citation union, repaired links.')
        counts=[]
        def launch(argv,**kwargs):
            _,state=c.load(root); counts.append(sum(v['status']=='reserved' for v in state['items'].values()));return 0
        with patch.object(c,'cron_window'),patch.object(c,'launch',side_effect=launch):c.run(root,self.runtime,profile,2,2,300)
        self.assertEqual(counts,[1])

    def test_blocked_between_waves_never_dispatches(self):
        c,root,profile=self.setup_run(2); frozen,state=c.load(root); calls=[]
        def launch(argv,**kwargs):
            calls.append(argv); Path(frozen['items'][1]['path']).write_text('Human edit during first wave');return 0
        with patch.object(c,'cron_window'),patch.object(c,'launch',side_effect=launch):result=c.run(root,self.runtime,profile,2,1,300)
        self.assertEqual(len(calls),1);self.assertEqual(result['counts'],{'interrupted':1,'blocked':1})

class Priority(Campaign):
    def test_repeated_project_mentions_count_once(self):
        c=self.module(); (self.brain/'projects').mkdir()
        (self.brain/'projects/active.md').write_text('---\nstatus: active\n---\n[[papers/paper]] [[papers/paper]]')
        self.assertEqual(c.inventory(self.brain)['items'][0]['priority']['active_references'],['projects/active.md'])

class WindowRace(Campaign):
    def test_claim_arriving_during_pause_holds_run(self):
        c=self.module(); root=self.root/'campaign';root.mkdir();w.save(root/'run-config.json',{})
        profile=self.root/'profile';profile.mkdir()
        row=dict(id='daily',enabled=True,state='scheduled',schedule={'kind':'cron','expr':'0 7 * * *'})
        class RaceJobs:
            def list_jobs(self,**kw):return [row.copy()]
            def pause_job(self,id,reason):row.update(enabled=False,state='paused',paused_reason=reason,fire_claim={'owner':'scheduler'});return row.copy()
        with self.assertRaisesRegex(ValueError,'active-scheduled-writer'):
            c.window_control(root,profile,'pause',jobs=RaceJobs(),gateway={'active_agents':0})

class MergeSnapshot(Campaign):
    def test_mapping_requires_retained_original_bytes(self):
        c=self.module(); other=self.page.parent/'duplicate.md';other.write_text(self.page.read_text())
        root=self.root/'campaign';c.initialize(root,self.brain); frozen,state=c.load(root)
        item=next(r['id'] for r in frozen['items'] if r['path']==str(other));other.unlink()
        with self.assertRaisesRegex(ValueError,'original-snapshot-required'):c.map_item(root,item,self.page,'Verified duplicate')

class AccessRetry(Campaign):
    def test_missing_source_can_be_explicitly_released(self):
        c=self.module();root=self.root/'campaign';c.initialize(root,self.brain)
        item=next(iter(c.load(root)[1]['items']));j=w.start(self.page,runtime_root=self.runtime)['job_id']
        job=w.load_job(j,self.runtime);job.update(status='needs-input',blocking_reason='manuscript-unavailable');w.store_job(job,self.runtime)
        c.reconcile(root,self.runtime);c.retry(root,item,'Full manuscript now available from verified repository.')
        self.assertTrue(c.load(root)[1]['items'][item]['admit'])
