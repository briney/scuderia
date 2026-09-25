"""Portable article archives with immutable revisions and verified local resolution.

Archive manifests contain keys/hashes only. local-map.json is a separate,
manifest-bound operational mapping and is NEVER uploaded. Historical evidence
bytes are retained unchanged, including old absolute paths inside receipts.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

from article_runtime import (absolute, relative_key, inside, sha, require, digest,
                             tree, external, trusted_modules)

SCHEMA = 'portable-article-manifest-v3'
LEGACY_SCHEMA = 'portable-article-manifest-v2'
DIAGNOSTIC_SCHEMA = 'selected-diagnostic-source-v1'
ROLES = ('source-original', 'source-package', 'source-retention', 'enrichment-job',
         'enrichment-review', 'enrichment-export', 'page', 'legacy-pdf', 'handoff')
MAX_MANIFEST_BYTES = 32 * 1024 * 1024
MAX_OBJECT_BYTES = 4 * 1024 * 1024 * 1024


def now_utc():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def load(path):
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, 'duplicate-json-key:' + key)
            value[key] = item
        return value
    def constant(value):
        raise ValueError('nonfinite-json')
    p = absolute(path)
    require(p.stat().st_size <= MAX_MANIFEST_BYTES, 'json-size-limit')
    return json.loads(p.read_bytes(), object_pairs_hook=pairs, parse_constant=constant)


def put(path, raw):
    p = absolute(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def save(path, value):
    put(path, (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2)+'\n').encode())


def new_directory(path):
    p = absolute(path)
    require(p.parent.is_dir(), 'output-parent-must-exist')
    p.mkdir(mode=0o700)
    return p


def file_record(role, key, local, *, note=None, binds=None):
    require(role in ROLES, 'unknown-role')
    p = absolute(local)
    require(p.is_file(), 'archive-source-missing:' + key)
    result = dict(role=role, key=relative_key(key), sha256=sha(p), size=p.stat().st_size)
    if note: result['note'] = note
    if binds: result['binds'] = binds
    return result


def article_key(article):
    require(isinstance(article, dict) and isinstance(article.get('slug'), str) and
            re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', article['slug']), 'article-slug-required')
    # Version is intentionally excluded: source versions share an article namespace.
    return digest({k: article.get(k) for k in ('slug', 'doi', 'pmid')})


def _hash(value):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'invalid-digest')


def validate_manifest(m):
    require(m.get('schema') in (SCHEMA, LEGACY_SCHEMA, DIAGNOSTIC_SCHEMA), 'manifest-schema')
    require('sources' not in m, 'operational-sources-forbidden-in-archive-manifest')
    if m['schema'] == DIAGNOSTIC_SCHEMA:
        require(m['article'] is None and m['article_key'] is None and m['scope']=='selected-diagnostic',
                'diagnostic-not-bibliographic-article')
        require(m['production_complete'] is False and m['page_refresh_complete'] is False and
                m['source_status']['complete'] is False and m['source_status']['acquisition_verified'] is False,
                'diagnostic-cannot-be-production-complete')
        require(isinstance(m['roster'],list) and m['roster'] and len(set(m['roster']))==len(m['roster']) and
                m['roster']==[e['element_id'] for e in m['elements']], 'diagnostic-explicit-roster-required')
    else:
        require(m['article_key'] == article_key(m['article']), 'article-key-binding')
    require(re.fullmatch('[a-z0-9][a-z0-9-]*', m['package_id']), 'package-id-required')
    require(isinstance(m['files'], list) and len(m['files']) <= 100000, 'file-inventory-limit')
    keys, aliases = set(), set()
    for f in m['files']:
        key = relative_key(f['key'])
        require(key not in keys and key.casefold() not in aliases, 'duplicate-or-case-alias-key')
        keys.add(key); aliases.add(key.casefold())
        _hash(f['sha256'])
        require(type(f['size']) is int and 0 <= f['size'] <= MAX_OBJECT_BYTES, 'invalid-size')
        require(f['role'] in ROLES, 'unknown-role')
    require(m['total_objects'] == len(keys), 'object-count-mismatch')
    for key in keys:
        require(not any(str(p) in keys for p in Path(key).parents if str(p) != '.'), 'file-directory-alias')
    require(not keys.intersection({'manifest.json', 'local-map.json', 'RESTORE-RECEIPT.json'}), 'reserved-output-key')
    docs = {}
    for d in m['documents']:
        require(d['identity'] not in docs, 'duplicate-document')
        _hash(d['source_sha256'])
        require(d['source_version'] and type(d['complete']) is bool and type(d['fixture']) is bool, 'document-version-status')
        require(d['raw_key'] in keys, 'missing-document-source')
        record = next(f for f in m['files'] if f['key'] == d['raw_key'])
        require(record['sha256'] == d['source_sha256'], 'document-source-hash-binding')
        docs[d['identity']] = d
    require(docs, 'documents-required')
    common = m['common_dependencies']
    require(isinstance(common, list) and len(common) == len(set(common)) and set(common) <= keys, 'missing-common-dependency')
    history_keys = {f['key'] for f in m['files'] if f['role'].startswith('enrichment-')}
    require(history_keys <= set(common), 'omitted-review-or-export-dependency')
    ids = set()
    for e in m['elements']:
        require(e['element_id'] not in ids and e['document'] in docs, 'element-identity-binding')
        ids.add(e['element_id'])
        require(e['source_sha256'] == docs[e['document']]['source_sha256'], 'element-version-binding')
        require(type(e['eligible']) is bool and (not e['eligible'] or e['kind'] in ('figure', 'table')), 'element-eligibility')
        deps = e['dependencies']
        require(isinstance(deps, list) and len(deps) == len(set(deps)) and set(deps) <= keys, 'missing-or-duplicate-element-dependency')
        require(set(e['inherited']) <= set(deps), 'missing-inherited-qualification')
        ev = e['evidence']
        require(ev['element_id'] == e['element_id'] and ev['source_document'] == e['document'] and
                ev['source_sha256'] == e['source_sha256'], 'evidence-identity-binding')
        for f in list(e['fragments']) + ev.get('body_fragments', []) + ev.get('captions', []):
            key = f.get('crop_key', f.get('crop'))
            require(key in deps, 'missing-crop-dependency')
            if f.get('crop_sha256'):
                require(next(r['sha256'] for r in m['files'] if r['key'] == key) == f['crop_sha256'], 'crop-hash-binding')
        require(set(e['context']['native_text_keys']) <= set(deps), 'missing-native-context')
        require(isinstance(e['unavailable'], list), 'typed-unavailable-required')
        for u in e['unavailable']:
            require(set(u) == {'kind', 'detail'} and u['kind'] and u['detail'], 'unavailable-disposition')
    status = m['source_status']
    require(all(type(status[k]) is bool for k in ('complete', 'fixture', 'acquisition_verified', 'extraction_verified')), 'typed-source-status')
    require(isinstance(status['holds'], list) and isinstance(m['dispositions'], list), 'typed-source-holds')
    require(not status['complete'] or (not status['holds'] and status['acquisition_verified'] and
            status['extraction_verified'] and all(d['complete'] for d in docs.values())), 'contradictory-source-completeness')
    require(status['fixture'] or not any(d['fixture'] for d in docs.values()), 'fixture-promotion-forbidden')
    return m


def local_sources(manifest_path, m=None):
    manifest_path = absolute(manifest_path)
    m = validate_manifest(load(manifest_path) if m is None else m)
    mapping = load(manifest_path.parent/'local-map.json')
    require(mapping['schema'] == 'portable-article-local-map-v2' and
            mapping['manifest_sha256'] == sha(manifest_path), 'local-map-manifest-binding')
    sources = mapping['sources']
    require(isinstance(sources, dict) and set(sources) <= {f['key'] for f in m['files']}, 'local-map-inventory-binding')
    # Validate ALL mappings, including unselected rows, before opening or writing.
    for key, row in sources.items():
        relative_key(key)
        require(set(row) == {'root', 'path'}, 'local-source-fields')
        inside(row['root'], row['path'])
    return sources


def verify_local(manifest_path, keys=None):
    m = validate_manifest(load(manifest_path))
    sources = local_sources(manifest_path, m)
    wanted = {f['key'] for f in m['files']} if keys is None else set(keys)
    records = {f['key']: f for f in m['files']}
    require(wanted <= records.keys(), 'unknown-file-key')
    paths = {}
    for key in sorted(wanted):
        require(key in sources, 'dependency-not-materialized:' + key)
        p = inside(sources[key]['root'], sources[key]['path'])
        require(p.is_file(), 'missing-archive-source:' + key)
        require(p.stat().st_size == records[key]['size'] and sha(p) == records[key]['sha256'], 'corrupt-archive-source:' + key)
        paths[key] = p
    return m, paths


def verify_source(manifest_path):
    """Recheck portable acquisition identity/hash/scope bindings without old paths.

    Synthetic hand-authored contracts are accepted only as permanent fixtures.
    Production claims require retained acquisition and accepted extraction facts.
    The manifest hash is the portable trust anchor for the build-time recomputed
    representation; historical absolute receipt paths are never dereferenced.
    """
    m = validate_manifest(load(manifest_path))
    if m['schema'] == DIAGNOSTIC_SCHEMA:
        return verify_diagnostic(manifest_path)
    if m['provenance'].get('source_schema') is None:
        require(m['source_status']['fixture'] and m['provenance'].get('fixture') is True,
                'nonfixture-requires-verified-source-provenance')
        return m['source_status']
    required = {'retention/retention.json', 'retention/input.json', 'retention/scope.json', 'package/manifest.json'}
    require(required <= set(m['common_dependencies']), 'missing-source-verification-dependencies')
    _, paths = verify_local(manifest_path, set(m['common_dependencies']))
    retained = load(paths['retention/retention.json'])
    import source_package as adapter
    require(retained['schema'] == 'source-retention-v1', 'source-retention-schema')
    acquisition = retained['acquisition']; adapter.validate_acquisition(acquisition)
    require(acquisition['article'] == m['article'] and retained['identity_basis'] == m['source_status']['identity_basis'], 'source-article-identity-binding')
    original = load(paths['retention/input.json']); adapter.validate_acquisition(original)
    normalized = copy.deepcopy(acquisition)
    require(len(normalized['files']) == len(original['files']) and len(normalized['attempts']) == len(original['attempts']), 'retained-input-count-binding')
    inventory = {f['key']: f for f in m['files']}
    for rel, expected in retained['bindings'].items():
        key = 'retention/' + relative_key(rel)
        require(key in inventory and inventory[key]['sha256'] == expected, 'retention-inventory-binding')
    for row, before in zip(normalized['files'], original['files']):
        require(inventory['retention/'+relative_key(row['path'])]['sha256'] == row['sha256'], 'source-original-binding')
        row['path'] = before['path']
        if 'page_count' not in before: row.pop('page_count', None)
        row.pop('extraction_disposition', None)
    for attempt, before in zip(normalized['attempts'], original['attempts']):
        require(len(attempt['artifacts']) == len(before['artifacts']), 'attempt-artifact-count-binding')
        for artifact, old in zip(attempt['artifacts'], before['artifacts']):
            require(inventory['retention/'+relative_key(artifact['path'])]['sha256'] == artifact['sha256'], 'attempt-artifact-binding')
            artifact['path'] = old['path']
    require(normalized == original, 'retained-input-metadata-binding')
    package = load(paths['package/manifest.json'])
    require(package['schema'] == m['provenance']['source_schema'] == 'pdf-source-package-v1', 'source-package-schema-binding')
    docs = {d['identity']: d for d in package['documents']}
    source_rows = {r['id']: r for r in acquisition['files'] if r['format'] == 'pdf'}
    scope = load(paths['retention/scope.json'])
    require({d['identity'] for d in scope['documents']} == set(source_rows), 'retained-scope-source-roster')
    require(set(docs) == {d['identity'] for d in m['documents']}, 'source-document-roster-binding')
    for d in m['documents']:
        doc = docs[d['identity']]; src = source_rows[d['source_id']]
        require(d['source_sha256'] == src['sha256'] == doc['sha256'] and
                doc['page_count'] == src['page_count'] and d['source_version'] == m['article']['version'] and
                d['raw_key'] == 'package/'+doc['raw'] and
                m['provenance']['original_document_bindings'][d['identity']] == d['source_id'], 'source-document-version-binding')
        if m['source_status']['complete']:
            require(doc['extraction_scope'] == 'whole-document' and
                    doc['selected_pages'] == list(range(1, doc['page_count']+1)), 'diagnostic-not-complete')
    facts = [r['detail'] for r in m['dispositions'] if r['kind'] == 'source-extraction']
    require(len(facts) == 1, 'extraction-facts-required')
    if m['source_status']['complete']:
        require(all(v['status'] == 'retrieved' for v in acquisition['obligations'].values()) and
                acquisition['attachments']['status'] != 'not-inspected' and
                all(i['status'] == 'retrieved' for i in acquisition['attachments']['items']), 'acquisition-incomplete')
        require(all(v['status'] == 'complete' and not v['uncertain_reservations'] for v in facts[0]['phases'].values()), 'extraction-execution-incomplete')
    if not m['source_status']['fixture']:
        require(not any(v['fixture_or_replay_calls'] for v in facts[0]['phases'].values()), 'source-fixture-promotion')
    return m['source_status']


def _collect_tree(files, sources, role, root, prefix, note):
    root = absolute(root)
    require(root.is_dir(), 'evidence-tree-required')
    for p in sorted(root.rglob('*')):
        absolute(p)  # reject symlinks even when their name would be excluded
        if not p.is_file(): continue
        rel = str(p.relative_to(root))
        parts = p.relative_to(root).parts
        if '__pycache__' in parts or p.name.endswith(('.pyc', '.lock')): continue
        require(not any(x.startswith('.') or x.lower() in ('credentials', 'config.yaml', 'tokenizers', 'venv')
                        for x in parts), 'unexpected-private-or-runtime-file:' + rel)
        key = prefix + relative_key(rel)
        files.append(file_record(role, key, p, note=note))
        sources[key] = dict(root=str(root), path=rel)


def _remap_evidence(evidence):
    ev = copy.deepcopy(evidence)
    for f in ev['body_fragments'] + ev['captions']:
        f['crop'] = 'package/' + relative_key(f['crop'])
    return ev


def build_manifest(retention, package, output, *, article=None, package_id,
                   handoff_dir=None, job=None, review=None, export=None, page=None,
                   legacy_pdfs=None, dispositions=None, document_bindings=None, test_root=None):
    """Build from accepted retained acquisition and recomputed source representation.

    document_bindings maps package document identity to acquisition source ID.
    A mapping cannot override hashes; operator identity assertions remain labeled.
    """
    import source_package as adapter
    roots = trusted_modules()
    from pdf_enrichment.package_io import SourcePackage
    from pdf_enrichment import requests
    retention, package, output = absolute(retention), absolute(package), absolute(output)
    protected = [retention.parent, package] + [absolute(x) for x in (handoff_dir, job, review, export) if x]
    if page: protected.append(absolute(page))
    external(output, protected)
    before = {str(r): tree(r) for r in protected if r.is_dir()}
    retained, scope = adapter.validate_retention(retention)
    identity = retained['acquisition']['article']
    require(article is None or article == identity, 'article-identity-mismatch')
    pkg = SourcePackage(package, method=roots['pdf_source_package'])
    require(not pkg.historical, 'current-verified-package-required')
    state = pkg.current_state
    pdfs = {r['id']: r for r in retained['acquisition']['files'] if r['format'] == 'pdf'}
    bindings = document_bindings or {d['identity']: d['identity'] for d in pkg.documents}
    require(set(bindings) == {d['identity'] for d in pkg.documents} and
            set(bindings.values()) == set(pdfs) and len(bindings) == len(pdfs), 'source-document-association-required')
    diagnostic_documents = []
    for d in pkg.documents:
        row = pdfs[bindings[d['identity']]]
        require(d['sha256'] == row['sha256'] and d['page_count'] == row['page_count'], 'source-document-hash-association')
        if d['extraction_scope'] != 'whole-document' or set(d['pages']) != set(range(1, d['page_count']+1)):
            diagnostic_documents.append(d['identity'])
    files, sources = [], {}
    _collect_tree(files, sources, 'source-retention', retention.parent, 'retention/', 'Unchanged acquisition, original identity basis and diagnostics')
    original_keys = {'retention/' + r['path']: r for r in retained['acquisition']['files']}
    for f in files:
        if f['key'] in original_keys:
            row = original_keys[f['key']]
            require(f['sha256'] == row['sha256'], 'retained-original-hash')
            f.update(role='source-original', binds=dict(source_id=row['id'], source_role=row['role'],
                source_version=identity['version'], identity_verification=row['identity_verification']))
    _collect_tree(files, sources, 'source-package', package, 'package/', 'Unchanged source/runtime evidence')
    for root, role, prefix in ((handoff_dir, 'handoff', 'handoff/'), (job, 'enrichment-job', 'job/'),
                               (review, 'enrichment-review', 'review/'), (export, 'enrichment-export', 'export/')):
        if root: _collect_tree(files, sources, role, root, prefix, 'Unchanged historical evidence; not automatically promoted')
    # Optional handoff and qualified export inputs must be independently revalidated.
    if handoff_dir:
        h = load(absolute(handoff_dir)/'handoff.json')
        require(h['status'] != 'test-only' or test_root is not None, 'explicit-fixture-root-required')
        actual = adapter.build_handoff(retention, package, h['launcher_result'], roots['pdf_source_package'],
                                      test_root=test_root if h['status'] == 'test-only' else None, historical=True)
        adapter.retain_code_provenance(actual, h)
        require(h == actual, 'handoff-revalidation-mismatch')
        _collect_tree(files, sources, 'handoff', absolute(h['launcher_result']).parent, 'launcher/', 'Code-owned acquisition launcher evidence')
        if h.get('inspection_dir'):
            _collect_tree(files, sources, 'handoff', h['inspection_dir'], 'inspections/', 'Inspection findings and raw responses')
    if handoff_dir:
        for field in ('facts_path', 'results_path', 'summary_path'):
            report = absolute(h[field])
            if not any(inside(s['root'], s['path']) == report for s in sources.values()):
                key = 'source-report/' + field + '/' + relative_key(report.name)
                files.append(file_record('handoff', key, report))
                sources[key] = dict(root=str(report.parent), path=report.name)
    if job:
        from qualified_enrichment import runtime
        job_path = absolute(job)
        if (job_path/'selection.json').exists():
            job_state = runtime.read_job(job_path)
        else:
            job_state = runtime.read_run(job_path/'v7' if (job_path/'v7').is_dir() else job_path)
        require(job_state['source_package'] == str(package), 'job-wrong-source-package')
    if export:
        require(review and job, 'export-requires-review-and-runtime-evidence')
        from qualified_enrichment.exports import verify_export
        # No promotion here: production eligibility remains in the retained export.
        verified_export = verify_export(absolute(export)/'handoff.json', str(package), production=False)
        require(verified_export['review_root'] == str(absolute(review)), 'export-review-root-binding')
    if review:
        require(job, 'review-requires-runtime-evidence')
        from qualified_enrichment.reviews import verify, decisions
        dossier = verify(absolute(review)); decisions(absolute(review), dossier)
        require(dossier['snapshot']['source_package'] == str(package) and
                absolute(dossier['snapshot']['path']).is_relative_to(absolute(job)), 'review-wrong-source-or-job')
    if page:
        p = absolute(page); key = 'page/' + relative_key(p.name)
        files.append(file_record('page', key, p)); sources[key] = dict(root=str(p.parent), path=p.name)
    for value in legacy_pdfs or []:
        p = absolute(value); key = 'legacy/' + relative_key(p.name)
        files.append(file_record('legacy-pdf', key, p)); sources[key] = dict(root=str(p.parent), path=p.name)
    # Preserve all review/export/raw-run evidence. This deliberately over-includes
    # history rather than guessing which warning a later consumer may need.
    inherited = sorted(f['key'] for f in files if f['role'].startswith('enrichment-') or f['role'] == 'handoff')
    common = sorted(set(inherited + [f['key'] for f in files if f['role'] in ('source-retention', 'source-original')]
                        + ['package/manifest.json']))
    records = {f['key']: f for f in files}
    elements, documents = [], []
    eligibility = {r['element_id']: r for r in pkg.eligible_elements(['figure', 'table'])}
    for d in pkg.documents:
        source_id = bindings[d['identity']]
        documents.append(dict(identity=d['identity'], source_id=source_id, source_sha256=d['sha256'],
            source_version=identity['version'], raw_key='package/'+d['raw'], complete=d['source_complete'],
            fixture=d['source_fixture'], gaps=d['gaps'], source_role=pdfs[source_id]['role']))
        for e in d['elements']:
            ev = _remap_evidence(requests._base_evidence(pkg, d, e))
            frags = [dict(fragment_id=f['id'], page=f['page'], bbox=f['bbox'],
                          crop_key='package/'+f['crop'], crop_sha256=f.get('crop_sha256'))
                     for f in e['ordered_source_fragments']]
            deps = set(common + ['package/'+d['raw'], 'retention/'+pdfs[source_id]['path']])
            pages = set(f['page'] for f in frags)
            for f in ev['body_fragments'] + ev['captions']:
                deps.add(f['crop']); pages.add(f['page'])
            deps.update(f['crop_key'] for f in frags)
            native_keys = []
            for n in sorted(pages):
                info = d['pages'][n]  # document scoped, never page-number globbing
                for field in ('native_text', 'page_image'):
                    require(info.get(field), 'missing-page-context:'+d['identity']+':'+str(n))
                    key = 'package/' + relative_key(info[field]); deps.add(key)
                    if field == 'native_text': native_keys.append(key)
            require(deps <= records.keys(), 'missing-source-representation-dependency')
            kind = eligibility[e['id']]['kind']
            elements.append(dict(element_id=e['id'], document=d['identity'], source_sha256=d['sha256'],
                content_type=e['content_type'], kind=kind, eligible=kind is not None, label=e.get('label'),
                fragments=frags, caption_note_refs=copy.deepcopy(e['caption_note_refs']),
                evidence=ev, source_element=copy.deepcopy(e), dependencies=sorted(deps),
                inherited=inherited, context=dict(native_text_keys=native_keys,
                    heading_unit_footnote_scope='whole physical page; associations remain unverified'),
                unavailable=[] if ev['captions'] else [dict(kind='caption-not-associated', detail='No associated caption in verified source representation; do not infer absence from article.')]))
    holds = adapter.holds_for(retained, state, package)
    holds.extend('diagnostic-not-whole-document:' + d for d in diagnostic_documents)
    fixture = bool(state['fixture'])
    mechanical_holds = [h for h in holds if h != 'fixture-not-production' and not h.startswith('fixture-or-replay-')]
    acquisition = retained['acquisition']
    auto_dispositions = [dict(kind='acquisition', detail=copy.deepcopy(acquisition['obligations'])),
        dict(kind='attachments', detail=copy.deepcopy(acquisition['attachments'])),
        dict(kind='attempts', detail=copy.deepcopy(acquisition['attempts'])),
        dict(kind='source-file-dispositions', detail=[dict(source_id=r['id'], role=r['role'], format=r['format'],
            disposition=r.get('extraction_disposition', 'PDF extraction scope is recorded per document')) for r in acquisition['files']]),
        dict(kind='source-extraction', detail=copy.deepcopy(state['facts'])),
        dict(kind='algorithm-policy', detail='Algorithms and code are deferred, never included in the eligible roster.')]
    m = dict(schema=SCHEMA, package_id=package_id, article=identity, article_key=article_key(identity),
        created_at=now_utc(), files=files, total_objects=len(files), documents=documents, elements=elements,
        common_dependencies=common, dispositions=auto_dispositions + (dispositions or []),
        source_status=dict(complete=not mechanical_holds, fixture=fixture, holds=mechanical_holds,
            acquisition_verified=True, extraction_verified=True, identity_basis=retained['identity_basis']),
        provenance=dict(source_schema=pkg.schema, source_tree_sha256=pkg.snapshot['tree_sha256'],
            method_code=tree(roots['pdf_source_package']/'pdf_source_package'),
            fixture=fixture, original_document_bindings=bindings,
            statement='Identity is operator asserted; hashes and extraction bindings are code verified. Scientific acceptance is not established.'))
    validate_manifest(m)
    require(before == {str(r): tree(r) for r in protected if r.is_dir()}, 'inputs-changed-during-build')
    destination = new_directory(output)
    save(destination/'manifest.json', m)
    save(destination/'local-map.json', dict(schema='portable-article-local-map-v2',
        manifest_sha256=sha(destination/'manifest.json'), sources=sources))
    verify_local(destination/'manifest.json')
    return m


def _diagnostic_value(package, elements):
    """Recompute a local diagnostic bundle; never assert article acquisition.

    The whole saved inventory is retained and verified, but only exact selected
    logical element IDs become requests. No candidate is promoted or retyped.
    """
    roots = trusted_modules()
    from pdf_enrichment.package_io import SourcePackage
    from pdf_enrichment import requests
    package = absolute(package)
    before = tree(package)  # reject links before the source reader opens files
    require(isinstance(elements, list) and elements and all(isinstance(e,str) and e for e in elements) and
            len(elements)==len(set(elements)), 'diagnostic-explicit-roster-required')
    pkg = SourcePackage(package, method=roots['pdf_source_package'])
    require(not pkg.historical, 'diagnostic-current-source-required')
    index = {r['element_id']:r for r in pkg.eligible_elements(['figure','table'])}
    require(set(elements)<=index.keys() and all(index[e]['kind'] in ('figure','table') for e in elements),
            'diagnostic-selected-element-ineligible')
    files, sources = [], {}
    _collect_tree(files, sources, 'source-package', package, 'package/', 'Unchanged diagnostic source evidence; not an article archive')
    common = sorted(f['key'] for f in files)
    # Retain every original. Project recorded warning metadata through the same
    # history reader used by production; raw request/response wires stay refs.
    inherited = common
    documents = []
    holds = ['diagnostic-only', 'article-acquisition-and-association-not-established', 'scientific-acceptance-not-established']
    dispositions = [dict(kind='source-extraction',detail=copy.deepcopy(pkg.current_state['facts']))]
    for d in pkg.documents:
        original = next(doc for doc in pkg.manifest['documents'] if doc['identity']==d['identity'])
        selected_pages = copy.deepcopy(original['selected_pages'])
        whole = d['extraction_scope']=='whole-document' and selected_pages==list(range(1,d['page_count']+1))
        if not whole: holds.append('diagnostic-not-whole-document:'+d['identity'])
        if not d['source_complete']: holds.append('source-incomplete:'+d['identity'])
        documents.append(dict(identity=d['identity'],source_sha256=d['sha256'],source_version=d['sha256'],
            raw_key='package/'+d['raw'],complete=bool(whole and d['source_complete']),fixture=d['source_fixture'],
            page_count=d['page_count'],selected_pages=selected_pages,extraction_scope=d['extraction_scope'],gaps=d['gaps']))
        dispositions.append(dict(kind='source-document',detail=dict(document=d['identity'],gaps=d['gaps'],
            logical_dispositions=d['logical_dispositions'],source_complete=d['source_complete'])))
    status=dict(complete=False,fixture=bool(pkg.current_state['fixture']),holds=holds,
        acquisition_verified=False,extraction_verified=True,identity_basis='Saved document identities and PDF hashes only; no bibliographic article association')
    selected=[]
    for eid in elements:
        row=index[eid]; d=pkg.doc(row['document']); e=row['element']
        ev=_remap_evidence(requests._base_evidence(pkg,d,e))
        require(ev['body_fragments'], 'diagnostic-body-fragment-required')
        ev['diagnostic_context']=dict(scope='selected-diagnostic',source_status=status,dispositions=dispositions)
        frags=[dict(fragment_id=f['id'],page=f['page'],bbox=f['bbox'],crop_key='package/'+f['crop'],
                    crop_sha256=f.get('crop_sha256')) for f in e['ordered_source_fragments']]
        pages=sorted({f['page'] for f in ev['body_fragments']+ev['captions']})
        native=[]
        for n in pages:
            require(d['pages'][n].get('native_text') and d['pages'][n].get('page_image'), 'missing-page-context')
            native.append('package/'+relative_key(d['pages'][n]['native_text']))
        selected.append(dict(element_id=eid,document=d['identity'],source_sha256=d['sha256'],content_type=e['content_type'],
            kind=row['kind'],eligible=True,label=e.get('label'),fragments=frags,caption_note_refs=copy.deepcopy(e['caption_note_refs']),
            evidence=ev,source_element=copy.deepcopy(e),dependencies=common,inherited=inherited,
            context=dict(native_text_keys=native,heading_unit_footnote_scope='whole physical page; associations remain unverified'),
            unavailable=[] if ev['captions'] else [dict(kind='caption-not-associated',detail='No associated caption in verified source representation; not evidence of article absence.')]))
    value=dict(schema=DIAGNOSTIC_SCHEMA,scope='selected-diagnostic',roster=elements,
        package_id='diagnostic-'+digest(before)[:20],article=None,article_key=None,
        production_complete=False,page_refresh_complete=False,files=files,total_objects=len(files),
        documents=documents,elements=selected,common_dependencies=common,source_status=status,dispositions=dispositions,
        provenance=dict(source_schema=pkg.schema,source_tree_sha256=pkg.snapshot['tree_sha256'],fixture=status['fixture'],
            method_code=tree(roots['pdf_source_package']/'pdf_source_package'),
            statement='Verified saved source bundle; original document identities retained, article acquisition unverified. Diagnostic selection only.'))
    require(tree(package)==before, 'inputs-changed-during-diagnostic-build')
    validate_manifest(value)
    return value,sources


def build_diagnostic(package, output, *, elements):
    package,output=absolute(package),absolute(output)
    external(output,[package])
    value,sources=_diagnostic_value(package,elements)
    new_directory(output); save(output/'manifest.json',value)
    save(output/'local-map.json',dict(schema='portable-article-local-map-v2',manifest_sha256=sha(output/'manifest.json'),sources=sources))
    verify_diagnostic(output/'manifest.json')
    return value


def verify_diagnostic(manifest_path):
    m,paths=verify_local(manifest_path)
    require(m['schema']==DIAGNOSTIC_SCHEMA, 'diagnostic-source-contract-required')
    root=paths['package/manifest.json'].parent
    require(all(paths[f['key']]==inside(root,f['key'].removeprefix('package/')) for f in m['files']),
            'diagnostic-original-package-layout-required')
    actual,_=_diagnostic_value(root,m['roster'])
    from pdf_enrichment.trusted import validate_code_provenance
    actual['provenance']['method_code'] = validate_code_provenance(m['provenance']['method_code'])
    require(m==actual, 'diagnostic-source-recomputation-mismatch')
    return m['source_status']


def element_index(package):
    """Compatibility discovery only; archive creation uses the verified build path."""
    roots = trusted_modules()
    from pdf_enrichment.package_io import SourcePackage
    return [r for r in SourcePackage(package, method=roots['pdf_source_package']).eligible_elements(['figure','table'])]


def closure_for(manifest, elements):
    validate_manifest(manifest)
    require(isinstance(elements, list) and elements and len(elements) == len(set(elements)), 'empty-or-duplicate-selection-rejected')
    index = {e['element_id']: e for e in manifest['elements']}
    require(set(elements) <= index.keys(), 'unknown-element')
    return set(manifest['common_dependencies']).union(*(set(index[e]['dependencies']) for e in elements))


def _history_scope(value, inherited=None, *, document=False):
    scope=dict(inherited or {})
    for key in ('document','source_document','source_sha256','element_id'):
        if isinstance(value.get(key),str) and value[key]:
            scope['document' if key=='source_document' else key]=value[key]
    if document:
        if isinstance(value.get('identity'),str): scope['document']=value['identity']
        if isinstance(value.get('sha256'),str): scope['source_sha256']=value['sha256']
    return scope


def _history_matches(scope, element):
    # Labels, page numbers and local IDs are not cross-document identities.
    return all(scope.get(k,element[k])==element[k] for k in ('document','source_sha256','element_id'))


def qualification_projection(value, *, element=None, scope=None):
    """Project metadata only; never embed prior exports or request/image bodies.

    Unknown warning metadata is conservatively retained with its JSON pointer.
    Omitted raw payloads remain hash-addressable in the same archive. There is no
    model-based pruning, length limit, or implicit resolution across revisions.
    """
    result=[]
    if isinstance(value, dict) and value.get('schema') in (
            'qualified-enrichment-export-v1', 'qualified-enrichment-export-v2', 'portable-qualified-export-v2', 'portable-qualified-export-v3', 'portable-qualified-export-v4'):
        trusted_modules()
        from qualified_enrichment.exports import exact_view, content_targets
        current=value['schema'] in ('qualified-enrichment-export-v2','portable-qualified-export-v4')
        for view in value['elements']:
            if element is not None and not _history_matches(_history_scope(view,scope),element): continue
            if current:
                findings=[f for f in view['findings'] if f['status']=='unresolved' or f.get('resolutions')]
                if findings: result.append(dict(element_id=view['element_id'],source_sha256=view['source_sha256'],findings=findings))
                continue
            targets=sorted(set([''] + content_targets(view['outcome']) +
                [f['target'] for f in view['findings']] + [c['target'] for c in view['coverage']]))
            scopes=[]
            for target in targets:
                exact=exact_view(view,target,purpose='exact',qualification='Archived scoped review; originals unchanged.')
                scopes.append({k:v for k,v in exact.items() if k!='content'})
            result.append(dict(element_id=view['element_id'],source_sha256=view['source_sha256'],
                findings=view['findings'],coverage=view['coverage'],review_status=view['review_status'],scopes=scopes))
        if element is None: return result
        # Scoped views do not replace genuinely unscoped export-level warnings.
        value={k:v for k,v in value.items() if k!='elements' and (not current or k not in ('notice','dispositions','request_accounting','review_bindings'))}
    metadata={'findings','automatic_findings','warnings','warning','notice','limitations','unresolved',
              'coverage','resolutions','dispositions','holds','unavailable','uncertainty','uncertainties'}
    omitted={'inherited_history','consumer_views','messages','response_body','request_wire'}
    if element is not None:
        metadata |= {'limitation','source_limitation','gaps','model_root_uncertainty','coverage_warnings'}
    def walk(v,pointer='',parent_scope=None,attribution=None,document=False):
        if isinstance(v,dict):
            current=_history_scope(v,parent_scope,document=document)
            if element is not None and not _history_matches(current,element): return
            author=v.get('reviewer',v.get('provenance',attribution))
            for key,item in v.items():
                if key in omitted: continue
                target=pointer+'/'+key.replace('~','~0').replace('/','~1')
                if key in metadata:
                    if element is None:
                        result.append(dict(target=target,metadata=item,
                            attribution=v.get('reviewer',v.get('provenance')),
                            association='Historical metadata; scope as recorded, not a new correction.'))
                    else:
                        # Each actual finding keeps its recorded scope/author.
                        # Empty/null containers are not warnings or model context.
                        for i,entry in enumerate(item if isinstance(item,list) else [item]):
                            scoped=_history_scope(entry,current) if isinstance(entry,dict) else current
                            if entry in (None,[],{},'') or not _history_matches(scoped,element): continue
                            result.append(dict(target=target+('/'+str(i) if isinstance(item,list) else ''),metadata=entry,
                                scope=scoped or 'unscoped',attribution=entry.get('reviewer',entry.get('provenance',author)) if isinstance(entry,dict) else author,
                                association='Historical metadata; scope as recorded, not a new correction.'))
                else: walk(item,target,current,author,key=='documents')
        elif isinstance(v,list):
            for i,item in enumerate(v): walk(item,pointer+'/'+str(i),parent_scope,attribution,document)
    walk(value,parent_scope=scope)
    return result


def prompt_history(paths, keys, element):
    """Selected prompt projection only; consumer/archive history is unchanged."""
    directories={}
    # Use recorded directory associations, never a filename/label/page guess.
    for key,path in paths.items():
        if Path(key).name not in ('manifest.json','initial-plan.json','classification-plan.json','association-plan.json','prepared.json'): continue
        value=load(path)
        if not isinstance(value,dict): continue
        prefix=str(Path(key).parent)+'/' if '/' in key else ''
        if value.get('schema')=='pdf-source-package-v1':
            for doc in value['documents']:
                directories[prefix+doc['directory']+'/']=_history_scope(doc,document=True)
        for row in value.get('requests',[]):
            if row.get('directory'):
                directories[prefix+row['directory']+'/']=_history_scope(row)
    result=[]; seen=set()
    for key in sorted(keys):
        path=paths[key]; scope={}
        for directory,association in sorted(directories.items(),key=lambda x:len(x[0])):
            if key.startswith(directory): scope.update(association)
        if not _history_matches(scope,element): continue
        if path.suffix=='.json' and Path(key).name not in ('request-wire.json','response-body.json'):
            qualifications=qualification_projection(load(path),element=element,scope=scope)
        elif path.suffix in ('.txt','.md') and ('review' in key.split('/') or 'findings' in Path(key).name):
            qualifications=[dict(metadata=path.read_text(),scope=scope or 'unscoped',association='Unscoped historical review text')]
        else: continue
        unique=[]
        for q in qualifications:
            # Identical decoded/result projections share one representative raw
            # reference. Different scope, attribution or finding values survive.
            target=q.get('target','')
            # Only known duplicate decoder wrappers are interchangeable. Keep
            # cell/fragment indexes and other target paths distinct.
            while target.split('/')[1:2] in (['mapped'],['raw_selection'],['raw_alias_selection'],['validator_input']):
                target=target[target.index('/',1):] if '/' in target[1:] else ''
            identity=digest(dict({k:v for k,v in q.items() if k!='target'},target=target))
            if identity not in seen:
                seen.add(identity); unique.append(q)
        if unique: result.append(dict(key=key,sha256=sha(path),qualifications=unique,raw_retained=True))
    return result


def history_refs(paths, keys):
    history=[]
    for key in sorted(keys):
        p=paths[key]; entry=dict(key=key,sha256=sha(p))
        # These are raw wire envelopes, not standalone review metadata. Their
        # interpreted outcomes/findings remain in the retained reviews/exports.
        if p.suffix=='.json' and p.name not in ('request-wire.json','response-body.json'):
            entry['qualifications']=qualification_projection(load(p))
        elif p.suffix in ('.txt','.md') and ('review' in key.split('/') or 'findings' in p.name):
            entry['qualifications']=[dict(metadata=p.read_text(),association='Unscoped historical review text')]
        entry['raw_retained']=True
        history.append(entry)
    return history


def consume(manifest_path, elements=None, *, purpose='discovery', qualification=None):
    m = validate_manifest(load(manifest_path))
    if m['schema']==DIAGNOSTIC_SCHEMA:
        verify_source(manifest_path)
        require(elements is None or elements==m['roster'], 'diagnostic-consumer-roster-binding')
    ids = [e['element_id'] for e in m['elements']] if elements is None else elements
    keys = closure_for(m, ids) if ids else set(m['common_dependencies'])
    _, paths = verify_local(manifest_path, keys)
    require(purpose in ('discovery', 'summary', 'exact'), 'consumer-purpose')
    require(purpose != 'exact' or isinstance(qualification, str) and qualification.strip(), 'exact-use-requires-explicit-qualification')
    inherited=set(m['common_dependencies']).union(*(set(e['inherited']) for e in m['elements'] if e['element_id'] in ids))
    history=history_refs(paths,keys & inherited)
    return dict(schema='portable-article-consumer-v3', article=m['article'], elements=[e for e in m['elements'] if e['element_id'] in ids],
                source_status=m['source_status'], dispositions=m['dispositions'], history=history,
                purpose=purpose, qualification=qualification, scientific_acceptance='not-established',
                **(dict(scope='selected-diagnostic',production_complete=False,page_refresh_complete=False)
                   if m['schema']==DIAGNOSTIC_SCHEMA else {}))


def revision_prefix(m, prefix):
    return relative_key(prefix) + '/articles/' + m['article_key'] + '/revisions/' + m['package_id']


def object_key(m, prefix, record):
    # Schema is the storage contract: saved v2 keys never change meaning.
    require(m.get('schema') in (SCHEMA, LEGACY_SCHEMA), 'manifest-schema')
    root = (revision_prefix(m, prefix) if m['schema'] == LEGACY_SCHEMA else
            relative_key(prefix) + '/articles/' + m['article_key'])
    return root + '/objects/' + record['sha256']


class RcloneTransport:
    """Trusted remote/bucket from caller; immutable content-addressed objects.

    --immutable and --ignore-existing protect existing keys. rclone is not CAS:
    concurrent conforming writers at the same hash key can only write identical
    bytes. No mutable latest key. Read-back detects corrupt/nonconforming writers;
    it does not promise protection against a hostile writer changing objects later.
    """
    def __init__(self, remote, bucket, runner=None):
        require(isinstance(remote, str) and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]*', remote), 'safe-remote-required')
        require(isinstance(bucket, str) and re.fullmatch('[a-z0-9][a-z0-9.-]*', bucket), 'safe-bucket-required')
        self.remote, self.bucket, self.runner = remote, bucket, runner or _run_rclone
    def _target(self, key):
        return self.remote + ':' + self.bucket + '/' + relative_key(key)
    def call(self, argv, output=None):
        return self.runner(['rclone'] + argv + ['--s3-no-check-bucket', '--retries', '1', '--low-level-retries', '1',
                            '--contimeout', '30s', '--timeout', '120s'], output=output, timeout=300)
    def object_exists(self, key):
        return bool(self.call(['lsf', self._target(key), '--max-depth', '1']).strip())
    def download(self, key, target, expected_hash=None, expected_size=None, limit=MAX_OBJECT_BYTES):
        p = absolute(target)
        with p.open('xb') as stream:
            self.call(['cat', self._target(key), '--count', str((expected_size if expected_size is not None else limit)+1)], output=stream)
            stream.flush(); os.fsync(stream.fileno())
        require(p.stat().st_size <= limit, 'remote-object-size-limit')
        if expected_size is not None: require(p.stat().st_size == expected_size, 'remote-size-mismatch')
        if expected_hash is not None: require(sha(p) == expected_hash, 'remote-object-hash-mismatch')
        return p
    def verify(self, key, expected_hash, expected_size):
        with tempfile.TemporaryDirectory(prefix='article-readback-') as tmp:
            self.download(key, Path(tmp)/'object', expected_hash, expected_size)
        return dict(key=key, sha256=expected_hash, size=expected_size, method='read_back_sha256')
    def upload(self, local, key, expected_hash, expected_size):
        p = absolute(local)
        require(sha(p) == expected_hash and p.stat().st_size == expected_size, 'local-upload-input-changed')
        reused = self.object_exists(key)
        if not reused:
            # Upload a verified private snapshot, not a mutable external input.
            with tempfile.TemporaryDirectory(prefix='article-upload-') as tmp:
                snapshot = Path(tmp)/'object'; shutil.copyfile(p, snapshot)
                require(sha(snapshot) == expected_hash and snapshot.stat().st_size == expected_size, 'local-upload-input-changed')
                self.call(['copyto', str(snapshot), self._target(key), '--immutable', '--ignore-existing'])
        result = self.verify(key, expected_hash, expected_size)
        require(sha(p) == expected_hash and p.stat().st_size == expected_size, 'local-upload-input-changed')
        return dict(result, reused=reused, verified_at=now_utc())


def _run_rclone(argv, *, output=None, timeout=300):
    require(argv and argv[0] == 'rclone', 'rclone-argv-required')
    try:
        result = subprocess.run(argv, stdout=output if output is not None else subprocess.PIPE,
                                stderr=subprocess.DEVNULL, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise ValueError('rclone-timeout') from exc
    if result.returncode == 3 and argv[1] == 'lsf':
        return ''  # documented directory-not-found, not authentication failure
    require(result.returncode == 0, 'rclone-failed:' + argv[1])
    return result.stdout.decode('utf-8') if output is None else ''


def publish(manifest_path, remote, bucket, prefix, *, runner=None):
    relative_key(prefix)
    path = absolute(manifest_path)
    m, paths = verify_local(path)  # even reused remote objects do not waive current input validation
    require(m['schema'] != DIAGNOSTIC_SCHEMA, 'diagnostic-publication-forbidden')
    initial = sha(path)
    transport = RcloneTransport(remote, bucket, runner)
    receipts = []
    for f in m['files']:
        receipts.append(transport.upload(paths[f['key']], object_key(m, prefix, f), f['sha256'], f['size']))
    verify_local(path)
    require(sha(path) == initial, 'manifest-changed-during-publish')
    key = revision_prefix(m, prefix) + '/manifests/' + initial + '.json'
    receipts.append(transport.upload(path, key, initial, path.stat().st_size))
    return dict(schema='portable-article-publication-v2', prefix=prefix, article_key=m['article_key'],
        verification_scope='offline-transport-double' if runner is not None else 'rclone-live-readback',
        remote=remote, bucket=bucket, manifest_key=key, manifest_sha256=initial,
        objects=len(m['files']), uploaded=sum(not r['reused'] for r in receipts), receipts=receipts, published_at=now_utc())


def restore(manifest_path, destination, *, elements=None, include_package=True, include_enrichment=True,
            include_page=True, remote=None, bucket=None, prefix=None, runner=None):
    path = absolute(manifest_path); m = validate_manifest(load(path)); original_hash = sha(path)
    require(m['schema'] != DIAGNOSTIC_SCHEMA, 'diagnostic-archive-restore-forbidden')
    destination = absolute(destination)
    require(not destination.exists(), 'destination-must-be-new')
    require(elements is None or isinstance(elements, list) and elements, 'empty-selection-rejected')
    keys = {f['key'] for f in m['files']}
    want = closure_for(m, elements) if elements is not None else set(keys)
    want = {f['key'] for f in m['files'] if f['key'] in want and
        (include_package or f['role'] != 'source-package') and
        (include_enrichment or not f['role'].startswith('enrichment-')) and (include_page or f['role'] != 'page')}
    require(want, 'nothing-selected-to-restore')
    transport = None
    if remote:
        require(bucket and prefix, 'trusted-remote-binding-required')
        relative_key(prefix); transport = RcloneTransport(remote, bucket, runner)
        external(destination, [path.parent])
        paths = {}
    else:
        _, paths = verify_local(path, want)
        external(destination, [path.parent] + [p.parent for p in paths.values()])
    # All manifest and source validation precedes the first destination write.
    new_directory(destination)
    restored, mapping = [], {}
    for f in m['files']:
        key = f['key']
        if key not in want: continue
        target = inside(destination, key); target.parent.mkdir(parents=True, exist_ok=True)
        if transport:
            transport.download(object_key(m, prefix, f), target, f['sha256'], f['size'])
        else:
            with paths[key].open('rb') as src, target.open('xb') as dst:
                shutil.copyfileobj(src, dst, 1024*1024)
                dst.flush(); os.fsync(dst.fileno())
            require(target.stat().st_size == f['size'] and sha(target) == f['sha256'], 'restore-hash-mismatch')
        restored.append(key); mapping[key] = dict(root=str(destination), path=key)
    require(sha(path) == original_hash, 'manifest-changed-during-restore')
    put(destination/'manifest.json', path.read_bytes())  # byte-identical index, not fabricated materialization
    save(destination/'local-map.json', dict(schema='portable-article-local-map-v2',manifest_sha256=original_hash,sources=mapping))
    excluded = not (include_package and include_enrichment and include_page)
    completed = 'partial-package' if excluded else 'selected-elements' if elements is not None else 'full-package'
    receipt = dict(schema='portable-article-restore-v2', manifest_sha256=original_hash, restored=sorted(restored),
        restored_count=len(restored), unavailable=sorted(keys-want), requested_elements=elements,
        completed=completed, from_remote=bool(remote), restored_at=now_utc(), destination=str(destination))
    verify_local(destination/'manifest.json', want)
    save(destination/'RESTORE-RECEIPT.json', receipt)
    return receipt


def restore_remote(manifest_key, manifest_sha256, destination, *, remote, bucket, prefix, article_key,
                   runner=None, **kwargs):
    relative_key(manifest_key); relative_key(prefix); _hash(manifest_sha256); _hash(article_key)
    expected = prefix + '/articles/' + article_key + '/revisions/'
    require(manifest_key.startswith(expected) and manifest_key.endswith('/manifests/'+manifest_sha256+'.json'), 'trusted-manifest-key-binding')
    # Caller supplies expected key AND hash and trusted transport, never a URL from archive data.
    transport = RcloneTransport(remote, bucket, runner)
    with tempfile.TemporaryDirectory(prefix='article-manifest-') as tmp:
        path = Path(tmp)/'manifest.json'
        transport.download(manifest_key, path, manifest_sha256, limit=MAX_MANIFEST_BYTES)
        m = validate_manifest(load(path))
        require(m['article_key'] == article_key and manifest_key == revision_prefix(m, prefix)+'/manifests/'+manifest_sha256+'.json', 'manifest-identity-prefix-binding')
        return restore(path, destination, remote=remote, bucket=bucket, prefix=prefix, runner=runner, **kwargs)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    b = sub.add_parser('manifest')
    for name in ('retention', 'package', 'output', 'package-id'): b.add_argument('--'+name, required=True)
    for name in ('handoff', 'job', 'review', 'export', 'page', 'document-bindings', 'fixture-root'): b.add_argument('--'+name)
    b.add_argument('--legacy-pdf', action='append')
    d = sub.add_parser('diagnostic-manifest')
    for name in ('package','output'): d.add_argument('--'+name, required=True)
    d.add_argument('--element', action='append', required=True)
    p = sub.add_parser('publish'); p.add_argument('--manifest', required=True)
    for name in ('remote', 'bucket', 'prefix'): p.add_argument('--'+name, required=True)
    r = sub.add_parser('restore'); r.add_argument('--manifest')
    for name in ('manifest-key', 'manifest-sha256', 'article-key', 'remote', 'bucket', 'prefix'): r.add_argument('--'+name)
    r.add_argument('--destination', required=True); r.add_argument('--element', action='append')
    for name in ('package', 'enrichment', 'page'): r.add_argument('--no-'+name, action='store_true')
    c = sub.add_parser('consume'); c.add_argument('--manifest', required=True); c.add_argument('--element', action='append')
    c.add_argument('--purpose', default='discovery'); c.add_argument('--qualification')
    args = parser.parse_args(argv)
    try:
        if args.command == 'manifest':
            result = build_manifest(args.retention, args.package, args.output, package_id=args.package_id,
                handoff_dir=args.handoff, job=args.job, review=args.review, export=args.export, page=args.page,
                legacy_pdfs=args.legacy_pdf, document_bindings=load(args.document_bindings) if args.document_bindings else None, test_root=args.fixture_root)
            result = dict(schema=result['schema'], objects=result['total_objects'], elements=len(result['elements']))
        elif args.command == 'diagnostic-manifest':
            result = build_diagnostic(args.package, args.output, elements=args.element)
            result = dict(schema=result['schema'],scope=result['scope'],roster=result['roster'],
                production_complete=False,page_refresh_complete=False,source_status=result['source_status'])
        elif args.command == 'publish': result = publish(args.manifest, args.remote, args.bucket, args.prefix)
        elif args.command == 'consume': result = consume(args.manifest, args.element, purpose=args.purpose, qualification=args.qualification)
        else:
            flags = dict(elements=args.element, include_package=not args.no_package,
                         include_enrichment=not args.no_enrichment, include_page=not args.no_page)
            if args.manifest_key:
                require(not args.manifest, 'choose-local-or-remote-manifest')
                result = restore_remote(args.manifest_key, args.manifest_sha256, args.destination,
                    remote=args.remote, bucket=args.bucket, prefix=args.prefix, article_key=args.article_key, **flags)
            else:
                require(args.manifest, 'manifest-required')
                result = restore(args.manifest, args.destination, remote=args.remote, bucket=args.bucket, prefix=args.prefix, **flags)
        print(json.dumps(result, indent=2)); return 0
    except (OSError, ValueError, KeyError, TypeError, ImportError) as exc:
        print(json.dumps(dict(status='hold', error=str(exc))), file=sys.stderr); return 2


if __name__ == '__main__':
    sys.exit(main())
