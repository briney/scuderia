"""Strict response schema validation and decode.

Rejects: wrong shape, extra keys, non-integer positions, negative spans,
invented native strings (model must only assign native_line_ids), undefined
status, unresolved-root masking, truncated output (missing required keys),
and raster text presented as native.
"""
import json
from .io import require

RESPONSE_SCHEMA = 'enrichment-response-v7'

FIGURE_KEYS = {'shown', 'observations', 'caption_context', 'limitations'}
TABLE_KEYS = {'status', 'rows', 'columns', 'cells', 'header_hierarchy', 'units', 'caption_markers', 'unresolved'}
ALGO_KEYS = {'status', 'title', 'inputs', 'outputs', 'lines', 'unresolved_symbols', 'apparent_typos'}

CELL_KEYS = {'row', 'column', 'row_span', 'col_span', 'raw_value', 'native_line_ids', 'raster_text',
             'blank', 'unreadable', 'unresolved', 'notes'}


def _exact(value, keys, what):
    require(isinstance(value, dict), 'root-object:' + what)
    require(set(value) == keys, 'exact-keys:' + what + ':' + str(sorted(set(value) ^ keys)))


def _int(v, what):
    require(type(v) is int and v >= 0, 'nonneg-int:' + what)


def _str_or_none(v, what):
    require(v is None or isinstance(v, str), 'str-or-none:' + what)


def _list(v, what):
    require(isinstance(v, list), 'list:' + what)


def _basis(v, allowed, what):
    require(v in allowed, 'basis:' + what + ':' + str(v))


def parse(text):
    """Strict JSON parse of a model response body (message content)."""
    try:
        from .io import strict
        value = strict(text)
    except json.JSONDecodeError as exc:
        raise ValueError('invalid-json:' + str(exc.msg))
    require(isinstance(value, dict), 'response-root')
    return value


def figure_coverage(value, evidence):
    """Coverage of the supplied variant, never independent visual verification."""
    from .references import claim
    scope = 'caption-only' if evidence.get('caption_only') else 'image-plus-caption'
    coverage = value.get('coverage')
    if coverage is None:
        require('coverage' not in value, 'coverage-object')
        return dict(scope=scope, status='unknown', declared_status=None, source_refs=[],
                    gaps=[], reason='legacy-response-without-coverage-declaration')
    _exact(coverage, {'scope','status','source_refs','gaps'}, 'coverage')
    require(coverage['scope'] == scope, 'coverage-variant')
    require(coverage['status'] in ('complete','partial','unknown'), 'coverage-status')
    refs = coverage['source_refs']
    _list(refs, 'coverage.source_refs')
    require(all(isinstance(r,str) for r in refs) and len(refs)==len(set(refs)), 'coverage-refs')
    supplied = {c['region_id'] for c in evidence.get('captions', [])}
    if not evidence.get('caption_only'):
        supplied.update(f['fragment_id'] for f in evidence.get('body_fragments', []))
    require(set(refs) <= supplied, 'coverage-unknown-ref')
    _list(coverage['gaps'], 'coverage.gaps')
    for gap in coverage['gaps']:
        _exact(gap, {'text','basis','source_ref'}, 'coverage-gap')
        claim(evidence,gap,('crop-image','caption-text','input-scope'))
    missing = sorted(supplied - set(refs))
    status = 'partial' if coverage['gaps'] or missing else coverage['status']
    return dict(coverage, status=status, declared_status=coverage['status'],
                missing_source_refs=missing, scientific_review='pending')


def validate_figure(value, evidence=None):
    from .references import claim
    require(isinstance(value,dict) and FIGURE_KEYS <= set(value) <= FIGURE_KEYS | {'embedded_tables','coverage'}, 'figure-keys')
    require(evidence is not None, 'figure-evidence-required')
    require(isinstance(value['shown'],dict) and isinstance(value['caption_context'],dict), 'figure-claim-maps')
    panels = {}
    for key, group in value['shown'].items():
        items = group if isinstance(group,list) else [group]
        for item in items:
            claim(evidence,item)
            if key == 'panels':
                ident=item.get('id')
                require(isinstance(ident,str) and ident and ident not in panels, 'panel-id')
                panels[ident]=item
    _list(value['observations'],'observations')
    for obs in value['observations']:
        require(isinstance(obs,dict) and {'panel','text','panel_ref','source_ref','evidence_basis'} <= set(obs) <= {'panel','text','panel_ref','source_ref','evidence_basis','caption_quote','caption_ids'}, 'observation-keys')
        claim(evidence,obs)
        panel=obs['panel_ref']
        require(panel is None or panel in panels, 'unknown-panel-ref')
        require(obs['panel'] == panel, 'panel-label-mismatch')
        # A caption and a crop may reference the same panel. Both sources must
        # resolve, but interpretation of the printed panel label needs review.
    for item in value['caption_context'].values():
        claim(evidence,item,('caption-text',))
    _list(value['limitations'],'limitations')
    for item in value['limitations']:
        claim(evidence,item,('crop-image','caption-text','input-scope'))
    _list(value.get('embedded_tables',[]),'embedded_tables')
    if evidence.get('caption_only'):
        require(not value.get('embedded_tables'), 'caption-only-no-embedded-tables')
    figure_coverage(value,evidence)
    return value


def validate_table(value):
    require(isinstance(value,dict), 'root-object:table')
    _exact(value, TABLE_KEYS | (set(value) & {'default_source_ref','notation_coverage'}), 'table')
    if 'notation_coverage' in value:
        coverage=value['notation_coverage']
        _exact(coverage, {'status'}, 'table-notation-coverage')
        require(coverage['status'] in ('all-cells-checked','unresolved','unknown'), 'table-notation-coverage-status')
    _str_or_none(value.get('default_source_ref'), 'table.default_source_ref')
    require(value['status'] in ('ok', 'unresolved'), 'table-status')
    _list(value['rows'], 'rows')
    for r in value['rows']:
        require(isinstance(r, dict) and set(r) == {'index', 'span_from', 'span_to'}, 'row-keys')
        _int(r['index'], 'row.index')
        require(r['span_from'] is None or type(r['span_from']) is int, 'row.span_from')
        require(r['span_to'] is None or type(r['span_to']) is int, 'row.span_to')
    _list(value['columns'], 'columns')
    seen_rows, seen_cols = set(), set()
    for c in value['columns']:
        require(isinstance(c, dict) and set(c) == {'index', 'span_from', 'span_to'}, 'column-keys')
        _int(c['index'], 'column.index')
        require(c['index'] not in seen_cols, 'duplicate-column-index')
        seen_cols.add(c['index'])
    for r in value['rows']:
        require(r['index'] not in seen_rows, 'duplicate-row-index')
        seen_rows.add(r['index'])
    for bands in (value['rows'],value['columns']):
        for band in bands:
            start,end=band['span_from'],band['span_to']
            require((start is None and end is None) or (type(start) is int and type(end) is int and 0 <= start <= end < len(bands)), 'band-span-outside-grid')
    _list(value['cells'], 'cells')
    require(len(value['cells']) <= 100000, 'cell-count-bound')
    for cell in value['cells']:
        require(isinstance(cell, dict) and CELL_KEYS - {'native_line_ids'} <= set(cell) <= CELL_KEYS | {'native_refs', 'separator', 'source_refs', 'notation'}, 'cell-keys')
        require('native_line_ids' in cell or bool(cell.get('native_refs')), 'cell-native-source-branch')
        ids, refs = cell.get('native_line_ids', []), cell.get('native_refs', [])
        _list(ids, 'cell.native_line_ids'); _list(refs, 'cell.native_refs')
        require(not (ids and refs), 'native-lines-or-slices-not-both')
        _int(cell['row'], 'cell.row'); _int(cell['column'], 'cell.column')
        require(type(cell['row_span']) is int and cell['row_span'] >= 1, 'cell.row_span')
        require(type(cell['col_span']) is int and cell['col_span'] >= 1, 'cell.col_span')
        _str_or_none(cell['raster_text'], 'cell.raster_text')
        require(cell['raw_value'] is None, 'cell.raw-value-must-be-null-code-copies')
        for lid in ids:
            require(isinstance(lid, str) or type(lid) is int, 'cell.native_line_id-type')
        for flag in ('blank', 'unreadable', 'unresolved'):
            require(type(cell[flag]) is bool, 'cell.' + flag)
        _str_or_none(cell['notes'], 'cell.notes')
        # Exactly one content disposition per cell (blank/unreadable/unresolved vs bound content).
        flags = (cell['blank'], cell['unreadable'], cell['unresolved'])
        has_content = bool(ids or refs) or cell['raster_text'] is not None
        require(sum(flags) + int(has_content) == 1, 'cell-exactly-one-disposition')
        require(not ((ids or refs) and cell['raster_text'] is not None), 'mixed-cell-use-separate-cells-or-unresolved')
        require(cell['row'] in seen_rows and cell['column'] in seen_cols, 'cell-position-not-in-grid')
    require(0 < len(seen_rows) <= 1000 and 0 < len(seen_cols) <= 1000 and len(seen_rows)*len(seen_cols) <= 100000, 'grid-dimensions-bound')
    require(seen_rows == set(range(len(seen_rows))) and seen_cols == set(range(len(seen_cols))), 'grid-indices-contiguous')
    slots = set()
    for cell in value['cells']:
        require(cell['row'] + cell['row_span'] <= len(seen_rows) and cell['column'] + cell['col_span'] <= len(seen_cols), 'span-outside-grid')
        for r in range(cell['row'], cell['row']+cell['row_span']):
            for c in range(cell['column'], cell['column']+cell['col_span']):
                require((r,c) not in slots, 'duplicate-cell-slot')
                slots.add((r,c))
    require(len(slots) == len(seen_rows)*len(seen_cols), 'grid-gap-not-blank')
    require(isinstance(value['header_hierarchy'], dict), 'header_hierarchy-object')
    _list(value['units'], 'units')
    for u in value['units']:
        require(isinstance(u, dict) and 'basis' in u, 'unit-shape')
        _basis(u.get('basis'), ('native-text', 'caption-text'), 'units.basis')
    _list(value['caption_markers'], 'caption_markers')
    for m in value['caption_markers']:
        require(isinstance(m, dict), 'caption_marker-shape')
        _basis(m.get('basis'), ('native-text', 'caption-text'), 'caption_markers.basis')
    for field in ('units','caption_markers'):
        for item in value[field]:
            if 'caption_ids' not in item: continue  # Legacy model-authored metadata.
            allowed={'basis','source_ref','caption_ids'} | ({'row','column'} if field=='units' else {'role'})
            require(set(item) <= allowed and item['basis']=='caption-text', 'caption-selection-fields')
            if field=='caption_markers':
                require(item.get('role') in ('caption','marker','note'), 'caption-selection-role')
    _list(value['unresolved'], 'unresolved')
    for u in value['unresolved']:
        require(isinstance(u, dict) and set(u) == {'kind', 'ref', 'reason'}, 'unresolved-keys')
        require(u['kind'] in ('cell', 'column', 'row', 'header', 'units'), 'unresolved-kind')
    return value


def validate_algorithm(value):
    from . import native_layout
    require(isinstance(value,dict), 'root-object:algorithm')
    layout='native_layout' in value
    _exact(value, ALGO_KEYS | ({'native_layout'} if layout else set()), 'algorithm')
    if layout:
        native_layout.validate(value['native_layout'])
        # Native metadata uses the same exact-copy path, never replacement prose.
        require(value['title'] is None and value['inputs']==[] and value['outputs']==[], 'native-layout-metadata-use-other')
    require(value['status'] in ('ok', 'unresolved'), 'algorithm-status')
    _str_or_none(value['title'], 'title')
    for field in ('inputs', 'outputs'):
        _list(value[field], field)
        for io in value[field]:
            require(isinstance(io, dict) and set(io) == {'name', 'description', 'line_refs', 'basis'}, 'io-keys')
            require(isinstance(io['name'], str) and io['name'].strip(), 'io-name')
            _str_or_none(io['description'], 'io.description')
            _list(io['line_refs'], 'io.line_refs')
            _basis(io['basis'], ('crop-image', 'native-text', 'caption-text'), 'io.basis')
    _list(value['lines'], 'lines')
    require(value['lines'], 'algorithm-lines-empty')
    numbers = []
    for ln in value['lines']:
        if layout and isinstance(ln,dict) and ln.get('basis')=='native-text':
            native_layout.validate_statement(ln,value['native_layout']['version'])
            continue
        if layout:
            require(isinstance(ln,dict) and ln.get('basis')=='crop-image', 'native-layout-line-basis')
        require(isinstance(ln, dict) and {'line_number', 'line_number_printed', 'indent', 'text',
                                        'comment', 'native_line_ids', 'basis'} <= set(ln) <=
                {'line_number', 'line_number_printed', 'indent', 'text','comment', 'native_line_ids', 'basis','source_refs','notation','text_format'}, 'line-keys')
        if 'text_format' in ln:
            require(ln['text_format']=='latex' and ln['basis']=='crop-image' and ln['native_line_ids']==[], 'latex-raster-only')
        require(ln['line_number'] is None or isinstance(ln['line_number'], str) or type(ln['line_number']) is int, 'printed-line-label')
        require(type(ln['line_number_printed']) is bool, 'line.line_number_printed')
        _int(ln['indent'], 'line.indent')
        require(isinstance(ln['text'], str), 'line.text')
        _str_or_none(ln['comment'], 'line.comment')
        _list(ln['native_line_ids'], 'line.native_line_ids')
        _basis(ln['basis'], ('crop-image', 'native-text'), 'line.basis')
        numbers.append(ln['line_number'])
    # List order is authoritative; printed numbering can restart or repeat.
    _list(value['unresolved_symbols'], 'unresolved_symbols')
    _list(value['apparent_typos'], 'apparent_typos')
    for t in value['apparent_typos']:
        require(isinstance(t, dict) and set(t) == {'line_number', 'text', 'note'}, 'typo-keys')
    return value


VALIDATORS = dict(figure=validate_figure, table=validate_table, algorithm=validate_algorithm)
