"""Downstream request preparation and partial-state accounting."""
from pathlib import Path
import copy
from .io import *
from . import preparation, classification, association


def output_bindings(root, directory):
    p = Path(root) / directory
    return {str(x.relative_to(root)): sha(x) for x in sorted(p.rglob('*'))
            if x.is_file() and (x.name in ('response-body.json','raw-selection.json','decoded.json','candidates.json',
                'validation.json','call.json','reservation.json') or 'crops' in x.parts)}


def verify_result(root, row):
    p = Path(root) / row['directory']
    receipt = load(p / 'output-bindings.json')
    for name, h in receipt.items():
        require(sha(safe(root,name)) == h, 'result-artifact-changed:' + name)
    call = load(p / 'call.json')
    require(call['request_sha256'] == row['request_sha256'] == sha(p/'request-wire.json'), 'result-request-binding')
    require(load(p/'reservation.json')['transport_origin'] == call['transport_origin'], 'result-origin-binding')
    if (p/'response-body.json').exists():
        require(sha(p/'response-body.json') == call['saved_response_sha256'], 'response-binding')
    return call


def collect(root):
    root=Path(root); manifest=load(root/'manifest.json'); result={d['identity']:[] for d in manifest['documents']}
    if not (root/'initial-plan.json').exists(): return result
    for row in load(root/'initial-plan.json')['requests']:
        p=root/row['directory']
        if not (p/'candidates.json').exists(): continue
        call=verify_result(root,row)
        cs=load(p/'candidates.json')
        if not manifest['fixture']:
            require(call['transport_origin']=='parent-authorized-live' and all(c['extraction_origin']=='parent-authorized-live' for c in cs), 'no-fixture-promotion')
        result[row['document']].extend(cs)
    if (root/'classification-plan.json').exists():
        for row in load(root/'classification-plan.json')['requests']:
            p=root/row['directory']
            if not (p/'validation.json').exists(): continue
            call=verify_result(root,row)
            if call.get('selection_status')!='validated': continue
            value=load(p/'raw-selection.json'); candidates=load(p/'candidates.json')
            classification.classify_validate(value,candidates)
            known={c['id']:c for c in result[row['document']]}
            for obs in value['classifications']:
                c=known[obs['candidate_id']]
                c.update(classification_observation=copy.deepcopy(obs), content_type=obs['content_type'],
                         type_origin='model-classification-not-native-text')
                if obs['source_label'] is not None:
                    item=dict(label=obs['source_label'],origin='model-observation:'+obs['label_evidence'])
                    if item not in c['observed_labels']: c['observed_labels'].append(item)
    for cs in result.values():
        require(len({c['id'] for c in cs})==len(cs),'duplicate-candidate')
        cs.sort(key=association.rank)
    return result


def prior_dependencies(root, phases):
    dependencies=['manifest.json']
    for phase in phases:
        plan_path=root/f'{phase}-plan.json'
        if not plan_path.exists(): continue
        dependencies.append(str(plan_path.relative_to(root)))
        for row in load(plan_path)['requests']:
            p=root/row['directory']
            if (p/'output-bindings.json').exists():
                verify_result(root,row)
                dependencies += list(load(p/'output-bindings.json')) + [row['directory']+'/output-bindings.json']
    return sorted(set(dependencies))


def prepare_stage(root, phase):
    root=Path(root); require(phase in ('classification','association'),'downstream-phase')
    require(not (root/'stop.json').exists(),'shared-stop-pending')
    require(not (root/f'{phase}-plan.json').exists(),'stage-already-prepared')
    require((root/'initial-complete.json').exists(),'initial-execution-must-finish')
    manifest=load(root/'manifest.json'); all_cs=collect(root); rows=[]; dispositions=[]
    if phase=='association' and any('classification' in d['channels'] for d in manifest['documents']):
        require((root/'classification-complete.json').exists(),'classification-execution-must-finish')
    dependencies=prior_dependencies(root,['initial'] if phase=='classification' else ['initial','classification'])
    for index,doc in enumerate(manifest['documents'],1):
        if phase not in doc['channels']: continue
        cs=all_cs[doc['identity']]
        if phase=='classification':
            for page in doc['pages']:
                if not page['selected'] or page['policy']['disposition']!='eligible': continue
                candidates=[c for c in cs if c['page']==page['page'] and c['detector_family']=='structured']
                if not candidates:
                    dispositions.append(dict(document=doc['identity'],page=page['page'],status='no-exported-candidates', not_proof_of_empty=True)); continue
                row=dict(identity=doc['identity'],page=page['page'],directory=page['directory'])
                wire=classification.classifier_request(root,row,candidates)
                ident=f'd{index:04d}-p{page["page"]:04d}-classification'
                inputs=[doc['raw'],page['directory']+'/inventory.json',page['directory']+'/original-wire.json']
                inputs += [r['crop'] for c in candidates for r in c['regions']]
                save(root/'requests'/ident/'candidates.json',candidates)
                inputs.append(f'requests/{ident}/candidates.json')
                rows.append(preparation.request_row(root,phase,ident,phase,doc['identity'],page['page'],wire,inputs,
                    page_directory=page['directory'],raw=doc['raw']))
        else:
            association.validate_candidates(cs)
            if not cs:
                dispositions.append(dict(document=doc['identity'],status='no-exported-candidates',not_proof_of_empty=True)); continue
            ident=f'd{index:04d}-association'
            pages=[p for p in doc['pages'] if p['policy']['disposition']=='eligible']
            wire=preparation.association_request(root,doc,cs,pages)
            save(root/'requests'/ident/'candidates.json',cs)
            inputs=[doc['raw'],f'requests/{ident}/candidates.json']
            inputs += [p[k] for p in doc['pages'] for k in ('page_image','native_text')]
            inputs += [r['crop'] for c in cs for r in c['regions']]
            rows.append(preparation.request_row(root,phase,ident,phase,doc['identity'],None,wire,inputs,
                representation='whole-document',image_omitted_pages=[p['page'] for p in doc['pages'] if p not in pages]))
    total=sum(len(load(root/f'{p}-plan.json')['requests']) for p in ('initial','classification') if (root/f'{p}-plan.json').exists())+len(rows)
    require(total<=manifest['maximum_posts'],'stage-budget-exceeded')
    plan=dict(phase=phase,requests=rows,dispositions=dispositions,dependencies=dependencies)
    save(root/f'{phase}-plan.json',plan)
    return plan


def assemble_logical(cs, selection, pages, channels):
    """Accepted reference assembly plus integration-only coverage diagnostics."""
    conflicts = association.containment(cs)
    logical = association.final_dispositions(cs, selection, conflicts=conflicts)
    unresolved = conflicts + (selection.get('conflicts', []) if selection else [])
    logical['unresolved_conflicts'] = copy.deepcopy(unresolved)
    if unresolved or selection is not None and selection['status'] != 'ok':
        logical['complete'] = False
    known = {p['page']: p for p in pages}
    candidates = {c['id']:c for c in cs}
    for element in logical['elements']:
        span = [r['page'] for r in element['ordered_source_fragments']]
        typ = element['content_type']
        bodies = ['figure'] if typ == 'figure' else ['structured'] if typ in ('table','algorithm','code','data-file') else ['figure','structured']
        if typ == 'unknown':
            families = {candidates[i].get('detector_family') for i in element['body_refs']}
            # Detector lineage identifies a missing channel without claiming a
            # scientific type from provisional table-only metadata.
            if families and families <= {'structured','table-only','table','offline-recovered-selection'}:
                bodies = ['structured']
            elif families == {'figure'}:
                bodies = ['figure']
        relevant = [ch for ch in ['caption'] + bodies if ch in channels]
        warnings = []
        for n in range(min(span) + 1, max(span)):
            outcomes = known.get(n, {}).get('outcomes', {})
            for channel in relevant:
                status = outcomes.get(channel, 'page-availability-unknown')
                if status in ('complete', 'policy-excluded'):
                    continue
                warnings.append(dict(kind='possible-completeness-gap', page=n, channel=channel,
                    status=status, source_confirmed_omission=False,
                    message=f'Physical page {n}: {channel} availability is {status}. The group may be incomplete; no omitted source content or fragment is established.'))
        element['coverage_warnings'] = warnings
    return logical


def final_state(root, inspection_dir=None):
    root=Path(root); manifest=load(root/'manifest.json'); all_cs=collect(root); docs=[]
    plans={p:load(root/f'{p}-plan.json') for p in ('initial','classification','association') if (root/f'{p}-plan.json').exists()}
    for doc in manifest['documents']:
        gaps=[]; pages=[]; cs=all_cs[doc['identity']]
        for page in doc['pages']:
            outcomes={}
            for ch in doc['channels']:
                if ch not in ('caption','figure','structured'): continue
                if not page['selected']: status='outside-extraction-scope'
                elif page['policy']['disposition']=='policy-excluded': status='policy-excluded'
                elif ch in ('figure','structured') and page['source_limitation']: status='source-limitation-native-inventory'
                else:
                    request=page['requests'].get(ch,{})
                    r=next((r for r in plans['initial']['requests'] if r['id']==request.get('id')),None)
                    if r is None: status=request.get('status','unattempted')
                    elif (root/r['directory']/'output-bindings.json').exists():
                        call=verify_result(root,r); status='complete' if call['complete'] else call.get('selection_status') if call.get('selection_status') not in (None,'unattempted') else call['status']
                    elif (root/r['directory']/'reservation.json').exists(): status='interrupted-reserved-may-have-posted'
                    else: status=r['status'] if r['status']!='ready' else 'unattempted'
                outcomes[ch]=status
                if status not in ('outside-extraction-scope','policy-excluded','complete'): gaps.append(dict(page=page['page'],channel=ch,status=status))
            pages.append(dict(page=page['page'],selected=page['selected'],policy=page['policy'],outcomes=outcomes,
                page_image=page['page_image'],raw=doc['raw'],directory=page['directory'],
                **{k:page[k] for k in ('rotation','rotation_matrix','cropbox','mediabox','page_bbox') if k in page}))
        for phase in ('initial','classification','association'):
            if phase != 'initial' and phase not in doc['channels']: continue
            if phase not in plans or not (root/f'{phase}-complete.json').exists():
                gaps.append(dict(channel=phase,status='unattempted')); continue
            for r in plans[phase]['requests']:
                if r['document']!=doc['identity']: continue
                if not (root/r['directory']/'output-bindings.json').exists(): gaps.append(dict(channel=phase,status='unattempted',request_id=r['id']))
                elif not verify_result(root,r)['complete']: gaps.append(dict(channel=phase,status='incomplete',request_id=r['id']))
        selection=None
        for r in plans.get('association',{}).get('requests',[]):
            if r['document']==doc['identity'] and (root/r['directory']/'validation.json').exists():
                verify_result(root,r); selection=load(root/r['directory']/'raw-selection.json')
        # Candidate references retain the accepted association semantics and
        # explicit unassociated/conflict dispositions, never inferred links.
        logical=assemble_logical(cs,selection,pages,doc['channels'])
        if logical['unresolved_conflicts']:
            gaps.append(dict(channel='content-association',status='unresolved-content-or-association-conflicts'))
        if 'association' not in doc['channels']:
            logical['complete']=False
        elif not logical['complete']:
            gaps.append(dict(channel='association', status='incomplete-candidate-accounting-or-conflicts'))
        request_states=[]; association_scope=None
        for phase, plan in plans.items():
            for row in plan['requests']:
                if row['document'] != doc['identity']:
                    continue
                p=root/row['directory']
                call=load(p/'call.json') if (p/'call.json').exists() else dict(attempted=False,status='unattempted')
                files=[str(x.relative_to(root)) for x in sorted(p.rglob('*')) if x.is_file()]
                crops=[name for name in files if '/crops/' in name and name.lower().endswith('.png') and not Path(name).stem.lower().startswith('overview')]
                represented={r['crop'] for c in cs for r in c['regions']}
                partial=[name for name in crops if not call.get('complete') or name not in represented] if row['channel'] in ('caption','figure','structured') else []
                if row['channel']=='association':
                    wire=load(p/'request-wire.json')
                    evidence=strict(wire['messages'][0]['content'][0]['text'].split('\nSOURCE EVIDENCE\n',1)[1])
                    association_scope=dict(mode=evidence['visual_context_mode'],
                        included_image_pages=evidence['source_physical_pages'],omitted_image_pages=evidence['image_omitted_pages'])
                request_states.append(dict(id=row['id'],phase=phase,channel=row['channel'],page=row['page'],
                    directory=row['directory'],preflight_status=row['status'],count=row.get('count'),call=call,files=files,
                    actual_crop_count=len(crops),partial_crops=partial,partial_crop_count=len(partial)))
        docs.append(dict(identity=doc['identity'],raw=doc['raw'],page_count=doc['page_count'],pages=pages,requests=request_states,
            extraction_scope=doc['extraction_scope'],package_kind=doc['package_kind'],candidates=cs,
            logical=logical,association_input_scope=association_scope,gaps=gaps,requested_work_complete=not gaps,
            complete_package=not gaps and doc['extraction_scope']=='whole-document' and set(doc['channels'])==set(preparation.CHANNELS) and logical['complete']))
    state = dict(schema='pdf-final-state-v1',fixture=manifest['fixture'],documents=docs,
        requested_work_complete=all(d['requested_work_complete'] for d in docs),human_acceptance='pending',
        exhaustive_extraction_established=False)
    from .reporting import facts
    state['facts'] = facts(root, state, inspection_dir)
    return state
