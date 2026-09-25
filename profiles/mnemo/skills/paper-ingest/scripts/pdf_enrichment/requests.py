"""Enrichment request construction and run preparation.

prepare --source-package SAVED --output NEW_RUN --kinds figure,table,algorithm

Binds (all recorded in the run manifest for independent regeneration):
  - source package root + its tree hash at preparation time,
  - document identity + raw sha256 per element,
  - element ID, candidate refs, fragments/pages, labels,
  - request payloads (prompt + crop images + native line evidence),
  - prompt/model/request settings,
  - synthetic-test-response import path for the offline vertical slice.

Never sends requests. Explicitly gated live execution is in live.py; counting,
sealing and parent approval are separate operations.
"""
from pathlib import Path
import base64
import copy
import json
from .io import require, save, put, safe, sha, digest, dumps, load, tree_hash, now_utc, STAGE
from . import package_io, prompts
from .prompts import FIGURE_PROMPT, TABLE_PROMPT, ALGORITHM_PROMPT, FIGURE_PROMPT_CAPTION_ONLY

MODEL = 'qwen3.8-27b'
SETTINGS = dict(model=MODEL, temperature=0,
                response_format={'type': 'json_object'}, max_tokens=65536)
KINDS = ('figure', 'table', 'algorithm')
PROMPTS = dict(figure=FIGURE_PROMPT, table=TABLE_PROMPT, algorithm=ALGORITHM_PROMPT)


def image_part(raw):
    return dict(type='image_url', image_url=dict(url='data:image/png;base64,' + base64.b64encode(raw).decode()))


def native_line(line, page):
    text=line['text']; spans=copy.deepcopy(line.get('spans',[]))
    exact=bool(spans) and ''.join(s['text'] for s in spans)==text
    offset=0
    for number,span in enumerate(spans):
        span['span_id']=str(line['id'])+'::span:'+str(number)
        span['start']=offset if exact else None
        offset+=len(span['text'])
        span['end']=offset if exact else None
    return dict(line_id=line['id'],page=line.get('page',page),bbox=line['bbox'],text=text,
                spans=spans,span_offsets_exact=exact,character_offset_basis='zero-based Unicode code points; end exclusive')


def fragment_evidence(pkg, doc, element, with_native_lines=True):
    """Body fragments with crops (+ literal native line evidence)."""
    body_ids = set(element['body_refs'])
    out = []
    for f in element['ordered_source_fragments']:
        if f['candidate_id'] not in body_ids:
            continue
        entry = dict(fragment_id=f['id'], page=f['page'], bbox=f['bbox'], crop=f['crop'],
                     crop_sha256=f.get('crop_sha256'))
        if with_native_lines:
            lines = f.get('lines') or [m for m in f.get('source_members',[]) if m.get('type')=='native-text-line']
            native=[]
            for line in lines:
                # Some retained fragments have lean lines AND richer source members.
                # Copy metadata only; never change selected strings, geometry or IDs.
                matches=[m for m in f.get('source_members',[]) if m.get('type')=='native-text-line' and
                         m.get('spans') and all(m.get(k)==line.get(k) for k in ('id','text','page','bbox'))]
                if not line.get('spans') and matches:
                    require(all(m['spans']==matches[0]['spans'] for m in matches), 'ambiguous-retained-spans')
                    saved=native_line(dict(line,spans=matches[0]['spans']),f['page'])
                    saved['span_provenance']=dict(basis='retained-source-member',fragment_id=f['id'],
                                                  candidate_id=f['candidate_id'],member_id=line['id'],
                                                  match_fields=['id','text','page','bbox'])
                else:
                    saved=native_line(line,f['page'])
                native.append(saved)
            entry['native_lines'] = native
        out.append(entry)
    return out


def caption_evidence(pkg, doc, element):
    """Caption + note fragments (native text, crops, line IDs) of an element."""
    out = []
    for ref in element['caption_note_refs']:
        c = pkg.candidate(doc['identity'], ref)
        for r in c['regions']:
            out.append(dict(candidate_id=ref, region_id=r['id'], page=r['page'], bbox=r['bbox'],
                            crop=r['crop'], crop_sha256=r.get('crop_sha256'),
                            native_text='\n'.join(l['text'] for l in r['lines']) if r.get('lines') else c.get('native_text', ''),
                            native_text_scope='region-lines' if r.get('lines') else 'candidate-text',
                            lines=[native_line(l,r['page']) for l in (r.get('lines') or [])]))
    return out


def _base_evidence(pkg, doc, element, extra=None):
    evidence = dict(element_id=element['id'], source_document=doc['identity'], source_sha256=doc['sha256'],
                    label=element.get('label'),
                    body_fragments=fragment_evidence(pkg, doc, element),
                    captions=caption_evidence(pkg, doc, element))
    if extra:
        evidence.update(extra)
    return evidence


def _attach_images(content, pkg, body_frags, caps, kind_label):
    for f in body_frags:
        content.append(dict(type='text', text=f'{kind_label} body fragment {f["fragment_id"]} (page {f["page"]}, full resolution)'))
        content.append(image_part(safe(pkg.root, f['crop']).read_bytes()))
    for c in caps:
        content.append(dict(type='text', text=f'Associated caption fragment {c["region_id"]} (page {c["page"]})'))
        content.append(image_part(safe(pkg.root, c['crop']).read_bytes()))


def figure_request(pkg, doc, element, caption_only=False):
    """Figure request: ordered full-resolution crop fragments + caption + regional native text."""
    evidence = _base_evidence(pkg, doc, element)
    evidence['caption_only'] = bool(caption_only)
    if caption_only:
        evidence['body_fragments'] = []
        text = FIGURE_PROMPT_CAPTION_ONLY + '\nSOURCE EVIDENCE (caption only; no images supplied)\n' + \
            json.dumps(evidence, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
        return dict(SETTINGS, messages=[dict(role='user', content=[dict(type='text', text=text)])]), evidence
    content = [dict(type='text', text=FIGURE_PROMPT + '\nSOURCE EVIDENCE\n' +
                    json.dumps(evidence, ensure_ascii=False, separators=(',', ':'), allow_nan=False))]
    _attach_images(content, pkg, evidence['body_fragments'], evidence['captions'], 'Figure')
    return dict(SETTINGS, messages=[dict(role='user', content=content)]), evidence


def table_request(pkg, doc, element):
    """Table crops with retained spans and source-bound sub-line selection."""
    extra = dict(binding_granularity='native-line-or-character-slice',
                 binding_note='Saved spans are retained; when exact span-to-line concatenation holds, deterministic span offsets are supplied. Otherwise select exact source-bound character offsets without changing the extractor.')
    evidence = _base_evidence(pkg, doc, element, extra)
    content = [dict(type='text', text=TABLE_PROMPT + '\nSOURCE EVIDENCE\n' +
                    json.dumps(evidence, ensure_ascii=False, separators=(',', ':'), allow_nan=False))]
    _attach_images(content, pkg, evidence['body_fragments'], evidence['captions'], 'Table')
    return dict(SETTINGS, messages=[dict(role='user', content=content)]), evidence


def algorithm_request(pkg, doc, element):
    """Algorithm/code request: retained evidence, with source scope separate from layout."""
    evidence = _base_evidence(pkg, doc, element, dict(source_incompleteness=dict(
        document_complete=doc.get('source_complete'),document_gaps=doc.get('gaps',[]),
        element_warnings=element.get('coverage_warnings',[]))))
    content = [dict(type='text', text=ALGORITHM_PROMPT + '\nSOURCE EVIDENCE\n' +
                    json.dumps(evidence, ensure_ascii=False, separators=(',', ':'), allow_nan=False))]
    _attach_images(content, pkg, evidence['body_fragments'], evidence['captions'], 'Algorithm')
    return dict(SETTINGS, messages=[dict(role='user', content=content)]), evidence


def build_request(pkg, doc, element, kind, caption_only=False):
    require(kind in KINDS, 'kind')
    if kind == 'figure':
        return figure_request(pkg, doc, element, caption_only=caption_only)
    if kind == 'table':
        return table_request(pkg, doc, element)
    return algorithm_request(pkg, doc, element)


def prepare(source_package, output, kinds=None, caption_only=False, *, element_ids=None,
            method=None, fixture=True):
    """Prepare immutable exact payloads; explicit IDs are required for live runs."""
    from . import trusted, schema
    root = Path(output).absolute()
    source = Path(source_package).absolute()
    require(not root.resolve().is_relative_to(source.resolve()), 'output-inside-source-forbidden')
    require(not root.exists(), 'output-must-be-new')
    safe(root, 'enrichment-plan.json')
    kinds = list(kinds) if kinds else list(KINDS)
    require(kinds and all(k in KINDS for k in kinds) and len(kinds) == len(set(kinds)), 'kinds')
    require(type(fixture) is bool, 'fixture-boolean')
    require(fixture or element_ids, 'live-prepare-explicit-element-ids-required')
    if element_ids is not None:
        require(isinstance(element_ids,list) and element_ids and len(element_ids)==len(set(element_ids)), 'selection-unique-nonempty')
    pkg = package_io.SourcePackage(source,method=method)
    eligible=pkg.eligible_elements(kinds)
    ids=[r['element_id'] for r in eligible]
    require(len(ids)==len(set(ids)), 'duplicate-element-id')
    require(element_ids is None or set(element_ids) <= set(ids), 'unknown-selected-element')
    selected=set(ids if element_ids is None else element_ids)
    require(all(r['kind'] for r in eligible if r['element_id'] in selected) if element_ids else True, 'selected-element-ineligible')
    root.mkdir(parents=True)
    rows=[]
    for row in eligible:
        e=row['element']; ident=f'e{len(rows)+1:04d}-{row["kind"] or "skip"}'
        base=dict(element_id=row['element_id'],document=row['document'],kind=row['kind'],pages=row['pages'],content_type=row['content_type'],
                  label=row['label'],coverage_warnings=e.get('coverage_warnings',[]))
        if row['kind'] is None or row['element_id'] not in selected:
            reason=row['reason'] if row['reason'] in ('unknown-type','not-selected') else 'source-incomplete'
            if row['kind'] is not None and row['element_id'] not in selected: reason='not-selected'
            rows.append(dict(base,kind=None,status=reason))
            continue
        doc=pkg.doc(row['document'])
        require(fixture or not doc['source_fixture'],'fixture-source-cannot-be-live-promoted')
        wire,evidence=build_request(pkg,doc,e,row['kind'],caption_only=caption_only)
        prompt=FIGURE_PROMPT_CAPTION_ONLY if caption_only and row['kind']=='figure' else PROMPTS[row['kind']]
        directory='requests/'+ident; p=safe(root,directory)
        save(p/'request-wire.json',wire); save(p/'source-evidence.json',evidence); put(p/'prompt.txt',prompt)
        rows.append(dict(base,id=ident,status='prepared-not-sent',directory=directory,
                         request_sha256=sha(p/'request-wire.json'),evidence_sha256=sha(p/'source-evidence.json'),
                         element_sha256=digest(dumps(e)),source_sha256=doc['sha256'],
                         source_package_tree_sha256=pkg.snapshot['tree_sha256'],
                         prompt_sha256=sha(p/'prompt.txt'),prompt_version=prompts.PROMPT_VERSION,response_schema=schema.RESPONSE_SCHEMA,
                         model=MODEL,settings=copy.deepcopy(SETTINGS),
                         caption_only=bool(caption_only and row['kind']=='figure')))
    documents=[{k:v for k,v in d.items() if k not in ('elements','pages')} for d in pkg.documents]
    manifest=dict(schema=STAGE,stage='enrichment-prepare-v7',prompt_version=prompts.PROMPT_VERSION,
                  response_schema=schema.RESPONSE_SCHEMA,prepared_at=now_utc(),
                  source_package=dict(root=str(pkg.root),tree_sha256=pkg.snapshot['tree_sha256'],
                                      file_count=pkg.snapshot['file_count'],schema=pkg.schema,historical=pkg.historical),
                  documents=documents,kinds=kinds,selection=element_ids,caption_only_variant=bool(caption_only),
                  settings=SETTINGS,model=MODEL,requests=rows,fixture=fixture,
                  method=dict(root=str(pkg.method),code=trusted.method_hashes(pkg.method)),
                  code=trusted.code_hashes(),human_acceptance='pending',production_approved=False)
    save(root/'enrichment-plan.json',manifest)
    put(root/'plan.sha256',sha(root/'enrichment-plan.json'))
    if fixture: put(root/'OFFLINE-FIXTURE','Synthetic-only; this run cannot be live-promoted.\n')
    return manifest
