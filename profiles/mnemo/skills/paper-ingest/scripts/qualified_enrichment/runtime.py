"""Read and revalidate frozen v7 evidence; never mutate a consumed run."""
from pathlib import Path
from pdf_enrichment import bindings, importer, live, trusted, requests
from pdf_enrichment.package_io import SourcePackage
from .records import require
from .storage import absolute, tree, load, sha, save, new, code_hashes


def outcomes(run, plan):
    results = importer.outcomes(run, plan)
    counts = live.verify_counts(run, plan, method=trusted.read_method_path()) if (run/'counts.json').exists() else None
    holds = []
    fixture = plan['fixture']
    session = None
    if (run/'execution-session.json').exists():
        session = load(run/'execution-session.json')
        require(counts is not None, 'execution-counts-missing')
        sealed = load(run/'seal.json')
        require(sealed.get('schema') == 'enrichment-seal-v2', 'unsupported-enrichment-seal-format')
        require(all(sealed[k] == plan[k] for k in ('code', 'method', 'source_package', 'fixture')), 'seal-binding')
        for name, expected in sealed['files'].items():
            require(sha(absolute(run/name)) == expected, 'seal-file-changed')
        approval_raw, approval = live._approval(run, run/'executed-approval.json', plan, counts)
        from pdf_enrichment.io import digest as raw_digest
        require(session['approval_sha256'] == raw_digest(approval_raw), 'session-approval-binding')
        require(session['maximum_posts'] == approval['maximum_posts'], 'session-budget-binding')
        require(session['origin'] == ('offline-bounded-fake-transport' if fixture else 'parent-authorized-live'), 'session-route-binding')
        if not (run/'execution-complete.json').exists():
            holds.append('execution-pending-or-possibly-posted')
        else:
            finished = load(run/'execution-complete.json')
            require(finished['origin'] == session['origin'] and finished['results'] == results, 'execution-completion-binding')
            expected = [row['id'] for row in approval['requests']]
            attempted = finished['attempted']
            require(attempted == expected[:len(attempted)] and attempted, 'execution-attempt-order')
            require(set(results) == set(attempted), 'execution-outcome-roster')
            require(len(attempted) == len(expected) or results[attempted[-1]]['status'] == 'failed', 'execution-unexplained-shortfall')
    for row in plan['requests']:
        rid = row.get('id')
        if not rid:
            continue
        path = absolute(run/row['directory'])
        value = results.get(rid)
        if value is None:
            if counts and not counts['requests'][rid]['fits']:
                results[rid] = dict(status='unsupported', complete=False, reason='full-payload-context-overflow; no trimming')
            elif session and (run/'execution-complete.json').exists():
                results[rid] = dict(status='skipped-after-failure', complete=False,
                                    reason='Original executor stopped after a failed request; never resumed.')
            else:
                holds.append('unattempted-or-pending:'+rid)
            continue
        if value['status'] == 'interrupted':
            holds.append('reserved-may-have-posted:'+rid)
            continue
        require(value.get('synthetic') is fixture, 'outcome-fixture-binding')
        require(value['status'] in ('enriched', 'partial', 'failed'), 'unknown-outcome-status')
        if not fixture:
            require(session is not None, 'live-outcome-without-session')
            reservation = load(path/'reservation.json')
            require(reservation['origin'] == session['origin'] and reservation['request_sha256'] == row['request_sha256']
                    and reservation['approval_sha256'] == session['approval_sha256']
                    and reservation['seal_sha256'] == sha(run/'seal.json'), 'reservation-binding')
            require(value['origin'] == session['origin'] and value['requested_model'] == requests.MODEL
                    and value['timeout_seconds'] == 1200 and value['retries'] == 0, 'outcome-route-binding')
        if value['status'] == 'failed':
            require(not value.get('record'), 'failed-outcome-cannot-have-accepted-record')
            # Failed schema/assembly is a limitation. A transport ambiguity or
            # serving/integrity mismatch is still an execution hold.
            reason = value.get('reason', '')
            if (not fixture and (value.get('transport_status') == 'transport-failure' or
                    any(token in reason for token in ('model', 'count-mismatch', 'usage', 'binding', 'changed', 'missing-response-body')))):
                holds.append('failed-route-or-uncertain-post:'+rid)
            continue
        require(value.get('raw_file'), 'accepted-outcome-without-raw')
        raw = (path/value['raw_file']).read_bytes()
        if value.get('origin'):
            method = trusted.module('execution', trusted.read_method_path())
            text, envelope = method.envelope(raw)
            usage = envelope['usage']
            require(usage == value['usage'] and envelope['model'] == value['returned_model'], 'returned-envelope-binding')
            require(all(type(usage.get(k)) is int and usage[k] >= 0 for k in ('prompt_tokens', 'completion_tokens', 'total_tokens')), 'usage-shape')
            require(counts is not None and usage['prompt_tokens'] == counts['requests'][rid]['prompt_tokens_local']
                    and usage['completion_tokens'] <= 65536 and usage['total_tokens'] == usage['prompt_tokens']+usage['completion_tokens'], 'usage-count-binding')
        else:
            require(fixture, 'fixture-import-only')
            text = load(path/value['raw_file'])['content']
        recomputed = importer.assemble_response(row, load(path/'source-evidence.json'), text, fixture)
        require(all(value.get(k) == v for k, v in recomputed.items()), 'outcome-record-recomputation-mismatch')
    return results, sorted(set(holds))


def read_run(run):
    run = absolute(run)
    before = tree(run)
    plan, pkg = bindings._verify(run, for_execution=False)
    results, holds = outcomes(run, plan)
    eligible = pkg.eligible_elements(['figure', 'table'])
    require({r['element_id'] for r in plan['requests']} == {r['element_id'] for r in eligible}, 'all-element-accounting-required')
    rows = {r['element_id']: r for r in plan['requests']}
    elements = []
    for source in eligible:
        row = rows[source['element_id']]
        doc = pkg.doc(row['document'])
        ev = (load(run/row['directory']/'source-evidence.json') if row.get('id') else
              requests._base_evidence(pkg, doc, source['element']))
        value = results.get(row.get('id'), dict(status=row['status'], complete=False,
                            reason='No enrichment record; native source and crops remain available.'))
        elements.append(dict(element_id=row['element_id'], source_sha256=doc['sha256'], document=doc['identity'],
                             content_type=row['content_type'], eligible_default=source['kind'] is not None,
                             outcome=value, evidence=ev, source_element=source['element'],
                             source_pdf=str(pkg.root/doc['raw'])))
    require(before == tree(run), 'run-changed-during-read')
    source_bindings = tree(pkg.root)
    require(source_bindings == {k:v for k,v in pkg.snapshot['files'].items() if '__pycache__' not in Path(k).parts},
            'source-changed-during-read')
    return dict(kind='v7-run', path=str(run), bindings=before, plan=plan,
                source_package=str(pkg.root), source_bindings=source_bindings,
                elements=elements, execution_holds=holds, fixture=plan['fixture'],
                documents=plan['documents'])


def source_handoff(path, method, test_root=None):
    import source_package as adapter
    path = absolute(path)
    if test_root is None:
        return adapter.verify_handoff(path, method)
    value = load(path)
    require(value['status'] == 'test-only', 'fixture-handoff-required')
    actual = adapter.build_handoff(value['retention'], value['package'], value['launcher_result'], method, test_root, historical=True)
    adapter.retain_code_provenance(actual, value)
    require(value == actual, 'fixture-source-handoff-mismatch')
    require((path.parent/'summary.txt').read_text() == actual['summary'], 'fixture-summary-mismatch')
    return actual


def prepare(handoff, output, method, test_root=None):
    accepted = source_handoff(handoff, method, test_root)
    pkg = SourcePackage(accepted['package'], method=method)
    selected = [r['element_id'] for r in pkg.eligible_elements(['figure', 'table']) if r['kind']]
    output = new(output, [pkg.root, absolute(handoff).parent, absolute(method)])
    if test_root:
        require(output.is_relative_to(absolute(test_root)), 'fixture-output-outside-test-root')
    # V7 deliberately requires a nonempty explicit live roster. Do not forge a
    # dummy request or synthetic v7 run for a genuinely empty selection.
    if selected:
        requests.prepare(pkg.root, output/'v7', kinds=['figure', 'table'], element_ids=selected,
                         method=method, fixture=test_root is not None)
    selection = dict(schema='qualified-selection-v1', source_handoff=str(absolute(handoff)),
                     source_handoff_sha256=sha(handoff), source_package=str(pkg.root),
                     source_bindings=tree(pkg.root), method=str(absolute(method)), selected=selected,
                     default_kinds=['figure', 'table'], algorithm_disposition='deferred-not-selected',
                     fixture=test_root is not None, test_root=str(absolute(test_root)) if test_root else None,
                     code=code_hashes())
    save(output/'selection.json', selection)
    return selection


def read_job(job):
    job = absolute(job)
    selection = load(job/'selection.json')
    require(selection['schema'] == 'qualified-selection-v1', 'unsupported-selection-format')
    trusted.validate_code_provenance(selection['code'])
    require(sha(selection['source_handoff']) == selection['source_handoff_sha256'], 'source-handoff-changed')
    method = trusted.read_method_path()
    accepted = source_handoff(selection['source_handoff'], method, selection['test_root'])
    require(accepted['package'] == selection['source_package'] and tree(accepted['package']) == selection['source_bindings'], 'selection-source-binding')
    pkg = SourcePackage(accepted['package'], method=method)
    eligible = pkg.eligible_elements(['figure', 'table'])
    selected = [r['element_id'] for r in eligible if r['kind']]
    require(selected == selection['selected'] and selection['default_kinds'] == ['figure', 'table']
            and selection['algorithm_disposition'] == 'deferred-not-selected', 'default-roster-binding')
    if selected:
        result = read_run(job/'v7')
        require(result['plan']['selection'] == selected and result['plan']['kinds'] == ['figure', 'table']
                and not result['plan']['caption_only_variant'] and result['fixture'] == selection['fixture'], 'production-selection-variant-binding')
    else:
        elements = []
        for row in eligible:
            doc = pkg.doc(row['document'])
            elements.append(dict(element_id=row['element_id'], source_sha256=doc['sha256'], document=doc['identity'],
                content_type=row['content_type'], eligible_default=False,
                outcome=dict(status=row['reason'], complete=False, reason='Not selected by default; source retained.'),
                evidence=requests._base_evidence(pkg, doc, row['element']), source_element=row['element'],
                source_pdf=str(pkg.root/doc['raw'])))
        result = dict(kind='zero-eligible', source_package=str(pkg.root), source_bindings=tree(pkg.root),
                      elements=elements, execution_holds=[], fixture=selection['fixture'],
                      documents=[{k:v for k,v in d.items() if k not in ('elements','pages')} for d in pkg.documents])
    result.update(kind='qualified-job', path=str(job), selection=selection, selection_sha256=sha(job/'selection.json'))
    return result


def snapshot(path, kind):
    require(kind in ('qualified-job', 'v7-run'), 'snapshot-kind')
    return read_job(path) if kind == 'qualified-job' else read_run(path)
