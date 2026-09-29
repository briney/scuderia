"""Bounded paper campaign operations; scientific work belongs to manuscript_ingest."""
import argparse
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import os
import re
import subprocess
import time
import json
from pathlib import Path
import sys
import yaml

if not __package__:
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    __package__='manuscript_ingest'
from . import workflow as w


def _scan(instance):
    instance=w.absolute(instance); items=[]; diagnostics=[]
    w.require((instance/'papers').is_dir(),'papers-directory-required')
    for path in sorted((instance/'papers').glob('*.md')):
        try:
            w.absolute(path); raw=path.read_bytes(); text=raw.decode('utf-8'); fm=w.page_metadata(text)
            w.require(fm.get('kind')=='paper','paper-kind-required')
            for key in ('tags','cited_by','links'):
                w.require((fm.get(key) is None or isinstance(fm[key],list)),'invalid-list:'+key)
            for key in ('needs-ingest','needs-enrichment'):
                w.require(fm.get(key) is None or type(fm[key]) is bool,'invalid-boolean:'+key)
            items.append(dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),metadata=fm))
        except (OSError,ValueError,yaml.YAMLError) as exc:
            diagnostics.append(dict(path=str(path),reason=str(exc)))
    return dict(items=items,diagnostics=diagnostics)


def scan_queue(instance:Path)->dict:
    result=_scan(instance)
    result['items']=[r for r in result['items'] if r['metadata'].get('needs-ingest') is True]
    result['items'].sort(key=lambda r:(-len(r['metadata'].get('cited_by') or []),r['path']))
    return result


def now():
    return datetime.now(timezone.utc).isoformat()


def inventory(instance:Path)->dict:
    instance=w.absolute(instance); scanned=_scan(instance); references={}
    for kind in ('projects','grants'):
        for path in sorted((instance/kind).glob('*.md')):
            text=path.read_text()
            try: fm=w.page_metadata(text)
            except (ValueError,yaml.YAMLError): continue
            if fm.get('status') not in ('active','planning','draft','in-progress','submitted','funded'):continue
            for slug in set(re.findall(r'\[\[papers/([^]|#]+)',text)):
                references.setdefault(slug,[]).append(str(path.relative_to(instance)))
    items=[]
    for row in scanned['items']:
        path=Path(row['path']); fm=row.pop('metadata'); text=path.read_text()
        pointer=re.search(r'^Article archive: (.+)$',text,re.M)
        stub='stub' in (fm.get('tags') or [])
        missing=not(fm.get('doi') or fm.get('pmid')) or not fm.get('title')
        priority=dict(active_references=references.get(path.stem,[]),
            weak_source=fm.get('needs-enrichment') is True or fm.get('fulltext_source')=='abstract-only',
            cited_by=len(fm.get('cited_by') or []))
        row.update(identity={k:fm.get(k) for k in ('title','doi','pmid','version')},
            classification='stub' if stub else 'identity-exception' if missing else 'archive-candidate' if pointer else 'refresh',
            archive_pointer=pointer[1] if pointer else None,priority=priority,
            preserved_metadata={k:fm[k] for k in ('cited_by','stub_source','ingest_attempts','links') if k in fm})
        items.append(row)
    for diagnostic in scanned['diagnostics']:
        items.append(dict(**diagnostic,sha256=None,classification='metadata-exception',identity={},priority={}))
    for row in items:row['id']=hashlib.sha256(str(Path(row['path']).relative_to(instance)).encode()).hexdigest()[:20]
    items.sort(key=lambda r:(-len(r['priority'].get('active_references',[])),
        -int(r['priority'].get('weak_source',False)),-r['priority'].get('cited_by',0),r['path']))
    # YAML dates are metadata, not a second serialization contract.
    return json.loads(json.dumps(dict(version=1,instance=str(instance),created_at=now(),items=items),default=str))


@contextmanager
def exclusive(root):
    root=w.outside_instance(root); root.mkdir(parents=True,exist_ok=True)
    with (root/'campaign.lock').open('a') as handle:
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('campaign-already-running')
        yield handle.fileno() # close releases the lock; inherited child descriptors keep orphaned waves exclusive


def initialize(root:Path,instance:Path)->dict:
    root=w.outside_instance(root); instance=w.absolute(instance)
    w.require(not root.is_relative_to(instance) and not instance.is_relative_to(root),'campaign-must-be-outside-instance')
    with exclusive(root):
        w.require(not (root/'inventory.json').exists() and not (root/'state.json').exists(),'campaign-already-initialized')
        frozen=inventory(instance)
        from article_archive_compat.portable_articles import save
        save(root/'inventory.json',frozen)
        states={}
        for row in frozen['items']:
            kind=row['classification']
            states[row['id']]=dict(status='excluded-stub' if kind=='stub' else 'blocked' if kind.endswith('exception') else 'pending',
                reason=row.get('reason',kind if kind.endswith('exception') else None),canonical_path=row['path'],job_id=None,
                updated_at=now(),admit=True,git=dict(committed=False,pushed=False))
        w.save(root/'state.json',dict(inventory_sha256=w.sha(root/'inventory.json'),items=states,runs=[]))
    return report(root)


def load(root):
    root=w.outside_instance(root); state=json.loads((root/'state.json').read_text())
    w.require(w.sha(root/'inventory.json')==state['inventory_sha256'],'frozen-inventory-changed')
    frozen=json.loads((root/'inventory.json').read_text())
    w.require(set(state['items'])=={r['id'] for r in frozen['items']},'campaign-denominator-changed')
    return frozen,state


def report(root):
    frozen,state=load(root); counts=dict(Counter(r['status'] for r in state['items'].values()))
    distinct={r['canonical_path'] for r in state['items'].values() if r['status'] in ('complete','already-current')}
    published={r['canonical_path'] for r in state['items'].values() if r['status']=='complete' and r['git']['pushed']}
    seconds=sum(r.get('wall_seconds',0) for r in state['runs'])
    return dict(total=len(frozen['items']),counts=counts,distinct_complete=len(distinct),published=len(published),
        wall_seconds=seconds,published_per_hour=len(published)*3600/seconds if seconds else None,
        merged_inputs=sum(bool(r.get('mapping_reason')) for r in state['items'].values()),
        outstanding=[dict(id=k,**v) for k,v in state['items'].items() if v['status'] not in ('excluded-stub','complete','already-current')],
        runs=state['runs'])


def git_state(instance,page):
    def git(*args):
        p=subprocess.run(['git','-C',str(instance),*args],capture_output=True,timeout=30)
        return p.stdout if p.returncode==0 else None
    relative=str(page.relative_to(instance)); raw=page.read_bytes()
    committed=git('show','HEAD:'+relative)==raw
    head=git('rev-parse','HEAD') if committed else None
    upstream=git('rev-parse','--abbrev-ref','--symbolic-full-name','@{upstream}')
    pushed=False
    if committed and upstream:
        remote,branch=upstream.decode().strip().split('/',1)
        tip=git('ls-remote',remote,'refs/heads/'+branch)
        if tip:
            commit=tip.decode().split()[0]
            pushed=git('show',commit+':'+relative)==raw
    return dict(committed=committed,pushed=pushed,commit=head.decode().strip() if head else None)


def completed(job,runtime_root):
    """Read existing evidence only. Never publish, dispatch or rerun integration here."""
    from . import archive
    work=w.job_path(job['job_id'],runtime_root); folder=work/'archives'/str(job['revision'])
    manifest=folder/'manifest.json'; receipt=folder/'publication.json'
    archive.publication_check(manifest,json.loads(receipt.read_text()))
    w.require(archive.page_matches(folder/'page.md',Path(job['page']),receipt),'completed-page-changed')
    w.require(job.get('artifacts',{}).get('integration_obligations')==[],'integration-evidence-missing')
    fm=w.page_metadata(Path(job['page']).read_text())
    w.require(w.manuscript_read(job) and fm.get('fulltext_source')!='abstract-only','full-manuscript-required')
    return manifest


def _reconcile(root,runtime_root):
    frozen,state=load(root); settings=w.config(runtime_root)
    w.require(settings['instance']==frozen['instance'],'campaign-runtime-instance-mismatch')
    active_path=Path(runtime_root)/'active.json'
    active=json.loads(active_path.read_text()) if active_path.exists() else {}
    for row in frozen['items']:
        entry=state['items'][row['id']]; page=Path(entry['canonical_path'])
        if entry['status']=='excluded-stub':continue
        try:
            if entry['status']=='blocked':continue # explicit retry releases a reviewed hold
            candidate=entry['job_id'] or active.get(str(page))
            job=w.load_job(candidate,runtime_root) if candidate else None
            replacement=active.get(str(page))
            if job and replacement and replacement!=candidate:
                from . import archive
                newer=w.load_job(replacement,runtime_root)
                prior=w.job_path(candidate,runtime_root)/'archives'/str(job['revision'])
                original=w.job_path(replacement,runtime_root)/'original.md'
                w.require(job['status']=='complete' and newer['page']==str(page)
                    and original.is_file() and w.sha(original)==newer['original_sha256']
                    and archive.page_matches(prior/'page.md',original,prior/'publication.json'),
                    'replacement-job-reconciliation-required')
                candidate=replacement; job=newer
            if job:
                w.require(job['page']==str(page),'job-canonical-path-mismatch')
                # Old completed jobs can establish currentness only through their actual evidence.
                if not entry['job_id'] and job['status']!='complete':
                    w.require(job['original_sha256']==entry.get('accepted_sha256',row['sha256']),'job-inventory-base-mismatch')
                entry.update(job_id=candidate,revision=job['revision'])
                if job['status']=='complete':
                    completed(job,runtime_root)
                    was_current=not entry.get('run_id') and job['original_sha256']!=row['sha256']
                    entry.update(status='already-current' if was_current else 'complete',reason=None,
                        git=git_state(Path(frozen['instance']),page))
                else:
                    # Existing status detects/snapshots a concurrent live edit without inference.
                    result=w.status(candidate,runtime_root=runtime_root)
                    entry.update(status='blocked' if result['status']=='held' else result['status'],reason=result['blocking_reason'])
            else:
                w.require(page.exists(),'canonical-page-missing; resolve mapping before start')
                w.require(w.sha(page)==entry.get('accepted_sha256',row['sha256']),'changed-since-inventory')
                text=page.read_text()
                if re.search(r'^#{1,6}\s+(?:personal|human|my|manual) (?:notes|annotations)\b',text,re.I|re.M):
                    w.require(entry.get('annotation_review_sha256')==w.sha(page),'human-annotation-review')
                if entry['status'] in ('reserved','waiting-canonical'):entry.update(status='interrupted',reason='reserved-without-runtime-job')
            entry['updated_at']=now()
        except (OSError,ValueError,KeyError,yaml.YAMLError) as exc:
            entry.update(status='blocked',reason=str(exc),updated_at=now())
    w.save(Path(root)/'state.json',state)
    return state


def reconcile(root:Path,runtime_root:Path)->dict:
    with exclusive(root):_reconcile(root,runtime_root)
    return report(root)


def retry(root,item,reason):
    w.require(reason and reason.strip(),'retry-requires-reason')
    with exclusive(root):
        frozen,state=load(root); entry=state['items'][item]
        w.require(entry['status'] in ('blocked','interrupted','working','needs-input','ready','publication-pending','integration-pending'),'item-not-retryable')
        row=next(r for r in frozen['items'] if r['id']==item)
        page=Path(entry['canonical_path']); fm=w.page_metadata(page.read_text())
        w.require(fm.get('title') and (fm.get('doi') or fm.get('pmid')),'resolve-identity-before-retry')
        entry.setdefault('retry_history',[]).append(dict(at=now(),reason=reason,prior=entry['reason']))
        entry.update(status='pending',reason=None,admit=True,accepted_sha256=w.sha(page),annotation_review_sha256=w.sha(page))
        w.save(Path(root)/'state.json',state)
    return report(root)


def map_item(root,item,canonical,reason):
    """Record a parent-reviewed rename/merge; do not perform graph mutation here."""
    w.require(reason and reason.strip(),'mapping-requires-source-backed-reason')
    with exclusive(root):
        frozen,state=load(root); entry=state['items'][item]; canonical=w.absolute(canonical)
        instance=Path(frozen['instance']); row=next(r for r in frozen['items'] if r['id']==item)
        w.require(canonical.parent==instance/'papers' and canonical.suffix=='.md' and canonical.exists(),'invalid-canonical-page')
        w.require(not entry['job_id'],'resolve-mapping-before-start; do not rebind a runtime job')
        snapshot=Path(root)/'originals'/(item+'.md')
        w.require(snapshot.is_file() and w.sha(snapshot)==row['sha256'],'original-snapshot-required-before-merge')
        fm=w.page_metadata(canonical.read_text())
        preserved=row.get('preserved_metadata',{})
        w.require(set(preserved.get('cited_by') or [])<=set(fm.get('cited_by') or []),'mapped-citing-edges-missing')
        old=Path(row['path'])
        w.require(canonical!=old and not old.exists(),'old-page-still-present')
        for path in instance.rglob('*.md'):
            if path.is_relative_to(instance/'working-docs'):continue
            w.require(not re.search(r'\[\[(?:papers/)?'+re.escape(old.stem)+r'(?:[|#\]])',path.read_text()),'unrepaired-inbound-link:'+str(path))
        entry.update(canonical_path=str(canonical),mapping_reason=reason,accepted_sha256=w.sha(canonical),status='pending',reason=None)
        w.save(Path(root)/'state.json',state)
    return report(root)


def launch(argv,*,env,cwd,log,lock_fds=()):
    # Admission deadlines never kill an in-flight publication.
    started=time.time(); query=argv[argv.index('--query-file')+1]
    marker=Path(env['HERMES_HOME'])/'paper-refresh'/('child-'+w.digest(query)[:24]+'.json')
    with Path(log).open('xb') as output:
        child=subprocess.Popen(argv,env=env,cwd=cwd,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,pass_fds=lock_fds)
        w.save(marker,dict(pid=child.pid,query=query))
        try:
            rc=child.wait()
        finally:
            # A surviving process keeps its marker and inherited profile lock.
            if child.poll() is not None:marker.unlink(missing_ok=True)
        w.save(Path(log).parent/'process.json',dict(started_at=started,finished_at=time.time(),pid=child.pid,returncode=rc))
        return rc


def worker_prompt(frozen,state,item,folder,deadline):
    entry=state['items'][item]
    return f'''Stage only this existing paper: {entry['canonical_path']}
Existing job: {entry.get('job_id')}. Brain: {frozen['instance']}. External work: {folder}.
Load the bound paper-ingest skill and runtime reference. Do not load the exhaustive historical workflow.
You own identity/acquisition, one complete manuscript read, fresh drafting, and a focused check of central claims.
Read the old page for valid provenance, links and human annotations, not as scientific evidence.
Reuse the same job and retained sources/draft. Existing archive: sources without inputs first.
Use markdown_path for staging. If already staged, return durable job/revision evidence without another full read or generation.
Retain available original supplements only, with the shared 120-second attachment budget; do not process them.
No nested delegation, publish, live paper edits, shared graph/ledger writes or Git. Return integration candidates externally.
An ambiguous author association is unresolved, never a name-only merge. A missing full manuscript is a hold, not abstract-only success.
Do not repeat failed JSON payloads, archive downloads or metadata sleep loops. Return specific remaining obligations.
Stop new work after {deadline}; finish a safe in-flight step. On systemic provider/authentication/archive outage write {folder/'STOP'}.
Write concise observations in {folder/'observations.md'}. Durable runtime state is authoritative; no rigid response schema.
Do not use the shared institutional browser concurrently. If browser acquisition is necessary, return the retained needs-input job and observed URL to the primary, which owns that browser serially.
All output English. Preserve model pins, output caps and approval settings.
'''


def maximum_overlap(paths):
    events=[]
    for path in paths:
        if path.exists():
            row=json.loads(path.read_text()); events.extend([(row['started_at'],1),(row['finished_at'],-1)])
    active=peak=0
    for _,delta in sorted(events):active+=delta;peak=max(peak,active)
    return peak


def cron_window(root,profile_home,action):
    cfg=json.loads((Path(root)/'run-config.json').read_text())
    env=dict(os.environ,HERMES_HOME=str(profile_home))
    result=subprocess.run([cfg['hermes_python'],'-B',str(Path(__file__).resolve()),'_window',
        '--root',str(root),'--profile-home',str(profile_home),'--action',action],env=env,capture_output=True,text=True,timeout=60)
    w.require(result.returncode==0,'cron-window-failed:'+result.stdout[-2000:]+result.stderr[-2000:])


def window_control(root,profile_home,action,*,jobs=None,gateway=None):
    """Run under the installed Hermes Python so native cron locking/scheduling applies."""
    cfg=json.loads((Path(root)/'run-config.json').read_text())
    if jobs is None:
        w.require(os.environ.get('HERMES_HOME')==str(profile_home),'wrong-hermes-home')
        sys.path.insert(0,cfg['hermes_repo'])
        from cron import jobs
        from gateway.control_socket import query_gateway_control
        gateway=lambda:query_gateway_control(profile_home,'status')
    path=Path(root)/'window.json'; reason='paper-refresh:'+str(root)
    if action=='restore':
        snapshot=json.loads(path.read_text())
        w.require(snapshot['profile_home']==str(profile_home),'window-profile-mismatch')
        for old in snapshot['jobs']:
            current=jobs.get_job(old['id'])
            if not current or current.get('paused_reason')!=reason:continue # preserve an operator's intervening edit
            updates={k:old.get(k) for k in ('enabled','state','paused_at','paused_reason','next_run_at')}
            if old.get('enabled') and old.get('state')!='paused':
                if not old.get('next_run_at') or datetime.fromisoformat(old['next_run_at'])<=datetime.now(timezone.utc):
                    updates['schedule']=old['schedule'] # native update computes the next future slot; never resume catch-up
            jobs.update_job(old['id'],updates)
        path.unlink();return dict(restored=True)
    status=gateway() if callable(gateway) else gateway
    w.require(status is not None and status.get('active_agents')==0,'gateway-busy-or-status-unavailable')
    rows=jobs.list_jobs(include_disabled=True)
    w.require(not any(r.get('fire_claim') for r in rows if not r.get('no_agent')),'active-scheduled-writer')
    # ponytail: a controlled profile-wide window; a shared lease protocol is needed only for concurrent primaries.
    selected=[r for r in rows if not r.get('no_agent') and r.get('enabled') and r.get('state')!='paused']
    w.require(not path.exists(),'window-already-open')
    w.save(path,dict(profile_home=str(profile_home),jobs=selected,created_at=now()))
    for row in selected:
        result=jobs.pause_job(row['id'],reason=reason)
        w.require(result is not None and not result['enabled'],'pause-failed:'+row['id'])
    w.require(not any(r.get('fire_claim') for r in jobs.list_jobs(include_disabled=True) if not r.get('no_agent')),'active-scheduled-writer-after-pause')
    status=gateway() if callable(gateway) else gateway
    w.require(status is not None and status.get('active_agents')==0,'gateway-busy-after-pause')
    return dict(paused=len(selected))


def wave_prompt(frozen,state,selected,folder,deadline,cfg):
    items=[dict(id=i,path=state['items'][i]['canonical_path'],job_id=state['items'][i]['job_id']) for i in selected]
    return f'''Refresh only these existing paper inputs in {frozen['instance']}:
{json.dumps(items,indent=2)}
Load ingest-pending-papers/references/corpus-refresh.md, paper-ingest and batch-drain from the bound profile.
Use the six manuscript-to-page operations only. Reuse staged manuscript drafts and retained originals; supplements remain unprocessed.
Inspect the old page for valid links, provenance and human annotations; do not paraphrase it as evidence.
Resolve identity and dedup before start. A rename/merge or ambiguous human annotation is a hold for this wave; propose it externally.
Reuse named jobs and their sources/drafts; inspect durable artifacts even after a missing worker summary.
Workers have already attempted these inputs. For staged jobs, do not delegate, acquire again, reread full manuscripts or regenerate drafts.
For a needs-input job with a documented authorized-browser route, the primary alone may finish that acquisition and its first manuscript read/draft serially; reuse prior attempts and respect the admission deadline. Otherwise preserve the access hold.
Inspect the retained annotated drafts and selected evidence for material issues; integrate shared files, amend only when needed, and publish the same jobs. No other queued or bibliography paper is in scope.
Check current job status and pending obligations first. A transient metadata lookup means defer this item's publication without sleeping or restarting. Missing full manuscript remains an access hold.
Stop new admissions after {deadline}; finish safe in-flight work. On provider/authentication/archive outage, stop admissions and write its reason to {folder/'STOP'}.
Record per-input access/identity/annotation issues and remaining obligations in {folder/'observations.md'}; no rigid final output schema is required.
Keep all sources, drafts, machine state and receipts external. Do not edit campaign state or launch another campaign command.
Git closeout policy: {cfg['git_closeout']}. If hold-for-review, leave owned changes for pilot review and report exact paths; do not commit/push.
Otherwise the parent follows git-ops for coherent verified owned changes, preserving pre-existing dirt. A failed push never restarts ingestion.
All output in English. Do not change model pins, output caps or approval settings.
'''


def run(root:Path,runtime_root:Path,profile_home:Path,limit:int,concurrency:int,max_seconds:int)->dict:
    root=w.outside_instance(root); profile_home=w.outside_instance(profile_home)
    w.require(all(type(n) is int and n>0 for n in (limit,concurrency,max_seconds)),'positive-run-limits-required')
    with exclusive(root) as root_fd,exclusive(profile_home/'paper-refresh') as profile_fd:
        cfg=json.loads((root/'run-config.json').read_text())
        for marker in (profile_home/'paper-refresh').glob('child*.json'):
            previous=json.loads(marker.read_text())
            ps=subprocess.run(['ps','-p',str(previous['pid']),'-o','command='],capture_output=True,text=True)
            w.require(previous['query'] not in ps.stdout,'previous-coordinator-still-running')
            marker.unlink()
        if (root/'window.json').exists():
            cron_window(root,profile_home,'restore'); _reconcile(root,runtime_root)
            raise ValueError('recovered-window; review interrupted work before another run')
        profile=yaml.safe_load((profile_home/'config.yaml').read_text())
        ceiling=profile.get('delegation',{}).get('max_concurrent_children')
        w.require(type(ceiling) is int and ceiling>0,'native-child-ceiling-required')
        concurrency=min(concurrency,ceiling)
        w.require(datetime.fromisoformat(cfg['exclusive_window_until']).timestamp()>=time.time()+max_seconds,'confirmed-exclusive-window-required')
        w.require(cfg.get('git_closeout') in ('hold-for-review','publish'),'explicit-git-closeout-policy-required')
        _reconcile(root,runtime_root); frozen,state=load(root)
        selection=cfg['selection']; w.require(isinstance(selection,list) and len(selection)==len(set(selection)) and set(selection)<=set(state['items']),'invalid-explicit-selection')
        def eligible(i):
            return state['items'][i].get('admit') and state['items'][i]['status'] in ('pending','working','needs-input','ready','integration-pending','publication-pending')
        chosen=[]; paths=set()
        for i in selection:
            path=state['items'][i]['canonical_path']
            if eligible(i) and path not in paths:chosen.append(i);paths.add(path)
        chosen=chosen[:limit]
        if not chosen:return report(root)
        started=time.time(); deadline=started+max_seconds; run_id=str(time.time_ns()); folder=root/'runs'/run_id; folder.mkdir(parents=True)
        record=dict(id=run_id,started_at=now(),items=[],concurrency=concurrency,limit=limit,max_seconds=max_seconds,waves=[])
        state['runs'].append(record); w.save(root/'state.json',state)
        try:
            cron_window(root,profile_home,'pause')
            for offset in range(0,len(chosen),concurrency):
                if time.time()>=deadline:record['stop_reason']='admission-deadline';break
                state=_reconcile(root,runtime_root); record=state['runs'][-1]
                selected=[i for i in chosen[offset:offset+concurrency] if eligible(i)]
                if not selected:continue
                record['items'].extend(selected)
                targets={state['items'][i]['canonical_path'] for i in selected}
                for item,entry in state['items'].items():
                    if entry['canonical_path'] in targets and entry['status'] not in ('blocked','excluded-stub'):
                        entry.update(status='reserved' if item in selected else 'waiting-canonical',admit=False,run_id=run_id,updated_at=now())
                w.save(root/'state.json',state) # durable reservation before any subprocess
                wave=folder/str(offset); wave.mkdir(); wave_start=time.time()
                worker_items=[i for i in selected if not state['items'][i].get('job_id') or
                    w.load_job(state['items'][i]['job_id'],runtime_root)['status'] not in ('ready','integration-pending','publication-pending','complete')]
                from concurrent.futures import ThreadPoolExecutor
                worker_paths=[]
                def stage_worker(item):
                    task=wave/item;task.mkdir();query=task/'query.txt'
                    query.write_text(worker_prompt(frozen,state,item,task,datetime.fromtimestamp(deadline,timezone.utc).isoformat()))
                    return launch([*cfg['hermes_command'],'chat','--query-file',str(query),'--toolsets','file,terminal,web,paper_ingest'],
                        env=dict(os.environ,HERMES_HOME=str(profile_home)),cwd=str(task),log=task/'hermes.log',lock_fds=(root_fd,profile_fd))
                with ThreadPoolExecutor(max_workers=concurrency) as pool:
                    futures=[pool.submit(stage_worker,i) for i in worker_items]
                    codes=[future.result() for future in futures]
                worker_paths=[wave/i/'process.json' for i in worker_items]
                worker_end=time.time();rc=next((code for code in codes if code),0)
                state=_reconcile(root,runtime_root);record=state['runs'][-1]
                ready=[i for i in selected if state['items'][i]['status'] in ('ready','integration-pending','publication-pending','needs-input')]
                if ready and not rc and not list(wave.rglob('STOP')):
                    primary=wave/'integration';primary.mkdir();query=primary/'query.txt'
                    query.write_text(wave_prompt(frozen,state,ready,primary,datetime.fromtimestamp(deadline,timezone.utc).isoformat(),cfg))
                    rc=launch([*cfg['hermes_command'],'chat','--query-file',str(query),'--toolsets','file,terminal,web,paper_ingest'],
                        env=dict(os.environ,HERMES_HOME=str(profile_home)),cwd=frozen['instance'],log=primary/'hermes.log',lock_fds=(root_fd,profile_fd))
                state=_reconcile(root,runtime_root); record=state['runs'][-1]
                phases={i:w.load_job(state['items'][i]['job_id'],runtime_root).get('timings',{}) for i in selected if state['items'][i].get('job_id')}
                peak=maximum_overlap(worker_paths)
                record['actual_worker_concurrency']=max(record.get('actual_worker_concurrency',0),peak)
                record['waves'].append(dict(items=selected,returncode=rc,wall_seconds=time.time()-wave_start,
                    worker_wall_seconds=worker_end-wave_start,integration_wall_seconds=time.time()-worker_end,
                    actual_worker_concurrency=peak,job_timings=phases,artifacts=str(wave)))
                outage=any(state['items'][i]['status']=='publication-pending' for i in selected)
                if rc or list(wave.rglob('STOP')) or outage:
                    record['stop_reason']='coordinator-failed' if rc else 'systemic-outage'
                    break
                w.save(root/'state.json',state)
        finally:
            # Preserve partial state even on launch failure or interruption; no blind redispatch.
            latest=_reconcile(root,runtime_root); current=latest['runs'][-1]
            current.update(record,wall_seconds=time.time()-started,finished_at=now(),overrun_seconds=max(0,time.time()-deadline))
            w.save(root/'state.json',latest)
            if (root/'window.json').exists() and not list((profile_home/'paper-refresh').glob('child*.json')):cron_window(root,profile_home,'restore')
    return report(root)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    scan=commands.add_parser('scan-queue'); scan.add_argument('--instance',required=True,type=Path)
    scan.add_argument('--output',type=Path,help='New external JSON file; stdout otherwise')
    init=commands.add_parser('init'); init.add_argument('--instance',required=True,type=Path); init.add_argument('--root',required=True,type=Path)
    rep=commands.add_parser('report'); rep.add_argument('--root',required=True,type=Path)
    rec=commands.add_parser('reconcile'); rec.add_argument('--root',required=True,type=Path); rec.add_argument('--runtime-root',required=True,type=Path)
    ret=commands.add_parser('retry'); ret.add_argument('--root',required=True,type=Path); ret.add_argument('--item',required=True); ret.add_argument('--reason',required=True)
    mapping=commands.add_parser('map'); mapping.add_argument('--root',required=True,type=Path); mapping.add_argument('--item',required=True); mapping.add_argument('--canonical',required=True,type=Path); mapping.add_argument('--reason',required=True)
    runner=commands.add_parser('run')
    for name in ('root','runtime-root','profile-home'):runner.add_argument('--'+name,required=True,type=Path)
    for name in ('limit','concurrency','max-seconds'):runner.add_argument('--'+name,required=True,type=int)
    window=commands.add_parser('_window',help=argparse.SUPPRESS)
    window.add_argument('--root',required=True,type=Path); window.add_argument('--profile-home',required=True,type=Path); window.add_argument('--action',choices=('pause','restore'),required=True)
    args=parser.parse_args(argv)
    try:
        if args.command=='scan-queue':
            result=scan_queue(args.instance)
            if args.output:
                from article_archive_compat.portable_articles import save
                save(w.outside_instance(args.output),result)
                result=dict(output=str(args.output),items=len(result['items']),diagnostics=len(result['diagnostics']))
        elif args.command=='init':result=initialize(args.root,args.instance)
        elif args.command=='reconcile':result=reconcile(args.root,args.runtime_root)
        elif args.command=='retry':result=retry(args.root,args.item,args.reason)
        elif args.command=='map':result=map_item(args.root,args.item,args.canonical,args.reason)
        elif args.command=='run':result=run(args.root,args.runtime_root,args.profile_home,args.limit,args.concurrency,args.max_seconds)
        elif args.command=='_window':result=window_control(args.root,args.profile_home,args.action)
        else:result=report(args.root)
        print(json.dumps(result,ensure_ascii=False,default=str));return 0
    except (OSError,ValueError,yaml.YAMLError) as exc:
        print(json.dumps(dict(error=str(exc))));return 2

if __name__=='__main__':raise SystemExit(main())
