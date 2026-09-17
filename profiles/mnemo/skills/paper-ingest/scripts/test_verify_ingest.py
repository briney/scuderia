#!/usr/bin/env python3
"""Offline regression tests for verify_ingest.py (Phase 10 verification).

Run with a Python >= 3.9 interpreter:

    python3 test_verify_ingest.py

Covers the verifier's contracts, developed test-first:

- the filled-page contract (--require-filled): kind/slug/title/venue/
  year/status checks, doi key presence + bare-DOI shape (explicit null
  allowed), authors shape + distinctness ([] allowed), cited_by shape,
  needs-ingest exactly false + no stub tag, fulltext_source presence,
  abstract-only => needs-enrichment exactly true, and the required
  nonempty level-two body sections (fenced example headings do not
  count);
- page-only intermediate mode (--page-only): unresolved well-shaped
  author refs DEFERRED TO PARENT, needs-ingest exactly True with
  --require-filled (PAGE_READY), other graph errors NOT waived, output
  labeled intermediate;
- canonical-identity repairs: PubMed title/year comparison for no-DOI
  (PMID-only) papers, missing-DOI failure when PubMed supplies a DOI,
  collective-only authorship, empty authors vs named canonical
  individuals, conservative DataCite creator counting, and
  no-identifier => canonical UNVERIFIED;
- external http(s) links skipped from filesystem existence checks;
- malformed list/ledger values reported as FAIL, never a crash;
- offline pass says identity checks were skipped, never an
  unqualified "All checks OK".

No network is used: canonical tests mock the source boundary
(fetch_json) with clearly synthetic fixtures; CLI tests run main()
against real files in TemporaryDirectory brains under a
network-forbidden guard, always with --offline.
"""

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
import urllib.request
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import yaml

SCRIPT = Path(__file__).resolve().parent / "verify_ingest.py"
PMID = 99999999
PAGE_TITLE = "Synthetic interleukin signaling in resident memory cells"


def load_module():
    spec = importlib.util.spec_from_file_location("verify_ingest_u", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class NetworkTouched(AssertionError):
    pass


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


def run_cli(mod, argv):
    """Run main() with argv; return (exit_code, stdout, stderr)."""
    argv_save = sys.argv
    sys.argv = ["verify_ingest.py"] + list(argv)
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err), forbid_network():
            try:
                mod.main()
                rc = 0
            except SystemExit as e:
                rc = e.code if isinstance(e.code, int) else 0
    finally:
        sys.argv = argv_save
    return rc, out.getvalue(), err.getvalue()


# --------------------------------------------------------------- fixtures

BODY = """## Abstract

Synthetic abstract sentence.

## Context

Synthetic context sentence.

## Approach

Synthetic approach sentence.

## Findings

Synthetic findings sentence.

## Limitations

Synthetic limitations sentence.

## Analysis

Synthetic analysis sentence.

## Citation

Synthetic citation sentence.

## Ingest log

Synthetic ingest log sentence.
"""

LEDGER_OK = """entries:
  - slug: carol-fixtured
    name: Carol Fixtured
    orcid: null
    affiliations: []
    citations: []
"""

PERSON_PAGE = """---
kind: person
slug: {slug}
title: "{name}"
importance: 0.3
links: []
tags: []
---

Profile placeholder.
"""


def paper_fm(**over):
    """Frontmatter for a well-filled synthetic paper page."""
    fm = {
        "kind": "paper",
        "slug": "fixture-paper",
        "title": PAGE_TITLE,
        "status": "published",
        "doi": "10.9999/synthetic.0001",
        "pmid": PMID,
        "authors": ["people/alice-fixtured", "people/bob-fixtured"],
        "venue": "Synthetic Journal of Fixtures",
        "year": 2026,
        "importance": 0.5,
        "links": ["https://doi.org/10.9999/synthetic.0001"],
        "tags": [],
        "needs-ingest": False,
        "fulltext_source": "pmc-xml",
        "cited_by": [],
    }
    fm.update(over)
    return fm


def make_brain(root, ledger=LEDGER_OK,
               people=("alice-fixtured", "bob-fixtured")):
    brain = Path(root)
    (brain / "papers").mkdir(parents=True, exist_ok=True)
    (brain / "people").mkdir(parents=True, exist_ok=True)
    for slug in people:
        (brain / "people" / f"{slug}.md").write_text(
            PERSON_PAGE.format(slug=slug,
                               name=slug.replace("-", " ").title()))
    if ledger is not None:
        (brain / "people" / "_ledger.yaml").write_text(ledger)
    return str(brain)


def write_paper(brain, fm=None, body=BODY, name="fixture-paper"):
    fm = paper_fm() if fm is None else fm
    text = "---\n" + yaml.safe_dump(fm, sort_keys=False) + "---\n" + body
    path = Path(brain) / "papers" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return str(path)


# ------------------------------------------- canonical source-boundary mocks

def openalex_json(title, year=2026, n_authors=2, retracted=False):
    return {
        "title": title,
        "publication_year": year,
        "authorships": [{} for _ in range(n_authors)],
        "is_retracted": retracted,
    }


def datacite_json(title, year=2026, creators=None):
    return {"data": {"attributes": {
        "titles": [{"title": title}],
        "publicationYear": year,
        "creators": [] if creators is None else creators,
    }}}


def pubmed_json(title, year="2026", doi=None, individuals=2, collectives=0,
                pmid=PMID, error=None):
    if error:
        return {"result": {str(pmid): {"error": error}}}
    authors = [{"name": f"Author {i + 1}", "authtype": "Author"}
               for i in range(individuals)]
    authors += [{"name": f"Synthetic Trial Group {i + 1}",
                 "authtype": "CollectiveName"} for i in range(collectives)]
    articleids = [{"idtype": "doi", "value": doi}] if doi else []
    return {"result": {str(pmid): {
        "title": title,
        "pubdate": f"{year} Jun",
        "authors": authors,
        "articleids": articleids,
        "pubtype": ["Journal Article"],
    }}}


def patch_sources(mod, openalex=None, datacite=None, crossref=None,
                  pubmed=None):
    """Route fetch_json by URL to synthetic source fixtures."""

    def fake_fetch(url, *args, **kwargs):
        if "api.openalex.org" in url:
            if openalex is None:
                raise AssertionError("unexpected OpenAlex fetch: " + url)
            return openalex
        if "api.datacite.org" in url:
            if datacite is None:
                raise AssertionError("unexpected DataCite fetch: " + url)
            return datacite
        if "api.crossref.org" in url:
            if crossref is None:
                raise AssertionError("unexpected Crossref fetch: " + url)
            return crossref
        if "eutils" in url:
            if pubmed is None:
                raise AssertionError("unexpected PubMed fetch: " + url)
            return pubmed
        raise AssertionError("unexpected fetch: " + url)

    return patch.object(mod, "fetch_json", side_effect=fake_fetch)


# ----------------------------------------------------------------- CLI base

class CliCase(unittest.TestCase):
    """Shared plumbing: fresh module + temp brain per test, offline CLI."""

    def setUp(self):
        self.mod = load_module()
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.brain = make_brain(self._tmp.name)

    def set_ledger(self, text):
        (Path(self.brain) / "people" / "_ledger.yaml").write_text(text)

    def verify(self, *flags, fm=None, body=BODY, name="fixture-paper"):
        write_paper(self.brain, fm=fm, body=body, name=name)
        return run_cli(self.mod, [name, "--instance", self.brain,
                                  "--offline", *flags])


class TestRequireFilled(CliCase):
    """--require-filled: the filled-page contract."""

    def test_filled_fixture_passes(self):
        rc, out, err = self.verify("--require-filled")
        self.assertEqual(rc, 0, out)
        self.assertIn("Filled contract: OK", out)
        self.assertIn("SKIPPED (--offline)", out)

    def test_missing_doi_key_fails(self):
        fm = paper_fm()
        del fm["doi"]
        rc, out, _ = self.verify("--require-filled", fm=fm)
        self.assertEqual(rc, 1, out)
        self.assertIn("doi key missing", out)

    def test_empty_doi_fails(self):
        rc, out, _ = self.verify("--require-filled", fm=paper_fm(doi=""))
        self.assertEqual(rc, 1, out)
        self.assertIn("doi is empty", out)

    def test_doi_placeholder_fails(self):
        rc, out, _ = self.verify("--require-filled", fm=paper_fm(doi="n/a"))
        self.assertEqual(rc, 1, out)
        self.assertIn("placeholder", out)

    def test_doi_url_fails(self):
        rc, out, _ = self.verify("--require-filled",
                                  fm=paper_fm(doi="https://doi.org/10.9999/x"))
        self.assertEqual(rc, 1, out)
        self.assertIn("URL", out)

    def test_malformed_doi_fails(self):
        rc, out, _ = self.verify("--require-filled", fm=paper_fm(doi="not-a-doi"))
        self.assertEqual(rc, 1, out)
        self.assertIn("not shaped", out)

    def test_explicit_null_doi_allowed(self):
        rc, out, _ = self.verify("--require-filled", fm=paper_fm(doi=None))
        self.assertEqual(rc, 0, out)
        self.assertIn("Filled contract: OK", out)

    def test_missing_section_fails(self):
        body = BODY.replace(
            "## Findings\n\nSynthetic findings sentence.\n\n", "")
        rc, out, _ = self.verify("--require-filled", body=body)
        self.assertEqual(rc, 1, out)
        self.assertIn("Findings", out)

    def test_empty_section_fails(self):
        body = BODY.replace("Synthetic findings sentence.", "")
        rc, out, _ = self.verify("--require-filled", body=body)
        self.assertEqual(rc, 1, out)
        self.assertIn("Findings", out)

    def test_fenced_fake_heading_not_counted(self):
        body = BODY.replace(
            "## Findings\n\nSynthetic findings sentence.\n\n", "")
        body += ("\n```\nExample page template:\n\n## Findings\n\n"
                 "A heading inside a fenced example must not count.\n```\n")
        rc, out, _ = self.verify("--require-filled", body=body)
        self.assertEqual(rc, 1, out)
        self.assertIn("Findings", out)

    def test_stub_tag_fails(self):
        rc, out, _ = self.verify("--require-filled",
                                  fm=paper_fm(tags=["stub"]))
        self.assertEqual(rc, 1, out)
        self.assertIn("stub", out)

    def test_needs_ingest_true_fails(self):
        rc, out, _ = self.verify("--require-filled",
                                 fm=paper_fm(**{"needs-ingest": True}))
        self.assertEqual(rc, 1, out)
        self.assertIn("needs-ingest", out)

    def test_needs_ingest_absent_fails(self):
        fm = paper_fm()
        del fm["needs-ingest"]
        rc, out, _ = self.verify("--require-filled", fm=fm)
        self.assertEqual(rc, 1, out)
        self.assertIn("needs-ingest", out)

    def test_abstract_only_without_enrichment_fails(self):
        rc, out, _ = self.verify(
            "--require-filled",
            fm=paper_fm(fulltext_source="abstract-only"))
        self.assertEqual(rc, 1, out)
        self.assertIn("abstract-only", out)
        self.assertIn("needs-enrichment", out)

    def test_abstract_only_with_enrichment_passes(self):
        rc, out, _ = self.verify(
            "--require-filled",
            fm=paper_fm(fulltext_source="abstract-only",
                        **{"needs-enrichment": True}))
        self.assertEqual(rc, 0, out)
        self.assertIn("Filled contract: OK", out)

    def test_preprint_enrichment_not_required(self):
        rc, out, _ = self.verify(
            "--require-filled",
            fm=paper_fm(fulltext_source="arxiv-html",
                        **{"needs-enrichment": False}))
        self.assertEqual(rc, 0, out)

    def test_illegal_cited_by_fails(self):
        rc, out, _ = self.verify(
            "--require-filled",
            fm=paper_fm(cited_by=["concepts/fixtured-concept"]))
        self.assertEqual(rc, 1, out)
        self.assertIn("papers/<slug> or grants/<slug>", out)

    def test_duplicate_authors_fails(self):
        rc, out, _ = self.verify(
            "--require-filled",
            fm=paper_fm(authors=["people/alice-fixtured",
                                 "people/alice-fixtured"]))
        self.assertEqual(rc, 1, out)
        self.assertIn("duplicate authors", out)

    def test_malformed_author_shape_fails(self):
        rc, out, _ = self.verify(
            "--require-filled",
            fm=paper_fm(authors=["people/alice-fixtured", "Alice Fixtured"]))
        self.assertEqual(rc, 1, out)
        self.assertIn("people/<slug>", out)

    def test_bare_slug_author_fails_filled_contract(self):
        rc, out, _ = self.verify(
            "--require-filled",
            fm=paper_fm(authors=["alice-fixtured", "bob-fixtured"]))
        self.assertEqual(rc, 1, out)
        self.assertIn("people/<slug>", out)

    def test_empty_authors_structurally_allowed(self):
        rc, out, _ = self.verify("--require-filled", fm=paper_fm(authors=[]))
        self.assertEqual(rc, 0, out)
        self.assertIn("Filled contract: OK", out)

    def test_bad_status_fails(self):
        rc, out, _ = self.verify("--require-filled",
                                 fm=paper_fm(status="in review"))
        self.assertEqual(rc, 1, out)
        self.assertIn("status", out)

    def test_quoted_year_string_passes(self):
        """Regression: valid legacy paper pages can carry quoted digit
        years ('2024') — integer-valued strings are acceptable, not
        defects forcing repair."""
        rc, out, _ = self.verify("--require-filled", fm=paper_fm(year="2024"))
        self.assertEqual(rc, 0, out)
        self.assertIn("Filled contract: OK", out)

    def test_non_numeric_year_fails(self):
        rc, out, _ = self.verify("--require-filled",
                                 fm=paper_fm(year="circa 2024"))
        self.assertEqual(rc, 1, out)
        self.assertIn("year", out)

    def test_bool_year_fails(self):
        rc, out, _ = self.verify("--require-filled", fm=paper_fm(year=True))
        self.assertEqual(rc, 1, out)
        self.assertIn("year", out)

    def test_nondecimal_digit_year_fails_without_crashing(self):
        rc, out, _ = self.verify("--require-filled", fm=paper_fm(year="²"))
        self.assertEqual(rc, 1, out)
        self.assertIn("year", out)

    def test_blank_year_fails(self):
        rc, out, _ = self.verify("--require-filled", fm=paper_fm(year=""))
        self.assertEqual(rc, 1, out)
        self.assertIn("year", out)

    def test_zero_year_fails(self):
        rc, out, _ = self.verify("--require-filled", fm=paper_fm(year=0))
        self.assertEqual(rc, 1, out)
        self.assertIn("year", out)

    def test_blank_title_and_venue_fail(self):
        rc, out, _ = self.verify("--require-filled",
                                 fm=paper_fm(title="  ", venue=""))
        self.assertEqual(rc, 1, out)
        self.assertIn("title", out)
        self.assertIn("venue", out)

    def test_kind_mismatch_fails(self):
        rc, out, _ = self.verify("--require-filled", fm=paper_fm(kind="note"))
        self.assertEqual(rc, 1, out)
        self.assertIn("kind", out)

    def test_slug_mismatch_fails(self):
        rc, out, _ = self.verify("--require-filled",
                                 fm=paper_fm(slug="different-slug"))
        self.assertEqual(rc, 1, out)
        self.assertIn("does not match", out)

    def test_missing_fulltext_source_fails(self):
        fm = paper_fm()
        del fm["fulltext_source"]
        rc, out, _ = self.verify("--require-filled", fm=fm)
        self.assertEqual(rc, 1, out)
        self.assertIn("fulltext_source", out)

    def test_placeholder_fulltext_source_fails(self):
        """Regression: a legacy page carries fulltext_source: none (actual
        missing retrieval) despite a nonempty body — obvious placeholders
        are not retrieval provenance."""
        for bad in ("none", "None", "null", "unknown", "n/a", "tbd", "  "):
            with self.subTest(value=bad):
                rc, out, _ = self.verify(
                    "--require-filled", fm=paper_fm(fulltext_source=bad))
                self.assertEqual(rc, 1, out)
                self.assertIn("fulltext_source", out)
                self.assertIn("placeholder", out)

    def test_real_fulltext_source_label_passes(self):
        """No closed enum: any non-placeholder provenance label passes
        (parent source checks verify labels)."""
        rc, out, _ = self.verify(
            "--require-filled", fm=paper_fm(fulltext_source="exotic-new-route"))
        self.assertEqual(rc, 0, out)

    def test_missing_cited_by_key_passes(self):
        """A filled page with no inbound citations may legitimately omit
        the cited_by key — the contract polices entries, not key presence
        (legacy pages with no citers carry no cited_by)."""
        fm = paper_fm()
        del fm["cited_by"]
        rc, out, _ = self.verify("--require-filled", fm=fm)
        self.assertEqual(rc, 0, out)
        self.assertIn("Filled contract: OK", out)


class TestPageOnly(CliCase):
    """--page-only: intermediate PAGE_READY validation."""

    UNWIRED = ["people/alice-fixtured", "people/carol-unwired"]

    def test_page_only_defers_unresolved_authors(self):
        rc, out, _ = self.verify("--page-only", fm=paper_fm(authors=self.UNWIRED))
        self.assertEqual(rc, 0, out)
        self.assertIn("DEFERRED TO PARENT", out)
        self.assertIn("PAGE_READY", out)
        self.assertNotIn("PASS: All checks OK", out)
        self.assertIn("not a full ingest", out)

    def test_full_mode_rejects_unresolved_authors(self):
        rc, out, _ = self.verify(fm=paper_fm(authors=self.UNWIRED))
        self.assertEqual(rc, 1, out)
        self.assertIn("UNRESOLVED", out)
        self.assertNotIn("DEFERRED TO PARENT", out)

    def test_page_only_require_filled_needs_ingest_true(self):
        rc, out, _ = self.verify(
            "--page-only", "--require-filled",
            fm=paper_fm(authors=self.UNWIRED, **{"needs-ingest": True}))
        self.assertEqual(rc, 0, out)
        self.assertIn("Filled contract: OK", out)
        self.assertIn("PAGE_READY", out)
        self.assertIn("DEFERRED TO PARENT", out)

    def test_page_only_require_filled_needs_ingest_false_fails(self):
        rc, out, _ = self.verify(
            "--page-only", "--require-filled",
            fm=paper_fm(authors=self.UNWIRED, **{"needs-ingest": False}))
        self.assertEqual(rc, 1, out)
        self.assertIn("needs-ingest", out)
        self.assertIn("PAGE_READY", out)

    def test_page_only_require_filled_needs_ingest_absent_fails(self):
        fm = paper_fm(authors=self.UNWIRED)
        del fm["needs-ingest"]
        rc, out, _ = self.verify("--page-only", "--require-filled", fm=fm)
        self.assertEqual(rc, 1, out)
        self.assertIn("needs-ingest", out)

    def test_page_only_filled_body_requires_stub_tag_removed(self):
        rc, out, _ = self.verify(
            "--page-only", "--require-filled",
            fm=paper_fm(authors=self.UNWIRED, tags=["stub"],
                        **{"needs-ingest": True}))
        self.assertEqual(rc, 1, out)
        self.assertIn("stub tag", out)

    def test_page_only_does_not_waive_missing_internal_link(self):
        rc, out, _ = self.verify(
            "--page-only",
            fm=paper_fm(links=["concepts/missing-concept"]))
        self.assertEqual(rc, 1, out)
        self.assertIn("MISSING", out)

    def test_page_only_does_not_waive_malformed_ledger(self):
        self.set_ledger(
            "entries:\n"
            "  - slug: carol-fixtured\n    name: Carol Fixtured\n"
            "  - slug: carol-fixtured\n    name: Carol Again\n")
        rc, out, _ = self.verify("--page-only")
        self.assertEqual(rc, 1, out)
        self.assertIn("DUPLICATE SLUGS", out)

    def test_page_only_malformed_author_not_deferred(self):
        rc, out, _ = self.verify(
            "--page-only",
            fm=paper_fm(authors=["people/alice-fixtured", "Alice Fixtured"]))
        self.assertEqual(rc, 1, out)
        self.assertIn("UNRESOLVED", out)
        self.assertNotIn("DEFERRED TO PARENT", out)


class TestLedgerless(CliCase):
    def test_explicit_ledgerless_page_only_defers_new_people(self):
        (Path(self.brain) / "people" / "_ledger.yaml").unlink()
        rc, out, _ = self.verify(
            "--ledgerless", "--page-only", "--require-filled",
            fm=paper_fm(authors=["people/new-person"],
                        **{"needs-ingest": True}))
        self.assertEqual(rc, 0, out)
        self.assertIn("declared ledgerless", out)
        self.assertIn("DEFERRED TO PARENT", out)

    def test_ledgerless_full_mode_requires_person_pages(self):
        (Path(self.brain) / "people" / "_ledger.yaml").unlink()
        rc, out, _ = self.verify(
            "--ledgerless", "--require-filled",
            fm=paper_fm(authors=["people/new-person"]))
        self.assertEqual(rc, 1, out)
        self.assertIn("UNRESOLVED", out)

    def test_ledgerless_cannot_hide_an_existing_ledger(self):
        rc, out, _ = self.verify("--ledgerless", "--page-only")
        self.assertEqual(rc, 1, out)
        self.assertIn("ledger exists", out)

    def test_missing_ledger_fails_without_explicit_topology(self):
        (Path(self.brain) / "people" / "_ledger.yaml").unlink()
        rc, out, _ = self.verify("--page-only")
        self.assertEqual(rc, 1, out)
        self.assertIn("Ledger: FAIL", out)


class TestGraphDefaults(CliCase):
    """Default invocation compatibility + guards + external URLs."""

    def test_no_identifier_failure_is_counted_once(self):
        write_paper(self.brain, fm=paper_fm(doi=None, pmid=None, authors=[]))
        rc, out, _ = run_cli(self.mod, ["fixture-paper", "--instance", self.brain])
        self.assertEqual(rc, 1, out)
        self.assertIn("FAIL: 1 problem(s) found", out)

    def test_default_offline_pass_is_qualified(self):
        rc, out, _ = self.verify()
        self.assertEqual(rc, 0, out)
        self.assertIn("Canonical identity: SKIPPED", out)
        self.assertIn("SKIPPED (--offline)", out)
        self.assertNotIn("PASS: All checks OK", out)
        self.assertNotIn("Filled contract", out)

    def test_default_mode_ignores_filled_contract_fields(self):
        rc, out, _ = self.verify(
            fm=paper_fm(**{"needs-ingest": True}, tags=["stub"]))
        self.assertEqual(rc, 0, out)
        self.assertNotIn("Filled contract", out)

    def test_external_url_skipped_not_missing(self):
        rc, out, _ = self.verify(
            fm=paper_fm(links=["https://doi.org/10.9999/synthetic.0001"]))
        self.assertEqual(rc, 0, out)
        self.assertNotIn("MISSING", out)
        self.assertIn("external URL", out)

    def test_external_cited_by_is_not_waived(self):
        rc, out, _ = self.verify(
            fm=paper_fm(cited_by=["https://example.org/a-citing-paper"]))
        self.assertEqual(rc, 1, out)
        self.assertIn("cited_by", out)

    def test_internal_missing_link_fails(self):
        rc, out, _ = self.verify(
            fm=paper_fm(links=["concepts/missing-concept"]))
        self.assertEqual(rc, 1, out)
        self.assertIn("MISSING", out)

    def test_mixed_links_external_labeled_internal_missing(self):
        rc, out, _ = self.verify(
            fm=paper_fm(links=["concepts/missing-concept",
                               "https://doi.org/10.9999/x"]))
        self.assertEqual(rc, 1, out)
        self.assertIn("MISSING", out)
        self.assertIn("external URL", out)

    def test_malformed_ledger_slug_fails_not_crashes(self):
        self.set_ledger(
            "entries:\n"
            "  - slug: alice-fixtured\n    name: Alice Fixtured\n"
            "  - name: Malformed Entry\n    slug:\n"
            "      nested: true\n")
        rc, out, err = self.verify()
        self.assertEqual(rc, 1, out)
        self.assertIn("Ledger: FAIL", out)
        self.assertNotIn("Traceback", err)

    def test_nonstring_ledger_entry_fails(self):
        self.set_ledger("entries:\n  - alice-fixtured\n")
        rc, out, _ = self.verify()
        self.assertEqual(rc, 1, out)
        self.assertIn("Ledger: FAIL", out)

    def test_malformed_ledger_container_fails_not_crashes(self):
        for value in (7, "not-a-list", {}, None):
            with self.subTest(value=value):
                self.set_ledger(yaml.safe_dump({"entries": value}))
                rc, out, err = self.verify()
                self.assertEqual(rc, 1, out)
                self.assertIn("Ledger: FAIL", out)
                self.assertNotIn("Traceback", err)

    def test_authors_not_a_list_fails(self):
        rc, out, _ = self.verify(fm=paper_fm(authors="people/alice-fixtured"))
        self.assertEqual(rc, 1, out)
        self.assertIn("not a list", out)

    def test_links_not_a_list_fails(self):
        rc, out, _ = self.verify(fm=paper_fm(links="papers/fixture-paper"))
        self.assertEqual(rc, 1, out)
        self.assertIn("not a list", out)


class TestCanonicalChecks(unittest.TestCase):
    """canonical_checks against mocked canonical sources."""

    def setUp(self):
        self.mod = load_module()

    def canonical(self, fm, **sources):
        with patch_sources(self.mod, **sources):
            return self.mod.canonical_checks(fm)

    @staticmethod
    def fails(findings):
        return [m for lvl, m in findings if lvl == "FAIL"]

    def test_doi_resolves_ok(self):
        findings, unverified = self.canonical(
            paper_fm(pmid=None), openalex=openalex_json(PAGE_TITLE))
        self.assertEqual(self.fails(findings), [])
        self.assertFalse(unverified)
        self.assertTrue(any("doi resolves" in m for lvl, m in findings
                            if lvl == "OK"))

    def test_doi_wrong_paper_fails(self):
        findings, _ = self.canonical(
            paper_fm(),
            openalex=openalex_json("Zebra migration patterns across savanna"))
        self.assertTrue(any("different paper" in m
                            for m in self.fails(findings)))

    def test_pmid_only_no_doi_paper_ok(self):
        findings, unverified = self.canonical(
            paper_fm(doi=None), pubmed=pubmed_json(PAGE_TITLE, individuals=2))
        self.assertEqual(self.fails(findings), [])
        self.assertFalse(unverified)
        self.assertTrue(any("no doi" in m for lvl, m in findings
                            if lvl == "OK"))

    def test_pmid_only_wrong_title_fails(self):
        findings, _ = self.canonical(
            paper_fm(doi=None),
            pubmed=pubmed_json("Zebra migration patterns across savanna"))
        self.assertTrue(any("different paper" in m
                            for m in self.fails(findings)))

    def test_pmid_only_year_mismatch_fails(self):
        findings, _ = self.canonical(
            paper_fm(doi=None), pubmed=pubmed_json(PAGE_TITLE, year="1999"))
        self.assertTrue(any("vs PubMed" in m for m in self.fails(findings)))

    def test_wrong_pmid_without_doi_fails_even_when_page_doi_matches(self):
        findings, _ = self.canonical(
            paper_fm(), openalex=openalex_json(PAGE_TITLE),
            pubmed=pubmed_json("Zebra migration patterns across savanna"))
        self.assertTrue(any("different paper" in m
                            for m in self.fails(findings)))

    def test_pubmed_supplies_doi_page_lacks_fails(self):
        findings, _ = self.canonical(
            paper_fm(doi=None),
            pubmed=pubmed_json(PAGE_TITLE, doi="10.9999/pubmed-has-it"))
        self.assertTrue(any("supplies doi" in m for m in self.fails(findings)))

    def test_collective_only_authors_pass(self):
        findings, _ = self.canonical(
            paper_fm(doi=None, authors=[]),
            pubmed=pubmed_json(PAGE_TITLE, individuals=0, collectives=2))
        self.assertEqual(self.fails(findings), [])

    def test_empty_authors_vs_named_individuals_fails(self):
        findings, _ = self.canonical(
            paper_fm(doi=None, authors=[]),
            pubmed=pubmed_json(PAGE_TITLE, individuals=3))
        self.assertTrue(any("empty" in m for m in self.fails(findings)))

    def test_no_identifiers_unverified(self):
        findings, unverified = self.canonical(paper_fm(doi=None, pmid=None))
        self.assertTrue(unverified)
        self.assertTrue(any("manual" in m for m in self.fails(findings)))

    def test_pmid_not_found_fails(self):
        findings, _ = self.canonical(
            paper_fm(doi=None),
            pubmed=pubmed_json(PAGE_TITLE, error="cannot get document"))
        self.assertTrue(any("not found" in m for m in self.fails(findings)))

    def test_pmid_doi_disagreement_fails(self):
        findings, _ = self.canonical(
            paper_fm(), openalex=openalex_json(PAGE_TITLE),
            pubmed=pubmed_json(PAGE_TITLE, doi="10.9999/different-doi"))
        self.assertTrue(any("identifiers disagree" in m
                            for m in self.fails(findings)))

    def test_datacite_absent_nametype_conservative_count(self):
        creators = [{"name": f"Creator {i}"} for i in range(4)]  # no nameType
        findings, _ = self.canonical(
            paper_fm(doi="10.48550/arXiv.2601.99999", pmid=None),
            datacite=datacite_json(PAGE_TITLE, creators=creators))
        self.assertTrue(any("truncated" in m for m in self.fails(findings)))

    def test_datacite_all_organizational_zero_individuals(self):
        creators = [{"name": "Synthetic Consortium",
                     "nameType": "Organizational"}] * 3
        findings, unverified = self.canonical(
            paper_fm(doi="10.48550/arXiv.2601.99999", pmid=None, authors=[]),
            datacite=datacite_json(PAGE_TITLE, creators=creators))
        self.assertEqual(self.fails(findings), [])
        self.assertFalse(unverified)


if __name__ == "__main__":
    unittest.main(verbosity=2)
