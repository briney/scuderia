"""Historical read-only dependency closure; extracted without changing validation contracts."""
from __future__ import annotations
from pathlib import Path
from article_archive_compat import portable_articles as pa
from article_archive_compat.article_runtime import absolute, require, sha
POLICY = 'final-products-v1'
PRODUCT_SCHEMA = 'article-scientific-products-v1'
CORRECTED_PRODUCT_SCHEMA = 'article-scientific-products-v2'

def validate(m):
    require(m['provenance'].get('retention_policy') == POLICY, 'final-products-policy')
    if m['schema'] == pa.SCOPED_FINAL_SCHEMA:
        from article_archive_compat import source_package as adapter
        processing = m.get('processing')
        require(isinstance(processing, dict), 'final-processing-required')
        selected = processing.get('manuscript', {})
        source_id = selected.get('source_id')
        document = next((d for d in m['documents'] if d.get('source_id', d['identity']) == source_id), None)
        require(document is not None, 'final-processing-document')
        sources = [s for s in m['source_documents'] if s.get('source_id', s['identity']) == source_id]
        require(len(sources) == 1 and sources[0]['sha256'] == document['source_sha256'], 'final-processing-original')
        scope = dict(processing=processing, documents=[dict(identity=source_id, pages=selected.get('pages'), channels=adapter.CHANNELS)])
        adapter.verify_processing_scope(None, scope, [])
        metadata = sources[0].get('acquisition', {})
        if metadata:
            require(metadata['role'] == 'manuscript' and metadata['format'] == 'pdf', 'final-processing-manuscript-role')
            require(max(selected['pages']) <= metadata['page_count'], 'final-processing-page-range')
        extra = {d['identity'] for d in m['documents'] if d is not document}
        require(extra == set(m.get('preserved_documents', [])), 'final-unprocessed-document-roster')
        for page in m['text_pages']:
            if page.get('document') == document['identity']:
                require(page.get('page') in selected['pages'], 'final-processing-text-page')
        for element in m['elements']:
            if element['document'] == document['identity']:
                require(all((f['page'] in selected['pages'] for f in element['fragments'])), 'final-processing-fragment-page')
    records = {f['key']: f for f in m['files']}
    require(len({f['sha256'] for f in m['files']}) == len(records), 'duplicate-final-product-bytes')
    require(m['products_key'] in records and records[m['products_key']]['role'] == 'enrichment-export', 'missing-final-results')
    require(set(m['native_text_keys']) <= records.keys(), 'missing-final-native-text')
    require(m['source_documents'], 'final-sources-required')
    require(len({s['identity'] for s in m['source_documents']}) == len(m['source_documents']), 'duplicate-final-source-identity')
    allowed = {m['products_key']} | set(m['native_text_keys']) | set(m['caption_crop_keys'])
    allowed.update((s['key'] for s in m['source_documents']))
    for e in m['elements']:
        allowed.update((f['crop_key'] for f in e['fragments']))
        allowed.update((f['crop'] for f in e['evidence'].get('body_fragments', []) + e['evidence'].get('captions', [])))
    require(allowed == records.keys(), 'nonproduct-archive-file')
    for f in m['files']:
        require(f['key'].split('/')[0] in ('sources', 'text', 'crops', 'results') and Path(f['key']).stem == f['sha256'], 'final-product-content-key')
    require({row['key'] for row in m['text_pages']} == set(m['native_text_keys']), 'native-page-index')
    for s in m['source_documents']:
        require(s['key'] in records and records[s['key']]['sha256'] == s['sha256'] and (records[s['key']]['role'] == 'source-original'), 'final-source-binding')
    return m

def verify(manifest_path):
    (m, paths) = pa.verify_local(manifest_path)
    require(pa.is_final_manifest(m), 'final-products-required')
    validate(m)
    products = pa.load(paths[m['products_key']])
    require(products['schema'] in (PRODUCT_SCHEMA, CORRECTED_PRODUCT_SCHEMA), 'final-results-schema')
    if products['schema'] == CORRECTED_PRODUCT_SCHEMA:
        require(isinstance(products.get('amendments'), list) and products['amendments'], 'corrected-products-amendments-required')
        from article_archive_compat.qualified_enrichment import reviews
        for amendment in products['amendments']:
            reviews.provenance(amendment['reviewer'])
            require(amendment['reason'] and amendment['changes'], 'correction-attribution-required')
            for change in amendment['changes']:
                require(pa.digest(change['original']) == change['old_sha256'] and change['source_refs'], 'correction-original-binding')
    elements = {e['element_id']: e for e in m['elements']}
    documents = {d['identity']: d for d in m['documents']}
    records = {f['key']: f for f in m['files']}
    caption_keys = set()
    for caption in products.get('source_captions', []):
        require(caption['source_document'] in documents and caption['source_sha256'] == documents[caption['source_document']]['source_sha256'], 'caption-source-binding')
        for region in caption['regions']:
            if region.get('crop'):
                key = region['crop']
                caption_keys.add(key)
                require(key in records and (not region.get('crop_sha256') or region['crop_sha256'] == records[key]['sha256']), 'caption-crop-binding')
    require(caption_keys == set(m['caption_crop_keys']), 'caption-crop-inventory')
    seen = set()
    for e in products['elements']:
        require(e['element_id'] not in seen and e['element_id'] in elements and (e['source_sha256'] == elements[e['element_id']]['source_sha256']), 'result-source-binding')
        seen.add(e['element_id'])
    return m

def verify_completion(receipt, m, paths, page, manifest_path):
    """Caller has verified the pinned manifest, inventory and publication receipts."""
    from article_archive_compat import reenrich as rr
    require(receipt['schema'] == 'portable-article-completion-v3', 'final-completion-schema')
    facts = m['completion']
    require(all((receipt.get(k) == v for (k, v) in facts.items())), 'final-completion-binding')
    require(receipt['production_complete'] == (not facts['fixture']), 'final-completion-fixture')
    require(receipt['publication']['verification_scope'] == 'rclone-live-readback' or facts['fixture'], 'offline-publication-not-production')
    require(not receipt['production_complete'] or not m['source_status']['fixture'], 'fixture-promotion-forbidden')
    record = next((f for f in m['files'] if f['key'] == m['products_key']))
    require(receipt['export'] == {k: record[k] for k in ('key', 'sha256')}, 'final-export-binding')
    if facts['page_refresh_complete']:
        require(page is not None, 'completion-real-page-required')
        page = absolute(page)
        rr._page_identity(page, m['article']['slug'], m['article'])
        require(sha(page) == facts['page_sha256'], 'completion-page-snapshot')
        register = rr.read_register(page.read_text())
        if facts.get('page_register_location') == 'archive':
            require(register is None, 'page-must-not-contain-register')
            register = facts['page_register']
        require(register and pa.digest(register) == facts['register_sha256'] and (register['binding'] == facts['binding']), 'completion-qualification-register-or-pointer')
        rr._register_archive(register, paths)
        if facts.get('page_storage') == 'archive-only-v1':
            from article_archive_compat import figure_embeds
            figure_embeds.verify_archive_only(page.read_text())
            require('Article archive: ' + register['publication_receipt'] in page.read_text().splitlines(), 'completion-page-archive-pointer')
        if facts.get('figure_embeds'):
            from article_archive_compat import figure_embeds
            figure_embeds.verify(page.read_text(), manifest_path, page)
        require(pa.load(page.parent / register['publication_receipt']) == receipt, 'completion-page-receipt-pointer')
    else:
        require(page is None and facts['page_sha256'] is None, 'archive-only-not-page-refresh')
    return receipt

def verify_ingest(manifest, article, body, page=None, *, publication_receipt=None, require_publication=True):
    m = verify(manifest)
    require(all((m['article'].get(k) == v for (k, v) in article.items() if k in ('slug', 'title', 'doi', 'pmid'))), 'final-ingest-article-binding')
    completed = m['initial_ingest']
    require(completed['production_complete'] is True and (not m['source_status']['fixture']) and (completed['readiness']['page_ready'] is True) and (not completed['readiness']['holds']), 'final-ingest-not-complete')
    require(isinstance(completed['qualifications'], str), 'final-ingest-qualifications-missing')
    if completed.get('page_storage') == 'archive-only-v1':
        from article_archive_compat import figure_embeds
        figure_embeds.verify_archive_only(body)
    if completed.get('figure_embeds'):
        from article_archive_compat import figure_embeds
        require(page is not None, 'figure-page-path-required')
        figure_embeds.verify(body, manifest, page)
    if require_publication:
        require(publication_receipt is not None, 'publication-receipt-required')
        verify_publication(manifest, pa.load(publication_receipt))
    return m

def verify_publication(manifest, publication):
    """Verify saved remote read-back against this exact local final inventory."""
    (m, _) = pa.verify_local(manifest)
    require(publication.get('schema') == 'portable-article-publication-v2', 'publication-schema')
    require(publication.get('verification_scope') == 'rclone-live-readback', 'offline-publication-not-production')
    pa.RcloneTransport(publication['remote'], publication['bucket'])
    key = pa.revision_prefix(m, publication['prefix']) + '/manifests/' + sha(manifest) + '.json'
    require(publication['manifest_sha256'] == sha(manifest) and publication['manifest_key'] == key and (publication['article_key'] == m['article_key']), 'publication-manifest-binding')
    expected = {(pa.object_key(m, publication['prefix'], f), f['sha256'], f['size']) for f in m['files']}
    expected.add((key, sha(manifest), absolute(manifest).stat().st_size))
    rows = publication['receipts']
    require(publication['objects'] == len(m['files']) and len(rows) == len(expected) and (expected == {(r['key'], r['sha256'], r['size']) for r in rows}) and all((r['method'] == 'read_back_sha256' for r in rows)), 'publication-readback-inventory')
    return publication
