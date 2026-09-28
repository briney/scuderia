"""Historical article verification and restoration. Never execute archived code."""
from . import portable_articles as pa, final_products

def verify(manifest):
    value, _ = pa.verify_local(manifest)
    pa.verify_source(manifest)
    if pa.is_final_manifest(value):
        final_products.verify(manifest)
    return value

def restore(receipt, destination, *, transport=None):
    import os
    from pathlib import Path
    import tempfile
    from .article_runtime import outside_instance
    destination=outside_instance(destination)
    pa.require(not destination.exists(), 'destination-must-be-new')
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.restore-',dir=destination.parent) as tmp:
        staged=Path(tmp)/'package'
        result=_restore(receipt,staged,transport=transport)
        # Historical maps contain absolute roots. Rebind before atomic promotion.
        mapping=pa.load(staged/'local-map.json')
        for row in mapping['sources'].values():
            pa.require(row['root']==str(staged),'restored-map-outside-package')
            row['root']=str(destination)
        (staged/'local-map.json').unlink()
        pa.save(staged/'local-map.json',mapping)
        result['destination']=str(destination)
        (staged/'RESTORE-RECEIPT.json').unlink()
        pa.save(staged/'RESTORE-RECEIPT.json',result)
        os.rename(staged,destination)
    verify(destination/'manifest.json')
    return result


def _restore(receipt, destination, *, transport=None):
    value = pa.load(receipt)
    if value.get('schema', '').startswith('portable-article-manifest-'):
        result = pa.restore(receipt, destination)
    else:
        publication = value.get('publication', value)
        pa.require(transport is not None, 'trusted-transport-required')
        pa.require(all(publication[k] == transport[k] for k in ('remote','bucket','prefix')), 'archive-transport-mismatch')
        result = pa.restore_remote(publication['manifest_key'], publication['manifest_sha256'], destination,
            article_key=publication['article_key'], **transport)
    verify(destination/'manifest.json')
    return result
