#!/usr/bin/env python3
"""Offline regression tests for fetch_fulltext.py retained behavior.

Run with a Python >= 3.10 interpreter:

    python3 test_fetch_fulltext.py

Covers the helpers that survived the 2026-09-16 removal of the
article-package adapter: the PMC XML -> text converter (including the
<preformat> pre-2000 body fallback), the Wayback HTML stripper, and the
fail-fast rejection of the removed package-mode flags BEFORE any network
access. No network is used; retrieval helpers that need the network are
monkeypatched to raise if touched.
"""

import importlib.util
import io
import json
import sys
import tempfile
from unittest.mock import patch
import unittest
import urllib.request
from contextlib import redirect_stderr
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "fetch_fulltext.py"


def load_module():
    spec = importlib.util.spec_from_file_location("fetch_fulltext_u", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class NetworkTouched(AssertionError):
    pass


import contextlib


@contextlib.contextmanager
def forbid_network():
    """Fail the test if the script attempts any network access."""

    attempted = []

    def boom(*args, **kwargs):
        attempted.append(True)
        raise NetworkTouched("network access attempted during offline test")

    orig = (urllib.request.urlopen, urllib.request.Request)
    urllib.request.urlopen = boom
    urllib.request.Request = boom
    try:
        yield
    finally:
        urllib.request.urlopen, urllib.request.Request = orig
        if attempted:
            raise NetworkTouched("network access was attempted, even if caught")


class TestPmcXmlToText(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def test_body_paragraphs_and_sections(self):
        xml = (
            "<article><body>"
            "<sec><title>Results</title><p>First finding.</p></sec>"
            "<sec><title>Methods</title><p>How.</p></sec>"
            "</body></article>"
        )
        text = self.mod.pmc_xml_to_text(xml)
        self.assertIn("## Results", text)
        self.assertIn("First finding.", text)
        self.assertIn("## Methods", text)

    def test_preformat_legacy_body(self):
        xml = (
            "<article><body><preformat preformat-type='pmc-pdf-text'>"
            "Whole body text in a preformat block."
            "</preformat></body></article>"
        )
        text = self.mod.pmc_xml_to_text(xml)
        self.assertIn("Whole body text in a preformat block.", text)

    def test_figure_and_table_captions(self):
        xml = (
            "<article><body>"
            "<fig><label>Figure 1</label><caption>A caption.</caption></fig>"
            "<table-wrap><label>Table 1</label><caption>A table.</caption></table-wrap>"
            "</body></article>"
        )
        text = self.mod.pmc_xml_to_text(xml)
        self.assertIn("[Figure 1] A caption.", text)
        self.assertIn("[Table 1] A table.", text)

    def test_no_body_returns_empty(self):
        self.assertEqual(self.mod.pmc_xml_to_text("<article><front/></article>"), "")
        self.assertEqual(self.mod.pmc_xml_to_text("not xml at all"), "")


class TestStripHtml(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def test_drops_script_style_and_tags(self):
        html = (
            "<html><head><style>.x{}</style></head><body>"
            "<script>evil()</script>"
            "<h1>Title</h1><p>Para &amp; entity</p>"
            "</body></html>"
        )
        text = self.mod.strip_html(html)
        self.assertNotIn("evil()", text)
        self.assertNotIn(".x{}", text)
        self.assertIn("Title", text)
        self.assertIn("Para & entity", text)


class TestRemovedFlagsFailFast(unittest.TestCase):
    """The article-package routes were removed 2026-09-16: the old flags
    must fail with exit code 2 before any network access."""

    def setUp(self):
        self.mod = load_module()

    def _run_main(self, argv):
        argv_save = sys.argv
        sys.argv = ["fetch_fulltext.py"] + argv
        stderr = io.StringIO()
        try:
            with redirect_stderr(stderr), forbid_network():
                with self.assertRaises(SystemExit) as raised:
                    self.mod.main()
                rc = raised.exception.code
        finally:
            sys.argv = argv_save
        return rc, stderr.getvalue()

    def test_package_mode_rejected(self):
        rc, err = self._run_main(["--doi", "10.1/x", "--out", "/tmp/ff_t",
                                  "--package-mode"])
        self.assertEqual(rc, 2)
        self.assertIn("--package-mode", err)
        self.assertIn("unrecognized arguments", err)

    def test_state_dir_rejected(self):
        rc, err = self._run_main(["--doi", "10.1/x", "--out", "/tmp/ff_t",
                                  "--state-dir", "/tmp/state"])
        self.assertEqual(rc, 2)
        self.assertIn("--state-dir", err)

    def test_resume_rejected(self):
        rc, _ = self._run_main(["--doi", "10.1/x", "--out", "/tmp/ff_t",
                                "--resume", "pkg-1"])
        self.assertEqual(rc, 2)

    def test_legacy_fulltext_rejected(self):
        rc, err = self._run_main(["--doi", "10.1/x", "--out", "/tmp/ff_t",
                                  "--legacy-fulltext"])
        self.assertEqual(rc, 2)
        self.assertIn("--legacy-fulltext", err)

    def test_default_ladder_writes_pmc_body(self):
        body = "Source paragraph with exact lexical value 007. " * 60
        xml = "<article><body><p>" + body + "</p></body></article>"
        gate = json.dumps({"resultList": {"result": [
            {"pmcid": "PMC12345", "inPMC": "Y", "isOpenAccess": "Y"}]}})
        with tempfile.TemporaryDirectory() as directory:
            prefix = str(Path(directory) / "paper")
            stdout = io.StringIO()
            with patch.object(sys, "argv", ["fetch_fulltext.py", "--pmid", "12345", "--out", prefix]), \
                    patch.object(self.mod, "fetch", side_effect=[gate, xml]) as fetch, \
                    contextlib.redirect_stdout(stdout), forbid_network():
                self.assertIsNone(self.mod.main())
            result = json.loads(stdout.getvalue())
            self.assertEqual(result["provenance"], "pmc-xml")
            self.assertEqual(Path(result["text_file"]).read_text(), body.strip())
            self.assertEqual(result["text_file"], prefix + ".txt")
            self.assertEqual(fetch.call_count, 2)
            self.assertIn("europepmc", fetch.call_args_list[0].args[0])
            self.assertIn("efetch.fcgi", fetch.call_args_list[1].args[0])

    def test_help_still_works(self):
        """--help exits 0 via argparse and no longer lists removed flags."""
        argv_save = sys.argv
        sys.argv = ["fetch_fulltext.py", "--help"]
        stdout = io.StringIO()
        try:
            with redirect_stderr(io.StringIO()):
                buf, sys.stdout = sys.stdout, stdout
                try:
                    with self.assertRaises(SystemExit) as cm:
                        self.mod.main()
                finally:
                    sys.stdout = buf
        finally:
            sys.argv = argv_save
        self.assertEqual(cm.exception.code, 0)
        for flag in ("--package-mode", "--state-dir", "--resume",
                     "--legacy-fulltext"):
            self.assertNotIn(flag, stdout.getvalue())


class TestAcquisitionEvidence(unittest.TestCase):
    """Synthetic HTTP responses only; no socket is opened."""
    def setUp(self):
        self.mod = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def response(self, code, raw, url='https://example.invalid/article'):
        import urllib.response
        from email.message import Message
        headers = Message(); headers['Content-Type'] = 'text/plain'
        response = urllib.response.addinfourl(io.BytesIO(raw), headers, url, code)
        response.msg = 'Synthetic transport fixture'
        return response

    def test_retry_preserves_failed_body_before_success(self):
        self.mod.EVIDENCE = self.mod.AcquisitionEvidence(self.base/'evidence')
        import urllib.error
        responses = [self.response(503,b'SYNTHETIC unavailable'),self.response(200,b'SYNTHETIC success')]
        with patch('urllib.request.HTTPHandler.http_open', side_effect=responses), \
                patch.object(self.mod.time,'sleep'), forbid_socket():
            result = self.mod.fetch('http://example.invalid/article')
        self.assertEqual(result,'SYNTHETIC success')
        records = sorted((self.base/'evidence').glob('attempt-*/response-*/response.json'))
        self.assertEqual([json.loads(p.read_text())['status'] for p in records],[503,200])
        self.assertEqual((records[0].parent/'body.bin').read_bytes(),b'SYNTHETIC unavailable')
        self.assertEqual(len(list((self.base/'evidence').glob('attempt-*/error.json'))),1)

    def test_partial_response_and_completion_log_failure(self):
        import http.client
        self.mod.EVIDENCE = self.mod.AcquisitionEvidence(self.base/'evidence')
        response=self.response(200,b'')
        response.read=lambda: (_ for _ in ()).throw(http.client.IncompleteRead(b'SYNTHETIC partial',100))
        with patch('urllib.request.HTTPHandler.http_open',return_value=response),forbid_socket():
            self.assertIsNone(self.mod.fetch_quiet('http://example.invalid/article',retries=0))
        partial=next((self.base/'evidence').glob('attempt-*/response-*/partial-body.bin'))
        self.assertEqual(partial.read_bytes(),b'SYNTHETIC partial')
        self.assertFalse(json.loads((partial.parent/'partial.json').read_text())['complete'])
        real=self.mod.save
        def fail_completion(path,value):
            if Path(path).name == 'complete.json': raise OSError('SYNTHETIC disk failure')
            return real(path,value)
        with patch.object(self.mod,'save',side_effect=fail_completion), \
                patch('urllib.request.HTTPHandler.http_open',return_value=self.response(200,b'SYNTHETIC success')),forbid_socket():
            with self.assertRaises(self.mod.EvidenceError):
                self.mod.fetch_quiet('http://example.invalid/article')

    def test_direct_doi_head_and_transport_failure(self):
        import urllib.error
        self.mod.EVIDENCE = self.mod.AcquisitionEvidence(self.base/'evidence')
        with patch('urllib.request.HTTPSHandler.https_open',side_effect=urllib.error.URLError('SYNTHETIC failure')), forbid_socket():
            self.assertIsNone(self.mod.resolve_doi('10.9999/fixture'))
        error = next((self.base/'evidence').glob('attempt-*/error.json'))
        self.assertEqual(json.loads(error.read_text())['error_type'],'URLError')
        self.assertEqual(json.loads((error.parent/'request.json').read_text())['method'],'HEAD')

    def test_redirect_responses_are_individual_evidence(self):
        first=self.response(302,b'SYNTHETIC redirect','http://example.invalid/start')
        first.headers['Location']='http://example.invalid/finish'
        self.mod.EVIDENCE = self.mod.AcquisitionEvidence(self.base/'evidence')
        with patch('urllib.request.HTTPHandler.http_open',side_effect=[first,self.response(200,b'SYNTHETIC final','http://example.invalid/finish')]), forbid_socket():
            self.assertEqual(self.mod.fetch('http://example.invalid/start'),'SYNTHETIC final')
        records=list((self.base/'evidence').glob('attempt-*/response-*/response.json'))
        self.assertEqual(len(records),2)

    def test_evidence_failure_cannot_be_swallowed(self):
        self.mod.EVIDENCE = self.mod.AcquisitionEvidence(self.base/'evidence')
        with patch.object(self.mod,'save',side_effect=OSError('SYNTHETIC disk failure')), forbid_socket():
            with self.assertRaises(self.mod.EvidenceError):
                self.mod.fetch_quiet('https://example.invalid/article')

    def test_evidence_cli_new_directory_and_legacy_output(self):
        body=b'<article><body><p>'+b'SYNTHETIC source body. '*120+b'</p></body></article>'
        evidence=self.base/'evidence'; prefix=evidence/'derived'/'paper'
        argv=['fetch_fulltext.py','--pmcid','PMC123','--out',str(prefix),'--evidence-dir',str(evidence)]
        out=io.StringIO()
        with patch.object(sys,'argv',argv), patch('urllib.request.HTTPSHandler.https_open',return_value=self.response(200,body)), \
                contextlib.redirect_stdout(out),forbid_socket():
            self.mod.main()
        self.assertEqual(json.loads(out.getvalue())['provenance'],'pmc-xml')
        self.assertEqual(next(evidence.glob('attempt-*/response-*/body.bin')).read_bytes(),body)
        with patch.object(sys,'argv',argv),forbid_socket():
            with self.assertRaises((ValueError,OSError,SystemExit)):
                self.mod.main()

    def test_credentials_rejected_before_request(self):
        self.mod.EVIDENCE = self.mod.AcquisitionEvidence(self.base/'evidence')
        with forbid_socket(), self.assertRaises(self.mod.EvidenceError):
            self.mod.fetch_quiet('https://example.invalid/a?api_key=do-not-retain')
        self.assertFalse(list((self.base/'evidence').rglob('*')))


@contextlib.contextmanager
def forbid_socket():
    import socket
    with patch.object(socket,'socket',side_effect=AssertionError('offline socket forbidden')):
        yield


if __name__ == "__main__":
    unittest.main(verbosity=2)
