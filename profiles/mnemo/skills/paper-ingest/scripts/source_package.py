#!/usr/bin/env python3
"""Retain acquired sources and verify the accepted PDF workflow handoff.

No retrieval, workflow execution, approval, model calls or scientific prose.
See references/source-package-integration.md for the input contract.
"""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit, parse_qsl

CHANNELS = ['caption', 'figure', 'structured', 'classification', 'association']


def require(ok, message):
    if not ok:
        raise ValueError(message)


def absolute(value):
    require(isinstance(value, (str, Path)) and bool(str(value)), 'path required')
    p = Path(value)
    require(p.is_absolute() and '..' not in p.parts and '\\' not in str(p), 'absolute path without traversal required')
    require(not any(x.is_symlink() for x in (p, *p.parents)), 'symlink path forbidden')
    require(not p.is_file() or p.stat().st_nlink == 1, 'hardlink file forbidden')
    return p


def inside(root, name):
    p = Path(name)
    require(not p.is_absolute() and '..' not in p.parts and str(p) not in ('', '.'), 'unsafe relative path')
    return absolute(absolute(root)/p)


def sha(path):
    h = hashlib.sha256()
    with absolute(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key: ' + key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError('nonfinite JSON')
    return json.loads(absolute(path).read_bytes(), object_pairs_hook=pairs, parse_constant=constant)


def put(path, raw):
    p = absolute(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    fd = os.open(p.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def save(path, value):
    put(path, (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode())


def new_directory(path):
    p = absolute(path)
    require(p.parent.is_dir(), 'output parent must exist')
    p.mkdir(mode=0o700)
    return p


def public_url(value):
    """Reject credential-bearing inputs; never silently rewrite source tokens."""
    require(isinstance(value, str), 'URL required')
    u = urlsplit(value)
    require(u.scheme in ('http', 'https') and u.hostname and not u.username and not u.password, 'public HTTP URL required')
    for key, _ in parse_qsl(u.query, keep_blank_values=True) + parse_qsl(u.fragment, keep_blank_values=True):
        require(not re.search(r'token|secret|password|credential|signature|api.?key|authorization|cookie', key, re.I),
                'credential-bearing URL forbidden; retain only public source URL')
    return value


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]*', value), 'safe identifier required')
    return value


def file_metadata(row, article):
    identifier(row['id'])
    require(set(row) <= {'id','role','format','path','sha256','filename','source_url','discovery_url',
                         'article_slug','identity_verification','page_count','extraction_disposition'}, 'unknown source fields; no selected-page/channel diagnostics')
    require(row['role'] in ('manuscript', 'supplement', 'body'), 'source role')
    require(row['format'] in ('pdf', 'other'), 'source format')
    require(row['role'] != 'manuscript' or row['format'] == 'pdf', 'original manuscript must be PDF')
    name = row['filename']
    require(isinstance(name, str) and name not in ('', '.', '..') and '/' not in name and '\\' not in name, 'filename must be a basename')
    require(row['article_slug'] == article['slug'], 'source article identity mismatch')
    identity = row['identity_verification']
    require(identity['status'] == 'operator-verified' and isinstance(identity['basis'], str) and identity['basis'].strip(),
            'operator identity verification required (not adapter verification)')
    public_url(row['source_url']); public_url(row['discovery_url'])


def validate_acquisition(value):
    require(value['schema'] == 'acquired-sources-v1', 'acquisition schema')
    require(set(value) == {'schema','article','files','attempts','obligations','attachments'}, 'unknown acquisition fields')
    article = value['article']; identifier(article['slug'])
    require(all(k in article for k in ('title', 'doi', 'pmid', 'version')), 'explicit article identity fields required')
    require(isinstance(article['title'], str) and article['title'].strip() and article['version'], 'article title and version required')
    files = value['files']; attempts = value['attempts']
    require(isinstance(files, list) and isinstance(attempts, list), 'files and attempts lists required')
    ids = [r['id'] for r in files]
    aids = [r['id'] for r in attempts]
    require(len(ids) == len(set(ids)) and len(aids) == len(set(aids)), 'duplicate source/attempt ID')
    require(len({r['sha256'] for r in files}) == len(files), 'duplicate source bytes; list aliases as discovery evidence, not duplicate files')
    for row in files:
        file_metadata(row, article)
    for row in attempts:
        identifier(row['id']); public_url(row['source_url'])
        require(row['outcome'] in ('failed','retrieved','unknown'), 'attempt outcome')
        require(row['route'] and row['observed_at'] and row['raw_response'] in ('available','unavailable'), 'attempt evidence metadata')
        require(isinstance(row['artifacts'], list), 'attempt artifacts list')
        require(row['artifacts'] or (row['raw_response'] == 'unavailable' and row['limitation']), 'missing attempt evidence limitation')
        require(row['raw_response'] != 'unavailable' or row['limitation'], 'raw response limitation required')
    require(set(value['obligations']) == {'body','manuscript'}, 'body/manuscript obligations required')
    for role in ('body','manuscript'):
        obligation = value['obligations'][role]
        require(obligation['status'] in ('retrieved','missing'), 'body/manuscript disposition required')
        if obligation['status'] == 'retrieved':
            expected = {r['id'] for r in files if r['role'] == role}
            require(expected and set(obligation['file_ids']) == expected, 'obligation source binding')
        else:
            require(obligation['disposition'] and set(obligation['attempt_ids']) <= set(aids), 'missing source disposition')
            require(not any(r['role'] == role for r in files), 'missing obligation contradicts retained source')
    attachments = value['attachments']
    require(attachments['status'] in ('not-inspected','none-listed','advertised'), 'attachment discovery state')
    items = attachments['items']
    require(isinstance(items, list) and len({x['id'] for x in items}) == len(items), 'attachment items')
    if attachments['status'] != 'not-inspected': public_url(attachments['inspected_url'])
    require((attachments['status'] == 'advertised') == bool(items), 'advertised attachments must be enumerated')
    retained = []
    for item in items:
        identifier(item['id']); public_url(item['observed_link'])
        require(item['filename'], 'advertised filename required')
        if item['status'] == 'retrieved':
            retained.append(item['file_id'])
        else:
            require(item['status'] == 'missing' and item['disposition'] and
                    set(item['attempt_ids']) <= set(aids), 'missing attachment disposition')
    require(len(retained) == len(set(retained)) and set(retained) == {r['id'] for r in files if r['role'] == 'supplement'},
            'silent or duplicate attachment loss')


def pdf_count(path):
    import pymupdf
    with pymupdf.open(path) as pdf:
        require(pdf.is_pdf and not pdf.needs_pass and len(pdf) > 0, 'unsupported PDF')
        return len(pdf)


def scope_for(acquisition, root, endpoint, budget):
    public_url(endpoint)
    u = urlsplit(endpoint)
    require(not u.query and not u.fragment, 'application endpoint cannot contain query or fragment')
    require(type(budget) is int and budget >= 0, 'explicit nonnegative application-post budget required')
    docs = []
    for row in acquisition['files']:
        source = inside(root, row['path'])
        with source.open('rb') as stream:
            pdf_header = b'%PDF-' in stream.read(1024)
        require(row['format'] == 'pdf' or not (pdf_header or row['filename'].lower().endswith('.pdf')),
                'PDF cannot be declared non-PDF')
        if row['format'] != 'pdf': continue
        require(row['role'] in ('manuscript','supplement'), 'PDF role must be manuscript or supplement')
        require(sha(source) == row['sha256'], 'retained source hash mismatch')
        count = pdf_count(source)
        require(row['page_count'] == count, 'source page count mismatch')
        docs.append(dict(identity=row['id'], source=str(source), sha256=row['sha256'], page_count=count,
                         pages=list(range(1, count+1)), channels=list(CHANNELS)))
    require(docs, 'at least one acquired PDF required for this route')
    return dict(documents=docs, max_application_posts=budget, application_endpoint=endpoint)


def prepare(input_path, output, endpoint, budget):
    source = absolute(input_path); value = load(source)
    validate_acquisition(value)
    # Validate every declared input before reserving a destination. Failure after
    # mkdir is preserved, never removed or reused.
    rows = value['files'] + [r for a in value['attempts'] for r in a['artifacts']]
    for row in rows:
        require(sha(row['path']) == row['sha256'], 'input source hash mismatch')
    root = new_directory(output)
    put(root/'input.json', source.read_bytes())
    retained = json.loads(json.dumps(value))
    for row in retained['files']:
        src = absolute(row['path']); raw = src.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == row['sha256'], 'source changed during retention')
        name = 'originals/'+row['id']+'/'+row['filename']
        put(inside(root,name), raw); row['path'] = name
        if row['format'] == 'pdf':
            count = pdf_count(inside(root,name))
            require(row.get('page_count',count) == count, 'source page count mismatch')
            row['page_count'] = count
        else:
            row['extraction_disposition'] = 'deferred-non-PDF' if row['role'] == 'supplement' else 'operator-readable-body'
    for attempt in retained['attempts']:
        for index, row in enumerate(attempt['artifacts']):
            raw = absolute(row['path']).read_bytes()
            require(hashlib.sha256(raw).hexdigest() == row['sha256'], 'attempt evidence changed')
            name = f'attempts/{attempt["id"]}/{index:04d}.bin'
            put(inside(root,name), raw); row['path'] = name
    scope = scope_for(retained, root, endpoint, budget)
    save(root/'scope.json', scope)
    bindings = tree_hashes(root)
    record = dict(schema='source-retention-v1', acquisition=retained, bindings=bindings,
                  identity_basis='operator-verified; adapter checks bindings only', timestamps='Input observations only; missing historical times remain not-recorded')
    save(root/'retention.json', record)
    validate_retention(root/'retention.json')
    return dict(retention=str(root/'retention.json'), scope=str(root/'scope.json'), authorization=False)


def tree_hashes(root):
    root = absolute(root)
    result = {}
    for p in sorted(root.rglob('*')):
        absolute(p)
        if p.is_file(): result[str(p.relative_to(root))] = sha(p)
    return result


def validate_retention(path):
    path = absolute(path); root = path.parent; value = load(path)
    require(path.name == 'retention.json' and value['schema'] == 'source-retention-v1', 'retention schema/path')
    actual = tree_hashes(root); actual.pop('retention.json')
    require(actual == value['bindings'], 'retention evidence changed or incomplete')
    acquisition = value['acquisition']; validate_acquisition(acquisition)
    original = load(root/'input.json'); validate_acquisition(original)
    # Reconstruct the only permitted acquisition transformations.
    normalized = json.loads(json.dumps(acquisition))
    require(len(original['files']) == len(normalized['files']) and len(original['attempts']) == len(normalized['attempts']), 'retention input mismatch')
    for row, old in zip(normalized['files'], original['files']):
        require(sha(inside(root,row['path'])) == row['sha256'], 'retained original mismatch')
        row['path'] = old['path']
        if 'page_count' not in old: row.pop('page_count',None)
        row.pop('extraction_disposition',None)
    for attempt, old in zip(normalized['attempts'],original['attempts']):
        require(len(attempt['artifacts']) == len(old['artifacts']), 'attempt artifact loss')
        for row, before in zip(attempt['artifacts'],old['artifacts']):
            require(sha(inside(root,row['path'])) == row['sha256'], 'attempt evidence hash mismatch')
            row['path'] = before['path']
    require(normalized == original, 'retention input metadata mismatch')
    scope = load(root/'scope.json')
    require(scope == scope_for(acquisition,root,scope['application_endpoint'],scope['max_application_posts']), 'retention scope mismatch')
    return value, scope


def trusted_method(path):
    root = absolute(path)
    require((root/'pdf_source_package/phase_evidence.py').is_file(), 'trusted accepted method required')
    sys.dont_write_bytecode = True
    sys.path.insert(0,str(root))
    module = importlib.import_module('pdf_source_package')
    module_file = getattr(module, '__file__', None)
    require(module_file is not None and Path(module_file).resolve().parent == root/'pdf_source_package', 'different method already imported')
    return root


def verified_state(retention_path, package, launcher_result, method, *, historical=False):
    """Read-only revalidation, not a second workflow executor."""
    trusted_method(method)
    from pdf_source_package.workflow import final_state
    from pdf_source_package.phase_evidence import operation_evidence
    from pdf_source_package.reporting import factual_summary
    retention, scope = validate_retention(retention_path)
    package = absolute(package); result_path = absolute(launcher_result)
    require(result_path.name == 'result.json', 'saved launcher result.json required')
    attempt = result_path.parent
    require(not attempt.is_relative_to(package), 'launcher attempt must be external')
    result = load(result_path); process = load(attempt/'process.json'); receipt = load(attempt/'phase-evidence.json')
    require(result['schema'] == process['schema'] == 'pdf-workflow-process-v1', 'launcher schema')
    operation = result['operation']
    require(operation in ('report','finalize','summary'), 'successful reporting/finalization launcher required')
    require(result['success'] is True and result['artifact_status'] == 'verified', 'launcher failed or incomplete')
    for key in ('argv','cwd','started_at','ended_at','exit_code','process_status','termination','termination_errors','child_pid','log'):
        require(result[key] == process[key], 'launcher/process contradiction: '+key)
    require(type(process['exit_code']) is int and process['exit_code'] == 0 and process['process_status'] == 'exited' and
            process['termination'] == 'normal' and process['termination_errors'] == [], 'launcher process not successfully completed')
    require(process['started_at'] and process['ended_at'] and type(process['child_pid']) is int, 'launcher process evidence missing')
    absolute(process['cwd'])  # recorded producer location; never imported
    if not historical:
        require(process['cwd'] == str(absolute(method)), 'launcher trusted method mismatch')
    require(result['attempt_dir'] == str(attempt) and result['process_record'] == str(attempt/'process.json') and
            result['phase_evidence'] == str(attempt/'phase-evidence.json') and process['log'] == str(attempt/'console.log'), 'launcher attempt path mismatch')
    require((attempt/'console.log').is_file(), 'launcher console missing')
    argv = process['argv']
    # The code-owned launcher has a fixed argv grammar for report operations.
    require(argv[1:6] == ['-B','-u','-E','-m','pdf_source_package'], 'unexpected launcher argv')
    tokens = argv[6:]
    if tokens and tokens[0] == '--offline': tokens = tokens[1:]
    require(tokens[:3] == ['--workflow-evidence',str(attempt/'phase-evidence.json'),operation], 'launcher operation mismatch')
    tokens = tokens[3:]
    require(len(tokens)%2 == 0, 'launcher argument pairs')
    flags = dict(zip(tokens[::2],tokens[1::2]))
    require(len(flags)*2 == len(tokens) and set(flags) <= {'--root','--output','--inspections'} and flags['--root'] == str(package), 'launcher package binding')
    require(('--output' in flags) == (operation == 'summary'), 'launcher output binding')
    destination = absolute(flags['--output']) if operation == 'summary' else package
    if operation == 'summary': require(not destination.is_relative_to(package), 'summary must be external')
    inspections = absolute(flags['--inspections']) if '--inspections' in flags else None
    # Check symlinks before the accepted validator traverses package inputs.
    package_bindings = tree_hashes(package)
    inspection_bindings = tree_hashes(inspections) if inspections and inspections.exists() else None
    manifest = load(package/'manifest.json')
    require(load(package/'scope.json') == scope, 'workflow scope does not match retained sources')
    require(len(manifest['documents']) == len(scope['documents']), 'workflow source count mismatch')
    for doc, source in zip(manifest['documents'],scope['documents']):
        require(all(doc[k] == source[k] for k in ('identity','sha256','page_count','channels')), 'workflow source identity/hash/page/channel mismatch')
        require(doc['selected_pages'] == source['pages'] and doc['extraction_scope'] == 'whole-document', 'selected-page diagnostic not production scope')
        require(sha(inside(package,doc['raw'])) == source['sha256'], 'workflow retained PDF mismatch')
    state = final_state(package,inspections)
    recomputed = operation_evidence(package,operation,output=destination,state=state)
    require(receipt == recomputed, 'stale or corrupt launcher receipt')
    for key in ('artifact_status','requested_work_complete','fixture','facts_path','summary_path','results_path'):
        require(result[key] == receipt[key], 'launcher/receipt contradiction: '+key)
    summary = factual_summary(state['facts'])
    require(result['summary'] == summary, 'launcher summary mismatch')
    require(package_bindings == tree_hashes(package), 'package changed during verification')
    if inspections and inspections.exists(): require(inspection_bindings == tree_hashes(inspections), 'inspection changed during verification')
    return retention, state, summary, inspections


def holds_for(retention, state, package):
    holds = []
    acquisition = retention['acquisition']
    for role, value in acquisition['obligations'].items():
        if value['status'] != 'retrieved': holds.append('acquisition-'+role+'-missing')
    attachments = acquisition['attachments']
    if attachments['status'] == 'not-inspected': holds.append('attachments-not-inspected')
    if any(x['status'] == 'missing' for x in attachments['items']): holds.append('advertised-attachments-missing')
    if state['fixture'] or (Path(package)/'OFFLINE-FIXTURE').exists(): holds.append('fixture-not-production')
    if not state['requested_work_complete']: holds.append('requested-work-incomplete')
    if not all(d['complete_package'] for d in state['documents']): holds.append('incomplete-full-document-package')
    for phase, row in state['facts']['phases'].items():
        if row['status'] != 'complete' or row['uncertain_reservations']: holds.append('phase-hold-'+phase)
        if row['fixture_or_replay_calls']: holds.append('fixture-or-replay-'+phase)
    if (Path(package)/'stop.json').exists(): holds.append('workflow-stop-record')
    inspection = state['facts']['inspection']
    if inspection['uncertain_reservations'] or inspection['status'] in ('incomplete-records','directory-missing'):
        holds.append('inspection-evidence-incomplete')
    if inspection['fixture_or_replay_calls']: holds.append('fixture-inspection-not-production')
    return holds


def build_handoff(retention_path, package, launcher_result, method, test_root=None, *, historical=False):
    retention, state, summary, inspections = verified_state(retention_path,package,launcher_result,method,historical=historical)
    holds = holds_for(retention,state,package)
    if test_root is None: require(not holds, 'production hold: '+', '.join(holds))
    else:
        test_root = absolute(test_root)
        require(state['fixture'] is True, 'test-only requires explicit workflow fixture')
        require(all(absolute(p).is_relative_to(test_root) for p in (retention_path,package,launcher_result)), 'test-only inputs must be under test root')
    value = dict(schema='source-package-handoff-v1', status='test-only' if test_root else 'production-mechanical-complete',
        production_complete=not holds and test_root is None, holds=holds, article=retention['acquisition']['article'],
        retention=str(absolute(retention_path)), retention_sha256=sha(retention_path), package=str(absolute(package)),
        launcher_result=str(absolute(launcher_result)), launcher_bindings=tree_hashes(absolute(launcher_result).parent),
        package_bindings=tree_hashes(package), method_bindings={k:v for k,v in tree_hashes(absolute(method)/'pdf_source_package').items() if not k.endswith('.pyc')},
        inspection_dir=str(inspections) if inspections else None,
        inspection_bindings=tree_hashes(inspections) if inspections and inspections.exists() else None,
        facts=state['facts'], facts_path=load(launcher_result)['facts_path'], results_path=load(launcher_result)['results_path'],
        summary_path=load(launcher_result)['summary_path'], summary=summary,
        sources=retention['acquisition'], documents=state['documents'],
        limitations=['Mechanical completion is not exhaustive recall or scientific/crop/human acceptance.',
                     'Identity is operator-verified; the adapter verifies bindings, not article content.',
                     'Inspection input coverage is distinct from model findings and human acceptance.',
                     'Absent historical clocks remain not-recorded; originals and non-PDF dispositions are retained.'])
    for source in retention['acquisition']['files']:
        if source.get('extraction_disposition') == 'deferred-non-PDF':
            value['limitations'].append(
                f'Non-PDF extraction deferred: {source["id"]}. Original retained; '
                'claims depending on unread data require an explicit source limitation in the paper.')
    return value


def trusted_enrichment(integration, enrichment_root):
    """Only explicitly configured code roots may verify enriched evidence."""
    integration = absolute(integration); enrichment_root = absolute(enrichment_root)
    require((integration/'qualified_enrichment/exports.py').is_file() and
            (enrichment_root/'pdf_enrichment/bindings.py').is_file(), 'trusted enrichment roots required')
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(integration), str(enrichment_root)]
    for name, root in (('qualified_enrichment', integration), ('pdf_enrichment', enrichment_root)):
        module = importlib.import_module(name)
        require(Path(module.__file__).resolve().parent == root/name, 'different enrichment code already imported')
    return importlib.import_module('qualified_enrichment.exports')


def qualification_text(enrichment):
    lines = ['Enrichment qualifications (scoped, not correctness certification):']
    for view in enrichment['elements']:
        lines.append('Element '+view['element_id']+': '+view['review_status']+
                     '; exact use requires source inspection or explicit qualification of affected/unreviewed scope.')
        for finding in view['findings']:
            lines.append('Finding '+finding['id']+'; target '+finding['target']+'; '+finding['stage']+'; '+
                         finding['status']+'; '+finding['category']+': '+finding['reason'])
            if finding.get('resolutions'):
                lines.append('Original unchanged. Attributed resolution proposals for '+finding['id']+': '+
                             json.dumps(finding['resolutions'], ensure_ascii=False, sort_keys=True))
    for row in enrichment['eligibility']['element_accounting']:
        if row['disposition'] != 'enriched':
            lines.append('Disposition '+row['element_id']+': '+row['disposition'])
    if enrichment['eligibility']['zero_eligible']:
        lines.append('Zero eligible figure/table elements; this is not proof of their absence.')
    return '\n'.join(lines)


def build_enriched_handoff(retention_path, package, launcher_result, method,
                           enrichment_handoff, enrichment_launcher_result, integration, enrichment_root,
                           test_root=None, *, historical=False):
    # Do not relax any v1 acquisition, full-document, phase or fixture hold.
    source = build_handoff(retention_path, package, launcher_result, method, test_root, historical=historical)
    exports = trusted_enrichment(integration, enrichment_root)
    enriched = exports.verify_export(enrichment_handoff, source_package=package, production=test_root is None)
    from qualified_enrichment.launcher import verify_result
    ep = absolute(enrichment_handoff)
    receipt = verify_result(enrichment_launcher_result, 'export',
                            {str(ep): sha(ep), str(ep.parent/'annotated.html'): sha(ep.parent/'annotated.html')})
    if not historical:
        require(receipt['deployment']['integration_dir'] == str(absolute(integration)) and
                receipt['deployment']['enrichment_root'] == str(absolute(enrichment_root)) and
                receipt['deployment']['method_dir'] == str(absolute(method)), 'enrichment launcher deployment mismatch')
    if test_root:
        require(all(absolute(p).is_relative_to(absolute(test_root)) for p in
                    (ep,enrichment_launcher_result,enriched['review_root'])), 'test-only enrichment outside test root')
    holds = sorted(set(source['holds'] + enriched['eligibility']['holds']))
    return dict(source, schema='source-package-handoff-v2',
                status='test-only' if test_root else 'qualified-production-complete',
                production_complete=test_root is None and not holds, holds=holds,
                source_handoff=source, enrichment=enriched,
                enrichment_handoff=str(ep), enrichment_sha256=sha(ep),
                enrichment_launcher_result=str(absolute(enrichment_launcher_result)),
                enrichment_launcher_bindings=tree_hashes(absolute(enrichment_launcher_result).parent),
                integration_bindings=tree_hashes(absolute(integration)/'qualified_enrichment'),
                qualifications=qualification_text(enriched))


def retain_code_provenance(actual, saved):
    """Keep producer hashes after independently reconstructing the evidence."""
    for key in ('method_bindings', 'integration_bindings'):
        if key in actual:
            value = saved.get(key)
            require(isinstance(value, dict) and value and all(
                isinstance(k, str) and k and isinstance(v, str) and re.fullmatch('[0-9a-f]{64}', v)
                for k, v in value.items()), 'invalid-code-provenance')
            actual[key] = value
    if 'source_handoff' in actual:
        retain_code_provenance(actual['source_handoff'], saved['source_handoff'])
    return actual


def verify_handoff(path, method, expected_article=None, *, integration=None,
                   enrichment_root=None, require_enriched=False):
    value = load(path)
    if value['schema'] == 'source-package-handoff-v2':
        require(value['production_complete'] is True and value['status'] == 'qualified-production-complete',
                'handoff is not production completion')
        require(integration and enrichment_root, 'explicit trusted enrichment roots required')
        actual = build_enriched_handoff(value['retention'],value['package'],value['launcher_result'],method,
                    value['enrichment_handoff'],value['enrichment_launcher_result'],integration,enrichment_root,historical=True)
        require((absolute(path).parent/'qualifications.txt').read_text() == actual['qualifications'],
                'removed or mismatched qualifications')
    else:
        require(not require_enriched, 'new production route requires enriched v2 handoff')
        require(value['schema'] == 'source-package-handoff-v1' and value['production_complete'] is True and
                value['status'] == 'production-mechanical-complete', 'handoff is not production completion')
        actual = build_handoff(value['retention'],value['package'],value['launcher_result'],method,historical=True)
    retain_code_provenance(actual, value)
    require(value == actual, 'stale or mismatched handoff')
    require((absolute(path).parent/'summary.txt').read_text() == actual['summary'], 'handoff exact summary changed')
    if expected_article is not None:
        for key, expected in expected_article.items():
            require(actual['article'].get(key) == expected, 'paper/handoff identity mismatch: '+key)
    return actual


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    p = sub.add_parser('prepare')
    p.add_argument('--input',required=True); p.add_argument('--output',required=True)
    p.add_argument('--application-endpoint',required=True); p.add_argument('--max-application-posts',type=int,required=True)
    p = sub.add_parser('handoff')
    for flag in ('retention','package','launcher-result','method','output'): p.add_argument('--'+flag,required=True)
    p.add_argument('--test-only-root')
    for flag in ('enrichment-handoff','enrichment-launcher-result','integration','enrichment-root'):
        p.add_argument('--'+flag)
    p = sub.add_parser('verify'); p.add_argument('--handoff',required=True); p.add_argument('--method',required=True)
    p.add_argument('--integration'); p.add_argument('--enrichment-root'); p.add_argument('--require-enriched',action='store_true')
    args = parser.parse_args(argv)
    if args.command == 'handoff':
        options = [args.enrichment_handoff,args.enrichment_launcher_result,args.integration,args.enrichment_root]
        if any(options) and not all(options): parser.error('all four enrichment handoff/deployment arguments are required')
    # Adapter operations never need network, even when invoked without --offline.
    sys.addaudithook(lambda event,values: (_ for _ in ()).throw(RuntimeError('adapter-network-forbidden')) if event.startswith('socket.') else None)
    try:
        if args.command == 'prepare':
            result = prepare(args.input,args.output,args.application_endpoint,args.max_application_posts)
        elif args.command == 'handoff':
            output = absolute(args.output)
            if args.test_only_root: require(output.is_relative_to(absolute(args.test_only_root)), 'test-only output outside test root')
            require(not output.exists(), 'handoff output must be new')
            protected = [absolute(args.retention).parent, absolute(args.package),
                         absolute(args.launcher_result).parent, absolute(args.method)]
            report = load(args.launcher_result)
            if report.get('facts_path'): protected.append(absolute(report['facts_path']).parent)
            if args.enrichment_handoff:
                protected += [absolute(args.enrichment_handoff).parent, absolute(args.enrichment_launcher_result).parent,
                              absolute(args.integration), absolute(args.enrichment_root)]
                enriched = load(args.enrichment_handoff)
                protected.append(absolute(enriched['review_root']))
            for target in protected:
                require(not output.is_relative_to(target) and not target.is_relative_to(output), 'handoff output must be external to evidence')
            if args.enrichment_handoff:
                result = build_enriched_handoff(args.retention,args.package,args.launcher_result,args.method,
                    args.enrichment_handoff,args.enrichment_launcher_result,args.integration,args.enrichment_root,args.test_only_root)
            else:
                result = build_handoff(args.retention,args.package,args.launcher_result,args.method,args.test_only_root)
            if result['inspection_dir']:
                inspection = absolute(result['inspection_dir'])
                require(not output.is_relative_to(inspection) and not inspection.is_relative_to(output), 'handoff output must be external to inspection evidence')
            root = new_directory(output)
            save(root/'handoff.json',result); put(root/'summary.txt',result['summary'].encode())
            if 'qualifications' in result: put(root/'qualifications.txt',result['qualifications'].encode())
            result = dict(handoff=str(root/'handoff.json'),status=result['status'],production_complete=result['production_complete'],holds=result['holds'])
        else:
            result = verify_handoff(args.handoff,args.method,integration=args.integration,
                                    enrichment_root=args.enrichment_root,require_enriched=args.require_enriched)
            result = dict(status=result['status'],production_complete=result['production_complete'])
        print(json.dumps(result,indent=2)); return 0
    except (OSError,ValueError,KeyError,TypeError,ImportError,RuntimeError) as exc:
        print(json.dumps(dict(status='hold',error=str(exc))),file=sys.stderr); return 2


if __name__ == '__main__':
    sys.exit(main())
