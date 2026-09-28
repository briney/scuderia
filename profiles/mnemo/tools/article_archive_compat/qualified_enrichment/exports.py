"""Historical read-only dependency closure; extracted without changing validation contracts."""
from .records import nodes, related, require, resolve_pointer, digest
from . import reviews

def affected(view, target):
    return [f for f in view['findings'] if related(target, f['target']) and (not f.get('summary_only') or f.get('resolutions') or target == f['target'] or f['target'].startswith(target + '/'))]

def scoped(view, target, aspects):
    return {a: [c for c in view['coverage'] if c['target'] == target and c['aspect'] == a] for a in aspects}

def exact_view(view, target, *, purpose='discovery', aspects=('content',), qualification=None, source_inspection=None):
    require(purpose in ('discovery', 'summary', 'exact', 'algorithm-specification'), 'consumer-purpose')
    content = resolve_pointer(view['outcome'], target)
    require(aspects and set(aspects) <= set(reviews.ASPECTS), 'consumer-review-aspects')
    checked_aspects = reviews.ASPECTS if purpose in ('exact', 'algorithm-specification') else aspects
    coverage = scoped(view, target, checked_aspects)
    unknown = [a for (a, checks) in coverage.items() if not checks]
    relevant = affected(view, target)
    warnings = [f for f in relevant if f['status'] == 'unresolved']
    corrections = [f['id'] for f in relevant if any((digest(r['proposed_value']) != digest(resolve_pointer(view['outcome'], f['target'])) for r in f.get('resolutions', [])))]
    needs_qualification = bool(warnings or unknown or corrections)
    algorithm = view['outcome'].get('record', {}).get('kind') == 'algorithm'
    if source_inspection is not None:
        require(set(source_inspection) == {'reviewer', 'reason', 'evidence'}, 'inspection-attestation-fields')
        reviews.provenance(source_inspection['reviewer'])
        require(isinstance(source_inspection['reason'], str) and source_inspection['reason'].strip(), 'inspection-reason')
        inspection_refs = reviews.evidence(view, source_inspection['evidence'])
        require(inspection_refs, 'inspection-evidence-required')
        owners = reviews.owners_for(view, target)
        require(owners and {r['owner'] for r in inspection_refs} <= owners, 'inspection-wrong-source-association')
        if algorithm or purpose == 'algorithm-specification':
            require(any((r['kind'] == 'crop' for r in inspection_refs)), 'algorithm-inspection-requires-crop')
    if qualification is not None:
        require(isinstance(qualification, str) and qualification.strip(), 'explicit-qualification-text')
    strict = purpose in ('exact', 'algorithm-specification')
    require(not strict or not needs_qualification or qualification or source_inspection, 'exact-use-requires-source-inspection-or-explicit-qualification')
    require(purpose != 'algorithm-specification' or source_inspection is not None, 'algorithm-specification-always-requires-source-inspection')
    return dict(element_id=view['element_id'], source_sha256=view['source_sha256'], target=target, content=content, findings=relevant, unresolved_findings=warnings, unreviewed_aspects=unknown, unapplied_correction_findings=corrections, original_unchanged=True, coverage=coverage, scope_review_status='reviewed-scoped-content' if not unknown else 'partially-reviewed' if any(coverage.values()) else 'unreviewed', purpose=purpose, qualification=qualification, source_inspection=source_inspection, use_condition='Original unchanged; retain attributed proposals and inspect source or explicitly qualify affected scope.' if needs_qualification else 'Reviewed only for the named scope/aspects; retain resolution history; not a correctness guarantee.', algorithm_not_default=algorithm, notice=reviews.NOTICE)

def page_view(view, target, *, qualification=None):
    """Ordinary paper claims need material qualifications, not coverage certification."""
    value = exact_view(view, target, purpose='summary', qualification=qualification or None)
    needs = bool(value['unresolved_findings'] or value['unapplied_correction_findings'])
    require(not needs or (isinstance(qualification, str) and qualification.strip()), 'material-finding-requires-qualification')
    return value

def content_targets(outcome):
    """Small semantic targets; full unchanged record stays alongside these."""
    result = []
    for (path, value) in nodes(outcome).items():
        if path.startswith('/record/') and path.rsplit('/', 1)[-1] in ('raw_value', 'text', 'caption_quote', 'units', 'header_hierarchy', 'status', 'unresolved', 'unresolved_symbols'):
            if not any(('/' + key + '/' in path for key in ('source_refs', 'native_spans', 'caption_sources'))):
                result.append(path)
    return result or ['']
