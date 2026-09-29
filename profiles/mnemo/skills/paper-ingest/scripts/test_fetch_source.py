"""Direct source retrieval: preserved bytes, visible failures, no overwrite."""
import io
import http.client
import json
import tempfile
import unittest
import urllib.response
from contextlib import redirect_stdout
from email.message import Message
from pathlib import Path
from unittest.mock import patch

import fetch_source


class FetchSourceTests(unittest.TestCase):
    def test_cli_retains_bytes_and_exposes_http_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            for status, raw, name in ((200, b'{"collection": []}', 'details.json'),
                                      (200, b'%PDF-1.7\nsynthetic', 'manuscript.pdf'),
                                      (403, b'Access denied', 'blocked.pdf')):
                directory = root / name
                response = urllib.response.addinfourl(io.BytesIO(raw), Message(),
                                                       'http://example.org/source', status)
                response.msg = 'Synthetic'
                output = io.StringIO()
                with patch('urllib.request.HTTPHandler.http_open', return_value=response) as request, redirect_stdout(output):
                    code = fetch_source.main(['--url', 'http://example.org/source',
                                              '--evidence-dir', str(directory), '--filename', name])
                self.assertEqual(request.call_count, 1)
                self.assertEqual(code, 0 if status == 200 else 2)
                result = json.loads(output.getvalue())
                self.assertEqual(next(directory.glob('attempt-*/response-*/body.bin')).read_bytes(), raw)
                if status == 200:
                    self.assertEqual(Path(result['file']).read_bytes(), raw)
                    self.assertEqual(result['bytes'], len(raw))
                else:
                    self.assertNotIn('file', result)
                    self.assertFalse((directory/'derived'/name).exists())

    def test_partial_download_is_failure_with_retained_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp).resolve()/'partial'
            response = urllib.response.addinfourl(io.BytesIO(b''), Message(),
                                                   'http://example.org/source', 200)
            response.msg = 'Synthetic'
            response.read = lambda: (_ for _ in ()).throw(http.client.IncompleteRead(b'partial', 100))
            output = io.StringIO()
            with patch('urllib.request.HTTPHandler.http_open', return_value=response), redirect_stdout(output):
                code = fetch_source.main(['--url', 'http://example.org/source',
                                          '--evidence-dir', str(directory), '--filename', 'source.pdf'])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(output.getvalue())['error'], 'IncompleteRead')
            self.assertEqual(next(directory.glob('attempt-*/response-*/partial-body.bin')).read_bytes(), b'partial')
            self.assertFalse((directory/'derived').exists())

    def test_rejects_unsafe_input_and_reuse_before_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            vault = root/'vault'; vault.mkdir(); (vault/'instance.yaml').write_text('name: test')
            for url, directory, filename in (
                ('file:///etc/passwd', root/'file', 'source.txt'),
                ('https://example.org/?api_key=secret', root/'secret', 'source.txt'),
                ('https://example.org', root/'escape', '../escape'),
                ('https://example.org', vault/'sources', 'source.txt'),
                ('https://example.org', root, 'source.txt'),
            ):
                with patch('urllib.request.build_opener', side_effect=AssertionError('network touched')), redirect_stdout(io.StringIO()):
                    self.assertEqual(fetch_source.main(['--url', url, '--evidence-dir', str(directory), '--filename', filename]), 2)
            self.assertFalse((root/'escape').exists())


if __name__ == '__main__':
    unittest.main()

class OriginalEvidence(unittest.TestCase):
    def test_empty_directory_and_original_xml_inventory(self):
        from fetch_fulltext import AcquisitionEvidence
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()/'evidence'; root.mkdir()
            try:evidence=AcquisitionEvidence(root)
            except FileExistsError:self.fail('empty evidence directory rejected')
            raw=b'<article><front><article-id pub-id-type="pmc">PMC123</article-id></front><body><p>Full manuscript</p><supplementary-material xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="mmc1.pdf"/></body></article>'
            response=urllib.response.addinfourl(io.BytesIO(raw),Message(),'http://example.org/article.xml',200); response.msg='OK'
            with patch('urllib.request.HTTPHandler.http_open',return_value=response):evidence.open(urllib.request.Request('http://example.org/article.xml')).close()
            summary=evidence.source_inventory()
            self.assertEqual(Path(summary['source_candidates'][0]['path']).read_bytes(),raw)
            self.assertEqual(summary['attachments'][0]['url'],'https://pmc.ncbi.nlm.nih.gov/articles/PMC123/bin/mmc1.pdf')
            with self.assertRaises(ValueError):AcquisitionEvidence(root)

class SupplementBudget(unittest.TestCase):
    def test_budget_limits_time_and_observed_urls(self):
        with tempfile.TemporaryDirectory() as tmp:
            state=Path(tmp).resolve()/'budget.json'
            self.assertTrue(hasattr(fetch_source,'reserve_attachment'))
            with patch('time.time',return_value=100):self.assertEqual(fetch_source.reserve_attachment(state,'S1','https://example.org/1'),120)
            with patch('time.time',return_value=110):self.assertEqual(fetch_source.reserve_attachment(state,'S1','https://example.org/2'),110)
            with self.assertRaisesRegex(ValueError,'attachment-attempt'):
                fetch_source.reserve_attachment(state,'S1','https://example.org/3')
            with patch('time.time',return_value=221),self.assertRaisesRegex(ValueError,'budget'):
                fetch_source.reserve_attachment(state,'S2','https://example.org/4')
