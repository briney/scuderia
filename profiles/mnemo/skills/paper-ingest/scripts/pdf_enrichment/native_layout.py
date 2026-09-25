"""Native statement assignment: v2 adds separate crop-attributed mathematics.

No text recognition, syntax/scope inference, or scientific verification. Piece
order and separators are declarations; native inventory order is not reading order.
"""
from .io import require
from . import copy_rules, notation
from .references import image_refs

VERSION = 'native-layout-v2'
LEGACY_VERSION = 'native-layout-v1'


def validate(declaration):
    require(isinstance(declaration,dict) and set(declaration)=={'version','status','unresolved','other'}, 'native-layout-keys')
    require(declaration['version'] in (VERSION,LEGACY_VERSION), 'native-layout-version')
    require(declaration['status'] in ('resolved','unresolved'), 'native-layout-status')
    require(isinstance(declaration['unresolved'],list) and all(isinstance(s,str) and s.strip() for s in declaration['unresolved']), 'native-layout-unresolved')
    require(isinstance(declaration['other'],list), 'native-layout-other')


def validate_statement(line, version=LEGACY_VERSION):
    keys={'basis','pieces','printed_label','indent','grouping','source_refs'}
    optional={'notation','math_transcription'} if version==VERSION else {'notation'}
    require(isinstance(line,dict) and keys <= set(line) <= keys|optional, 'native-statement-keys')
    require(line['basis']=='native-text', 'native-statement-basis')
    require(line['indent'] is None or (type(line['indent']) is int and line['indent'] >= 0), 'native-statement-indent')
    require(line['grouping'] in ('resolved','unresolved'), 'native-statement-grouping')
    label=line['printed_label']
    require(label is None or (isinstance(label,dict) and
            (set(label) in ({'span_id'},{'piece_index'}) or (set(label)=={'start','end'} and
             type(label['start']) is int and type(label['end']) is int and 0 <= label['start'] < label['end']))), 'native-printed-label-range')


def copy_pieces(pieces, index):
    """Use the existing range copier, then shift offsets by explicit per-piece joins."""
    require(isinstance(pieces,list) and pieces, 'native-pieces-required')
    text=''; sources=[]
    for i,piece in enumerate(pieces):
        require(isinstance(piece,dict) and set(piece) in ({'line_id','separator'},{'line_id','start','end','separator'}), 'native-piece-keys')
        separator=piece['separator']
        require(separator in ('',' ','\n','\t') and (i>0 or separator==''), 'native-piece-separator')
        lid=piece['line_id']
        require(isinstance(lid,str) and lid in index, 'unknown-native-line-id:'+str(lid))
        selection={'native_refs':[{k:piece[k] for k in ('line_id','start','end')}]} if 'start' in piece else {'native_line_ids':[lid]}
        copied=copy_rules.copy_cell_native(selection,index)
        text+=separator; offset=len(text)
        for source in copied['source_refs']:
            sources.append(dict(source,output_start=source['output_start']+offset,output_end=source['output_end']+offset,piece_index=i))
        text+=copied['raw_value']
    return dict(text=text,source_refs=sources,pieces=pieces)


def layout_sources(evidence, refs, sources):
    crops=image_refs(evidence,refs)
    require(set(refs)=={s['fragment_id'] for s in sources}, 'layout-crop-must-own-pieces')
    # Retain crop identity and geometry, not a second copy of the entire inventory.
    return [{k:c[k] for k in ('source_ref','fragment_id','page','bbox','crop','crop_sha256') if k in c} for c in crops]


def label_reference(label, copied, index):
    if label is None: return None
    if 'start' not in label:
        mapped=copy_rules.selected_range(label,copied['text'],copied['source_refs'],index)
        require(mapped is not None, 'native-printed-label-unmappable')
        label=dict(start=mapped['start'],end=mapped['end'],selector=label)
    a,b=label['start'],label['end']; refs=[]
    require(b <= len(copied['text']), 'native-printed-label-range')
    for source in copied['source_refs']:
        left,right=max(a,source['output_start']),min(b,source['output_end'])
        if left < right:
            start=source['start']+left-source['output_start']; end=start+right-left
            text=index[source['line_id']]['text']
            refs.append(dict(source,start=start,end=end,output_start=left,output_end=right,
                             utf8_start=len(text[:start].encode()),utf8_end=len(text[:end].encode())))
    require(sum(r['end']-r['start'] for r in refs)==b-a, 'printed-label-must-be-native-not-join')
    return dict(label,text=copied['text'][a:b],source_refs=refs,included_in_text=True)


def mathematical_representation(line, record):
    """Optional crop transcription cannot replace native text or its accounting."""
    record['native_text_status']='copied'
    record['mathematics_status']=record['notation']['status']
    if 'math_transcription' not in line: return record
    value=line['math_transcription']
    require(isinstance(value,dict) and set(value)=={'text','status','unresolved'}, 'native-math-transcription-keys')
    crops=record['layout_source_refs']
    require(crops and all(isinstance(c.get('crop'),str) and c['crop'].strip() for c in crops), 'native-math-source-image-required')
    math=notation.literal_mathematics(value['text'],{k:value[k] for k in ('status','unresolved')},crops)
    record['math_transcription']=dict(math,text=value['text'])
    record['mathematics_status']=math['status']
    return record


def statement(evidence, line, index, sequence, version=LEGACY_VERSION):
    copied=copy_pieces(line['pieces'],index)
    label=label_reference(line['printed_label'],copied,index)
    crops=layout_sources(evidence,line['source_refs'],copied['source_refs'])
    record=dict(copied,sequence=sequence,basis='native-text',native_text=copied['text'],
                native_line_ids=[s['line_id'] for s in copied['source_refs']],
                line_number=label['text'] if label else None,line_number_printed=label is not None,
                printed_label=label,indent=line['indent'],grouping=line['grouping'],
                indent_basis='crop-image-model-interpreted',layout_source_refs=crops,layout_version=version,
                comment=None,comment_in_native_text=True,provenance='native-copy:ordered-pieces',
                notation=notation.assemble(evidence,line.get('notation'),copied['text'],copied['source_refs'],present='notation' in line))
    return mathematical_representation(line,record)


def metadata(evidence, declaration, index):
    records=[]
    for item in declaration['other']:
        keys={'role','pieces','source_refs','reason'}
        optional={'notation','math_transcription'} if declaration['version']==VERSION else {'notation'}
        require(isinstance(item,dict) and keys <= set(item) <= keys|optional, 'native-other-keys')
        require('math_transcription' not in item or item['role'] in ('input','output'), 'native-math-metadata-role')
        require(item['role'] in ('title','input','output','excluded'), 'native-other-role')
        require(isinstance(item['reason'],str) and item['reason'].strip() if item['role']=='excluded' else item['reason'] is None, 'native-other-reason')
        copied=copy_pieces(item['pieces'],index)
        record=dict(copied,role=item['role'],reason=item['reason'],
                    layout_source_refs=layout_sources(evidence,item['source_refs'],copied['source_refs']),
                    basis='native-text',assignment_basis='crop-image-model-interpreted',
                    notation=notation.assemble(evidence,item.get('notation'),copied['text'],copied['source_refs'],present='notation' in item))
        records.append(mathematical_representation(item,record))
    return records


def accounting(index, lines, other):
    """Sorted interval checks per supplied object; no character bitmap or syntax rules."""
    used=[]
    for line in lines:
        label=line.get('printed_label')
        for source in line['source_refs']:
            if 'line_id' not in source: continue
            # The label is a view of already copied text, never a second assignment.
            boundaries={source['output_start'],source['output_end']}
            if label:
                boundaries.update(n for n in (label['start'],label['end']) if source['output_start'] < n < source['output_end'])
            edges=sorted(boundaries)
            for a,b in zip(edges,edges[1:]):
                start=source['start']+a-source['output_start']; end=start+b-a
                role='printed-label' if label and label['start'] <= a < b <= label['end'] else 'statement-body'
                used.append(dict(line_id=source['line_id'],start=start,end=end,role=role,sequence=line['sequence']))
    for number,item in enumerate(other):
        used.extend(dict(line_id=s['line_id'],start=s['start'],end=s['end'],role=item['role'],metadata_index=number) for s in item['source_refs'])
    by_id={lid:[] for lid in index}
    for item in used: by_id[item['line_id']].append(item)
    missing=[]
    for lid,line in index.items():
        cursor=0
        for use in sorted(by_id[lid],key=lambda x:(x['start'],x['end'])):
            require(use['start'] >= cursor, 'overlapping-native-ranges:'+lid)
            if use['start']>cursor: missing.append(dict(line_id=lid,start=cursor,end=use['start']))
            cursor=use['end']
        if cursor<len(line['text']): missing.append(dict(line_id=lid,start=cursor,end=len(line['text'])))
        # Empty native objects still need an explicit disposition; not fabricated text.
        if not line['text'] and not by_id[lid]:
            missing.append(dict(line_id=lid,start=0,end=0))
    for gap in missing:
        line=index[gap['line_id']]
        gap.update(text=line['text'][gap['start']:gap['end']],fragment_id=line['fragment_id'],page=line['page'],bbox=line['bbox'])
    return dict(status='partial' if missing else 'accounted',available_objects=len(index),used=used,missing=missing,
                note='Assignment accounting only; exclusions and layout are model declarations, not independently verified coverage.')
