"""Deterministic annotated exports and exact-use consumer contract."""
import html
import json
from pathlib import Path
from .records import nodes, related, require, resolve_pointer, digest
from .storage import absolute, new, load, save, put, sha, tree, code_hashes
from . import reviews


def affected(view, target):
    return [f for f in view['findings'] if related(target, f['target'])
            and (not f.get('summary_only') or f.get('resolutions') or target == f['target'] or f['target'].startswith(target+'/'))]


def scoped(view, target, aspects):
    # A checked cell never certifies its parent table or an adjacent field.
    return {a: [c for c in view['coverage'] if c['target'] == target and c['aspect'] == a] for a in aspects}


def exact_view(view, target, *, purpose='discovery', aspects=('content',), qualification=None, source_inspection=None):
    require(purpose in ('discovery','summary','exact','algorithm-specification'), 'consumer-purpose')
    content = resolve_pointer(view['outcome'], target)
    require(aspects and set(aspects) <= set(reviews.ASPECTS), 'consumer-review-aspects')
    # Exact reuse cannot hide unreviewed units/layout by requesting text alone.
    checked_aspects = reviews.ASPECTS if purpose in ('exact','algorithm-specification') else aspects
    coverage = scoped(view, target, checked_aspects)
    unknown = [a for a, checks in coverage.items() if not checks]
    relevant = affected(view, target)
    warnings = [f for f in relevant if f['status'] == 'unresolved']
    # A resolution is an attributed proposal, not a corrected outcome. Only
    # exact JSON equality proves that it requests no change to its own target.
    corrections = [f['id'] for f in relevant if any(
        digest(r['proposed_value']) != digest(resolve_pointer(view['outcome'], f['target']))
        for r in f.get('resolutions', []))]
    needs_qualification = bool(warnings or unknown or corrections)
    algorithm = view['outcome'].get('record', {}).get('kind') == 'algorithm'
    if source_inspection is not None:
        require(set(source_inspection) == {'reviewer','reason','evidence'}, 'inspection-attestation-fields')
        reviews.provenance(source_inspection['reviewer'])
        require(isinstance(source_inspection['reason'], str) and source_inspection['reason'].strip(), 'inspection-reason')
        inspection_refs = reviews.evidence(view, source_inspection['evidence'])
        require(inspection_refs, 'inspection-evidence-required')
        owners = reviews.owners_for(view, target)
        require(owners and {r['owner'] for r in inspection_refs} <= owners, 'inspection-wrong-source-association')
        if algorithm or purpose == 'algorithm-specification':
            require(any(r['kind'] == 'crop' for r in inspection_refs), 'algorithm-inspection-requires-crop')
    if qualification is not None:
        require(isinstance(qualification, str) and qualification.strip(), 'explicit-qualification-text')
    strict = purpose in ('exact','algorithm-specification')
    require(not strict or not needs_qualification or qualification or source_inspection,
            'exact-use-requires-source-inspection-or-explicit-qualification')
    require(purpose != 'algorithm-specification' or source_inspection is not None,
            'algorithm-specification-always-requires-source-inspection')
    return dict(element_id=view['element_id'], source_sha256=view['source_sha256'], target=target,
                content=content, findings=relevant, unresolved_findings=warnings, unreviewed_aspects=unknown,
                unapplied_correction_findings=corrections, original_unchanged=True,
                coverage=coverage, scope_review_status=('reviewed-scoped-content' if not unknown else
                    'partially-reviewed' if any(coverage.values()) else 'unreviewed'),
                purpose=purpose, qualification=qualification, source_inspection=source_inspection,
                use_condition='Original unchanged; retain attributed proposals and inspect source or explicitly qualify affected scope.' if needs_qualification else
                              'Reviewed only for the named scope/aspects; retain resolution history; not a correctness guarantee.',
                algorithm_not_default=algorithm, notice=reviews.NOTICE)


def page_view(view, target, *, qualification=None):
    """Ordinary paper claims need material qualifications, not coverage certification."""
    value=exact_view(view,target,purpose='summary',qualification=qualification or None)
    needs=bool(value['unresolved_findings'] or value['unapplied_correction_findings'])
    require(not needs or (isinstance(qualification,str) and qualification.strip()),
            'material-finding-requires-qualification')
    return value


def content_targets(outcome):
    """Small semantic targets; full unchanged record stays alongside these."""
    result = []
    for path, value in nodes(outcome).items():
        if path.startswith('/record/') and path.rsplit('/',1)[-1] in (
                'raw_value','text','caption_quote','units','header_hierarchy','status','unresolved','unresolved_symbols'):
            # Native source references are provenance, not generated statements.
            if not any('/'+key+'/' in path for key in ('source_refs','native_spans','caption_sources')):
                result.append(path)
    return result or ['']


def warning_html(view, path):
    relevant = affected(view, path)
    messages = [] if view.get('policy')=='observed-limitations-v1' else ['Unreviewed scope: '+path] if not any(c['target'] == path for c in view['coverage']) else ['Scoped review only: '+path]
    for f in relevant:
        messages.append(f['id']+' | '+f['status']+' | '+f['category']+' | '+f['stage']+' | '+f['reason'])
        if f.get('resolutions'):
            messages.append('Original unchanged. Attributed resolution proposals for '+f['target']+': '+
                            json.dumps(f['resolutions'], ensure_ascii=False, sort_keys=True))
    if not messages: return ''
    return '<aside class="warning">'+''.join('<p>'+html.escape(m)+'</p>' for m in messages)+'</aside>'


def render_record(view, record, path='/record'):
    esc = html.escape
    overview = warning_html(view, '') if path == '/record' else ''
    if record.get('kind') == 'table':
        out = [overview, warning_html(view, path), '<table>']
        by_position = {(c['row'],c['column']):(i,c) for i,c in enumerate(record['cells'])}
        for row in record['rows']:
            out.append('<tr>')
            for column in record['columns']:
                found = by_position.get((row['index'],column['index']))
                if not found: continue
                index, cell = found; cp = path+'/cells/'+str(index)
                out.append(f'<td rowspan="{int(cell["row_span"])}" colspan="{int(cell["col_span"])}">')
                out.append('<pre>'+esc(str(cell.get('raw_value')))+'</pre>'+warning_html(view,cp))
                out.append('<pre>'+esc(json.dumps(cell.get('notation'),ensure_ascii=False))+'</pre></td>')
            out.append('</tr>')
        out.append('</table>')
        for name in ('units','header_hierarchy','caption_markers','unresolved'):
            out.append('<h4>'+name+'</h4><pre>'+esc(json.dumps(record.get(name),ensure_ascii=False))+'</pre>'+warning_html(view,path+'/'+name))
        return ''.join(out)
    if record.get('kind') == 'algorithm':
        out = [overview, warning_html(view,path), '<p>Algorithm discovery only; specification use requires source inspection.</p>']
        for index, line in enumerate(record.get('lines', [])):
            lp = path+'/lines/'+str(index)
            out.append('<section><pre>'+esc(json.dumps(line,ensure_ascii=False,indent=2))+'</pre>'+warning_html(view,lp)+'</section>')
        return ''.join(out)
    out = [overview]
    for name in ('shown','observations','caption_context','limitations'):
        value = record.get(name, [])
        for p, v in nodes(value, path+'/'+name).items():
            if isinstance(v, dict) and ('text' in v or 'caption_quote' in v):
                out.append('<section><pre>'+esc(json.dumps(v,ensure_ascii=False,indent=2))+'</pre>'+warning_html(view,p)+'</section>')
    for index, child in enumerate(record.get('embedded_tables', [])):
        out.append(render_record(view,child,path+'/embedded_tables/'+str(index)))
    return ''.join(out)


def render(machine):
    parts = ['<!doctype html><html lang="en"><meta charset="utf-8"><title>Qualified enrichment</title>',
             '<style>body{font-family:system-ui;margin:2rem}pre{white-space:pre-wrap}td{border:1px solid #777;vertical-align:top}.warning{background:#fff0c0;padding:.3em}section{border-top:1px solid #777}</style>',
             '<h1>Qualified enrichment, not scientific certification</h1><p>'+html.escape(reviews.NOTICE)+'</p>',
             '<pre>'+html.escape(json.dumps(machine['eligibility'],ensure_ascii=False,indent=2))+'</pre>']
    for view in machine['elements']:
        parts.append('<section><h2>'+html.escape(view['element_id'])+'</h2>')
        parts.append('<p>Source SHA256: '+view['source_sha256']+'</p>')
        if view.get('source_pdf'):
            parts.append('<a href="'+html.escape(Path(view['source_pdf']).as_uri(),quote=True)+'">Original PDF</a>')
        paths=None
        if machine.get('schema')=='qualified-enrichment-export-v2':
            import portable_articles as pa
            _,paths=pa.verify_local(machine['manifest'])
        for fragment in view['evidence'].get('body_fragments', []) + view['evidence'].get('captions', []):
            crop = paths[fragment['crop']] if paths is not None else absolute(Path(machine['source_package'])/fragment['crop'])
            parts.append('<p><a href="'+html.escape(crop.as_uri(),quote=True)+'">Source crop, physical page '+
                         html.escape(str(fragment['page']))+'</a></p>')
        parts.append(render_record(view, view['outcome'].get('record', {})))
        parts.append('<details><summary>Original outcome and source locators</summary><pre>'+html.escape(json.dumps(
            {'outcome':view['outcome'],'evidence':view['evidence']},ensure_ascii=False,indent=2))+'</pre></details>')
        for consumer in view['consumer_views']:
            parts.append('<section><h4>'+html.escape(consumer['target'])+'</h4><pre>'+html.escape(json.dumps(consumer['content'],ensure_ascii=False))+'</pre>'
                         +warning_html(view,consumer['target'])+'</section>')
        parts.append('<details><summary>All findings, scoped reviews and attributed resolutions</summary><pre>'+html.escape(json.dumps(
            {k:view[k] for k in ('findings','coverage','review_status')},ensure_ascii=False,indent=2))+'</pre></details></section>')
    return ''.join(parts)+'</html>'


def eligibility(state):
    holds = list(state['execution_holds'])
    if state['fixture']: holds.append('fixture-not-production')
    if state['kind'] != 'qualified-job': holds.append('review-only-not-default-production-roster')
    if 'source_readiness' in state:
        holds.extend(state['source_readiness']['holds'])
    elif any(d.get('source_status') != 'complete' or not d.get('source_complete') for d in state['documents']):
        holds.append('source-acquisition-extraction-not-complete')
    accounting = []
    for element in state['elements']:
        value = element['outcome']; status = value['status']
        if element['content_type'] in ('algorithm','code') and not element['eligible_default']:
            disposition = 'algorithm-deferred-not-selected'
        else: disposition = status
        if element['eligible_default'] and (value.get('variant') == 'caption-only' or value.get('record',{}).get('caption_only')):
            holds.append('caption-only-not-image-enriched')
        accounting.append(dict(element_id=element['element_id'], document=element['document'],
                               content_type=element['content_type'], eligible_default=element['eligible_default'],
                               disposition=disposition, accepted_structured_record=bool(value.get('record')),
                               source_pdf=element['source_pdf'], source_sha256=element['source_sha256']))
    return dict(status='execution-hold' if holds else 'qualified-production-eligible',
                qualified_production_eligible=not holds, holds=sorted(set(holds)),
                element_accounting=accounting, total_elements=len(accounting),
                eligible_elements=sum(e['eligible_default'] for e in accounting),
                zero_eligible=not any(e['eligible_default'] for e in accounting),
                scientific_correctness='not-established', human_acceptance='not-established',
                note=('Partial source outcomes remain recorded; pending source work requires assessment.' if 'source_readiness' in state else
                      'Field limitations and partial enrichment do not waive source-stage execution holds.'))


def build(root):
    root = absolute(root); dossier = reviews.verify(root)
    entries, views = reviews._reviewed_decisions(root,dossier)
    for view in views:
        view['consumer_views'] = [exact_view(view,p) for p in content_targets(view['outcome'])]
    machine = dict(schema='qualified-enrichment-export-v1', review_root=str(root),
                   review_bindings=tree(root), source_package=dossier['snapshot']['source_package'],
                   source_bindings=dossier['snapshot']['source_bindings'], code=code_hashes(),
                   eligibility=eligibility(dossier['snapshot']), elements=views, notice=reviews.NOTICE)
    if reviews.policy(dossier)!='legacy':
        import article_enrichment as ae
        assessment=reviews.assessment(dossier,entries)
        accounting=dossier['snapshot']['request_accounting']
        ready=ae.readiness(accounting,assessment,dossier['snapshot'].get('source_readiness'))
        machine.update(schema='qualified-enrichment-export-v2',policy=reviews.policy(dossier),manifest=dossier['snapshot']['manifest'],
                       request_accounting=accounting,execution_complete=accounting['complete'],assessment=assessment,readiness=ready)
        e=machine['eligibility']; e['holds']=sorted(set(e['holds']+ready['holds']))
        e['qualified_production_eligible']=not e['holds']
        e['status']='qualified-production-eligible' if not e['holds'] else 'execution-hold'
    return machine


def export(root, output):
    machine = build(root)
    dossier = load(absolute(root)/'dossier.json')
    destination = new(output, [absolute(root), absolute(machine['source_package']), absolute(dossier['snapshot']['path'])])
    save(destination/'handoff.json', machine)
    put(destination/'annotated.html', render(machine))
    return machine


def verify_export(path, source_package=None, production=True):
    path = absolute(path); saved = load(path)
    require(saved['schema'] in ('qualified-enrichment-export-v1','qualified-enrichment-export-v2'), 'export-schema')
    actual = build(saved['review_root'])
    from pdf_enrichment.trusted import validate_code_provenance
    actual['code'] = validate_code_provenance(saved['code'])
    require(saved == actual, 'removed-or-mismatched-enrichment-warnings')
    require((path.parent/'annotated.html').read_text() == render(actual), 'removed-or-mismatched-readable-warnings')
    if source_package is not None:
        require(actual['source_package'] == str(absolute(source_package)), 'enrichment-wrong-source-package')
    if production:
        require(actual['eligibility']['qualified_production_eligible'], 'enrichment-execution-hold:'+','.join(actual['eligibility']['holds']))
    return actual
