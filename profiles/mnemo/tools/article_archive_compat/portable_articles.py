"""Historical read-only dependency closure; extracted without changing validation contracts."""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from article_archive_compat.article_runtime import absolute, relative_key, inside, sha, require, digest, external, trusted_modules
SCHEMA = 'portable-article-manifest-v3'
FINAL_SCHEMA = 'portable-article-manifest-v4'
SCOPED_FINAL_SCHEMA = 'portable-article-manifest-v5'

def is_final_manifest(m):
    return m.get('schema') in (FINAL_SCHEMA, SCOPED_FINAL_SCHEMA)
LEGACY_SCHEMA = 'portable-article-manifest-v2'
DIAGNOSTIC_SCHEMA = 'selected-diagnostic-source-v1'
ROLES = ('source-original', 'source-package', 'source-retention', 'enrichment-job', 'enrichment-review', 'enrichment-export', 'page', 'legacy-pdf', 'handoff')
MAX_MANIFEST_BYTES = 256 * 1024 * 1024
MAX_OBJECT_BYTES = 4 * 1024 * 1024 * 1024

def now_utc():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def load(path):

    def pairs(items):
        value = {}
        for (key, item) in items:
            require(key not in value, 'duplicate-json-key:' + key)
            value[key] = item
        return value

    def constant(value):
        raise ValueError('nonfinite-json')
    p = absolute(path)
    require(p.stat().st_size <= MAX_MANIFEST_BYTES, f'json-size-limit:{p}:bytes={p.stat().st_size}:limit={MAX_MANIFEST_BYTES}')
    return json.loads(p.read_bytes(), object_pairs_hook=pairs, parse_constant=constant)

def put(path, raw):
    p = absolute(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())

def save(path, value):
    put(path, (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + '\n').encode())

def new_directory(path):
    from article_archive_compat.article_runtime import outside_instance
    outside_instance(path)
    p = absolute(path)
    require(p.parent.is_dir(), 'output-parent-must-exist')
    p.mkdir(mode=448)
    return p

def article_key(article):
    require(isinstance(article, dict) and isinstance(article.get('slug'), str) and re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]*', article['slug']), 'article-slug-required')
    return digest({k: article.get(k) for k in ('slug', 'doi', 'pmid')})

def _hash(value):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'invalid-digest')

def validate_manifest(m):
    require(m.get('schema') in (SCHEMA, LEGACY_SCHEMA, FINAL_SCHEMA, SCOPED_FINAL_SCHEMA, DIAGNOSTIC_SCHEMA), 'manifest-schema')
    require('sources' not in m, 'operational-sources-forbidden-in-archive-manifest')
    if m['schema'] == DIAGNOSTIC_SCHEMA:
        require(m['article'] is None and m['article_key'] is None and (m['scope'] == 'selected-diagnostic'), 'diagnostic-not-bibliographic-article')
        require(m['production_complete'] is False and m['page_refresh_complete'] is False and (m['source_status']['complete'] is False) and (m['source_status']['acquisition_verified'] is False), 'diagnostic-cannot-be-production-complete')
        require(isinstance(m['roster'], list) and m['roster'] and (len(set(m['roster'])) == len(m['roster'])) and (m['roster'] == [e['element_id'] for e in m['elements']]), 'diagnostic-explicit-roster-required')
    else:
        require(m['article_key'] == article_key(m['article']), 'article-key-binding')
    require(re.fullmatch('[a-z0-9][a-z0-9-]*', m['package_id']), 'package-id-required')
    require(isinstance(m['files'], list) and len(m['files']) <= 100000, 'file-inventory-limit')
    (keys, aliases) = (set(), set())
    for f in m['files']:
        key = relative_key(f['key'])
        require(key not in keys and key.casefold() not in aliases, 'duplicate-or-case-alias-key')
        keys.add(key)
        aliases.add(key.casefold())
        _hash(f['sha256'])
        require(type(f['size']) is int and 0 <= f['size'] <= MAX_OBJECT_BYTES, 'invalid-size')
        require(f['role'] in ROLES, 'unknown-role')
    require(m['total_objects'] == len(keys), 'object-count-mismatch')
    for key in keys:
        require(not any((str(p) in keys for p in Path(key).parents if str(p) != '.')), 'file-directory-alias')
    require(not keys.intersection({'manifest.json', 'local-map.json', 'RESTORE-RECEIPT.json'}), 'reserved-output-key')
    docs = {}
    for d in m['documents']:
        require(d['identity'] not in docs, 'duplicate-document')
        _hash(d['source_sha256'])
        require(d['source_version'] and type(d['complete']) is bool and (type(d['fixture']) is bool), 'document-version-status')
        require(d['raw_key'] in keys, 'missing-document-source')
        record = next((f for f in m['files'] if f['key'] == d['raw_key']))
        require(record['sha256'] == d['source_sha256'], 'document-source-hash-binding')
        docs[d['identity']] = d
    require(docs, 'documents-required')
    common = m['common_dependencies']
    require(isinstance(common, list) and len(common) == len(set(common)) and (set(common) <= keys), 'missing-common-dependency')
    history_keys = {f['key'] for f in m['files'] if f['role'].startswith('enrichment-')}
    require(history_keys <= set(common), 'omitted-review-or-export-dependency')
    ids = set()
    for e in m['elements']:
        require(e['element_id'] not in ids and e['document'] in docs, 'element-identity-binding')
        ids.add(e['element_id'])
        require(e['source_sha256'] == docs[e['document']]['source_sha256'], 'element-version-binding')
        require(type(e['eligible']) is bool and (not e['eligible'] or e['kind'] in ('figure', 'table')), 'element-eligibility')
        deps = e['dependencies']
        require(isinstance(deps, list) and len(deps) == len(set(deps)) and (set(deps) <= keys), 'missing-or-duplicate-element-dependency')
        require(set(e['inherited']) <= set(deps), 'missing-inherited-qualification')
        ev = e['evidence']
        require(ev['element_id'] == e['element_id'] and ev['source_document'] == e['document'] and (ev['source_sha256'] == e['source_sha256']), 'evidence-identity-binding')
        for f in list(e['fragments']) + ev.get('body_fragments', []) + ev.get('captions', []):
            key = f.get('crop_key', f.get('crop'))
            require(key in deps, 'missing-crop-dependency')
            if f.get('crop_sha256'):
                require(next((r['sha256'] for r in m['files'] if r['key'] == key)) == f['crop_sha256'], 'crop-hash-binding')
        require(set(e['context']['native_text_keys']) <= set(deps), 'missing-native-context')
        require(isinstance(e['unavailable'], list), 'typed-unavailable-required')
        for u in e['unavailable']:
            require(set(u) == {'kind', 'detail'} and u['kind'] and u['detail'], 'unavailable-disposition')
    status = m['source_status']
    if 'readiness' in status:
        from article_archive_compat import source_package as adapter
        adapter.validate_source_readiness(status['readiness'])
        require(m['schema'] != DIAGNOSTIC_SCHEMA, 'diagnostic-source-readiness-forbidden')
    require(all((type(status[k]) is bool for k in ('complete', 'fixture', 'acquisition_verified', 'extraction_verified'))), 'typed-source-status')
    require(isinstance(status['holds'], list) and isinstance(m['dispositions'], list), 'typed-source-holds')
    completed_docs = list(docs.values())
    if m['schema'] == SCOPED_FINAL_SCHEMA:
        selected = m.get('processing', {}).get('manuscript', {}).get('source_id')
        completed_docs = [d for d in docs.values() if d.get('source_id', d['identity']) == selected]
    require(not status['complete'] or (not status['holds'] and status['acquisition_verified'] and status['extraction_verified'] and completed_docs and all((d['complete'] for d in completed_docs))), 'contradictory-source-completeness')
    require(status['fixture'] or not any((d['fixture'] for d in docs.values())), 'fixture-promotion-forbidden')
    if is_final_manifest(m):
        from article_archive_compat import final_products
        final_products.validate(m)
    return m

def local_sources(manifest_path, m=None):
    manifest_path = absolute(manifest_path)
    m = validate_manifest(load(manifest_path) if m is None else m)
    mapping = load(manifest_path.parent / 'local-map.json')
    require(mapping['schema'] == 'portable-article-local-map-v2' and mapping['manifest_sha256'] == sha(manifest_path), 'local-map-manifest-binding')
    sources = mapping['sources']
    require(isinstance(sources, dict) and set(sources) <= {f['key'] for f in m['files']}, 'local-map-inventory-binding')
    for (key, row) in sources.items():
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
    return (m, paths)

def verify_source(manifest_path):
    """Recheck portable acquisition identity/hash/scope bindings without old paths.

    Synthetic hand-authored contracts are accepted only as permanent fixtures.
    Production claims require retained acquisition and accepted extraction facts.
    The manifest hash is the portable trust anchor for the build-time recomputed
    representation; historical absolute receipt paths are never dereferenced.
    """
    m = validate_manifest(load(manifest_path))
    if is_final_manifest(m):
        verify_local(manifest_path, set(m['common_dependencies']))
        return m['source_status']
    if m['schema'] == DIAGNOSTIC_SCHEMA:
        return verify_diagnostic(manifest_path)
    if m['provenance'].get('source_schema') is None:
        require(m['source_status']['fixture'] and m['provenance'].get('fixture') is True, 'nonfixture-requires-verified-source-provenance')
        return m['source_status']
    required = {'retention/retention.json', 'retention/input.json', 'retention/scope.json', 'package/manifest.json'}
    require(required <= set(m['common_dependencies']), 'missing-source-verification-dependencies')
    (_, paths) = verify_local(manifest_path, set(m['common_dependencies']))
    retained = load(paths['retention/retention.json'])
    from article_archive_compat import source_package as adapter
    require(retained['schema'] == 'source-retention-v1', 'source-retention-schema')
    acquisition = retained['acquisition']
    adapter.validate_acquisition(acquisition)
    require(acquisition['article'] == m['article'] and retained['identity_basis'] == m['source_status']['identity_basis'], 'source-article-identity-binding')
    original = load(paths['retention/input.json'])
    adapter.validate_acquisition(original)
    normalized = copy.deepcopy(acquisition)
    require(len(normalized['files']) == len(original['files']) and len(normalized['attempts']) == len(original['attempts']), 'retained-input-count-binding')
    inventory = {f['key']: f for f in m['files']}
    for (rel, expected) in retained['bindings'].items():
        key = 'retention/' + relative_key(rel)
        require(key in inventory and inventory[key]['sha256'] == expected, 'retention-inventory-binding')
    for (row, before) in zip(normalized['files'], original['files']):
        require(inventory['retention/' + relative_key(row['path'])]['sha256'] == row['sha256'], 'source-original-binding')
        row['path'] = before['path']
        if 'page_count' not in before:
            row.pop('page_count', None)
        row.pop('extraction_disposition', None)
    for (attempt, before) in zip(normalized['attempts'], original['attempts']):
        require(len(attempt['artifacts']) == len(before['artifacts']), 'attempt-artifact-count-binding')
        for (artifact, old) in zip(attempt['artifacts'], before['artifacts']):
            require(inventory['retention/' + relative_key(artifact['path'])]['sha256'] == artifact['sha256'], 'attempt-artifact-binding')
            artifact['path'] = old['path']
    require(normalized == original, 'retained-input-metadata-binding')
    package = load(paths['package/manifest.json'])
    require(package['schema'] == m['provenance']['source_schema'] == 'pdf-source-package-v1', 'source-package-schema-binding')
    docs = {d['identity']: d for d in package['documents']}
    source_rows = {r['id']: r for r in adapter.processing_sources(acquisition)}
    scope = load(paths['retention/scope.json'])
    require(m.get('processing') == acquisition.get('processing') == package.get('processing'), 'portable-processing-binding')
    if 'processing' in acquisition:
        adapter.verify_processing_scope(acquisition, scope, package['documents'])
    require({d['identity'] for d in scope['documents']} == set(source_rows), 'retained-scope-source-roster')
    require(set(docs) == {d['identity'] for d in m['documents']}, 'source-document-roster-binding')
    for d in m['documents']:
        doc = docs[d['identity']]
        src = source_rows[d['source_id']]
        require(d['source_sha256'] == src['sha256'] == doc['sha256'] and doc['page_count'] == src['page_count'] and (d['source_version'] == m['article']['version']) and (d['raw_key'] == 'package/' + doc['raw']) and (m['provenance']['original_document_bindings'][d['identity']] == d['source_id']), 'source-document-version-binding')
        if m['source_status']['complete'] and 'processing' not in acquisition:
            require(doc['extraction_scope'] == 'whole-document' and doc['selected_pages'] == list(range(1, doc['page_count'] + 1)), 'diagnostic-not-complete')
    facts = [r['detail'] for r in m['dispositions'] if r['kind'] == 'source-extraction']
    require(len(facts) == 1, 'extraction-facts-required')
    if 'readiness' in m['source_status']:
        expected = adapter.source_readiness(acquisition, facts[0], fixture=m['source_status']['fixture'], stopped='package/stop.json' in inventory)
        if 'processing' not in acquisition and any((doc['extraction_scope'] != 'whole-document' or doc['selected_pages'] != list(range(1, doc['page_count'] + 1)) or set(doc['channels']) != {'caption', 'figure', 'structured', 'classification', 'association'} for doc in docs.values())):
            expected['holds'] = sorted(set(expected['holds'] + ['diagnostic-not-whole-document']))
        require(m['source_status']['readiness'] == expected, 'source-readiness-binding')
        require(not any((h.startswith('diagnostic-not-whole-document:') for h in m['source_status']['holds'])) or 'diagnostic-not-whole-document' in expected['holds'], 'source-readiness-diagnostic-scope')
    if m['source_status']['complete']:
        require(all((v['status'] == 'retrieved' for v in acquisition['obligations'].values())) and acquisition['attachments']['status'] != 'not-inspected' and all((i['status'] == 'retrieved' for i in acquisition['attachments']['items'])), 'acquisition-incomplete')
        require(all((v['status'] == 'complete' and (not v['uncertain_reservations']) for v in facts[0]['phases'].values())), 'extraction-execution-incomplete')
    if not m['source_status']['fixture']:
        require(not any((v['fixture_or_replay_calls'] for v in facts[0]['phases'].values())), 'source-fixture-promotion')
    return m['source_status']

def verify_diagnostic(manifest_path):
    raise ValueError('historical-diagnostic-runtime-required: not an article archive')

def closure_for(manifest, elements):
    validate_manifest(manifest)
    require(isinstance(elements, list) and elements and (len(elements) == len(set(elements))), 'empty-or-duplicate-selection-rejected')
    index = {e['element_id']: e for e in manifest['elements']}
    require(set(elements) <= index.keys(), 'unknown-element')
    return set(manifest['common_dependencies']).union(*(set(index[e]['dependencies']) for e in elements))

def _history_scope(value, inherited=None, *, document=False):
    scope = dict(inherited or {})
    for key in ('document', 'source_document', 'source_sha256', 'element_id'):
        if isinstance(value.get(key), str) and value[key]:
            scope['document' if key == 'source_document' else key] = value[key]
    if document:
        if isinstance(value.get('identity'), str):
            scope['document'] = value['identity']
        if isinstance(value.get('sha256'), str):
            scope['source_sha256'] = value['sha256']
    return scope

def _history_matches(scope, element):
    return all((scope.get(k, element[k]) == element[k] for k in ('document', 'source_sha256', 'element_id')))

def qualification_projection(value, *, element=None, scope=None):
    """Project metadata only; never embed prior exports or request/image bodies.

    Unknown warning metadata is conservatively retained with its JSON pointer.
    Omitted raw payloads remain hash-addressable in the same archive. There is no
    model-based pruning, length limit, or implicit resolution across revisions.
    """
    result = []
    if isinstance(value, dict) and value.get('schema') in ('article-scientific-products-v1', 'article-scientific-products-v2'):
        for view in value['elements']:
            if element is None or _history_matches(_history_scope(view), element):
                if view['findings']:
                    result.append(dict(element_id=view['element_id'], source_sha256=view['source_sha256'], findings=view['findings']))
        for q in value['qualifications']:
            scope = q.get('scope') if isinstance(q.get('scope'), dict) else _history_scope(q)
            if element is None or _history_matches(scope, element):
                result.append(dict(target=q.get('metadata_target', q.get('target', '')), metadata=q.get('metadata', q.get('reason')), scope=scope or 'unscoped', attribution=q.get('attribution', q.get('provenance'))))
        if value['source_limitations']:
            result.append(dict(target='/source_limitations', metadata=value['source_limitations']))
        return result
    if isinstance(value, dict) and value.get('schema') == 'source-package-handoff-v4':
        return result
    if isinstance(value, dict) and value.get('schema') == 'source-package-handoff-v5':
        result = qualification_projection(value['enrichment'], element=element, scope=scope)
        return [dict(row, target='/enrichment' + row['target']) if 'target' in row else row for row in result]
    if isinstance(value, dict) and value.get('schema') in ('qualified-enrichment-export-v1', 'qualified-enrichment-export-v2', 'portable-qualified-export-v2', 'portable-qualified-export-v3', 'portable-qualified-export-v4'):
        trusted_modules()
        from article_archive_compat.qualified_enrichment.exports import exact_view, content_targets
        current = value['schema'] in ('qualified-enrichment-export-v2', 'portable-qualified-export-v4')
        for view in value['elements']:
            if element is not None and (not _history_matches(_history_scope(view, scope), element)):
                continue
            if current:
                findings = [f for f in view['findings'] if f['status'] == 'unresolved' or f.get('resolutions')]
                if findings:
                    result.append(dict(element_id=view['element_id'], source_sha256=view['source_sha256'], findings=findings))
                continue
            targets = sorted(set([''] + content_targets(view['outcome']) + [f['target'] for f in view['findings']] + [c['target'] for c in view['coverage']]))
            scopes = []
            for target in targets:
                exact = exact_view(view, target, purpose='exact', qualification='Archived scoped review; originals unchanged.')
                scopes.append({k: v for (k, v) in exact.items() if k != 'content'})
            result.append(dict(element_id=view['element_id'], source_sha256=view['source_sha256'], findings=view['findings'], coverage=view['coverage'], review_status=view['review_status'], scopes=scopes))
        if element is None:
            limitations = (value.get('assessment') or {}).get('source_limitations', [])
            if limitations:
                result.append(dict(target='/assessment/source_limitations', metadata=limitations, association='Attributed source limitations; review provenance retained in archive.'))
            return result
        value = {k: v for (k, v) in value.items() if k != 'elements' and (not current or k not in ('notice', 'dispositions', 'request_accounting', 'review_bindings'))}
    metadata = {'findings', 'automatic_findings', 'warnings', 'warning', 'notice', 'limitations', 'unresolved', 'coverage', 'resolutions', 'dispositions', 'holds', 'unavailable', 'uncertainty', 'uncertainties', 'source_limitations'}
    omitted = {'inherited_history', 'consumer_views', 'messages', 'response_body', 'request_wire'}
    if element is not None:
        metadata |= {'limitation', 'source_limitation', 'gaps', 'model_root_uncertainty', 'coverage_warnings'}

    def walk(v, pointer='', parent_scope=None, attribution=None, document=False):
        if isinstance(v, dict):
            current = _history_scope(v, parent_scope, document=document)
            if element is not None and (not _history_matches(current, element)):
                return
            author = v.get('reviewer', v.get('provenance', attribution))
            for (key, item) in v.items():
                if key in omitted:
                    continue
                target = pointer + '/' + key.replace('~', '~0').replace('/', '~1')
                if key in metadata:
                    if element is None:
                        result.append(dict(target=target, metadata=item, attribution=v.get('reviewer', v.get('provenance')), association='Historical metadata; scope as recorded, not a new correction.'))
                    else:
                        for (i, entry) in enumerate(item if isinstance(item, list) else [item]):
                            scoped = _history_scope(entry, current) if isinstance(entry, dict) else current
                            if entry in (None, [], {}, '') or not _history_matches(scoped, element):
                                continue
                            result.append(dict(target=target + ('/' + str(i) if isinstance(item, list) else ''), metadata=entry, scope=scoped or 'unscoped', attribution=entry.get('reviewer', entry.get('provenance', author)) if isinstance(entry, dict) else author, association='Historical metadata; scope as recorded, not a new correction.'))
                else:
                    walk(item, target, current, author, key == 'documents')
        elif isinstance(v, list):
            for (i, item) in enumerate(v):
                walk(item, pointer + '/' + str(i), parent_scope, attribution, document)
    walk(value, parent_scope=scope)
    return result

def prompt_history(paths, keys, element):
    """Selected prompt projection only; consumer/archive history is unchanged."""
    directories = {}
    for (key, path) in paths.items():
        if Path(key).name not in ('manifest.json', 'initial-plan.json', 'classification-plan.json', 'association-plan.json', 'prepared.json'):
            continue
        value = load(path)
        if not isinstance(value, dict):
            continue
        prefix = str(Path(key).parent) + '/' if '/' in key else ''
        if value.get('schema') == 'pdf-source-package-v1':
            for doc in value['documents']:
                directories[prefix + doc['directory'] + '/'] = _history_scope(doc, document=True)
        for row in value.get('requests', []):
            if row.get('directory'):
                directories[prefix + row['directory'] + '/'] = _history_scope(row)
    result = []
    seen = set()
    for key in sorted(keys):
        path = paths[key]
        scope = {}
        for (directory, association) in sorted(directories.items(), key=lambda x: len(x[0])):
            if key.startswith(directory):
                scope.update(association)
        if not _history_matches(scope, element):
            continue
        if path.suffix == '.json' and Path(key).name not in ('request-wire.json', 'response-body.json'):
            qualifications = qualification_projection(load(path), element=element, scope=scope)
        elif path.suffix in ('.txt', '.md') and ('review' in key.split('/') or 'findings' in Path(key).name):
            qualifications = [dict(metadata=path.read_text(), scope=scope or 'unscoped', association='Unscoped historical review text')]
        else:
            continue
        unique = []
        for q in qualifications:
            target = q.get('target', '')
            while target.split('/')[1:2] in (['mapped'], ['raw_selection'], ['raw_alias_selection'], ['validator_input']):
                target = target[target.index('/', 1):] if '/' in target[1:] else ''
            identity = digest(dict({k: v for (k, v) in q.items() if k != 'target'}, target=target))
            if identity not in seen:
                seen.add(identity)
                unique.append(q)
        if unique:
            result.append(dict(key=key, sha256=sha(path), qualifications=unique, raw_retained=True))
    return result

def history_refs(paths, keys):
    history = []
    for key in sorted(keys):
        p = paths[key]
        entry = dict(key=key, sha256=sha(p))
        if p.suffix == '.json' and p.name not in ('request-wire.json', 'response-body.json'):
            entry['qualifications'] = qualification_projection(load(p))
        elif p.suffix in ('.txt', '.md') and ('review' in key.split('/') or 'findings' in p.name):
            entry['qualifications'] = [dict(metadata=p.read_text(), association='Unscoped historical review text')]
        entry['raw_retained'] = True
        history.append(entry)
    return history

def revision_prefix(m, prefix):
    return relative_key(prefix) + '/articles/' + m['article_key'] + '/revisions/' + m['package_id']

def object_key(m, prefix, record):
    require(m.get('schema') in (SCHEMA, LEGACY_SCHEMA, FINAL_SCHEMA, SCOPED_FINAL_SCHEMA), 'manifest-schema')
    root = revision_prefix(m, prefix) if m['schema'] == LEGACY_SCHEMA else relative_key(prefix) + '/articles/' + m['article_key']
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
        (self.remote, self.bucket, self.runner) = (remote, bucket, runner or _run_rclone)

    def _target(self, key):
        return self.remote + ':' + self.bucket + '/' + relative_key(key)

    def call(self, argv, output=None):
        return self.runner(['rclone'] + argv + ['--s3-no-check-bucket', '--retries', '1', '--low-level-retries', '1', '--contimeout', '30s', '--timeout', '120s'], output=output, timeout=300)

    def object_exists(self, key):
        return bool(self.call(['lsf', self._target(key), '--max-depth', '1']).strip())

    def download(self, key, target, expected_hash=None, expected_size=None, limit=MAX_OBJECT_BYTES):
        p = absolute(target)
        require(not p.exists(), 'download-target-exists')
        # Only verified bytes become a completed object; failed attempts stay temporary.
        with tempfile.TemporaryDirectory(prefix='.download-', dir=p.parent) as tmp:
            partial = Path(tmp) / 'object'
            with partial.open('xb') as stream:
                self.call(['cat', self._target(key), '--count', str((expected_size if expected_size is not None else limit) + 1)], output=stream)
                stream.flush()
                os.fsync(stream.fileno())
            require(partial.stat().st_size <= limit, 'remote-object-size-limit')
            if expected_size is not None:
                require(partial.stat().st_size == expected_size, 'remote-size-mismatch')
            if expected_hash is not None:
                require(sha(partial) == expected_hash, 'remote-object-hash-mismatch')
            os.link(partial, p)  # Atomic, exclusive promotion; never replaces existing evidence.
        return p

    def verify(self, key, expected_hash, expected_size):
        with tempfile.TemporaryDirectory(prefix='article-readback-', dir=Path(tempfile.gettempdir()).resolve(strict=True)) as tmp:
            self.download(key, Path(tmp) / 'object', expected_hash, expected_size)
        return dict(key=key, sha256=expected_hash, size=expected_size, method='read_back_sha256')

    def upload(self, local, key, expected_hash, expected_size):
        p = absolute(local)
        require(sha(p) == expected_hash and p.stat().st_size == expected_size, 'local-upload-input-changed')
        reused = self.object_exists(key)
        if not reused:
            with tempfile.TemporaryDirectory(prefix='article-upload-', dir=Path(tempfile.gettempdir()).resolve(strict=True)) as tmp:
                snapshot = Path(tmp) / 'object'
                shutil.copyfile(p, snapshot)
                require(sha(snapshot) == expected_hash and snapshot.stat().st_size == expected_size, 'local-upload-input-changed')
                self.call(['copyto', str(snapshot), self._target(key), '--immutable', '--ignore-existing'])
        result = self.verify(key, expected_hash, expected_size)
        require(sha(p) == expected_hash and p.stat().st_size == expected_size, 'local-upload-input-changed')
        return dict(result, reused=reused, verified_at=now_utc())

def _run_rclone(argv, *, output=None, timeout=300):
    require(not any((os.environ.get(k) == '1' for k in ('PDF_ENRICHMENT_OFFLINE', 'PDF_SOURCE_PACKAGE_OFFLINE'))), 'offline-rclone-forbidden')
    require(argv and argv[0] == 'rclone', 'rclone-argv-required')
    try:
        result = subprocess.run(argv, stdout=output if output is not None else subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise ValueError('rclone-timeout') from exc
    if result.returncode == 3 and argv[1] == 'lsf':
        return ''
    require(result.returncode == 0, 'rclone-failed:' + argv[1])
    return result.stdout.decode('utf-8') if output is None else ''

def restore(manifest_path, destination, *, elements=None, include_package=True, include_enrichment=True, include_page=True, remote=None, bucket=None, prefix=None, runner=None):
    path = absolute(manifest_path)
    m = validate_manifest(load(path))
    original_hash = sha(path)
    require(m['schema'] != DIAGNOSTIC_SCHEMA, 'diagnostic-archive-restore-forbidden')
    destination = absolute(destination)
    require(not destination.exists(), 'destination-must-be-new')
    require(elements is None or (isinstance(elements, list) and elements), 'empty-selection-rejected')
    keys = {f['key'] for f in m['files']}
    want = closure_for(m, elements) if elements is not None else set(keys)
    want = {f['key'] for f in m['files'] if f['key'] in want and (include_package or f['role'] != 'source-package') and (include_enrichment or not f['role'].startswith('enrichment-')) and (include_page or f['role'] != 'page')}
    require(want, 'nothing-selected-to-restore')
    transport = None
    if remote:
        require(bucket and prefix, 'trusted-remote-binding-required')
        relative_key(prefix)
        transport = RcloneTransport(remote, bucket, runner)
        external(destination, [path.parent])
        paths = {}
    else:
        (_, paths) = verify_local(path, want)
        external(destination, [path.parent] + [p.parent for p in paths.values()])
    new_directory(destination)
    (restored, mapping) = ([], {})
    for f in m['files']:
        key = f['key']
        if key not in want:
            continue
        target = inside(destination, key)
        target.parent.mkdir(parents=True, exist_ok=True)
        if transport:
            transport.download(object_key(m, prefix, f), target, f['sha256'], f['size'])
        else:
            with paths[key].open('rb') as src, target.open('xb') as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
                dst.flush()
                os.fsync(dst.fileno())
            require(target.stat().st_size == f['size'] and sha(target) == f['sha256'], 'restore-hash-mismatch')
        restored.append(key)
        mapping[key] = dict(root=str(destination), path=key)
    require(sha(path) == original_hash, 'manifest-changed-during-restore')
    put(destination / 'manifest.json', path.read_bytes())
    save(destination / 'local-map.json', dict(schema='portable-article-local-map-v2', manifest_sha256=original_hash, sources=mapping))
    excluded = not (include_package and include_enrichment and include_page)
    completed = 'partial-package' if excluded else 'selected-elements' if elements is not None else 'full-package'
    receipt = dict(schema='portable-article-restore-v2', manifest_sha256=original_hash, restored=sorted(restored), restored_count=len(restored), unavailable=sorted(keys - want), requested_elements=elements, completed=completed, from_remote=bool(remote), restored_at=now_utc(), destination=str(destination))
    verify_local(destination / 'manifest.json', want)
    save(destination / 'RESTORE-RECEIPT.json', receipt)
    return receipt

def restore_remote(manifest_key, manifest_sha256, destination, *, remote, bucket, prefix, article_key, runner=None, **kwargs):
    from article_archive_compat.article_runtime import outside_instance
    outside_instance(destination)
    relative_key(manifest_key)
    relative_key(prefix)
    _hash(manifest_sha256)
    _hash(article_key)
    expected = prefix + '/articles/' + article_key + '/revisions/'
    require(manifest_key.startswith(expected) and manifest_key.endswith('/manifests/' + manifest_sha256 + '.json'), 'trusted-manifest-key-binding')
    transport = RcloneTransport(remote, bucket, runner)
    with tempfile.TemporaryDirectory(prefix='article-manifest-', dir=Path(tempfile.gettempdir()).resolve(strict=True)) as tmp:
        path = Path(tmp) / 'manifest.json'
        transport.download(manifest_key, path, manifest_sha256, limit=MAX_MANIFEST_BYTES)
        m = validate_manifest(load(path))
        require(m['article_key'] == article_key and manifest_key == revision_prefix(m, prefix) + '/manifests/' + manifest_sha256 + '.json', 'manifest-identity-prefix-binding')
        return restore(path, destination, remote=remote, bucket=bucket, prefix=prefix, runner=runner, **kwargs)
