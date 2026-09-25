"""Enrichment-only gates over accepted counting and transport primitives.

No extractor phase modification, automatic approval, retry, fallback or trimming.
"""
from pathlib import Path
import re
from urllib.parse import urlsplit
from .io import require, load, save, put, sha, digest, dumps, strict, safe, now_utc
from . import bindings, trusted
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


def execute(run, approval, *, authorize=False):
    """Historical v7 evidence is read-only; create a current portable job."""
    raise ValueError('historical-job-read-only-new-job-required')
