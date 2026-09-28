"""Historical read-only dependency closure; extracted without changing validation contracts."""
from __future__ import annotations
import json
from pathlib import Path
import re
from article_archive_compat import portable_articles as pa
from article_archive_compat import article_enrichment as ae
from article_archive_compat.article_runtime import require, absolute, sha, digest
DIAGNOSTIC_PLAN = 'reenrich-diagnostic-plan-v1'

def _page_identity(page, article, identity=None):
    import yaml
    text = absolute(page).read_text()
    match = re.match('\\A---\\n([\\s\\S]*?)\\n(?:---|\\.\\.\\.)\\n', text)
    require(match is not None, 'paper-page-frontmatter-required')
    try:
        metadata = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise ValueError('invalid-page-frontmatter') from exc
    require(isinstance(metadata, dict) and metadata.get('kind') == 'paper' and (metadata.get('slug') == article), 'paper-page-article-identity-mismatch')
    if identity and metadata.get('doi') is not None:
        require(metadata['doi'] == identity.get('doi'), 'paper-page-doi-mismatch')
REGISTER_START = '<!-- portable-article-register:start -->\n'
REGISTER_END = '<!-- portable-article-register:end -->\n'

def without_register(text):
    require(text.count(REGISTER_START) == text.count(REGISTER_END) <= 1, 'malformed-qualification-register')
    if REGISTER_START not in text:
        return text
    start = text.index(REGISTER_START)
    end = text.index(REGISTER_END) + len(REGISTER_END)
    require(start < end, 'malformed-qualification-register')
    return text[:start] + text[end:]

def page_receipt_name(page, binding):
    return pa.relative_key(Path(page).name + '.article-' + binding[:20] + '.json')

def page_ready(exported):
    if exported['schema'] == 'portable-qualified-export-v4':
        require(exported['readiness'] == ae.readiness(exported['request_accounting'], exported['assessment'], exported['source_status'].get('readiness')), 'page-readiness-binding')
        return exported['readiness']['page_ready']
    require(exported['schema'] == 'portable-qualified-export-v3', 'unsupported-export-format')
    return exported['execution_complete']

def source_reference(ref, manifest, paths):
    from article_archive_compat.qualified_enrichment.records import resolve_pointer
    inspected = ref.get('kind') == 'inspection'
    fields = {'kind', 'key', 'sha256', 'page', 'reason', 'qualification'} if inspected else {'kind', 'key', 'sha256', 'pointer', 'quote', 'qualification'}
    require(set(ref) == fields and ref['kind'] in ('source', 'inspection'), 'candidate-source-fields')
    files = {f['key']: f for f in manifest['files']}
    require(ref['key'] in files and ref['key'] in paths, 'candidate-source-key')
    f = files[ref['key']]
    path = paths[ref['key']]
    require(f['role'] in ('source-original', 'source-package', 'source-retention') and sha(path) == ref['sha256'] == f['sha256'], 'candidate-source-binding')
    require(isinstance(ref['qualification'], str), 'candidate-qualification-type')
    if inspected:
        require(path.suffix.lower() == '.pdf' and type(ref['page']) is int and isinstance(ref['reason'], str) and ref['reason'].strip(), 'candidate-inspection-fields')
        import pymupdf
        with pymupdf.open(path) as pdf:
            require(1 <= ref['page'] <= len(pdf), 'candidate-inspection-page')
    else:
        require(path.suffix.lower() in ('.txt', '.md', '.json', '.html', '.csv'), 'candidate-readable-source-required')
        value = resolve_pointer(pa.load(path), ref['pointer']) if path.suffix.lower() == '.json' else path.read_text()
        if path.suffix.lower() != '.json':
            require(ref['pointer'] == '', 'candidate-text-pointer')
        require(isinstance(value, str) and isinstance(ref['quote'], str) and ref['quote'].strip() and (ref['quote'] in value), 'candidate-source-literal-selection')
    return ref

def _material_finding(finding, paths, evidence):
    """Suppress only known automatic baseline states; keep the archived original."""
    if finding.get('resolutions') or finding.get('category') != 'saved-uncertainty' or finding.get('provenance') != dict(kind='deterministic-check', check='v7-state-projection-v1'):
        return True
    from article_archive_compat.qualified_enrichment.records import project, resolve_pointer
    archived = pa.load(paths[evidence['key']])
    view = next((v for v in archived.get('elements', []) if v['element_id'] == finding.get('element_id')), None)
    if view is None:
        return True
    if archived.get('schema') in ('article-scientific-products-v1', 'article-scientific-products-v2'):
        return True
    return _material_finding_in_view(finding, view)

def _material_finding_in_view(finding, view):
    if finding.get('resolutions') or finding.get('category') != 'saved-uncertainty' or finding.get('provenance') != dict(kind='deterministic-check', check='v7-state-projection-v1'):
        return True
    from article_archive_compat.qualified_enrichment.records import project, resolve_pointer
    target = finding['target']
    raw = resolve_pointer(view['outcome'], target)
    if isinstance(raw, dict) and any((raw.get(k) for k in ('limitations', 'coverage_warnings', 'element_warnings'))):
        return True
    return any((f['target'] == target for f in project(dict(view, source_element=view.get('source_element') or {}), policy='observed-limitations-v1')['findings']))

def _material_history(value):
    target = value.get('metadata_target', value.get('target', ''))
    metadata = value.get('metadata')
    if target.endswith('/unreviewed_aspects'):
        return False
    if 'coverage' in target.split('/'):
        rows = metadata if isinstance(metadata, list) else [metadata]
        ordinary = {'element_id', 'target', 'aspect', 'evidence', 'reason', 'reviewer'}
        return any((isinstance(row, dict) and bool(set(row) - ordinary) for row in rows))
    if target.endswith('/notice'):
        from article_archive_compat.qualified_enrichment.reviews import NOTICE
        if metadata == NOTICE:
            return False
    return metadata not in ('', [], {})

def _current_register(exported, submission, m, p, annotated_sha256, paths, previous):
    from article_archive_compat.qualified_enrichment.exports import page_view, affected
    from article_archive_compat.qualified_enrichment.records import related
    prefix = 'refresh-' + exported['binding'][:20] + '/'
    locator = dict(key=prefix + 'export/handoff.json', sha256=submission['export_sha256'])
    views = {e['element_id']: e for e in exported['elements']}
    targets = []
    sources = []
    qualifications = []
    index = {e['element_id']: e for e in m['elements']}

    def add(value):
        if value not in qualifications:
            qualifications.append(value)
    for entry in exported.get('inherited_history', []):
        for q in entry.get('qualifications', []):
            if 'source_limitations' in q.get('target', '').split('/') and q.get('metadata'):
                add(dict(scope='Prior source evidence', metadata_target=q['target'], metadata=q['metadata'], evidence={k: entry[k] for k in ('key', 'sha256')}))
    for reason in (exported.get('assessment') or {}).get('source_limitations', []):
        add(dict(scope='Source evidence', reason=reason, evidence=locator))
    for replacement in submission['replacements']:
        for ref in replacement['evidence']:
            if ref['kind'] in ('source', 'inspection'):
                source_reference(ref, m, paths)
                if ref not in sources:
                    sources.append(ref)
            else:
                page_view(views[ref['element_id']], ref['target'], qualification=ref['qualification'])
                targets.append(dict(ref, reviewer=submission['reviewer'], evidence=dict(key=prefix + 'page-candidate/input.json')))
    for view in views.values():
        e = index[view['element_id']]
        scope = {k: e[k] for k in ('document', 'source_sha256', 'element_id')}
        cited = [t['target'] for t in targets if t['element_id'] == view['element_id']] or ['']
        active = {f['id']: f for target in cited for f in affected(view, target)}
        for f in active.values():
            if f['status'] == 'unresolved' or f.get('resolutions'):
                add(dict(scope, **{k: f[k] for k in ('target', 'status', 'category', 'reason', 'provenance', 'resolutions') if k in f}, evidence=locator))
        for entry in pa.prompt_history(paths, set(m['common_dependencies']) | set(e['inherited']), e):
            evidence = {k: entry[k] for k in ('key', 'sha256')}
            for q in entry['qualifications']:
                if 'findings' in q:
                    for f in {f['id']: f for target in cited for f in affected(q, target)}.values():
                        if (f['status'] == 'unresolved' or f.get('resolutions')) and _material_finding(f, paths, evidence):
                            add(dict(scope, **{k: f[k] for k in ('target', 'status', 'category', 'reason', 'provenance', 'resolutions') if k in f}, evidence=evidence))
                elif _material_history(q):
                    metadata = q['metadata']
                    if isinstance(metadata, dict) and str(metadata.get('target', '')).startswith('/record') and (not any((related(t, metadata['target']) for t in cited))):
                        continue
                    add(dict(scope=q.get('scope', 'unscoped'), metadata_target=q.get('target', ''), metadata=q['metadata'], attribution=q.get('attribution'), evidence=evidence))
    if previous is not None:
        _register_archive(previous, paths)
        if previous['schema'].endswith('-v1'):
            old = 'refresh-' + previous['binding'][:20] + '/'
            previous = qualification_register(pa.load(paths[previous['export_locator']['key']]), pa.load(paths[old + 'page-candidate/input.json']), pa.load(paths[old + 'parent-manifest.json']), pa.load(paths[old + 'plan.json']), previous['annotated_export_locator']['sha256'], archive_paths=paths)
        for q in previous['qualifications']:
            if _material_history(q) and _material_finding(q, paths, q['evidence']):
                add(q)
        for target in previous['selected_targets']:
            if target.get('qualification') and target not in targets:
                targets.append(target)
        if previous.get('operator_qualification') and previous['operator_qualification'] != submission['qualification']:
            key = previous['export_locator']['key'] if previous['schema'] == 'portable-page-qualification-register-v4' else 'refresh-' + previous['binding'][:20] + '/page-candidate/input.json'
            add(dict(scope='Prior page review', metadata_target='/qualification', metadata=previous['operator_qualification'], attribution=previous['reviewer'], evidence=dict(key=key, sha256=sha(paths[key]))))
        for ref in previous.get('selected_sources', []):
            if ref not in sources:
                sources.append(ref)
    result = dict(schema='portable-page-qualification-register-v3', binding=exported['binding'], article=m['article'], article_key=m['article_key'], publication_receipt=page_receipt_name(p['page_path'], exported['binding']), export_locator=locator, annotated_export_locator=dict(key=prefix + 'export/annotated.html', sha256=annotated_sha256), source_locators=[dict(document=d['identity'], key=d['raw_key'], sha256=d['source_sha256']) for d in m['documents']], reviewer=submission['reviewer'], operator_qualification=submission['qualification'], selected_targets=targets, selected_sources=sources, qualifications=qualifications, source_status=exported['source_status'], enrichment_status=dict(counts=exported['request_accounting']['counts'], requests_successful=exported['execution_complete']))
    return result

def qualification_register(exported, submission, m, p, annotated_sha256, *, version=2, archive_paths=None, previous=None):
    if version == 3:
        return _current_register(exported, submission, m, p, annotated_sha256, archive_paths, previous)
    from article_archive_compat.qualified_enrichment.exports import exact_view
    views = {v['element_id']: v for v in exported['elements']}
    targets = []
    for row in submission['replacements']:
        for ref in row['evidence']:
            value = exact_view(views[ref['element_id']], ref['target'], purpose='exact', qualification=ref['qualification'])
            targets.append({k: v for (k, v) in value.items() if k != 'content'})
    prefix = 'refresh-' + exported['binding'][:20] + '/'
    register = dict(schema='portable-page-qualification-register-v1', binding=exported['binding'], article=m['article'], article_key=m['article_key'], publication_receipt=page_receipt_name(p['page_path'], exported['binding']), locator_contract='Resolve archive keys through the publication receipt manifest key/hash; receipt absent means publication pending.', source_locators=[dict(document=d['identity'], key=d['raw_key'], sha256=d['source_sha256']) for d in m['documents']], export_locator=dict(key=prefix + 'export/handoff.json', sha256=submission['export_sha256']), annotated_export_locator=dict(key=prefix + 'export/annotated.html', sha256=annotated_sha256), reviewer=submission['reviewer'], full_distillation_reviewed=submission['full_distillation_reviewed'], reconciliation_outcome=submission.get('reconciliation_outcome', 'scientific-text-revised'), operator_qualification=submission['qualification'], selected_targets=targets, source_status=exported['source_status'], notice='Native/model originals are unchanged. Findings and attributed correction proposals are annotations, not applied factual corrections. Prior unresolved findings remain active; review covers only recorded scopes/aspects.')
    if version == 1:
        return dict(register, current_qualifications=pa.qualification_projection(exported), inherited_qualifications=[r for r in exported['inherited_history'] if r.get('qualifications')], dispositions=exported['dispositions'])
    require(version == 2 and archive_paths is not None, 'register-archive-required')
    register['schema'] = 'portable-page-qualification-register-v2'
    register['selected_targets'] = [{k: t[k] for k in ('element_id', 'source_sha256', 'target', 'qualification', 'unreviewed_aspects', 'scope_review_status', 'unapplied_correction_findings')} for t in targets]
    for t in register['selected_targets']:
        t.update(reviewer=submission['reviewer'], evidence=dict(key=prefix + 'page-candidate/input.json'))
    index = {e['element_id']: e for e in m['elements']}
    qualifications = []
    seen = set()

    def add(value, locator):
        identity = digest(value)
        if identity not in seen:
            seen.add(identity)
            qualifications.append(dict(value, evidence=locator))

    def finding(f, scope, locator):
        value = dict(scope, **{k: f[k] for k in ('target', 'status', 'category', 'reason', 'provenance') if k in f})
        if f.get('resolutions'):
            value['resolutions'] = f['resolutions']
            value['correction'] = 'Attributed proposals only; originals remain unchanged.'
        add(value, locator)
    from article_archive_compat.qualified_enrichment.exports import affected
    from article_archive_compat.qualified_enrichment.records import related
    for target in targets:
        element = index[target['element_id']]
        scope = {k: element[k] for k in ('document', 'source_sha256', 'element_id')}
        for f in target['findings']:
            finding(f, scope, register['export_locator'])
        keys = set(m['common_dependencies']) | set(element['inherited'])
        for entry in pa.prompt_history(archive_paths, keys, element):
            locator = {k: entry[k] for k in ('key', 'sha256')}
            for q in entry['qualifications']:
                if 'findings' in q:
                    for f in affected(q, target['target']):
                        finding(f, scope, locator)
                    continue
                metadata = q['metadata']
                if isinstance(metadata, dict) and (metadata.get('target') == '/record' or str(metadata.get('target', '')).startswith('/record/')):
                    if not related(metadata['target'], target['target']):
                        continue
                add(dict(scope=q.get('scope', 'unscoped'), metadata_target=q.get('target', ''), metadata=metadata, attribution=q.get('attribution')), locator)
    register['qualifications'] = qualifications
    if previous is not None:
        _register_archive(previous, archive_paths)
        if previous['schema'].endswith('-v1'):
            old_prefix = 'refresh-' + previous['binding'][:20] + '/'
            previous = qualification_register(pa.load(archive_paths[previous['export_locator']['key']]), pa.load(archive_paths[old_prefix + 'page-candidate/input.json']), pa.load(archive_paths[old_prefix + 'parent-manifest.json']), pa.load(archive_paths[old_prefix + 'plan.json']), previous['annotated_export_locator']['sha256'], archive_paths=archive_paths)
        identity = lambda t: (t['element_id'], t['source_sha256'], t['target'], t['qualification'], digest(t['reviewer']))
        current = {identity(t) for t in register['selected_targets']}
        register['selected_targets'] += [t for t in previous['selected_targets'] if identity(t) not in current]
        if (previous['operator_qualification'], previous['reviewer']) != (register['operator_qualification'], register['reviewer']):
            key = previous['export_locator']['key'] if previous['schema'] == 'portable-page-qualification-register-v4' else 'refresh-' + previous['binding'][:20] + '/page-candidate/input.json'
            add(dict(scope='Prior page review', metadata_target='/qualification', metadata=previous['operator_qualification'], attribution=previous['reviewer']), dict(key=key, sha256=sha(archive_paths[key])))
        for q in previous['qualifications']:
            add({k: v for (k, v) in q.items() if k != 'evidence'}, q['evidence'])
        sources = {digest(d) for d in register['source_locators']}
        register['source_locators'] += [d for d in previous['source_locators'] if digest(d) not in sources]
    return register

def read_register(text):
    import html
    without_register(text)
    if REGISTER_START not in text:
        return None
    block = text.split(REGISTER_START, 1)[1].split(REGISTER_END, 1)[0]
    match = re.search('<!-- portable-page-qualification-register-v[234]: ([^\\n]*) -->\\n$', block) or re.search('<pre>([\\s\\S]*)</pre>\\n$', block)
    require(match is not None, 'malformed-qualification-register')
    value = json.loads(html.unescape(match[1]))
    require(value.get('schema') in ('portable-page-qualification-register-v1', 'portable-page-qualification-register-v2', 'portable-page-qualification-register-v3', 'portable-page-qualification-register-v4'), 'unknown-qualification-register')
    require(REGISTER_START + block + REGISTER_END == register_text(value), 'noncanonical-qualification-register')
    return value

def _register_archive(register, paths):
    require(paths is not None, 'register-archive-required')
    if register['schema'] == 'portable-page-qualification-register-v4':
        locators = [register['export_locator']] + register['source_locators'] + register.get('selected_sources', [])
        locators += [q['evidence'] for q in register['qualifications'] + register['selected_targets'] if q.get('evidence')]
        for locator in locators:
            require(locator['key'] in paths and sha(paths[locator['key']]) == locator['sha256'], 'register-archive-evidence')
        return
    prefix = 'refresh-' + register['binding'][:20] + '/'
    snapshot = paths.get(prefix + 'applied-page.md')
    require(snapshot is not None and read_register(snapshot.read_text()) == register, 'register-archive-snapshot')
    locators = [register['export_locator'], register['annotated_export_locator']] + register['source_locators']
    locators += [{k: ref[k] for k in ('key', 'sha256')} for ref in register.get('selected_sources', [])]
    locators += [q['evidence'] for q in register.get('qualifications', []) + register['selected_targets'] if q.get('evidence')]
    exported = pa.load(paths[register['export_locator']['key']]) if register['export_locator']['key'] in paths else None
    require(exported is not None, 'register-archive-evidence')
    for (key, h) in exported['review_bindings'].items():
        locators.append(dict(key=prefix + 'review/' + pa.relative_key(key), sha256=h))
    for locator in locators:
        path = paths.get(locator['key'])
        require(path is not None and ('sha256' not in locator or sha(path) == locator['sha256']), 'register-archive-evidence')
    for ref in exported['inherited_history']:
        path = paths.get(ref['key'])
        require(path is not None and sha(path) == ref['sha256'], 'register-archive-history')

def register_text(register):
    import html
    header = REGISTER_START + 'Article package: ' + register['publication_receipt'] + '\n' + 'Annotated export: ' + register['annotated_export_locator']['key'] + ' (resolve through article package receipt)\n'
    if register['schema'] in ('portable-page-qualification-register-v3', 'portable-page-qualification-register-v4'):

        def esc(value):
            return html.escape(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)).replace('\n', '&#10;').replace('\r', '&#13;')
        parts = [header]
        if register['operator_qualification'].strip():
            parts.append('<p>' + esc(register['operator_qualification']) + '</p>\n')
        for target in register['selected_targets']:
            if target['qualification']:
                parts.append('<p>' + esc(target['element_id'] + ' ' + target['target'] + ': ' + target['qualification']) + '</p>\n')
        for ref in register['selected_sources']:
            if ref['qualification']:
                parts.append('<p>' + esc(ref['key'] + ': ' + ref['qualification']) + '</p>\n')
        for q in register['qualifications']:
            parts.append('<p>' + esc(q.get('scope', {k: q[k] for k in ('document', 'element_id', 'target') if k in q})) + ': ' + esc(q.get('reason', q.get('metadata'))) + (' Attributed proposals; originals unchanged: ' + esc(q['resolutions']) if q.get('resolutions') else '') + '</p>\n')
        parts.append('<!-- ' + register['schema'] + ': ' + html.escape(json.dumps(register, ensure_ascii=False, sort_keys=True, separators=(',', ':'))) + ' -->\n' + REGISTER_END)
        return ''.join(parts)
    if register['schema'].endswith('-v1'):
        return header + '<pre>' + html.escape(json.dumps(register, ensure_ascii=False, sort_keys=True, indent=2)) + '</pre>\n' + REGISTER_END

    def text(value):
        return html.escape(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)).replace('\n', '&#10;').replace('\r', '&#13;')
    parts = [header, '<p><strong>Source qualifications</strong> — ' + text(register['operator_qualification']) + ' Attribution: ' + text(register['reviewer']) + '.</p>\n']
    if not register['source_status'].get('complete') or register['source_status'].get('holds') or register['source_status'].get('fixture'):
        parts.append('<p>Source status: ' + text(register['source_status']) + '</p>\n')
    for target in register['selected_targets']:
        parts.append('<p><code>' + text(target['element_id'] + ' ' + target['target']) + '</code>: ' + text(target['qualification']) + ' Unreviewed aspects: ' + text(', '.join(target['unreviewed_aspects']) or 'none for this exact scope') + '. Attribution: ' + text(target['reviewer']) + ' Evidence: <code>' + text(target['evidence']['key']) + '</code>.</p>\n')
    for q in register['qualifications']:
        scope = q.get('scope', {k: q[k] for k in ('document', 'element_id', 'source_sha256', 'target') if k in q})
        parts.append('<p>' + text(scope) + (' ' + text(q['metadata_target']) if q.get('metadata_target') else '') + ' — ' + text(q.get('status', 'Historical qualification')) + ': ' + text(q.get('reason', q.get('metadata'))) + (' Attributed proposals only; original unchanged: ' + text(q['resolutions']) if q.get('resolutions') else '') + ' Attribution: ' + text(q.get('provenance', q.get('attribution'))) + ' Evidence: <code>' + text(q['evidence']['key']) + '</code>.</p>\n')
    parts.append('<p>' + text(register['notice']) + '</p>\n')
    parts.append('<!-- portable-page-qualification-register-v2: ' + html.escape(json.dumps(register, ensure_ascii=False, sort_keys=True, separators=(',', ':'))) + ' -->\n' + REGISTER_END)
    return ''.join(parts)

def completion_label(p):
    require(p['schema'] != DIAGNOSTIC_PLAN, 'diagnostic-has-no-article-completion-label')
    return ('offline-' if p['fixture'] else '') + p['mode'] + ('-refresh-complete' if p['page_path'] else '-archive-complete')

def verify_completion(receipt_path, manifest_path, *, manifest_key, manifest_sha256, article_key, page=None):
    """Portable verification, not source_package v2 ingest verification.

    Trust comes from caller-pinned manifest key/hash and article identity, not
    from a receipt's own claims. This works after the original run is removed.
    Publication read-back is historical; it is not a fresh remote health check.
    """
    pa._hash(manifest_sha256)
    pa._hash(article_key)
    pa.relative_key(manifest_key)
    require(sha(manifest_path) == manifest_sha256, 'completion-manifest-hash')
    (m, paths) = pa.verify_local(manifest_path)
    pa.verify_source(manifest_path)
    require(m['schema'] != pa.DIAGNOSTIC_SCHEMA, 'diagnostic-article-completion-forbidden')
    receipt = pa.load(receipt_path)
    pub = receipt['publication']
    require(receipt['schema'] in ('portable-article-completion-v1', 'portable-article-completion-v2', 'portable-article-completion-v3') and receipt['article'] == m['article'] and (m['article_key'] == article_key == pub['article_key']), 'completion-article-binding')
    require(pub['manifest_key'] == manifest_key and pub['manifest_sha256'] == manifest_sha256 and (manifest_key == pa.revision_prefix(m, pub['prefix']) + '/manifests/' + manifest_sha256 + '.json'), 'completion-publication-pointer')
    pa.RcloneTransport(pub['remote'], pub['bucket'])
    expected = {(pa.object_key(m, pub['prefix'], f), f['sha256'], f['size']) for f in m['files']}
    expected.add((manifest_key, manifest_sha256, absolute(manifest_path).stat().st_size))
    require(expected == {(r['key'], r['sha256'], r['size']) for r in pub['receipts']} and all((r['method'] == 'read_back_sha256' for r in pub['receipts'])), 'publication-readback-inventory')
    if pa.is_final_manifest(m):
        from article_archive_compat import final_products
        return final_products.verify_completion(receipt, m, paths, page, manifest_path)
    refresh = m['provenance']['refresh']
    binding = refresh['binding']
    prefix = 'refresh-' + binding[:20] + '/'
    require(receipt['binding'] == binding, 'completion-run-binding')
    p = pa.load(paths[prefix + 'plan.json'])
    exported = pa.load(paths[prefix + 'export/handoff.json'])
    parent_path = paths[prefix + 'parent-manifest.json']
    parent = pa.validate_manifest(pa.load(parent_path))
    require(sha(parent_path) == m['provenance']['parent_manifest_sha256'] and parent['article'] == m['article'], 'completion-parent-binding')
    require(exported['schema'] in ('portable-qualified-export-v3', 'portable-qualified-export-v4') and exported['binding'] == binding and (exported['roster'] == refresh['roster']) and (exported['fixture'] == p['fixture'] == refresh['fixture']) and (refresh['mode'] == p['mode']), 'completion-export-contract')
    current = receipt['schema'] == 'portable-article-completion-v2'
    require(current == (exported['schema'] == 'portable-qualified-export-v4'), 'completion-policy-binding')
    require(page_ready(exported), 'partial-export-cannot-verify-completion')
    if current:
        require(all((receipt[k] == exported['readiness'][k] for k in ('requests_accounted_for', 'requests_successful'))), 'completion-accounting-binding')
    require(receipt['completion'] == completion_label(p) and receipt['page_refresh_complete'] == bool(p['page_path']) and (receipt['production_complete'] == (not p['fixture'])), 'completion-status-binding')
    require(pub['verification_scope'] == 'rclone-live-readback' or p['fixture'], 'offline-publication-not-production')
    for f in parent['files']:
        require(f['key'] in paths and sha(paths[f['key']]) == f['sha256'], 'completion-parent-object-binding')
    ids = exported['roster']
    keys = pa.closure_for(parent, ids) if ids else set(parent['common_dependencies'])
    inherited = set(parent['common_dependencies']).union(*(set(e['inherited']) for e in parent['elements'] if e['element_id'] in ids))
    require(exported['inherited_history'] == pa.history_refs(paths, keys & inherited) and exported['source_status'] == parent['source_status'] and (exported['dispositions'] == parent['dispositions']), 'completion-inherited-qualifications')
    from article_archive_compat.article_runtime import trusted_modules
    trusted_modules()
    from article_archive_compat.qualified_enrichment import reviews
    from article_archive_compat.qualified_enrichment.exports import exact_view, content_targets
    dossier = pa.load(paths[prefix + 'review/dossier.json'])
    decision_keys = sorted((k for k in paths if k.startswith(prefix + 'review/decisions/') and k.endswith('.json')))
    entries = [pa.load(paths[k]) for k in decision_keys]
    if current:
        require(dossier['snapshot']['manifest_sha256'] == sha(parent_path), 'completion-review-manifest')
        ae.validate_accounting(dossier['request_accounting'])
    views = reviews.apply(dossier, entries, manifest=parent, paths=paths)
    if current:
        assessment = reviews.assessment(dossier, entries, manifest=parent, paths=paths)
        require(exported['assessment'] == assessment and exported['request_accounting'] == dossier['request_accounting'] and (exported['readiness'] == ae.readiness(dossier['request_accounting'], assessment, parent['source_status'].get('readiness'))), 'completion-review-readiness')
    require(entries or not views, 'completion-review-required')
    for view in views:
        view['consumer_views'] = [exact_view(view, t) for t in content_targets(view['outcome'])]
    require(exported['elements'] == views and [v['element_id'] for v in views] == ids, 'completion-export-findings')
    for (key, h) in exported['review_bindings'].items():
        require(sha(paths[prefix + 'review/' + pa.relative_key(key)]) == h, 'completion-review-binding')
    import html
    annotated = '<!doctype html><html lang="en"><meta charset="utf-8"><title>Qualified article evidence</title><pre>' + html.escape(json.dumps(exported, indent=2)) + '</pre></html>'
    require(paths[prefix + 'export/annotated.html'].read_text() == annotated, 'completion-annotated-export')
    require(receipt['export'] == dict(key=prefix + 'export/handoff.json', sha256=sha(paths[prefix + 'export/handoff.json'])) and receipt['annotated_export'] == dict(key=prefix + 'export/annotated.html', sha256=sha(paths[prefix + 'export/annotated.html'])), 'completion-export-pointer')
    if p['page_path']:
        require(page is not None, 'completion-real-page-required')
        page = absolute(page)
        _page_identity(page, p['article'], m['article'])
        submission = pa.load(paths[prefix + 'page-candidate/input.json'])
        require(submission['export_sha256'] == receipt['export']['sha256'] and submission['binding'] == binding, 'completion-candidate-binding')
        reviews.provenance(submission['reviewer'])
        if p['mode'] == 'full' or p['manifest'] is None:
            require(submission['full_distillation_reviewed'] is True, 'full-distillation-attestation-required')
        text = page.read_text()
        stored = read_register(text)
        require(stored is not None, 'completion-qualification-register-or-pointer')
        version = int(stored['schema'].rsplit('-v', 1)[1])
        register = qualification_register(exported, submission, parent, p, receipt['annotated_export']['sha256'], version=version, archive_paths=paths, previous=read_register(paths[prefix + 'original-page.md'].read_text()))
        require(register_text(register) in text and text.count(REGISTER_START) == 1, 'completion-qualification-register-or-pointer')
        require(sha(page) == sha(paths[prefix + 'applied-page.md']) == receipt['page_sha256'], 'completion-page-snapshot')
        sidecar = page.parent / register['publication_receipt']
        require(pa.load(sidecar) == receipt, 'completion-page-receipt-pointer')
    else:
        require(page is None and receipt['page_sha256'] is None, 'archive-only-not-page-refresh')
    return receipt
