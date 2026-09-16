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


if __name__ == "__main__":
    unittest.main(verbosity=2)
