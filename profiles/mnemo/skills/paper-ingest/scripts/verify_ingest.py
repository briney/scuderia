#!/usr/bin/env python3
"""verify_ingest.py — Phase 10 verification for paper-ingest.

Checks the graph invariants for one ingested paper page:

  1. Paper frontmatter parses as valid YAML.
  2. All `links:` targets exist as pages on disk. Recognized http(s)
     external URLs are not filesystem targets — they are skipped from
     the existence check and the omission is labeled, never reported
     MISSING. Internal missing links still fail.
  3. All `authors:` slugs resolve to existing people/ pages OR ledger
     entries (see --page-only for the deferred-to-parent variant).
  4. All `cited_by:` targets exist; external URLs are not citation edges.
  5. people/_ledger.yaml parses and has no duplicate slugs. Malformed
     values — non-dict entries, non-string slugs — are reported as
     FAIL, never a crash.

Plus the canonical-identity phase (network; skip with --offline):

  6. The page's identifiers agree with the canonical record:
     - `doi` resolves (DataCite first for arXiv-registered 10.48550/* DOIs,
       OpenAlex otherwise; each falls back to the other, then Crossref) and
       the resolved title matches the page title (token-set ratio >= 90)
       and the publication year is within ±1.
     - `pmid` resolves in PubMed (esummary). PMID-only papers (doi: null)
       compare title and year against PubMed too — a DOI record is not
       the only admissible identity witness. If PubMed supplies a DOI the
       page lacks, that is a missing-DOI FAIL, not a silent 'agrees'. A
       retraction pubtype is surfaced as a warning.
     - the author list is complete against the canonical count (PubMed
       individual authors when pmid present, else the DOI record's
       authors). Fewer than canonical = truncated list (FAIL); more =
       possible conflation (WARN); empty page list against a non-empty
       canonical list of individuals = FAIL. Collectives do not count
       (collective-only authorship legitimately carries `authors: []`).
       For DataCite records, zero individuals is only concluded when
       every creator is explicitly Organizational — absent nameType
       uses the total creator count as a conservative estimate.
     - A page carrying neither DOI nor PMID is canonical UNVERIFIED:
       the online run fails and names the manual source verification
       needed; it does not pass by default.

Filled-page contract (opt-in with --require-filled):

  7. kind is paper; slug matches the bare filename; title and venue are
     nonblank; year is integer-valued — a positive int, or a positive
     decimal digit string like '2024' (quoted legacy values stay
     acceptable; bools, blank, and non-numeric values fail); status is
     published/preprint/unknown; the doi KEY exists carrying either an
     explicit null or a nonblank bare DOI shaped 10.<digits>/<suffix>
     (placeholders and URL forms rejected); authors is a list of
     distinct valid people/<slug> strings ([] is structurally allowed —
     collective-only authorship); cited_by holds only papers/<slug> and
     grants/<slug>; needs-ingest is exactly False; the stub tag is
     absent; fulltext_source is present and nonblank; abstract-only
     requires needs-enrichment exactly True; and the level-two
     sections Abstract/Context/Approach/Findings/Limitations/Analysis/
     Citation/Ingest log are present and nonempty (headings inside
     fenced code examples do not count).

Page-only intermediate mode (--page-only):

  The same read-only checks, but unresolved WELL-SHAPED people/<slug>
  author references are reported DEFERRED TO PARENT rather than failed
  — a "Write ONLY the paper page" child leaves wiring to its parent.
  Other graph errors and malformed shapes are NOT waived, and a
  malformed ledger still fails. With --require-filled, needs-ingest
  must be exactly True (PAGE_READY): the page stays in the ingest queue
  until the parent verifies sources and completes bibliography/author/
  graph wiring — otherwise a parent crash would silently drop
  unfinished work from the queue. The parent flips needs-ingest to
  false only after source verification and wiring, then re-runs full
  verification (no --page-only). Output is labeled intermediate
  (PAGE_READY), never a full-ingest-completed claim.

--ledgerless declares a satellite vault without an author ledger. It refuses
when a ledger exists, so it cannot hide ledger damage in the main brain.
Without --page-only, authors must resolve to person pages in that vault.

Rationale: the five graph invariants verify the brain's internal
consistency but never the paper's real-world identity. Phase 1 resolves
identity; nothing read it back — wrong-DOI defects (a DOI that resolves
to a different paper than the page describes) and truncated or empty
author lists land silently without this phase. It closes both classes
in ~2 API calls per paper.

Usage:
  python3 verify_ingest.py <paper-slug> [--instance /path/to/brain] [--offline]
                          [--require-filled] [--page-only] [--ledgerless]

The brain root is auto-detected by walking up from the cwd looking for a
directory containing both papers/ and people/. Exit code 0 = all pass;
1 = failures found (including canonical lookup errors or unverified identity);
2 = usage/argument errors.

--offline skips the canonical phase for airgapped work; the pass line
then says identity checks were SKIPPED. It is not a publication bypass:
re-run online before commit.
"""

import argparse
import html
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

try:
    import yaml
except ImportError:
    sys.stderr.write("ERROR: PyYAML is required (pip install pyyaml)\n")
    sys.exit(2)

UA = "mnemo-verify-ingest/1.2 (mailto:bryan.briney@gmail.com)"
MAILTO = "bryan.briney@gmail.com"
TIMEOUT = 30
TITLE_PASS = 90.0
STOP = set(
    "the a an of in on for and or to with by from at as is are was were "
    "be been its their we our".split()
)

# Filled-contract shapes (mirrors core/tools/lint-frontmatter.py's DOI rule).
DOI_SHAPE_RE = re.compile(r"^10\.\d{4,9}/\S+$")
DOI_PLACEHOLDERS = ("", "null", "none", "n/a", "tbd")
AUTHOR_REF_RE = re.compile(r"^people/[a-z0-9][a-z0-9-]*$")
CITED_BY_REF_RE = re.compile(r"^(papers|grants)/[a-z0-9][a-z0-9-]*$")
REQUIRED_SECTIONS = (
    "Abstract", "Context", "Approach", "Findings", "Limitations",
    "Analysis", "Citation", "Ingest log",
)


# ------------------------------------------------------------------ matching
# Same token-set matching as validate_identifiers.py — reordered words and
# subset titles (paraphrases) score high; never pass on title alone elsewhere.

def norm_title(t):
    t = html.unescape(re.sub(r"<[^>]+>", " ", t or ""))
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", t.lower()).split())


def content_tokens(t):
    return [x for x in norm_title(t).split() if x not in STOP]


def token_set_ratio(a, b):
    import difflib

    A, B = set(content_tokens(a)), set(content_tokens(b))
    if not A or not B:
        return 0.0
    inter = sorted(A & B)
    rest_a = sorted(A - B)
    rest_b = sorted(B - A)
    t0 = " ".join(inter)
    t1 = " ".join(inter + rest_a)
    t2 = " ".join(inter + rest_b)

    def ratio(x, y):
        return difflib.SequenceMatcher(None, x, y).ratio() * 100 if x and y else 0.0

    return max(ratio(t0, t1), ratio(t0, t2), ratio(t1, t2))


# ------------------------------------------------------------------ fetching

def fetch_json(url, retries=2, backoff=4.0):
    """GET a JSON document with retry/backoff on 429/5xx/transient errors."""
    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                import json

                return json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503) and attempt < retries:
                time.sleep(backoff * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
                continue
            raise
    if last is not None:
        raise last
    raise RuntimeError("fetch failed without exception: %s" % url)


def openalex_work(doi):
    u = (
        f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}"
        f"?mailto={MAILTO}"
    )
    m = fetch_json(u)
    auths = m.get("authorships") or []
    return {
        "title": m.get("title") or "",
        "year": m.get("publication_year"),
        "n_authors": len(auths),
        "retracted": bool(m.get("is_retracted")),
        "source": "OpenAlex",
    }


def datacite_work(doi):
    u = f"https://api.datacite.org/dois/{urllib.parse.quote(doi)}"
    d = fetch_json(u)
    attrs = d.get("data", {}).get("attributes", {})
    titles = attrs.get("titles") or [{}]
    creators = attrs.get("creators") or []
    # Zero individuals is only concluded when EVERY creator is explicitly
    # Organizational. An absent nameType is not evidence of an
    # organization — count those creators as people (conservative: the
    # page author list is then checked against the larger total).
    if creators and all(
        isinstance(c, dict)
        and str(c.get("nameType") or "").strip().lower() == "organizational"
        for c in creators
    ):
        n_individuals = 0
    else:
        n_individuals = len(creators)
    return {
        "title": titles[0].get("title") or "",
        "year": attrs.get("publicationYear"),
        "n_authors": len(creators),
        "n_individuals": n_individuals,
        "n_personal": n_individuals,  # retained alias for older callers
        "retracted": False,
        "source": "DataCite",
    }


def crossref_work(doi):
    u = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
    m = fetch_json(u)["message"]
    issued = (m.get("issued", {}).get("date-parts") or [[None]])[0]
    return {
        "title": (m.get("title") or [""])[0],
        "year": issued[0],
        "n_authors": len(m.get("author") or []),
        "retracted": False,
        "source": "Crossref",
    }


def pubmed_esummary(pmid):
    u = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        f"?db=pubmed&id={pmid}&retmode=json"
    )
    d = fetch_json(u)
    rec = d.get("result", {}).get(str(pmid), {})
    if not rec or rec.get("error"):
        return None
    doi = next(
        (a["value"] for a in rec.get("articleids", []) if a.get("idtype") == "doi"),
        "",
    )
    pubtypes = rec.get("pubtype", []) or []
    # esummary's authors array mixes individuals (authtype "Author") with
    # collectives (authtype "CollectiveName", e.g. trial groups). Only
    # individuals count against the page's author list — a collective-only
    # paper legitimately carries `authors: []` (corporate-authorship branch,
    # paper-ingest Phase 8).
    individuals = [
        a for a in rec.get("authors", []) or []
        if str(a.get("authtype", "")).lower() == "author"
    ]
    return {
        "title": rec.get("title", ""),
        "year": (rec.get("pubdate", "") or "")[:4] or None,
        "doi": doi.lower().rstrip(".") or None,
        "n_authors": len(individuals),
        "n_authors_all": len(rec.get("authors", []) or []),
        "retracted": any("retract" in str(p).lower() for p in pubtypes),
        "source": "PubMed",
    }


# ------------------------------------------------------- canonical identity

def _clean_identifier(value):
    """Normalize a frontmatter identifier; None for absent/placeholder."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    s = str(value).strip()
    if s.lower() in ("", "null", "none"):
        return None
    return s


def canonical_checks(fm):
    """Verify frontmatter identifiers against canonical sources.

    Returns (findings, unverified) where findings is a list of
    (level, message) with level in {"OK", "WARN", "FAIL"}.
    `unverified` is True when no usable identifier existed. Lookup errors
    are returned as FAIL findings; neither outcome is a canonical pass.
    """
    findings = []
    doi = _clean_identifier(fm.get("doi"))
    pmid = _clean_identifier(fm.get("pmid"))
    if doi is None and pmid is None:
        findings.append((
            "FAIL",
            "no usable identifiers (doi, pmid) on the page — canonical "
            "identity is UNVERIFIED; this paper needs manual source "
            "verification (paper-ingest Phase 1) before the canonical "
            "phase can pass",
        ))
        return findings, True

    # ---- DOI resolution + title/year match ------------------------------
    doi_rec = None
    if doi is not None:
        chain = (
            [datacite_work, openalex_work, crossref_work]
            if doi.startswith("10.48550/")
            else [openalex_work, datacite_work, crossref_work]
        )
        errors = []
        for fn in chain:
            try:
                rec = fn(doi)
                if rec.get("title"):
                    doi_rec = rec
                    break
            except Exception as e:  # HTTPError 404 etc. — try next source
                errors.append(f"{getattr(fn, '__name__', '?')}: {e}")
        if doi_rec is None:
            findings.append(("FAIL", f"doi {doi} did not resolve to a record "
                                     f"({'; '.join(errors)[:180]})"))
        else:
            score = token_set_ratio(fm.get("title") or "", doi_rec["title"])
            if score < TITLE_PASS:
                findings.append((
                    "FAIL",
                    f"doi {doi} resolves to a different paper — title match "
                    f"{score:.0f} (<{TITLE_PASS:.0f}): page "
                    f"\"{str(fm.get('title'))[:70]}\" vs {doi_rec['source']} "
                    f"\"{doi_rec['title'][:70]}\"",
                ))
            else:
                findings.append(("OK", f"doi resolves ({doi_rec['source']}, "
                                       f"title match {score:.0f})"))
            try:
                page_year = int(str(fm.get("year"))[:4])
                rec_year = int(str(doi_rec.get("year"))[:4])
                if abs(page_year - rec_year) > 1:
                    findings.append(("FAIL", f"year {page_year} vs canonical "
                                             f"{rec_year} ({doi_rec['source']})"))
            except (TypeError, ValueError):
                pass
            if doi_rec.get("retracted"):
                findings.append(("WARN", "retracted per record — the page must "
                                         "carry a prominent retraction warning "
                                         "(paper-ingest Phase 3)"))

    # ---- PMID resolution + DOI agreement + author count ------------------
    pm_rec = None
    if pmid is not None:
        try:
            pm_rec = pubmed_esummary(pmid)
        except Exception as e:
            findings.append(("FAIL", f"pmid {pmid} lookup failed: {str(e)[:120]}"))
        if pm_rec is None:
            findings.append(("FAIL", f"pmid {pmid} not found in PubMed"))
        else:
            # Validate the PMID's identity independently even when the DOI
            # resolves: an unrelated older record may carry no DOI to compare.
            score = token_set_ratio(fm.get("title") or "",
                                    pm_rec.get("title") or "")
            if score < TITLE_PASS:
                findings.append((
                    "FAIL", f"pmid {pmid} resolves to a different paper — "
                    f"title match {score:.0f} (<{TITLE_PASS:.0f})",
                ))
            else:
                findings.append((
                    "OK", f"pmid title matches ({score:.0f})" +
                    ("; no doi on page" if doi is None else ""),
                ))
            try:
                page_year = int(str(fm.get("year"))[:4])
                rec_year = int(str(pm_rec.get("year"))[:4])
                if abs(page_year - rec_year) > 1:
                    findings.append(("FAIL", f"year {page_year} vs PubMed "
                                             f"{rec_year}"))
            except (TypeError, ValueError):
                pass
            if doi is None:
                if pm_rec.get("doi"):
                    findings.append((
                        "FAIL",
                        f"pmid {pmid} supplies doi {pm_rec['doi']} but the "
                        f"page has no doi — add it (doi: null is only for "
                        f"papers PubMed itself has no DOI for)",
                    ))
            else:
                if pm_rec.get("doi") and pm_rec["doi"] != doi.lower():
                    findings.append((
                        "FAIL",
                        f"pmid {pmid} carries doi {pm_rec['doi']} but page says "
                        f"{doi} — identifiers disagree",
                    ))
                elif pm_rec.get("doi"):
                    findings.append(("OK", f"pmid doi agrees ({pm_rec['doi']})"))
            if pm_rec.get("retracted"):
                findings.append(("WARN", "retracted per PubMed pubtype — the page "
                                         "must carry a prominent retraction "
                                         "warning (paper-ingest Phase 3)"))

    # ---- author-list completeness ----------------------------------------
    page_n = len(fm.get("authors") or [])
    if pm_rec is not None:
        canon_n = pm_rec["n_authors"]
        src = "PubMed"
    elif doi_rec is not None:
        canon_n = doi_rec.get(
            "n_individuals", doi_rec.get("n_authors", 0)
        )
        src = doi_rec["source"]
    else:
        canon_n = None
        src = None

    if canon_n:
        if page_n == 0:
            # PubMed/individual-filtered sources: empty is a defect. OpenAlex
            # counts organizations as authors, so an empty list there is only
            # a warning — corporate authorship is a legitimate Phase 8 branch.
            level = "FAIL" if src in ("PubMed", "DataCite") else "WARN"
            findings.append((
                level,
                f"author list is empty but {src} lists {canon_n} "
                f"(individual) authors — pull the complete list "
                f"(paper-ingest Phase 8); if this is deliberate corporate "
                f"authorship, note it in the Ingest log",
            ))
        elif page_n < canon_n:
            findings.append((
                "FAIL",
                f"author list truncated: page has {page_n}, {src} lists "
                f"{canon_n} — pull the complete list (paper-ingest Phase 8)",
            ))
        elif page_n > canon_n:
            findings.append((
                "WARN",
                f"page lists more authors ({page_n}) than {src} ({canon_n}) "
                f"— check for conflation or ledger-grouping",
            ))
        else:
            findings.append(("OK", f"author count matches {src} ({page_n})"))

    # ---- unverified detection ---------------------------------------------
    attempted = (doi is not None) or (pmid is not None)
    got_record = doi_rec is not None or pm_rec is not None
    unverified = attempted and not got_record and not any(
        lvl == "FAIL" for lvl, _ in findings
    )
    return findings, unverified


# ------------------------------------------------------------ graph invariants

def find_brain_root(start):
    d = os.path.abspath(start)
    while True:
        if os.path.isdir(os.path.join(d, "papers")) and os.path.isdir(
            os.path.join(d, "people")
        ):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def load_page(path):
    """Return (frontmatter_dict, body_text, error). Error is None on success."""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        return None, None, str(e)
    if not text.startswith("---"):
        return None, None, "no frontmatter block (file does not start with ---)"
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, None, "unterminated frontmatter block"
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        return None, None, f"YAML parse error: {e}"
    if not isinstance(fm, dict):
        return None, None, "frontmatter is not a mapping"
    return fm, parts[2] or "", None


def load_frontmatter(path):
    """Return (frontmatter_dict, error). Error is None on success."""
    fm, _, err = load_page(path)
    return fm, err


def target_exists(brain, target):
    """A link target like 'papers/<slug>' or 'concepts/<slug>' exists as a page."""
    t = str(target).strip()
    t = t.strip("[]")
    if t.endswith(".md"):
        t = t[:-3]
    return os.path.isfile(os.path.join(brain, t + ".md"))


def _is_external_url(target):
    """Recognized http(s) external links are not filesystem targets."""
    return (
        isinstance(target, str)
        and target.strip().lower().startswith(("http://", "https://"))
    )


def load_ledger(brain):
    """Return (entries_list, error)."""
    path = os.path.join(brain, "people", "_ledger.yaml")
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        return [], "people/_ledger.yaml not found"
    except yaml.YAMLError as e:
        return None, f"ledger YAML parse error: {e}"
    if data is None:
        return [], None
    if isinstance(data, dict):
        entries = data.get("entries", [])
    elif isinstance(data, list):
        entries = data
    else:
        return None, f"unexpected ledger structure: {type(data).__name__}"
    if not isinstance(entries, list):
        return None, "ledger entries must be a list"
    return entries, None


# ----------------------------------------------------------- filled contract

def required_sections(body):
    """Map level-two heading name -> list of content lines under it.

    Headings inside fenced code blocks (``` or ~~~) do not count — a
    page quoting a template in an example must not satisfy its own
    section requirements from the quote. Level-three-and-deeper
    headings stay inside the enclosing level-two section; a level-one
    heading closes it. Kept deliberately simple.
    """
    sections = {}
    current = None
    fence = None
    for line in (body or "").splitlines():
        stripped = line.strip()
        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            continue
        if stripped.startswith("```") or stripped.startswith("~~~"):
            fence = stripped[:3]
            continue
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", stripped)
        if m:
            level = len(m.group(1))
            if level == 2:
                current = m.group(2)
                sections.setdefault(current, [])
            elif level == 1:
                current = None
            # level >= 3 keeps the enclosing section open
            continue
        if current is not None:
            sections[current].append(stripped)
    return sections


def filled_contract_checks(fm, body, filename_slug, page_only=False):
    """Enforce the filled-page contract (opt-in via --require-filled).

    Returns a list of FAIL message strings; empty means the contract
    holds. In page_only mode, needs-ingest must be exactly True
    (PAGE_READY — the page stays in the queue until the parent
    completes wiring); in full mode needs-ingest must be exactly False.
    Both modes require the completed body to have dropped the stub tag.
    Structural only: content quality and canonical identity are judged
    elsewhere (source read-back by the parent, canonical phase here).
    """
    fails = []

    if fm.get("kind") != "paper":
        fails.append(f"kind must be 'paper' — got {fm.get('kind')!r}")
    slug = fm.get("slug")
    if not isinstance(slug, str) or slug.strip() != filename_slug:
        fails.append(f"slug {slug!r} does not match the page filename "
                     f"'{filename_slug}'")
    title = fm.get("title")
    if not isinstance(title, str) or not title.strip():
        fails.append("title is missing or blank")
    venue = fm.get("venue")
    if not isinstance(venue, str) or not venue.strip():
        fails.append("venue is missing or blank")
    # Integer-valued years only: int, or a positive decimal digit string
    # Quoted legacy years remain acceptable; reject booleans and text.
    year = fm.get("year")
    year_valid = (
        (isinstance(year, int) and not isinstance(year, bool) and year > 0)
        or (isinstance(year, str) and re.fullmatch(r"[0-9]+", year.strip())
            and int(year) > 0)
    )
    if not year_valid:
        fails.append(f"year must be a positive integer (a quoted digit "
                     f"string like '2024' is accepted) — got {year!r}")
    if fm.get("status") not in ("published", "preprint", "unknown"):
        fails.append(f"status must be published/preprint/unknown — "
                     f"got {fm.get('status')!r}")

    if "doi" not in fm:
        fails.append("doi key missing — every paper page must carry a doi "
                     "(explicit null for no-DOI papers)")
    else:
        doi = fm["doi"]
        if doi is None:
            pass  # explicit null — allowed
        elif not isinstance(doi, str) or not doi.strip():
            fails.append("doi is empty or blank — use an explicit "
                         "doi: null for no-DOI papers")
        else:
            s = doi.strip()
            if s.lower() in DOI_PLACEHOLDERS:
                fails.append(f"doi is a placeholder string ({doi!r}) — use an "
                             f"explicit doi: null for no-DOI papers")
            elif s.lower().startswith(("http://", "https://",
                                       "doi.org", "dx.doi.org")):
                fails.append(f"doi is stored as a URL ({doi!r}) — use the "
                             f"bare 10.<digits>/<suffix> form")
            elif not DOI_SHAPE_RE.match(s):
                fails.append(f"doi {doi!r} is not shaped 10.<digits>/<suffix>")

    authors = fm.get("authors")
    if not isinstance(authors, list):
        fails.append(f"authors must be a list of people/<slug> strings — "
                     f"got {type(authors).__name__}")
    else:
        bad_refs = [a for a in authors
                    if not (isinstance(a, str) and AUTHOR_REF_RE.match(a.strip()))]
        if bad_refs:
            fails.append(f"authors entries must be people/<slug> strings — "
                         f"bad entries: {bad_refs}")
        dups = sorted({a for a in authors
                       if isinstance(a, str) and authors.count(a) > 1})
        if dups:
            fails.append(f"duplicate authors: {dups}")

    # A filled page with no inbound citations may omit the cited_by key
    # entirely (legacy pages do); present-but-malformed still fails.
    cited_by = fm.get("cited_by")
    if cited_by is None:
        cited_by = []
    if not isinstance(cited_by, list):
        fails.append(f"cited_by must be a list of papers/<slug> or "
                     f"grants/<slug> strings — got {type(cited_by).__name__}")
    else:
        bad_cb = [c for c in cited_by
                  if not (isinstance(c, str) and CITED_BY_REF_RE.match(c.strip()))]
        if bad_cb:
            fails.append(f"cited_by entries must be papers/<slug> or "
                         f"grants/<slug> strings — bad entries: {bad_cb}")

    needs_ingest = fm.get("needs-ingest")
    if page_only:
        if needs_ingest is not True:
            fails.append(f"needs-ingest must be exactly true in page-only mode "
                         f"(PAGE_READY) — the page stays in the ingest queue "
                         f"until the parent completes wiring; got "
                         f"{needs_ingest!r}")
    else:
        if needs_ingest is not False:
            fails.append(f"needs-ingest must be exactly false after a "
                         f"completed ingest — got {needs_ingest!r} (page "
                         f"still queued/unfilled)")

    tags = fm.get("tags") or []
    tag_list = tags if isinstance(tags, list) else [tags]
    if any(
        isinstance(t, str) and t.strip().lower() == "stub" for t in tag_list
    ):
        fails.append("tags still contains 'stub' — a filled page must drop "
                     "the stub tag")

    fulltext_source = fm.get("fulltext_source")
    # Obvious placeholder labels are not retrieval provenance (a legacy
    # corpus page carries `fulltext_source: none` — actual missing
    # retrieval — despite a nonempty body). No closed enum: any other
    # nonblank label passes; parent source checks verify labels.
    if (
        not isinstance(fulltext_source, str)
        or not fulltext_source.strip()
        or fulltext_source.strip().lower() in DOI_PLACEHOLDERS + ("unknown",)
    ):
        fails.append("fulltext_source is missing, blank, or a placeholder "
                     "— record where the distilled text came from "
                     "(e.g. pmc-xml, abstract-only)")
    if isinstance(fulltext_source, str) and fulltext_source.strip() == "abstract-only":
        if fm.get("needs-enrichment") is not True:
            fails.append("fulltext_source is abstract-only but needs-enrichment "
                         "is not exactly true — partial distillations must be "
                         "flagged for enrichment")

    sections = required_sections(body)
    for name in REQUIRED_SECTIONS:
        content = sections.get(name)
        if not content or not any(ln.strip() for ln in content):
            fails.append(f"required body section '## {name}' is missing or empty")

    return fails


def main():
    ap = argparse.ArgumentParser(description="Phase 10 verification for paper-ingest")
    ap.add_argument("slug", help="paper slug (papers/<slug>.md)")
    ap.add_argument("--instance", "--brain", dest="instance",
                    help="instance root (auto-detected from cwd if omitted); --brain is a deprecated alias")
    ap.add_argument("--offline", action="store_true",
                    help="skip the canonical-identity phase (network checks)")
    ap.add_argument("--require-filled", action="store_true",
                    help="additionally enforce the filled-page contract: "
                         "kind/slug/title/venue/year/status, doi key + bare-"
                         "DOI shape (explicit null allowed), authors/"
                         "cited_by shapes, needs-ingest, stub tag, "
                         "fulltext_source, abstract-only => needs-"
                         "enrichment, and required nonempty body sections")
    ap.add_argument("--page-only", action="store_true",
                    help="page-only intermediate validation: unresolved "
                         "well-shaped people/<slug> author refs are "
                         "DEFERRED TO PARENT instead of failures (parents "
                         "re-run full verification after wiring); with "
                         "--require-filled, needs-ingest must be true "
                         "(PAGE_READY)")
    ap.add_argument("--ledgerless", action="store_true",
                    help="explicit satellite topology with no author ledger; "
                         "full mode requires person pages, page-only may defer "
                         "their creation; refuses when a ledger exists")
    ap.add_argument('--source-package-handoff', help='absolute verified source-package handoff.json; required for the retained-PDF production route')
    ap.add_argument('--source-package-method', help='absolute explicitly trusted accepted PDF method directory (requires its PDF dependencies)')
    args = ap.parse_args()
    if bool(args.source_package_handoff) != bool(args.source_package_method):
        ap.error('--source-package-handoff and --source-package-method must be supplied together')

    brain = args.instance or find_brain_root(os.getcwd())
    if not brain:
        sys.stderr.write(
            "ERROR: could not auto-detect instance root (no papers/ + people/ above cwd); "
            "pass --instance\n"
        )
        sys.exit(2)

    slug = args.slug[:-3] if args.slug.endswith(".md") else args.slug
    paper_path = os.path.join(brain, "papers", slug + ".md")
    if not os.path.isfile(paper_path):
        sys.stderr.write(f"ERROR: paper page not found: {paper_path}\n")
        sys.exit(2)

    failures = 0
    print(f"Paper: {slug}")
    if args.page_only:
        print("  Mode: page-only intermediate validation — not a full ingest")

    # Invariant 1: frontmatter parses
    fm, body, err = load_page(paper_path)
    if err:
        print(f"  Frontmatter: FAIL ({err})")
        failures += 1
    else:
        print("  Frontmatter: OK")
    fm = fm if isinstance(fm, dict) else {}
    body = body or ""

    # Invariant 2: links targets exist (http(s) URLs are external, not
    # filesystem targets — skipped and labeled, never existence-checked)
    links = fm.get("links")
    links = [] if links is None else links
    if not isinstance(links, list):
        print("  links: FAIL (links is not a list)")
        failures += 1
        links = []
    external_links = [t for t in links if _is_external_url(t)]
    internal_links = [t for t in links if not _is_external_url(t)]
    bad = [t for t in internal_links if not target_exists(brain, t)]
    ext_note = (f", {len(external_links)} external URL(s) skipped "
                f"(not filesystem targets)") if external_links else ""
    if bad:
        print(f"  links: {len(links)} checked, {len(bad)} MISSING: {bad}{ext_note}")
        failures += len(bad)
    else:
        print(f"  links: {len(links)} checked, {len(internal_links)} OK{ext_note}")

    # Invariant 5 (loaded early — invariant 3 needs the ledger): ledger parses,
    # no duplicate slugs, malformed entries FAIL instead of crashing
    if args.ledgerless:
        ledger_path = os.path.join(brain, "people", "_ledger.yaml")
        entries = []
        lerr = ("ledger exists: --ledgerless cannot bypass its validation"
                if os.path.lexists(ledger_path) else None)
        if lerr is None:
            print("  Ledger: not applicable (declared ledgerless topology)")
    else:
        entries, lerr = load_ledger(brain)
    entries = entries or []
    ledger_slugs = set()
    if lerr:
        print(f"  Ledger: FAIL ({lerr})")
        failures += 1
    else:
        malformed = 0
        counts = {}
        for e in entries:
            if not isinstance(e, dict):
                malformed += 1
                continue
            s = e.get("slug")
            if s is None or (isinstance(s, str) and s == ""):
                continue
            if not isinstance(s, str):
                malformed += 1
                continue
            counts[s] = counts.get(s, 0) + 1
        dups = {s for s, n in counts.items() if n > 1}
        ledger_slugs = set(counts)
        if malformed:
            print(f"  Ledger: FAIL ({malformed} malformed entries — non-dict "
                  f"entry or non-string slug)")
            failures += 1
        if dups:
            print(f"  Ledger: {len(entries)} entries, DUPLICATE SLUGS: {sorted(dups)}")
            failures += len(dups)
        if not malformed and not dups and not args.ledgerless:
            print(f"  Ledger: {len(entries)} entries, 0 duplicates")

    # Invariant 3: authors resolve to people/ pages or ledger entries
    # (page-only mode defers well-shaped unresolved refs to the parent)
    authors = fm.get("authors")
    authors = [] if authors is None else authors
    if not isinstance(authors, list):
        print("  authors: FAIL (authors is not a list)")
        failures += 1
        authors = []
    deferred = []
    unresolved = []
    for a in authors:
        t = str(a).strip().strip("[]")
        if t.endswith(".md"):
            t = t[:-3]
        if t.startswith("people/"):
            person_slug = t[len("people/"):]
        else:
            person_slug = t
        page = os.path.join(brain, "people", person_slug + ".md")
        if not os.path.isfile(page) and person_slug not in ledger_slugs:
            if args.page_only and isinstance(a, str) and AUTHOR_REF_RE.match(t):
                deferred.append(t)
            else:
                unresolved.append(t)
    if unresolved:
        print(f"  authors: {len(authors)} checked, {len(unresolved)} UNRESOLVED: {unresolved}")
        failures += len(unresolved)
    if deferred:
        print(f"  authors: {len(authors)} checked, {len(deferred)} "
              f"DEFERRED TO PARENT (page-only): {deferred}")
    if not unresolved and not deferred:
        print(
            f"  authors: {len(authors)} checked, {len(authors)} OK "
            "(all resolve to people/ pages or ledger)"
        )

    # Invariant 4: cited_by targets must exist as internal pages.
    cited_by = fm.get("cited_by")
    cited_by = [] if cited_by is None else cited_by
    if not isinstance(cited_by, list):
        print("  cited_by: FAIL (cited_by is not a list)")
        failures += 1
        cited_by = []
    bad_cb = [t for t in cited_by if not target_exists(brain, t)]
    if bad_cb:
        print(f"  cited_by: {len(cited_by)} checked, {len(bad_cb)} MISSING: {bad_cb}")
        failures += len(bad_cb)
    else:
        print(f"  cited_by: {len(cited_by)} checked, {len(cited_by)} OK")

    # Filled-page contract (--require-filled; page-only refines its
    # needs-ingest/stub semantics)
    if args.require_filled:
        filled_fails = filled_contract_checks(fm, body, slug,
                                               page_only=args.page_only)
        if filled_fails:
            print(f"  Filled contract: {len(filled_fails)} FAIL")
            for msg in filled_fails:
                print(f"    [FAIL] {msg}")
            failures += len(filled_fails)
        else:
            print("  Filled contract: OK" + (
                " (PAGE_READY: needs-ingest true, wiring deferred to parent)"
                if args.page_only else ""))

    if args.source_package_handoff:
        try:
            from source_package import absolute, verify_handoff
            handoff = absolute(args.source_package_handoff)
            # The log pointer is relative to the paper page, not new frontmatter.
            pointer = os.path.relpath(handoff, os.path.dirname(os.path.abspath(paper_path)))
            log = required_sections(body).get('Ingest log', [])
            if ('Source package: ' + pointer) not in log:
                raise ValueError('Ingest log requires relative source-package pointer: Source package: ' + pointer)
            verify_handoff(handoff, args.source_package_method,
                           expected_article={key: fm.get(key) for key in ('slug','title','doi','pmid')})
            print('  Source package: OK (mechanical completion only; scientific acceptance remains separate)')
        except (OSError, ValueError, KeyError, TypeError, ImportError, RuntimeError) as exc:
            print(f'  Source package: FAIL ({exc})')
            failures += 1

    # Invariant 6: canonical identity (network)
    if args.offline:
        print("  Canonical identity: SKIPPED (--offline)")
    else:
        try:
            findings, unverified = canonical_checks(fm)
        except Exception as e:
            findings, unverified = [("FAIL", f"canonical phase crashed: {e}")], False
        n_fail = sum(1 for lvl, _ in findings if lvl == "FAIL")
        n_warn = sum(1 for lvl, _ in findings if lvl == "WARN")
        if unverified:
            print("  Canonical identity: UNVERIFIED — no usable identifiers "
                  "on the page. This page needs manual source verification "
                  "(paper-ingest Phase 1); offline structure checks cannot "
                  "establish its identity.")
            if not n_fail:
                failures += 1
        elif n_fail or n_warn:
            print(f"  Canonical identity: {n_fail} FAIL, {n_warn} WARN")
        else:
            print("  Canonical identity: OK")
        for lvl, msg in findings:
            if lvl != "OK":
                print(f"    [{lvl}] {msg}")
        failures += n_fail

    print()
    if failures:
        print(f"FAIL: {failures} problem(s) found")
        sys.exit(1)
    if args.page_only:
        print("PAGE_READY: page-only intermediate validation passed — not a "
              "full ingest completed. needs-ingest stays true until the "
              "parent verifies sources and completes bibliography/author/"
              "graph wiring, then re-runs full verification.")
        sys.exit(0)
    if args.offline:
        print("PASS: offline structural checks OK — canonical identity "
              "checks SKIPPED (--offline); re-run online before commit")
        sys.exit(0)
    print("PASS: All checks OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
