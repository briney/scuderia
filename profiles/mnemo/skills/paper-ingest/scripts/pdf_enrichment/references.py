"""Resolve only references present in this request, never inferred source IDs."""
from .io import require
from .copy_rules import fragment_line_index


def resolve(evidence, ref, basis):
    require(isinstance(ref, str) and bool(ref), 'source-ref-required')
    bodies = {f['fragment_id']: f for f in evidence.get('body_fragments', [])}
    captions = {c['region_id']: c for c in evidence.get('captions', [])}
    if basis == 'crop-image':
        require(not evidence.get('caption_only'), 'caption-only-has-no-images')
        require(ref in bodies or ref in captions, 'unknown-image-ref:' + ref)
        return (bodies | captions)[ref]
    if basis == 'caption-text':
        require(ref in captions, 'unknown-caption-ref:' + ref)
        return captions[ref]
    if basis == 'native-text':
        index = fragment_line_index(evidence)
        require(ref in index, 'unknown-native-ref:' + ref)
        return index[ref]
    if basis == 'input-scope':
        require(ref == evidence['element_id'], 'unknown-input-scope-ref')
        return {'element_id':ref}
    raise ValueError('unknown-evidence-basis:' + str(basis))


def claim(evidence, value, allowed=('crop-image','caption-text')):
    require(isinstance(value, dict), 'claim-object')
    basis = value.get('basis', value.get('evidence_basis'))
    require(basis in allowed, 'claim-basis')
    text = value.get('text')
    require(isinstance(text, str) and text.strip(), 'claim-text')
    source = resolve(evidence, value.get('source_ref'), basis)
    if 'caption_ids' in value:
        require(basis == 'caption-text' and 'caption_quote' not in value, 'caption-selection-competing-content')
        caption_selection(evidence, value['source_ref'], value['caption_ids'])
    if 'caption_quote' in value:
        quote = value['caption_quote']
        require(basis == 'caption-text' and isinstance(quote,str) and quote and quote in source['native_text'], 'caption-quote-not-literal')
    return source


def caption_selection(evidence, owner, ids):
    """Copy supplied IDs only. Region-only evidence never gains line geometry."""
    require(isinstance(ids,list) and ids and all(isinstance(i,str) for i in ids)
            and len(ids)==len(set(ids)), 'caption-selection-ids')
    index={}
    for cap in evidence.get('captions',[]):
        base={k:cap[k] for k in ('candidate_id','region_id','page','bbox','crop','crop_sha256','native_text_scope') if k in cap}
        def add(ident, text, scope, **extra):
            index.setdefault(ident,[]).append(dict(base,selection_id=ident,text=text,scope=scope,**extra))
        add(cap['region_id'],cap['native_text'],'region',geometry_scope='region')
        for line in cap.get('lines',[]):
            add(line['line_id'],line['text'],'line',line_id=line['line_id'],bbox=line.get('bbox',cap['bbox']),
                geometry_scope='line' if 'bbox' in line else 'region')
            for span in line.get('spans',[]):
                a,b=span.get('start'),span.get('end')
                if type(a) is int and type(b) is int and 0 <= a < b <= len(line['text']) and line['text'][a:b]==span['text']:
                    add(span['span_id'],span['text'],'span',line_id=line['line_id'],start=a,end=b,
                        bbox=span.get('bbox',line.get('bbox',cap['bbox'])),
                        geometry_scope='span' if 'bbox' in span else 'line' if 'bbox' in line else 'region')
                else:
                    # An inexact span is unselectable, but its ID still exists.
                    index.setdefault(span['span_id'],[]).append(None)
    selected=[]
    for ident in ids:
        matches=index.get(ident,[])
        require(len(matches)==1 and matches[0] is not None, 'caption-selection-unknown-or-ambiguous:'+ident)
        region=matches[0]['region_id']
        require(len(index.get(region,[]))==1, 'caption-selection-ambiguous-owner:'+region)
        require(owner is None or region==owner, 'caption-selection-wrong-owner:'+ident)
        selected.append(matches[0])
    require(len({s['region_id'] for s in selected})==1, 'caption-selection-multiple-owners')
    return selected


def copied_claim(evidence, value):
    if 'caption_ids' not in value: return value
    if 'source_ref' in value:
        require(isinstance(value['source_ref'],str) and bool(value['source_ref']), 'caption-selection-owner')
    sources=caption_selection(evidence,value.get('source_ref'),value['caption_ids'])
    return dict(value,source_ref=sources[0]['region_id'],caption_quote='\n'.join(s['text'] for s in sources),caption_sources=sources,
                caption_join=dict(separator='\n',basis='explicit-display-separator-between-selected-excerpts'),
                caption_provenance='code-copy:selected-caption-ids')


def image_refs(evidence, refs):
    require(isinstance(refs,list) and refs and len(refs)==len(set(refs)), 'image-source-refs-required')
    return [dict(source_ref=r, **resolve(evidence,r,'crop-image')) for r in refs]
