"""Read-only facts for final_state and its deterministic text projection.

No saved results snapshot, prose assessment, filesystem mtime or current-code
approval is used as evidence of historical execution.
"""
from pathlib import Path
from datetime import datetime
import base64
import json
from typing import Any
import pymupdf as fitz
from .io import load, sha, safe, require, digest, strict, SETTINGS, LIMIT

PHASES = ('initial', 'classification', 'association')
INITIAL = ('caption', 'figure', 'structured')
NOT_RECORDED = 'not-recorded'


class Evidence:
    """Retain hashes of actually read inputs; detect changes during reporting."""
    def __init__(self, root):
        self.root = Path(root)
        self.files = {}

    def file(self, name):
        p = safe(self.root, name)
        value = sha(p)
        require(name not in self.files or self.files[name] == value, 'evidence-changed:' + name)
        self.files[name] = value
        return p

    def json(self, name):
        p = self.file(name)
        value = load(p)
        require(sha(p) == self.files[name], 'evidence-changed:' + name)
        return value

    def check(self):
        for name, value in self.files.items():
            require(sha(safe(self.root, name)) == value, 'evidence-changed:' + name)


def source_facts(evidence):
    manifest = evidence.json('manifest.json')
    require(manifest['schema'] == 'pdf-source-package-v1' and manifest['documents'], 'manifest-schema')
    require(manifest['settings'] == SETTINGS, 'manifest-settings')
    require(len({d['identity'] for d in manifest['documents']}) == len(manifest['documents']), 'duplicate-document')
    pages = dict(original_retained=0, inventoried=0, native_inventory_failures=0, rendered=0)
    for doc in manifest['documents']:
        source = evidence.file(doc['raw'])
        require(evidence.files[doc['raw']] == doc['sha256'], 'source-hash-mismatch')
        with fitz.open(source) as pdf:
            count = len(pdf)
        require(count == doc['page_count'], 'source-page-count')
        require(evidence.json(doc['directory'] + '/document.json') == doc, 'document-manifest-mismatch')
        require([p['page'] for p in doc['pages']] == list(range(1, count + 1)), 'page-inventory-range')
        require([p['page'] for p in doc['pages'] if p['selected']] == doc['selected_pages'], 'selected-page-mismatch')
        pages['original_retained'] += count
        for page in doc['pages']:
            directory = page['directory']
            ci = evidence.json(directory + '/caption-inventory.json')
            require(ci['page'] == page['page'] and ci['source_sha256'] == doc['sha256'], 'caption-inventory-identity')
            evidence.json(page['native_text'])
            evidence.file(directory + '/native-text.txt')
            require(evidence.json(directory + '/reporting-policy.json') == page['policy'], 'policy-mismatch')
            if page['source_limitation']:
                evidence.json(directory + '/inventory-failure.json')
                pages['native_inventory_failures'] += 1
            else:
                inv = evidence.json(directory + '/inventory.json')
                require(inv['page'] == page['page'] and inv['source_sha256'] == doc['sha256'], 'native-inventory-identity')
                pages['inventoried'] += 1
            image = evidence.file(page['page_image'])
            from PIL import Image
            with Image.open(image) as im:
                im.verify()
            pages['rendered'] += 1
    return manifest, pages


def count_record(value, request_hash):
    require(value['request_sha256'] == request_hash, 'count-request-binding')
    n = value['prompt_tokens_local']
    require(type(n) is int and n > 0, 'invalid-count')
    require(value.get('reserved_completion_tokens', 65536) == SETTINGS['max_tokens'] and
            value.get('context_limit', LIMIT) == LIMIT, 'count-settings')
    require(value['fits'] is (n + SETTINGS['max_tokens'] <= LIMIT), 'count-fit-contradiction')


def recorded_time(value):
    if value is None or value == NOT_RECORDED:
        return NOT_RECORDED
    require(isinstance(value, str), 'runtime-timestamp-type')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(parsed.tzinfo is not None and parsed.utcoffset().total_seconds() == 0, 'runtime-timestamp-not-utc')
    return value


def reduction(evidence, row, wire):
    directory = row['directory']
    prefix = ('whole-document' if row.get('representation') == 'candidate-page-images-full-native' else
              'compact-flat' if row.get('representation') == 'native-clip-units-after-measured-overflow' else None)
    if prefix is None:
        require(not any((evidence.root / directory / (p + '-count.json')).exists()
                        for p in ('whole-document', 'compact-flat')), 'unreported-overflow-reduction')
        return None
    old = evidence.json(directory + '/' + prefix + '-count.json')
    old_wire = evidence.json(directory + '/' + prefix + '-wire.json')
    count_record(old, evidence.files[directory + '/' + prefix + '-wire.json'])
    require(old['fits'] is False, 'reduction-without-measured-overflow')
    value = dict(request_id=row['id'], document=row['document'], phase=row['phase'],
                 original_prompt_tokens=old['prompt_tokens_local'], final_prompt_tokens=row['count']['prompt_tokens_local'],
                 reserved_completion_tokens=SETTINGS['max_tokens'], context_limit=LIMIT, measured_overflow=True,
                 original_request_sha256=old['request_sha256'], final_request_sha256=row['request_sha256'],
                 final_fits=row['count']['fits'], representation=row['representation'])
    if row['channel'] == 'association':
        scope = association_scope(evidence, row, wire)
        old_scope = association_scope(evidence, row, old_wire)
        value.update(association_image_scope=scope, original_association_image_scope=old_scope)
    return value


def association_scope(evidence, row, wire):
    content = wire['messages'][0]['content']
    data = strict(content[0]['text'].split('\nSOURCE EVIDENCE\n', 1)[1])
    included, omitted = data['source_physical_pages'], data['image_omitted_pages']
    doc = next(d for d in evidence.json('manifest.json')['documents'] if d['identity'] == row['document'])
    require(len(set(included + omitted)) == len(included + omitted) == doc['page_count'] and
            set(included + omitted) == set(range(1, doc['page_count'] + 1)), 'association-image-page-scope')
    images = [p['image_url']['url'] for p in content if p['type'] == 'image_url']
    require(len(images) == len(included), 'association-image-count')
    for n, image in zip(included, images):
        page = next(p for p in doc['pages'] if p['page'] == n)
        evidence.file(page['page_image'])
        require(digest(base64.b64decode(image.split(',', 1)[1], validate=True)) == evidence.files[page['page_image']],
                'association-image-binding')
    return dict(mode=data['visual_context_mode'], included_image_pages=included, omitted_image_pages=omitted)


def call_evidence(evidence, row, wire):
    from .workflow import output_bindings
    directory = row['directory']
    call_name, reservation_name = directory + '/call.json', directory + '/reservation.json'
    call = evidence.json(call_name) if (evidence.root / call_name).exists() else {}
    reserved = (evidence.root / reservation_name).exists()
    if reserved:
        reservation = evidence.json(reservation_name)
        require(reservation['request_sha256'] == row['request_sha256'], 'reservation-request-binding')
    if call:
        require(reserved and call['request_sha256'] == row['request_sha256'] and call['phase'] == row['phase'], 'call-request-binding')
        require(call['transport_origin'] == reservation['transport_origin'], 'call-origin-binding')
    binding_path = directory + '/output-bindings.json'
    bound = (evidence.root / binding_path).exists()
    if bound:
        bindings = evidence.json(binding_path)
        require(bool(call) and bindings == output_bindings(evidence.root, directory), 'output-bindings-incomplete-or-changed')
        for name, value in bindings.items():
            evidence.file(name)
            require(evidence.files[name] == value, 'output-binding')
    returned = NOT_RECORDED
    response_name = directory + '/response-body.json'
    if (evidence.root / response_name).exists():
        evidence.file(response_name)
        if bound:
            require(evidence.files[response_name] == call['saved_response_sha256'], 'response-binding')
        try:
            env = evidence.json(response_name)
            returned = env.get('model', NOT_RECORDED) if isinstance(env, dict) else NOT_RECORDED
        except (ValueError, UnicodeError):
            require(not call.get('complete'), 'invalid-completed-response')
    if call.get('actual_model'):
        require(call['actual_model'] == returned, 'returned-model-contradiction')
    if call.get('complete'):
        require(bound and call.get('attempted') is True and call.get('status') == 'response-received' and
                call.get('http_status') == 200 and returned == wire['model'], 'completed-call-evidence')
        require(env['choices'][0]['finish_reason'] == 'stop', 'completed-response-finish')
        if row['channel'] in INITIAL:
            evidence.json(directory + '/decoded.json')
            candidates = evidence.json(directory + '/candidates.json')
            require(call['candidate_count'] == len(candidates), 'candidate-count-contradiction')
            require(call['crop_count'] == sum(len(c['regions']) for c in candidates), 'crop-count-contradiction')
            for candidate in candidates:
                for region in candidate['regions']:
                    evidence.file(region['crop'])
                    require(evidence.files[region['crop']] == region['crop_sha256'], 'candidate-crop-binding')
        else:
            evidence.json(directory + '/validation.json')
        evidence.json(directory + '/raw-selection.json')
    return call, reserved, bound, returned


def basic_phase(evidence, phase):
    path = evidence.root / f'{phase}-plan.json'
    if not path.exists():
        return dict(status='not-prepared', planned=0, attempted=0, completed=0,
                    failed=0, unattempted=0, uncertain_reservations=0, fresh_calls=0,
                    fixture_or_replay_calls=0), []
    plan = evidence.json(path.name)
    require(plan['phase'] == phase, 'plan-phase-mismatch')
    rows = plan['requests']
    require(len({r['id'] for r in rows}) == len(rows), 'duplicate-request')
    manifest = evidence.json('manifest.json')
    if phase == 'initial':
        declared = {(r['id'], d['identity'], p['page'], ch) for d in manifest['documents'] for p in d['pages']
                    for ch,r in p['requests'].items() if 'id' in r}
        require(declared == {(r['id'],r['document'],r['page'],r['channel']) for r in rows}, 'plan-scope-mismatch')
    counts: dict[str, Any] = dict(status='prepared', planned=len(rows), attempted=0, completed=0,
                  failed=0, unattempted=0, uncertain_reservations=0, fresh_calls=0,
                  fixture_or_replay_calls=0)
    records = []
    for row in rows:
        directory = row['directory']
        require(row['phase'] == phase, 'request-phase')
        wire = evidence.json(directory + '/request-wire.json')
        require(evidence.files[directory + '/request-wire.json'] == row['request_sha256'], 'request-binding')
        require({k:v for k,v in wire.items() if k != 'messages'} == SETTINGS, 'request-settings')
        if row.get('count') is not None:
            value = evidence.json(directory + '/count.json')
            require(value == row['count'], 'count-plan-contradiction')
            count_record(value, row['request_sha256'])
            require(row['status'] == ('ready' if value['fits'] else 'preflight-context-overflow'), 'count-status-contradiction')
        else:
            require(row['status'] == 'uncounted', 'missing-count')
        call, reserved, bound, returned = call_evidence(evidence, row, wire)
        completed = call.get('complete') is True
        attempted = call.get('attempted') is True
        uncertain = reserved and (not bound or not call or call.get('status') == 'in-flight')
        counts['attempted'] += attempted
        counts['completed'] += completed
        counts['failed'] += attempted and not completed and not uncertain
        counts['unattempted'] += not attempted and not reserved
        counts['uncertain_reservations'] += uncertain
        fresh = call.get('transport_origin') == 'parent-authorized-live' and not evidence.json('manifest.json')['fixture']
        counts['fresh_calls'] += attempted and fresh
        counts['fixture_or_replay_calls'] += attempted and not fresh
        records.append(dict(id=row['id'], phase=phase, document=row['document'], page=row['page'], channel=row['channel'],
                            attempted=attempted, completed=completed, uncertain_reservation=uncertain,
                            requested_model=wire['model'], returned_model=returned,
                            started_at=recorded_time(call.get('started_at')), ended_at=recorded_time(call.get('ended_at')),
                            transport_origin=call.get('transport_origin', NOT_RECORDED),
                            overflow_reduction=reduction(evidence, row, wire),
                            association_image_scope=association_scope(evidence, row, wire) if row['channel'] == 'association' else None))
    seal_name = f'{phase}-seal.json'
    if (evidence.root / seal_name).exists():
        seal = evidence.json(seal_name)
        require(seal['phase'] == phase and seal['schema'] == 'pdf-phase-seal-v1', 'seal-phase')
        required = {f'{phase}-plan.json', 'manifest.json'} | set(plan['dependencies'])
        for row in rows:
            required.update(row['inputs'])
            required.update(row['directory'] + '/' + n for n in ('request-wire.json', 'count.json'))
        require(required <= set(seal['files']), 'seal-missing-inputs')
        for name, value in seal['files'].items():
            evidence.file(name)
            require(evidence.files[name] == value, 'sealed-input-changed:' + name)
        counts['status'] = 'sealed'
        counts['code_binding'] = 'recorded-seal-code-not-current-live-authorization'
    complete_name = f'{phase}-complete.json'
    counts['started_at'] = (recorded_time(evidence.json(f'{phase}-session.json').get('started_at'))
                            if (evidence.root/f'{phase}-session.json').exists() else NOT_RECORDED)
    counts['ended_at'] = NOT_RECORDED
    if (evidence.root / complete_name).exists():
        marker = evidence.json(complete_name)
        # A later phase's shared stop cannot rewrite this phase's history.
        complete = counts['completed'] == len(rows) and all(r['status'] == 'ready' for r in rows)
        require(marker['all_requested_complete'] is complete, 'completion-marker-contradiction')
        if marker.get('transport_origin') == 'deterministic-empty':
            require(not rows and marker['seal_sha256'] == evidence.files[seal_name], 'empty-completion-binding')
            require(not (evidence.root/f'{phase}-session.json').exists() and not (evidence.root/f'{phase}-approval.json').exists(), 'empty-phase-has-execution')
            counts.update(status='complete', ended_at=recorded_time(marker.get('ended_at')))
            return counts, records
        session = evidence.json(f'{phase}-session.json')
        require(session['phase'] == phase and session['origin'] == marker['transport_origin'], 'completion-session-binding')
        approval = evidence.json(f'{phase}-approval.json')
        require(session['approval_sha256'] == evidence.files[f'{phase}-approval.json'], 'session-approval-binding')
        require(approval['seal_sha256'] == evidence.files[seal_name], 'approval-seal-binding')
        require(approval['code'] == seal['code'], 'historical-approval-code-binding')
        counts['status'] = 'complete' if complete else 'incomplete'
        counts['ended_at'] = recorded_time(marker.get('ended_at'))
    return counts, records


def inspection_facts(targets, inspection_dir):
    result: dict[str, Any] = dict(status='not-supplied', calls=None, fresh_calls=None, fixture_or_replay_calls=None,
        completed_findings=None, uncertain_reservations=None, records=[], covered_crop_files=None,
        uncovered_crop_files=None, covered_source_files=None, uncovered_source_files=None,
        findings='model-observations-not-human-acceptance', coverage_basis='exact-image-sha256-not-labels-or-findings')
    if inspection_dir is None:
        return result
    root = Path(inspection_dir)
    if not root.is_dir():
        result['status'] = 'directory-missing'
        return result
    # Explicit directory only; do not search siblings or read assessment prose.
    directories = sorted({p.parent for name in ('input.json', 'result.json', 'attempt.json', 'post-reserved.json')
                          for p in root.rglob(name)})
    if not directories:
        result['status'] = 'no-records'
        return result
    result.update(status='verified-records', calls=0, fresh_calls=0, fixture_or_replay_calls=0,
                  completed_findings=0, uncertain_reservations=0)
    covered = set()
    for directory in directories:
        evidence = Evidence(directory)
        inp = evidence.json('input.json') if (directory/'input.json').exists() else None
        out = evidence.json('result.json') if (directory/'result.json').exists() else None
        reserved = evidence.json('post-reserved.json') if (directory/'post-reserved.json').exists() else None
        row = dict(directory=str(directory), status=out.get('status') if out else 'result-not-recorded',
                   requested_model=NOT_RECORDED, returned_model=NOT_RECORDED, input_sha256=[],
                   started_at=out.get('timestamp', NOT_RECORDED) if out else NOT_RECORDED,
                   ended_at=out.get('completed_at', NOT_RECORDED) if out else NOT_RECORDED)
        if inp:
            images = inp['images']
            require(isinstance(images, list) and images, 'inspection-images-empty')
            content = [dict(type='text', text=inp['question'])]
            hashes = []
            for image in images:
                raw = evidence.file(image['evidence_file']).read_bytes()
                require(digest(raw) == image['sha256'] and len(raw) == image['bytes'], 'inspection-image-binding')
                hashes.append(image['sha256'])
                content.extend([dict(type='text', text=image['label']), dict(type='image_url', image_url=dict(
                    url='data:' + image['mime_type'] + ';base64,' + base64.b64encode(raw).decode('ascii')))])
            require(evidence.json('recipe.json') == inp['recipe'], 'inspection-recipe-binding')
            wire = dict(inp['recipe']['settings'], messages=[dict(role='system', content=inp['prompt']), dict(role='user', content=content)])
            wire_hash = digest(json.dumps(wire, ensure_ascii=True, sort_keys=True, separators=(',', ':')).encode())
            row['requested_model'] = inp['recipe']['settings']['model']
            row['input_sha256'] = hashes
            if reserved:
                require(reserved['request_sha256'] == wire_hash and reserved['images'] == images, 'inspection-reservation-binding')
            if out and out.get('attempted'):
                require(reserved and out['request_sha256'] == wire_hash and out['images'] == images and
                        out['settings'] == inp['recipe']['settings'], 'inspection-result-request-binding')
                covered.update(hashes)
        if out and out.get('attempted'):
            require(inp and reserved, 'inspection-attempt-missing-input')
            result['calls'] += 1
            fixture = out.get('offline_fixture') is True or 'replay' in out.get('transport_origin', '')
            result['fixture_or_replay_calls' if fixture else 'fresh_calls'] += 1
        elif reserved:
            result['uncertain_reservations'] += 1
        if not out:
            result['status'] = 'incomplete-records'
        if out and out.get('status') == 'ok':
            require(out.get('attempted') is True, 'inspection-ok-without-attempt')
            response = evidence.json('response.sanitized.txt')
            require(evidence.files['response.sanitized.txt'] == out['sanitized_response_sha256'], 'inspection-response-binding')
            require(response['model'] == out['returned_model'] == row['requested_model'], 'inspection-model-binding')
            require(len(response['choices']) == 1 and response['choices'][0]['finish_reason'] == 'stop' and
                    response['choices'][0]['message']['content'] == out['findings'], 'inspection-findings-binding')
            result['completed_findings'] += 1
        row['returned_model'] = out.get('returned_model') or NOT_RECORDED if out else NOT_RECORDED
        result['records'].append(row)
        evidence.check()
    for kind, files in targets.items():
        items = [dict(path=name, sha256=value, supplied_as_verified_inspection_input=value in covered)
                 for name, value in sorted(files.items())]
        result[kind + '_files'] = items
        result['covered_' + kind + '_files'] = sum(item['supplied_as_verified_inspection_input'] for item in items)
        # An interrupted record is not proof that the remaining files were never sent.
        result['uncovered_' + kind + '_files'] = (len(items) - result['covered_' + kind + '_files']
                                                 if result['status'] == 'verified-records' else None)
    return result


def facts(root, state, inspection_dir=None):
    evidence = Evidence(root)
    manifest, pages = source_facts(evidence)
    phases, records = {}, []
    for phase in PHASES:
        counts, rows = basic_phase(evidence, phase)
        phases[phase] = counts
        records.extend(rows)
    initial = [r for r in records if r['phase'] == 'initial']
    selected = {(d['identity'], p['page']) for d in manifest['documents'] for p in d['pages'] if p['selected']}
    completed = {(r['document'], r['page']) for r in initial if r['completed']}
    attempted = {(r['document'], r['page']) for r in initial if r['attempted']}
    pairs = sum(len(set(d['channels']) & set(INITIAL)) for d in manifest['documents'] for p in d['pages'] if p['selected'])
    # A completed physical page means all requested extraction channels completed;
    # policy exclusions are not silently called model extraction completions.
    complete_pages = sum(all(p['outcomes'][ch] == 'complete' for ch in p['outcomes']) and bool(p['outcomes'])
                         for d in state['documents'] for p in d['pages'] if p['selected'])
    crops = sorted({name for d in state['documents'] for r in d['requests'] for name in r['files']
                    if '/crops/' in name and name.endswith('.png') and not Path(name).stem.startswith('overview')})
    for name in crops:
        evidence.file(name)
    executed = [v for p,v in phases.items() if (evidence.root/f'{p}-session.json').exists()]
    started = [v.get('started_at', NOT_RECORDED) for v in executed]
    ended = [v.get('ended_at', NOT_RECORDED) for v in executed]
    result = dict(schema='pdf-artifact-facts-v1', fixture=manifest['fixture'], evidence_status='verified',
                  requested_work_complete=state['requested_work_complete'], human_acceptance=state['human_acceptance'],
                  exhaustive_extraction_established=state['exhaustive_extraction_established'], pages=pages,
                  extraction=dict(physical_pages_selected=len(selected), physical_pages_attempted=len(attempted),
                      physical_pages_with_completed_channel=len(completed), physical_pages_completed=complete_pages,
                      channel_pairs_selected=pairs, channel_pairs_planned=len(initial),
                      channel_pairs_attempted=sum(r['attempted'] for r in initial),
                      channel_pairs_completed=sum(r['completed'] for r in initial)),
                  phases=phases, requests=records, crop_files=len(crops),
                  overflow_reductions=[r['overflow_reduction'] for r in records if r['overflow_reduction']],
                  runtime=dict(started_at=min(started) if started and NOT_RECORDED not in started else NOT_RECORDED,
                               ended_at=max(ended) if ended and NOT_RECORDED not in ended else NOT_RECORDED,
                               scope='Recorded execution phase clocks only; not preparation, file dates or reservation times.'),
                  inspection=inspection_facts(dict(crop={name:evidence.files[name] for name in crops},
                      source={p['page_image']:evidence.files[p['page_image']] for d in manifest['documents'] for p in d['pages']}), inspection_dir))
    evidence.check()
    state['artifact_bindings'] = dict(evidence.files)
    return result


def summary_models(rows):
    return {label: sorted({r[key] for r in rows}) for label, key in
            (('requested', 'requested_model'), ('returned', 'returned_model'))}


def summary_clocks(rows):
    result = {}
    for key in ('started_at', 'ended_at'):
        recorded = [r[key] for r in rows if r.get(key, NOT_RECORDED) != NOT_RECORDED]
        result[key] = dict(recorded=len(recorded), not_recorded=len(rows) - len(recorded),
                           earliest_recorded=min(recorded) if recorded else NOT_RECORDED,
                           latest_recorded=max(recorded) if recorded else NOT_RECORDED)
    return result


def summary_image_scope(scopes):
    # Fixed-size ranges, never a list of source pages or image hashes.
    return dict(requests=len(scopes), modes=sorted({s['mode'] for s in scopes}),
                **{key: [min(len(s[key]) for s in scopes), max(len(s[key]) for s in scopes)]
                   for key in ('included_image_pages', 'omitted_image_pages')})


def factual_summary(value):
    """Concise deterministic projection of facts, not a second evidence state.

    Line count scales with phases/documents, never with request/page/image rows.
    Each labelled line has one JSON value for exact projection tests. Ranges
    aggregate multiple reductions without discarding original overflow counts.
    """
    lines = ['PDF artifact facts — concise overview']
    def emit(label, item):
        lines.append(label + ': ' + json.dumps(item, ensure_ascii=True, sort_keys=True))
    emit('Evidence', {k: value[k] for k in ('schema', 'evidence_status', 'fixture')})
    for label, key in (('Requested work complete', 'requested_work_complete'), ('Human acceptance', 'human_acceptance'),
                       ('Exhaustive extraction established', 'exhaustive_extraction_established'), ('Source pages', 'pages')):
        emit(label, value[key])
    emit('Extraction physical pages', {k:v for k,v in value['extraction'].items() if k.startswith('physical_')})
    emit('Extraction channel pairs', {k:v for k,v in value['extraction'].items() if k.startswith('channel_')})
    emit('Crop files', value['crop_files'])
    counts = ('planned', 'attempted', 'completed', 'failed', 'unattempted', 'uncertain_reservations',
              'fresh_calls', 'fixture_or_replay_calls')
    emit('Workflow calls (all phases)', {k: sum(p[k] for p in value['phases'].values()) for k in counts})
    for phase in PHASES:
        phase_value = value['phases'][phase]
        rows = [r for r in value['requests'] if r['phase'] == phase]
        emit(f'Phase {phase} calls', {k:phase_value[k] for k in ('status', *counts)})
        emit(f'Phase {phase} models', summary_models(rows))
        emit(f'Phase {phase} runtime', dict(started_at=phase_value.get('started_at', NOT_RECORDED),
            ended_at=phase_value.get('ended_at', NOT_RECORDED), calls=summary_clocks(rows)))
        emit(f'Phase {phase} code binding', phase_value.get('code_binding', NOT_RECORDED))
    emit('Runtime', value['runtime'])
    reductions = value['overflow_reductions']
    emit('Measured overflow reductions', len(reductions))
    for document, phase in sorted({(r['document'], r['phase']) for r in reductions}):
        rows = [r for r in reductions if (r['document'], r['phase']) == (document, phase)]
        emit(f'Overflow {document} / {phase}', dict(requests=len(rows),
            measured_overflow=sum(r['measured_overflow'] for r in rows), final_fits=sum(r['final_fits'] for r in rows),
            **{k:[min(r[k] for r in rows), max(r[k] for r in rows)] for k in
               ('original_prompt_tokens', 'final_prompt_tokens', 'reserved_completion_tokens', 'context_limit')}))
        scopes = [r for r in rows if r.get('association_image_scope')]
        if scopes:
            emit(f'Overflow image scope {document} / {phase}',
                 dict(original=summary_image_scope([r['original_association_image_scope'] for r in scopes]),
                      final=summary_image_scope([r['association_image_scope'] for r in scopes])))
    association = [r for r in value['requests'] if r.get('association_image_scope')]
    for document in sorted({r['document'] for r in association}):
        emit(f'Association image scope {document}', summary_image_scope(
            [r['association_image_scope'] for r in association if r['document'] == document]))
    inspection = value['inspection']
    emit('Inspection status', inspection['status'])
    emit('Inspection calls', {k:inspection[k] for k in
        ('calls', 'fresh_calls', 'fixture_or_replay_calls', 'completed_findings', 'uncertain_reservations')})
    for kind in ('crop', 'source'):
        emit(f'Inspection {kind} inputs', {k:inspection[f'{k}_{kind}_files'] for k in ('covered', 'uncovered')})
    emit('Inspection models', summary_models(inspection['records']))
    emit('Inspection runtime', summary_clocks(inspection['records']))
    emit('Inspection findings', inspection['findings'])
    emit('Inspection coverage basis', inspection['coverage_basis'])
    emit('Unknown coverage caveat', 'null means not measured/unknown, not zero or proven uncovered.')
    emit('Range caveat', '[min, max] counts summarize requests per document/phase; image counts are inputs, not extraction coverage. Full rows and hashes remain in facts.json.')
    emit('Completion caveat', 'Mechanical completion is not exhaustive extraction or human acceptance; inspection findings are model observations, not human verdicts.')
    emit('Historical caveat', 'Fresh-call counts describe recorded non-fixture execution, not new calls by this report. Recorded seals are not current live approval. Missing clocks remain not-recorded.')
    return '\n'.join(lines) + '\n'
