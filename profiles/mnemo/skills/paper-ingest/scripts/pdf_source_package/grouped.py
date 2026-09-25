import copy, json, math, struct
from . import native as pilot
from .grouping import verify_partition

SETTINGS = dict(model='qwen3.8-27b', temperature=0, response_format={'type': 'json_object'}, max_tokens=65536)


SEPARATOR = '\nCENTRAL PAGE INVENTORY\n'


REPRESENTATION = ('Inventory representation: each page-local integer local_id (1 through N) is a bijective alias for one original native object ID. Return these integers in object_ids, never original string IDs. objects_by_type gives each row its native type; columns are [local_id,x0,y0,x1,y1] with exact native text appended only for native-text-line rows. default_issues=[] and default_selectable=true apply unless exceptions supplies [local_id,issues,selectable]; retain and respect every exception. Coordinates are original unrotated PyMuPDF page points (top-left origin, x right, y down), not pixels or generated bounds. Short decimal coordinates decode to their exact original IEEE754 binary32 values, including signed zero; a nonfinite_native_float marker preserves an unrenderable native value. Export always uses the untouched original inventory bounds, never these encoded decimals. No objects are grouped, removed or deduplicated by this encoding.\n')


FLAT_PROMPT = pilot.PROMPT.replace('"object_ids":[string,...]', '"object_ids":[integer,...]').replace('Return ONLY one JSON object with EXACT keys:\n', REPRESENTATION + 'Return ONLY one JSON object with EXACT keys:\n')


UNIT_REPRESENTATION = ('Inventory representation: each page-local integer local_id (1 through N) selects one indivisible unit. A unit is one original object or a native-path-group. Selecting a group expands to ALL original members, never a subset. Each group uses one distinct native clipping-scope occurrence, not rectangle similarity or a semantic figure label. group_provenance rows are [local_id,scope_occurrence,scope_level,drawing_index,member_count,type_counts]; full memberships stay in the local mapping. A group does not imply a figure. If any indivisible unit spans unrelated content or multiple figures so a complete valid selection cannot be represented, use status unresolved with the limitation; never split it, silently drop members, duplicate it or generate coordinates. objects_by_type rows are [local_id,x0,y0,x1,y1], with exact native text appended for native-text-line only. Group bounds are the exact min/max union of ORIGINAL member paint bounds, never clip/scissor or drawing rectangles. default_issues=[] and default_selectable=true apply unless exceptions supplies [local_id,issues,selectable]. Coordinates are original unrotated PyMuPDF page points (top-left origin, x right, y down). Short decimals reconstruct exact original IEEE754 binary32 values, including signed zero; nonfinite_native_float marks an unrenderable native value. Export uses untouched original members and their original bounds. Every original ID belongs to exactly one unit; none are removed. Return integer unit IDs in object_ids.\n')


COMPACT_PROMPT = FLAT_PROMPT.replace(REPRESENTATION, UNIT_REPRESENTATION).replace('existing native object IDs', 'existing native unit IDs').replace('Filled and stroked versions are distinct IDs; select both when both belong.', 'Filled and stroked paint operations remain distinct source members; select every unit needed to include both when both belong.').replace('If a source object is indivisible', 'If a source object or native group is indivisible')


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


def unit_inventory(inv, mapping):
    verify_partition(inv, mapping)
    data = {k: inv[k] for k in ('page', 'page_bbox', 'coordinate_system')}
    data['objects'] = [dict(id=f'p{inv["page"]:04d}-unit-{u["unit_id"]}',
         type=u.get('type', 'native-path-group'), **{k: copy.deepcopy(u[k]) for k in ('bbox','issues','selectable','text') if k in u}) for u in mapping['units']]
    return data


def make_request(inv, old, mapping):
    require(set(old) == set(SETTINGS) | {'messages'}, 'original wire settings shape')
    require({k: old[k] for k in SETTINGS} == SETTINGS, 'original settings changed')
    require(len(old['messages']) == 1 and old['messages'][0]['role'] == 'user', 'message shape')
    original_text = old['messages'][0]['content'][0]['text']
    _, original_compact = encode(inv)
    expected = FLAT_PROMPT + SEPARATOR + json.dumps(original_compact, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    require(original_text == expected, 'saved compact inventory/prompt mismatch')
    unit_inv = unit_inventory(inv, mapping)
    _, compact = encode(unit_inv)
    compact['group_provenance'] = [[u['unit_id'], u['scope_occurrence'], u['scope_level'], u['scope_drawing_index'], u['member_count'], u['type_counts']] for u in mapping['units'] if u['kind'] == 'native-path-group']
    request = copy.deepcopy(old)
    request['messages'][0]['content'][0]['text'] = COMPACT_PROMPT + SEPARATOR + json.dumps(compact, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    require(request['messages'][0]['content'][1:] == old['messages'][0]['content'][1:], 'image parts changed')
    return request, mapping, compact


def alias_to_native(value, inv, mapping):
    unit_inv = unit_inventory(inv, mapping)
    aliases = copy.deepcopy(value)
    require(isinstance(aliases, dict) and isinstance(aliases.get('figures'), list), 'unit root schema')
    seen = set()
    for group in aliases['figures']:
        require(isinstance(group, dict) and isinstance(group.get('fragments'), list), 'unit group schema')
        for fragment in group['fragments']:
            require(isinstance(fragment, dict) and isinstance(fragment.get('object_ids'), list), 'unit fragment schema')
            for i, unit in enumerate(fragment['object_ids']):
                require(type(unit) is int, 'unit must be an integer, not bool/float/string')
                require(1 <= unit <= len(mapping['units']), 'unknown/out-of-range unit')
                require(unit not in seen, 'duplicate unit')
                seen.add(unit)
                fragment['object_ids'][i] = unit_inv['objects'][unit-1]['id']
    pilot.validate(aliases, unit_inv)
    mapped, expanded = copy.deepcopy(value), set()
    for group in mapped['figures']:
        for fragment in group['fragments']:
            members = [oid for unit in fragment['object_ids'] for oid in mapping['units'][unit-1]['members']]
            require(len(members) == len(set(members)) and not expanded.intersection(members), 'repeated expanded original member')
            expanded.update(members)
            fragment['object_ids'] = members
    return pilot.validate(mapped, inv)
