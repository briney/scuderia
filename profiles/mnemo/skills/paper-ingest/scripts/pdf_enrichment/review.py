"""Derived, source-first review. Immutable evidence and human notes are never overwritten."""
from pathlib import Path
import html
import json
import os
from urllib.parse import quote
from .io import load, put, safe


def esc(value):
    return html.escape(str(value)) if value is not None else ''


def pre(value):
    return '<pre>'+esc(json.dumps(value,ensure_ascii=False,indent=2) if isinstance(value,(dict,list)) else value)+'</pre>'


def image(base, crop):
    url=quote(base+'/'+crop,safe='/')
    return '<a href="'+esc(url)+'"><img loading="lazy" src="'+esc(url)+'" alt="Full-resolution source crop"></a>'


def render(destination, plan, outcomes, source_package_root, *, evidence_root=None):
    from . import tables, algorithms
    destination=Path(destination); evidence_root=Path(evidence_root or destination)
    base=os.path.relpath(source_package_root,destination)
    parts=['<!doctype html><html lang="en"><meta charset="utf-8"><title>Enrichment source review</title>',
           '<style>body{font-family:system-ui;margin:2rem}img{max-width:100%}pre{white-space:pre-wrap}td{white-space:pre-wrap;border:1px solid #999;padding:.3em}section{border-top:2px solid #888;margin-top:2rem}.warning{background:#fff0c0}</style>',
           '<h1>Enrichment source review</h1><p>Scientific validation and human acceptance pending. Reference validity is not scientific accuracy. Production completion is not established.</p>']
    if plan['fixture']:
        parts.append('<p class="warning">SYNTHETIC TEST RESPONSE run: NOT SCIENTIFIC OUTPUT, cannot be live-promoted.</p>')
    for doc in plan['documents']:
        parts.append('<h2>Source document: '+esc(doc['identity'])+'</h2>')
        parts.append('<p>Source disposition: '+esc(doc['source_status'])+'; extraction scope: '+esc(doc['extraction_scope'])+'</p>')
        parts.append('<a href="'+esc(quote(base+'/'+doc['raw'],safe='/'))+'">Original full PDF</a>')
        parts.append(pre({k:v for k,v in doc.items() if k in ('gaps','logical_dispositions','channels','candidate_count')}))
        for row in plan['requests']:
            if row['document']!=doc['identity']: continue
            result=outcomes.get(row.get('id'),{}); record=result.get('record')
            parts.append('<section><h3>'+esc(row.get('label') or row['element_id'])+'</h3><p>Status: '+esc(result.get('status',row['status']))+'</p>')
            if row.get('directory'):
                ev=load(safe(evidence_root,row['directory'])/'source-evidence.json')
                if row['caption_only']: parts.append('<p>CAPTION-ONLY VARIANT; no body text or images supplied to the model.</p>')
                for fragment in ev.get('body_fragments',[]):
                    parts.append('<p>Source body, physical page '+esc(fragment['page'])+'</p>'+image(base,fragment['crop']))
                for caption in ev.get('captions',[]):
                    parts.append('<p>Associated caption/note, physical page '+esc(caption['page'])+'</p>'+image(base,caption['crop'])+pre(caption['native_text']))
            parts.append(pre({k:v for k,v in result.items() if k!='record'} if result else 'No attempt recorded; pending work is not success.'))
            if row.get('coverage_warnings'): parts.append(pre(row['coverage_warnings']))
            if record:
                parts.append('<h4>Generated output ('+esc(record['kind'])+')</h4>')
                if record['kind']=='table': parts.append(tables.render_html(record))
                elif record['kind']=='algorithm': parts.append(algorithms.render_html(record))
                else:
                    parts.append('<h4>Input-variant coverage (scientific review pending)</h4>'+pre(record.get('coverage',{'status':'unknown'})))
                    for field in ('shown','observations','caption_context','limitations'):
                        parts.append('<h4>'+field+'</h4>'+pre(record[field]))
                        group=record[field].values() if isinstance(record[field],dict) else record[field]
                        for item in group:
                            for claim in (item if isinstance(item,list) else [item]):
                                if 'caption_quote' in claim:
                                    parts.append('<p>Copied caption evidence ('+esc(claim['source_ref'])+')</p>'+pre(claim['caption_quote']))
                    for child in record.get('embedded_tables',[]):
                        parts.append('<h4>Embedded table '+esc(child['child_id'])+'</h4>'+tables.render_html(child))
                parts.append('<details><summary>Authoritative record and provenance</summary>'+pre(record)+'</details>')
            parts.append('</section>')
    parts.append('</html>')
    put(destination/'review.html',''.join(parts),replace=True)
