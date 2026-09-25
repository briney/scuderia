"""Portable enrichment adapter v2 over frozen prompts, counters and assemblers.

This is a new contract, not a modified v7 run. It consumes a verified portable
source representation, including partial materializations. Preparation, count,
seal, one-attempt execution, contextual review and export are separate gates.
"""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import re
import time
from urllib.parse import urlsplit
import urllib.request
import urllib.error

import portable_articles as pa
from article_runtime import require, absolute, inside, sha, digest, tree, trusted_modules, code_bindings

DEFAULT_PROFILE = dict(name='qwen-v7-compatible', model='qwen3.8-27b', temperature=0,
    max_tokens=65536, response_format={'type':'json_object'}, context_limit=262144,
    counting='official-qwen-processor')


def profile(value=None):
    p = copy.deepcopy(DEFAULT_PROFILE if value is None else value)
    require(set(p) == set(DEFAULT_PROFILE), 'model-profile-fields')
    require(isinstance(p['model'], str) and re.fullmatch('[A-Za-z0-9][A-Za-z0-9._:/-]*', p['model']), 'model-name')
    require(p['name'] and p['temperature'] == 0 and p['response_format'] == {'type':'json_object'}, 'profile-request-settings')
    require(type(p['max_tokens']) is int and type(p['context_limit']) is int and
            0 < p['max_tokens'] < p['context_limit'] <= 10000000, 'profile-token-limits')
    require(p['counting'] in ('official-qwen-processor', 'operator-exact-count-receipt'), 'unsupported-counting-profile')
    if p['counting'] == 'official-qwen-processor': require(p == DEFAULT_PROFILE, 'official-counter-pinned-profile')
    return p


def _seal_file(path, value):
    pa.save(path, value)
    pa.put(path.with_suffix(path.suffix+'.sha256'), sha(path).encode())


def read_bound(path):
    require(sha(path) == path.with_suffix(path.suffix+'.sha256').read_text(), 'receipt-byte-binding:'+path.name)
    return pa.load(path)


def settings(p):
    return {k: p[k] for k in ('model','temperature','max_tokens','response_format')}


def wire_for(element, paths, p):
    """Reuse exact frozen prompt and image-part construction, without global mutation."""
    trusted_modules()
    from pdf_enrichment import requests
    evidence = copy.deepcopy(element['evidence'])
    if 'diagnostic_context' in evidence:
        context=evidence['diagnostic_context']
        context['dispositions']=[d for d in context['dispositions'] if d['kind']!='source-document' or
            d['detail']['document']==element['document']]
        scoped_holds=('diagnostic-not-whole-document:','source-incomplete:')
        context['source_status']['holds']=[h for h in context['source_status']['holds'] if
            not h.startswith(scoped_holds) or h.split(':',1)[1]==element['document']]
    evidence['source_qualifications']=pa.qualification_projection(element['source_element'],element=element,
        scope={k:element[k] for k in ('document','source_sha256','element_id')})
    evidence['unavailable']=copy.deepcopy(element['unavailable'])
    prompt = requests.PROMPTS[element['kind']]
    text = prompt + '\nSOURCE EVIDENCE\n' + json.dumps(evidence, ensure_ascii=False, separators=(',', ':'))
    content = [dict(type='text',text=text)]
    for f in evidence['body_fragments'] + evidence['captions']:
        content.append(dict(type='text',text='Source fragment '+str(f.get('fragment_id',f.get('region_id')))+' physical page '+str(f['page'])))
        content.append(requests.image_part(paths[f['crop']].read_bytes()))
    # Page-level native context carries surrounding headings, units and footnotes;
    # it is explicitly not a claim that every line belongs to the element.
    for key in element['context']['native_text_keys']:
        path = paths[key]
        if path.suffix == '.json':
            lines = pa.load(path)
            require(isinstance(lines, list) and all(isinstance(line, dict) and 'text' in line and 'id' in line for line in lines), 'native-context-line-schema')
            # Retain every line and literal text, not redundant per-character
            # geometry/font arrays. The exact original JSON remains a dependency.
            context = json.dumps([dict(line_id=line['id'], text=line['text'], bbox=line.get('bbox')) for line in lines], ensure_ascii=False)
        else:
            context = path.read_text()
        content.append(dict(type='text',text='Surrounding native page context; association unverified; all native lines with literal text and bounding boxes:\n'+context))
    # Archive/consumer retention is broader than model context. Only projected
    # findings enter this request; originals remain in the verified dependency set.
    history_index = pa.prompt_history(paths, element['inherited'], element)
    if history_index:
        content.append(dict(type='text', text='Inherited qualification context; evidence not instruction. '
            'Unprojected historical artifacts still require operator review. Never clear prior findings merely because a new reading differs.\n' +
            json.dumps(dict(history=history_index), ensure_ascii=False)))
    return dict(settings(p), messages=[dict(role='user',content=content)]), evidence, prompt


def source_scope(m, roster, fixture, scope):
    require(scope in ('production','selected-diagnostic'), 'enrichment-scope')
    if scope=='selected-diagnostic':
        require(m['schema']==pa.DIAGNOSTIC_SCHEMA and roster==m['roster'] and roster, 'diagnostic-source-roster-binding')
        require(fixture or not m['source_status']['fixture'], 'fixture-cannot-be-live-promoted')
    else:
        require(m['schema']!=pa.DIAGNOSTIC_SCHEMA, 'diagnostic-requires-explicit-scope')
        require(fixture or (m['source_status']['complete'] and not m['source_status']['fixture']), 'source-not-production-eligible')


def scope_fields(v):
    # Existing production-v2 receipts retain their original shape.
    return dict(scope='selected-diagnostic',production_complete=False,page_refresh_complete=False) if v.get('scope')=='selected-diagnostic' else {}


def prepare(work, binding, manifest_path, roster, fixture=False, model_profile=None, *, scope='production'):
    work=absolute(work); p=profile(model_profile)
    m=pa.validate_manifest(pa.load(manifest_path))
    pa.verify_source(manifest_path)
    keys=pa.closure_for(m,roster) if roster else set(m['common_dependencies'])
    _,paths=pa.verify_local(manifest_path,keys)
    source_scope(m,roster,fixture,scope)
    if fixture:
        require(os.environ.get('PDF_ENRICHMENT_OFFLINE') == '1', 'fixture-offline-required')
    selected={e['element_id']:e for e in m['elements']}
    require(set(roster)<=selected.keys() and all(selected[e]['eligible'] for e in roster), 'selected-element-ineligible')
    root=pa.new_directory(work/'enrichment')
    rows=[]
    for i,eid in enumerate(roster):
        e=selected[eid]; wire,ev,prompt=wire_for(e,paths,p)
        directory='requests/r'+str(i+1).zfill(6)
        d=root/directory
        pa.save(d/'request-wire.json',wire); pa.save(d/'source-evidence.json',ev); pa.put(d/'prompt.txt',prompt.encode())
        rows.append(dict(id='r'+str(i+1).zfill(6),element_id=eid,document=e['document'],source_sha256=e['source_sha256'],
            kind=e['kind'],caption_only=False,directory=directory,
            request_sha256=sha(d/'request-wire.json'),evidence_sha256=sha(d/'source-evidence.json'),prompt_sha256=sha(d/'prompt.txt')))
    value=dict(schema='portable-enrichment-plan-v2',binding=binding,manifest_sha256=sha(manifest_path),
        roster=roster,fixture=bool(fixture),profile=p,requests=rows,code=code_bindings(),prepared_at=pa.now_utc(),
        **scope_fields(dict(scope=scope)))
    _seal_file(root/'prepared.json',value)
    return value


def verify(work, binding, manifest_path, *, for_execution=True):
    root=absolute(work)/'enrichment'; v=read_bound(root/'prepared.json')
    require(v['binding']==binding and v['manifest_sha256']==sha(manifest_path), 'prepared-plan-binding')
    require(v.get('schema') == 'portable-enrichment-plan-v2', 'unsupported-portable-enrichment-format')
    trusted_modules()
    from pdf_enrichment.trusted import validate_code_provenance
    validate_code_provenance(v['code'])
    if for_execution:
        require(v['code']==code_bindings(), 'adapter-or-dependency-code-changed')
    p=profile(v['profile']); m=pa.validate_manifest(pa.load(manifest_path))
    pa.verify_source(manifest_path)
    source_scope(m,v['roster'],v['fixture'],v.get('scope','production'))
    if scope_fields(v):
        require(all(v.get(k)==x for k,x in scope_fields(v).items()), 'diagnostic-status-binding')
    keys=pa.closure_for(m,v['roster']) if v['roster'] else set(m['common_dependencies'])
    _,paths=pa.verify_local(manifest_path,keys)
    es={e['element_id']:e for e in m['elements']}
    require([r['element_id'] for r in v['requests']]==v['roster'], 'request-roster-binding')
    for row in v['requests']:
        d=inside(root,row['directory']); e=es[row['element_id']]
        require(row['kind']==e['kind'] and row['document']==e['document'] and row['source_sha256']==e['source_sha256'] and row['caption_only'] is False,'request-source-binding')
        wire,ev,prompt=wire_for(e,paths,p)
        require(pa.load(d/'request-wire.json')==wire and pa.load(d/'source-evidence.json')==ev and
                (d/'prompt.txt').read_text()==prompt, 'prepared-payload-regeneration-mismatch')
        for name,key in (('request-wire.json','request_sha256'),('source-evidence.json','evidence_sha256'),('prompt.txt','prompt_sha256')):
            require(sha(d/name)==row[key], 'prepared-file-changed')
    return v


def count(work,binding,manifest_path,cache=None,receipt=None):
    v=verify(work,binding,manifest_path); root=absolute(work)/'enrichment'
    require(not (root/'count-start.json').exists(), 'count-interrupted-or-already-consumed-new-run-required')
    results={}; p=v['profile']; provenance={}
    require(receipt is None or p['counting']=='operator-exact-count-receipt', 'count-receipt-not-for-official-counter')
    if not v['requests']:
        provenance={'kind':'zero-eligible-no-count-needed'}
    elif p['counting']=='official-qwen-processor':
        require(cache, 'official-processor-cache-required')
        from pdf_enrichment import trusted, live
        counter_module=trusted.module('counting',trusted_modules()['pdf_source_package'])
        require(counter_module.SETTINGS['max_tokens']==p['max_tokens'] and counter_module.LIMIT==p['context_limit'], 'counter-profile-mismatch')
        provenance=live.assets(cache,counter_module)
        counter=counter_module.Counter(counter_module.processor(cache))
    else:
        require(receipt, 'exact-count-receipt-required')
        supplied=pa.load(receipt)
        require(set(supplied)=={'schema','prepared_sha256','model','requests','attestation','evidence'},'count-receipt-fields')
        require(supplied['schema']=='portable-exact-count-input-v1' and supplied['prepared_sha256']==sha(root/'prepared.json') and
                supplied['model']==p['model'], 'count-receipt-binding')
        require(isinstance(supplied['attestation'],str) and supplied['attestation'].strip(),'count-attestation-required')
        evidence=supplied['evidence']; require(set(evidence)=={'path','sha256','method'},'count-evidence-fields')
        require(sha(evidence['path'])==evidence['sha256'] and evidence['method'] in ('official-processor','provider-count-api'),'exact-count-evidence-required')
        require(set(supplied['requests'])=={r['id'] for r in v['requests']}, 'count-roster-binding')
        provenance=dict(kind='operator-supplied-exact-count; checked-against-returned-usage-at-execution',
                        receipt=supplied,evidence_sha256=evidence['sha256'])
    pa.save(root/'count-start.json',dict(prepared_sha256=sha(root/'prepared.json'),started_at=pa.now_utc()))
    if receipt:
        pa.put(root/'count-input.json',absolute(receipt).read_bytes())
        pa.put(root/'count-evidence.bin',absolute(supplied['evidence']['path']).read_bytes())
    for row in v['requests']:
        if p['counting']=='official-qwen-processor':
            c=counter.count(pa.load(root/row['directory']/'request-wire.json')); n=c['prompt_tokens_local']
        else:
            c=supplied['requests'][row['id']]
            require(set(c)=={'request_sha256','prompt_tokens'},'exact-count-row-fields')
            require(c['request_sha256']==row['request_sha256'],'count-request-binding'); n=c['prompt_tokens']
        require(type(n) is int and n>0,'positive-exact-prompt-count')
        results[row['id']]=dict(request_sha256=row['request_sha256'],prompt_tokens=n,
            max_tokens=p['max_tokens'],context_limit=p['context_limit'],fits=n+p['max_tokens']<=p['context_limit'])
    value=dict(schema='portable-count-v2',prepared_sha256=sha(root/'prepared.json'),requests=results,provenance=provenance)
    _seal_file(root/'counts.json',value)
    return value


def verify_counts(root,v):
    c=read_bound(root/'counts.json')
    require(c.get('schema') == 'portable-count-v2', 'unsupported-portable-count-format')
    require(c['prepared_sha256']==sha(root/'prepared.json') and set(c['requests'])=={r['id'] for r in v['requests']},'count-plan-roster-binding')
    for row in v['requests']:
        n=c['requests'][row['id']]; p=v['profile']
        require(type(n['prompt_tokens']) is int and n['prompt_tokens']>0 and n['request_sha256']==row['request_sha256'] and
                n['max_tokens']==p['max_tokens'] and n['context_limit']==p['context_limit'] and
                n['fits']==(n['prompt_tokens']+p['max_tokens']<=p['context_limit']), 'count-profile-binding')
    if v['profile']['counting']=='official-qwen-processor' and v['requests']:
        from pdf_enrichment import trusted
        from pdf_enrichment.io import sha as asset_sha
        module=trusted.module('counting',trusted_modules()['pdf_source_package'])
        assets=c['provenance']; asset_root=absolute(assets['root'])
        # The explicitly trusted HF cache uses snapshot symlinks to blobs.
        # This read-only code dependency is not an archive input/output path.
        require(assets['revision']==module.REVISION and assets['model_repo']==module.MODEL_REPO and
                {p.name:asset_sha(p) for p in sorted(asset_root.iterdir()) if p.is_file()}==assets['files'], 'official-counter-assets-changed')
    if v['profile']['counting']=='operator-exact-count-receipt' and v['requests']:
        supplied=c['provenance']['receipt']
        require(pa.load(root/'count-input.json')==supplied and sha(root/'count-evidence.bin')==supplied['evidence']['sha256'],'count-input-evidence-changed')
        for row in v['requests']:
            require(supplied['requests'][row['id']]['prompt_tokens']==c['requests'][row['id']]['prompt_tokens'],'count-import-binding')
    return c


def seal(work,binding,manifest_path):
    v=verify(work,binding,manifest_path); root=absolute(work)/'enrichment'; c=verify_counts(root,v)
    require(all(x['fits'] for x in c['requests'].values()), 'full-payload-context-overflow-no-trimming')
    value=dict(schema='portable-enrichment-seal-v2',binding=binding,prepared_sha256=sha(root/'prepared.json'),
        counts_sha256=sha(root/'counts.json'),fixture=v['fixture'],profile=v['profile'],requests=v['requests'],**scope_fields(v))
    _seal_file(root/'seal.json',value)
    template=dict(schema='portable-enrichment-approval-v2',seal_sha256=sha(root/'seal.json'),binding=binding,
        profile=v['profile'],fixture=v['fixture'],approved=False,approved_by=None,
        source_payload_counts_reviewed=False,endpoint=None,credential_env=None,
        maximum_posts=len(v['requests']),maximum_total_tokens=sum(x['prompt_tokens']+x['max_tokens'] for x in c['requests'].values()),
        timeout_seconds=1200,retries=0,**scope_fields(v))
    pa.save(root/'approval.template.json',template)
    return template


def approval(root,v,value):
    require(set(value)==set(pa.load(root/'approval.template.json')), 'approval-fields')
    require(all(value.get(k)==x for k,x in scope_fields(v).items()), 'diagnostic-approval-scope-binding')
    c=verify_counts(root,v); s=read_bound(root/'seal.json')
    require(s==dict(schema='portable-enrichment-seal-v2',binding=v['binding'],prepared_sha256=sha(root/'prepared.json'),
        counts_sha256=sha(root/'counts.json'),fixture=v['fixture'],profile=v['profile'],requests=v['requests'],**scope_fields(v)), 'seal-bindings-changed')
    require(value['schema']=='portable-enrichment-approval-v2' and all(x['fits'] for x in c['requests'].values()), 'approval-schema-or-context-overflow')
    require(value['seal_sha256']==sha(root/'seal.json') and value['binding']==v['binding'] and
        value['profile']==v['profile'] and value['fixture'] is v['fixture'] and value['timeout_seconds']==1200 and value['retries']==0,'approval-binding')
    require(value['approved'] is True and value['source_payload_counts_reviewed'] is True and
            isinstance(value['approved_by'],str) and value['approved_by'].strip(),'explicit-parent-approval-required')
    require(type(value['maximum_posts']) is int and value['maximum_posts']>=len(v['requests']) and
        type(value['maximum_total_tokens']) is int and value['maximum_total_tokens']>=sum(x['prompt_tokens']+x['max_tokens'] for x in c['requests'].values()),'approved-budget-insufficient')
    endpoint=value['endpoint']
    require(isinstance(endpoint,str) and endpoint and not any(c.isspace() or ord(c)<32 or ord(c)==127 for c in endpoint),
            'safe-explicit-endpoint-required')
    try:
        u=urlsplit(endpoint)
        valid=(u.scheme in ('http','https') and u.hostname and u.username is None and u.password is None and
               '?' not in endpoint and '#' not in endpoint and '\\' not in endpoint and
               not u.netloc.endswith(':') and (u.port is None or 0<u.port<=65535))
    except ValueError:
        valid=False
    require(valid,'safe-explicit-endpoint-required')
    require(isinstance(value['credential_env'],str) and re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',value['credential_env']),'credential-env-name-required')
    return c


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None


def _post(payload,value):
    key=os.environ.get(value['credential_env']); require(key,'runtime-credential-unavailable')
    req=urllib.request.Request(value['endpoint'],data=payload,method='POST',
        headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
    opener=urllib.request.build_opener(NoRedirect(),urllib.request.ProxyHandler({}))
    try:
        with opener.open(req,timeout=value['timeout_seconds']) as response:
            raw=response.read(32*1024*1024+1); status=response.status
    except urllib.error.HTTPError as exc:
        raw=exc.read(32*1024*1024+1); status=exc.code
    require(len(raw)<=32*1024*1024,'response-size-limit')
    from pdf_enrichment import trusted
    raw,redacted=trusted.module('compact',trusted_modules()['pdf_source_package']).redact_response(raw,key)
    return dict(raw=raw,http_status=status,credential_echo_redacted=redacted)


def _response(row,ev,raw,p,expected_tokens,fixture):
    from pdf_enrichment import importer
    # Strict JSON and exact model/count checks are independent of the pinned v7 envelope.
    from pdf_enrichment.io import strict
    env=strict(raw)
    require(isinstance(env,dict),'response-envelope')
    require(env.get('model')==p['model'],'response-model-mismatch')
    choices=env.get('choices'); require(isinstance(choices,list) and len(choices)==1,'response-choices')
    require(choices[0]['finish_reason']=='stop','non-stop-finish-reason')
    text=choices[0]['message']['content']; require(isinstance(text,str) and text.strip(),'response-content')
    usage=env.get('usage'); require(isinstance(usage,dict) and all(type(usage.get(k)) is int and usage[k]>=0 for k in ('prompt_tokens','completion_tokens','total_tokens')),'response-usage')
    require(usage['prompt_tokens']==expected_tokens and usage['completion_tokens']<=p['max_tokens'] and
        usage['total_tokens']==usage['prompt_tokens']+usage['completion_tokens'],'response-usage-count-mismatch')
    return importer.assemble_response(row,ev,text,fixture),usage


def execute(work,binding,manifest_path,approval_path,*,authorize=False,fixture_transport=None):
    v=verify(work,binding,manifest_path); root=absolute(work)/'enrichment'
    value=pa.load(approval_path); counts=approval(root,v,value)
    fixture=fixture_transport is not None
    require(v['fixture'] is fixture,'fixture-cannot-be-live-promoted')
    if fixture:
        require(os.environ.get('PDF_ENRICHMENT_OFFLINE')=='1','fixture-offline-required')
    else:
        require(authorize is True and not os.environ.get('PDF_ENRICHMENT_OFFLINE') and
            not os.environ.get('PDF_SOURCE_PACKAGE_OFFLINE'),'explicit-live-authorization-required')
    if (root/'execution-start.json').exists():
        require(sha(approval_path)==sha(root/'executed-approval.json'),'execution-approval-changed')
        state=execution_state(work,binding,manifest_path)
        require(not state['accounting']['integrity_hold'],'execution-integrity-hold-new-run-required')
    else:
        pa.put(root/'executed-approval.json',absolute(approval_path).read_bytes())
        _seal_file(root/'execution-start.json',dict(approval_sha256=sha(root/'executed-approval.json'),fixture=fixture,
            binding=binding,started_at=pa.now_utc(),origin='offline-inference-double' if fixture else 'parent-authorized-live'))
    for row in v['requests']:
        verify(work,binding,manifest_path); approval(root,v,pa.load(root/'executed-approval.json'))
        require(sha(approval_path)==sha(root/'executed-approval.json'),'execution-approval-changed')
        # Revalidate all prior outcomes before another post. A consumed request
        # is never posted again, including an interrupted write or lost response.
        state=execution_state(work,binding,manifest_path)
        if state['accounting']['requests'][row['id']]['status']!='pending': continue
        d=root/row['directory']; raw=(d/'request-wire.json').read_bytes()
        _seal_file(d/'reservation.json',dict(status='reserved-may-have-posted',request_sha256=row['request_sha256'],
            approval_sha256=sha(root/'executed-approval.json'),started_at=pa.now_utc()))
        try:
            result=fixture_transport(raw,row) if fixture else _post(raw,value)
        except (OSError,ValueError) as exc:
            # Never save exception text: transports may include credentials.
            fatal=isinstance(exc,ValueError)
            _seal_file(d/'failure.json',dict(status='uncertain',reason=type(exc).__name__,fatal=fatal,
                reservation_sha256=sha(d/'reservation.json'),response_sha256=None))
            if fatal: raise
            continue
        pa.put(d/'response-body.json',result['raw'])
        try:
            require(result['http_status']==200,'http-failure')
            outcome,usage=_response(row,pa.load(d/'source-evidence.json'),result['raw'],v['profile'],counts['requests'][row['id']]['prompt_tokens'],fixture)
        except (ValueError,KeyError,TypeError,IndexError) as exc:
            fatal=(str(exc) in ('response-model-mismatch','response-usage-count-mismatch') or
                   result['http_status'] in (301,302,303,307,308,401,403))
            _seal_file(d/'failure.json',dict(status='failed',reason='response-rejected',fatal=fatal,http_status=result['http_status'],
                reservation_sha256=sha(d/'reservation.json'),response_sha256=sha(d/'response-body.json')))
            if fatal: raise
            continue
        _seal_file(d/'outcome.json',dict(outcome=outcome,usage=usage,returned_model=v['profile']['model'],
            fixture=fixture,response_sha256=sha(d/'response-body.json'),request_sha256=row['request_sha256'],**scope_fields(v)))
    state=execution_state(work,binding,manifest_path)
    if state['accounting']['complete'] and not (root/'execution-complete.json').exists():
        _seal_file(root/'execution-complete.json',dict(binding=binding,fixture=fixture,
            outcomes={r['id']:sha(root/r['directory']/'outcome.json') for r in v['requests']},finished_at=pa.now_utc(),**scope_fields(v)))
    return state


def execution_state(work,binding,manifest_path):
    """Recompute request accounting from immutable reservations and outcomes."""
    return _execution_state(work,binding,manifest_path,verify(work,binding,manifest_path,for_execution=False))


def _execution_state(work,binding,manifest_path,v):
    # Caller owns this operation's already-verified preparation. Never persist it.
    root=absolute(work)/'enrichment'
    start=read_bound(root/'execution-start.json'); a=pa.load(root/'executed-approval.json')
    require(start['approval_sha256']==sha(root/'executed-approval.json') and start['binding']==binding and start['fixture'] is v['fixture'],'execution-start-binding')
    counts=approval(root,v,a); result=[]; rows={}; hashes={}; integrity_hold=False
    m=pa.load(manifest_path); es={e['element_id']:e for e in m['elements']}
    for row in v['requests']:
        d=root/row['directory']; status=dict(element_id=row['element_id'],status='pending')
        rows[row['id']]=status
        if not (d/'reservation.json').exists():
            require(not any((d/n).exists() for n in ('outcome.json','response-body.json','failure.json')),'response-without-reservation')
            continue
        reservation=read_bound(d/'reservation.json')
        require(reservation['request_sha256']==row['request_sha256'] and reservation['approval_sha256']==sha(root/'executed-approval.json'),'outcome-reservation-binding')
        status.update(status='uncertain',reservation_sha256=sha(d/'reservation.json'))
        if (d/'failure.json').exists():
            failure=read_bound(d/'failure.json')
            require(failure['reservation_sha256']==sha(d/'reservation.json') and failure['status'] in ('failed','uncertain') and
                type(failure['fatal']) is bool and not (d/'outcome.json').exists(),'failure-reservation-binding')
            require(failure['response_sha256']==(sha(d/'response-body.json') if (d/'response-body.json').exists() else None),'failure-response-binding')
            status.update(status=failure['status'],failure=failure,failure_sha256=sha(d/'failure.json'))
            integrity_hold |= failure['fatal']
            continue
        if not (d/'outcome.json').exists(): continue
        saved=read_bound(d/'outcome.json')
        require(all(saved.get(k)==x for k,x in scope_fields(v).items()), 'diagnostic-outcome-scope-binding')
        require(saved['response_sha256']==sha(d/'response-body.json') and
                saved['request_sha256']==row['request_sha256'] and saved['fixture'] is v['fixture'],'outcome-reservation-binding')
        ev=pa.load(d/'source-evidence.json')
        recomputed,usage=_response(row,ev,(d/'response-body.json').read_bytes(),v['profile'],counts['requests'][row['id']]['prompt_tokens'],v['fixture'])
        require(saved['outcome']==recomputed and saved['usage']==usage and saved['returned_model']==v['profile']['model'],'outcome-recomputation-mismatch')
        status.update(status='completed',outcome_sha256=sha(d/'outcome.json')); hashes[row['id']]=sha(d/'outcome.json')
        e=es[row['element_id']]
        result.append(dict(element_id=row['element_id'],source_sha256=row['source_sha256'],document=row['document'],
            content_type=e['content_type'],outcome=recomputed,evidence=ev,source_element=e['source_element'],source_pdf=None,**scope_fields(v)))
    accounting=dict(requests=rows,counts={s:sum(r['status']==s for r in rows.values()) for s in ('pending','uncertain','failed','completed')},
        complete=len(hashes)==len(v['requests']),integrity_hold=integrity_hold)
    if (root/'execution-complete.json').exists():
        complete=read_bound(root/'execution-complete.json')
        require(complete['binding']==binding and complete['fixture'] is v['fixture'] and accounting['complete'] and
            complete['outcomes']==hashes,'execution-completion-binding')
        require(all(complete.get(k)==x for k,x in scope_fields(v).items()),'diagnostic-completion-scope-binding')
    return dict(elements=result,accounting=accounting)


def outcomes(work,binding,manifest_path):
    return execution_state(work,binding,manifest_path)['elements']


def review_create(work,binding,manifest_path):
    state=execution_state(work,binding,manifest_path); elements=state['elements']
    require(elements or state['accounting']['complete'],'no-successful-material-to-review')
    from qualified_enrichment import reviews, records
    root=pa.new_directory(absolute(work)/'review')
    dossier=dict(schema='portable-review-dossier-v2',binding=binding,request_accounting=state['accounting'],
        snapshot=dict(source_package='portable:'+sha(manifest_path),elements=elements),notice=reviews.NOTICE)
    _seal_file(root/'dossier.json',dossier)
    packet=reviews.packet_value(dossier,sha(root/'dossier.json'),[e['element_id'] for e in elements],8000000) if elements else None
    if packet: pa.save(root/'packet.json',packet)
    (root/'decisions').mkdir()
    return dossier


def review_verify(work,binding,manifest_path):
    return _review_verify(work,binding,manifest_path,execution_state(work,binding,manifest_path))


def _review_verify(work,binding,manifest_path,state):
    root=absolute(work)/'review'
    dossier=read_bound(root/'dossier.json')
    require(dossier.get('schema') == 'portable-review-dossier-v2', 'unsupported-portable-dossier-format')
    # An immutable partial review remains readable if untouched siblings later
    # finish; it never expands its reviewed scope or completion claim.
    ids={e['element_id'] for e in dossier['snapshot']['elements']}
    elements=[e for e in state['elements'] if e['element_id'] in ids]
    saved=dossier['request_accounting']; current=state['accounting']
    require(set(saved['requests'])==set(current['requests']) and all(
        row==current['requests'][rid] or row['status']=='pending' for rid,row in saved['requests'].items()),'review-accounting-changed')
    require(dossier['binding']==binding and dossier['snapshot']['elements']==elements and
        dossier['snapshot']['source_package']=='portable:'+sha(manifest_path),'review-source-or-outcome-changed')
    from qualified_enrichment import reviews
    require(dossier['notice']==reviews.NOTICE,'review-notice-binding')
    entries=[]; previous=sha(root/'dossier.json')
    for i,path in enumerate(sorted((root/'decisions').glob('*.json')),1):
        entry=read_bound(path)
        require(path.name==f'{i:06d}.json' and entry['previous_sha256']==previous and entry['sequence']==i and
            entry['dossier_sha256']==sha(root/'dossier.json'),'review-history-binding')
        entries.append(entry); previous=sha(path)
    views=reviews.apply(dossier,entries)
    return dossier,entries,views


def review_import(work,binding,manifest_path,submission_path):
    root=absolute(work)/'review'; dossier,entries,_=review_verify(work,binding,manifest_path)
    require(not (absolute(work)/'export').exists(),'export-frozen-new-run-required')
    from qualified_enrichment import reviews
    packet=pa.load(root/'packet.json'); submission=pa.load(submission_path)
    require(packet==reviews.packet_value(dossier,sha(root/'dossier.json'),[e['element_id'] for e in dossier['snapshot']['elements']],8000000),'review-packet-changed')
    entry=dict(sequence=len(entries)+1,previous_sha256=sha(root/'decisions'/f'{len(entries):06d}.json') if entries else sha(root/'dossier.json'),
        dossier_sha256=sha(root/'dossier.json'),packet=packet,submission=submission,input_sha256=sha(submission_path),imported_at=pa.now_utc())
    reviews.apply(dossier,entries+[entry])
    _seal_file(root/'decisions'/f'{len(entries)+1:06d}.json',entry)
    return entry


def export(work,binding,manifest_path):
    root=absolute(work); dossier,entries,views=review_verify(work,binding,manifest_path)
    from qualified_enrichment.exports import exact_view,content_targets
    # An explicit review import is required for nonempty runs; empty findings
    # are an attributed review, never a correctness certificate.
    require(entries or not views,'operator-review-import-required')
    v=read_bound(root/'enrichment'/'prepared.json')
    prior=pa.consume(manifest_path,v['roster']) if v['roster'] else pa.consume(manifest_path)
    for view in views:
        view['consumer_views']=[exact_view(view,p) for p in content_targets(view['outcome'])]
    v=read_bound(root/'enrichment'/'prepared.json')
    value=dict(schema='portable-qualified-export-v3',binding=binding,fixture=v['fixture'],profile=v['profile'],
        roster=v['roster'],elements=views,execution_complete=dossier['request_accounting']['complete'],
        request_accounting=dossier['request_accounting'],inherited_history=prior['history'],dispositions=prior['dispositions'],
        source_status=prior['source_status'],review_bindings=tree(root/'review'),
        scientific_acceptance='not-established',notice='Prior findings and review history remain active; a new outcome never resolves them automatically.',**scope_fields(v))
    destination=pa.new_directory(root/'export'); _seal_file(destination/'handoff.json',value)
    import html
    pa.put(destination/'annotated.html',('<!doctype html><html lang="en"><meta charset="utf-8"><title>Qualified article evidence</title><pre>'+html.escape(json.dumps(value,indent=2))+'</pre></html>').encode())
    return value


def consumer(work, binding, manifest_path, element_id, target='', *, purpose='discovery', qualification=None):
    """Portable exact-use boundary; old uncertainty cannot be erased by a new view."""
    value=verify_export(work,binding,manifest_path)
    views={e['element_id']:e for e in value['elements']}
    require(element_id in views,'consumer-element-outside-request')
    if purpose in ('exact','algorithm-specification') and value['inherited_history']:
        require(isinstance(qualification,str) and qualification.strip(),'inherited-history-requires-explicit-qualification')
    from qualified_enrichment.exports import exact_view
    result=exact_view(views[element_id],target,purpose=purpose,qualification=qualification)
    result.update(inherited_history=value['inherited_history'],source_status=value['source_status'],
        request_accounting=value['request_accounting'],execution_complete=value['execution_complete'],
        dispositions=value['dispositions'],prior_findings_automatically_resolved=False,fixture=value['fixture'],**scope_fields(value))
    return result


def verify_export(work,binding,manifest_path):
    return _verify_export(work,binding,manifest_path,review_verify(work,binding,manifest_path))


def _verify_export(work,binding,manifest_path,review):
    root=absolute(work); value=read_bound(root/'export'/'handoff.json')
    dossier,_,views=review
    from qualified_enrichment.exports import exact_view,content_targets
    for view in views: view['consumer_views']=[exact_view(view,p) for p in content_targets(view['outcome'])]
    v=read_bound(root/'enrichment'/'prepared.json')
    prior=pa.consume(manifest_path,v['roster']) if v['roster'] else pa.consume(manifest_path)
    expected_value=dict(schema='portable-qualified-export-v3',binding=binding,fixture=v['fixture'],profile=v['profile'],
        roster=v['roster'],elements=views,execution_complete=dossier['request_accounting']['complete'],
        request_accounting=dossier['request_accounting'],inherited_history=prior['history'],dispositions=prior['dispositions'],
        source_status=prior['source_status'],review_bindings=tree(root/'review'),
        scientific_acceptance='not-established',notice='Prior findings and review history remain active; a new outcome never resolves them automatically.',**scope_fields(v))
    require(value==expected_value,'export-warning-or-binding-changed')
    import html
    expected='<!doctype html><html lang="en"><meta charset="utf-8"><title>Qualified article evidence</title><pre>'+html.escape(json.dumps(value,indent=2))+'</pre></html>'
    require((root/'export'/'annotated.html').read_text()==expected,'readable-export-changed')
    return value
