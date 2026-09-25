from pathlib import Path
from collections import Counter
import hashlib, math, json, copy
import pymupdf as fitz
from .io import save
MODEL="qwen3.8-27b"

GRAPHICS = {'fill-image', 'fill-imgmask', 'fill-path', 'stroke-path', 'fill-shade'}


TEXT = {'fill-text', 'stroke-text', 'ignore-text'}


COORD = 'original one-based PDF page; unrotated PyMuPDF points; top-left origin, x right, y down; rotation asserted zero'


LIMITATIONS = [
    'Native selection plus a new figure-body prompt is being tested; this is not a coordinates-only or model-only comparison.',
    'Geometric paint bounds are not visible-tight figure boundaries. The bbox device reports transformed image rectangles and path bounds; its installed callbacks do not intersect these with clipping paths or test opacity, masks, occlusion or visible ink.',
    'Fill and stroke are separate operations. A path, image or native text line can be indivisible and span unrelated material or multiple figures. No generated box, grouping heuristic or repair is permitted.',
    'get_text(dict) uses its default page clip and extraction settings, as in the caption inventory. Native extraction can omit clipped glyphs, contain hidden text or combine unrelated text; text paint operations are retained in the raw log but not duplicated as graphical candidates. No one-to-one line/paint mapping is claimed.',
    'Rasterized or outlined lettering is not recovered as separate native text. Image masks remain graphical candidates. get_drawings and get_image_info counts are diagnostic only; no mapping to bboxlog objects is inferred.',
    'Selected bounds are unioned without padding. Rendering retains ALL original source content inside each crop, including unselected and unrelated content. Out-of-page unions are implicitly clipped by the renderer to the page.',
    'Crops use fresh source handles, group/fragment order at 300 DPI, then overview at 150 DPI. Reproducibility applies to this sequence, not all render orders.',
    'Figures remain page-local; caption extraction, cross-page identity and inferred label attachment are excluded. Null labels remain null.',
    'Valid IDs, reproducible pixels and completed calls do not establish visual completeness or correct grouping. Human review is pending.',
]


PROMPT = '''Identify every complete author-defined scientific FIGURE BODY on the CENTRAL original PDF page by selecting existing native object IDs from the complete inventory below. Neighboring images are context only. Only central-page IDs may be selected.
Include every panel, figure-internal legend, axis label, panel letter, and table panel inside a figure. Keep all panels of one figure together; keep distinct figures separate. Exclude caption prose, standalone tables, body prose, headers/footers and publisher logos. Do not extract captions or describe figures.
ID semantics: select ALL source objects belonging to the full figure body, not arbitrary interior anchors or a few objects chosen only to imply a rectangle. Native text lines and graphical paint operations are both candidates. Filled and stroked versions are distinct IDs; select both when both belong. For a raster body, lettering/panels inside the image are inseparable parts of that image. Do not select caption lines to enlarge a crop. A table panel inside a figure belongs to that figure and must be preserved, even though a standalone table is excluded.
Each figure has ordered source-region fragments. Normally put all its objects in one fragment. Use multiple ordered fragments only when separate source regions are needed, never proximity-based regrouping or stitching. Each ID may appear once in the entire response. Every fragment must have at least one ID.
The exporter computes a min/max union of the selected native bounds for each fragment, with no padding or reconstruction. It renders ALL original source content inside that union, not just selected objects. Bounds may include whitespace, invisible paint or unrelated material; they are NOT guaranteed visible-tight boundaries. Never supply coordinates, boxes, transcribed crop content or figure descriptions.
If a source object is indivisible across two figures or unrelated content, explicitly state the limitation in uncertainty. Do not pretend to separate it by generating a box or duplicating its ID. If no valid grouping can be represented, use status unresolved and explain the limitation, with no fabricated group. Unsupported or non-finite/degenerate objects remain visible in the inventory but cannot be rendered; explain any resulting inability to select a full figure.
Report the full observed figure label only if visibly established on the CENTRAL page; otherwise label=null. Do not attach a neighboring caption's label, infer a label sequence or integrate cross-page identity. Label is metadata only, never crop content. Uncertainty strings must be brief selection/indivisibility limitations, not scientific descriptions.
Return ONLY one JSON object with EXACT keys:
{"status":"ok"|"empty"|"unresolved","figures":[{"label":string|null,"fragments":[{"object_ids":[string,...]}],"uncertainty":[string,...]}],"uncertainty":[string,...]}
No additional keys, no generated bbox, no markdown. status=ok requires at least one figure. status=empty requires figures=[] and explicitly means no figure body on the central page. status=unresolved requires nonempty uncertainty and means selection could not be represented completely; any representable groups may be retained. Do not use empty to conceal uncertainty or a processing failure.
'''


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    return sha_bytes(Path(path).read_bytes())


def bounds_issues(box, page_box):
    if len(box) != 4 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in box):
        return ['non-finite-or-malformed-bounds']
    issues = []
    if box[0] >= box[2] or box[1] >= box[3]:
        issues.append('degenerate-or-inverted-bounds')
    if box[0] < page_box[0] or box[1] < page_box[1] or box[2] > page_box[2] or box[3] > page_box[3]:
        issues.append('out-of-page-bounds')
    return issues


def safe_numbers(value):
    # JSON has no non-finite numbers: preserve their explicit repr, never substitute coordinates.
    if isinstance(value, float) and not math.isfinite(value):
        return {'nonfinite_native_float': repr(value)}
    if isinstance(value, (list, tuple)):
        return [safe_numbers(v) for v in value]
    if isinstance(value, dict):
        return {str(k): safe_numbers(v) for k, v in value.items()}
    return value


def inventory(path, number):
    with fitz.open(path) as doc:
        page = doc[number - 1]
        assert page.rotation == 0, 'unsupported rotation: source remains unchanged'
        page_box = list(page.rect)
        log = page.get_bboxlog()
        data = page.get_text('dict')
        objects, excluded = [], []
        for i, (kind, bbox) in enumerate(log):
            item = {'id': f'p{number:04d}-o{i:05d}', 'page': number,
                    'type': kind, 'sequence_index': i, 'bbox': list(bbox), 'coordinate_system': COORD,
                    'issues': bounds_issues(bbox, page_box)}
            if kind in TEXT:
                excluded.append({**item, 'reason': 'text paint: native text lines are inventoried instead; no exact line/operation mapping asserted'})
                continue
            if kind not in GRAPHICS:
                item['issues'].append('unsupported-paint-type')
            item['selectable'] = not any(x != 'out-of-page-bounds' for x in item['issues'])
            objects.append(item)
        for bi, block in enumerate(data['blocks']):
            if block['type'] != 0:
                continue
            for li, line in enumerate(block['lines']):
                issues = bounds_issues(line['bbox'], page_box)
                objects.append({'id': f'p{number:04d}-b{bi:04d}-l{li:04d}', 'page': number,
                                'type': 'native-text-line', 'block_index': bi, 'line_index': li,
                                'native_block_number': block.get('number'), 'bbox': list(line['bbox']),
                                'text': ''.join(s['text'] for s in line['spans']), 'spans': line['spans'],
                                'wmode': line['wmode'], 'dir': line['dir'], 'coordinate_system': COORD,
                                'issues': issues, 'selectable': not any(x != 'out-of-page-bounds' for x in issues)})
        drawings = page.get_drawings()
        result = {'page': number, 'page_count': len(doc), 'page_bbox': page_box, 'rotation': page.rotation,
                  'cropbox': list(page.cropbox), 'mediabox': list(page.mediabox), 'coordinate_system': COORD,
                  'source_sha256': sha(path), 'objects': objects,
                  'bboxlog': [{'sequence_index': i, 'type': t, 'bbox': list(b)} for i, (t, b) in enumerate(log)],
                  'excluded_paint_operations': excluded,
                  'accounting': {'bboxlog_count': len(log), 'paint_types': dict(Counter(t for t, b in log)),
                                 'excluded_by_type': dict(Counter(o['type'] for o in excluded)),
                                 'candidate_types': dict(Counter(o['type'] for o in objects)),
                                 'candidate_count': len(objects), 'native_text_lines': sum(o['type'] == 'native-text-line' for o in objects),
                                 'native_block_types': dict(Counter(b['type'] for b in data['blocks'])),
                                 'image_occurrences_diagnostic': len(page.get_image_info()),
                                 'drawing_paths_diagnostic': len(drawings),
                                 'drawing_elementary_commands_diagnostic': sum(len(d['items']) for d in drawings),
                                 'unsupported_types': sorted({o['type'] for o in objects if o['type'] not in GRAPHICS | {'native-text-line'}})},
                  'limitations': LIMITATIONS}
        assert len(log) == len(excluded) + sum(o['type'] != 'native-text-line' for o in objects)
        return safe_numbers(result)


def make_request(inv, old_wire):
    compact = [{k: o[k] for k in ('id', 'type', 'bbox', 'text', 'issues', 'selectable') if k in o} for o in inv['objects']]
    text = PROMPT + '\nCENTRAL PAGE INVENTORY\n' + json.dumps(
        {'page': inv['page'], 'page_bbox': inv['page_bbox'], 'coordinate_system': COORD, 'objects': compact},
        ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    # Preserve all original neighbor/central image parts AND exact labels, in original order.
    old_content = old_wire['messages'][0]['content']
    assert len(old_wire['messages']) == 1 and old_content[0]['type'] == 'text'
    return {'model': MODEL, 'temperature': 0, 'response_format': {'type': 'json_object'}, 'max_tokens': 16384,
            'messages': [{'role': 'user', 'content': [{'type': 'text', 'text': text}] + copy.deepcopy(old_content[1:])}]}


class SelectionError(ValueError):
    pass


def require(condition, diagnostic):
    if not condition:
        raise SelectionError(diagnostic)


def strict_json(text):
    def pairs(items):
        d = {}
        for key, value in items:
            require(key not in d, 'duplicate-json-key:' + key)
            d[key] = value
        return d
    def constant(value):
        raise SelectionError('non-json-number:' + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def validate(value, inv):
    require(isinstance(value, dict) and set(value) == {'status', 'figures', 'uncertainty'}, 'root-schema')
    require(value['status'] in ('ok', 'empty', 'unresolved'), 'status-schema')
    def uncertainty(x):
        return isinstance(x, list) and all(isinstance(s, str) and bool(s.strip()) for s in x)
    require(uncertainty(value['uncertainty']), 'root-uncertainty-schema')
    require(isinstance(value['figures'], list), 'figures-schema')
    require(value['status'] != 'empty' or not value['figures'], 'explicit-empty-with-groups')
    require(value['status'] != 'ok' or bool(value['figures']), 'ok-without-groups')
    require(value['status'] != 'unresolved' or bool(value['uncertainty']), 'unresolved-without-reason')
    known = {o['id']: o for o in inv['objects']}
    seen = set()
    for gi, group in enumerate(value['figures']):
        require(isinstance(group, dict) and set(group) == {'label', 'fragments', 'uncertainty'}, f'group-schema:{gi}')
        require(group['label'] is None or isinstance(group['label'], str) and bool(group['label'].strip()), f'label-schema:{gi}')
        require(uncertainty(group['uncertainty']), f'uncertainty-schema:{gi}')
        require(isinstance(group['fragments'], list) and bool(group['fragments']), f'fragments-schema:{gi}')
        for fi, fragment in enumerate(group['fragments']):
            require(isinstance(fragment, dict) and set(fragment) == {'object_ids'}, f'fragment-schema:{gi}:{fi}')
            ids = fragment['object_ids']
            require(isinstance(ids, list) and bool(ids), f'empty-or-malformed-fragment:{gi}:{fi}')
            for oid in ids:
                require(isinstance(oid, str), 'id-type')
                require(oid.startswith(f'p{inv["page"]:04d}-'), 'wrong-page-id:' + oid)
                require(oid in known, 'unknown-id:' + oid)
                require(oid not in seen, 'duplicate-id:' + oid)
                require(known[oid]['selectable'], 'unrenderable-id:' + oid)
                seen.add(oid)
    return value


def union(boxes):
    return [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]


def selected_regions(selection, inv):
    known = {o['id']: o for o in inv['objects']}
    regions = []
    for gi, group in enumerate(selection['figures'], 1):
        group_box = union([known[oid]['bbox'] for fragment in group['fragments'] for oid in fragment['object_ids']])
        for fi, fragment in enumerate(group['fragments'], 1):
            selected = [known[oid] for oid in fragment['object_ids']]
            box = union([o['bbox'] for o in selected])
            clipped = list(fitz.Rect(box) & fitz.Rect(inv['page_bbox']))
            require(not fitz.Rect(clipped).is_empty, f'empty-page-intersection:{gi}:{fi}')
            regions.append({'group': gi, 'fragment': fi, 'label': group['label'], 'uncertainty': group['uncertainty'],
                            'page': inv['page'], 'coordinate_system': COORD, 'bbox': box, 'figure_union_bbox': group_box, 'page_intersection': clipped,
                            'implicit_page_edge_clipping': clipped != box,
                            'selected_boxes': [{k: o[k] for k in ('id', 'type', 'bbox')} for o in selected],
                            'object_ids': fragment['object_ids'], 'png': f'figure-{gi:03d}-fragment-{fi:02d}.png'})
    return regions


def export(path, number, regions, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    events = []
    with fitz.open(path) as doc:
        page = doc[number - 1]
        assert page.rotation == 0, 'unsupported rotation'
        for region in regions:
            pix = page.get_pixmap(clip=fitz.Rect(region['bbox']), dpi=300, alpha=False)
            dest = out / region['png']
            assert not dest.exists(), 'never overwrite crop evidence'
            pix.save(dest)
            events.append({'order': len(events), 'kind': 'crop', 'path': dest.name, 'dpi': 300,
                           'bbox': region['bbox'], 'width': pix.width, 'height': pix.height,
                           'pixel_sha256': sha_bytes(pix.samples), 'png_sha256': sha(dest)})
        pix = page.get_pixmap(dpi=150, alpha=False)
        dest = out / 'overview.png'
        assert not dest.exists(), 'never overwrite overview evidence'
        pix.save(dest)
        events.append({'order': len(events), 'kind': 'overview', 'path': dest.name, 'dpi': 150,
                       'width': pix.width, 'height': pix.height, 'pixel_sha256': sha_bytes(pix.samples), 'png_sha256': sha(dest)})
    save(out / 'render-sequence.json', {'fresh_source_handle': True, 'operations_before_render': 'open PDF, load central page, assert rotation; no inventory/text/image render on this handle', 'events': events})
    return events
