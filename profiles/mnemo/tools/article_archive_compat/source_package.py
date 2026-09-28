"""Historical read-only dependency closure; extracted without changing validation contracts."""
import re
from urllib.parse import urlsplit, parse_qsl
CHANNELS = ['caption', 'figure', 'structured', 'classification', 'association']

def require(ok, message):
    if not ok:
        raise ValueError(message)

def public_url(value):
    """Reject credential-bearing inputs; never silently rewrite source tokens."""
    require(isinstance(value, str), 'URL required')
    u = urlsplit(value)
    require(u.scheme in ('http', 'https') and u.hostname and (not u.username) and (not u.password), 'public HTTP URL required')
    for (key, _) in parse_qsl(u.query, keep_blank_values=True) + parse_qsl(u.fragment, keep_blank_values=True):
        require(not re.search('token|secret|password|credential|signature|api.?key|authorization|cookie', key, re.I), 'credential-bearing URL forbidden; retain only public source URL')
    return value

def identifier(value):
    require(isinstance(value, str) and re.fullmatch('[a-zA-Z0-9][a-zA-Z0-9._-]*', value), 'safe identifier required')
    return value

def file_metadata(row, article, *, scoped=False):
    identifier(row['id'])
    require(set(row) <= {'id', 'role', 'format', 'path', 'sha256', 'filename', 'source_url', 'discovery_url', 'article_slug', 'identity_verification', 'page_count', 'extraction_disposition'} | ({'relationship', 'publisher_description'} if scoped else set()), 'unknown source fields; no selected-page/channel diagnostics')
    require(row['role'] in ('manuscript', 'supplement', 'body'), 'source role')
    require(row['format'] in ('pdf', 'other'), 'source format')
    require(row['role'] != 'manuscript' or row['format'] == 'pdf', 'original manuscript must be PDF')
    name = row['filename']
    require(isinstance(name, str) and name not in ('', '.', '..') and ('/' not in name) and ('\\' not in name), 'filename must be a basename')
    require(row['article_slug'] == article['slug'], 'source article identity mismatch')
    identity = row['identity_verification']
    require(identity['status'] == 'operator-verified' and isinstance(identity['basis'], str) and identity['basis'].strip(), 'operator identity verification required (not adapter verification)')
    if 'relationship' in row:
        require(scoped and row['relationship'] == 'alternative' and (row['role'] == 'supplement') and (row['format'] == 'pdf'), 'alternative source must be a supplement-role PDF')
    if 'publisher_description' in row:
        require(isinstance(row['publisher_description'], str), 'publisher description must be text')
    public_url(row['source_url'])
    public_url(row['discovery_url'])

def validate_acquisition(value):
    require(value['schema'] in ('acquired-sources-v1', 'acquired-sources-v2'), 'acquisition schema')
    scoped = value['schema'] == 'acquired-sources-v2'
    require(set(value) == {'schema', 'article', 'files', 'attempts', 'obligations', 'attachments'} | ({'processing'} if scoped else set()), 'unknown acquisition fields')
    article = value['article']
    identifier(article['slug'])
    require(all((k in article for k in ('title', 'doi', 'pmid', 'version'))), 'explicit article identity fields required')
    require(isinstance(article['title'], str) and article['title'].strip() and article['version'], 'article title and version required')
    files = value['files']
    attempts = value['attempts']
    require(isinstance(files, list) and isinstance(attempts, list), 'files and attempts lists required')
    ids = [r['id'] for r in files]
    aids = [r['id'] for r in attempts]
    require(len(ids) == len(set(ids)) and len(aids) == len(set(aids)), 'duplicate source/attempt ID')
    require(len({r['sha256'] for r in files}) == len(files), 'duplicate source bytes; list aliases as discovery evidence, not duplicate files')
    for row in files:
        file_metadata(row, article, scoped=scoped)
    for row in attempts:
        identifier(row['id'])
        public_url(row['source_url'])
        require(row['outcome'] in ('failed', 'retrieved', 'unknown'), 'attempt outcome')
        require(row['route'] and row['observed_at'] and (row['raw_response'] in ('available', 'unavailable')), 'attempt evidence metadata')
        require(isinstance(row['artifacts'], list), 'attempt artifacts list')
        require(row['artifacts'] or (row['raw_response'] == 'unavailable' and row['limitation']), 'missing attempt evidence limitation')
        require(row['raw_response'] != 'unavailable' or row['limitation'], 'raw response limitation required')
    require(set(value['obligations']) == {'body', 'manuscript'}, 'body/manuscript obligations required')
    for role in ('body', 'manuscript'):
        obligation = value['obligations'][role]
        require(obligation['status'] in ('retrieved', 'missing'), 'body/manuscript disposition required')
        if obligation['status'] == 'retrieved':
            expected = {r['id'] for r in files if r['role'] == role}
            require(expected and set(obligation['file_ids']) == expected, 'obligation source binding')
        else:
            require(obligation['disposition'] and set(obligation['attempt_ids']) <= set(aids), 'missing source disposition')
            require(not any((r['role'] == role for r in files)), 'missing obligation contradicts retained source')
    attachments = value['attachments']
    require(attachments['status'] in ('not-inspected', 'none-listed', 'advertised'), 'attachment discovery state')
    items = attachments['items']
    require(isinstance(items, list) and len({x['id'] for x in items}) == len(items), 'attachment items')
    if attachments['status'] != 'not-inspected':
        public_url(attachments['inspected_url'])
    require((attachments['status'] == 'advertised') == bool(items), 'advertised attachments must be enumerated')
    retained = []
    for item in items:
        identifier(item['id'])
        public_url(item['observed_link'])
        require(item['filename'], 'advertised filename required')
        if item['status'] == 'retrieved':
            retained.append(item['file_id'])
        else:
            require(item['status'] == 'missing' and item['disposition'] and (set(item['attempt_ids']) <= set(aids)), 'missing attachment disposition')
    supplements = {r['id'] for r in files if r['role'] == 'supplement'}
    if scoped:
        require(supplements <= set(retained) <= {r['id'] for r in files if r['role'] in ('manuscript', 'supplement')}, 'silent attachment loss or unknown alias')
        for item in items:
            if item['status'] == 'retrieved':
                row = next((r for r in files if r['id'] == item['file_id']))
                require(item['observed_link'] in (row['source_url'], row['discovery_url']), 'attachment alias link binding')
        processing_sources(value)
    else:
        require(len(retained) == len(set(retained)) and set(retained) == supplements, 'silent or duplicate attachment loss')

def processing_sources(acquisition):
    """Select processing inputs without changing retention or inferring boundaries."""
    if acquisition['schema'] == 'acquired-sources-v1':
        return [dict(r, pages=list(range(1, r['page_count'] + 1))) for r in acquisition['files'] if r['format'] == 'pdf']
    require(acquisition['schema'] == 'acquired-sources-v2', 'acquisition schema')
    processing = acquisition['processing']
    require(set(processing) == {'policy', 'manuscript'} and processing['policy'] == 'manuscript-only-v1', 'processing policy')
    selected = processing['manuscript']
    require(set(selected) == {'source_id', 'pages', 'basis'}, 'manuscript scope fields')
    require(isinstance(selected['basis'], str) and selected['basis'].strip(), 'manuscript boundary basis required')
    rows = [r for r in acquisition['files'] if r['id'] == selected['source_id']]
    require(len(rows) == 1 and rows[0]['role'] == 'manuscript' and (rows[0]['format'] == 'pdf'), 'processing manuscript source')
    pages = selected['pages']
    require(isinstance(pages, list) and pages and all((type(n) is int and n > 0 for n in pages)) and (pages == sorted(set(pages))), 'processing physical pages')
    if 'page_count' in rows[0]:
        require(pages[-1] <= rows[0]['page_count'], 'processing page out of range')
    return [dict(rows[0], pages=list(pages))]

def verify_processing_scope(acquisition, scope, documents):
    """Verify selected source/pages; acquisition=None checks preparation shape only."""
    processing = scope.get('processing')
    if processing is None:
        require(acquisition is None or acquisition['schema'] == 'acquired-sources-v1', 'missing processing binding')
        require(all((d['extraction_scope'] == 'whole-document' for d in documents)), 'selected-page diagnostic not production scope')
        return dict(policy='all-pdfs-v1', complete=all((d.get('complete_package', False) for d in documents)))
    selected = processing.get('manuscript', {})
    require(processing.get('policy') == 'manuscript-only-v1' and set(processing) == {'policy', 'manuscript'} and (set(selected) == {'source_id', 'pages', 'basis'}), 'processing binding fields')
    pages = selected['pages']
    require(isinstance(selected['basis'], str) and selected['basis'].strip() and isinstance(pages, list) and pages and all((type(n) is int and n > 0 for n in pages)) and (pages == sorted(set(pages))), 'processing binding pages/basis')
    sources = scope['documents']
    require(len(sources) == 1 and sources[0]['identity'] == selected['source_id'] and (sources[0]['pages'] == pages) and (set(sources[0]['channels']) == set(CHANNELS)), 'processing source/page/channel binding')
    if acquisition is not None:
        require(acquisition['schema'] == 'acquired-sources-v2' and acquisition['processing'] == processing, 'acquisition processing binding')
        row = processing_sources(acquisition)[0]
        require(row['sha256'] == sources[0]['sha256'] and row['page_count'] == sources[0]['page_count'], 'processing original binding')
    if documents:
        require(len(documents) == 1 and documents[0]['identity'] == selected['source_id'] and ([p['page'] for p in documents[0]['pages']] == pages) and all((p['selected'] for p in documents[0]['pages'])), 'processing document binding')
    return dict(policy=processing['policy'], source_id=selected['source_id'], pages=list(pages), complete=bool(documents) and all((d.get('requested_work_complete', False) and d.get('logical', {}).get('complete', False) for d in documents)))

def source_readiness(acquisition, facts, *, fixture, stopped=False):
    """Verified evidence may be partial; pending work needs an attributed disposition.

    This policy never changes mechanical completion or authorizes a retry.
    Namespaced pending keys share the enrichment review's unattempted map.
    """
    pending = []
    holds = ['fixture-not-production'] if fixture else []
    for (role, value) in acquisition['obligations'].items():
        if value['status'] != 'retrieved' and (not value.get('disposition', '').strip()):
            pending.append('source:acquisition:' + role)
    attachments = acquisition['attachments']
    if attachments['status'] == 'not-inspected':
        pending.append('source:attachments')
    for item in attachments['items']:
        if item['status'] != 'retrieved' and (not item.get('disposition', '').strip()):
            pending.append('source:attachment:' + item['id'])
    for (phase, row) in facts['phases'].items():
        if row['status'] == 'not-prepared':
            pending.append('source:phase:' + phase)
        if row['fixture_or_replay_calls']:
            holds.append('fixture-or-replay-' + phase)
    for row in facts['requests']:
        if not row['attempted'] and (not row['uncertain_reservation']):
            pending.append('source:request:' + row['id'])
    if stopped:
        holds.append('workflow-stop-record')
    inspection = facts['inspection']
    if inspection['status'] in ('incomplete-records', 'directory-missing'):
        holds.append('inspection-evidence-incomplete')
    if inspection['fixture_or_replay_calls']:
        holds.append('fixture-inspection-not-production')
    return dict(policy='source-readiness-v1', pending=sorted(pending), holds=sorted(holds))

def validate_source_readiness(value):
    require(set(value) == {'policy', 'pending', 'holds'} and value['policy'] == 'source-readiness-v1', 'unknown-source-readiness-policy')
    for key in ('pending', 'holds'):
        require(isinstance(value[key], list) and all((isinstance(x, str) and x for x in value[key])) and (value[key] == sorted(set(value[key]))), 'source-readiness-fields')
    require(all((x.startswith('source:') for x in value['pending'])), 'source-pending-namespace')
    return value
