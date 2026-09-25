"""Enrichment-only gates over accepted counting and transport primitives.

No extractor phase modification, automatic approval, retry, fallback or trimming.
"""
from pathlib import Path
import fcntl
import os
import re
import time
from urllib.parse import urlsplit
from .io import require, load, save, put, sha, digest, dumps, strict, safe, now_utc
from . import bindings, trusted, importer
from .requests import SETTINGS


def assets(cache, counting):
    root=Path(cache).absolute()/('models--'+counting.MODEL_REPO.replace('/','--'))/'snapshots'/counting.REVISION
    require(root.is_dir(),'official-processor-revision-not-cached')
    files={p.name:sha(p) for p in sorted(root.iterdir()) if p.is_file()}
    require(files,'empty-processor-assets')
    return dict(root=str(root),files=files,revision=counting.REVISION,model_repo=counting.MODEL_REPO)


def count(run, cache):
    run=Path(run).absolute(); plan=bindings.verify(run)
    require(not (run/'seal.json').exists(),'already-sealed')
    save(run/'count-session.json',dict(started_at=now_utc(),status='one-shot; interruption requires new run'))
    module=trusted.module('counting',plan['method']['root'])
    processor_assets=assets(cache,module)
    counter=module.Counter(module.processor(cache))
    results={}
    for row in plan['requests']:
        if not row.get('id'): continue
        _,wire=bindings.request(run,row)
        result=counter.count(wire)
        result['request_sha256']=row['request_sha256']
        save(safe(run,row['directory'])/'count.json',result)
        results[row['id']]=result
        print(dumps(dict(stage='count',id=row['id'],prompt_tokens=result['prompt_tokens_local'],fits=result['fits'])).decode(),flush=True)
    value=dict(schema='enrichment-count-v2',plan_sha256=sha(run/'enrichment-plan.json'),requests=results,
               processor=processor_assets,started_at=load(run/'count-session.json')['started_at'],finished_at=now_utc())
    save(run/'counts.json',value); put(run/'counts.sha256',sha(run/'counts.json'))
    return value


def verify_counts(run,plan, *, method=None):
    run=Path(run)
    require(sha(run/'counts.json')==(run/'counts.sha256').read_text(),'count-binding')
    value=load(run/'counts.json')
    require(value.get('schema') == 'enrichment-count-v2', 'unsupported-enrichment-count-format')
    require(value['plan_sha256']==sha(run/'enrichment-plan.json'),'count-plan-binding')
    require(set(value['requests'])=={r['id'] for r in plan['requests'] if r.get('id')},'count-roster-binding')
    method = method or plan['method']['root']
    module=trusted.module('counting',method)
    info=value['processor']; root=Path(info['root'])
    require(info['revision']==module.REVISION and info['model_repo']==module.MODEL_REPO,'processor-revision-binding')
    require({p.name:sha(p) for p in sorted(root.iterdir()) if p.is_file()}==info['files'],'processor-assets-changed')
    limit=trusted.module('io',method).LIMIT
    for row in plan['requests']:
        if not row.get('id'): continue
        c=value['requests'][row['id']]
        require(load(safe(run,row['directory'])/'count.json')==c,'request-count-binding')
        n=c['prompt_tokens_local']
        require(type(n) is int and n>0 and c['request_sha256']==row['request_sha256'],'count-request-binding')
        require(c['reserved_completion_tokens']==65536 and c['context_limit']==limit and c['fits']==(n+65536<=limit),'count-fit-binding')
    return value


def seal(run):
    run=Path(run).absolute(); plan=bindings.verify(run); counts=verify_counts(run,plan)
    require(not (run/'execution-session.json').exists(),'execution-already-started')
    names=['enrichment-plan.json','plan.sha256','counts.json','counts.sha256']
    for row in plan['requests']:
        if row.get('id'):
            names += [row['directory']+'/'+name for name in ('request-wire.json','source-evidence.json','prompt.txt','count.json')]
    value=dict(schema='enrichment-seal-v2',sealed_at=now_utc(),code=plan['code'],method=plan['method'],
               source_package=plan['source_package'],fixture=plan['fixture'],files={name:sha(safe(run,name)) for name in names})
    save(run/'seal.json',value)
    template=dict(schema='enrichment-parent-approval-v2',approved=False,approved_by=None,
                  source_and_payload_reviewed=False,counts_and_route_reviewed=False,
                  endpoint=None,credential_env=None,maximum_posts=None,
                  seal_sha256=sha(run/'seal.json'),fixture=plan['fixture'],settings=SETTINGS,
                  timeout_seconds=1200,retries=0,reasoning='omitted/default',
                  requests=[dict(id=r['id'],request_sha256=r['request_sha256'],count=counts['requests'][r['id']])
                            for r in plan['requests'] if r.get('id') and counts['requests'][r['id']]['fits']])
    save(run/'approval.template.json',template)
    return template


def _approval(run,path,plan,counts):
    raw=Path(path).read_bytes(); approval=strict(raw)
    template=load(run/'approval.template.json')
    # Regenerate immutable bindings rather than trusting editable template flags.
    require(template['seal_sha256']==sha(run/'seal.json'),'seal-template-binding')
    want=dict(schema='enrichment-parent-approval-v2',seal_sha256=sha(run/'seal.json'),fixture=plan['fixture'],
              settings=SETTINGS,timeout_seconds=1200,retries=0,reasoning='omitted/default',
              requests=[dict(id=r['id'],request_sha256=r['request_sha256'],count=counts['requests'][r['id']])
                        for r in plan['requests'] if r.get('id') and counts['requests'][r['id']]['fits']])
    editable={'approved','approved_by','source_and_payload_reviewed','counts_and_route_reviewed','endpoint','credential_env','maximum_posts'}
    require(isinstance(approval,dict) and set(approval)==set(want)|editable,'approval-schema')
    require(all(approval[k]==v for k,v in want.items()),'approval-bindings-changed')
    require(all(approval[k] is True for k in ('approved','source_and_payload_reviewed','counts_and_route_reviewed')) and isinstance(approval['approved_by'],str) and approval['approved_by'].strip(),'explicit-parent-approval-required')
    require(type(approval['maximum_posts']) is int and 0<len(want['requests'])<=approval['maximum_posts'],'explicit-post-budget-required')
    require(isinstance(approval['endpoint'],str),'parent-endpoint-required')
    endpoint=urlsplit(approval['endpoint'])
    require(endpoint.scheme in ('http','https') and endpoint.hostname and not endpoint.username and not endpoint.password and not endpoint.query and not endpoint.fragment,'endpoint-no-embedded-credentials')
    require(isinstance(approval['credential_env'],str) and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',approval['credential_env']),'credential-env-name-required')
    return raw,approval


def stamp(path):
    s=path.stat()
    return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)


def execute(run, approval, *, authorize=False):
    """The public live entry has no injectable transport."""
    require(authorize is True,'explicit-authorize-posts-required')
    require(not os.environ.get('PDF_ENRICHMENT_OFFLINE') and not os.environ.get('PDF_SOURCE_PACKAGE_OFFLINE'),'offline-live-forbidden')
    return _execute(run,approval,fixture_transport=None)


def execute_fixture(run, approval, transport):
    """Test-only injection; requires a permanently fixture-bound run and offline mode."""
    require(os.environ.get('PDF_ENRICHMENT_OFFLINE')=='1','fixture-execution-offline-required')
    require(callable(transport),'fixture-transport-required')
    return _execute(run,approval,fixture_transport=transport)


def _execute(run, approval_path, fixture_transport):
    run=Path(run).absolute(); approval_path=Path(approval_path).absolute()
    safe(run,'.execution.lock')
    with (run/'.execution.lock').open('a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        require(not (run/'execution-session.json').exists(),'one-attempt-no-resume')
        initial=load(run/'enrichment-plan.json')
        source=Path(initial['source_package']['root'])
        # Capture metadata before full entry validation; subsequent requests do not rehash the huge tree.
        source_stamps={p:stamp(p) for p in source.rglob('*') if p.is_file()}
        plan=bindings.verify(run); counts=verify_counts(run,plan)
        sealed=load(run/'seal.json')
        require(sealed['code']==plan['code'] and sealed['method']==plan['method'] and sealed['source_package']==plan['source_package'],'seal-code-source-binding')
        for name,h in sealed['files'].items(): require(sha(safe(run,name))==h,'sealed-input-changed:'+name)
        approval_raw,approval=_approval(run,approval_path,plan,counts)
        fixture=fixture_transport is not None
        require(plan['fixture'] is fixture and ((run/'OFFLINE-FIXTURE').exists() is fixture),'no-fixture-promotion')
        rows=[r for r in plan['requests'] if r.get('id') in {a['id'] for a in approval['requests']}]
        require(all(not (safe(run,r['directory'])/'reservation.json').exists() for r in rows),'consumed-reservation')
        method=trusted.module('execution',plan['method']['root'])
        constants=trusted.module('io',plan['method']['root'])
        require(constants.TIMEOUT==1200 and constants.SETTINGS==SETTINGS,'accepted-method-settings-mismatch')
        transport=fixture_transport if fixture else method.LiveTransport(approval)
        origin='offline-bounded-fake-transport' if fixture else 'parent-authorized-live'
        frozen={safe(run,n):safe(run,n).read_bytes() for n in sealed['files']}
        frozen[run/'seal.json']=(run/'seal.json').read_bytes()
        frozen[approval_path]=approval_raw
        def check(row):
            require(all(p.read_bytes()==raw for p,raw in frozen.items()),'entry-input-changed')
            require(trusted.code_hashes()==plan['code'] and trusted.method_hashes(plan['method']['root'])==plan['method']['code'],'entry-code-changed')
            require({p:stamp(p) for p in source.rglob('*') if p.is_file()}==source_stamps,'entry-source-changed')
            bindings.request(run,row)
        save(run/'execution-session.json',dict(started_at=now_utc(),pid=os.getpid(),origin=origin,approval_sha256=digest(approval_raw),maximum_posts=approval['maximum_posts']))
        put(run/'executed-approval.json',approval_raw)
        finished=[]
        for row in rows:
            check(row)
            p=safe(run,row['directory']); payload=(p/'request-wire.json').read_bytes()
            reservation=dict(status='reserved-may-have-posted',started_at=now_utc(),origin=origin,
                             request_sha256=digest(payload),approval_sha256=digest(approval_raw),seal_sha256=sha(run/'seal.json'))
            save(p/'reservation.json',reservation)
            meta=dict(started_at=reservation['started_at'],requested_model=SETTINGS['model'],returned_model=None,
                      usage=None,origin=origin,synthetic=fixture,timeout_seconds=1200,retries=0)
            started=time.monotonic()
            try:
                # Transport invokes this check immediately before its single HTTP POST.
                received=transport(payload,row,lambda:check(row))
            except (OSError,TimeoutError,ConnectionError) as exc:
                received=dict(status='transport-failure',error_type=type(exc).__name__)
            raw=received.get('raw')
            meta.update({('transport_status' if k=='status' else k):v for k,v in received.items() if k!='raw'})
            meta.update(finished_at=now_utc(),latency_seconds=time.monotonic()-started)
            if raw is not None:
                put(p/'response-body.json',raw)
                meta.update(raw_file='response-body.json',raw_sha256=digest(raw))
            try:
                require(raw is not None,'missing-response-body')
                require(received.get('http_status')==200,'http-failure:'+str(received.get('http_status')))
                env=strict(raw)
                meta['returned_model']=env.get('model') if isinstance(env,dict) else None
                meta['usage']=env.get('usage') if isinstance(env,dict) else None
                text,env=method.envelope(raw)
                usage=env.get('usage')
                require(isinstance(usage,dict) and all(type(usage.get(k)) is int and usage[k]>=0 for k in ('prompt_tokens','completion_tokens','total_tokens')),'missing-or-invalid-usage')
                require(usage['prompt_tokens']==counts['requests'][row['id']]['prompt_tokens_local'],'actual-prompt-count-mismatch')
                require(usage['completion_tokens']<=65536 and usage['total_tokens']==usage['prompt_tokens']+usage['completion_tokens'],'invalid-usage-total')
                result=importer.assemble_response(row,load(p/'source-evidence.json'),text,fixture)
            except (ValueError,KeyError,TypeError,IndexError) as exc:
                result=dict(status='failed',complete=False,reason=type(exc).__name__+':'+str(exc))
            result.update(meta)
            importer.retain_outcome(run,row,result)
            finished.append(row['id'])
            if result['status']=='failed': break  # no repair, no retry, stop remaining work
        result=dict(finished_at=now_utc(),origin=origin,attempted=finished,results=importer.outcomes(run,plan))
        save(run/'execution-complete.json',result)
        return result
