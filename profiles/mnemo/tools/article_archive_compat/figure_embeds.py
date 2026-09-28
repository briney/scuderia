"""Historical read-only dependency closure; extracted without changing validation contracts."""
import hashlib
import json
import re
from urllib.parse import unquote
from article_archive_compat import portable_articles as pa
from article_archive_compat.article_runtime import absolute, require
PATTERN = re.compile('<!-- paper-figure (\\{[^\\n]*\\}) -->\\n([\\s\\S]*?)<!-- /paper-figure -->\\n')

def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()

def blocks(text):
    matches = list(PATTERN.finditer(text))
    require(text.count('<!-- paper-figure ') == len(matches) and text.count('<!-- /paper-figure -->') == len(matches), 'malformed-figure-block')
    values = [(json.loads(m[1]), m[2]) for m in matches]
    require(len({v[0]['element_id'] for v in values}) == len(values), 'duplicate-figure-block')
    for (metadata, body) in values:
        require(metadata['sha256'] == digest(body), 'figure-block-edited: reconcile manual edits before regenerating')
    return values

def role(element, manifest):
    value = next((d.get('source_role') for d in manifest['documents'] if d['identity'] == element['document']))
    require(value in ('manuscript', 'supplement'), 'figure-source-role-unresolved')
    return value

def verify(text, manifest, page, *, image_root=None, require_local=True):
    from article_archive_compat import final_products as fp
    m = fp.verify(manifest)
    (_, paths) = pa.verify_local(manifest)
    image_root = absolute(image_root or absolute(manifest).parent)
    index = {e['element_id']: e for e in m['elements']}
    values = blocks(text)
    required = {e['element_id'] for e in m['elements'] if e['kind'] == 'figure' and role(e, m) == 'manuscript'}
    present = {meta['element_id'] for (meta, _) in values}
    require(required <= present, 'manuscript-figure-embed-missing')
    for (meta, body) in values:
        e = index.get(meta['element_id'])
        require(e and e['kind'] == 'figure' and (e['source_sha256'] == meta['source_sha256']), 'figure-source-binding')
        require(role(e, m) == 'manuscript' or (role(e, m) == 'supplement' and meta.get('reason', '').strip()), 'supplement-reason-required')
        links = re.findall('!\\[(?:\\\\.|[^\\]])*\\]\\(([^\\n)]+)\\)', body)
        fragments = e['evidence'].get('body_fragments', [])
        require(len(links) == len(fragments), 'figure-fragment-count')
        for (link, fragment) in zip(links, fragments):
            require(not re.match('[a-zA-Z][a-zA-Z0-9+.-]*:', link) and (not link.startswith('/')), 'local-relative-figure-required')
            target = (absolute(page).parent / unquote(link)).resolve()
            require(target == (image_root / fragment['crop']).resolve(), 'figure-crop-binding')
            require(pa.sha(paths[fragment['crop']]) == fragment['crop_sha256'], 'figure-crop-hash')
            if require_local:
                require(target.is_file() and pa.sha(target) == fragment['crop_sha256'], 'figure-image-missing-or-changed')
    return len(values)

def verify_archive_only(text):
    require(not re.search('<!-- /?paper-figure|!\\[|<img\\b|^(?:Source package|Enrichment products|Annotated enrichment):', text, re.MULTILINE | re.IGNORECASE), 'archive-only-page-must-not-embed-images-or-local-source-pointers')
