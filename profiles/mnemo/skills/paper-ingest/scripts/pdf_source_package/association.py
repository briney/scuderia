import copy, math, re
from .io import require, digest, dumps

LABEL = re.compile(r'(?<!\w)(?P<prefix>(?:(?:Extended Data|Supplementary)\s+)?)(?P<kind>Figure|Fig\.|Table|Algorithm|Data[ -]file)\s+(?P<number>S?\d+[A-Za-z]?)(?!\w)',re.I)


def label_key(s):
    if s is None: return None
    m=LABEL.fullmatch(s.strip().rstrip('.:'))
    require(m is not None,'unknown-label-namespace')
    kind=m['kind'].lower().replace(' ','-')
    if kind=='fig.': kind='figure'
    return (m['prefix'].strip().lower(),kind,m['number'].lower())


def leading_labels(text):
    # An inline reference to another figure/table is not this caption's heading.
    text=re.sub(r'^\s*(?:caption|legend)\s+for\s+','',text,flags=re.I).lstrip()
    m=LABEL.match(text)
    return [] if m is None else [dict(label=m.group(),origin='native-text')]


def labels(c):
    return {label_key(x['label']) for x in c['observed_labels']}


def compatibility_type(c):
    if c['role']=='body' and c['type_origin']=='table-only-detector-unconfirmed':
        # Detector family is not a source-confirmed classification. Only an
        # actual native heading supplies a type constraint for this body.
        native={label_key(x['label'])[1] for x in leading_labels(c['native_text'])}
        return next(iter(native)) if len(native)==1 else None
    return c['content_type'] if c['content_type'] not in ('unknown','uncertain','other') else None


def logical_type(members):
    native={label_key(x['label'])[1] for c in members for x in leading_labels(c['native_text'])}
    types={t for c in members if (t:=compatibility_type(c)) is not None}
    if len(native)==1: return next(iter(native)),'native-printed-namespace'
    if len(types)==1: return next(iter(types)),'inferred-from-compatible-recorded-observations'
    return 'unknown','no-source-supported-type'


def bbox_ok(b):
    require(isinstance(b,list) and len(b)==4 and all(type(v) in (int,float) and math.isfinite(v) for v in b),'nonfinite-or-unknown-geometry')
    require(b[0]<b[2] and b[1]<b[3],'inverted-or-empty-geometry')


def rank(c):
    r=min(c['regions'],key=lambda r:(r['page'],r['bbox'][1],r['bbox'][0]))
    return (c['page'],r['bbox'][1],r['bbox'][0],c['id'])


def validate_candidates(cs):
    require(len({c['id'] for c in cs})==len(cs),'duplicate-input-candidate')
    require(len({(c['source_document'],c['source_sha256']) for c in cs})<=1,'cross-document-candidates')
    for c in cs:
        require(c['role'] in ('body','caption','note'),'unknown-role')
        require(c['content_type'] in ('figure','table','algorithm','code','data-file','other','uncertain','unknown'),'unknown-content-type')
        require(type(c['page']) is int and c['page']>=1,'physical-page')
        require(c['regions'],'missing-source-region')
        labels(c)
        for r in c['regions']:
            bbox_ok(r['bbox'])
            require(r['page']==c['page'],'source-region-page')
            for line in r['lines']:
                bbox_ok(line['bbox']); require(line['page']==c['page'],'source-line-page')
                require(isinstance(line['text'],str),'native-text-schema')
        require(c['regions']==sorted(c['regions'],key=lambda r:(r['page'],r['bbox'][1],r['bbox'][0],r['id'])),'fragment-source-order')


def validate(value,cs):
    validate_candidates(cs)
    require(isinstance(value,dict) and set(value)=={'status','groups','unassociated','conflicts'},'association-schema')
    require(value['status'] in ('ok','unresolved'),'association-status')
    require(all(isinstance(value[k],list) for k in ('groups','unassociated','conflicts')),'association-lists')
    require(value['status']=='unresolved' or not value['conflicts'],'conflict-status')
    known={c['id']:c for c in cs}; seen=set()
    def refs(ids,doc,roles):
        require(isinstance(ids,list),'reference-list')
        found=[]
        for i in ids:
            require(isinstance(i,str) and i in known,'unknown-reference')
            c=known[i]
            require(c['source_document']==doc,'wrong-source-document')
            require(c['role'] in roles,'wrong-role-reference')
            require(i not in seen,'duplicate-reference'); seen.add(i); found.append(c)
        require(found==sorted(found,key=rank),'wrong-source-order')
        return found
    for g in value['groups']:
        require(isinstance(g,dict) and set(g)=={'source_document','body_refs','caption_note_refs','label'},'group-schema')
        bs=refs(g['body_refs'],g['source_document'],('body',)); require(bs,'body-required')
        ns=refs(g['caption_note_refs'],g['source_document'],('caption','note'))
        members=bs+ns
        # Unknown model classification does not override a printed namespace.
        types={t for c in members if (t:=compatibility_type(c)) is not None}
        keys=set().union(*(labels(c) for c in members))
        require(len(types)<=1,'group-type-incompatible')
        require(len({k[1] for k in keys})<=1,'group-namespace-incompatible')
        require(not types or not keys or {k[1] for k in keys}<=types,'label-type-incompatible')
        require(len(keys)<=1,'distinct-source-labels-cannot-merge')
        require(g['label'] is None or isinstance(g['label'],str) and bool(g['label'].strip()),'group-label-schema')
        require(g['label'] is None or label_key(g['label']) in keys,'unsupported-label')
        # A note does not need to repeat the parent label. No text is generated.
    for row in value['unassociated']:
        require(isinstance(row,dict) and set(row)=={'candidate_id','source_document'},'unassociated-schema')
        refs([row['candidate_id']],row['source_document'],('body','caption','note'))
    for row in value['conflicts']:
        require(isinstance(row,dict) and set(row)=={'candidate_refs','source_document','reason'},'conflict-schema')
        require(row['reason'] in ('ambiguous-association','overlapping-content','insufficient-source'),'conflict-reason')
        require(row['candidate_refs'],'empty-conflict')
        refs(row['candidate_refs'],row['source_document'],('body','caption','note'))
    require(seen==set(known),'omitted-candidates')
    return dict(status='passed',assigned_once=sorted(seen),candidate_count=len(cs),semantic_review='pending-parent')


def wire_candidate(c):
    # Strict positive whitelist. Never includes old predictions, uncertainty, or verdicts.
    return {k:copy.deepcopy(c[k]) for k in ('id','source_document','source_sha256','page','role','content_type','type_origin','observed_labels','native_text')} | {
        # Member-level inventory stays in source artifacts. Association selects
        # component references, so repeated per-line text/geometry is redundant.
        'regions':[{k:copy.deepcopy(r[k]) for k in ('id','page','bbox','coordinate_system')} for r in c['regions']]}


def containment(cs):
    result=[]
    for i,a in enumerate(cs):
        if a['role']!='body': continue
        for b in cs[i+1:]:
            if b['role']!='body' or a['page']!=b['page'] or a['content_type']==b['content_type']: continue
            overlaps=[]
            for ar in a['regions']:
                for br in b['regions']:
                    x,y=ar['bbox'],br['bbox']
                    area=max(0,min(x[2],y[2])-max(x[0],y[0]))*max(0,min(x[3],y[3])-max(x[1],y[1]))
                    fraction=area/min((x[2]-x[0])*(x[3]-x[1]),(y[2]-y[0])*(y[3]-y[1]))
                    if fraction>=0.98: overlaps.append(dict(first_region=ar['id'],second_region=br['id'],contained_fraction=fraction))
            if overlaps: result.append(dict(candidate_refs=[a['id'],b['id']],status='unresolved conflict',reason='cross-type-contained-content',regions=overlaps))
    return result


def final_dispositions(cs,selection=None,conflicts=(),failed=False,partition_pending=False):
    byid={c['id']:c for c in cs}; dispositions={}; elements=[]
    for c in cs:
        dispositions[c['id']]=dict(candidate_id=c['id'],status='policy-excluded' if c['disposition']=='policy-excluded' else
            'unavailable/failed' if c['availability']!='available' or failed else
            'unresolved conflict' if partition_pending else 'explicitly unassociated',
            reason=c.get('exclusion_reason') or ('association-pending' if selection is None else 'model-unassociated'))
    conflict_ids=set().union(*(set(x['candidate_refs']) for x in conflicts)) if conflicts else set()
    if selection is not None:
        eligible=[c for c in cs if c['disposition']=='eligible' and c['availability']=='available']
        validate(selection,eligible)
        conflict_ids.update(i for x in selection['conflicts'] for i in x['candidate_refs'])
        for g in selection['groups']:
            refs=g['body_refs']+g['caption_note_refs']
            if conflict_ids.intersection(refs):
                conflict_ids.update(refs); continue
            inferred_type,inferred_origin=logical_type([byid[i] for i in refs])
            e=dict(id=byid[refs[0]]['source_document']+'::element-'+digest(dumps(refs))[:16],
                source_document=g['source_document'],content_type=inferred_type,type_origin=inferred_origin,label=g['label'],
                member_type_observations=[dict(candidate_id=i,observed_content_type=byid[i]['content_type'],type_origin=byid[i]['type_origin'],detector_family=byid[i].get('detector_family')) for i in refs],
                body_refs=g['body_refs'],caption_note_refs=g['caption_note_refs'],
                ordered_source_fragments=[dict(candidate_id=i,**r) for i in sorted(refs,key=lambda i:rank(byid[i])) for r in byid[i]['regions']],
                status='reference-validated; semantic review pending')
            elements.append(e)
            for i in refs: dispositions[i].update(status='grouped',reason='reference-only-selection',element_id=e['id'])
    for i in conflict_ids:
        if dispositions[i]['status']!='policy-excluded': dispositions[i].update(status='unresolved conflict',reason='explicit-content-or-association-conflict')
    require(set(dispositions)==set(byid),'final-accounting')
    return dict(elements=elements,dispositions=list(dispositions.values()),complete=not any(x['status'] in ('unavailable/failed','unresolved conflict') or x['reason']=='association-pending' for x in dispositions.values()))
