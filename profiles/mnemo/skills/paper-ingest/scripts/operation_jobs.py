"""Detached supervisors for the existing fixed-operation launchers, not a scheduler.

An attempt is reserved once. Reattachment never sends another request. Process
absence without a terminal receipt is uncertain, not permission to retry.
"""
import argparse
from dataclasses import asdict
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

from article_runtime import absolute, require, sha


def write(path, value):
    with absolute(path).open('x') as stream:
        json.dump(value,stream,indent=2,allow_nan=False); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def load_job(attempt):
    root=absolute(attempt); path=root/'job.json'
    require(path.is_file() and (root/'job.sha256').is_file(),'operation-job-required')
    require(sha(path)==(root/'job.sha256').read_text(),'operation-job-changed')
    job=json.loads(path.read_text()); require(job['schema']=='paper-operation-job-v1','operation-job-schema')
    return root,job


def start(kind, arguments, deployment):
    require(kind in ('source','enrichment'),'operation-kind')
    root=absolute(arguments['attempt_dir'])
    config={k:str(v) for k,v in asdict(deployment).items()}
    identity=dict(kind=kind,arguments=arguments,deployment=config)
    if root.exists():
        _,job=load_job(root); require(job['identity']==identity,'attempt-holds-different-operation')
        return status(root)
    # Reserve before spawning; even an interrupted start cannot redispatch.
    root.mkdir(parents=True,mode=0o700)
    job=dict(schema='paper-operation-job-v1',identity=identity,created_at=time.time(),
             supervisor_sha256=sha(Path(__file__).resolve()))
    write(root/'job.json',job)
    with (root/'job.sha256').open('x') as stream: stream.write(sha(root/'job.json')); stream.flush(); os.fsync(stream.fileno())
    with (root/'supervisor.log').open('xb') as log:
        child=subprocess.Popen([config['python'],'-B',str(Path(__file__).resolve()),'worker',str(root),sha(root/'job.json')],
            stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
            cwd=Path(__file__).resolve().parent,close_fds=True)
    write(root/'supervisor.json',dict(pid=child.pid,started_at=time.time()))
    # Reaping occurs in a daemon thread while the caller lives; worker survives its exit.
    threading.Thread(target=child.wait,daemon=True).start()
    return status(root)


def execution_progress(identity, process):
    """Read the worker's actual execution settings; never infer them from this caller."""
    if not isinstance(process,dict) or not process.get('child_pid'): return None
    args=identity.get('arguments',{})
    if identity.get('kind')=='source' and args.get('operation')=='execute':
        path=absolute(args['package_dir'])/(args['phase']+'-session.json')
    elif identity.get('kind')=='enrichment' and args.get('operation')=='execute':
        path=absolute(args['job'])/'enrichment/execution-start.json'
    elif args.get('operation')=='article' and args.get('arguments',{}).get('command')=='approved-execute':
        path=absolute(args['arguments']['work_root'])/'enrichment/execution-start.json'
    else:
        return None
    if path.name=='execution-start.json':
        runs=sorted((path.parent/'execution-runs').glob('*.json'))
        if runs: path=runs[-1]
    try:
        value=json.loads(path.read_text())
    except FileNotFoundError:
        return None
    except (ValueError,OSError):
        return dict(status='updating')
    if value.get('pid')!=process['child_pid']: return None
    try:
        if datetime.fromisoformat(value['started_at'].replace('Z','+00:00')) < datetime.fromisoformat(process['started_at'].replace('Z','+00:00')): return None
    except (KeyError,ValueError,TypeError): return None
    progress={k:value.get(k) for k in ('vlm_concurrency','concurrency_source','started_at')}
    from datetime import timezone
    import operation_timing
    progress['elapsed_seconds']=operation_timing.seconds(value.get('started_at'),datetime.now(timezone.utc).isoformat())
    root=path.parent.parent if path.name=='execution-start.json' or path.parent.name=='execution-runs' else path.parent
    if path.parent.name=='execution-runs': root=root.parent
    kind='source' if identity.get('kind')=='source' else 'enrichment'
    try:
        timing=operation_timing.summarize(**{kind+'_attempts':[root]})
        progress['counts']=timing['counts']
        progress['pending']=sum(phase['counts']['pending'] for attempt in timing['attempts'] for phase in attempt['phases'])
    except (ValueError,OSError,KeyError): progress['counts_status']='not-yet-readable'
    return progress


def status(attempt):
    root,job=load_job(attempt)
    value=dict(attempt_dir=str(root),job_sha256=sha(root/'job.json'),success=False,
               log=str(root/'supervisor.log'),next_operation=dict(operation='status',attempt_dir=str(root)))
    if (root/'terminal.json').exists():
        if not (root/'terminal.sha256').is_file(): return dict(value,status='uncertain',diagnostic='terminal-receipt-incomplete')
        require(sha(root/'terminal.json')==(root/'terminal.sha256').read_text(),'terminal-receipt-changed')
        terminal=json.loads((root/'terminal.json').read_text())
        require(terminal['job_sha256']==value['job_sha256'],'terminal-job-binding')
        value.update(status='finished' if terminal['result'].get('success') else 'failed',
                     success=bool(terminal['result'].get('success')),result=terminal['result'],next_operation=None)
        result=terminal['result']
        execution=result.get('execution') or (result.get('receipt') or {}).get('details',{}).get('execution')
        if execution is not None: value['execution']=execution
        args=job['identity'].get('arguments',{})
        article_args=args.get('arguments',{})
        work=article_args.get('work_root')
        if not work:
            for field in ('package_dir','job','review_root','output_dir','output'):
                if args.get(field):
                    parent=Path(args[field]).parent
                    if (parent/'plan.json').is_file() and json.loads((parent/'plan.json').read_text()).get('schema')=='initial-ingest-plan-v1':
                        work=str(parent); break
        if work and (Path(work)/'plan.json').is_file():
            plan=json.loads((Path(work)/'plan.json').read_text())
            if plan.get('schema')=='initial-ingest-plan-v1':
                value['next_operation']=dict(tool='paper_enrichment',operation='article',
                    arguments=dict(command='execute',work_root=work),attempt_dir=str(root.parent/(root.name+'-continuation')))
        # Results remain evidence-bound after the controlling session disappears.
        for path,h in terminal.get('artifacts',{}).items():
            require(sha(path)==h,'terminal-artifact-changed:'+path)
        return value
    running=False
    if (root/'worker.lock').exists():
        with (root/'worker.lock').open('rb') as lock:
            try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError: running=True
    value['status']='running' if running else ('starting' if time.time()-job['created_at']<10 else 'uncertain')
    process=root/'worker/process.json'
    if not process.exists(): process=root/'worker/running.json'
    if process.exists():
        try: value['process']=json.loads(process.read_text())
        except (ValueError,OSError): value['process']='updating'
    progress=execution_progress(job['identity'],value.get('process'))
    if progress is not None: value['execution']=progress
    if value['status']=='uncertain': value['diagnostic']='Supervisor absent without terminal evidence; inspect reservations; do not redispatch.'
    return value


def cancel(attempt):
    root,_=load_job(attempt)
    value=status(root)
    if value['status'] in ('finished','failed'): return value
    try: write(root/'cancel.json',dict(requested_at=time.time()))
    except FileExistsError: pass
    return dict(value,cancellation_requested=True)


def worker(attempt, expected_hash):
    root,job=load_job(attempt)
    require(sha(root/'job.json')==expected_hash and job['supervisor_sha256']==sha(Path(__file__).resolve()),'worker-binding-changed')
    with (root/'worker.lock').open('xb') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        stopped=threading.Event()
        def cancellation():
            while not stopped.wait(.1):
                if (root/'cancel.json').exists(): os.kill(os.getpid(),signal.SIGTERM); return
        # Launchers handle SIGTERM by terminating/reaping their own child group.
        def interrupted(number, frame): raise KeyboardInterrupt()
        signal.signal(signal.SIGTERM,interrupted)
        watcher=threading.Thread(target=cancellation,daemon=True)
        result=None
        try:
            identity=job['identity']; args=dict(identity['arguments'],attempt_dir=str(root/'worker'))
            config={k:Path(v) for k,v in identity['deployment'].items()}
            if (root/'cancel.json').exists():
                result=dict(success=False,diagnostic='cancelled-before-dispatch')
            else:
                if identity['kind']=='source': from pdf_source_package import launcher
                else: from qualified_enrichment import launcher
                watcher.start()
                result=launcher.launch(args,launcher.Deployment(**config))
        except BaseException as exc:
            result=dict(success=False,diagnostic=str(exc),error_type=type(exc).__name__,
                        reservation_disposition='inspect; possibly sent requests remain uncertain')
        finally: stopped.set()
        artifacts={}
        if result.get('receipt'): artifacts.update(result['receipt'].get('checked_artifacts',{}))
        if result.get('phase_evidence'):
            receipt=json.loads(absolute(result['phase_evidence']).read_text())
            for base,bindings in receipt['evidence_roots'].items():
                for name,h in bindings.items(): artifacts[str(absolute(Path(base)/name))]=h
        for name in ('result.json','process.json','console.log','artifacts.json','phase-evidence.json'):
            path=root/'worker'/name
            if path.is_file(): artifacts[str(path)]=sha(path)
        write(root/'terminal.json',dict(job_sha256=expected_hash,result=result,artifacts=artifacts))
        with (root/'terminal.sha256').open('x') as stream: stream.write(sha(root/'terminal.json')); stream.flush(); os.fsync(stream.fileno())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('worker','status','cancel')); parser.add_argument('attempt'); parser.add_argument('job_hash',nargs='?')
    args=parser.parse_args()
    if args.operation=='worker': worker(args.attempt,args.job_hash)
    else: print(json.dumps(status(args.attempt) if args.operation=='status' else cancel(args.attempt)))


if __name__=='__main__': main()
