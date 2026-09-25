"""One conservative native-clip partition; geometry always comes from bboxlog."""


import copy


import hashlib


import json


from collections import Counter


import pymupdf as fitz


from . import native as pilot


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()).hexdigest()


def native_json(value):
    if isinstance(value, dict):
        return {k: native_json(v) for k, v in value.items()}
    if isinstance(value, (tuple, list, fitz.Rect, fitz.Point, fitz.Quad)):
        return [native_json(v) for v in value]
    return pilot.safe_numbers(value)


def partition(source, inv):
    pilot.require(pilot.sha(source) == inv['source_sha256'], 'partition source binding')
    with fitz.open(source) as doc:
        page = doc[inv['page'] - 1]
        pilot.require(page.rotation == 0 and list(page.rect) == inv['page_bbox'], 'partition page geometry')
        log = [{'sequence_index': i, 'type': t, 'bbox': list(b)} for i, (t, b) in enumerate(page.get_bboxlog())]
        pilot.require(pilot.safe_numbers(log) == inv['bboxlog'], 'partition native log binding')
        records = native_json(page.get_drawings(extended=True))
        from .native_trace import trace_page
        native_trace = trace_page(page, log, records)
    # Original bboxlog sequence_index is authoritative. Drawing path seqno is
    # deliberately unused: get_drawings may omit empty paths or merge f/s.
    blockers = [{'reason': 'native-callback-verification-failed', **b} for b in native_trace['blockers']]
    for obj in inv['objects']:
        if 'sequence_index' not in obj:
            continue
        seq = obj['sequence_index']
        if (type(seq) is not int or not 0 <= seq < len(log) or
                obj['type'] != log[seq]['type'] or digest(obj['bbox']) != digest(log[seq]['bbox'])):
            blockers.append({'reason': 'original-object-bboxlog-binding-mismatch', 'native_id': obj['id']})
    scopes, decisions, assigned = [], [], {}
    for match in native_trace['scope_record_correspondence']:
        record = records[match['drawing_index']]
        scopes.append({'occurrence': match['scope_occurrence'], 'drawing_index': match['drawing_index'],
                       'parents': match['parents'], **copy.deepcopy(record),
                       'native_event_index': match['native_event_index'], 'native_kind': match['native_kind']})
    for obj in inv['objects']:
        seq = obj.get('sequence_index')
        actual = native_trace['paints'][seq] if type(seq) is int and 0 <= seq < len(native_trace['paints']) else None
        stack = actual['stack'] if actual else []
        clips = [s for s in stack if s['type'] != 'group']
        active_clip = clips[-1] if clips else None
        hidden = any(s['type'] not in ('clip_path', 'clip_stroke_path') for s in clips)
        scope = scopes[active_clip['occurrence']-1] if active_clip and active_clip['occurrence'] is not None and not blockers else None
        decision = {'native_id': obj['id'], 'type': obj['type'], 'sequence_index': seq,
                    'scope_occurrence': scope['occurrence'] if scope else None,
                    'native_stack': stack, 'active_occurrences': [s['occurrence'] for s in stack]}
        if obj['type'] not in ('fill-path', 'stroke-path'):
            reason = 'non-path-original-object-kept-individual'
        elif not obj['selectable'] or any(x != 'out-of-page-bounds' for x in obj['issues']):
            reason = 'unrenderable-original-operation'
        elif blockers:
            reason = 'native-stream-or-source-binding-blocked-all-original-leaves-retained'
        elif actual is None:
            reason = 'missing-original-paint-index-kept-individual'
        elif actual['type'] != obj['type']:
            # Full stream equality above normally makes this unreachable; retain
            # the individual object rather than infer a nearby operation.
            reason = 'native-paint-type-disagreement-kept-individual'
        elif hidden:
            reason = 'unsupported-active-native-clip-kept-individual'
        elif not scope:
            reason = 'no-active-native-clip'
        else:
            reason = 'original-paint-mapped-to-deepest-native-path-clip'
            assigned[obj['id']] = scope['occurrence']
        decision['disposition'] = reason
        decisions.append(decision)
    buckets = {}
    for obj in inv['objects']:
        if obj['id'] in assigned:
            buckets.setdefault(assigned[obj['id']], []).append(obj)
    units, done = [], set()
    for obj in inv['objects']:
        if obj['id'] in done:
            continue
        occurrence = assigned.get(obj['id'])
        members = buckets.get(occurrence, [])
        if len(members) >= 2:
            unit = {'kind': 'native-path-group', 'members': [m['id'] for m in members],
                    'bbox': pilot.union([m['bbox'] for m in members]), 'scope_occurrence': occurrence,
                    'scope_level': scopes[occurrence-1]['level'], 'scope_drawing_index': scopes[occurrence-1]['drawing_index'],
                    'member_count': len(members), 'type_counts': dict(Counter(m['type'] for m in members)),
                    'issues': list(dict.fromkeys(x for m in members for x in m['issues'])), 'selectable': True}
        else:
            unit = {'kind': 'object', 'members': [obj['id']], **{k: copy.deepcopy(obj[k]) for k in ('type', 'bbox', 'issues', 'selectable', 'text') if k in obj}}
        unit['unit_id'] = len(units) + 1
        units.append(unit)
        done.update(unit['members'])
    mapping = {'page': inv['page'], 'source_sha256': inv['source_sha256'], 'inventory_digest': digest(inv), 'units': units}
    verify_partition(inv, mapping)
    grouped = [u for u in units if u['kind'] == 'native-path-group']
    evidence = {'source_sha256': inv['source_sha256'], 'page': inv['page'], 'pymupdf': fitz.__version__,
                'records': records, 'scopes': scopes, 'path_decisions': decisions, 'native_trace': native_trace,
                'original_object_dispositions': [{'id': o['id'], 'type': o['type'],
                    'scope_occurrence': assigned.get(o['id']),
                    'disposition': ('group-member' if o['id'] in assigned and len(buckets[assigned[o['id']]]) >= 2 else
                                    'single-member-native-scope-leaf' if o['id'] in assigned else
                                    'page-mapping-blocked-leaf' if blockers else
                                    'unmapped-or-unsupported-or-ambiguous-original-leaf')}
                    for o in inv['objects']],
                'unmapped_original_ids': [o['id'] for o in inv['objects'] if o['id'] not in assigned],
                'sequence_mapping_blockers': blockers,
                'summary': {'native_mapping_verified': not blockers, 'sequence_mapping_blocker_count': len(blockers),
                    'original_candidates': len(inv['objects']), 'visible_units': len(units),
                    'native_path_groups': len(grouped), 'grouped_original_paths': sum(len(u['members']) for u in grouped),
                    'clip_occurrences': sum(s['type'] == 'clip' for s in scopes),
                    'transparency_group_occurrences': sum(s['type'] == 'group' for s in scopes),
                    'drawing_types': dict(Counter(r['type'] for r in records)),
                    'mapping_dispositions': dict(Counter(d['disposition'] for d in decisions))},
                'identity_method': 'Original inventory sequence_index -> verified full native paint callback; drawing path seqno unused.',
                'lineart_seqno_disposition': 'Retained raw records are diagnostic only; omitted/merged path records are not paint identity.',
                'limitations': ['Eligible original fill/stroke paints are mapped independently using their original bboxlog indices and actual native clip lifetimes.',
                    'Degenerate, unsupported and nonselectable originals remain individual leaves; no offsets, fs adjacency assumptions or geometry substitution.',
                    'Native callback lifetimes determine scope membership; every unsupported active clip keeps the operation individual. Level-only lifetime inference is forbidden.',
                    'Native clip occurrences are rendering structure, not semantic figures; no adaptive splitting.',
                    'Only original member paint bounds define group unions. Scissor and drawing rect never replace them.']}
    return mapping, evidence


def verify_partition(inv, mapping):
    pilot.require(mapping['page'] == inv['page'] and mapping['source_sha256'] == inv['source_sha256'] and mapping['inventory_digest'] == digest(inv), 'partition inventory/source binding')
    known = {o['id']: o for o in inv['objects']}
    pilot.require(len(known) == len(inv['objects']), 'duplicate original ID')
    seen = set()
    for i, unit in enumerate(mapping['units'], 1):
        pilot.require(type(unit['unit_id']) is int and unit['unit_id'] == i, 'unit order/ID')
        members = unit['members']
        pilot.require(isinstance(members, list) and members and all(type(k) is str and k in known and k not in seen for k in members), 'unit membership')
        pilot.require(len(members) == len(set(members)), 'repeated original member')
        seen.update(members)
        originals = [known[k] for k in members]
        if unit['kind'] == 'object':
            pilot.require(len(members) == 1, 'leaf has multiple members')
            pilot.require(all(unit.get(k) == originals[0].get(k) for k in ('type','bbox','issues','selectable','text')), 'leaf changed')
        else:
            pilot.require(unit['kind'] == 'native-path-group' and len(members) >= 2, 'group kind/size')
            pilot.require(all(o['selectable'] and o['type'] in ('fill-path','stroke-path') for o in originals), 'ineligible grouped member')
            pilot.require(unit['bbox'] == pilot.union([o['bbox'] for o in originals]), 'group is not exact member union')
            pilot.require(unit['member_count'] == len(members) and unit['type_counts'] == dict(Counter(o['type'] for o in originals)), 'group counts')
            pilot.require(type(unit['scope_occurrence']) is int and unit['scope_occurrence'] > 0, 'scope occurrence')
            pilot.require(unit['selectable'] is True and unit['issues'] == list(dict.fromkeys(x for o in originals for x in o['issues'])), 'group flags')
    pilot.require(seen == set(known), 'partition is not exhaustive')
