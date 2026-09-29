import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

class CachedMetadata(unittest.TestCase):
    def test_cache_reuses_raw_record_but_rejects_wrong_url_binding(self):
        import metadata_http as m
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp).resolve()
            with patch('urllib.request.urlopen',return_value=io.BytesIO(b'{"title":"Example"}')):
                first=m.fetch_json('https://example.org/record',cache=cache)
            with patch('urllib.request.urlopen',side_effect=AssertionError('repeat request')):
                self.assertEqual(m.fetch_json('https://example.org/record',cache=cache),first)
                path=next(cache.glob('*.json')); row=json.loads(path.read_text()); row['url']='https://other.org'; path.write_text(json.dumps(row))
                with self.assertRaisesRegex(ValueError,'cache-binding'):m.fetch_json('https://example.org/record',cache=cache)
    def test_long_retry_after_releases_request_without_sleep(self):
        import metadata_http as m
        error=urllib.error.HTTPError('https://example.org',429,'busy',{'Retry-After':'300'},None)
        with patch('urllib.request.urlopen',side_effect=error),patch('time.sleep',side_effect=AssertionError('blocking sleep')):
            with self.assertRaises(m.MetadataUnavailable):m.fetch_json('https://example.org')

    def test_acquisition_batch_uses_equivalent_pmid_evidence_on_outage(self):
        import validate_identifiers as v
        def fetch(url,*args,**kwargs):
            if 'eutils' in url:raise urllib.error.HTTPError(url,429,'busy',{},None)
            return {'resultList':{'result':[{'id':'123','source':'MED','title':'Example','pubYear':'2026','authorList':{'author':[{'fullName':'Author A'}]}}]}}
        with patch.object(v,'fetch_json',side_effect=fetch):record=v.pubmed_esummary_batch(['123'])['123']
        self.assertEqual(record['title'],'Example'); self.assertEqual(record['n_authors'],1)
