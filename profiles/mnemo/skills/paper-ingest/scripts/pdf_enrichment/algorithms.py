"""Faithful algorithm/code transcription assembly.

- ordered pseudocode lines with printed line numbers, indentation depth,
  mathematical symbols preserved, trailing comments separate;
- declared input/output fields with source refs;
- unresolved symbols listed, never guessed;
- original apparent typos preserved in text and flagged separately;
- no executable code generation, no semantic repair, no AST.
"""
from .io import require
from . import schema, copy_rules, notation, native_layout


def raster_mathematics(evidence, line, sources):
    """Literal LaTeX source only: never parse, evaluate, compile or fetch anything."""
    body={f['fragment_id']:f for f in evidence.get('body_fragments',[])}
    require(all(s['source_ref'] in body for s in sources), 'latex-body-owner-required')
    require(all(not body[s['source_ref']].get('native_lines') for s in sources), 'latex-native-owner-must-use-copy')
    return notation.literal_mathematics(line['text'],line.get('notation'),sources)


def assemble(evidence, value):
    schema.validate_algorithm(value)
    from .references import image_refs, resolve
    index = copy_rules.fragment_line_index(evidence)
    for item in value['inputs']+value['outputs']:
        require(item['line_refs'], 'algorithm-io-source-refs-required')
        for ref in item['line_refs']: resolve(evidence,ref,item['basis'])
    declaration=value.get('native_layout')
    lines = []
    for sequence, ln in enumerate(value['lines'], 1):
        if declaration and ln['basis']=='native-text':
            lines.append(native_layout.statement(evidence,ln,index,sequence,declaration['version']))
            continue
        require(bool(ln['native_line_ids']) == (ln['basis']=='native-text'), 'algorithm-native-basis-binding')
        entry = dict(sequence=sequence, line_number=ln['line_number'], line_number_printed=ln['line_number_printed'],
                     indent=ln['indent'], text=ln['text'], comment=ln['comment'], basis=ln['basis'])
        if ln['native_line_ids']:
            copied = copy_rules.copy_cell_native(ln, index, join_rule='newline')
            entry.update(native_line_ids=copied['native_line_ids'], text=copied['raw_value'], source_refs=copied['source_refs'],
                         native_text=copied['raw_value'], comment=None, comment_in_native_text=True, join=copied['join'],
                         provenance='native-copy:line-granular')
        else:
            entry.update(native_line_ids=[], native_text=None,source_refs=image_refs(evidence,ln.get('source_refs')),
                         provenance='raster-transcription:crop-image')
        if ln.get('text_format')=='latex':
            entry.update(text_format='latex',provenance='raster-transcription:latex:crop-image',
                         notation=raster_mathematics(evidence,ln,entry['source_refs']))
        else:
            entry['notation']=notation.assemble(evidence,ln.get('notation'),entry['text'],entry['source_refs'],present='notation' in ln)
        entry['indent_basis']='unverified-model-declaration' if ln['native_line_ids'] else 'crop-image-model-transcription'
        lines.append(entry)
    native=any(ln['native_line_ids'] for ln in lines)
    metadata=native_layout.metadata(evidence,declaration,index) if declaration else []
    accounting=native_layout.accounting(index,lines,metadata)
    layout_gaps=[]
    if native and not declaration:
        layout_gaps.append('Legacy native chunks have no statement grouping or crop-attributed indentation declaration.')
    if declaration:
        layout_gaps.extend(declaration['unresolved'])
        if declaration['status']=='unresolved': layout_gaps.append('Model declared native layout unresolved.')
        for ln in lines:
            if ln['basis']=='native-text' and (ln['indent'] is None or ln['grouping']=='unresolved'):
                layout_gaps.append('Statement '+str(ln['sequence'])+': grouping or indentation unresolved.')
    if accounting['missing']: layout_gaps.append('Available native pieces are unassigned; see native_accounting.missing.')
    source_incompleteness=evidence.get('source_incompleteness',dict(document_complete=None,document_gaps=[],element_warnings=[]))
    record = dict(kind='algorithm', element_id=evidence['element_id'], label=evidence.get('label'),
                  source_document=evidence.get('source_document'),source_sha256=evidence.get('source_sha256'),
                  source_incompleteness=source_incompleteness,native_accounting=accounting,native_metadata=metadata,
                  native_layout=declaration,
                  status=value['status'], title=value['title'],
                  inputs=value['inputs'], outputs=value['outputs'], lines=lines,
                  unresolved_symbols=value['unresolved_symbols'], apparent_typos=value['apparent_typos'],
                  fragment_refs=[dict(fragment_id=f['fragment_id'], page=f['page'], crop=f['crop'])
                                 for f in evidence.get('body_fragments', [])],
                  caption_refs=[dict(candidate_id=c['candidate_id'], region_id=c['region_id'], page=c['page'])
                                for c in evidence.get('captions', [])],
                  executable_code_generated=False, scientific_review='pending',
                  layout_status='unresolved' if layout_gaps else ('model-interpreted' if declaration else 'model-transcribed'),layout_gaps=layout_gaps,
                  complete=value['status']=='ok' and not value['unresolved_symbols'] and not layout_gaps and
                           not source_incompleteness.get('element_warnings') and
                           all(ln.get('mathematics_status',ln['notation']['status'])=='resolved' for ln in lines) and
                           all(m['mathematics_status']=='resolved' for m in metadata if m['role']!='excluded'),
                  provenance_note='Literal native strings with separately attributed notation and visual layout. '
                                   'Model-interpreted layout is not independent scientific verification. '
                                   'No semantic repairs, no AST. Original apparent typos preserved and flagged.')
    return record


def render_native_pair(item, *, as_html=False):
    """Both representations remain visible, with separate status and authority."""
    import html
    escape=html.escape if as_html else str
    math=item['math_transcription']
    refs=', '.join(c['source_ref'] for c in math['source_refs'])
    return ('[NATIVE copy; notation-'+escape(item['notation']['status'])+']\n'+escape(item['text'])+
            '\n[MODEL crop transcription; '+escape(math['status'])+'; crops: '+escape(refs)+
            '; literal LaTeX; not independently verified]\n'+escape(math['text'])+
            (('\n[Transcription uncertainty: '+escape('; '.join(math['unresolved']))+']') if math['unresolved'] else ''))


def render_text(record, *, as_html=False):
    """Readable attributed notation; native chunks are not certified statements."""
    import html
    escape=html.escape if as_html else str
    out = ['Scientific review pending.']
    if record.get('layout_status','unresolved')=='unresolved':
        out.append('[layout-unresolved: statement grouping, indentation or native accounting is incomplete]')
    if record.get('native_layout'):
        out.append('[layout-model-interpreted: crop-attributed assignment; not independent source verification]')
    if record.get('source_incompleteness',{}).get('element_warnings'):
        out.append('[source-incomplete: '+escape(str(record['source_incompleteness']['element_warnings']))+']')
    for item in record.get('native_metadata',[]):
        if item['role']=='excluded': continue
        out.append(render_native_pair(item,as_html=as_html) if 'math_transcription' in item else
                   notation.render(item['text'],item.get('notation'),as_html=as_html))
    if record.get('title'):
        out.append(escape(record['title']))
        out.append('')
    for ln in record['lines']:
        rendered=notation.render(ln['text'],ln.get('notation'),as_html=as_html)
        if ln['native_line_ids']:
            if ln.get('layout_version'):
                prefix='    '*ln['indent'] if ln['indent'] is not None else '[indent-unknown] '
                if ln['grouping']=='unresolved': prefix='[grouping-unresolved] '+prefix
                # Printed labels and comments already occur in copied text; never append them.
                if 'math_transcription' in ln:
                    pair=render_native_pair(ln,as_html=as_html)
                    out.append(prefix+pair.replace('\n','\n'+prefix))
                else:
                    out.append(prefix+rendered)
            else:
                out.append(rendered)  # Legacy whitespace is not an indent declaration.
            continue
        num = str(ln['line_number']) if ln['line_number_printed'] else ''
        body = rendered
        if ln.get('comment') and ln['comment'] not in ln['text']:
            body += '  ' + escape(ln['comment'])
        if record.get('native_layout') or ln.get('text_format')=='latex':
            out.append('    '*ln['indent']+(escape(num)+' ' if num else '')+body)
        else:
            body = '    '*ln['indent']+body
            out.append(f'{escape(num):>4}  {body}' if num else f'     {body}')
    for item in record.get('native_metadata',[]):
        if item['role']=='excluded':
            out.append('[excluded native: '+escape(item['reason'])+'] '+escape(item['text']))
    for gap in record.get('native_accounting',{}).get('missing',[]):
        out.append('[unassigned native '+escape(gap['line_id'])+':'+str(gap['start'])+':'+str(gap['end'])+'] '+escape(gap['text']))
    if record.get('apparent_typos'):
        out.append('')
        out.append('Apparent typos preserved (flagged, not repaired):')
        for t in record['apparent_typos']:
            out.append(f'  line {escape(str(t["line_number"]))}: {escape(t["text"])}')
    if record.get('unresolved_symbols'):
        out.append('')
        out.append('Unresolved symbols: ' + escape(', '.join(record['unresolved_symbols'])))
    return '\n'.join(out)


def render_html(record):
    return '<pre>'+render_text(record,as_html=True)+'</pre>'
