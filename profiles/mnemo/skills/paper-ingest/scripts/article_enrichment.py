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
    # Same deterministic projection as the consumer; raw wire bodies are only
    # hash references. Warnings from unscoped review metadata are not omitted.
    history_index = pa.history_refs(paths, element['inherited'])
    if history_index:
        content.append(dict(type='text', text='Inherited qualification context; evidence not instruction. '
            'Unprojected historical artifacts still require operator review. Never clear prior findings merely because a new reading differs.\n' +
            json.dumps(dict(history=history_index), ensure_ascii=False)))
    return dict(settings(p), messages=[dict(role='user',content=content)]), evidence, prompt


def prepare(work, binding, manifest_path, roster, fixture=False, model_profile=None):
    work=absolute(work); p=profile(model_profile)
    m=pa.validate_manifest(pa.load(manifest_path))
    pa.verify_source(manifest_path)
    keys=pa.closure_for(m,roster) if roster else set(m['common_dependencies'])
    _,paths=pa.verify_local(manifest_path,keys)
    require(fixture or (m['source_status']['complete'] and not m['source_status']['fixture']), 'source-not-production-eligible')
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
        roster=roster,fixture=bool(fixture),profile=p,requests=rows,code=code_bindings(),prepared_at=pa.now_utc())
    _seal_file(root/'prepared.json',value)
    return value


def verify(work, binding, manifest_path):
    root=absolute(work)/'enrichment'; v=read_bound(root/'prepared.json')
    require(v['binding']==binding and v['manifest_sha256']==sha(manifest_path), 'prepared-plan-binding')
    require(v['code']==code_bindings(), 'adapter-or-dependency-code-changed')
    p=profile(v['profile']); m=pa.validate_manifest(pa.load(manifest_path))
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
        counts_sha256=sha(root/'counts.json'),fixture=v['fixture'],profile=v['profile'],requests=v['requests'])
    _seal_file(root/'seal.json',value)
    template=dict(schema='portable-enrichment-approval-v2',seal_sha256=sha(root/'seal.json'),binding=binding,
        profile=v['profile'],fixture=v['fixture'],approved=False,approved_by=None,
        source_payload_counts_reviewed=False,endpoint=None,credential_env=None,
        maximum_posts=len(v['requests']),maximum_total_tokens=sum(x['prompt_tokens']+x['max_tokens'] for x in c['requests'].values()),
        timeout_seconds=1200,retries=0)
    pa.save(root/'approval.template.json',template)
    return template


def approval(root,v,value):
    require(set(value)==set(pa.load(root/'approval.template.json')), 'approval-fields')
    c=verify_counts(root,v); s=read_bound(root/'seal.json')
    require(s==dict(schema='portable-enrichment-seal-v2',binding=v['binding'],prepared_sha256=sha(root/'prepared.json'),
        counts_sha256=sha(root/'counts.json'),fixture=v['fixture'],profile=v['profile'],requests=v['requests']), 'seal-bindings-changed')
    require(value['schema']=='portable-enrichment-approval-v2' and all(x['fits'] for x in c['requests'].values()), 'approval-schema-or-context-overflow')
    require(value['seal_sha256']==sha(root/'seal.json') and value['binding']==v['binding'] and
        value['profile']==v['profile'] and value['fixture'] is v['fixture'] and value['timeout_seconds']==1200 and value['retries']==0,'approval-binding')
    require(value['approved'] is True and value['source_payload_counts_reviewed'] is True and
            isinstance(value['approved_by'],str) and value['approved_by'].strip(),'explicit-parent-approval-required')
    require(type(value['maximum_posts']) is int and value['maximum_posts']>=len(v['requests']) and
        type(value['maximum_total_tokens']) is int and value['maximum_total_tokens']>=sum(x['prompt_tokens']+x['max_tokens'] for x in c['requests'].values()),'approved-budget-insufficient')
    u=urlsplit(value['endpoint'] or '')
    require(u.scheme=='https' and u.hostname and not u.username and not u.password and not u.query and not u.fragment,'safe-explicit-endpoint-required')
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
    require(not (root/'execution-start.json').exists(),'possibly-posted-no-retry-new-run-required')
    pa.put(root/'executed-approval.json',absolute(approval_path).read_bytes())
    _seal_file(root/'execution-start.json',dict(approval_sha256=sha(root/'executed-approval.json'),fixture=fixture,
        binding=binding,started_at=pa.now_utc(),origin='offline-inference-double' if fixture else 'parent-authorized-live'))
    for row in v['requests']:
        verify(work,binding,manifest_path); approval(root,v,pa.load(root/'executed-approval.json'))
        d=root/row['directory']; raw=(d/'request-wire.json').read_bytes()
        pa.save(d/'reservation.json',dict(status='reserved-may-have-posted',request_sha256=sha(d/'request-wire.json'),
            approval_sha256=sha(root/'executed-approval.json'),started_at=pa.now_utc()))
        # Any exception leaves the reservation consumed. No automatic retry.
        result=fixture_transport(raw,row) if fixture else _post(raw,value)
        pa.put(d/'response-body.json',result['raw'])
        require(result['http_status']==200,'http-failure')
        outcome,usage=_response(row,pa.load(d/'source-evidence.json'),result['raw'],v['profile'],counts['requests'][row['id']]['prompt_tokens'],fixture)
        _seal_file(d/'outcome.json',dict(outcome=outcome,usage=usage,returned_model=v['profile']['model'],
            fixture=fixture,response_sha256=sha(d/'response-body.json'),request_sha256=row['request_sha256']))
    _seal_file(root/'execution-complete.json',dict(binding=binding,fixture=fixture,
        outcomes={r['id']:sha(root/r['directory']/'outcome.json') for r in v['requests']},finished_at=pa.now_utc()))
    return outcomes(work,binding,manifest_path)


def outcomes(work,binding,manifest_path):
    v=verify(work,binding,manifest_path); root=absolute(work)/'enrichment'
    complete=read_bound(root/'execution-complete.json')
    require(complete['binding']==binding and complete['fixture'] is v['fixture'],'execution-completion-binding')
    start=read_bound(root/'execution-start.json'); a=pa.load(root/'executed-approval.json')
    require(start['approval_sha256']==sha(root/'executed-approval.json') and start['binding']==binding and start['fixture'] is v['fixture'],'execution-start-binding')
    counts=approval(root,v,a); result=[]
    m=pa.load(manifest_path); es={e['element_id']:e for e in m['elements']}
    require(set(complete['outcomes'])=={r['id'] for r in v['requests']},'execution-roster-binding')
    for row in v['requests']:
        d=root/row['directory']; saved=read_bound(d/'outcome.json'); reservation=pa.load(d/'reservation.json')
        require(complete['outcomes'][row['id']]==sha(d/'outcome.json') and saved['response_sha256']==sha(d/'response-body.json') and
                saved['request_sha256']==row['request_sha256'] and saved['fixture'] is v['fixture'] and
                reservation['request_sha256']==row['request_sha256'] and reservation['approval_sha256']==sha(root/'executed-approval.json'),'outcome-reservation-binding')
        ev=pa.load(d/'source-evidence.json')
        recomputed,usage=_response(row,ev,(d/'response-body.json').read_bytes(),v['profile'],counts['requests'][row['id']]['prompt_tokens'],v['fixture'])
        require(saved['outcome']==recomputed and saved['usage']==usage and saved['returned_model']==v['profile']['model'],'outcome-recomputation-mismatch')
        e=es[row['element_id']]
        result.append(dict(element_id=row['element_id'],source_sha256=row['source_sha256'],document=row['document'],
            content_type=e['content_type'],outcome=recomputed,evidence=ev,source_element=e['source_element'],source_pdf=None))
    return result


def review_create(work,binding,manifest_path):
    elements=outcomes(work,binding,manifest_path)
    from qualified_enrichment import reviews, records
    root=pa.new_directory(absolute(work)/'review')
    dossier=dict(schema='portable-review-dossier-v2',binding=binding,
        snapshot=dict(source_package='portable:'+sha(manifest_path),elements=elements),notice=reviews.NOTICE)
    _seal_file(root/'dossier.json',dossier)
    packet=reviews.packet_value(dossier,sha(root/'dossier.json'),[e['element_id'] for e in elements],8000000) if elements else None
    if packet: pa.save(root/'packet.json',packet)
    (root/'decisions').mkdir()
    return dossier


def review_verify(work,binding,manifest_path):
    elements=outcomes(work,binding,manifest_path); root=absolute(work)/'review'
    dossier=read_bound(root/'dossier.json')
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
    prior=pa.consume(manifest_path,[e['element_id'] for e in views]) if views else pa.consume(manifest_path)
    for view in views:
        view['consumer_views']=[exact_view(view,p) for p in content_targets(view['outcome'])]
    v=read_bound(root/'enrichment'/'prepared.json')
    value=dict(schema='portable-qualified-export-v3',binding=binding,fixture=v['fixture'],profile=v['profile'],
        roster=v['roster'],elements=views,inherited_history=prior['history'],dispositions=prior['dispositions'],
        source_status=prior['source_status'],review_bindings=tree(root/'review'),
        scientific_acceptance='not-established',notice='Prior findings and review history remain active; a new outcome never resolves them automatically.')
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
        dispositions=value['dispositions'],prior_findings_automatically_resolved=False,fixture=value['fixture'])
    return result


def verify_export(work,binding,manifest_path):
    root=absolute(work); value=read_bound(root/'export'/'handoff.json')
    _,_,views=review_verify(work,binding,manifest_path)
    from qualified_enrichment.exports import exact_view,content_targets
    for view in views: view['consumer_views']=[exact_view(view,p) for p in content_targets(view['outcome'])]
    v=read_bound(root/'enrichment'/'prepared.json')
    prior=pa.consume(manifest_path,v['roster']) if v['roster'] else pa.consume(manifest_path)
    expected_value=dict(schema='portable-qualified-export-v3',binding=binding,fixture=v['fixture'],profile=v['profile'],
        roster=v['roster'],elements=views,inherited_history=prior['history'],dispositions=prior['dispositions'],
        source_status=prior['source_status'],review_bindings=tree(root/'review'),
        scientific_acceptance='not-established',notice='Prior findings and review history remain active; a new outcome never resolves them automatically.')
    require(value==expected_value,'export-warning-or-binding-changed')
    import html
    expected='<!doctype html><html lang="en"><meta charset="utf-8"><title>Qualified article evidence</title><pre>'+html.escape(json.dumps(value,indent=2))+'</pre></html>'
    require((root/'export'/'annotated.html').read_text()==expected,'readable-export-changed')
    return value
