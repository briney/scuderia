"""Table assembly: authoritative cell JSON with native-copy vs raster provenance.

- raw strings preserved exactly (007, <0.01, ND, 1.5E-3, ±); no numeric coercion.
- blank vs unreadable vs unresolved stay distinct.
- native cells: code copies strings via native_line_ids + explicit join rules.
- raster cells: model transcription with explicit provenance, never native.
- mixed support without pretending raster cells are native.
- renders HTML/Markdown; CSV only when the grid is rectangular and dense,
  with metadata linking the full structure.
"""
from .io import require
from . import copy_rules, schema, notation


def _metadata(evidence, item):
    """Selection text is authoritative; legacy prose is retained, not verified."""
    from .references import copied_claim, resolve
    if 'caption_ids' in item:
        return copied_claim(evidence,item)
    source={k:item[k] for k in ('basis','source_ref','row','column') if k in item}
    if item['basis']=='caption-text':
        # Copy only the cited ID, never adjacent lines suggested by old prose.
        source.pop('source_ref',None)
        source=copied_claim(evidence,dict(source,caption_ids=[item.get('source_ref')]))
    else:
        resolve(evidence,item.get('source_ref'),item['basis'])
    return dict(source,model_authored=dict(item),text_verification='unverified-legacy-prose')


def assemble(evidence, value):
    """Assemble the authoritative table record from validated response + evidence."""
    schema.validate_table(value)
    index = copy_rules.fragment_line_index(evidence)
    from .references import image_refs
    inherited='default_source_ref' in value
    default=value.get('default_source_ref')
    body_ids={f['fragment_id'] for f in evidence.get('body_fragments',[])}
    if default is not None:
        image_refs(evidence,[default])
        require(default in body_ids, 'table-default-must-be-body')
    anchors = {f"{c['row']},{c['column']}" for c in value['cells']}
    for header, parents in value['header_hierarchy'].items():
        require(header in anchors and isinstance(parents,list) and all(p in anchors and p != header for p in parents), 'header-target-not-cell-anchor')
    remaining={k:set(v) for k,v in value['header_hierarchy'].items()}
    while remaining:
        leaves={k for k,v in remaining.items() if not v.intersection(remaining)}
        require(leaves,'header-cycle')
        remaining={k:v for k,v in remaining.items() if k not in leaves}
    for item in value['units'] + value['caption_markers']:
        if 'column' in item:
            require(type(item['column']) is int and 0 <= item['column'] < len(value['columns']), 'unit-column')
        if 'row' in item:
            require(type(item['row']) is int and 0 <= item['row'] < len(value['rows']), 'unit-row')
    metadata={field:[_metadata(evidence,item) for item in value[field]]
              for field in ('units','caption_markers')}
    cells = []
    shared = {}
    for cell in value['cells']:
        entry = dict(row=cell['row'], column=cell['column'], row_span=cell['row_span'], col_span=cell['col_span'])
        native=bool(cell.get('native_line_ids',[]) or cell.get('native_refs'))
        if inherited:
            refs=cell.get('source_refs')
            if refs is not None:
                entry['source_refs']=image_refs(evidence,refs)
                require(set(refs) <= body_ids, 'table-cell-owner-must-be-body')
                entry['ownership']=dict(basis='explicit-cell',source_refs=refs)
            elif not native:
                require(default is not None or cell['unresolved'], 'table-cell-owner-unresolved')
                refs=[default] if default is not None else []
                entry['source_refs']=image_refs(evidence,refs) if refs else []
                entry['ownership']=dict(basis='table-default' if refs else 'unresolved',source_refs=refs)
        elif cell.get('source_refs') or not native:
            entry['source_refs'] = image_refs(evidence,cell.get('source_refs'))
        if cell['blank']:
            entry.update(status='blank', raw_value='')
        elif cell['unreadable']:
            entry.update(status='unreadable', raw_value=None)
        elif cell['unresolved']:
            entry.update(status='unresolved', raw_value=None)
        elif cell.get('native_line_ids', []) or cell.get('native_refs'):
            copied = copy_rules.copy_cell_native(cell, index)
            for ref in copied['source_refs']:
                ranges=shared.setdefault(ref['line_id'], [])
                require(all(ref['end'] <= a or ref['start'] >= b for a,b in ranges), 'overlapping-native-ranges')
                ranges.append((ref['start'],ref['end']))
            if inherited:
                owners=list(dict.fromkeys(s['fragment_id'] for s in copied['source_refs']))
                require(len(owners)==1 or cell.get('source_refs'), 'table-multifragment-native-owner')
                require('source_refs' not in cell or set(cell['source_refs'])==set(owners), 'table-native-owner-conflict')
                entry['ownership']=dict(basis='selected-native-pieces',source_refs=owners)
            entry.update(status='native', **copied)
        elif cell['raster_text'] is not None:
            entry.update(status='raster', raw_value=cell['raster_text'],
                         provenance='raster-transcription:crop-image')
        else:
            entry.update(status='empty-no-disposition', raw_value=None)
        if cell.get('notes'):
            entry['notes'] = cell['notes']
        if ('notation' not in cell and entry['status'] in ('native','raster','blank') and
                value.get('notation_coverage',{}).get('status')=='all-cells-checked'):
            entry['notation']=dict(status='resolved',runs=[],unresolved=[],scientific_review='pending',
                basis='model-table-coverage',
                derivation='Plain notation inherited from table notation_coverage; no explicit cell declaration.',
                source_fidelity='model-declared-not-independently-verified')
        elif entry['status']=='blank' and 'notation' not in cell:
            entry['notation']=dict(status='resolved',runs=[],unresolved=[],scientific_review='pending')
        else:
            entry['notation']=notation.assemble(evidence,cell.get('notation'),entry['raw_value'],entry['source_refs'],present='notation' in cell)
        cells.append(entry)
    warnings = ['legacy-metadata-text-unverified'] if any(
        'model_authored' in item for group in metadata.values() for item in group) else []
    # Positions must be unique (no duplicate grid slots) apart from explicit spans.
    slots = {}
    for c in cells:
        for r in range(c['row'], c['row'] + c['row_span']):
            for col in range(c['column'], c['column'] + c['col_span']):
                key = (r, col)
                require(key not in slots, 'duplicate-cell-slot:' + str(key))
                slots[key] = c
    record = dict(kind='table', element_id=evidence['element_id'], label=evidence.get('label'),
                  status=value['status'],
                  rows=[{k: r[k] for k in ('index', 'span_from', 'span_to')} for r in value['rows']],
                  columns=[{k: c[k] for k in ('index', 'span_from', 'span_to')} for c in value['columns']],
                  cells=cells, header_hierarchy=value['header_hierarchy'],
                  units=metadata['units'], caption_markers=metadata['caption_markers'],
                  unresolved=value['unresolved'],
                  fragment_refs=[dict(fragment_id=f['fragment_id'], page=f['page'], crop=f['crop'])
                                 for f in evidence.get('body_fragments', [])],
                  caption_refs=[dict(candidate_id=c['candidate_id'], region_id=c['region_id'], page=c['page'])
                                for c in evidence.get('captions', [])],
                  provenance_notes=warnings,
                  content_basis='mixed' if {c['status'] for c in cells} >= {'native','raster'} else
                                'native' if any(c['status']=='native' for c in cells) else 'raster',
                  complete=value['status']=='ok' and not value['unresolved'] and not warnings and
                           all(c['status'] not in ('unreadable','unresolved') and c['notation']['status']=='resolved' for c in cells),
                  scientific_review='pending')
    if 'notation_coverage' in value:
        record['notation_coverage']=dict(value['notation_coverage'])
    return record


def render_markdown(record):
    """HTML is valid Markdown and preserves merged cells without pipe ambiguity."""
    return render_html(record)


def render_html(record):
    import html
    import json
    cells={(c['row'],c['column']):c for c in record['cells']}
    out=['<p>Scientific review pending. Notation roles are source-attributed declarations; raw text is retained separately.</p>']
    if 'notation_coverage' in record:
        out.append('<p>MODEL table notation coverage: '+html.escape(record['notation_coverage']['status'])+
                   '. Inherited plain notation is a model declaration, not geometry proof or independent validation.</p>')
    for field in ('caption_markers','units'):
        for item in record.get(field,[]):
            legacy='model_authored' in item
            if 'caption_quote' in item:
                label='Copied cited caption source' if legacy else 'Copied table '+item.get('role','unit')
                label+=''.join(' ('+axis+' '+str(item[axis])+')' for axis in ('row','column') if axis in item)
                attrs=' data-source-ref="'+html.escape(item['source_ref'])+'"'
                attrs+=' data-caption-ids="'+html.escape(' '.join(item['caption_ids']))+'"'
                out.append('<p>'+html.escape(label)+'</p><pre'+attrs+'>'+html.escape(item['caption_quote'])+'</pre>')
            if legacy:
                out.append('<p>Legacy model-authored metadata (unverified)</p><pre>'+html.escape(
                    json.dumps(item['model_authored'],ensure_ascii=False,indent=2))+'</pre>')
    out.append('<table>')
    for row in record['rows']:
        out.append('<tr>')
        for column in record['columns']:
            c=cells.get((row['index'],column['index']))
            if c is None: continue  # covered by a validated span
            value=c['raw_value'] if c['raw_value'] is not None else '['+c['status']+']'
            rendered=notation.render(value,c.get('notation'),as_html=True)
            ownership=c.get('ownership',{})
            attrs=' data-ownership="'+html.escape(ownership.get('basis','legacy-explicit'))+'"'
            attrs+=' data-source-refs="'+html.escape(' '.join(ownership.get('source_refs',[])))+'"'
            attrs+=' data-notation-basis="'+html.escape(c.get('notation',{}).get('basis','cell-record'))+'"'
            out.append(f'<td rowspan="{c["row_span"]}" colspan="{c["col_span"]}" data-basis="{c["status"]}"'+attrs+'>'+rendered+'</td>')
        out.append('</tr>')
    return ''.join(out)+'</table>'


def rectangular_dense(record):
    """True when every grid slot holds exactly one 1x1 cell with a raw string."""
    rows = sorted(r['index'] for r in record['rows'])
    cols = sorted(c['index'] for c in record['columns'])
    if not rows or not cols:
        return False
    if any(c['row_span'] != 1 or c['col_span'] != 1 for c in record['cells']):
        return False
    slots = {(c['row'], c['column']) for c in record['cells']}
    want = {(r, col) for r in rows for col in cols}
    if slots != want:
        return False
    return all(c['status'] in ('native', 'raster', 'blank') for c in record['cells'])


def export_csv(record):
    """CSV only when meaningful rectangular export applies; metadata links full structure."""
    require(rectangular_dense(record), 'csv-requires-rectangular-dense-grid')
    rows = sorted(r['index'] for r in record['rows'])
    cols = sorted(c['index'] for c in record['columns'])
    grid = {(c['row'], c['column']): c for c in record['cells']}
    import csv
    import io
    stream=io.StringIO(newline='')
    writer=csv.writer(stream)
    for r in rows:
        writer.writerow([grid[(r,col)]['raw_value'] for col in cols])
    return stream.getvalue(), dict(structure=record, formula_execution=False,
        typographically_lossy=any(c.get('notation',{}).get('status')!='resolved' or c.get('notation',{}).get('runs') for c in record['cells']),
        semantically_authoritative_values=False,
        note='Literal raw CSV; typographically lossy for displaced or unverified notation. Not a mathematically authoritative value export. Import as text; spreadsheet applications may interpret formula-like strings. Full structure and attributed notation are retained here.')

