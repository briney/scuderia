"""Raw PDF preparation and accepted source-only request construction."""
from pathlib import Path
import base64
import copy
import json
import re
import pymupdf as fitz
from . import native, caption, compact, grouped, grouping, classification, association
from .io import ASSETS, SETTINGS, TIMEOUT, LIMIT, require, load, save, put, sha, digest, dumps, safe

CHANNELS = ('caption', 'figure', 'structured', 'classification', 'association')


def context(source, number, count):
    """Original physical prev/current/next images, in accepted render order."""
    parts, images = [], []
    with fitz.open(source) as pdf:
        for n in range(max(1, number - 1), min(count, number + 1) + 1):
            pix = pdf[n - 1].get_pixmap(dpi=150, alpha=False)
            raw = pix.tobytes('png')
            label = f'Page {n}; image {pix.width} x {pix.height} pixels; ' + ('CENTRAL' if n == number else 'context only')
            parts.extend([dict(type='text', text=label), image_part(raw)])
            images.append(dict(page=n, central=n == number, label=label, sha256=digest(raw)))
    return parts, images


def image_part(raw):
    return dict(type='image_url', image_url=dict(url='data:image/png;base64,' + base64.b64encode(raw).decode()))


def caption_request(inv, parts):
    data = dict(coordinate_system=inv['coordinate_system'],
                central_page_native_lines=[{k: line[k] for k in ('id', 'text', 'bbox')} for line in inv['lines']])
    text = (ASSETS / 'caption-prompt.txt').read_text() + f'\nCENTRAL page: {inv["page"]}.\n' + json.dumps(data, ensure_ascii=False)
    return dict(SETTINGS, messages=[dict(role='user', content=[dict(type='text', text=text)] + copy.deepcopy(parts))])


def body_request(inv, parts, channel, mapping=None):
    old = native.make_request(inv, dict(messages=[dict(content=[dict(type='text', text='')] + parts)]))
    old.update(SETTINGS)
    wire, flat, encoded = compact.make_request(inv, old)
    if mapping is None:
        mapping = flat
    else:
        wire, mapping, encoded = grouped.make_request(inv, wire, mapping)
    if channel == 'structured':
        representation = grouped.UNIT_REPRESENTATION if 'units' in mapping else compact.REPRESENTATION
        wire['messages'][0]['content'][0]['text'] = ((ASSETS / 'locator-prompt.txt').read_text() + '\n' +
            representation + compact.SEPARATOR + json.dumps(encoded, ensure_ascii=False, separators=(',', ':'), allow_nan=False))
    return wire, mapping, encoded


def request_row(root, phase, ident, channel, doc, page, wire, inputs, **extra):
    directory = f'requests/{ident}'
    p = safe(root, directory)
    save(p / 'request-wire.json', wire)
    row = dict(id=ident, directory=directory, channel=channel, phase=phase,
               document=doc, page=page, request_sha256=sha(p / 'request-wire.json'),
               inputs=sorted(set(inputs)), status='uncounted', **extra)
    return row


def prepare(scope_path, output, fixture=False):
    root = Path(output).absolute()
    require(not root.exists(), 'output-must-be-new')
    require(fitz.__version__ == '1.28.2', 'pymupdf-version-changed')
    scope = load(scope_path)
    require(scope.get('settings', SETTINGS) in (SETTINGS, dict(model='qwen3.8-27b', temperature=0,
        response_format={'type':'json_object'}, max_tokens=65536, timeout_seconds=1200,
        context_limit=262144, reasoning='omitted/default', retries=0)), 'unsupported-settings')
    endpoint = scope['application_endpoint']
    from urllib.parse import urlsplit
    u = urlsplit(endpoint)
    require(u.scheme in ('http','https') and u.hostname and not u.username and not u.password and not u.query and not u.fragment, 'endpoint-shape')
    require(type(scope['max_application_posts']) is int and scope['max_application_posts'] >= 0, 'post-budget')
    ids = [d['identity'] for d in scope['documents']]
    require(len(ids) == len(set(ids)) and ids, 'unique-documents-required')
    root.mkdir(parents=True)
    if fixture:
        put(root / 'OFFLINE-FIXTURE', 'Never promote replay or synthetic output to live inference.\n')
    save(root / 'scope.json', scope)
    docs, requests = [], []
    for index, item in enumerate(scope['documents'], 1):
        identity = item['identity']
        require(isinstance(identity, str) and identity.strip(), 'document-identity')
        source = Path(item['source'])
        raw = source.read_bytes()
        require(digest(raw) == item['sha256'], 'source-hash-mismatch')
        directory = f'documents/d{index:04d}'
        retained = directory + '/raw/source.pdf'
        put(safe(root, retained), raw)
        with fitz.open(root / retained) as pdf:
            require(pdf.is_pdf and not pdf.needs_pass, 'unsupported-pdf')
            count = len(pdf)
        require(item.get('page_count', count) == count, 'source-page-count')
        pages = item.get('pages', list(range(1, count + 1)))
        require(isinstance(pages, list) and pages and all(type(n) is int and 1 <= n <= count for n in pages)
                and len(pages) == len(set(pages)), 'selected-page-range')
        channels = item.get('channels', list(CHANNELS))
        require(channels and len(channels) == len(set(channels)) and set(channels) <= set(CHANNELS), 'channels')
        require('classification' not in channels or 'structured' in channels, 'classification-needs-structured')
        doc = dict(identity=identity, directory=directory, raw=retained, sha256=digest(raw),
            page_count=count, selected_pages=sorted(pages), channels=channels,
            extraction_scope='whole-document' if len(pages) == count else 'selected-pages',
            package_kind='figure-only-diagnostic' if channels == ['figure'] else 'channel-scoped-package', pages=[])
        for n in range(1, count + 1):
            d = f'{directory}/pages/p{n:04d}'; dest = root / d
            with fitz.open(root / retained) as pdf:
                p = pdf[n - 1]
                ci = caption.inventory(p, identity, n)
                # Adapt only identity metadata, never native lines or geometry.
                ci.update(document=identity, source_document=identity, source_sha256=doc['sha256'])
                text = p.get_text('text')
                metadata = dict(rotation=p.rotation, rotation_matrix=list(p.rotation_matrix),
                    cropbox=list(p.cropbox), mediabox=list(p.mediabox), page_bbox=list(p.rect))
            save(dest / 'caption-inventory.json', ci)
            put(dest / 'native-text.txt', text)
            save(dest / 'native-text.json', ci['lines'])
            inv = None; limitation = None
            try:
                inv = native.inventory(root / retained, n)
                save(dest / 'inventory.json', inv)
                policy = classification.reporting_disposition(inv)
            except (ValueError, AssertionError) as exc:
                limitation = str(exc)
                policy = classification.reporting_disposition(dict(objects=[dict(line, type='native-text-line') for line in ci['lines']]))
                save(dest / 'inventory-failure.json', dict(status='source-limitation', reason=limitation, **metadata))
            with fitz.open(root / retained) as pdf:
                pix = pdf[n - 1].get_pixmap(dpi=150, alpha=False)
                put(dest / 'source-page.png', pix.tobytes('png'))
            page = dict(page=n, directory=d, selected=n in pages, policy=policy,
                source_limitation=limitation, native_text=d + '/native-text.json',
                page_image=d + '/source-page.png', requests={}, **metadata)
            save(dest / 'reporting-policy.json', policy)
            if n in pages and policy['disposition'] != 'policy-excluded':
                parts, images = context(root / retained, n, count)
                save(dest / 'context.json', images)
                # Classification reuses these exact original image parts, never an overlay.
                save(dest / 'original-wire.json', dict(SETTINGS, messages=[dict(role='user',content=[dict(type='text',text='Source context')] + parts)]))
                for channel in channels:
                    if channel not in ('caption','figure','structured'):
                        continue
                    if channel in ('figure', 'structured') and limitation:
                        page['requests'][channel] = dict(status='source-limitation-native-inventory', reason=limitation)
                        continue
                    if channel == 'caption' and not ci['lines']:
                        page['requests'][channel] = dict(status='source-limitation-no-native-text')
                        continue
                    ident = f'd{index:04d}-p{n:04d}-{channel}'
                    inputs = [retained, d + '/caption-inventory.json', d + '/original-wire.json', d + '/reporting-policy.json']
                    if channel == 'caption':
                        wire = caption_request(ci, parts)
                    else:
                        inputs.append(d + '/inventory.json')
                        wire, mapping, encoded = body_request(inv, parts, channel)
                        save(root / 'requests' / ident / 'mapping.json', mapping)
                        save(root / 'requests' / ident / 'encoded-inventory.json', encoded)
                        inputs += [f'requests/{ident}/mapping.json', f'requests/{ident}/encoded-inventory.json']
                    row = request_row(root, 'initial', ident, channel, identity, n, wire, inputs,
                                      page_directory=d, raw=retained, representation='caption-lines' if channel == 'caption' else 'compact-flat')
                    requests.append(row); page['requests'][channel] = dict(id=ident, status='prepared')
            doc['pages'].append(page)
        require(sha(source) == doc['sha256'] == sha(root / retained), 'source-changed-during-prepare')
        save(root / directory / 'document.json', doc)
        docs.append(doc)
        print(json.dumps(dict(phase='prepared-source', document=identity, retained_pages=count, selected_pages=pages)), flush=True)
    require(len(requests) <= scope['max_application_posts'], 'initial-stage-budget-exceeded')
    manifest = dict(schema='pdf-source-package-v1', fixture=bool(fixture), documents=docs,
        settings=SETTINGS, endpoint=endpoint, credential_env=scope.get('credential_env','LITELLM_API_KEY'),
        timeout_seconds=TIMEOUT, context_limit=LIMIT, retries=0, reasoning='omitted/default',
        maximum_posts=scope['max_application_posts'], human_acceptance='pending', exhaustive_extraction_established=False)
    save(root / 'manifest.json', manifest)
    save(root / 'initial-plan.json', dict(phase='initial', requests=requests, dependencies=['manifest.json','scope.json']))
    return manifest


def association_request(root, doc, candidates, pages, all_native=False):
    evidence = dict(source_document=doc['identity'], candidates=[association.wire_candidate(c) for c in candidates],
        visual_context_mode='candidate-page-images-full-native' if all_native else 'whole-document',
        source_physical_pages=[p['page'] for p in pages],
        image_omitted_pages=[p['page'] for p in doc['pages'] if p['page'] not in {x['page'] for x in pages}])
    if all_native:
        evidence['native_page_text'] = [dict(page=p['page'], native_text='\n'.join(l['text'] for l in load(root / p['native_text'])))
            for p in doc['pages'] if p['policy']['disposition'] == 'eligible']
    content = [dict(type='text', text=(ASSETS / 'association-prompt.txt').read_text() + '\nSOURCE EVIDENCE\n' +
                    json.dumps(evidence, ensure_ascii=False, separators=(',', ':'), allow_nan=False))]
    for p in pages:
        content.extend([dict(type='text',text=f'Original source {doc["identity"]}, physical page {p["page"]}'), image_part((root / p['page_image']).read_bytes())])
    return dict(SETTINGS, messages=[dict(role='user',content=content)])
