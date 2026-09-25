"""Operation-local completion receipts for the fixed CLI launcher."""
from pathlib import Path
from .io import load, save, sha, require
from .reporting import Evidence, source_facts, basic_phase, PHASES


def operation_evidence(root, operation, phase=None, output=None, state=None):
    root = Path(root)
    evidence = Evidence(root)
    manifest, pages = source_facts(evidence)
    value = dict(schema='pdf-workflow-evidence-v1', operation=operation, phase=phase,
                 package_dir=str(root), fixture=manifest['fixture'], artifact_status='verified',
                 requested_work_complete=None, phase_status=None, evidence_roots={})
    if operation in ('report', 'finalize', 'summary'):
        require(state is not None and state['facts']['evidence_status'] == 'verified', 'missing-report-state')
        destination = Path(output) if operation == 'summary' else root
        require(load(destination/'facts.json') == state['facts'] and load(destination/'results.json') == state, 'report-snapshot-mismatch')
        from .reporting import factual_summary
        require((destination/'summary.txt').read_text() == factual_summary(state['facts']), 'summary-facts-mismatch')
        for name, expected in state['artifact_bindings'].items():
            evidence.file(name)
            require(evidence.files[name] == expected, 'report-input-changed')
        files = ['facts.json', 'summary.txt', 'results.json']
        if operation != 'summary': files += ['index.html', 'candidates.csv', 'review.csv', 'review-notes.md']
        value['evidence_roots'][str(destination)] = {name:sha(destination/name) for name in files}
        value.update(requested_work_complete=state['requested_work_complete'],
                     facts_path=str(destination/'facts.json'), summary_path=str(destination/'summary.txt'),
                     results_path=str(destination/'results.json'))
        if operation != 'summary' and not state['requested_work_complete']:
            value['artifact_status'] = 'incomplete'
    else:
        selected = 'initial' if operation == 'prepare' else phase
        counts, _ = basic_phase(evidence, selected)
        require(counts['status'] != 'not-prepared', 'missing-phase-plan')
        plan = evidence.json(f'{selected}-plan.json')
        if operation in ('prepare', 'prepare-stage'):
            require(all(r['status'] in ('uncounted','ready','preflight-context-overflow') for r in plan['requests']), 'prepare-phase-status')
        if operation in ('count', 'seal'):
            require(all(r['status'] in ('ready','preflight-context-overflow') for r in plan['requests']), 'missing-counted-requests')
        if (root/f'{selected}-seal.json').exists():
            evidence.json(f'{selected}-seal.json')
            template = evidence.json(f'{selected}-approval.template.json')
            require(template['approved'] is False, 'approval-template-not-unapproved')
            require(template['seal_sha256'] == evidence.files[f'{selected}-seal.json'], 'template-seal-binding')
        if operation in ('execute','replay'):
            require(counts['status'] in ('complete','incomplete'), 'missing-phase-completion')
            if counts['status'] != 'complete': value['artifact_status'] = 'incomplete'
        value['phase_status'] = counts
        from .gates import next_step
        value['next_step'] = next_step(root, selected, counts)
    evidence.check()
    value['evidence_roots'].setdefault(str(root), {}).update(evidence.files)
    return value
