"""External article packages and historical source reuse."""
from pathlib import Path
import re
from urllib.parse import urlsplit
from article_archive_compat import reader, portable_articles as pa
from . import workflow as w

SCHEMA='manuscript-article-package-v1'


def receipt_pointer(destination, name):
    """Assign an immutable receipt location before snapshotting (no hash cycle)."""
    w.require(re.fullmatch(r'(?:[0-9a-f]{32}-[1-9][0-9]*|[0-9a-f]{64})', name) is not None, 'archive-pointer-name')
    w.require(re.fullmatch(r'[a-z0-9][a-z0-9.-]*', destination['bucket']) is not None, 'archive-pointer-bucket')
    return 'r2://' + destination['bucket'] + '/' + pa.relative_key(destination['prefix']) + '/receipts/' + name + '.json'


def receipt_key(pointer, destination):
    w.require(isinstance(pointer, str) and destination, 'archive-pointer-transport-required')
    parsed = urlsplit(pointer)
    name = parsed.path.rsplit('/', 1)[-1].removesuffix('.json')
    w.require(pointer == receipt_pointer(destination, name), 'archive-pointer-destination-mismatch')
    return pa.relative_key(parsed.path.removeprefix('/'))


def retain_receipt(receipt, *, destination, pointer=None):
    """Keep the full receipt outside the brain and verify its remote bytes."""
    value = pa.load(receipt); publication = value.get('publication', value)
    w.require(value.get('schema') == 'manuscript-publication-v1' or value.get('schema', '').startswith('portable-article-completion-'), 'unsupported-publication-receipt')
    w.require(all(publication[k] == destination[k] for k in ('remote', 'bucket', 'prefix')), 'trusted-transport-mismatch')
    pointer = pointer or receipt_pointer(destination, w.sha(receipt))
    key = receipt_key(pointer, destination)
    if re.fullmatch('[0-9a-f]{64}',Path(key).stem):
        w.require(Path(key).stem==w.sha(receipt),'receipt-hash-mismatch')
    pa.RcloneTransport(destination['remote'], destination['bucket']).upload(Path(receipt), key, w.sha(receipt), Path(receipt).stat().st_size)
    return pointer


def resolve_receipt(pointer, cache, *, transport):
    """Restore receipt metadata to external work storage, never beside the page."""
    key = receipt_key(pointer, transport); cache = w.outside_instance(cache)
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / (w.digest(pointer) + '.json')
    name = key.rsplit('/', 1)[-1].removesuffix('.json')
    expected = name if re.fullmatch('[0-9a-f]{64}', name) else None
    if not path.exists():
        pa.RcloneTransport(transport['remote'], transport['bucket']).download(key, path, expected_hash=expected, limit=pa.MAX_MANIFEST_BYTES)
    w.require(expected is None or w.sha(path) == expected, 'receipt-hash-mismatch')
    value = pa.load(path); publication = value.get('publication', value)
    w.require(all(publication[k] == transport[k] for k in ('remote', 'bucket', 'prefix')), 'trusted-transport-mismatch')
    return path


def page_matches(snapshot, page, receipt=None):
    """Only an exact, hash-pinned receipt relocation may differ from the snapshot."""
    old=Path(snapshot).read_bytes(); current=Path(page).read_bytes()
    if old==current:return True
    if receipt is None:return False
    value=pa.load(receipt); publication=value.get('publication',value)
    pointer=receipt_pointer(publication,w.sha(receipt))
    lines=re.findall(rb'^Article archive: .+$',old,re.M)
    if len(lines)!=1:return False
    return re.sub(rb'^Article archive: .+$',('Article archive: '+pointer).encode(),old,count=1,flags=re.M)==current


def open_sources(receipt,destination,*,transport=None,cache=None):
    if isinstance(receipt,str) and receipt.startswith('r2://'):
        local=resolve_receipt(receipt,Path(destination).parent/'receipts',transport=transport)
        restored=open_sources(local,destination,transport=transport,cache=cache)
        if not re.search(r'/[0-9a-f]{64}\.json$',receipt):
            w.require(pa.load(Path(destination)/'manifest.json').get('receipt_name')==receipt,'restored-receipt-pointer-binding')
        return restored
    value=pa.load(receipt)
    publication=value.get('publication',value)
    cached=(cache or {}).get(publication.get('manifest_sha256'))
    if cached:
        cached=Path(cached); w.require(w.sha(cached)==publication['manifest_sha256'],'cached-manifest-binding')
        restored=open_sources(cached,destination)
        restored['history']['receipt']=value
        return restored
    if value.get('schema')==SCHEMA or value.get('schema')=='manuscript-publication-v1':
        return restore_sources(receipt,destination,transport=transport)
    if not destination.exists(): reader.restore(receipt,destination,transport=transport)
    manifest=destination/'manifest.json'
    expected=w.sha(receipt) if value.get('schema','').startswith('portable-article-manifest-') else publication['manifest_sha256']
    w.require(w.sha(manifest)==expected,'restored-manifest-binding')
    m=reader.verify(manifest); _, paths=pa.verify_local(manifest)
    selected=m.get('processing',{}).get('manuscript',{})
    documents=m.get('source_documents') or [dict(identity=d['identity'],key=d['raw_key'],role=d.get('source_role'),source_id=d.get('source_id')) for d in m['documents']]
    mains=[s for s in documents if (s.get('source_id') or s['identity'])==selected.get('source_id') or s.get('role')=='manuscript']
    w.require(len(mains)==1,'historical-manuscript-identity-ambiguous')
    inputs=[]
    for source in documents:
        main=source is mains[0]; row=dict(path=str(paths[source['key']]),role='manuscript' if main else 'supplement',
            identity={k:v for k,v in m['article'].items() if k in ('doi','pmid','version') and v},basis='Verified historical archive identity and original byte binding.')
        if main and selected.get('pages'):row['pages']=selected['pages']
        inputs.append(row)
    history=dict(receipt=pa.load(receipt),manifest_sha256=pa.sha(manifest),identity=m['article'])
    if m.get('products_key'):history['products']=pa.load(paths[m['products_key']])
    return dict(identity=m['article'],inputs=inputs,history=history)


def verify(manifest):
    m=pa.load(manifest); w.require(m.get('schema')==SCHEMA,'modern-article-schema')
    w.require(m['scope']=='manuscript-to-page' and m['identity'].get('title'),'modern-article-identity')
    w.require(m['article_key']==w.digest({k:m['identity'].get(k) for k in ('slug','doi','pmid')}),'modern-article-key')
    keys=set(); aliases=set(); records={}
    for row in m['files']:
        key=pa.relative_key(row['key']); w.require(key not in keys and key.casefold() not in aliases and key!='manifest.json','duplicate-or-reserved-key')
        keys.add(key); aliases.add(key.casefold()); records[key]=row
        path=pa.inside(Path(manifest).parent,key)
        w.require(type(row['size']) is int and 0<=row['size']<=pa.MAX_OBJECT_BYTES,'invalid-object-size')
        w.require(path.is_file() and path.stat().st_size==row['size'] and w.sha(path)==row['sha256'],'corrupt-article-object:'+key)
    w.require({'page.md','pending-page.md','review.txt','provenance.json'}<=keys,'missing-article-products')
    w.require(sum(s['role']=='manuscript' for s in m['sources'])==1,'one-manuscript-required')
    for source in m['sources']:
        w.require(source['key'] in records and records[source['key']]['sha256']==source['sha256'],'source-inventory-binding')
        for page in source.get('text',[]):
            w.require(page['key'] in records and records[page['key']]['sha256']==page['sha256'],'text-inventory-binding')
    for key in ('page.md','pending-page.md'):
        text=(Path(manifest).parent/key).read_text(); fm=w.page_metadata(text)
        w.require(all(fm.get(k)==m['identity'].get(k) for k in ('slug','title','doi','pmid')),'archive-page-identity')
        w.require(('Article archive: '+m['receipt_name']) in text.splitlines(),'archive-page-pointer')
    w.require(w.page_metadata((Path(manifest).parent/'page.md').read_text())['needs-ingest'] is False,'archive-final-queue-state')
    w.require(w.page_metadata((Path(manifest).parent/'pending-page.md').read_text())['needs-ingest'] is True,'archive-pending-queue-state')
    if 'citations.json' in keys:
        evidence=pa.load(Path(manifest).parent/'citations.json')
        w.require('annotated-page.md' in keys and evidence['annotated_sha256']==records['annotated-page.md']['sha256']
            and evidence['draft_sha256']==records['pending-page.md']['sha256']
            and evidence['page_sha256']==records['page.md']['sha256'],'citation-product-binding')
    return m


def build(job_id,revision,*,runtime_root):
    import shutil
    import re
    from .sources import verify_sources
    job=w.load_job(job_id,runtime_root); work=w.job_path(job_id,runtime_root)
    w.require(type(revision) is int and 1<=revision<=job['revision'],'invalid-draft-revision')
    draft=work/'drafts'/str(revision); meta=pa.load(draft/'revision.json')
    w.require(not meta['material_issues'],'material-review-hold')
    w.require(w.sha(draft/'page.md')==meta['page_sha256'] and w.sha(draft/'review.txt')==meta['review_sha256'],'draft-or-review-changed')
    for name,h in meta.get('citation_products',{}).items():
        w.require(name in ('annotated-page.md','citations.json') and w.sha(draft/name)==h,'citation-product-changed')
    verify_sources(job,work)
    root=work/'archives'/str(revision); manifest=root/'manifest.json'
    if manifest.exists(): verify(manifest); return manifest
    root.mkdir(parents=True,exist_ok=True)
    keys=[]
    for source in job['sources']:
        keys.append(source['key']); keys.extend(p['key'] for p in source.get('text',[]))
    for key in keys:
        target=pa.inside(root,key); target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(work/key,target)
    (root/'pending-page.md').write_bytes((draft/'page.md').read_bytes())
    (root/'page.md').write_text(re.sub(r'^needs-ingest: true$','needs-ingest: false',(draft/'page.md').read_text(),count=1,flags=re.M))
    (root/'review.txt').write_bytes((draft/'review.txt').read_bytes())
    if meta.get('citation_products'):
        (root/'annotated-page.md').write_bytes((draft/'annotated-page.md').read_bytes())
        evidence=pa.load(draft/'citations.json')
        evidence['page_sha256']=w.sha(root/'page.md')
        w.save(root/'citations.json',evidence)
    if (work/'original.md').exists():
        w.require(w.sha(work/'original.md')==job['original_sha256'],'original-page-snapshot-changed')
        (root/'original.md').write_bytes((work/'original.md').read_bytes())
    base=Path(meta.get('base_snapshot',work/'original.md'))
    if base.exists():
        w.require(meta.get('base_sha256') is None or w.sha(base)==meta['base_sha256'],'base-page-snapshot-changed')
        (root/'base-page.md').write_bytes(base.read_bytes())
    provenance=dict(job_id=job_id,revision=revision,source_hashes=meta['source_hashes'],original_page_sha256=job['original_sha256'],
        policy='Full manuscript reading with focused scientific review; no exhaustive figure/table certification.',
        base_page_sha256=meta.get('base_sha256',job['original_sha256']),
        warnings=job['warnings'],inspections=job.get('inspection_keys',{}),history=job.get('history'))
    w.save(root/'provenance.json',provenance)
    if (work/'inspections').exists():
        for path in (work/'inspections').rglob('*'):
            if path.is_file():
                w.absolute(path); target=root/path.relative_to(work); target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(path,target)
    files=[dict(key=str(p.relative_to(root)),sha256=w.sha(p),size=p.stat().st_size) for p in sorted(root.rglob('*')) if p.is_file()]
    m=dict(schema=SCHEMA,scope=job['scope'],identity=job['identity'],article_key=w.digest({k:job['identity'].get(k) for k in ('slug','doi','pmid')}),
        job_id=job_id,revision=revision,receipt_name=meta['receipt_name'],sources=job['sources'],files=files)
    w.save(manifest,m); verify(manifest); return manifest


def object_key(m,prefix,row):
    return pa.relative_key(prefix)+'/articles/'+m['article_key']+'/objects/'+row['sha256']


def publication_check(manifest,receipt):
    m=verify(manifest); h=w.sha(manifest)
    w.require(receipt.get('schema')=='manuscript-publication-v1' and receipt['verification_scope']=='rclone-live-readback','unverified-publication')
    w.require(receipt['manifest_sha256']==h and receipt['article_key']==m['article_key'],'publication-manifest-binding')
    expected={(object_key(m,receipt['prefix'],r),r['sha256'],r['size']) for r in m['files']}
    mk=pa.relative_key(receipt['prefix'])+'/articles/'+m['article_key']+'/manifests/'+h+'.json'
    w.require(receipt['manifest_key']==mk,'publication-manifest-key')
    if m['receipt_name'].startswith('r2://'):
        w.require(m['receipt_name']==receipt_pointer(receipt,m['job_id']+'-'+str(m['revision'])),'publication-pointer-binding')
    expected.add((mk,h,Path(manifest).stat().st_size))
    actual={(r['key'],r['sha256'],r['size']) for r in receipt['receipts']}
    w.require(actual==expected and all(r['method']=='read_back_sha256' for r in receipt['receipts']),'publication-readback-inventory')
    return receipt


def publish(manifest,*,destination):
    m=verify(manifest); prefix=pa.relative_key(destination['prefix']); h=w.sha(manifest)
    transport=pa.RcloneTransport(destination['remote'],destination['bucket']); receipts=[]
    for row in m['files']:
        receipts.append(transport.upload(Path(manifest).parent/row['key'],object_key(m,prefix,row),row['sha256'],row['size']))
    mk=prefix+'/articles/'+m['article_key']+'/manifests/'+h+'.json'
    receipts.append(transport.upload(Path(manifest),mk,h,Path(manifest).stat().st_size))
    value=dict(schema='manuscript-publication-v1',verification_scope='rclone-live-readback',manifest_key=mk,manifest_sha256=h,
        article_key=m['article_key'],remote=destination['remote'],bucket=destination['bucket'],prefix=prefix,receipts=receipts)
    return publication_check(manifest,value)


def _materialize_sources(receipt,destination,*,transport=None):
    import shutil
    value=pa.load(receipt); destination=w.outside_instance(destination); destination.mkdir(parents=True,exist_ok=True)
    if value.get('schema')==SCHEMA:
        manifest=Path(receipt); m=verify(manifest)
        for row in m['files']:
            target=pa.inside(destination,row['key']); target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists():shutil.copyfile(manifest.parent/row['key'],target)
        shutil.copyfile(manifest,destination/'manifest.json')
    else:
        w.require(transport and all(value[k]==transport[k] for k in ('remote','bucket','prefix')),'trusted-transport-mismatch')
        client=pa.RcloneTransport(transport['remote'],transport['bucket']); manifest=destination/'manifest.json'
        if not manifest.exists(): client.download(value['manifest_key'],manifest,value['manifest_sha256'],limit=pa.MAX_MANIFEST_BYTES)
        w.require(w.sha(manifest)==value['manifest_sha256'],'restored-manifest-binding')
        m=pa.load(manifest); w.require(m['schema']==SCHEMA and m['article_key']==value['article_key'],'restore-identity')
        for row in m['files']:
            target=pa.inside(destination,row['key']); target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists():client.download(object_key(m,transport['prefix'],row),target,row['sha256'],row['size'])
        publication_check(manifest,value)
    verify(destination/'manifest.json')


def restore_sources(receipt,destination,*,transport=None):
    import os
    import tempfile
    destination=w.outside_instance(destination); value=pa.load(receipt)
    if value.get('schema')!='manuscript-article-package-v1':
        w.require(transport and all(value[k]==transport[k] for k in ('remote','bucket','prefix')),'trusted-transport-mismatch')
    if not destination.exists():
        destination.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.restore-',dir=destination.parent) as tmp:
            staged=Path(tmp)/'package'
            _materialize_sources(receipt,staged,transport=transport)
            os.rename(staged,destination)
    expected=w.sha(receipt) if value.get('schema')==SCHEMA else value['manifest_sha256']
    w.require(w.sha(destination/'manifest.json')==expected,'restored-manifest-binding')
    m=verify(destination/'manifest.json')
    if value.get('schema')!=SCHEMA:publication_check(destination/'manifest.json',value)
    inputs=[]
    for row in m['sources']:
        item=dict(path=str(destination/row['key']),role=row['role'],identity={k:v for k,v in m['identity'].items() if k in ('doi','pmid','version') and v},basis='Verified modern archive source binding.',filename=row['filename'],page_count=row.get('pages'),retained_text=[dict(page=p['page'],path=str(destination/p['key']),sha256=p['sha256']) for p in row.get('text',[])])
        if row.get('selected_pages'):item['pages']=row['selected_pages']
        inputs.append(item)
    return dict(identity=m['identity'],inputs=inputs,history=dict(receipt=value,manifest_sha256=w.sha(destination/'manifest.json'),provenance=pa.load(destination/'provenance.json')))
