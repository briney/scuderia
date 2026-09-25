import copy, json, math, struct
from . import native as pilot

SETTINGS = dict(model='qwen3.8-27b', temperature=0, response_format={'type': 'json_object'}, max_tokens=65536)


SEPARATOR = '\nCENTRAL PAGE INVENTORY\n'


REPRESENTATION = ('Inventory representation: each page-local integer local_id (1 through N) is a bijective alias for one original native object ID. Return these integers in object_ids, never original string IDs. objects_by_type gives each row its native type; columns are [local_id,x0,y0,x1,y1] with exact native text appended only for native-text-line rows. default_issues=[] and default_selectable=true apply unless exceptions supplies [local_id,issues,selectable]; retain and respect every exception. Coordinates are original unrotated PyMuPDF page points (top-left origin, x right, y down), not pixels or generated bounds. Short decimal coordinates decode to their exact original IEEE754 binary32 values, including signed zero; a nonfinite_native_float marker preserves an unrenderable native value. Export always uses the untouched original inventory bounds, never these encoded decimals. No objects are grouped, removed or deduplicated by this encoding.\n')


COMPACT_PROMPT = pilot.PROMPT.replace('"object_ids":[string,...]', '"object_ids":[integer,...]').replace('Return ONLY one JSON object with EXACT keys:\n', REPRESENTATION + 'Return ONLY one JSON object with EXACT keys:\n')


def require(value, message):
    if not value:
        raise ValueError(message)


def f32(value):
    return struct.unpack('!f', struct.pack('!f', value))[0]


def bits(value):
    return struct.pack('!f', value)


def shortest(value):
    if isinstance(value, dict):
        require(set(value) == {'nonfinite_native_float'}, 'unknown coordinate marker')
        return copy.deepcopy(value)
    require(type(value) in (int, float) and math.isfinite(value) and f32(value) == value, 'not native binary32')
    for digits in range(1, 10):
        candidate = float(format(value, f'.{digits}g'))
        try:
            if f32(candidate) == value and bits(candidate) == bits(value):
                return candidate
        except OverflowError:
            continue  # A low-precision decimal can exceed binary32's finite limit.
    raise ValueError('no exact binary32 encoding')


def encode(inv):
    objects = inv['objects']
    ids = [o['id'] for o in objects]
    require(len(set(ids)) == len(ids), 'duplicate native IDs')
    mapping = {'page': inv['page'], 'native_ids': ids, 'semantics': 'native_ids[local_id-1]; stable original inventory order'}
    data = dict(page=inv['page'], page_bbox=inv['page_bbox'], coordinate_system=inv['coordinate_system'],
                columns=['local_id', 'x0', 'y0', 'x1', 'y1', 'text_for_native_lines_only'],
                coordinate_encoding='decimal values decode to original binary32; export uses untouched original boxes',
                default_issues=[], default_selectable=True, exceptions=[], objects_by_type={})
    for i, obj in enumerate(objects, 1):
        require(('text' in obj) == (obj['type'] == 'native-text-line'), 'unexpected text field')
        row = [i, *[shortest(v) for v in obj['bbox']]]
        if 'text' in obj:
            row.append(obj['text'])
        data['objects_by_type'].setdefault(obj['type'], []).append(row)
        if obj['issues'] or obj['selectable'] is not True:
            data['exceptions'].append([i, obj['issues'], obj['selectable']])
    verify_encoding(inv, mapping, json.loads(json.dumps(data, allow_nan=False)))
    return mapping, data


def verify_encoding(inv, mapping, data):
    require(mapping['page'] == data['page'] == inv['page'], 'mapping page')
    require(mapping['native_ids'] == [o['id'] for o in inv['objects']], 'mapping bijection/order')
    require(data['default_issues'] == [] and data['default_selectable'] is True, 'encoding defaults')
    seen, exceptions = set(), {}
    for alias, issues, selectable in data['exceptions']:
        require(type(alias) is int and 1 <= alias <= len(inv['objects']) and alias not in exceptions, 'exception alias')
        exceptions[alias] = (issues, selectable)
    for typ, rows in data['objects_by_type'].items():
        for row in rows:
            i = row[0]
            require(type(i) is int and 1 <= i <= len(inv['objects']) and i not in seen, 'coverage/alias')
            seen.add(i)
            obj = inv['objects'][i-1]
            require(typ == obj['type'] and len(row) == (6 if 'text' in obj else 5), 'type/row shape')
            require((row[5] if len(row) == 6 else None) == obj.get('text'), 'native text')
            require(exceptions.get(i, ([], True)) == (obj['issues'], obj['selectable']), 'flags')
            for original, compact in zip(obj['bbox'], row[1:5]):
                if isinstance(original, dict):
                    require(original == compact, 'exceptional coordinate')
                else:
                    require(f32(compact) == original and bits(compact) == bits(original), 'numerical/bitwise binary32 reconstruction')
    require(seen == set(range(1, len(inv['objects'])+1)), 'full coverage')


def make_request(inv, old):
    require(set(old) == set(SETTINGS) | {'messages'}, 'original wire settings shape')
    require({k: old[k] for k in SETTINGS} == SETTINGS, 'original settings changed')
    require(len(old['messages']) == 1 and old['messages'][0]['role'] == 'user', 'message shape')
    original_text = old['messages'][0]['content'][0]['text']
    require(original_text.split(SEPARATOR)[0] == pilot.PROMPT, 'semantic prompt mismatch')
    projected = [{k: o[k] for k in ('id', 'type', 'bbox', 'text', 'issues', 'selectable') if k in o} for o in inv['objects']]
    require(json.loads(original_text.split(SEPARATOR, 1)[1]) == {'page': inv['page'], 'page_bbox': inv['page_bbox'], 'coordinate_system': pilot.COORD, 'objects': projected}, 'original inventory mismatch')
    mapping, compact = encode(inv)
    request = copy.deepcopy(old)
    request['messages'][0]['content'][0]['text'] = COMPACT_PROMPT + SEPARATOR + json.dumps(compact, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    require(request['messages'][0]['content'][1:] == old['messages'][0]['content'][1:], 'image parts changed')
    return request, mapping, compact


def alias_to_native(value, inv, mapping):
    require(mapping['native_ids'] == [o['id'] for o in inv['objects']], 'mapping not bound to inventory')
    # Validate every structural rule with the frozen validator on integer-ID stand-ins.
    aliases = copy.deepcopy(value)
    alias_inv = copy.deepcopy(inv)
    for i, obj in enumerate(alias_inv['objects'], 1):
        obj['id'] = f'p{inv["page"]:04d}-alias-{i}'
    require(isinstance(aliases, dict) and isinstance(aliases.get('figures'), list), 'alias root schema')
    seen = set()
    for group in aliases['figures']:
        require(isinstance(group, dict) and isinstance(group.get('fragments'), list), 'alias group schema')
        for fragment in group['fragments']:
            require(isinstance(fragment, dict) and isinstance(fragment.get('object_ids'), list), 'alias fragment schema')
            for i, alias in enumerate(fragment['object_ids']):
                require(type(alias) is int, 'alias must be an integer, not bool/float/string')
                require(1 <= alias <= len(mapping['native_ids']), 'unknown/out-of-range alias')
                require(alias not in seen, 'duplicate alias')
                seen.add(alias)
                fragment['object_ids'][i] = f'p{inv["page"]:04d}-alias-{alias}'
    pilot.validate(aliases, alias_inv)
    mapped = copy.deepcopy(value)
    for group in mapped['figures']:
        for fragment in group['fragments']:
            fragment['object_ids'] = [mapping['native_ids'][alias-1] for alias in fragment['object_ids']]
    return pilot.validate(mapped, inv)


def redact_response(raw, key):
    """Redact a runtime credential even when a JSON string Unicode-escapes it."""
    forms = {key.encode(), json.dumps(key)[1:-1].encode(), json.dumps(key, ensure_ascii=False)[1:-1].encode()}
    changed = any(secret in raw for secret in forms)
    for secret in sorted(forms, key=len, reverse=True):
        raw = raw.replace(secret, b'[REDACTED-CREDENTIAL-ECHO]')
    def scrub(value):
        nonlocal changed
        if isinstance(value, str):
            if key in value:
                changed = True
                return value.replace(key, '[REDACTED-CREDENTIAL-ECHO]')
            # The message content can itself contain JSON-encoded strings.
            if value.lstrip().startswith(('{', '[')):
                try:
                    decoded = pilot.strict_json(value)
                    cleaned = scrub(decoded)
                    if cleaned != decoded:
                        return json.dumps(cleaned, ensure_ascii=False)
                except (ValueError, TypeError):
                    pass
            return value
        if isinstance(value, list):
            return [scrub(item) for item in value]
        if isinstance(value, dict):
            return {scrub(k): scrub(v) for k, v in value.items()}
        return value
    try:
        decoded = pilot.strict_json(raw.decode())
        cleaned = scrub(decoded)
        if cleaned != decoded:
            raw = json.dumps(cleaned, ensure_ascii=False).encode()
    except (ValueError, UnicodeError, TypeError):
        pass
    return raw, changed
