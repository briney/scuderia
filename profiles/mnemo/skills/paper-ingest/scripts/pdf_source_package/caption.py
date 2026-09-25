"""Private bounded native-line selection experiment. No production imports."""


import copy


import json


from pathlib import Path


import pymupdf as fitz


def select(content, inv):
    """Reject invalid fragments as a whole; retain every original decision in raw_selection."""
    import re
    result = {'status': 'ok', 'raw_content': content, 'objects': [], 'diagnostics': [], 'page': inv['page']}
    def error(code, location, value):
        result['status'] = 'validation_failed'
        result['diagnostics'].append({'code': code, 'location': location, 'value': value})
    def nullable(value):
        return value is None or isinstance(value, str)
    try:
        parsed = json.loads(content)
    except (ValueError, TypeError):
        result.update(status='parse_failed', diagnostics=[{'code': 'invalid_json', 'location': '$'}])
        return result
    result['raw_selection'] = parsed
    if not isinstance(parsed, dict) or not isinstance(parsed.get('objects'), list):
        error('malformed_output', '$', parsed)
        return result
    result.update(uncertainty=parsed.get('uncertainty'), empty_reason=parsed.get('empty_reason'))
    if type(parsed.get('page')) is not int or parsed['page'] != inv['page']:
        error('wrong_page', '$.page', parsed.get('page'))
        return result
    if any(k not in parsed for k in ('uncertainty', 'empty_reason')) or not all(nullable(parsed.get(k)) for k in ('uncertainty', 'empty_reason')):
        error('malformed_output', '$', parsed)
        return result
    if 'bbox' in parsed:
        error('generated_bbox_forbidden', '$', parsed['bbox'])
        return result
    if not parsed['objects']:
        if isinstance(parsed['empty_reason'], str) and parsed['empty_reason'].strip():
            result['status'] = 'explicit_empty'
        else:
            error('empty_not_explicit', '$', parsed)
        return result
    lookup = {line['id']: line for line in inv['lines']}
    seen_objects, seen_fragments, seen_lines = set(), set(), set()
    for oi, obj in enumerate(parsed['objects']):
        where = f'objects[{oi}]'
        if (not isinstance(obj, dict) or any(k not in obj for k in ('id', 'role', 'associated_label', 'uncertainty', 'fragments'))
                or not isinstance(obj.get('id'), str) or not re.fullmatch(r'o[0-9]+', obj['id'])
                or obj['role'] not in ('caption', 'footnote') or not nullable(obj['associated_label'])
                or obj['associated_label'] == '' or not nullable(obj['uncertainty'])
                or not isinstance(obj['fragments'], list) or not obj['fragments']):
            error('malformed_object', where, obj)
            continue
        if obj['id'] in seen_objects:
            error('duplicate_object_id', where, obj['id'])
            continue
        seen_objects.add(obj['id'])
        if 'bbox' in obj:
            error('generated_bbox_forbidden', where, obj['bbox'])
            continue
        out = {k: copy.deepcopy(obj[k]) for k in ('id', 'role', 'associated_label', 'uncertainty')}
        out['fragments'] = []
        result['objects'].append(out)
        for fi, fragment in enumerate(obj['fragments']):
            loc = f'{where}.fragments[{fi}]'
            count = len(result['diagnostics'])
            if (not isinstance(fragment, dict) or any(k not in fragment for k in ('id', 'line_ids', 'uncertainty'))
                    or not isinstance(fragment.get('id'), str) or not re.fullmatch(r'f[0-9]+', fragment['id'])
                    or not isinstance(fragment['line_ids'], list) or not fragment['line_ids']
                    or not nullable(fragment['uncertainty'])):
                error('malformed_fragment', loc, fragment)
                out['fragments'].append({'status': 'invalid', 'raw_fragment': fragment})
                continue
            target = {k: copy.deepcopy(fragment[k]) for k in ('id', 'line_ids', 'uncertainty')}
            target.update(status='invalid', raw_fragment=fragment)
            out['fragments'].append(target)
            if fragment['id'] in seen_fragments:
                error('duplicate_fragment_id', loc, fragment['id'])
            seen_fragments.add(fragment['id'])
            if 'bbox' in fragment:
                error('generated_bbox_forbidden', loc, fragment['bbox'])
            for index, line_id in enumerate(fragment['line_ids']):
                idloc = f'{loc}.line_ids[{index}]'
                if not isinstance(line_id, str) or not re.fullmatch(r'p[0-9]{4}-b[0-9]{4}-l[0-9]{4}', line_id):
                    error('malformed_id', idloc, line_id)
                    continue
                if not line_id.startswith(f'p{inv["page"]:04d}-'):
                    error('wrong_page_id', idloc, line_id)
                elif line_id not in lookup:
                    error('unknown_id', idloc, line_id)
                if line_id in seen_lines:
                    error('duplicate_id', idloc, line_id)
                seen_lines.add(line_id)
            if len(result['diagnostics']) != count:
                continue
            lines = [lookup[i] for i in fragment['line_ids']]
            target.update(selected_lines=lines, native_text='\n'.join(l['text'] for l in lines),
                          status='ok', bbox=[min(l['bbox'][0] for l in lines), min(l['bbox'][1] for l in lines),
                                             max(l['bbox'][2] for l in lines), max(l['bbox'][3] for l in lines)])
    return result


def export(page, result, out):
    """Direct source crop, no padding. Render order is object then fragment order."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rotation = page.rotation
    try:
        page.set_rotation(0)
        for oi, obj in enumerate(result['objects']):
            for fi, fragment in enumerate(obj['fragments']):
                if fragment['status'] != 'ok':
                    continue
                name = f'object-{oi + 1:02d}-fragment-{fi + 1:02d}.png'
                page.get_pixmap(dpi=300, clip=fitz.Rect(fragment['bbox']), alpha=False).save(out / name)
                fragment['png'] = name
                (out / name.replace('.png', '.txt')).write_text(fragment['native_text'])
    finally:
        page.set_rotation(rotation)


def inventory(page, paper, number):
    lines = []
    for bi, block in enumerate(page.get_text('dict')['blocks']):
        if block['type'] != 0:
            continue
        for li, line in enumerate(block['lines']):
            lines.append({'id': f'p{number:04d}-b{bi:04d}-l{li:04d}',
                          'page': number, 'block_index': bi, 'line_index': li,
                          'block_number': block.get('number'), 'block_bbox': list(block['bbox']),
                          'bbox': list(line['bbox']), 'text': ''.join(s['text'] for s in line['spans']),
                          'spans': line['spans'], 'direction': line.get('dir'), 'wmode': line.get('wmode')})
    return {'paper': paper, 'document': 'manuscript', 'page': number,
            'coordinate_system': 'top-left origin; unrotated PDF points',
            'rotation': page.rotation, 'cropbox': list(page.cropbox),
            'extraction': "PyMuPDF get_text('dict'), default order/flags; every line of every type-0 text block; span text concatenated without normalization",
            'lines': lines}
