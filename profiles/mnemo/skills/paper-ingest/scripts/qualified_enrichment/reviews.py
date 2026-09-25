"""Append-only contextual reviews. Evidence existence is not scientific proof."""
import copy
import fcntl
import json
from .records import nodes, finding, project, require, digest, related, resolve_pointer
from .storage import absolute, new, load, save, sha, tree, code_hashes, now_utc
from .runtime import snapshot

ASPECTS = ('content', 'source-association', 'notation', 'layout', 'units', 'headers')
NOTICE = ('Reference and literal-selection validation is not scientific verification. '
          'Empty findings do not establish correctness. Native text does not establish '
          'layout or typography; model readings have no automatic precedence.')


def create(path, kind, output):
    state = snapshot(path, kind)
    root = new(output, [absolute(path), absolute(state['source_package'])])
    dossier = dict(schema='uncertainty-dossier-v1', snapshot=state, code=code_hashes(), notice=NOTICE)
    save(root/'dossier.json', dossier)
    (root/'decisions').mkdir()
    return dossier


def verify(root):
    root = absolute(root)
    value = load(root/'dossier.json')
    require(value['schema'] == 'uncertainty-dossier-v1', 'unsupported-dossier-format')
    from pdf_enrichment.trusted import validate_code_provenance
    validate_code_provenance(value['code'])
    expected = snapshot(value['snapshot']['path'], value['snapshot']['kind'])
    require(expected == value['snapshot'], 'stale-source-or-outcome')
    return value


def packet_value(dossier, dossier_hash, elements, max_bytes):
    require(type(max_bytes) is int and 1024 <= max_bytes <= 8_000_000, 'bounded-packet-size-required')
    require(isinstance(elements, list) and elements and len(elements) == len(set(elements)), 'explicit-unique-packet-elements')
    available = {e['element_id']: e for e in dossier['snapshot']['elements']}
    require(set(elements) <= available.keys(), 'unknown-packet-element')
    result = dict(schema='contextual-review-packet-v1', dossier_sha256=dossier_hash,
                  source_package=dossier['snapshot']['source_package'], notice=NOTICE,
                  elements=[dict(available[e], targets=list(nodes(available[e]['outcome'])),
                                 automatic_findings=project(available[e])['findings']) for e in elements])
    require(len((json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode()) <= max_bytes, 'packet-too-large-select-fewer-elements')
    return result


def packet(root, elements, output, max_bytes=1_000_000):
    dossier = verify(root)
    result = packet_value(dossier, sha(absolute(root)/'dossier.json'), elements, max_bytes)
    from .storage import external
    external(output, [absolute(root), absolute(dossier['snapshot']['path']), absolute(dossier['snapshot']['source_package'])])
    save(absolute(output), result)
    return result


def provenance(value):
    require(isinstance(value, dict) and set(value) == {'kind','identity','model','provider','check','timestamp'}, 'reviewer-provenance-fields')
    require(value['kind'] in ('human', 'orchestrator-import', 'model-operator'), 'reviewer-kind')
    require(all(isinstance(value[k], str) and value[k].strip() for k in ('identity','check','timestamp')), 'reviewer-attribution-required')
    if value['kind'] == 'model-operator':
        require(all(isinstance(value[k], str) and value[k].strip() for k in ('model','provider')), 'model-operator-provenance')
    else:
        require(value['model'] is None and value['provider'] is None, 'import-must-not-claim-model-review')


def evidence(element, refs):
    require(isinstance(refs, list), 'evidence-list')
    source = nodes(element['evidence'])
    validated = []
    for ref in refs:
        require(isinstance(ref, dict) and set(ref) <= {'pointer','source_sha256','kind','text','start','end'}, 'evidence-fields')
        require(ref.get('source_sha256') == element['source_sha256'], 'evidence-source-hash')
        pointer = ref.get('pointer')
        require(pointer in source, 'nonexistent-source-reference')
        value = source[pointer]
        owner_pointer = pointer
        while owner_pointer and not (isinstance(source[owner_pointer], dict) and 'crop' in source[owner_pointer]):
            owner_pointer = owner_pointer.rsplit('/', 1)[0]
        owner = source[owner_pointer]
        require(isinstance(owner, dict) and 'crop' in owner and 'page' in owner, 'source-reference-without-owner')
        owner_id = owner.get('fragment_id', owner.get('region_id'))
        require(owner_id, 'source-reference-owner-id')
        if ref.get('kind') == 'native-text':
            require(isinstance(value, str) and pointer.endswith(('/text', '/native_text')), 'literal-native-text-reference')
            start, end = ref.get('start', 0), ref.get('end', len(value))
            require(type(start) is int and type(end) is int and 0 <= start < end <= len(value), 'literal-selection-range')
            require(ref.get('text') == value[start:end], 'literal-selected-text-mismatch')
        else:
            require(ref.get('kind') == 'crop' and pointer == owner_pointer, 'crop-owner-reference-required')
            require('text' not in ref and 'start' not in ref and 'end' not in ref, 'crop-is-not-literal-text')
        validated.append(dict(ref, owner=owner_id, page=owner['page'], crop=owner['crop'], crop_sha256=owner.get('crop_sha256')))
    return validated


def target(element, pointer):
    require(isinstance(pointer, str) and pointer in nodes(element['outcome']), 'nonexistent-target')


def owners_for(element, pointer):
    index = nodes(element['outcome'])
    while pointer:
        value = index[pointer]
        if isinstance(value, dict):
            refs = value.get('source_refs') or value.get('layout_source_refs') or ([value['source_ref']] if value.get('source_ref') else [])
            owners = set()
            for ref in refs:
                if isinstance(ref, str): owners.add(ref)
                elif isinstance(ref, dict):
                    owners.update(ref[k] for k in ('fragment_id','source_ref','region_id') if isinstance(ref.get(k), str))
            if owners:
                return owners
        pointer = pointer.rsplit('/', 1)[0]
    return set()


def apply(dossier, decisions):
    elements = {e['element_id']: e for e in dossier['snapshot']['elements']}
    views = {key: project(value) for key, value in elements.items()}
    known = {f['id']: f for v in views.values() for f in v['findings']}
    for entry in decisions:
        submission = entry['submission']
        provenance(submission['reviewer'])
        packet = entry['packet']
        require(packet['schema'] == 'contextual-review-packet-v1' and
                packet['source_package'] == dossier['snapshot']['source_package'] and packet['notice'] == NOTICE,
                'review-packet-source-association')
        require(packet['dossier_sha256'] == entry['dossier_sha256'], 'review-packet-dossier-binding')
        require(submission['schema'] == 'contextual-review-v1' and submission['packet_sha256'] == digest(packet), 'review-packet-binding')
        permitted = {e['element_id'] for e in packet['elements']}
        require(permitted <= elements.keys(), 'packet-element-binding')
        for item in packet['elements']:
            expected = dict(elements[item['element_id']], targets=list(nodes(elements[item['element_id']]['outcome'])),
                            automatic_findings=project(elements[item['element_id']])['findings'])
            require(item == expected, 'altered-review-packet')
        require(set(submission) == {'schema','packet_sha256','reviewer','findings','coverage','resolutions'}, 'review-fields')
        for group in ('findings','coverage','resolutions'):
            require(isinstance(submission[group], list), 'review-list:'+group)
        for item in submission['findings']:
            require(set(item) <= {'element_id','source_sha256','target','category','reason','stage','evidence','competing_readings'}
                    and all(k in item for k in ('element_id','source_sha256','target','category','reason','stage','evidence')), 'finding-fields')
            eid = item['element_id']; require(eid in permitted, 'finding-outside-packet')
            element = elements[eid]
            require(item['source_sha256'] == element['source_sha256'], 'finding-source-hash')
            target(element, item['target'])
            require(all(isinstance(item[k], str) and item[k].strip() for k in ('category','reason')), 'specific-free-text-reason-required')
            require(item['stage'] in ('extraction','answer'), 'finding-stage')
            refs = evidence(element, item['evidence'])
            value = finding(element, item['target'], item['category'], item['reason'],
                            stage=item['stage'], provenance=submission['reviewer'], evidence=refs)
            readings = item.get('competing_readings', [])
            require(isinstance(readings, list), 'competing-readings-list')
            for reading in readings:
                require(set(reading) == {'text','evidence'} and isinstance(reading['text'], str) and reading['text'].strip(), 'competing-reading-fields')
                require(evidence(element, reading['evidence']), 'competing-reading-evidence-required')
            value['competing_readings'] = readings
            value['id'] = digest(value)
            require(value['id'] not in known, 'duplicate-finding')
            views[eid]['findings'].append(value); known[value['id']] = value
        for item in submission['coverage']:
            require(set(item) == {'element_id','target','aspect','evidence','reason'}, 'coverage-fields')
            eid = item['element_id']; require(eid in permitted, 'coverage-outside-packet')
            element = elements[eid]; target(element, item['target'])
            require(item['target'].startswith('/record/') and item['aspect'] in ASPECTS, 'scoped-record-coverage-required')
            require(isinstance(item['reason'], str) and item['reason'].strip(), 'coverage-reason-required')
            refs = evidence(element, item['evidence']); require(refs, 'coverage-evidence-required')
            if item['aspect'] in ('notation','layout','headers'):
                require(any(r['kind'] == 'crop' for r in refs), 'native-text-cannot-prove-layout')
            views[eid]['coverage'].append(dict(item, evidence=refs, reviewer=submission['reviewer']))
        for item in submission['resolutions']:
            require(set(item) == {'finding_id','reason','basis','evidence','agreement','proposed_value','aspect'}, 'resolution-fields')
            require(item['finding_id'] in known, 'resolution-unknown-finding')
            original = known[item['finding_id']]; eid = original['element_id']
            require(eid in permitted, 'resolution-outside-packet')
            require(isinstance(item['reason'], str) and item['reason'].strip(), 'resolution-reason-required')
            require(item['basis'] in ('literal-copy','source-inspection') and item['aspect'] in ASPECTS, 'resolution-basis')
            # Saved uncertainty can combine unspecified content and structural
            # defects. Do not infer its scope from free-text reasons, or let the
            # caller narrow it by labelling a native match as content review.
            saved_uncertainty = (original['category'] == 'saved-uncertainty' and
                                 original['provenance']['kind'] == 'deterministic-check')
            require(not saved_uncertainty or item['basis'] == 'source-inspection',
                    'saved-uncertainty-requires-source-inspection')
            require(item['agreement'] in ('unambiguous','disputed'), 'resolution-agreement')
            refs = evidence(elements[eid], item['evidence'])
            require(refs, 'unsupported-resolution-no-evidence')
            owners = owners_for(elements[eid], original['target'])
            require(owners and {r['owner'] for r in refs} <= owners, 'resolution-wrong-source-association')
            if item['basis'] == 'literal-copy':
                require(item['aspect'] not in ('notation','layout','headers'), 'native-text-cannot-prove-layout')
                require(len(refs) == 1 and refs[0]['kind'] == 'native-text'
                        and item['proposed_value'] == refs[0]['text'], 'resolved-copy-must-match-source')
                # A valid line elsewhere in the same crop is not a valid unit
                # association. Require the selected native line to belong to
                # this exact field's nearest native-source-bearing container.
                index = nodes(elements[eid]['outcome']); p = original['target']; native_ids = set(); native_refs = []
                while p:
                    container = index[p]
                    if isinstance(container, dict) and container.get('source_refs'):
                        native_refs = [r for r in container['source_refs'] if isinstance(r, dict) and 'line_id' in r]
                        native_ids = {r['line_id'] for r in native_refs}
                        break
                    p = p.rsplit('/', 1)[0]
                source_index = nodes(elements[eid]['evidence']); p = refs[0]['pointer']; selected_id = None
                while p:
                    container = source_index[p]
                    if isinstance(container, dict) and 'line_id' in container:
                        selected_id = container['line_id']; break
                    p = p.rsplit('/', 1)[0]
                require(native_ids and selected_id in native_ids, 'resolution-wrong-native-source-association')
                selected_start = refs[0].get('start', 0)
                selected_end = refs[0].get('end', len(source_index[refs[0]['pointer']]))
                require(len(native_refs) == 1 and native_refs[0].get('start') == selected_start
                        and native_refs[0].get('end') == selected_end, 'resolution-ambiguous-native-range-association')
            else:
                require(any(r['kind'] == 'crop' for r in refs), 'source-inspection-requires-crop')
            # Resolutions are attributed proposals, never edits to the source.
            # Disagreement remains active, even with a resolution submission.
            original.setdefault('resolutions', []).append(dict(item, evidence=refs, reviewer=submission['reviewer']))
            original['status'] = ('resolved-with-attribution' if item['agreement'] == 'unambiguous'
                                  and not original.get('competing_readings')
                                  and (not saved_uncertainty or set(ASPECTS) <=
                                       {r['aspect'] for r in original['resolutions']})
                                  and all(r['agreement'] == 'unambiguous' for r in original['resolutions']) else 'unresolved')
    for view in views.values():
        # Compare all attributed proposals at overlapping saved targets, even
        # across distinct findings/aspect labels. proposed_value denotes the
        # whole finding target, not an implicit patch or scientific equivalence.
        proposals = [(f, r) for f in view['findings'] for r in f.get('resolutions', [])]
        for index, (left, lr) in enumerate(proposals):
            for right, rr in proposals[index+1:]:
                lp, rp = left['target'], right['target']
                if not related(lp, rp):
                    continue
                lv, rv = lr['proposed_value'], rr['proposed_value']
                try:
                    if lp != rp:
                        if rp.startswith(lp+'/'):
                            lv = resolve_pointer(lv, rp[len(lp):])
                        else:
                            rv = resolve_pointer(rv, lp[len(rp):])
                    agrees = digest(lv) == digest(rv)
                except ValueError:
                    agrees = False  # Overlap cannot be compared, not agreement.
                if not agrees:
                    left['status'] = right['status'] = 'unresolved'
        view['review_status'] = 'partially-reviewed' if view['coverage'] else 'unreviewed'
        view['notice'] = NOTICE
    return list(views.values())


def decisions(root, dossier):
    root = absolute(root)
    previous = sha(root/'dossier.json')
    entries = []
    files = sorted((root/'decisions').glob('*.json'))
    for index, path in enumerate(files, 1):
        require(path.name == f'{index:06d}.json', 'review-chain-gap')
        value = load(absolute(path))
        require(value.get('schema') == 'uncertainty-review-decision-v1', 'unsupported-review-decision-format')
        require(value['previous_sha256'] == previous and value['sequence'] == index
                and value['dossier_sha256'] == sha(root/'dossier.json'), 'review-chain-binding')
        entries.append(value); previous = sha(path)
    apply(dossier, entries)
    return entries


def import_review(root, packet_path, submission_path):
    root = absolute(root); dossier = verify(root)
    packet_data = load(absolute(packet_path)); submission = load(absolute(submission_path))
    require(packet_data['dossier_sha256'] == sha(root/'dossier.json'), 'stale-packet')
    with (root/'.review.lock').open('a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        entries = decisions(root, dossier)
        sequence = len(entries)+1
        previous = sha(root/'decisions'/f'{sequence-1:06d}.json') if entries else sha(root/'dossier.json')
        entry = dict(schema='uncertainty-review-decision-v1', sequence=sequence, previous_sha256=previous,
                     dossier_sha256=sha(root/'dossier.json'), packet=packet_data, submission=submission,
                     imported_at=now_utc(), import_attribution='Supplied review; not newly detected by this importer.',
                     input_sha256=sha(submission_path))
        apply(dossier, entries+[entry])
        save(root/'decisions'/f'{sequence:06d}.json', entry)
        return entry
