"""Static review helpers. No rendered annotation is a model input."""
from pathlib import Path
import base64
import csv
import html
import io
import json
import pymupdf as fitz
from .io import put, require
from . import native


def esc(value):
    return html.escape(str(value), quote=True)


def detail(title, value):
    return '<details><summary>'+esc(title)+'</summary><pre>'+esc(json.dumps(value, ensure_ascii=False, indent=2))+'</pre></details>'


def append_review_rows(path, rows, fields):
    """Retain original bytes as a prefix; append only previously unseen IDs."""
    path=Path(path); old=path.read_bytes() if path.exists() else None
    if old is None:
        existing=set(); columns=fields
    else:
        reader=csv.DictReader(io.StringIO(old.decode('utf-8-sig'), newline=''), strict=True)
        columns=reader.fieldnames
        require(columns and 'candidate_id' in columns and len(columns)==len(set(columns)), 'review-csv-header-invalid')
        existing={r['candidate_id'] for r in reader}
    additions=[]
    for row in rows:
        if row['candidate_id'] not in existing:
            additions.append(row); existing.add(row['candidate_id'])
    if old is not None and not additions:
        return
    stream=io.StringIO(newline=''); writer=csv.DictWriter(stream,fieldnames=columns,extrasaction='ignore')
    if old is None: writer.writeheader()
    writer.writerows(additions)
    prefix=old or b''
    if prefix and not prefix.endswith((b'\n',b'\r')): prefix+=b'\r\n'
    # Fail rather than overwrite an intervening human edit.
    require(old is None and not path.exists() or old is not None and path.read_bytes()==old, 'review-csv-changed-during-report')
    put(path,prefix+stream.getvalue().encode(),replace=old is not None)


def source_link(doc, number):
    return f'<a href="{esc(doc["raw"])}#page={number}">Source page {number}</a>'


def crop_card(doc, region):
    return ('<figure>'+source_link(doc,region['page'])+
        f'<a href="{esc(region["crop"])}"><img loading="lazy" src="{esc(region["crop"])}" alt="Original PDF selected-region crop"></a></figure>')


def overlay(root, doc, page, candidates):
    if not candidates: return None
    # Use retained source metadata. Older prepared packages can be read without
    # assuming a rotation: consult their byte-identical raw source once here.
    if 'rotation_matrix' in page:
        matrix=fitz.Matrix(*page['rotation_matrix']); box=page['page_bbox']
    else:
        with fitz.open(root/doc['raw']) as pdf:
            source=pdf[page['page']-1];matrix=source.rotation_matrix;box=list(source.rect)
    w,h=box[2]-box[0],box[3]-box[1]
    raw=base64.b64encode((root/page['page_image']).read_bytes()).decode()
    chunks=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box[0]} {box[1]} {w} {h}">',
        '<title>Review-only native candidate overlay on original source page</title>',
        f'<image x="{box[0]}" y="{box[1]}" width="{w}" height="{h}" href="data:image/png;base64,{raw}"/>']
    for c in candidates:
        color={'body':'#c00000','caption':'#0044cc','note':'#008040'}[c['role']]
        for region in c['regions']:
            require(region['coordinate_system'] in (native.COORD,'top-left origin; unrotated PDF points'),'unknown-review-coordinate-system')
            b=fitz.Rect(region['bbox'])*matrix
            chunks.append(f'<rect x="{b.x0}" y="{b.y0}" width="{b.width}" height="{b.height}" fill="none" stroke="{color}" stroke-width="1"><title>{esc(c["role"]+": "+c["id"])}</title></rect>')
    chunks.append('</svg>');path=Path(page['page_image']).with_name('review-overlay.svg')
    put(root/path,''.join(chunks),replace=(root/path).exists())
    return str(path)


def logical_cards(doc):
    chunks=['<h3>Document-level logical groups</h3>'];known={c['id']:c for c in doc['candidates']}
    for element in doc['logical']['elements']:
        chunks.append('<article class="logical-element"><h4>'+esc(element['label'] if element['label'] is not None else 'Unlabeled group')+' / '+esc(element['content_type'])+'</h4>')
        for role,title in [('body','Body members'),('caption','Caption members'),('note','Note members')]:
            refs=[i for i in element['body_refs']+element['caption_note_refs'] if known[i]['role']==role]
            chunks.append('<h5>'+title+'</h5>')
            if not refs: chunks.append('<p>None associated.</p>')
            for i in refs:
                c=known[i]
                for r in c['regions']:chunks.append(crop_card(doc,r))
                chunks.append(detail('Native text and candidate details',dict(candidate_id=i,role=role,native_text=c['native_text'],observed_labels=c['observed_labels'])))
        for warning in element.get('coverage_warnings',[]):chunks.append('<p class="warning">'+esc(warning['message'])+'</p>')
        chunks.append(detail('Logical group reference details',element));chunks.append('</article>')
    if not doc['logical']['elements']: chunks.append('<p>No validated logical groups are available.</p>')
    chunks.append(detail('All candidate dispositions and conflicts',doc['logical']))
    return ''.join(chunks)


def request_evidence(request):
    chunks=[]
    if request.get('partial_crops'):
        chunks.append('<aside class="partial"><h4>Partial/unvalidated diagnostic</h4><p>'+str(request['partial_crop_count'])+' actual crop PNG(s); overview images excluded. These files are not completed candidates or validated logical groups.</p>')
        for name in request['partial_crops']:
            chunks.append(f'<a href="{esc(name)}"><img loading="lazy" src="{esc(name)}" alt="Partial/unvalidated source-derived crop"></a>')
        chunks.append('</aside>')
    chunks.append('<details><summary>'+esc(request['channel'])+' request, raw response and export evidence</summary>')
    chunks.append('<pre>'+esc(json.dumps({k:v for k,v in request.items() if k!='files'},indent=2))+'</pre>')
    for name in request['files']:chunks.append(f'<p><a href="{esc(name)}">{esc(Path(name).name)}</a></p>')
    chunks.append('</details>');return ''.join(chunks)
