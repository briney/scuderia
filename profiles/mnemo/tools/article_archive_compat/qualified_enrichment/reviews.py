"""Historical read-only dependency closure; extracted without changing validation contracts."""
import copy
import json
from .records import nodes, finding, project, require, digest, related, resolve_pointer
from .storage import absolute, sha
ASPECTS = ('content', 'source-association', 'notation', 'layout', 'units', 'headers')
NOTICE = 'Reference and literal-selection validation is not scientific verification. Empty findings do not establish correctness. Native text does not establish layout or typography; model readings have no automatic precedence.'

def table_summary(record):
    cells = record.get('cells', [])
    return dict(cell_count=len(cells), populated_count=sum((c.get('raw_value') is not None and c.get('raw_value') != '' for c in cells)), blank_count=sum((c.get('status') == 'blank' for c in cells)), unreadable_count=sum((c.get('status') == 'unreadable' for c in cells)), unresolved_count=sum((c.get('status') == 'unresolved' for c in cells)), status=record.get('status'), complete=record.get('complete'), provenance_notes=copy.deepcopy(record.get('provenance_notes', [])))

def policy(dossier):
    require(dossier.get('schema') in (None, 'portable-review-dossier-v2', 'portable-review-dossier-v3', 'uncertainty-dossier-v1', 'uncertainty-dossier-v2'), 'unsupported-dossier-format')
    current = dossier.get('schema') in ('portable-review-dossier-v3', 'uncertainty-dossier-v2')
    if current:
        require(dossier.get('policy') == 'observed-limitations-v1', 'unknown-review-policy')
    else:
        require('policy' not in dossier, 'unknown-review-policy')
    return 'observed-limitations-v1' if current else 'legacy'

def source_files(manifest):
    return [dict(key=f['key'], sha256=f['sha256']) for f in manifest['files'] if f['role'] in ('source-original', 'source-package', 'source-retention')]

def validate_assessment(dossier, value, *, manifest=None, paths=None):
    if value is None:
        return None
    fields = {'usable_evidence', 'reason', 'source_refs', 'unattempted'}
    require(set(value) in (fields, fields | {'source_limitations'}), 'assessment-fields')
    if 'source_limitations' in value:
        require(isinstance(value['source_limitations'], list) and all((isinstance(x, str) and x.strip() for x in value['source_limitations'])), 'source-limitations-shape')
        require(not value['source_limitations'] or value['source_refs'], 'source-limitations-evidence-required')
    require(type(value['usable_evidence']) is bool and isinstance(value['reason'], str) and value['reason'].strip(), 'assessment-reason')
    require(isinstance(value['source_refs'], list) and isinstance(value['unattempted'], dict), 'assessment-evidence-fields')
    from article_archive_compat import portable_articles as pa
    if manifest is None:
        path = absolute(dossier['snapshot']['manifest'])
        require(sha(path) == dossier['snapshot']['manifest_sha256'], 'assessment-manifest-binding')
        (manifest, paths) = pa.verify_local(path, set(pa.local_sources(path)) | {r['key'] for r in value['source_refs']})
    require(dossier['snapshot']['source_files'] == source_files(manifest), 'assessment-source-inventory')
    files = {r['key']: r for r in manifest['files']}
    for ref in value['source_refs']:
        require(set(ref) in ({'key', 'sha256'}, {'key', 'sha256', 'page', 'inspection'}) and ref['key'] in files and (ref['key'] in paths), 'assessment-source-reference')
        record = files[ref['key']]
        path = paths[ref['key']]
        require(record['role'] in ('source-original', 'source-package', 'source-retention') and sha(path) == ref['sha256'] == record['sha256'], 'assessment-source-binding')
        if 'inspection' in ref:
            require(path.suffix.lower() == '.pdf' and type(ref['page']) is int and isinstance(ref['inspection'], str) and ref['inspection'].strip(), 'assessment-inspection-fields')
            import pymupdf
            with pymupdf.open(path) as pdf:
                require(1 <= ref['page'] <= len(pdf), 'assessment-inspection-page')
            continue
        require(path.suffix.lower() in ('.txt', '.md', '.json', '.html', '.csv'), 'assessment-readable-source-required')
        text = path.read_text().strip()
        require(text and text not in ('{}', '[]', 'null'), 'assessment-empty-source')
    require(not value['usable_evidence'] or value['source_refs'], 'assessment-source-evidence-required')
    accounting = dossier.get('request_accounting', dossier['snapshot'].get('request_accounting'))
    pending = {rid for (rid, row) in accounting['requests'].items() if row['status'] == 'pending'}
    pending.update(manifest['source_status'].get('readiness', {}).get('pending', []))
    require(set(value['unattempted']) <= pending and all((isinstance(reason, str) and reason.strip() for reason in value['unattempted'].values())), 'assessment-unattempted-disposition')
    return value

def assessment(dossier, entries, *, manifest=None, paths=None):
    value = None
    limitations = []
    for entry in entries:
        if entry['submission'].get('assessment') is not None:
            value = validate_assessment(dossier, entry['submission']['assessment'], manifest=manifest, paths=paths)
            limitations.extend((x for x in value.get('source_limitations', []) if x not in limitations))
    if limitations:
        value = dict(value, source_limitations=limitations)
    return value

def packet_value(dossier, dossier_hash, elements, max_bytes):
    require(type(max_bytes) is int and 1024 <= max_bytes <= 8000000, 'bounded-packet-size-required')
    require(isinstance(elements, list) and (elements or policy(dossier) != 'legacy') and (len(elements) == len(set(elements))), 'explicit-unique-packet-elements')
    available = {e['element_id']: e for e in dossier['snapshot']['elements']}
    require(set(elements) <= available.keys(), 'unknown-packet-element')
    result = dict(schema='contextual-review-packet-v2' if policy(dossier) != 'legacy' else 'contextual-review-packet-v1', dossier_sha256=dossier_hash, source_package=dossier['snapshot']['source_package'], notice=NOTICE, elements=[dict(available[e], targets=list(nodes(available[e]['outcome'])), automatic_findings=project(available[e], policy=policy(dossier))['findings']) for e in elements])
    if policy(dossier) != 'legacy':
        result['source_files'] = dossier['snapshot']['source_files']
        source = dossier['snapshot'].get('source_readiness')
        if source is not None:
            result['source_readiness'] = source
    require(len((json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()) <= max_bytes, 'packet-too-large-select-fewer-elements')
    return result

def provenance(value):
    require(isinstance(value, dict) and set(value) == {'kind', 'identity', 'model', 'provider', 'check', 'timestamp'}, 'reviewer-provenance-fields')
    require(value['kind'] in ('human', 'orchestrator-import', 'model-operator'), 'reviewer-kind')
    require(all((isinstance(value[k], str) and value[k].strip() for k in ('identity', 'check', 'timestamp'))), 'reviewer-attribution-required')
    if value['kind'] == 'model-operator':
        require(all((isinstance(value[k], str) and value[k].strip() for k in ('model', 'provider'))), 'model-operator-provenance')
    else:
        require(value['model'] is None and value['provider'] is None, 'import-must-not-claim-model-review')

def evidence(element, refs):
    require(isinstance(refs, list), 'evidence-list')
    source = nodes(element['evidence'])
    validated = []
    for ref in refs:
        require(isinstance(ref, dict) and set(ref) <= {'pointer', 'source_sha256', 'kind', 'text', 'start', 'end'}, 'evidence-fields')
        require(ref.get('source_sha256') == element['source_sha256'], 'evidence-source-hash')
        pointer = ref.get('pointer')
        require(pointer in source, 'nonexistent-source-reference')
        value = source[pointer]
        owner_pointer = pointer
        while owner_pointer and (not (isinstance(source[owner_pointer], dict) and 'crop' in source[owner_pointer])):
            owner_pointer = owner_pointer.rsplit('/', 1)[0]
        owner = source[owner_pointer]
        require(isinstance(owner, dict) and 'crop' in owner and ('page' in owner), 'source-reference-without-owner')
        owner_id = owner.get('fragment_id', owner.get('region_id'))
        require(owner_id, 'source-reference-owner-id')
        if ref.get('kind') == 'native-text':
            require(isinstance(value, str) and pointer.endswith(('/text', '/native_text')), 'literal-native-text-reference')
            (start, end) = (ref.get('start', 0), ref.get('end', len(value)))
            require(type(start) is int and type(end) is int and (0 <= start < end <= len(value)), 'literal-selection-range')
            require(ref.get('text') == value[start:end], 'literal-selected-text-mismatch')
        else:
            require(ref.get('kind') == 'crop' and pointer == owner_pointer, 'crop-owner-reference-required')
            require('text' not in ref and 'start' not in ref and ('end' not in ref), 'crop-is-not-literal-text')
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
                if isinstance(ref, str):
                    owners.add(ref)
                elif isinstance(ref, dict):
                    owners.update((ref[k] for k in ('fragment_id', 'source_ref', 'region_id') if isinstance(ref.get(k), str)))
            if owners:
                return owners
        pointer = pointer.rsplit('/', 1)[0]
    return set()

def apply(dossier, decisions, *, manifest=None, paths=None, validate_new=False):
    elements = {e['element_id']: e for e in dossier['snapshot']['elements']}
    views = {key: project(value, policy=policy(dossier)) for (key, value) in elements.items()}
    current = policy(dossier) != 'legacy'
    known = {f['id']: f for v in views.values() for f in v['findings']}
    for entry in decisions:
        submission = entry['submission']
        provenance(submission['reviewer'])
        packet = entry['packet']
        require(packet['schema'] == ('contextual-review-packet-v2' if current else 'contextual-review-packet-v1') and packet['source_package'] == dossier['snapshot']['source_package'] and (packet['notice'] == NOTICE), 'review-packet-source-association')
        require(packet['dossier_sha256'] == entry['dossier_sha256'], 'review-packet-dossier-binding')
        require(submission['schema'] == ('contextual-review-v2' if current else 'contextual-review-v1') and submission['packet_sha256'] == digest(packet), 'review-packet-binding')
        if current:
            require(packet == packet_value(dossier, entry['dossier_sha256'], [e['element_id'] for e in packet['elements']], 8000000), 'altered-review-packet')
        permitted = {e['element_id'] for e in packet['elements']}
        require(permitted <= elements.keys(), 'packet-element-binding')
        for item in packet['elements']:
            expected = dict(elements[item['element_id']], targets=list(nodes(elements[item['element_id']]['outcome'])), automatic_findings=project(elements[item['element_id']], policy=policy(dossier))['findings'])
            require(item == expected, 'altered-review-packet')
        fields = {'schema', 'packet_sha256', 'reviewer', 'findings', 'coverage', 'resolutions'}
        require(set(submission) in (fields, fields | {'assessment'}) if current else set(submission) == fields, 'review-fields')
        if current:
            validate_assessment(dossier, submission.get('assessment'), manifest=manifest, paths=paths)
        for group in ('findings', 'coverage', 'resolutions'):
            require(isinstance(submission[group], list), 'review-list:' + group)
        for item in submission['findings']:
            require(set(item) <= {'element_id', 'source_sha256', 'target', 'category', 'reason', 'stage', 'evidence', 'competing_readings'} and all((k in item for k in ('element_id', 'source_sha256', 'target', 'category', 'reason', 'stage', 'evidence'))), 'finding-fields')
            eid = item['element_id']
            require(eid in permitted, 'finding-outside-packet')
            element = elements[eid]
            require(item['source_sha256'] == element['source_sha256'], 'finding-source-hash')
            target(element, item['target'])
            if validate_new and entry is decisions[-1] and (item['category'] == 'empty-table-extraction'):
                populated = table_summary(element['outcome'].get('record', {}))['populated_count']
                require(populated == 0, 'empty-table-extraction-contradicted:populated=' + str(populated))
            require(all((isinstance(item[k], str) and item[k].strip() for k in ('category', 'reason'))), 'specific-free-text-reason-required')
            require(item['stage'] in ('extraction', 'answer'), 'finding-stage')
            refs = evidence(element, item['evidence'])
            if current:
                require(refs, 'material-finding-evidence-required')
            value = finding(element, item['target'], item['category'], item['reason'], stage=item['stage'], provenance=submission['reviewer'], evidence=refs)
            readings = item.get('competing_readings', [])
            require(isinstance(readings, list), 'competing-readings-list')
            for reading in readings:
                require(set(reading) == {'text', 'evidence'} and isinstance(reading['text'], str) and reading['text'].strip(), 'competing-reading-fields')
                require(evidence(element, reading['evidence']), 'competing-reading-evidence-required')
            value['competing_readings'] = readings
            value['id'] = digest(value)
            require(value['id'] not in known, 'duplicate-finding')
            views[eid]['findings'].append(value)
            known[value['id']] = value
        for item in submission['coverage']:
            require(set(item) == {'element_id', 'target', 'aspect', 'evidence', 'reason'}, 'coverage-fields')
            eid = item['element_id']
            require(eid in permitted, 'coverage-outside-packet')
            element = elements[eid]
            target(element, item['target'])
            require(item['target'].startswith('/record/') and item['aspect'] in ASPECTS, 'scoped-record-coverage-required')
            require(isinstance(item['reason'], str) and item['reason'].strip(), 'coverage-reason-required')
            refs = evidence(element, item['evidence'])
            require(refs, 'coverage-evidence-required')
            if item['aspect'] in ('notation', 'layout', 'headers'):
                require(any((r['kind'] == 'crop' for r in refs)), 'native-text-cannot-prove-layout')
            views[eid]['coverage'].append(dict(item, evidence=refs, reviewer=submission['reviewer']))
        for item in submission['resolutions']:
            require(set(item) == {'finding_id', 'reason', 'basis', 'evidence', 'agreement', 'proposed_value', 'aspect'}, 'resolution-fields')
            require(item['finding_id'] in known, 'resolution-unknown-finding')
            original = known[item['finding_id']]
            eid = original['element_id']
            require(eid in permitted, 'resolution-outside-packet')
            require(isinstance(item['reason'], str) and item['reason'].strip(), 'resolution-reason-required')
            require(item['basis'] in ('literal-copy', 'source-inspection') and item['aspect'] in ASPECTS, 'resolution-basis')
            saved_uncertainty = original['category'] == 'saved-uncertainty' and original['provenance']['kind'] == 'deterministic-check'
            require(not saved_uncertainty or item['basis'] == 'source-inspection', 'saved-uncertainty-requires-source-inspection')
            require(item['agreement'] in ('unambiguous', 'disputed'), 'resolution-agreement')
            refs = evidence(elements[eid], item['evidence'])
            require(refs, 'unsupported-resolution-no-evidence')
            owners = owners_for(elements[eid], original['target'])
            require(owners and {r['owner'] for r in refs} <= owners, 'resolution-wrong-source-association')
            if item['basis'] == 'literal-copy':
                require(item['aspect'] not in ('notation', 'layout', 'headers'), 'native-text-cannot-prove-layout')
                require(len(refs) == 1 and refs[0]['kind'] == 'native-text' and (item['proposed_value'] == refs[0]['text']), 'resolved-copy-must-match-source')
                index = nodes(elements[eid]['outcome'])
                p = original['target']
                native_ids = set()
                native_refs = []
                while p:
                    container = index[p]
                    if isinstance(container, dict) and container.get('source_refs'):
                        native_refs = [r for r in container['source_refs'] if isinstance(r, dict) and 'line_id' in r]
                        native_ids = {r['line_id'] for r in native_refs}
                        break
                    p = p.rsplit('/', 1)[0]
                source_index = nodes(elements[eid]['evidence'])
                p = refs[0]['pointer']
                selected_id = None
                while p:
                    container = source_index[p]
                    if isinstance(container, dict) and 'line_id' in container:
                        selected_id = container['line_id']
                        break
                    p = p.rsplit('/', 1)[0]
                require(native_ids and selected_id in native_ids, 'resolution-wrong-native-source-association')
                selected_start = refs[0].get('start', 0)
                selected_end = refs[0].get('end', len(source_index[refs[0]['pointer']]))
                require(len(native_refs) == 1 and native_refs[0].get('start') == selected_start and (native_refs[0].get('end') == selected_end), 'resolution-ambiguous-native-range-association')
            else:
                require(any((r['kind'] == 'crop' for r in refs)), 'source-inspection-requires-crop')
            original.setdefault('resolutions', []).append(dict(item, evidence=refs, reviewer=submission['reviewer']))
            original['status'] = 'resolved-with-attribution' if item['agreement'] == 'unambiguous' and (not original.get('competing_readings')) and (not saved_uncertainty or set(ASPECTS) <= {r['aspect'] for r in original['resolutions']}) and all((r['agreement'] == 'unambiguous' for r in original['resolutions'])) else 'unresolved'
    for view in views.values():
        proposals = [(f, r) for f in view['findings'] for r in f.get('resolutions', [])]
        for (index, (left, lr)) in enumerate(proposals):
            for (right, rr) in proposals[index + 1:]:
                (lp, rp) = (left['target'], right['target'])
                if not related(lp, rp):
                    continue
                (lv, rv) = (lr['proposed_value'], rr['proposed_value'])
                try:
                    if lp != rp:
                        if rp.startswith(lp + '/'):
                            lv = resolve_pointer(lv, rp[len(lp):])
                        else:
                            rv = resolve_pointer(rv, lp[len(rp):])
                    agrees = digest(lv) == digest(rv)
                except ValueError:
                    agrees = False
                if not agrees:
                    left['status'] = right['status'] = 'unresolved'
        view['review_status'] = 'partially-reviewed' if view['coverage'] else 'unreviewed'
        view['notice'] = NOTICE
    return list(views.values())
