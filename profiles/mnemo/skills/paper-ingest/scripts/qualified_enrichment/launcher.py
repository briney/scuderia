"""Small native-capability launcher. No transport, retries or model configuration."""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading

OPERATIONS = {
    'article': ({'arguments'}, set()),
    'prepare': ({'source_handoff','output'}, {'test_root','processor_cache'}),
    'count': ({'job','processor_cache'}, set()),
    'seal': ({'job'}, {'processor_cache'}),
    'execute': ({'job','approval','authorize_posts'}, {'vlm_concurrency'}),
    'report': ({'job','output'}, set()),
    'import-test-response': ({'job','responses'}, set()),
    'review-create': ({'run','output'}, {'kind'}),
    'review-packet': ({'review_root','output','elements'}, {'max_bytes'}),
    'review-import': ({'review_root','packet','submission'}, set()),
    'export': ({'review_root','output'}, set()),
    'verify-export': ({'export_path'}, set()),
    'consume': ({'export_path','element','target','purpose','output'}, {'qualification','source_inspection','aspects'}),
}
PATHS = {'source_handoff','output','test_root','job','processor_cache','approval','responses',
         'run','review_root','packet','submission','export_path','source_inspection'}


def require(ok, reason):
    if not ok: raise ValueError(reason)


def absolute(value):
    require(isinstance(value,(str,Path)) and str(value), 'absolute-path-required')
    p=Path(value)
    require(p.is_absolute() and '..' not in p.parts and '\\' not in str(p), 'absolute-path-without-traversal-required')
    require(not any(x.is_symlink() for x in (p,*p.parents)), 'symlink-forbidden')
    require(not p.is_file() or p.stat().st_nlink==1, 'hardlink-forbidden')
    return p


def sha(path):
    h=hashlib.sha256()
    with absolute(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


def save(path,value):
    raw=(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
    with absolute(path).open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def now(): return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Deployment:
    integration_dir: Path
    enrichment_root: Path
    method_dir: Path
    adapter_dir: Path
    python: Path

    def validate(self, *, historical=False):
        for path,marker in ((self.integration_dir,'entry.py'),(self.enrichment_root,'pdf_enrichment/live.py'),
                            (self.method_dir,'pdf_source_package/phase_evidence.py'),(self.adapter_dir,'source_package.py')):
            root = absolute(path)
            require(historical or (root/marker).is_file(),'trusted-deployment-unavailable:'+marker)
        require(Path(self.python).is_absolute() and '..' not in Path(self.python).parts and
                (historical or Path(self.python).is_file()),'trusted-python-unavailable')


def argv_for(args, deployment, attempt, *, historical=False):
    if historical:
        require(args.get('operation') == 'export', 'historical-export-receipt-only')
    deployment.validate(historical=historical)
    require(isinstance(args,dict) and args.get('operation') in OPERATIONS,'unknown-operation')
    op=args['operation']; required,optional=OPERATIONS[op]
    require(required <= args.keys() and args.keys() <= required|optional|{'operation','attempt_dir','offline','timeout'}, 'operation-argument-fields')
    for key in PATHS & args.keys(): absolute(args[key])
    written = {'output', 'attempt_dir'} & args.keys()
    if op in ('count','seal','execute','import-test-response'): written.add('job')
    if op == 'review-import': written.add('review_root')
    for key in written:
        output = absolute(args[key])
        require(not any((p/'retention.json').exists() for p in (output, *output.parents)), 'write-inside-immutable-retention')
        for code in (deployment.integration_dir,deployment.enrichment_root,deployment.method_dir,deployment.adapter_dir):
            require(not output.is_relative_to(code) and not code.is_relative_to(output), 'write-overlaps-trusted-code')
    for key in ('offline','authorize_posts'):
        if key in args: require(type(args[key]) is bool,'boolean-required:'+key)
    if op=='execute': require(args['authorize_posts'] is True and not args.get('offline',False),'separate-approval-and-authorize-posts-required')
    if 'vlm_concurrency' in args:
        require(type(args['vlm_concurrency']) is int and args['vlm_concurrency'] > 0, 'vlm-concurrency-must-be-positive-integer')
    if args.get('test_root'): require(args.get('offline') is True,'test-root-requires-offline')
    if 'kind' in args: require(args['kind'] in ('qualified-job','v7-run'),'review-kind')
    if 'purpose' in args: require(args['purpose'] in ('discovery','summary','exact','algorithm-specification'),'consumer-purpose')
    if 'max_bytes' in args: require(type(args['max_bytes']) is int and 1024<=args['max_bytes']<=8000000,'bounded-packet-size')
    command=[str(deployment.python),'-B','-u','-E',str(deployment.integration_dir/'entry.py'),
             '--enrichment-root',str(deployment.enrichment_root),'--adapter-dir',str(deployment.adapter_dir),
             '--method',str(deployment.method_dir),'--receipt',str(attempt/'artifacts.json')]
    network=op=='execute' or (op=='article' and args.get('arguments',{}).get('command') in ('approved-execute','publish','initial-publish'))
    if args.get('offline') or not network: command.append('--offline')
    command.append(op)
    for key in sorted(required|optional):
        if key not in args: continue
        value=args[key]
        if key=='authorize_posts': command.append('--authorize-posts')
        elif key=='arguments':
            require(isinstance(value,dict),'article-arguments-object-required')
            command.append('--arguments-json='+json.dumps(value,allow_nan=False))
        elif key in ('elements','aspects'):
            require(isinstance(value,list) and (value or key=='elements') and len(value)==len(set(value)) and all(isinstance(x,str) and x for x in value),'explicit-unique-list')
            for item in value: command.append('--'+('element' if key=='elements' else 'aspect')+'='+item)
        else:
            require(isinstance(value,(str,int)) and not isinstance(value,bool),'scalar-argument')
            command.append('--'+key.replace('_','-')+'='+str(value))
    return command


def preflight(args, deployment):
    attempt=absolute(args.get("attempt_dir"))
    # Do not place process evidence into any input, output or trusted code tree.
    protected=[deployment.integration_dir,deployment.enrichment_root,deployment.method_dir,deployment.adapter_dir]
    for key in PATHS & args.keys():
        if key in ('test_root',): continue
        p=absolute(args[key])
        directory_keys={'job','run','review_root','processor_cache','output'}
        protected.append(p if p.is_dir() or key in directory_keys else p.parent)
    if args['operation']=='article':
        value=args['arguments']
        require(isinstance(value,dict) and 'work_root' in value,'article-work-root-required')
        work=absolute(value['work_root'])
        require(not any(work.is_relative_to(code) or code.is_relative_to(work) for code in protected), 'article-work-overlaps-trusted-code')
        nested_paths={'work_root','output','page','manifest','identity_approval','cache','count_receipt','approval','submission','packet'}
        for key in nested_paths & value.keys():
            path=absolute(value[key])
            if key in ('work_root','output','page'):
                require(not any((p/'retention.json').exists() for p in (path,*path.parents)), 'write-inside-immutable-retention')
                require(not any(path.is_relative_to(code) or code.is_relative_to(path) for code in protected[:4]), 'write-overlaps-trusted-code')
            protected.append(path)
        require(not (args.get('offline') and value.get('command') in ('publish','initial-publish')), 'offline-publication-forbidden')
    for p in protected:
        require(not attempt.is_relative_to(p) and not p.is_relative_to(attempt),'attempt-must-be-external')
    timeout=args.get('timeout',14400)
    require(type(timeout) in (int,float) and math.isfinite(timeout) and 0<timeout<=86400,'bounded-timeout')
    return timeout


def launch(args, deployment):
    if args.get('operation') in ('status','cancel'):
        require(set(args)=={'operation','attempt_dir'},'job-control-fields')
        import operation_jobs
        return getattr(operation_jobs,args['operation'])(args['attempt_dir'])
    if 'background' in args:
        require(type(args['background']) is bool,'background-boolean-required')
        args=dict(args); background=args.pop('background')
        if background:
            import operation_jobs
            argv_for(args,deployment,absolute(args['attempt_dir'])/'worker')
            preflight(args,deployment)
            return operation_jobs.start('enrichment',args,deployment)
    attempt=absolute(args.get('attempt_dir'))
    argv=argv_for(args,deployment,attempt)
    timeout=preflight(args,deployment)
    attempt.mkdir(mode=0o700, parents=True)
    started=now(); pid=None; termination='normal'; exit_code=None
    env=dict(os.environ); env['PYTHONDONTWRITEBYTECODE']='1'
    network=args['operation']=='execute' or (args['operation']=='article' and args.get('arguments',{}).get('command') in ('approved-execute','publish','initial-publish'))
    if args.get('offline') or not network:
        env.update(PDF_ENRICHMENT_OFFLINE='1',PDF_SOURCE_PACKAGE_OFFLINE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    previous={}
    def interrupted(number, frame): raise KeyboardInterrupt()
    if threading.current_thread() is threading.main_thread():
        previous={number:signal.signal(number,interrupted) for number in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP)}
    child=None
    try:
        save(attempt/'started.json',dict(started_at=started,operation=args['operation'],status='starting'))
        with (attempt/'console.log').open('xb') as log:
            child=subprocess.Popen(argv,cwd=deployment.integration_dir,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            pid=child.pid
            save(attempt/'running.json',dict(started_at=started,child_pid=pid,operation=args['operation'],status='running'))
            exit_code=child.wait(timeout=timeout)
    except (subprocess.TimeoutExpired,KeyboardInterrupt) as exc:
        termination='timeout-killed' if isinstance(exc,subprocess.TimeoutExpired) else 'cancelled'
    finally:
        if child is not None and child.poll() is None:
            try: os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            exit_code=child.wait()
        for number,handler in previous.items(): signal.signal(number,handler)
    process=dict(schema='paper-enrichment-process-v1',operation=args['operation'],argv=argv,cwd=str(deployment.integration_dir),
                 started_at=started,ended_at=now(),child_pid=pid,exit_code=exit_code,termination=termination,
                 process_status='exited',attempt_dir=str(attempt),log=str(attempt/'console.log'),
                 deployment={key:str(value) for key,value in deployment.__dict__.items()})
    save(attempt/'process.json',process)
    valid=False; receipt=None; diagnostic=None
    try:
        receipt=json.loads((attempt/'artifacts.json').read_bytes())
        require(receipt['schema']=='enrichment-operation-receipt-v1' and receipt['operation']==args['operation']
                and receipt['exit_code']==exit_code and receipt['artifact_status']=='verified','child-receipt-mismatch')
        require(receipt['checked_artifacts'] and all(sha(path)==value for path,value in receipt['checked_artifacts'].items()),'child-artifact-hash-mismatch')
        valid=True
    except (ValueError,KeyError,OSError,TypeError) as exc: diagnostic=str(exc)
    result=dict(process,success=exit_code==0 and termination=='normal' and valid,
                artifact_status='verified' if valid else 'unverified',receipt=receipt,diagnostic=diagnostic,
                process_sha256=sha(attempt/'process.json'),console_sha256=sha(attempt/'console.log'))
    save(attempt/'result.json',result)
    return result


def verify_result(path, expected_operation, expected_artifacts):
    path=absolute(path); root=path.parent; value=json.loads(path.read_bytes())
    process=json.loads((root/'process.json').read_bytes())
    require(path.name=='result.json' and value['schema']=='paper-enrichment-process-v1','launcher-result-schema')
    require(value['success'] is True and type(value['exit_code']) is int and value['exit_code']==0
            and value['termination']=='normal' and value['process_status']=='exited','launcher-not-complete')
    require(all(value[k]==v for k,v in process.items()),'launcher-process-mismatch')
    require(value['operation']==expected_operation and value['process_sha256']==sha(root/'process.json')
            and value['console_sha256']==sha(root/'console.log'),'launcher-process-binding')
    receipt=json.loads((root/'artifacts.json').read_bytes())
    require(value['receipt']==receipt and receipt['exit_code']==0 and receipt['artifact_status']=='verified','launcher-receipt-binding')
    require(receipt['checked_artifacts']==expected_artifacts,'launcher-expected-artifacts')
    require(all(sha(p)==h for p,h in expected_artifacts.items()),'launcher-artifact-changed')
    # Reconstruct the fixed export grammar rather than accepting arbitrary argv.
    d=Deployment(**{k:Path(v) for k,v in process['deployment'].items()})
    d.validate(historical=True)
    require(process['cwd']==str(d.integration_dir) and process['attempt_dir']==str(root),'launcher-deployment-binding')
    if expected_operation=='export':
        handoff=next(Path(p) for p in expected_artifacts if Path(p).name=='handoff.json')
        exported=json.loads(handoff.read_bytes())
        expected=argv_for(dict(operation='export',attempt_dir=str(root),review_root=exported['review_root'],
                               output=str(handoff.parent)),d,root,historical=True)
        require(process['argv']==expected,'launcher-fixed-argv-binding')
    return value
