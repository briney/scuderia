"""One full/selective article refresh path with executable operator continuations.

execute is status/resume validation, not implied authorization to post or apply.
Each mutating stage is explicit. Inference never retries a consumed request.
Immutable plan, input hashes, code bindings and append-only stage receipts bind
all continuations. Scientific prose and reviews remain operator-authored inputs.
"""
from __future__ import annotations
import argparse
import copy
from dataclasses import dataclass
import difflib
import json
import os
from pathlib import Path
import re
import sys

import portable_articles as pa
import article_enrichment as ae
from article_runtime import require, absolute, sha, digest, tree, external, locked

SCHEMA_PLAN='reenrich-plan-v2'
DIAGNOSTIC_PLAN='reenrich-diagnostic-plan-v1'
STAGES=('acquisition','source-preparation','enrichment','review-export','page-reconciliation','archive-publication')


@dataclass
class Request:
    article: str
    elements: list | None = None
    page: Path | None = None
    def __post_init__(self):
        pa.article_key(dict(slug=self.article))
        require(self.elements is None or isinstance(self.elements,list) and self.elements and
            all(isinstance(e,str) and e for e in self.elements) and len(self.elements)==len(set(self.elements)), 'empty-or-invalid-selection-rejected')
        if self.page is not None:
            self.page=absolute(self.page)
            require(self.page.is_file() and self.page.suffix=='.md','paper-page-required')


def _resolve_elements(manifest,elements):
    index={e['element_id']:e for e in manifest['elements']}; result=[]
    for selector in elements:
        matches=[selector] if selector in index else [e['element_id'] for e in manifest['elements'] if e.get('label')==selector]
        require(matches,'unknown-element:'+selector); require(len(matches)==1,'ambiguous-label:'+selector)
        require(index[matches[0]]['eligible'],'selected-element-ineligible:'+selector)
        result.append(matches[0])
    require(len(result)==len(set(result)),'duplicate-element-selector')
    return result


def _sections(text):
    # Only actual Markdown headings are editable boundaries. Frontmatter,
    # fenced code and multiline annotations cannot supply a fake heading.
    positions=[]; offset=0; frontmatter=text.startswith('---\n'); fence=None; comment=False; annotation=False
    for number,line in enumerate(text.splitlines(keepends=True)):
        stripped=line.strip()
        if frontmatter:
            if number and stripped in ('---','...'): frontmatter=False
            offset+=len(line); continue
        if '<!--' in line: comment=True
        if comment:
            if '-->' in line: comment=False
            offset+=len(line); continue
        if '%%' in line:
            if line.count('%%') % 2: annotation=not annotation
            offset+=len(line); continue
        if annotation:
            offset+=len(line); continue
        marker=re.match(r'^ {0,3}(`{3,}|~{3,})',line)
        if marker:
            token=marker.group(1)
            if fence is None: fence=token
            elif token[0]==fence[0] and len(token)>=len(fence): fence=None
            offset+=len(line); continue
        if fence is None and re.match(r'^#{1,6} [^\n]+\n$',line):
            positions.append((line.rstrip('\n'),offset,offset+len(line)))
        offset+=len(line)
    require(not frontmatter,'unterminated-page-frontmatter')
    result={}
    for i,(heading,start,end) in enumerate(positions):
        require(heading not in result,'duplicate-page-heading')
        result[heading]=(end,positions[i+1][1] if i+1<len(positions) else len(text))
    return result


def _page_identity(page, article, identity=None):
    import yaml
    text=absolute(page).read_text()
    match=re.match(r'\A---\n([\s\S]*?)\n(?:---|\.\.\.)\n',text)
    require(match is not None,'paper-page-frontmatter-required')
    try:
        metadata=yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise ValueError('invalid-page-frontmatter') from exc
    require(isinstance(metadata,dict) and metadata.get('kind')=='paper' and metadata.get('slug')==article,'paper-page-article-identity-mismatch')
    if identity and metadata.get('doi') is not None:
        require(metadata['doi']==identity.get('doi'),'paper-page-doi-mismatch')


def _plan_identity(p):
    return {k:v for k,v in p.items() if k!='planned_at'}


def _same_plan(left,right):
    return _plan_identity(left)==_plan_identity(right)


def plan(request,*,manifest=None,work_root,fixture=False,model_profile=None,page_scope=None):
    if isinstance(request,dict): request=Request(**request)
    require(isinstance(request,Request),'request-required')
    work=absolute(work_root); p=ae.profile(model_profile); m=None
    if manifest:
        manifest=absolute(manifest); m=pa.validate_manifest(pa.load(manifest))
        require(m['schema']!=pa.DIAGNOSTIC_SCHEMA, 'diagnostic-requires-diagnostic-plan')
        require(m['article']['slug']==request.article,'unknown-article')
        roster=_resolve_elements(m,request.elements) if request.elements is not None else [e['element_id'] for e in m['elements'] if e['eligible']]
        keys=pa.closure_for(m,roster) if request.elements is not None else {f['key'] for f in m['files']}
        pa.verify_local(manifest,keys)
        # Also detect mutation of any other currently materialized input. A
        # selected restore may omit files, but cannot conceal changed local ones.
        pa.verify_local(manifest,set(pa.local_sources(manifest)))
        pa.verify_source(manifest)
        roots=[manifest.parent]+[absolute(s['root']) for s in pa.local_sources(manifest).values()]
        external(work,roots)
    else: roster=None
    if request.page:
        external(work,[request.page])
        _page_identity(request.page,request.article,m['article'] if m else None)
    scopes=copy.deepcopy(page_scope or [])
    if scopes:
        require(request.page,'page-scope-without-page'); sections=_sections(request.page.read_text())
        for s in scopes:
            require(set(s)=={'heading','elements'} and s['heading'] in sections and s['elements'],'page-scope-fields')
            if roster is not None: require(set(s['elements'])<=set(roster),'page-scope-outside-selection')
        require(len({s['heading'] for s in scopes})==len(scopes),'duplicate-page-scope')
    pending=[] if m else ['source-retrieval','package-construction','full-distillation-and-reconciliation']
    if not m and request.elements is not None: pending.append('selection-validation')
    value=dict(schema=SCHEMA_PLAN,article=request.article,mode='selected' if request.elements is not None else 'full',
        request=dict(article=request.article,elements=request.elements,page=str(request.page) if request.page else None),
        elements=roster,manifest=str(manifest) if manifest else None,manifest_sha256=sha(manifest) if manifest else None,
        article_identity=m['article'] if m else None,page_path=str(request.page) if request.page else None,
        page_sha256=sha(request.page) if request.page else None,page_scope=scopes,fixture=bool(fixture),profile=p,
        pending_operator_steps=[dict(name=x) for x in pending],planned_at=pa.now_utc(),
        cost_exposure=dict(minimum_package_build_required=m is None,selected_elements=len(roster) if roster is not None else None,
            eligible_elements=sum(e['eligible'] for e in m['elements']) if m else None,model_profile=p,
            legacy_full_distillation_required=m is None,model_scope_will_not_be_broadened=True),
        stages=[dict(name=n,available=bool(m) if n in ('acquisition','source-preparation','enrichment') else False) for n in STAGES])
    if work.exists():
        saved=ae.read_bound(work/'plan.json'); require(_same_plan(saved,value),'work-root-already-holds-different-plan')
        return saved
    pa.new_directory(work); ae._seal_file(work/'plan.json',value); (work/'receipts').mkdir()
    if request.page: pa.put(work/'original-page.md',request.page.read_bytes())
    return value


def diagnostic_plan(manifest, elements, *, work_root, fixture=False, model_profile=None):
    manifest,work=absolute(manifest),absolute(work_root)
    m=pa.validate_manifest(pa.load(manifest)); pa.verify_source(manifest)
    ae.source_scope(m,elements,fixture,'selected-diagnostic')
    external(work,[manifest.parent]+[absolute(s['root']) for s in pa.local_sources(manifest).values()])
    value=dict(schema=DIAGNOSTIC_PLAN,scope='selected-diagnostic',article=None,article_identity=None,
        mode='selected-diagnostic',request=dict(article=None,elements=elements,page=None),elements=elements,
        manifest=str(manifest),manifest_sha256=sha(manifest),page_path=None,page_sha256=None,page_scope=[],
        fixture=bool(fixture),profile=ae.profile(model_profile),production_complete=False,page_refresh_complete=False,
        source_status=m['source_status'],planned_at=pa.now_utc())
    if work.exists():
        saved=ae.read_bound(work/'plan.json'); require(_same_plan(saved,value),'work-root-already-holds-different-plan')
        return saved
    pa.new_directory(work); ae._seal_file(work/'plan.json',value); (work/'receipts').mkdir()
    return value


def _history(work):
    previous=sha(work/'plan.json'); result=[]
    for i,path in enumerate(sorted((work/'receipts').glob('*.json')),1):
        row=ae.read_bound(path)
        require(path.name==f'{i:06d}.json' and row['sequence']==i and row['previous_sha256']==previous and
            row['plan_sha256']==sha(work/'plan.json'),'run-history-binding')
        for key,h in row['artifacts'].items(): require(sha(work/pa.relative_key(key))==h,'stage-artifact-changed:'+key)
        result.append(row); previous=sha(path)
    return result


def _record(work,stage,paths,value):
    history=_history(work)
    row=dict(schema='reenrich-stage-receipt-v2',sequence=len(history)+1,stage=stage,
        previous_sha256=sha(work/'receipts'/f'{len(history):06d}.json') if history else sha(work/'plan.json'),
        plan_sha256=sha(work/'plan.json'),artifacts={str(p.relative_to(work)):sha(p) for p in paths},
        result=value,created_at=pa.now_utc())
    ae._seal_file(work/'receipts'/f'{len(history)+1:06d}.json',row)
    return row


def context(work,*,check_page=True):
    work=absolute(work); p=ae.read_bound(work/'plan.json'); require(p['schema'] in (SCHEMA_PLAN,DIAGNOSTIC_PLAN),'plan-schema')
    diagnostic=p['schema']==DIAGNOSTIC_PLAN
    if diagnostic:
        require(p['mode']==p['scope']=='selected-diagnostic' and p['article'] is None and p['article_identity'] is None and
            p['page_path'] is None and p['request']['page'] is None and not p['page_scope'] and p['manifest'] and
            p['production_complete'] is False and p['page_refresh_complete'] is False,'diagnostic-plan-contract')
    history=_history(work)
    manifest=p['manifest']; roster=p['elements']
    if not manifest and (work/'adoption.json').exists():
        a=ae.read_bound(work/'adoption.json'); require(a['plan_sha256']==sha(work/'plan.json'),'adoption-plan-binding')
        manifest=a['manifest']; require(sha(manifest)==a['manifest_sha256'],'adopted-manifest-changed'); roster=a['elements']
    elif manifest: require(sha(manifest)==p['manifest_sha256'],'manifest-changed-since-plan')
    m=None
    if manifest:
        m=pa.validate_manifest(pa.load(manifest))
        if diagnostic:
            ae.source_scope(m,roster,p['fixture'],'selected-diagnostic')
            require(p['source_status']==m['source_status'], 'diagnostic-source-status-binding')
            expected=p['request']['elements']
        else:
            require(m['schema']!=pa.DIAGNOSTIC_SCHEMA, 'diagnostic-production-plan-forbidden')
            require(m['article']['slug']==p['article'],'article-identity-changed')
            if p['article_identity']: require(m['article']==p['article_identity'],'article-version-changed')
            expected=_resolve_elements(m,p['request']['elements']) if p['mode']=='selected' else [e['element_id'] for e in m['elements'] if e['eligible']]
        require(roster==expected,'roster-changed')
        keys=pa.closure_for(m,roster) if p['mode']=='selected' else {f['key'] for f in m['files']}
        pa.verify_local(manifest,keys)
        # Also detect mutation of any other currently materialized input. A
        # selected restore may omit files, but cannot conceal changed local ones.
        pa.verify_local(manifest,set(pa.local_sources(manifest)))
        pa.verify_source(manifest)
    if p['page_path']:
        require(sha(work/'original-page.md')==p['page_sha256'],'original-page-snapshot-changed')
        _page_identity(work/'original-page.md',p['article'],m['article'] if m else None)
        applied=next((h for h in history if h['stage']=='page-apply'),None)
        expected=applied['result']['page_sha256'] if applied else p['page_sha256']
        if check_page: require(sha(p['page_path'])==expected,'page-changed-since-plan')
    binding=digest(dict(plan_sha256=sha(work/'plan.json'),manifest_sha256=sha(manifest) if manifest else None,roster=roster))
    return work,p,manifest,m,roster,binding,history


def adopt(work_root,manifest,*,identity_approval):
    with locked(work_root):
        work,p,_,_,_,_,_=context(work_root)
        require(p['manifest'] is None and not (work/'adoption.json').exists(),'legacy-adoption-only-once')
        path=absolute(manifest); m,_=pa.verify_local(path)  # full legacy prerequisites, not a partial restore
        pa.verify_source(path)
        external(work,[path.parent]+[absolute(s['root']) for s in pa.local_sources(path).values()])
        require(m['article']['slug']==p['article'],'legacy-article-mismatch')
        if p['page_path']: _page_identity(work/'original-page.md',p['article'],m['article'])
        approval=pa.load(identity_approval)
        require(set(approval)=={'plan_sha256','manifest_sha256','article','requested_elements','approved_by','identity_and_scope_reviewed'},'adoption-approval-fields')
        require(approval['plan_sha256']==sha(work/'plan.json') and approval['manifest_sha256']==sha(path) and
            approval['article']==m['article'] and approval['requested_elements']==p['request']['elements'] and
            approval['identity_and_scope_reviewed'] is True and approval['approved_by'],'legacy-identity-and-scope-approval-required')
        roster=_resolve_elements(m,p['request']['elements']) if p['mode']=='selected' else [e['element_id'] for e in m['elements'] if e['eligible']]
        ae._seal_file(work/'adoption.json',dict(plan_sha256=sha(work/'plan.json'),manifest=str(path),manifest_sha256=sha(path),
            elements=roster,identity_approval=approval,full_distillation_required=True))
        _record(work,'legacy-adoption',[work/'adoption.json'],dict(elements=roster,source_status=m['source_status']))
        return execute(p,work_root=work)


def execute(plan_value=None,*,work_root):
    """Validate all current bindings and report the next explicit continuation."""
    work,p,manifest,m,roster,binding,history=context(work_root)
    if plan_value is not None: require(plan_value==p,'different-plan-in-work-root')
    receipts={n:dict(status='pending-operator') for n in STAGES}
    if m:
        receipts['acquisition']=dict(status='verified' if m['source_status']['acquisition_verified'] else 'hold',
            scope='selected-source-closure' if p['mode']=='selected' else 'full-source-inventory',holds=m['source_status']['holds'])
        locally_complete=set(pa.local_sources(manifest))=={f['key'] for f in m['files']}
        receipts['source-preparation']=dict(status='verified' if m['source_status']['extraction_verified'] else 'hold',
            complete=m['source_status']['complete'] and locally_complete,
            archive_source_complete=m['source_status']['complete'],
            verified_scope='full-materialization' if locally_complete else 'selected-dependency-closure',
            fixture=m['source_status']['fixture'])
    next_step='adopt'
    enrichment=work/'enrichment'
    if m: next_step='prepare'
    if (enrichment/'prepared.json').exists():
        prepared=ae.verify(work,binding,manifest,for_execution=False)
        require(prepared['roster']==roster and prepared['fixture'] is p['fixture'] and prepared['profile']==p['profile'],'prepared-request-contract-changed')
        receipts['enrichment']=dict(status='prepared-not-executed',roster=roster,mode=p['mode'],accounting=dict(
            requests={r['id']:dict(element_id=r['element_id'],status='pending') for r in prepared['requests']},
            counts=dict(pending=len(roster),uncertain=0,failed=0,completed=0),complete=False,integrity_hold=False)); next_step='count'
    if (enrichment/'counts.json').exists():
        ae.verify_counts(enrichment,prepared); next_step='seal'
    if (enrichment/'seal.json').exists(): next_step='approved-execute'
    if (enrichment/'execution-start.json').exists():
        accounting=ae.execution_state(work,binding,manifest)['accounting']
        receipts['enrichment']=dict(status='executed' if accounting['complete'] else 'partial',roster=roster,
            mode=p['mode'],fixture=p['fixture'],accounting=accounting)
        next_step=('approved-execute' if accounting['counts']['pending'] and not accounting['integrity_hold'] else
                   'review-create' if accounting['counts']['completed'] or accounting['complete'] else 'new-selected-run')
    if (work/'review'/'dossier.json').exists():
        ae.review_verify(work,binding,manifest); next_step='review-import'
    if (work/'export'/'handoff.json').exists():
        exported=ae.verify_export(work,binding,manifest)
        receipts['review-export']=dict(status='verified' if exported['execution_complete'] else 'partial',fixture=p['fixture'])
        next_step=('candidate-import' if p['page_path'] else 'publish') if exported['execution_complete'] else 'new-selected-run'
        if not p['page_path']: receipts['page-reconciliation']=dict(status='not-requested',applied=False)
    if (work/'page-candidate'/'candidate.json').exists():
        _candidate_verify(work,p,binding,manifest)
        receipts['page-reconciliation']=dict(status='staged-operator-prose',applied=False); next_step='apply'
    stages={h['stage'] for h in history}
    if 'page-apply' in stages:
        receipts['page-reconciliation']=dict(status='applied',applied=True); next_step='publish'
    if 'publish' in stages:
        publication=next(h['result'] for h in history if h['stage']=='publish')
        verify_completion(work/'completion.json',work/'archive'/'manifest.json',
            manifest_key=publication['manifest_key'],manifest_sha256=publication['manifest_sha256'],
            article_key=m['article_key'],page=p['page_path'])
        receipts['archive-publication']=dict(status='verified-at-publication',publication=publication)
    if p['schema']==DIAGNOSTIC_PLAN:
        exported=(work/'export'/'handoff.json').exists()
        diagnostic_ready=exported and receipts['review-export']['status']=='verified'
        receipts['acquisition']=dict(status='not-established',holds=m['source_status']['holds'])
        receipts['page-reconciliation']=dict(status='diagnostic-forbidden',applied=False)
        receipts['archive-publication']=dict(status='diagnostic-forbidden')
        return dict(schema='reenrich-diagnostic-run-v1',scope='selected-diagnostic',article=None,mode=p['mode'],
            elements=roster,stage_receipts=receipts,source_status=m['source_status'],
            status='diagnostic-export-ready' if diagnostic_ready else 'partial-diagnostic-export' if exported else 'pending-operator-continuation',
            completion='diagnostic-export-ready' if diagnostic_ready else 'pending',
            production_complete=False,page_refresh_complete=False,fixture=p['fixture'],next_step=None if diagnostic_ready else next_step)
    complete=all(x['status'] in ('verified','executed','applied','not-requested','verified-at-publication') for x in receipts.values())
    completion=completion_label(p) if complete else 'pending'
    return dict(schema='reenrich-run-v2',article=p['article'],mode=p['mode'],elements=roster,stage_receipts=receipts,
        status='finished' if complete else 'pending-operator-continuation',completion=completion,
        production_complete=complete and not p['fixture'],page_refresh_complete=complete and bool(p['page_path']),
        fixture=p['fixture'],next_step=None if complete else next_step)


def advance(work_root,operation,*,cache=None,count_receipt=None,approval=None,authorize=False,fixture_transport=None,submission=None):
    with locked(work_root):
        work,p,manifest,m,roster,binding,_=context(work_root)
        require(manifest,'legacy-prerequisites-not-adopted')
        if operation=='prepare':
            value=ae.prepare(work,binding,manifest,roster,p['fixture'],p['profile'],scope=p.get('scope','production')); path=work/'enrichment'/'prepared.json'
        elif operation=='count':
            value=ae.count(work,binding,manifest,cache,count_receipt); path=work/'enrichment'/'counts.json'
        elif operation=='seal':
            value=ae.seal(work,binding,manifest); path=work/'enrichment'/'seal.json'
        elif operation=='approved-execute':
            before=tree(work/'enrichment')
            value=ae.execute(work,binding,manifest,approval,authorize=authorize,fixture_transport=fixture_transport)
            after=tree(work/'enrichment')
            if after!=before:
                _record(work,operation,[work/'enrichment'/key for key in after if key not in before],value['accounting'])
            return value
        elif operation=='review-create':
            value=ae.review_create(work,binding,manifest); path=work/'review'/'dossier.json'
        elif operation=='review-import':
            value=ae.review_import(work,binding,manifest,submission)
            path=work/'review'/'decisions'/f'{value["sequence"]:06d}.json'
        elif operation=='export':
            value=ae.export(work,binding,manifest); path=work/'export'/'handoff.json'
        else: raise ValueError('unknown-continuation')
        _record(work,operation,[path],dict(artifact=str(path.relative_to(work))))
        return value


def _protected(text):
    return re.findall(r'<!--[\s\S]*?-->|%%[\s\S]*?%%|\[\[[^\]]+\]\]|\[[^\]\n]*\]\([^\)\n]+\)|^>[^\n]*(?:\n|$)|^(?:Source(?:s| PDF| package)?|Article package):[^\n]*(?:\n|$)',text,re.M)


REGISTER_START='<!-- portable-article-register:start -->\n'
REGISTER_END='<!-- portable-article-register:end -->\n'


def without_register(text):
    require(text.count(REGISTER_START)==text.count(REGISTER_END)<=1,'malformed-qualification-register')
    if REGISTER_START not in text: return text
    start=text.index(REGISTER_START); end=text.index(REGISTER_END)+len(REGISTER_END)
    require(start<end,'malformed-qualification-register')
    return text[:start]+text[end:]


def page_receipt_name(page,binding):
    # Historical page paths supply a basename only; never dereference old roots.
    return pa.relative_key(Path(page).name+'.article-'+binding[:20]+'.json')


def page_receipt_path(page,binding):
    page=absolute(page)
    return page.parent/page_receipt_name(page,binding)


def qualification_register(exported,submission,m,p,annotated_sha256,*,version=2,archive_paths=None,previous=None):
    from qualified_enrichment.exports import exact_view
    views={v['element_id']:v for v in exported['elements']}; targets=[]
    for row in submission['replacements']:
        for ref in row['evidence']:
            value=exact_view(views[ref['element_id']],ref['target'],purpose='exact',qualification=ref['qualification'])
            targets.append({k:v for k,v in value.items() if k!='content'})
    prefix='refresh-'+exported['binding'][:20]+'/'
    register=dict(schema='portable-page-qualification-register-v1',binding=exported['binding'],article=m['article'],
        article_key=m['article_key'],publication_receipt=page_receipt_name(p['page_path'],exported['binding']),
        locator_contract='Resolve archive keys through the publication receipt manifest key/hash; receipt absent means publication pending.',
        source_locators=[dict(document=d['identity'],key=d['raw_key'],sha256=d['source_sha256']) for d in m['documents']],
        export_locator=dict(key=prefix+'export/handoff.json',sha256=submission['export_sha256']),
        annotated_export_locator=dict(key=prefix+'export/annotated.html',sha256=annotated_sha256),
        reviewer=submission['reviewer'],full_distillation_reviewed=submission['full_distillation_reviewed'],
        reconciliation_outcome=submission.get('reconciliation_outcome','scientific-text-revised'),
        operator_qualification=submission['qualification'],selected_targets=targets,
        source_status=exported['source_status'],
        notice='Native/model originals are unchanged. Findings and attributed correction proposals are annotations, not applied factual corrections. Prior unresolved findings remain active; review covers only recorded scopes/aspects.')

    if version==1:
        return dict(register,current_qualifications=pa.qualification_projection(exported),
            inherited_qualifications=[r for r in exported['inherited_history'] if r.get('qualifications')],
            dispositions=exported['dispositions'])
    require(version==2 and archive_paths is not None,'register-archive-required')
    # The export retains full history. The paper needs the selected scopes only.
    register['schema']='portable-page-qualification-register-v2'
    register['selected_targets']=[{k:t[k] for k in ('element_id','source_sha256','target','qualification',
        'unreviewed_aspects','scope_review_status','unapplied_correction_findings')} for t in targets]
    for t in register['selected_targets']:
        t.update(reviewer=submission['reviewer'],evidence=dict(key=prefix+'page-candidate/input.json'))
    index={e['element_id']:e for e in m['elements']}
    qualifications=[]; seen=set()
    def add(value,locator):
        identity=digest(value)
        if identity not in seen:
            seen.add(identity); qualifications.append(dict(value,evidence=locator))
    def finding(f,scope,locator):
        value=dict(scope,**{k:f[k] for k in ('target','status','category','reason','provenance') if k in f})
        if f.get('resolutions'):
            value['resolutions']=f['resolutions']
            value['correction']='Attributed proposals only; originals remain unchanged.'
        add(value,locator)
    from qualified_enrichment.exports import affected
    from qualified_enrichment.records import related
    for target in targets:
        element=index[target['element_id']]
        scope={k:element[k] for k in ('document','source_sha256','element_id')}
        for f in target['findings']: finding(f,scope,register['export_locator'])
        keys=set(m['common_dependencies'])|set(element['inherited'])
        for entry in pa.prompt_history(archive_paths,keys,element):
            locator={k:entry[k] for k in ('key','sha256')}
            for q in entry['qualifications']:
                if 'findings' in q:
                    for f in affected(q,target['target']): finding(f,scope,locator)
                    continue
                # Untyped coverage may contain gaps or unresolved warnings.
                metadata=q['metadata']
                if isinstance(metadata,dict) and (metadata.get('target')=='/record' or str(metadata.get('target','')).startswith('/record/')):
                    if not related(metadata['target'],target['target']): continue
                add(dict(scope=q.get('scope','unscoped'),metadata_target=q.get('target',''),metadata=metadata,
                    attribution=q.get('attribution')),locator)
    register['qualifications']=qualifications
    if previous is not None:
        _register_archive(previous,archive_paths)
        if previous['schema'].endswith('-v1'):
            old_prefix='refresh-'+previous['binding'][:20]+'/'
            previous=qualification_register(pa.load(archive_paths[previous['export_locator']['key']]),
                pa.load(archive_paths[old_prefix+'page-candidate/input.json']),
                pa.load(archive_paths[old_prefix+'parent-manifest.json']),pa.load(archive_paths[old_prefix+'plan.json']),
                previous['annotated_export_locator']['sha256'],archive_paths=archive_paths)
        # Previously cited scopes still qualify unchanged prose elsewhere on the
        # page. A new selective refresh cannot silently retire those warnings.
        identity=lambda t: (t['element_id'],t['source_sha256'],t['target'],t['qualification'],digest(t['reviewer']))
        current={identity(t) for t in register['selected_targets']}
        register['selected_targets'] += [t for t in previous['selected_targets'] if identity(t) not in current]
        if (previous['operator_qualification'],previous['reviewer']) != (register['operator_qualification'],register['reviewer']):
            key='refresh-'+previous['binding'][:20]+'/page-candidate/input.json'
            add(dict(scope='Prior page review',metadata_target='/qualification',metadata=previous['operator_qualification'],
                attribution=previous['reviewer']),dict(key=key,sha256=sha(archive_paths[key])))
        for q in previous['qualifications']:
            add({k:v for k,v in q.items() if k!='evidence'},q['evidence'])
        sources={digest(d) for d in register['source_locators']}
        register['source_locators'] += [d for d in previous['source_locators'] if digest(d) not in sources]
    return register


def read_register(text):
    import html
    without_register(text)  # validate delimiters even when there is no register
    if REGISTER_START not in text: return None
    block=text.split(REGISTER_START,1)[1].split(REGISTER_END,1)[0]
    match=re.search(r'<!-- portable-page-qualification-register-v2: ([^\n]*) -->\n$',block) or re.search(r'<pre>([\s\S]*)</pre>\n$',block)
    require(match is not None,'malformed-qualification-register')
    value=json.loads(html.unescape(match[1]))
    require(value.get('schema') in ('portable-page-qualification-register-v1','portable-page-qualification-register-v2'),
        'unknown-qualification-register')
    require(REGISTER_START+block+REGISTER_END==register_text(value),'noncanonical-qualification-register')
    return value


def _register_archive(register,paths):
    require(paths is not None,'register-archive-required')
    # A verified archived snapshot proves the entire removed register survives,
    # including unknown/human-added qualifications. Never silently discard them.
    prefix='refresh-'+register['binding'][:20]+'/'
    snapshot=paths.get(prefix+'applied-page.md')
    require(snapshot is not None and read_register(snapshot.read_text())==register,'register-archive-snapshot')
    locators=[register['export_locator'],register['annotated_export_locator']]+register['source_locators']
    locators += [q['evidence'] for q in register.get('qualifications',[])+register['selected_targets'] if q.get('evidence')]
    exported=pa.load(paths[register['export_locator']['key']]) if register['export_locator']['key'] in paths else None
    require(exported is not None,'register-archive-evidence')
    for key,h in exported['review_bindings'].items():
        locators.append(dict(key=prefix+'review/'+pa.relative_key(key),sha256=h))
    for locator in locators:
        path=paths.get(locator['key'])
        require(path is not None and ('sha256' not in locator or sha(path)==locator['sha256']),'register-archive-evidence')
    for ref in exported['inherited_history']:
        path=paths.get(ref['key'])
        require(path is not None and sha(path)==ref['sha256'],'register-archive-history')


def register_text(register):
    import html
    header=(REGISTER_START+'Article package: '+register['publication_receipt']+'\n'+
        'Annotated export: '+register['annotated_export_locator']['key']+' (resolve through article package receipt)\n')
    if register['schema'].endswith('-v1'):
        return header+'<pre>'+html.escape(json.dumps(register,ensure_ascii=False,sort_keys=True,indent=2))+'</pre>\n'+REGISTER_END
    def text(value):
        return html.escape(value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,sort_keys=True)).replace('\n','&#10;').replace('\r','&#13;')
    parts=[header,'<p><strong>Source qualifications</strong> — '+text(register['operator_qualification'])+' Attribution: '+text(register['reviewer'])+'.</p>\n']
    if not register['source_status'].get('complete') or register['source_status'].get('holds') or register['source_status'].get('fixture'):
        parts.append('<p>Source status: '+text(register['source_status'])+'</p>\n')
    for target in register['selected_targets']:
        parts.append('<p><code>'+text(target['element_id']+' '+target['target'])+'</code>: '+
            text(target['qualification'])+' Unreviewed aspects: '+text(', '.join(target['unreviewed_aspects']) or 'none for this exact scope')+
            '. Attribution: '+text(target['reviewer'])+' Evidence: <code>'+text(target['evidence']['key'])+'</code>.</p>\n')
    for q in register['qualifications']:
        scope=q.get('scope',{k:q[k] for k in ('document','element_id','source_sha256','target') if k in q})
        parts.append('<p>'+text(scope)+(' '+text(q['metadata_target']) if q.get('metadata_target') else '')+
            ' — '+text(q.get('status','Historical qualification'))+': '+
            text(q.get('reason',q.get('metadata')))+
            (' Attributed proposals only; original unchanged: '+text(q['resolutions']) if q.get('resolutions') else '')+
            ' Attribution: '+text(q.get('provenance',q.get('attribution')))+
            ' Evidence: <code>'+text(q['evidence']['key'])+'</code>.</p>\n')
    parts.append('<p>'+text(register['notice'])+'</p>\n')
    # Compact machine binding, not a second visible review-history dump.
    parts.append('<!-- portable-page-qualification-register-v2: '+html.escape(json.dumps(register,
        ensure_ascii=False,sort_keys=True,separators=(',',':')))+' -->\n'+REGISTER_END)
    return ''.join(parts)


def install_register(text,register,*,archive_paths=None):
    old=read_register(text)
    if old is not None and old!=register: _register_archive(old,archive_paths)
    text=without_register(text)
    match=re.match(r'\A---\n[\s\S]*?\n(?:---|\.\.\.)\n',text)
    require(match is not None,'paper-page-frontmatter-required')
    return text[:match.end()]+register_text(register)+text[match.end():]


def _candidate_text(work,p,manifest,binding,submission,*,version=2):
    fields={'schema','binding','export_sha256','reviewer','qualification','full_distillation_reviewed','replacements'}
    require(set(submission) in (fields,fields|{'reconciliation_outcome'}),'candidate-fields')
    unchanged=submission.get('reconciliation_outcome')=='reviewed-no-scientific-text-change'
    require(submission.get('reconciliation_outcome','scientific-text-revised') in
        ('scientific-text-revised','reviewed-no-scientific-text-change'),'candidate-reconciliation-outcome')
    require(submission['schema']=='reenrich-page-candidate-v2' and submission['binding']==binding and
        submission['export_sha256']==sha(work/'export'/'handoff.json'),'candidate-binding')
    from qualified_enrichment import reviews
    from qualified_enrichment.exports import exact_view
    reviews.provenance(submission['reviewer'])
    require(isinstance(submission['qualification'],str) and submission['qualification'].strip(),'candidate-qualification-required')
    exported=ae.verify_export(work,binding,manifest); views={e['element_id']:e for e in exported['elements']}
    require(exported['execution_complete'],'partial-export-cannot-complete-page-refresh')
    if p['manifest'] is None or p['mode']=='full': require(submission['full_distillation_reviewed'] is True,'full-distillation-attestation-required')
    original=(work/'original-page.md').read_text(); sections=_sections(original)
    changes=[]; seen=set(); covered=set()
    scope={s['heading']:set(s['elements']) for s in p['page_scope']}
    require(isinstance(submission['replacements'],list) and submission['replacements'],'operator-scientific-replacements-required')
    for r in submission['replacements']:
        require(set(r)=={'heading','old_sha256','new_text','elements','evidence'},'replacement-fields')
        heading=r['heading']; require(heading in sections and heading not in seen,'replacement-heading'); seen.add(heading)
        start,end=sections[heading]; before=original[start:end]
        require(hashlib_sha(before)==r['old_sha256'] and isinstance(r['new_text'],str),'replacement-old-binding')
        after=r['new_text']; ids=set(r['elements'])
        require(ids<=set(exported['roster']) and (ids or not exported['roster']),'replacement-elements-outside-export')
        if p['mode']=='selected': require(heading in scope and ids<=scope[heading] and ids,'selective-page-scope-not-approved')
        require(not re.search(r'^#{1,6} ',after,re.M),'replacement-cannot-insert-section')
        require(_protected(before)==_protected(after),'human-annotations-or-graph-links-changed')
        strip=lambda s: re.sub(r'<!--[\s\S]*?-->|%%[\s\S]*?%%','',s).strip()
        require(bool(strip(after)) and (before==after if unchanged else strip(before)!=strip(after)),
            'comments-only-or-unchanged-candidate')
        require(isinstance(r['evidence'],list) and (r['evidence'] or not ids),'replacement-evidence-required')
        evidence_ids=set()
        for ref in r['evidence']:
            require(set(ref)=={'element_id','source_sha256','target','qualification'},'candidate-evidence-fields')
            require(ref['element_id'] in ids and ref['source_sha256']==views[ref['element_id']]['source_sha256'],'candidate-evidence-source-binding')
            exact_view(views[ref['element_id']],ref['target'],purpose='exact',qualification=ref['qualification'])
            require(ref['qualification'] and (unchanged or ref['qualification'] in after),'qualification-must-appear-in-prose')
            evidence_ids.add(ref['element_id'])
        require(evidence_ids==ids,'candidate-evidence-roster'); covered.update(ids)
        changes.append((start,end,after))
    require(covered==set(exported['roster']),'candidate-must-reconcile-requested-roster')
    text=original
    for start,end,after in sorted(changes,reverse=True): text=text[:start]+after+text[end:]
    m,paths=pa.verify_local(manifest,set(pa.local_sources(manifest)))
    register=qualification_register(exported,submission,m,p,sha(work/'export'/'annotated.html'),version=version,archive_paths=paths,previous=read_register(original))
    # Historical candidate read-back uses its original rendering contract.
    if version==1: text=without_register(text)
    return install_register(text,register,archive_paths=paths)


def hashlib_sha(text):
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()


def candidate_import(work_root,submission):
    with locked(work_root):
        work,p,manifest,_,_,binding,_=context(work_root)
        require(p['schema']!=DIAGNOSTIC_PLAN,'diagnostic-page-application-forbidden')
        require(p['page_path'],'page-not-planned')
        value=pa.load(submission); text=_candidate_text(work,p,manifest,binding,value)
        root=pa.new_directory(work/'page-candidate')
        pa.put(root/'page-candidate.md',text.encode()); pa.put(root/'input.json',absolute(submission).read_bytes())
        diff=''.join(difflib.unified_diff((work/'original-page.md').read_text().splitlines(True),text.splitlines(True),fromfile='original',tofile='candidate'))
        pa.put(root/'page-candidate.diff',diff.encode())
        ae._seal_file(root/'candidate.json',dict(binding=binding,original_sha256=p['page_sha256'],
            candidate_sha256=sha(root/'page-candidate.md'),input_sha256=sha(root/'input.json'),diff_sha256=sha(root/'page-candidate.diff')))
        _record(work,'candidate-import',[root/'candidate.json'],dict(candidate_sha256=sha(root/'page-candidate.md')))
        return pa.load(root/'candidate.json')


def _candidate_verify(work,p,binding,manifest):
    root=work/'page-candidate'; value=ae.read_bound(root/'candidate.json')
    require(value['binding']==binding and value['original_sha256']==p['page_sha256'] and
        value['input_sha256']==sha(root/'input.json') and value['candidate_sha256']==sha(root/'page-candidate.md') and
        value['diff_sha256']==sha(root/'page-candidate.diff'),'candidate-changed')
    saved=(root/'page-candidate.md').read_text()
    version=1 if read_register(saved)['schema'].endswith('-v1') else 2
    require(saved==_candidate_text(work,p,manifest,binding,pa.load(root/'input.json'),version=version),'candidate-regeneration-mismatch')
    return value


def apply(work_root,*,authorize=False):
    require(authorize is True,'explicit-page-apply-authorization-required')
    with locked(work_root):
        work,p,manifest,_,_,binding,history=context(work_root)
        require(p['schema']!=DIAGNOSTIC_PLAN,'diagnostic-page-application-forbidden')
        require(not any(r['stage']=='page-apply' for r in history),'page-already-applied')
        c=_candidate_verify(work,p,binding,manifest); page=absolute(p['page_path'])
        require(not (work/'apply-start.json').exists(),'interrupted-apply-requires-operator-recovery')
        pa.save(work/'apply-start.json',dict(binding=binding,page=str(page),original_sha256=p['page_sha256'],candidate_sha256=c['candidate_sha256']))
        # Advisory page lock plus final hash check. Cooperative writers are
        # excluded; noncooperating editors must be paused during this short apply.
        import fcntl
        with page.open('r+b') as stream:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            require(sha(page)==p['page_sha256'],'page-changed-since-plan')
            raw=(work/'page-candidate'/'page-candidate.md').read_bytes()
            stream.seek(0); stream.write(raw); stream.truncate(); stream.flush(); os.fsync(stream.fileno())
        require(sha(page)==c['candidate_sha256'],'page-apply-readback-mismatch')
        pa.put(work/'applied-page.md',page.read_bytes())
        receipt=_record(work,'page-apply',[work/'applied-page.md',work/'apply-start.json'],dict(page_sha256=sha(page)))
        return receipt['result']


def completion_label(p):
    require(p['schema']!=DIAGNOSTIC_PLAN,'diagnostic-has-no-article-completion-label')
    return ('offline-' if p['fixture'] else '')+p['mode']+('-refresh-complete' if p['page_path'] else '-archive-complete')


def verify_completion(receipt_path,manifest_path,*,manifest_key,manifest_sha256,article_key,page=None):
    """Portable verification, not source_package v2 ingest verification.

    Trust comes from caller-pinned manifest key/hash and article identity, not
    from a receipt's own claims. This works after the original run is removed.
    Publication read-back is historical; it is not a fresh remote health check.
    """
    pa._hash(manifest_sha256); pa._hash(article_key); pa.relative_key(manifest_key)
    require(sha(manifest_path)==manifest_sha256,'completion-manifest-hash')
    m,paths=pa.verify_local(manifest_path); pa.verify_source(manifest_path)
    require(m['schema']!=pa.DIAGNOSTIC_SCHEMA,'diagnostic-article-completion-forbidden')
    receipt=pa.load(receipt_path); pub=receipt['publication']
    require(receipt['schema']=='portable-article-completion-v1' and
        receipt['article']==m['article'] and m['article_key']==article_key==pub['article_key'],'completion-article-binding')
    require(pub['manifest_key']==manifest_key and pub['manifest_sha256']==manifest_sha256 and
        manifest_key==pa.revision_prefix(m,pub['prefix'])+'/manifests/'+manifest_sha256+'.json','completion-publication-pointer')
    pa.RcloneTransport(pub['remote'],pub['bucket'])  # validate only; never follows receipt-selected transport
    expected={(pa.object_key(m,pub['prefix'],f),f['sha256'],f['size']) for f in m['files']}
    expected.add((manifest_key,manifest_sha256,absolute(manifest_path).stat().st_size))
    require(expected=={(r['key'],r['sha256'],r['size']) for r in pub['receipts']} and
        all(r['method']=='read_back_sha256' for r in pub['receipts']),'publication-readback-inventory')
    refresh=m['provenance']['refresh']; binding=refresh['binding']; prefix='refresh-'+binding[:20]+'/'
    require(receipt['binding']==binding,'completion-run-binding')
    p=pa.load(paths[prefix+'plan.json']); exported=pa.load(paths[prefix+'export/handoff.json'])
    parent_path=paths[prefix+'parent-manifest.json']; parent=pa.validate_manifest(pa.load(parent_path))
    require(sha(parent_path)==m['provenance']['parent_manifest_sha256'] and parent['article']==m['article'], 'completion-parent-binding')
    require(exported['schema']=='portable-qualified-export-v3' and exported['binding']==binding and
        exported['roster']==refresh['roster'] and exported['fixture']==p['fixture']==refresh['fixture'] and
        refresh['mode']==p['mode'],'completion-export-contract')
    require(exported.get('execution_complete',True) is True,'partial-export-cannot-verify-completion')
    require(receipt['completion']==completion_label(p) and receipt['page_refresh_complete']==bool(p['page_path']) and
        receipt['production_complete']==(not p['fixture']),'completion-status-binding')
    require(pub['verification_scope']=='rclone-live-readback' or p['fixture'],'offline-publication-not-production')
    for f in parent['files']:
        require(f['key'] in paths and sha(paths[f['key']])==f['sha256'],'completion-parent-object-binding')
    ids=exported['roster']; keys=pa.closure_for(parent,ids) if ids else set(parent['common_dependencies'])
    inherited=set(parent['common_dependencies']).union(*(set(e['inherited']) for e in parent['elements'] if e['element_id'] in ids))
    require(exported['inherited_history']==pa.history_refs(paths,keys & inherited) and
        exported['source_status']==parent['source_status'] and exported['dispositions']==parent['dispositions'],
        'completion-inherited-qualifications')
    from article_runtime import trusted_modules
    trusted_modules()
    from qualified_enrichment import reviews
    from qualified_enrichment.exports import exact_view,content_targets
    dossier=pa.load(paths[prefix+'review/dossier.json'])
    decision_keys=sorted(k for k in paths if k.startswith(prefix+'review/decisions/') and k.endswith('.json'))
    entries=[pa.load(paths[k]) for k in decision_keys]
    views=reviews.apply(dossier,entries)
    require(entries or not views,'completion-review-required')
    for view in views: view['consumer_views']=[exact_view(view,t) for t in content_targets(view['outcome'])]
    require(exported['elements']==views and [v['element_id'] for v in views]==ids,'completion-export-findings')
    for key,h in exported['review_bindings'].items():
        require(sha(paths[prefix+'review/'+pa.relative_key(key)])==h,'completion-review-binding')
    import html
    annotated='<!doctype html><html lang="en"><meta charset="utf-8"><title>Qualified article evidence</title><pre>'+html.escape(json.dumps(exported,indent=2))+'</pre></html>'
    require(paths[prefix+'export/annotated.html'].read_text()==annotated,'completion-annotated-export')
    require(receipt['export']==dict(key=prefix+'export/handoff.json',sha256=sha(paths[prefix+'export/handoff.json'])) and
        receipt['annotated_export']==dict(key=prefix+'export/annotated.html',sha256=sha(paths[prefix+'export/annotated.html'])), 'completion-export-pointer')
    if p['page_path']:
        require(page is not None,'completion-real-page-required')
        page=absolute(page); _page_identity(page,p['article'],m['article'])
        submission=pa.load(paths[prefix+'page-candidate/input.json'])
        require(submission['export_sha256']==receipt['export']['sha256'] and submission['binding']==binding,'completion-candidate-binding')
        reviews.provenance(submission['reviewer'])
        if p['mode']=='full' or p['manifest'] is None:
            require(submission['full_distillation_reviewed'] is True,'full-distillation-attestation-required')
        text=page.read_text()
        stored=read_register(text)
        require(stored is not None,'completion-qualification-register-or-pointer')
        version=1 if stored['schema'].endswith('-v1') else 2
        register=qualification_register(exported,submission,parent,p,receipt['annotated_export']['sha256'],version=version,archive_paths=paths,
            previous=read_register(paths[prefix+'original-page.md'].read_text()))
        require(register_text(register) in text and text.count(REGISTER_START)==1,'completion-qualification-register-or-pointer')
        require(sha(page)==sha(paths[prefix+'applied-page.md'])==receipt['page_sha256'],'completion-page-snapshot')
        sidecar=page.parent/register['publication_receipt']
        require(pa.load(sidecar)==receipt,'completion-page-receipt-pointer')
    else:
        require(page is None and receipt['page_sha256'] is None,'archive-only-not-page-refresh')
    return receipt


def publish(work_root,remote,bucket,prefix,*,runner=None):
    with locked(work_root):
        work,p,manifest,m,roster,binding,history=context(work_root)
        require(p['schema']!=DIAGNOSTIC_PLAN,'diagnostic-publication-forbidden')
        require(not p['page_path'] or any(r['stage']=='page-apply' for r in history),'page-apply-required-before-publication')
        exported=ae.verify_export(work,binding,manifest)
        require(exported['execution_complete'],'partial-export-cannot-publish-completion')
        require(not any(r['stage']=='publish' for r in history),'already-published')
        require(runner is None or p['fixture'], 'offline-publication-double-requires-fixture-run')
        if p['page_path']:
            _candidate_verify(work,p,binding,manifest)
            require(not page_receipt_path(p['page_path'],binding).exists(),'publication-receipt-already-exists')
        # Archive-only is explicit in the immutable plan (page=None). A planned
        # page refresh cannot be silently downgraded to bypass application.
        pa.verify_local(manifest)
        archive=work/'archive'
        if not archive.exists():
            updated=copy.deepcopy(m); sources=copy.deepcopy(pa.local_sources(manifest))
            updated['schema']=pa.SCHEMA
            updated['package_id']='refresh-'+binding[:20]
            updated['provenance']['parent_manifest_sha256']=sha(manifest)
            updated['provenance']['refresh']=dict(binding=binding,mode=p['mode'],roster=roster,fixture=p['fixture'])
            prefix_local='refresh-'+binding[:20]+'/'
            added=[]
            for name,role in (('enrichment','enrichment-job'),('review','enrichment-review'),('export','enrichment-export'),('page-candidate','handoff')):
                if name=='page-candidate' and not p['page_path']: continue
                pa._collect_tree(added,sources,role,work/name,prefix_local+name+'/', 'Refresh evidence, immutable prior revisions retained')
            pa.put(work/'parent-manifest.json',absolute(manifest).read_bytes())
            names=['plan.json','plan.json.sha256','parent-manifest.json']
            if p['page_path']: names+=['applied-page.md','original-page.md']
            for name in names:
                key=prefix_local+name; added.append(pa.file_record('page' if name.endswith('.md') else 'handoff',key,work/name))
                sources[key]=dict(root=str(work),path=name)
            updated['files']+=added; updated['total_objects']=len(updated['files'])
            history_keys=[f['key'] for f in added if f['role'].startswith('enrichment-')]
            updated['common_dependencies']=sorted(set(updated['common_dependencies']+history_keys))
            for e in updated['elements']:
                if e['element_id'] in roster:
                    e['inherited']=sorted(set(e['inherited']+history_keys)); e['dependencies']=sorted(set(e['dependencies']+history_keys))
            pa.validate_manifest(updated); pa.new_directory(archive); pa.save(archive/'manifest.json',updated)
            pa.save(archive/'local-map.json',dict(schema='portable-article-local-map-v2',manifest_sha256=sha(archive/'manifest.json'),sources=sources))
            _record(work,'archive-build',[archive/'manifest.json',archive/'local-map.json'],dict(binding=binding))
        else:
            require(any(r['stage']=='archive-build' and r['result']['binding']==binding for r in history),
                    'interrupted-archive-build-no-receipt')
        result=pa.publish(archive/'manifest.json',remote,bucket,prefix,runner=runner)
        context(work_root)  # detect page/input edits during the upload before writing a receipt
        ae._seal_file(work/'publication.json',result)
        prefix_local='refresh-'+binding[:20]+'/'
        completion=dict(schema='portable-article-completion-v1',binding=binding,article=m['article'],publication=result,
            completion=completion_label(p),production_complete=not p['fixture'],page_refresh_complete=bool(p['page_path']),
            page_sha256=sha(p['page_path']) if p['page_path'] else None,
            export=dict(key=prefix_local+'export/handoff.json',sha256=sha(work/'export/handoff.json')),
            annotated_export=dict(key=prefix_local+'export/annotated.html',sha256=sha(work/'export/annotated.html')))
        # The page's stable sibling receipt is deliberately NOT an archive input:
        # page snapshot -> receipt name; receipt -> immutable manifest hash.
        # No hash cycle and no post-publication page rewrite. Never overwrite.
        if p['page_path']: pa.save(page_receipt_path(p['page_path'],binding),completion)
        pa.save(work/'completion.json',completion)
        verify_completion(work/'completion.json',archive/'manifest.json',manifest_key=result['manifest_key'],
            manifest_sha256=result['manifest_sha256'],article_key=m['article_key'],page=p['page_path'])
        _record(work,'publish',[work/'publication.json',work/'completion.json',archive/'manifest.json',archive/'local-map.json'],result)
        return execute(p,work_root=work)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__); sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('plan'); p.add_argument('--article',required=True); p.add_argument('--element',action='append')
    for name in ('page','manifest','profile','page-scope'): p.add_argument('--'+name)
    p.add_argument('--fixture',action='store_true'); p.add_argument('--work-root',required=True)
    d=sub.add_parser('diagnostic-plan')
    for name in ('manifest','work-root'): d.add_argument('--'+name,required=True)
    d.add_argument('--element',action='append',required=True); d.add_argument('--profile'); d.add_argument('--fixture',action='store_true')
    for name in ('execute','prepare','count','seal','approved-execute','review-create','review-import','export','candidate-import','apply','adopt','publish'):
        s=sub.add_parser(name); s.add_argument('--work-root',required=True)
        if name=='count': s.add_argument('--cache'); s.add_argument('--count-receipt')
        if name=='approved-execute': s.add_argument('--approval',required=True); s.add_argument('--authorize-posts',action='store_true')
        if name in ('review-import','candidate-import'): s.add_argument('--submission',required=True)
        if name=='apply': s.add_argument('--authorize-page-apply',action='store_true')
        if name=='adopt': s.add_argument('--manifest',required=True); s.add_argument('--identity-approval',required=True)
        if name=='publish':
            for flag in ('remote','bucket','prefix'): s.add_argument('--'+flag,required=True)
    c=sub.add_parser('consume'); c.add_argument('--work-root',required=True); c.add_argument('--element',required=True)
    c.add_argument('--target',default=''); c.add_argument('--purpose',default='discovery'); c.add_argument('--qualification')
    v=sub.add_parser('verify-completion')
    for name in ('receipt','manifest','manifest-key','manifest-sha256','article-key'): v.add_argument('--'+name,required=True)
    v.add_argument('--page')
    args=parser.parse_args(argv)
    try:
        if args.command=='verify-completion':
            result=verify_completion(args.receipt,args.manifest,manifest_key=args.manifest_key,
                manifest_sha256=args.manifest_sha256,article_key=args.article_key,page=args.page)
        elif args.command=='consume':
            work,p,manifest,_,_,binding,_=context(args.work_root)
            result=ae.consumer(work,binding,manifest,args.element,args.target,purpose=args.purpose,qualification=args.qualification)
        elif args.command=='plan': result=plan(Request(args.article,args.element,args.page),manifest=args.manifest,work_root=args.work_root,
            fixture=args.fixture,model_profile=pa.load(args.profile) if args.profile else None,page_scope=pa.load(args.page_scope) if args.page_scope else None)
        elif args.command=='diagnostic-plan': result=diagnostic_plan(args.manifest,args.element,work_root=args.work_root,
            fixture=args.fixture,model_profile=pa.load(args.profile) if args.profile else None)
        elif args.command=='execute': result=execute(work_root=args.work_root)
        elif args.command=='adopt': result=adopt(args.work_root,args.manifest,identity_approval=args.identity_approval)
        elif args.command=='candidate-import': result=candidate_import(args.work_root,args.submission)
        elif args.command=='apply': result=apply(args.work_root,authorize=args.authorize_page_apply)
        elif args.command=='publish': result=publish(args.work_root,args.remote,args.bucket,args.prefix)
        else: result=advance(args.work_root,args.command,cache=getattr(args,'cache',None),count_receipt=getattr(args,'count_receipt',None),
            approval=getattr(args,'approval',None),authorize=getattr(args,'authorize_posts',False),submission=getattr(args,'submission',None))
        print(json.dumps(result,indent=2)); return 0
    except (OSError,ValueError,KeyError,TypeError,ImportError) as exc:
        print(json.dumps(dict(status='hold',error=str(exc))),file=sys.stderr); return 2


if __name__=='__main__': sys.exit(main())
