"""Compile scientific products from verified operational archives; no replay state.

The caller validates live execution/review before supplying new exports. Archived
exports are hash-bound evidence, not new assertions of scientific correctness.
This module never posts requests, edits a paper, or deletes an input directory.
"""
from __future__ import annotations
import copy
from pathlib import Path
import re

import portable_articles as pa
from article_runtime import absolute, inside, external, require, sha

POLICY = 'final-products-v1'
PRODUCT_SCHEMA = 'article-scientific-products-v1'


def _remap(value, aliases, field=None):
    if field in ('outcome', 'recorded_evidence', 'acquisition'):
        return copy.deepcopy(value)
    if isinstance(value, dict):
        return {k: _remap(v, aliases, k) for k, v in value.items()}
    if isinstance(value, list):
        return [_remap(v, aliases, field) for v in value]
    if isinstance(value, str) and field in ('key','raw_key','raw','crop','crop_key','native_text_keys','dependencies','inherited'):
        return aliases.get(value, aliases.get('package/' + value, value))
    return value


def _results(m, paths, exports, page):
    """Latest scientific result per element, not a stack of previous exports."""
    if m['schema'] == pa.FINAL_SCHEMA:
        products = copy.deepcopy(pa.load(paths[m['products_key']]))
    else:
        products = dict(schema=PRODUCT_SCHEMA, elements=[], source_limitations=[], qualifications=[])
    index = {e['element_id']: e for e in m['elements']}
    old_profiles = {}
    for f in m['files']:
        if f['role']=='enrichment-job' and Path(f['key']).name=='enrichment-plan.json':
            plan = pa.load(paths[f['key']])
            for row in plan.get('requests', []):
                old_profiles[row['element_id']] = {k: copy.deepcopy(plan[k]) for k in ('model','settings','prompt_version','response_schema','prepared_at') if k in plan}
    results = {e['element_id']: e for e in products['elements']}
    saved = []
    if m['schema'] != pa.FINAL_SCHEMA:
        # Inventory order is archive revision order, never filesystem mtime.
        for f in m['files']:
            if f['role'] == 'enrichment-export' and f['key'].endswith('/handoff.json'):
                value = pa.load(paths[f['key']])
                if value.get('schema') in ('qualified-enrichment-export-v1', 'qualified-enrichment-export-v2',
                        'portable-qualified-export-v3', 'portable-qualified-export-v4'):
                    saved.append(value)
    for exported in saved + list(exports):
        for view in exported['elements']:
            element = index.get(view['element_id'])
            require(element and view['source_sha256'] == element['source_sha256'], 'result-source-binding')
            value = {k: copy.deepcopy(view[k]) for k in ('element_id', 'source_sha256', 'outcome', 'findings', 'coverage') if k in view}
            value['provenance'] = {k: copy.deepcopy(exported[k]) for k in ('schema', 'profile', 'policy', 'fixture', 'created_at', 'processing') if k in exported}
            if 'profile' not in value['provenance'] and view['element_id'] in old_profiles:
                value['provenance']['profile'] = old_profiles[view['element_id']]
            import reenrich
            material_view = dict(view, evidence=element['evidence'], source_element=element['source_element'])
            value['findings'] = [f for f in value.get('findings', [])
                                 if (f.get('status') == 'unresolved' or f.get('resolutions'))
                                 and reenrich._material_finding_in_view(f, material_view)]
            # Human correction proposals are research products, not run logs.
            previous = results.get(view['element_id'], {})
            for finding in previous.get('findings', []):
                def signature(f):
                    return pa.digest({k:f.get(k) for k in ('target','category','reason','resolutions')})
                if (finding.get('status')=='unresolved' or finding.get('resolutions')) and signature(finding) not in {signature(f) for f in value['findings']}:
                    value['findings'].append(copy.deepcopy(finding))
            results[view['element_id']] = value
        for limitation in (exported.get('assessment') or {}).get('source_limitations', []):
            if limitation not in products['source_limitations']:
                products['source_limitations'].append(limitation)
    products['elements'] = [results[k] for k in sorted(results)]
    if m['schema'] != pa.FINAL_SCHEMA:
        import reenrich
        for e in m['elements']:
            for entry in pa.prompt_history(paths, set(m['common_dependencies']) | set(e['inherited']), e):
                for q in entry['qualifications']:
                    if 'metadata' in q and reenrich._material_history(q):
                        value = dict(scope=q.get('scope', 'unscoped'), metadata_target=q.get('target', ''),
                                     metadata=q['metadata'], attribution=q.get('attribution'),
                                     recorded_evidence={k: entry[k] for k in ('key', 'sha256')})
                        if value not in products['qualifications']:
                            products['qualifications'].append(value)
    if page:
        import reenrich
        register = reenrich.read_register(absolute(page).read_text())
        if register:
            for q in register.get('qualifications', []):
                if not reenrich._material_history(q):
                    continue
                # The recorded evidence identity remains attribution, not a
                # promise to retain or replay the old execution artifact.
                value = copy.deepcopy(q)
                if 'evidence' in value:
                    value['recorded_evidence'] = value.pop('evidence')
                if value not in products['qualifications']:
                    products['qualifications'].append(value)
            for target in register.get('selected_targets', []) + register.get('selected_sources', []):
                if target.get('qualification'):
                    value = dict(reason=target['qualification'], provenance=target.get('reviewer',register.get('reviewer')),
                                 scope={k:target[k] for k in ('element_id','source_sha256','target','key','pointer') if k in target})
                    if value not in products['qualifications']: products['qualifications'].append(value)
            if register.get('operator_qualification'):
                value = dict(reason=register['operator_qualification'], provenance=register.get('reviewer'), scope='page')
                if value not in products['qualifications']:
                    products['qualifications'].append(value)
    return products


def build(manifest_path, destination, *, exports=(), page=None, qualifications=()):
    """Copy an allowlist into a new self-contained directory; inputs stay intact."""
    manifest_path, destination = absolute(manifest_path), absolute(destination)
    m, paths = pa.verify_local(manifest_path)
    pa.verify_source(manifest_path)
    require(m['schema'] != pa.DIAGNOSTIC_SCHEMA, 'diagnostic-finalization-forbidden')
    external(destination, [manifest_path.parent] + [p.parent for p in paths.values()])
    require(not destination.exists(), 'destination-must-be-new')
    input_hash = sha(manifest_path)
    records = {f['key']: f for f in m['files']}
    originals = {d['raw_key'] for d in m['documents']}
    originals.update(f['key'] for f in m['files'] if f['role'] == 'source-original')
    if m['schema'] == pa.FINAL_SCHEMA:
        originals.update(s['key'] for s in m['source_documents'])
    native = {key for e in m['elements'] for key in e['context']['native_text_keys']}
    native.update(f['key'] for f in m['files'] if f['key'].startswith('package/documents/') and f['key'].endswith(('/native-text.json','/native-text.txt')))
    native.update(m.get('native_text_keys', []))
    crops = {f['crop_key'] for e in m['elements'] for f in e['fragments']}
    crops.update(f['crop'] for e in m['elements'] for f in e['evidence'].get('body_fragments', []) + e['evidence'].get('captions', []))
    captions = copy.deepcopy(pa.load(paths[m['products_key']]).get('source_captions', [])) if m['schema']==pa.FINAL_SCHEMA else []
    if 'package/results.json' in paths:
        for document in pa.load(paths['package/results.json']).get('documents', []):
            for candidate in document.get('candidates', []):
                if candidate.get('role') not in ('caption', 'note'):
                    continue
                caption = {k: copy.deepcopy(candidate[k]) for k in ('id','source_document','source_sha256','page','role','native_text','model_observed_label','model_uncertainty','associated_label','availability','disposition','origin') if k in candidate}
                caption['regions'] = []
                for region in candidate.get('regions', []):
                    item = {k: copy.deepcopy(region[k]) for k in ('id','page','bbox','coordinate_system','crop','crop_sha256') if k in region}
                    item['lines'] = [{k: line[k] for k in ('id','text','bbox') if k in line} for line in region.get('lines', [])]
                    if item.get('crop'):
                        item['crop'] = 'package/' + item['crop']
                        crops.add(item['crop'])
                    caption['regions'].append(item)
                captions.append(caption)
    for caption in captions:
        crops.update(r['crop'] for r in caption.get('regions', []) if r.get('crop'))
    wanted = originals | native | crops
    require(wanted <= paths.keys(), 'missing-final-product-input')
    products = _results(m, paths, exports, page)
    products['source_captions'] = captions
    for q in qualifications:
        value = copy.deepcopy(q)
        if 'evidence' in value:
            value['recorded_evidence'] = value.pop('evidence')
        if value not in products['qualifications']:
            products['qualifications'].append(value)
    aliases, content, files = {}, {}, []
    for key in sorted(wanted, key=lambda k: (k not in originals, k not in native, k)):
        record = records[key]; h = record['sha256']
        if h not in content:
            kind = 'sources' if key in originals else 'text' if key in native else 'crops'
            suffix = paths[key].suffix.lower()
            require(not suffix or re.fullmatch(r'\.[a-z0-9]+', suffix), 'product-extension')
            new_key = kind + '/' + h + suffix
            content[h] = (new_key, paths[key])
            files.append(dict(role='source-original' if key in originals else 'source-package', key=new_key, sha256=h, size=record['size']))
        aliases[key] = content[h][0]
    if m['schema'] == pa.FINAL_SCHEMA:
        sources = _remap(m['source_documents'], aliases)
    else:
        sources = []
        for d in m['documents']:
            sources.append(dict(identity=d['identity'], key=aliases[d['raw_key']], sha256=d['source_sha256'],
                                version=d['source_version'], role=d.get('source_role'), source_id=d.get('source_id')))
        for key in sorted(originals):
            f = records[key]; binds = f.get('binds', {})
            if any(s['sha256'] == f['sha256'] and (not binds or s.get('source_id') == binds.get('source_id')) for s in sources):
                # Keep distinct explicitly named acquisition identities, but not
                # a second operational copy of a document's same source.
                if key == next((d['raw_key'] for d in m['documents'] if d['source_sha256'] == f['sha256']), None):
                    continue
                if binds and any(s.get('source_id') == binds.get('source_id') for s in sources):
                    continue
            if key not in {d['raw_key'] for d in m['documents']}:
                sources.append(dict(identity=binds.get('source_id', key), key=aliases[key], sha256=f['sha256'],
                                    version=binds.get('source_version', m['article']['version']), role=binds.get('source_role')))
        retained = paths.get('retention/retention.json')
        if retained:
            acquisition = pa.load(retained)['acquisition']
            for source in sources:
                row = next((r for r in acquisition['files'] if r['id'] == source.get('source_id', source['identity'])), None)
                if row:
                    source['acquisition'] = {k: copy.deepcopy(v) for k, v in row.items() if k not in ('path', 'page_count', 'sha256')}
    unique = {}
    for q in products['qualifications']:
        identity = pa.digest({k:v for k,v in q.items() if k not in ('evidence','recorded_evidence')})
        unique[identity] = q
    products['qualifications'] = list(unique.values())
    # A final product index carries actual scientific metadata, not request blobs.
    products = _remap(products, aliases)
    import json
    raw = (json.dumps(products, ensure_ascii=False, allow_nan=False, indent=2) + '\n').encode()
    import hashlib
    h = hashlib.sha256(raw).hexdigest(); product_key = 'results/' + h + '.json'
    files.append(dict(role='enrichment-export', key=product_key, sha256=h, size=len(raw)))
    caption_keys = {aliases[r['crop']] for c in captions for r in c.get('regions', []) if r.get('crop')}
    common = sorted({product_key} | {aliases[k] for k in originals | native} | caption_keys)
    elements = []
    for source in m['elements']:
        e = _remap(copy.deepcopy(source), aliases)
        e['inherited'] = [product_key]
        deps = set(common + e['context']['native_text_keys'])
        deps.update(f['crop_key'] for f in e['fragments'])
        deps.update(f['crop'] for f in e['evidence'].get('body_fragments', []) + e['evidence'].get('captions', []))
        e['dependencies'] = sorted(deps)
        elements.append(e)
    text_pages = copy.deepcopy(m.get('text_pages', []))
    if 'package/manifest.json' in paths:
        for d in pa.load(paths['package/manifest.json'])['documents']:
            for page_info in d['pages']:
                key = 'package/' + page_info['native_text'] if page_info.get('native_text') else None
                for variant in (key, str(Path(key).with_suffix('.txt')) if key else None):
                    if variant in native:
                        row = dict(document=d['identity'], page=page_info['page'], key=variant)
                        if row not in text_pages: text_pages.append(row)
    for key in native:
        if not any(row['key'] == key for row in text_pages):
            text_pages.append(dict(key=key, recorded_source_key=key))
    text_pages = _remap(text_pages, aliases)
    provenance = {k: copy.deepcopy(m['provenance'][k]) for k in ('source_schema', 'method_code', 'fixture', 'statement') if k in m['provenance']}
    processing = copy.deepcopy(m['provenance'].get('processing', []))
    for phase in ('initial','classification','association'):
        key = 'package/' + phase + '-approval.json'
        if key in paths:
            value = pa.load(paths[key])
            metadata = dict(phase=phase, settings=value['settings'])
            session = paths.get('package/' + phase + '-session.json')
            if session: metadata['started_at'] = pa.load(session).get('started_at')
            if metadata not in processing: processing.append(metadata)
    provenance.update(retention_policy=POLICY, input_manifest_sha256=input_hash, processing=processing)
    final = dict(schema=pa.FINAL_SCHEMA, package_id=m['package_id'], article=m['article'], article_key=m['article_key'],
                 created_at=m.get('created_at', pa.now_utc()), files=files, total_objects=len(files),
                 documents=_remap(m['documents'], aliases), elements=elements, source_documents=sources,
                 native_text_keys=sorted({aliases[k] for k in native}), text_pages=text_pages, caption_crop_keys=sorted(caption_keys), products_key=product_key,
                 common_dependencies=common, source_status=copy.deepcopy(m['source_status']), provenance=provenance,
                 dispositions=[copy.deepcopy(d) for d in m['dispositions'] if d['kind'] in ('acquisition', 'attachments', 'source-file-dispositions')])
    pa.validate_manifest(final)
    pa.verify_local(manifest_path)
    require(sha(manifest_path) == input_hash, 'finalization-input-changed')
    pa.new_directory(destination)
    for new_key, path in content.values():
        pa.put(inside(destination, new_key), path.read_bytes())
    pa.put(inside(destination, product_key), raw)
    pa.save(destination/'manifest.json', final)
    pa.save(destination/'local-map.json', dict(schema='portable-article-local-map-v2', manifest_sha256=sha(destination/'manifest.json'),
                                             sources={f['key']: dict(root=str(destination), path=f['key']) for f in files}))
    verify(destination/'manifest.json')
    return final


def validate(m):
    require(m['provenance'].get('retention_policy') == POLICY, 'final-products-policy')
    records = {f['key']: f for f in m['files']}
    require(len({f['sha256'] for f in m['files']}) == len(records), 'duplicate-final-product-bytes')
    require(m['products_key'] in records and records[m['products_key']]['role'] == 'enrichment-export', 'missing-final-results')
    require(set(m['native_text_keys']) <= records.keys(), 'missing-final-native-text')
    require(m['source_documents'], 'final-sources-required')
    require(len({s['identity'] for s in m['source_documents']})==len(m['source_documents']), 'duplicate-final-source-identity')
    allowed = {m['products_key']} | set(m['native_text_keys']) | set(m['caption_crop_keys'])
    allowed.update(s['key'] for s in m['source_documents'])
    for e in m['elements']:
        allowed.update(f['crop_key'] for f in e['fragments'])
        allowed.update(f['crop'] for f in e['evidence'].get('body_fragments', [])+e['evidence'].get('captions', []))
    require(allowed==records.keys(), 'nonproduct-archive-file')
    for f in m['files']:
        require(f['key'].split('/')[0] in ('sources','text','crops','results') and
                Path(f['key']).stem==f['sha256'], 'final-product-content-key')
    require({row['key'] for row in m['text_pages']}==set(m['native_text_keys']), 'native-page-index')
    for s in m['source_documents']:
        require(s['key'] in records and records[s['key']]['sha256'] == s['sha256'] and
                records[s['key']]['role'] == 'source-original', 'final-source-binding')
    return m


def verify(manifest_path):
    m, paths = pa.verify_local(manifest_path)
    require(m['schema'] == pa.FINAL_SCHEMA, 'final-products-required')
    validate(m)
    products = pa.load(paths[m['products_key']])
    require(products['schema'] == PRODUCT_SCHEMA, 'final-results-schema')
    elements = {e['element_id']: e for e in m['elements']}
    documents = {d['identity']: d for d in m['documents']}
    records = {f['key']: f for f in m['files']}
    caption_keys = set()
    for caption in products.get('source_captions', []):
        require(caption['source_document'] in documents and caption['source_sha256']==documents[caption['source_document']]['source_sha256'], 'caption-source-binding')
        for region in caption['regions']:
            if region.get('crop'):
                key=region['crop']; caption_keys.add(key)
                require(key in records and (not region.get('crop_sha256') or region['crop_sha256']==records[key]['sha256']), 'caption-crop-binding')
    require(caption_keys==set(m['caption_crop_keys']), 'caption-crop-inventory')
    seen = set()
    for e in products['elements']:
        require(e['element_id'] not in seen and e['element_id'] in elements and
                e['source_sha256'] == elements[e['element_id']]['source_sha256'], 'result-source-binding')
        seen.add(e['element_id'])
    return m


def prepare_refresh(work, plan, manifest, exported, qualifications=None):
    """Freeze the final evidence before composing the page's durable register."""
    import article_enrichment as ae
    work = absolute(work); root = work/'final-products'
    prepared = ae.read_bound(work/'enrichment/prepared.json')
    binding = dict(source_manifest=sha(manifest), prepared=sha(work/'enrichment/prepared.json'),
                   prior_source=sha(plan['source_archive']) if plan.get('source_archive') else None, export=sha(work/'export/handoff.json'),
                   original_page=sha(work/'original-page.md') if plan['page_path'] else None)
    if root.exists():
        saved = ae.read_bound(work/'final-products-input.json')
        require(saved['inputs'] == binding and saved['manifest_sha256'] == sha(root/'manifest.json'), 'final-products-input-changed')
        if qualifications is not None:
            require(saved['qualifications_sha256'] == pa.digest(qualifications), 'final-products-qualifications-changed')
        return verify(root/'manifest.json')
    retained = list(qualifications or ())
    if plan.get('source_archive'):
        prior = verify(plan['source_archive'])
        _, prior_paths = pa.verify_local(plan['source_archive'])
        products = pa.load(prior_paths[prior['products_key']])
        retained.extend(products['qualifications'])
        current = pa.load(manifest)
        identities = {(e['element_id'], e['source_sha256']) for e in current['elements']}
        for element in products['elements']:
            for finding in element.get('findings', []):
                scope = {k:element[k] for k in ('element_id','source_sha256')}
                retained.append(dict(scope=scope, metadata=finding,
                    source_association='matched' if (element['element_id'],element['source_sha256']) in identities else 'prior-extraction-unmapped'))
        retained.extend(dict(scope='Prior source evidence', reason=reason) for reason in products['source_limitations'])
    enriched = copy.deepcopy(exported)
    enriched['processing'] = dict(prepared_at=prepared['prepared_at'], protocol_sha256=pa.digest(prepared['code']))
    m = build(manifest, root, exports=[enriched], page=work/'original-page.md' if plan['page_path'] else None, qualifications=retained)
    ae._seal_file(work/'final-products-input.json', dict(inputs=binding, qualifications_sha256=pa.digest(qualifications or []), manifest_sha256=sha(root/'manifest.json')))
    return m


def page_register(work, plan, manifest, exported, submission):
    import reenrich as rr
    source, source_paths = pa.verify_local(manifest)
    previous = rr.read_register((absolute(work)/'original-page.md').read_text())
    if plan.get('source_archive'):
        source_paths.update(pa.verify_local(plan['source_archive'])[1])
    current = rr._current_register(exported, submission, source, plan,
                                  sha(absolute(work)/'export/annotated.html'), source_paths, previous)
    retained_qualifications = list(current['qualifications'])
    for target in current['selected_targets'] + current['selected_sources']:
        if target.get('qualification'):
            retained_qualifications.append(dict(reason=target['qualification'], provenance=target.get('reviewer',current['reviewer']),
                                               scope={k:target[k] for k in ('element_id','source_sha256','target','key','pointer') if k in target}))
    if current['operator_qualification']:
        retained_qualifications.append(dict(reason=current['operator_qualification'],provenance=current['reviewer'],scope='page'))
    m = prepare_refresh(work, plan, manifest, exported, retained_qualifications)
    _, paths = pa.verify_local(absolute(work)/'final-products/manifest.json')
    locator = dict(key=m['products_key'], sha256=sha(paths[m['products_key']]))
    qualifications = [dict(q, evidence=locator) for q in current['qualifications']]
    targets, sources = [], []
    records = {f['sha256']: f for f in m['files']}
    for replacement in submission['replacements']:
        for ref in replacement['evidence']:
            if ref.get('kind') in ('source', 'inspection'):
                require(ref['sha256'] in records, 'page-source-not-retained')
                sources.append(dict(ref, key=records[ref['sha256']]['key']))
            else:
                targets.append(dict(ref, reviewer=submission['reviewer'], evidence=locator))
    for target in current['selected_targets']:
        value = dict(target, evidence=locator)
        if value not in targets:
            targets.append(value)
    return dict(schema='portable-page-qualification-register-v4', binding=exported['binding'],
                article=m['article'], article_key=m['article_key'],
                publication_receipt=rr.page_receipt_name(plan['page_path'], exported['binding']),
                export_locator=locator, annotated_export_locator=locator,
                source_locators=[dict(document=d['identity'], key=d['raw_key'], sha256=d['source_sha256']) for d in m['documents']],
                reviewer=submission['reviewer'], operator_qualification=submission['qualification'],
                selected_targets=targets, selected_sources=sources, qualifications=qualifications,
                source_status=m['source_status'], enrichment_status=dict(counts=exported['request_accounting']['counts'],
                    requests_successful=exported['execution_complete']))


def publish_refresh(work, plan, manifest, source, roster, binding, history, exported, remote, bucket, prefix, runner):
    """Publish the frozen final evidence after the existing runtime/apply gates."""
    import reenrich as rr
    import article_enrichment as ae
    m = prepare_refresh(work, plan, manifest, exported)
    archive = work/'archive'
    completion = dict(binding=binding, completion=rr.completion_label(plan),
                      production_complete=not plan['fixture'], page_refresh_complete=bool(plan['page_path']),
                      page_sha256=sha(plan['page_path']) if plan['page_path'] else None,
                      requests_accounted_for=exported.get('readiness', {}).get('requests_accounted_for', exported['execution_complete']),
                      requests_successful=exported['execution_complete'], fixture=plan['fixture'], mode=plan['mode'], roster=roster)
    if plan['page_path']:
        completion['register_sha256'] = pa.digest(rr.read_register(absolute(plan['page_path']).read_text()))
    if not archive.exists():
        pa.restore(work/'final-products/manifest.json', archive)
        updated = copy.deepcopy(m); updated['package_id'] = 'refresh-' + binding[:20]
        updated['completion'] = completion
        # The register addresses immutable products, so adding the page hash
        # creates no page/manifest cycle and requires no post-apply page edit.
        (archive/'manifest.json').unlink(); pa.save(archive/'manifest.json', updated)
        mapping = pa.load(archive/'local-map.json'); mapping['manifest_sha256'] = sha(archive/'manifest.json')
        (archive/'local-map.json').unlink(); pa.save(archive/'local-map.json', mapping)
        (archive/'RESTORE-RECEIPT.json').unlink()  # temporary local copy, not a scientific product
        verify(archive/'manifest.json')
        rr._record(work, 'archive-build', [archive/'manifest.json', archive/'local-map.json'], dict(binding=binding))
    else:
        require(any(r['stage'] == 'archive-build' and r['result']['binding'] == binding for r in history), 'interrupted-archive-build-no-receipt')
        require(pa.load(archive/'manifest.json').get('completion') == completion, 'final-completion-input-changed')
    result = pa.publish(archive/'manifest.json', remote, bucket, prefix, runner=runner)
    rr.context(work)
    ae._seal_file(work/'publication.json', result)
    record = next(f for f in m['files'] if f['key'] == m['products_key'])
    receipt = dict(schema='portable-article-completion-v3', article=m['article'], publication=result,
                   export={k: record[k] for k in ('key', 'sha256')}, **completion)
    if plan['page_path']:
        pa.save(rr.page_receipt_path(plan['page_path'], binding), receipt)
    pa.save(work/'completion.json', receipt)
    rr.verify_completion(work/'completion.json', archive/'manifest.json', manifest_key=result['manifest_key'],
                         manifest_sha256=result['manifest_sha256'], article_key=m['article_key'], page=plan['page_path'])
    rr._record(work, 'publish', [work/'publication.json', work/'completion.json', archive/'manifest.json', archive/'local-map.json'], result)
    return rr.execute(plan, work_root=work)


def verify_completion(receipt, m, paths, page):
    """Caller has verified the pinned manifest, inventory and publication receipts."""
    import reenrich as rr
    require(receipt['schema'] == 'portable-article-completion-v3', 'final-completion-schema')
    facts = m['completion']
    require(all(receipt.get(k) == v for k, v in facts.items()), 'final-completion-binding')
    require(receipt['production_complete'] == (not facts['fixture']), 'final-completion-fixture')
    require(receipt['publication']['verification_scope'] == 'rclone-live-readback' or facts['fixture'], 'offline-publication-not-production')
    require(not receipt['production_complete'] or not m['source_status']['fixture'], 'fixture-promotion-forbidden')
    record = next(f for f in m['files'] if f['key'] == m['products_key'])
    require(receipt['export'] == {k: record[k] for k in ('key', 'sha256')}, 'final-export-binding')
    if facts['page_refresh_complete']:
        require(page is not None, 'completion-real-page-required')
        page = absolute(page); rr._page_identity(page, m['article']['slug'], m['article'])
        require(sha(page) == facts['page_sha256'], 'completion-page-snapshot')
        register = rr.read_register(page.read_text())
        require(register and pa.digest(register) == facts['register_sha256'] and register['binding'] == facts['binding'], 'completion-qualification-register-or-pointer')
        rr._register_archive(register, paths)
        require(pa.load(page.parent/register['publication_receipt']) == receipt, 'completion-page-receipt-pointer')
    else:
        require(page is None and facts['page_sha256'] is None, 'archive-only-not-page-refresh')
    return receipt


def from_ingest(handoff, destination, *, method, integration, enrichment_root):
    """Finalize initial ingestion before authoring the page's durable pointers."""
    import source_package
    import article_enrichment as ae
    verified = source_package.verify_handoff(handoff, method, integration=integration,
                                            enrichment_root=enrichment_root, require_enriched=True)
    require(verified['schema'] == 'source-package-handoff-v5', 'current-enriched-ingest-required')
    exported = copy.deepcopy(verified['enrichment'])
    require(exported['schema'] == 'qualified-enrichment-export-v2', 'current-enrichment-required')
    dossier = pa.load(absolute(exported['review_root'])/'dossier.json')
    prepared = ae.read_bound(absolute(dossier['snapshot']['path'])/'enrichment/prepared.json')
    exported['profile'] = prepared['profile']; exported['fixture'] = prepared['fixture']
    exported['processing'] = dict(prepared_at=prepared['prepared_at'], protocol_sha256=pa.digest(prepared['code']))
    m = build(exported['manifest'], destination, exports=[exported])
    m['initial_ingest'] = dict(source_handoff_sha256=sha(handoff),
                              production_complete=verified['production_complete'],
                              readiness=exported['readiness'], qualifications=verified['qualifications'])
    destination = absolute(destination)
    # This newly created package has not been published or referenced yet.
    (destination/'manifest.json').unlink(); pa.save(destination/'manifest.json', m)
    mapping = pa.load(destination/'local-map.json'); mapping['manifest_sha256'] = sha(destination/'manifest.json')
    (destination/'local-map.json').unlink(); pa.save(destination/'local-map.json', mapping)
    verify(destination/'manifest.json')
    return m


def verify_ingest(manifest, article, body):
    m = verify(manifest)
    require(all(m['article'].get(k) == v for k, v in article.items() if k in ('slug','title','doi','pmid')), 'final-ingest-article-binding')
    completed = m['initial_ingest']
    require(completed['production_complete'] is True and not m['source_status']['fixture'] and
            completed['readiness']['page_ready'] is True and not completed['readiness']['holds'], 'final-ingest-not-complete')
    require(completed['qualifications'] in body, 'final-ingest-qualifications-missing')
    return m


def main(argv=None):
    import argparse
    import json
    import sys
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    ingest = commands.add_parser('ingest')
    for flag in ('handoff', 'output', 'method', 'integration', 'enrichment-root'):
        ingest.add_argument('--'+flag, required=True)
    compact = commands.add_parser('compact')
    compact.add_argument('--manifest', required=True); compact.add_argument('--output', required=True)
    compact.add_argument('--page')
    check = commands.add_parser('verify'); check.add_argument('--manifest', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'ingest':
            m = from_ingest(args.handoff, args.output, method=args.method, integration=args.integration, enrichment_root=args.enrichment_root)
        elif args.command == 'compact':
            m = build(args.manifest, args.output, page=args.page)
        else:
            m = verify(args.manifest)
        print(json.dumps(dict(schema=m['schema'], article=m['article'], objects=m['total_objects'],
                              bytes=sum(f['size'] for f in m['files']), elements=len(m['elements'])), indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, ImportError) as exc:
        print(json.dumps(dict(status='hold', error=str(exc))), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
