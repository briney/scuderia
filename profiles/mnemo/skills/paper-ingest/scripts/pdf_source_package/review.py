"""Portable source-first review; preserve human rows and append new IDs."""
from pathlib import Path
import csv
import io
import json
from .io import put, save
from .workflow import final_state


def report(root, inspection_dir=None):
    from .review_support import esc, detail, append_review_rows, source_link, crop_card, overlay, logical_cards, request_evidence
    root=Path(root); state=final_state(root, inspection_dir)
    rows=[]; chunks=['<!doctype html><html lang="en"><meta charset="utf-8"><title>PDF source package review</title>',
        '<style>body{font:16px system-ui;margin:24px}img{max-width:100%;display:block}.source{max-height:900px}pre{white-space:pre-wrap}section,.logical-element{border-top:1px solid #bbb;padding:12px}.partial,.warning{border-left:4px solid #b50;padding:12px}figure{margin:12px 0}</style>',
        '<h1>PDF source package review</h1><p>Human acceptance pending. Native text is literal; classifications and associations are model observations. Mechanical completion does not establish exhaustive extraction.</p>',
        '<p><a href="results.json">JSON results</a> | <a href="facts.json">Machine facts</a> | <a href="summary.txt">Factual summary</a> | <a href="candidates.csv">Candidate CSV</a> | <a href="review.csv">Manual review CSV</a> | <a href="review-notes.md">Manual notes</a></p>']
    if state['fixture']: chunks.append('<h2>OFFLINE FIXTURE / HISTORICAL REPLAY. NOT FRESH INFERENCE.</h2>')
    for doc in state['documents']:
        chunks.extend([f'<h2>{esc(doc["identity"])}</h2>',f'<a href="{esc(doc["raw"])}">Full byte-identical original PDF ({doc["page_count"]} physical pages)</a>',
            f'<p>Extraction scope: {esc(doc["extraction_scope"])}; {esc(doc["package_kind"])}. Complete package: {doc["complete_package"]}. Requested work complete: {doc["requested_work_complete"]}.</p>',
            detail('Missing, failed or unattempted requested work',doc['gaps'])])
        scope=doc.get('association_input_scope')
        if scope:
            chunks.append('<h3>Association input image scope</h3><p>Mode: '+esc(scope['mode'])+'. These are input pages, not extraction coverage or a completeness verdict.</p>')
            for label,key in [('Included image pages','included_image_pages'),('Omitted image pages','omitted_image_pages')]:
                chunks.append('<p>'+label+': '+(', '.join(map(str,scope[key])) or 'none')+'</p>')
        else: chunks.append('<p>Association input image scope: no request prepared.</p>')
        chunks.append(logical_cards(doc))
        disp={r['candidate_id']:r for r in doc['logical']['dispositions']}
        for p in doc['pages']:
            candidates=[c for c in doc['candidates'] if c['page']==p['page']]
            annotated=overlay(root,doc,p,candidates)
            if annotated:p['review_overlay']=annotated
            chunks.extend([f'<section id="{esc(doc["identity"])}-p{p["page"]}"><h3>Original physical page {p["page"]}</h3>',source_link(doc,p['page']),
                f'<p>{esc(p["outcomes"])}</p><a href="{esc(p["page_image"])}">Unannotated source image</a>'])
            if annotated:chunks.append(f'<p>Review-only candidate overlay; never sent to the model. <a href="{esc(annotated)}">Open overlay</a></p>')
            display=annotated or p['page_image']
            chunks.append(f'<a href="{esc(display)}"><img loading="lazy" class="source" src="{esc(display)}" alt="Original source page with review-only candidate overlay"></a>')
            for c in candidates:
                disposition=disp[c['id']]
                chunks.append(f'<h4>{esc(c["role"])} / {esc(c["content_type"])}: {esc(disposition["status"])}</h4>')
                for r in c['regions']:chunks.append(crop_card(doc,r))
                chunks.append(detail('Native text and candidate details',dict(candidate=c,disposition=disposition)))
                rows.append(dict(candidate_id=c['id'],document=doc['identity'],physical_page=c['page'],role=c['role'],
                    original_role=c.get('original_role',c['role']),content_type=c['content_type'],
                    label_observations=json.dumps(c['observed_labels'],ensure_ascii=False),disposition=disposition['status'],
                    source_pdf=doc['raw'],crops=';'.join(r['crop'] for r in c['regions']),manual_verdict='',manual_notes=''))
            for request in doc['requests']:
                if request['page']==p['page']:chunks.append(request_evidence(request))
            chunks.append('</section>')
        for request in doc['requests']:
            if request['page'] is None:chunks.append(request_evidence(request))
    fields=['candidate_id','document','physical_page','role','original_role','content_type','label_observations','disposition','source_pdf','crops','manual_verdict','manual_notes']
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    put(root/'candidates.csv',stream.getvalue(),replace=(root/'candidates.csv').exists())
    append_review_rows(root/'review.csv',rows,fields)
    if not (root/'review-notes.md').exists():put(root/'review-notes.md','# Manual source and crop review\n\nNo human verdict is inferred from successful execution.\n')
    save(root/'results.json',state,replace=(root/'results.json').exists())
    from .reporting import factual_summary
    save(root/'facts.json',state['facts'],replace=(root/'facts.json').exists())
    put(root/'summary.txt',factual_summary(state['facts']),replace=(root/'summary.txt').exists())
    put(root/'index.html',''.join(chunks)+'</html>',replace=(root/'index.html').exists())
    return state


def export_summary(root, output, inspection_dir=None):
    """Export newly derived state without touching a historical package."""
    from .io import require
    from .reporting import factual_summary
    root, output = Path(root), Path(output)
    require(root.is_absolute() and output.is_absolute(), 'absolute-paths-required')
    require(not output.resolve().is_relative_to(root.resolve()), 'summary-output-must-be-external')
    require(not any(p.is_symlink() for p in (output, *output.parents)), 'symlink-output-forbidden')
    output.mkdir(mode=0o700)
    try:
        state = final_state(root, inspection_dir)
        save(output/'results.json', state)
        save(output/'facts.json', state['facts'])
        put(output/'summary.txt', factual_summary(state['facts']))
        return state
    except Exception as exc:
        save(output/'failure.json', dict(status='failed', success=False, error_type=type(exc).__name__))
        raise
