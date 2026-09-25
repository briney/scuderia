"""Shared decoding/export path for actual responses and explicitly bound replay."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import time
import urllib.error
import urllib.request
import socket
import os
from .io import *
from . import native, compact, grouped, caption, recovery, classification, association, gates


def runtime_timestamp():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def http_stops(status, raw):
    text = raw.decode('utf-8', errors='replace').lower()
    markers = ('invalid_api_key','invalid api key','authentication','unauthorized','invalid model name',
        'model_not_found','model not found','unknown model','model does not exist','no available deployment',
        'no deployments available','model route','model group not found')
    return any(s in text for s in markers) or status not in (200,400,413,422)


def exception_result(exc):
    reason = exc.reason if isinstance(exc, urllib.error.URLError) else exc
    timeout = isinstance(reason, (TimeoutError, socket.timeout))
    return dict(status='transport-timeout' if timeout else 'transport-failure',
                stop_pending=not timeout, error_type=type(reason).__name__)


class LiveTransport:
    origin = 'parent-authorized-live'
    def __init__(self, manifest):
        require(not os.environ.get('PDF_SOURCE_PACKAGE_OFFLINE'), 'offline-live-forbidden')
        self.endpoint = manifest['endpoint']
        self.key = os.environ.get(manifest['credential_env'])
        require(bool(self.key), 'runtime-credential-unavailable')

    def __call__(self, payload, row, before_post):
        opener = urllib.request.build_opener(NoRedirect(), urllib.request.ProxyHandler({}))
        req = urllib.request.Request(self.endpoint, data=payload, method='POST',
            headers={'Content-Type':'application/json', 'Authorization':'Bearer ' + self.key})
        try:
            before_post()
            with opener.open(req, timeout=TIMEOUT) as response:
                status, raw = response.status, response.read()
        except urllib.error.HTTPError as exc:
            status, raw = exc.code, exc.read()
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
            return exception_result(exc)
        original = digest(raw)
        raw, redacted = compact.redact_response(raw, self.key)
        return dict(http_status=status, raw=raw, original_response_sha256=original, credential_echo_redacted=redacted)


class ReplayTransport:
    origin = 'historical-saved-response-replay'
    def __init__(self, manifest):
        self.manifest_path = Path(manifest)
        self.manifest = load(manifest)
        require(self.manifest['provenance'] == self.origin, 'explicit-historical-provenance-required')
        self.bindings = {r['request_id']: r for r in self.manifest['responses']}
        require(len(self.bindings) == len(self.manifest['responses']), 'duplicate-replay-request')
        self.used = set()

    def __call__(self, payload, row):
        require(row['id'] not in self.used, 'replay-one-attempt')
        bound = self.bindings[row['id']]
        require(digest(payload) == bound['prepared_request_sha256'], 'replay-request-binding')
        require(bound['historical_source_sha256'] == row['source_sha256'], 'replay-source-binding')
        require(bound['historical_provenance'].strip(), 'historical-provenance-required')
        p = self.manifest_path.parent / bound['response']
        raw = p.read_bytes()
        require(digest(raw) == bound['response_sha256'], 'replay-response-binding')
        self.used.add(row['id'])
        return dict(http_status=bound['http_status'], raw=raw, original_response_sha256=digest(raw),
                    credential_echo_redacted=False, historical_provenance=bound['historical_provenance'])


def envelope(raw):
    env = strict(raw)
    require(isinstance(env, dict), 'response-root')
    require(env.get('model') == SETTINGS['model'], 'response-model-mismatch')
    choices = env.get('choices')
    require(isinstance(choices, list) and len(choices) == 1, 'response-choices')
    choice = choices[0]
    require(choice.get('finish_reason') == 'stop', 'non-stop-finish-reason')
    text = choice['message'].get('content')
    require(isinstance(text,str) and text.strip(), 'response-content')
    return text, env


def normalize_candidates(cs, row, channel, origin, root):
    for c in cs:
        c['original_id'] = c['id']; c['id'] = row['document'] + '::' + channel + '::' + c['id']
        c.update(origin=origin, extraction_origin=origin, associated_label=None, availability='available', disposition='eligible',
                 human_acceptance='pending', detector_family=channel, provenance=[dict(origin=origin, request_id=row['id'])])
        c['observed_labels'] = association.leading_labels(c['native_text'])
        if channel == 'figure':
            c.update(content_type='figure', type_origin='native-figure-selector-observation')
        elif channel == 'structured':
            c.update(content_type='unknown', type_origin='structured-localizer-unclassified')
        else:
            typ = association.label_key(c['observed_labels'][0]['label'])[1] if c['observed_labels'] else 'unknown'
            c.update(content_type=typ, type_origin='native-printed-caption-namespace' if c['observed_labels'] else 'unlabeled-native-text')
        for i, r in enumerate(c['regions']):
            r['original_fragment_order'] = i
            r['crop_sha256'] = sha(root / r['crop'])
        c['regions'].sort(key=lambda r: (r['page'],r['bbox'][1],r['bbox'][0],r['id']))
    return cs


def decode_export(root, row, text, origin, response_hash):
    """No source geometry or text generated here; accepted decoders own selection."""
    root = Path(root); p = root / row['directory']; channel = row['channel']
    value = __import__('json').loads(text) if channel == 'caption' else strict(text)
    save(p / 'raw-selection.json', value)
    if channel == 'classification':
        result = classification.classify_validate(value, load(p / 'candidates.json'))
        save(p / 'validation.json', result)
        return dict(selection_status='validated', export_status='not-applicable', complete=True)
    if channel == 'association':
        result = association.validate(value, load(p / 'candidates.json'))
        save(p / 'validation.json', result)
        return dict(selection_status=value['status'], export_status='not-applicable', complete=value['status']=='ok')
    source = root / row['raw']; n = row['page']; cs = []
    if channel == 'caption':
        ci = load(root / row['page_directory'] / 'caption-inventory.json')
        source_sha256 = ci.get('source_sha256') or sha(source)
        result = caption.select(text, ci)
        save(p / 'decoded-before-export.json', result)
        with native.fitz.open(source) as pdf:
            caption.export(pdf[n - 1], result, p / 'crops')
            pix = pdf[n - 1].get_pixmap(dpi=150, alpha=False)
            put(p / 'crops/overview.png', pix.tobytes('png'))
        for oi, obj in enumerate(result['objects'], 1):
            regions = []
            for f in obj['fragments']:
                if f['status'] != 'ok':
                    continue
                regions.append(dict(id=f'p{n:04d}-caption-{oi:03d}-{f["id"]}', page=n, bbox=f['bbox'], coordinate_system=ci['coordinate_system'],
                    original_member_ids=f['line_ids'], lines=copy.deepcopy(f['selected_lines']),
                    crop=row['directory'] + '/crops/' + f['png']))
            if regions:
                cs.append(dict(id=f'p{n:04d}-caption-{oi:03d}', source_document=row['document'], source_sha256=source_sha256,
                    page=n, role='note' if obj['role']=='footnote' else 'caption', original_role=obj['role'], regions=regions,
                    native_text='\n'.join(l['text'] for r in regions for l in r['lines']),
                    model_observed_label=obj['associated_label'], model_uncertainty=obj['uncertainty']))
        status = result['status']; complete = status in ('ok','explicit_empty')
        warnings = result['diagnostics']
    else:
        inv = load(root / row['page_directory'] / 'inventory.json')
        mapping = load(p / 'mapping.json')
        if channel == 'figure':
            mapped = (grouped if 'units' in mapping else compact).alias_to_native(value, inv, mapping)
            regions = native.selected_regions(mapped, inv)
            result = dict(mapped=mapped, regions=regions, warnings=[])
            known = {o['id']:o for o in inv['objects']}
            for gi, group in enumerate(mapped['figures'], 1):
                converted = []
                for r in regions:
                    if r['group'] != gi: continue
                    members = [copy.deepcopy(known[i]) for i in r['object_ids']]
                    converted.append(dict(id=f'p{n:04d}-figure-{gi:03d}-f{r["fragment"]:02d}', page=n, bbox=r['bbox'],
                        coordinate_system=native.COORD, original_member_ids=r['object_ids'], source_members=members,
                        lines=[o for o in members if o['type']=='native-text-line'], crop=row['directory']+'/crops/'+r['png']))
                cs.append(dict(id=f'p{n:04d}-figure-{gi:03d}', role='body', source_document=row['document'], source_sha256=inv['source_sha256'],
                    page=n, regions=converted, native_text='\n'.join(l['text'] for r in converted for l in r['lines']), model_observed_label=group['label']))
        else:
            result = recovery.decode_selection(value, inv, mapping)
            component_row = dict(identity=row['document'], page=n, source_sha256=inv['source_sha256'], directory=row['directory'])
            cs = recovery.components(component_row, result, inv, response_hash, origin=origin)
            for c in cs:
                for r in c['regions']:
                    r['crop'] = r['crop'].replace('/body-exports/', '/crops/')
            regions = result['regions']
        save(p / 'decoded-before-export.json', result)
        native.export(source, n, regions, p / 'crops')
        status = value['status']; complete = status in ('ok','empty')
        if result.get('export_outcome') == 'no-export-all-empty-placeholders':
            status = 'all-empty-placeholders'; complete = False
        warnings = result['warnings']
    save(p / 'decoded.json', result)
    cs = normalize_candidates(cs, row, channel, origin, root)
    save(p / 'candidates.json', cs)
    return dict(selection_status=status, export_status='complete', candidate_count=len(cs),
                crop_count=sum(len(c['regions']) for c in cs), complete=complete, warnings=warnings)


def usage_disposition(expected, actual, live):
    result = dict(expected_prompt_tokens=expected, reported_prompt_tokens=actual, prompt_count_matches=actual == expected)
    if live and actual != expected:
        result.update(complete=False, stop_pending=type(actual) is int,
                      count_diagnostic='actual-count-mismatch' if type(actual) is int else 'count-unavailable')
    if not live:
        result['count_comparison_scope'] = 'historical usage; not evidence of fresh request count agreement'
    return result


def run_phase(root, phase, approval, *, authorize=False, replay=None, transport=None):
    root = Path(root).absolute(); manifest = load(root / 'manifest.json')
    live = replay is None and transport is None
    if live:
        require(authorize is True, 'explicit-authorize-required')
        require(manifest.get('fixture') is False and not (root / 'OFFLINE-FIXTURE').exists(), 'no-fixture-promotion')
        if phase != 'initial':
            from .workflow import collect
            prior_candidates = collect(root)
            require(all(c['extraction_origin'] == 'parent-authorized-live' for cs in prior_candidates.values() for c in cs), 'no-fixture-promotion')
            for prior in ('initial', 'classification'):
                if prior == phase:
                    break
                session = root / f'{prior}-session.json'
                if session.exists():
                    require(load(session)['origin'] == 'parent-authorized-live', 'no-fixture-promotion')
    else:
        require(manifest.get('fixture') is True and (root / 'OFFLINE-FIXTURE').is_file(), 'replay-requires-offline-fixture')
    entry = gates.EntrySnapshot.capture(root, phase, approval)
    require(not (root / f'{phase}-session.json').exists(), 'phase-one-attempt-no-resume')
    require(all(not (root / r['directory'] / 'reservation.json').exists() for r in entry.rows), 'consumed-reservation')
    if live: transport = LiveTransport(manifest)
    elif replay is not None: transport = ReplayTransport(replay)
    origin = transport.origin
    save(root / f'{phase}-session.json', dict(phase=phase, origin=origin, approval_sha256=digest(entry.approval_bytes), pid=os.getpid(), started_at=runtime_timestamp()))
    put(root / f'{phase}-approval.json', entry.approval_bytes)
    good = True
    for saved_row in entry.rows:
        if (root / 'stop.json').exists(): good=False; break
        row = copy.deepcopy(saved_row)
        # Source hash passed to replay is derived from retained source, not expectations.
        source_doc = next(d for d in manifest['documents'] if d['identity']==row['document'])
        gates.reserve(entry, saved_row, origin)
        p = root / row['directory']; payload = (p / 'request-wire.json').read_bytes()
        entry.check(saved_row, payload)
        row['source_sha256'] = source_doc['sha256']
        call = dict(attempted=True, status='in-flight', selection_status='unattempted', export_status='unattempted',
            complete=False, transport_origin=origin, request_sha256=digest(payload), retries=0, timeout_seconds=TIMEOUT,
            approval_sha256=digest(entry.approval_bytes), phase=phase, started_at=runtime_timestamp())
        save(p / 'call.json', call)
        started = time.monotonic()
        entry.check(saved_row, payload)
        try:
            received = transport(payload, row, lambda: entry.check(saved_row, payload)) if live else transport(payload, row)
        except (urllib.error.URLError,TimeoutError,ConnectionError,OSError) as exc:
            received = exception_result(exc)
        raw = received.pop('raw', None)
        call.update(received, latency_seconds=time.monotonic()-started)
        if raw is not None:
            put(p / 'response-body.json', raw)
            call['saved_response_sha256'] = digest(raw)
            if received['http_status'] != 200:
                call.update(status='http-failure',stop_pending=http_stops(received['http_status'],raw))
            else:
                call['status'] = 'response-received'
                try:
                    env = strict(raw)
                    model = env.get('model') if isinstance(env,dict) else None
                    # Count failures remain shared even if selection decoding fails.
                    usage = env.get('usage') if isinstance(env, dict) else None
                    actual = usage.get('prompt_tokens') if isinstance(usage, dict) else None
                    count_state = usage_disposition(row['count']['prompt_tokens_local'], actual, live)
                    call.update(count_state)
                    if isinstance(model,str) and model.strip() and model != SETTINGS['model']:
                        call['stop_pending'] = True
                    text, env = envelope(raw)
                    call.update(actual_model=env['model'], usage=env.get('usage'), finish_reason=env['choices'][0]['finish_reason'])
                    call['export_status'] = 'pending'
                    call.update(decode_export(root,row,text,origin,digest(raw)))
                    call.update(count_state)
                except (ValueError,KeyError,TypeError,IndexError,UnicodeError,AssertionError,OSError) as exc:
                    if hasattr(exc,'evidence'): save(p / 'decoder-failure.json', exc.evidence)
                    call.update(status='decode-or-export-failure', diagnostic=str(exc), complete=False,
                                export_status='partial-or-failed' if (p/'crops').exists() else 'not-exported')
        if call.get('stop_pending'):
            save(root / 'stop.json', dict(request_id=row['id'], reason='shared-auth-route-gateway-dns-model-or-count-failure'))
        call['ended_at'] = runtime_timestamp()
        save(p / 'call.json', call, replace=True)
        from .workflow import output_bindings
        save(p / 'output-bindings.json', output_bindings(root, row['directory']))
        good = good and call['complete']
        print(__import__('json').dumps(dict(phase=phase,id=row['id'],status=call['status'],complete=call['complete'])), flush=True)
    plan = strict(entry.plan_bytes)
    good = good and all(r['status']=='ready' for r in plan['requests'])
    save(root / f'{phase}-complete.json', dict(phase=phase, all_requested_complete=good, transport_origin=origin, ended_at=runtime_timestamp()))
    return 0 if good else 1
