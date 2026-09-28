"""External article packages and historical source reuse."""
from pathlib import Path
from article_archive_compat import reader, portable_articles as pa
from . import workflow as w

SCHEMA='manuscript-article-package-v1'


def open_sources(receipt,destination,*,transport=None):
    value=pa.load(receipt)
    if value.get('schema')==SCHEMA or value.get('schema')=='manuscript-publication-v1':
        return restore_sources(receipt,destination,transport=transport)
    if not destination.exists(): reader.restore(receipt,destination,transport=transport)
    manifest=destination/'manifest.json'; m=reader.verify(manifest); _, paths=pa.verify_local(manifest)
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
