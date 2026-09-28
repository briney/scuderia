"""Historical article verification and restoration. Never execute archived code."""
from . import portable_articles as pa, final_products

def verify(manifest):
    value, _ = pa.verify_local(manifest)
    pa.verify_source(manifest)
    if pa.is_final_manifest(value):
        final_products.verify(manifest)
    return value

def restore(receipt, destination, *, transport=None):
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
