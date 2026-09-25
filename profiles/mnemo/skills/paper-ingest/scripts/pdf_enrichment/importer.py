"""Import of clearly marked synthetic test responses (offline vertical slice).

The responses file is a JSON object: {request_id: {"content": "<json text>"}}.
Every imported response is stamped synthetic-test-only and is never treated
as scientific output or live provenance. No network. Reuse of a consumed
request slot is rejected; incomplete/truncated output is rejected.
"""
from pathlib import Path
import json
from .io import require, load, save, safe, sha, digest, now_utc
from . import schema, tables, algorithms, accounting, review as review_mod


def _record_for(kind, evidence, value):
    if kind == 'figure':
        from .references import image_refs
        import copy
        schema.validate_figure(value, evidence)
        from .references import copied_claim
        value=copy.deepcopy(value)
        for field in ('shown','caption_context'):
            value[field]={k:([copied_claim(evidence,c) for c in group] if isinstance(group,list) else copied_claim(evidence,group)) for k,group in value[field].items()}
        for field in ('observations','limitations'):
            value[field]=[copied_claim(evidence,c) for c in value[field]]
        children=[]; seen=set()
        for child in value.get('embedded_tables', []):
            require(isinstance(child,dict) and set(child)=={'id','source_refs','table'}, 'embedded-table-keys')
            ident=child['id']
            require(isinstance(ident,str) and ident and ident not in seen, 'duplicate-embedded-table-id')
            seen.add(ident)
            image_refs(evidence,child['source_refs'])
            sub=copy.deepcopy(evidence)
            sub['body_fragments']=[f for f in sub['body_fragments'] if f['fragment_id'] in child['source_refs']]
            require(sub['body_fragments'], 'embedded-table-body-required')
            sub['element_id']=evidence['element_id']+'::embedded-table::'+ident
            rec=tables.assemble(sub,child['table'])
            rec.update(parent_element_id=evidence['element_id'], child_id=ident, standalone=False)
            children.append(rec)
        return dict(kind='figure', embedded_tables=children, scientific_review='pending; valid references do not establish interpretation', element_id=evidence['element_id'], label=evidence.get('label'),
                   fragment_refs=[dict(fragment_id=f['fragment_id'], page=f['page'], crop=f['crop'])
                                  for f in evidence.get('body_fragments', [])],
                   caption_refs=[dict(candidate_id=c['candidate_id'], region_id=c['region_id'], page=c['page'])
                                 for c in evidence.get('captions', [])],
                   shown=value['shown'], observations=value['observations'],
                   caption_context=value['caption_context'], limitations=value['limitations'],
                   caption_only=bool(evidence.get('caption_only')),
                   coverage=schema.figure_coverage(value,evidence),
                   whole_figure_visual_coverage=False)  # No independent visual coverage review.
    if kind == 'table':
        return tables.assemble(evidence, value)
    return algorithms.assemble(evidence, value)


def outcomes(run, plan):
    """Read immutable per-attempt outcomes; interrupted reservations stay unknown."""
    result={}
    known={r['id'] for r in plan['requests'] if r.get('id')}
    index=Path(run)/'enrichment-results.json'
    if index.exists():
        saved=load(index)
        require(isinstance(saved.get('responses'),dict) and set(saved['responses']) <= known,'unknown-result-id')
    for row in plan['requests']:
        if not row.get('id'): continue
        p=safe(run,row['directory'])
        if (p/'outcome.json').exists():
            require(sha(p/'outcome.json')==(p/'outcome.sha256').read_text(),'outcome-binding')
            value=load(p/'outcome.json')
            if value.get('raw_sha256'):
                require(sha(p/value['raw_file'])==value['raw_sha256'],'raw-response-binding')
            result[row['id']]=value
        elif (p/'reservation.json').exists():
            result[row['id']]=dict(status='interrupted',complete=False,reason='reserved-may-have-posted; never retry this run')
    return result


def retain_outcome(run, row, outcome):
    from .io import put
    p=safe(run,row['directory'])
    save(p/'outcome.json',outcome)
    put(p/'outcome.sha256',sha(p/'outcome.json'))


def assemble_response(row, evidence, text, synthetic):
    value=schema.parse(text)
    record=_record_for(row['kind'],evidence,value)
    if row['kind']=='figure':
        complete=bool(record['shown'] or record['observations'] or record['caption_context']) and record['coverage']['status']=='complete' and all(t['complete'] for t in record['embedded_tables'])
    else:
        complete=record['complete']
    variant='caption-only' if row['caption_only'] else 'image-plus-caption'
    record.update(synthetic=synthetic,response_sha256=digest(text.encode()),request_sha256=row['request_sha256'],
                  prompt_sha256=row['prompt_sha256'],caption_only=row['caption_only'],variant=variant,
                  response_schema=schema.RESPONSE_SCHEMA,scientific_review='pending',complete=complete)
    return dict(status='enriched' if complete else 'partial',complete=complete,kind=row['kind'],variant=variant,
                element_id=row['element_id'],document=row['document'],synthetic=synthetic,
                not_scientific_output=synthetic,scientific_review='pending',record=record)


def import_test_response(run, responses_path, request_id=None):
    """Fixture-only import. Preserve the batch, all entries and all failures."""
    from . import bindings
    from .io import put, strict
    import uuid
    run=Path(run).absolute(); plan=bindings.verify(run)
    require(plan['fixture'] is True and (run/'OFFLINE-FIXTURE').is_file(),'synthetic-import-requires-fixture-run')
    require(not (run/'execution-session.json').exists(),'execution-already-started')
    batch=run/'imports'/uuid.uuid4().hex
    raw=Path(responses_path).read_bytes(); put(batch/'raw.json',raw)
    try:
        responses=strict(raw)
        require(isinstance(responses,dict),'responses-object')
        rows={r['id']:r for r in plan['requests'] if r.get('id')}
        require(set(responses)<=set(rows),'unknown-result-id')
        targets=[request_id] if request_id else list(responses)
        require(targets and all(r in responses for r in targets),'missing-request-response')
        for rid in targets:
            require(not (safe(run,rows[rid]['directory'])/'reservation.json').exists(),'response-already-imported:'+rid)
        # Reserve and retain EVERY entry before parsing any content.
        for rid in targets:
            p=safe(run,rows[rid]['directory'])
            save(p/'reservation.json',dict(status='reserved-fixture',synthetic=True,at=now_utc(),batch=str(batch)))
            save(p/'response-raw.json',responses[rid])
        failed=[]
        for rid in targets:
            row=rows[rid]; p=safe(run,row['directory'])
            try:
                entry=responses[rid]
                require(isinstance(entry,dict) and set(entry)=={'content'},'response-entry-shape')
                require(isinstance(entry['content'],str) and entry['content'].strip(),'empty-response')
                result=assemble_response(row,load(p/'source-evidence.json'),entry['content'],True)
            except (ValueError,KeyError,TypeError,IndexError) as exc:
                result=dict(status='failed',complete=False,synthetic=True,reason=type(exc).__name__+':'+str(exc))
                failed.append(rid)
            result.update(raw_file='response-raw.json',raw_sha256=sha(p/'response-raw.json'),finished_at=now_utc())
            retain_outcome(run,row,result)
            save(run/'enrichment-results.json',dict(responses=outcomes(run,plan)),replace=True)
        save(batch/'result.json',dict(imported=targets,failed=failed))
        require(not failed,'response-failures:'+','.join(failed))
        return targets
    except (ValueError,KeyError,TypeError,IndexError) as exc:
        if not (batch/'result.json').exists(): save(batch/'result.json',dict(status='failed',reason=type(exc).__name__+':'+str(exc)))
        raise


def report(run, output=None):
    """Replace only derived report artifacts or write into a NEW external directory."""
    from . import bindings, trusted
    run=Path(run).absolute(); plan=bindings.verify(run, for_execution=False)
    destination=run if output is None else Path(output).absolute()
    if output is not None:
        require(not destination.exists(),'report-output-must-be-new')
        require(not destination.resolve().is_relative_to(run.resolve()) and not destination.resolve().is_relative_to(Path(plan['source_package']['root']).resolve()),'external-report-required')
        destination.mkdir(parents=True)
    results=outcomes(run,plan)
    count_path=run/'counts.json'
    if count_path.exists():
        from .live import verify_counts
        counts=verify_counts(run,plan, method=trusted.read_method_path())
        for rid,c in counts['requests'].items():
            if not c['fits'] and rid not in results:
                results[rid]=dict(status='unsupported',complete=False,reason='full-payload-context-overflow; no trimming')
    acct=accounting.accounting(plan,results)
    selected=[r for r in acct['elements'] if r['kind'] is not None]
    complete=bool(selected) and all(r.get('complete') for r in selected)
    synthetic=plan['fixture'] or any(r.get('synthetic') for r in results.values())
    state=dict(schema='pdf-source-package-enrichment-report-v3',run=str(run),accounting=acct,gaps=accounting.gaps(acct),
               selected_mechanics_complete=complete,requested_work_complete=complete and not synthetic,
               source_package_complete=bool(plan['documents']) and all(d['source_complete'] for d in plan['documents']),
               production_complete=False,human_acceptance='pending',scientific_review='pending',
               exhaustive_extraction_established=False,contains_synthetic_responses=synthetic)
    save(destination/'accounting.json',acct,replace=output is None)
    save(destination/'report.json',state,replace=output is None)
    from .io import put
    for rid,result in results.items():
        record=result.get('record',{})
        if record.get('kind')=='algorithm':
            label='SYNTHETIC TEST RESPONSE: not scientific output.\n' if result.get('synthetic') else 'Model transcription: scientific review pending.\n'
            put(safe(destination,'derived-algorithms/'+rid+'.txt'),label+algorithms.render_text(record)+'\n',replace=True)
        records=[record] if record.get('kind')=='table' else record.get('embedded_tables',[])
        for number,table in enumerate(records):
            if tables.rectangular_dense(table):
                csv,meta=tables.export_csv(table)
                target=safe(destination,'derived-tables/'+rid+'-'+str(number)+'.csv')
                put(target,csv,replace=True)
                save(target.with_suffix('.metadata.json'),meta,replace=True)
    review_mod.render(destination,plan,results,plan['source_package']['root'],evidence_root=run)
    return state
