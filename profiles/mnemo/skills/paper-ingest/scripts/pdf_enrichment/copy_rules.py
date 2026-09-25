"""Native-copy rules for table cells and algorithm lines.

CODE copies native strings; the model only assigns existing line IDs. Join
rules are explicit and recorded. The model never supplies replacement native
strings (validated: raw_value must be null).
"""
from .io import require


def fragment_line_index(evidence):
    """All native lines supplied in request evidence, keyed by line ID, with owning fragment."""
    index = {}
    for f in evidence.get('body_fragments', []):
        for l in f.get('native_lines', []):
            require(l['line_id'] not in index, 'duplicate-native-line-id:' + str(l['line_id']))
            index[l['line_id']] = dict(text=l['text'], fragment_id=f['fragment_id'], page=l['page'], bbox=l['bbox'],
                                      spans=l.get('spans',[]),span_provenance=l.get('span_provenance'))
    return index


def selected_range(selector, raw, sources, index):
    """Map identity to one copied output interval; never find text by occurrence."""
    require(isinstance(selector,dict) and set(selector) in ({'span_id'},{'piece_index'}), 'native-selector-keys')
    if 'piece_index' in selector:
        n=selector['piece_index']
        require(type(n) is int and 0 <= n < len(sources) and 'line_id' in sources[n], 'native-selector-piece')
        source=sources[n]
        return dict(start=source['output_start'],end=source['output_end'],source=source)
    ident=selector['span_id']
    require(isinstance(ident,str) and ident, 'native-selector-span-id')
    matches=[(lid,span) for lid,line in index.items() for span in line['spans'] if span.get('span_id')==ident]
    require(len(matches)==1, 'native-selector-unknown-or-ambiguous:'+ident)
    lid,span=matches[0]; a,b=span.get('start'),span.get('end')
    text=index[lid]['text']
    if not (type(a) is int and type(b) is int and 0 <= a < b <= len(text) and text[a:b]==span.get('text')):
        return None
    mapped=[]
    for source in sources:
        if source.get('line_id')==lid and source['start'] <= a < b <= source['end']:
            start=source['output_start']+a-source['start']; end=start+b-a
            if raw[start:end]==span['text']:
                mapped.append(dict(start=start,end=end,source=source))
    require(len(mapped)<=1, 'native-selector-ambiguous-output:'+ident)
    return mapped[0] if mapped else None


def join_lines(entries, join_rule='single-space'):
    """Explicit join of native line texts. Never silently changes strings."""
    require(join_rule in ('single-space', 'newline'), 'join-rule')
    texts = [e['text'] for e in entries]
    if join_rule == 'single-space':
        joined = ' '.join(texts)
    else:
        joined = '\n'.join(texts)
    return joined, dict(join_rule=join_rule, source_line_count=len(texts),
                        source_line_ids=[e['line_id'] for e in entries])


def copy_cell_native(cell, index, join_rule='single-space'):
    """Copy exact Unicode substrings, retaining byte offsets and source geometry.

    Offsets address the supplied native line string, not raw PDF stream bytes.
    Whole-line assignments remain supported; they cannot be combined with slices.
    """
    ids = cell.get('native_line_ids', [])
    refs = cell.get('native_refs', [])
    require(not (ids and refs), 'native-lines-or-slices-not-both')
    separator = cell.get('separator', '\n' if join_rule == 'newline' else ' ')
    require(separator in ('', ' ', '\n', '\t'), 'explicit-separator')
    refs = refs or [dict(line_id=lid, start=0, end=len(index[lid]['text']))
                    for lid in ids if lid in index]
    require(not ids or len(refs) == len(ids), 'unknown-native-line-id')
    texts, sources = [], []
    output_offset = 0
    for ref in refs:
        require(isinstance(ref, dict) and set(ref) == {'line_id', 'start', 'end'}, 'native-ref-shape')
        lid, start, end = ref['line_id'], ref['start'], ref['end']
        require(lid in index, 'unknown-native-line-id:' + str(lid))
        line = index[lid]; text = line['text']
        require(type(start) is int and type(end) is int and 0 <= start < end <= len(text), 'native-offset-range')
        texts.append(text[start:end])
        sources.append(dict(ref, fragment_id=line['fragment_id'], page=line['page'], bbox=line['bbox'], native_spans=line['spans'],
                            native_span_provenance=line['span_provenance'],
                            output_start=output_offset, output_end=output_offset+end-start,
                            utf8_start=len(text[:start].encode('utf-8')), utf8_end=len(text[:end].encode('utf-8')),
                            offset_basis='Unicode code points into supplied native line; UTF-8 offsets into that same string'))
        output_offset += end-start+len(separator)
    return dict(raw_value=separator.join(texts) if texts else None, native_line_ids=list(ids),
                native_refs=cell.get('native_refs', []), source_refs=sources,
                join=dict(separator=separator, source_line_count=len(texts)),
                provenance='native-copy:character-slices' if cell.get('native_refs') else 'native-copy:line-granular')
