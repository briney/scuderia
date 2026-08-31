#!/usr/bin/env python3
"""verify_ingest.py — Phase 10 verification for paper-ingest.

Checks the graph invariants for one ingested paper page:

  1. Paper frontmatter parses as valid YAML.
  2. All `links:` targets exist as pages on disk.
  3. All `authors:` slugs resolve to existing people/ pages OR ledger entries.
  4. All `cited_by:` targets exist.
  5. people/_ledger.yaml parses and has no duplicate slugs.

Plus the canonical-identity phase (network; skip with --offline):

  6. The page's identifiers agree with the canonical record:
     - `doi` resolves (DataCite first for arXiv-registered 10.48550/* DOIs,
       OpenAlex otherwise; each falls back to the other, then Crossref) and
       the resolved title matches the page title (token-set ratio >= 90)
       and the publication year is within ±1.
     - `pmid` resolves in PubMed (esummary) and its DOI agrees with the
       page `doi`; a retraction pubtype is surfaced as a warning.
     - the author list is complete against the canonical count (PubMed
       individual authors when pmid present, else the DOI record's
       authors). Fewer than canonical = truncated list (FAIL); more =
       possible conflation (WARN); empty page list against a non-empty
       canonical list of individuals = FAIL.

Rationale: the five graph invariants verify the brain's internal
consistency but never the paper's real-world identity. Phase 1 resolves
identity; nothing read it back — wrong-DOI defects (a DOI that resolves
to a different paper than the page describes) and truncated or empty
author lists land silently without this phase. It closes both classes
in ~2 API calls per paper.

Usage:
  python3 verify_ingest.py <paper-slug> [--instance /path/to/brain] [--offline]

The brain root is auto-detected by walking up from the cwd looking for a
directory containing both papers/ and people/. Exit code 0 = all pass;
1 = failures found (including canonical UNVERIFIED due to network);
2 = usage/argument errors.
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
    return {
        "title": titles[0].get("title") or "",
        "year": attrs.get("publicationYear"),
        "n_authors": len(creators),
        "n_personal": sum(
            1 for c in creators if c.get("nameType") == "Personal"
        ),
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
    `unverified` is True when every applicable source was unreachable —
    the caller must treat that as a non-pass, not a pass.
    """
    findings = []
    doi = _clean_identifier(fm.get("doi"))
    pmid = _clean_identifier(fm.get("pmid"))
    if doi is None and pmid is None:
        findings.append(("OK", "no identifiers on page — canonical phase not applicable"))
        return findings, False

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
            if doi is not None and pm_rec.get("doi") and pm_rec["doi"] != doi.lower():
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
        canon_n = doi_rec.get("n_personal", doi_rec.get("n_authors", 0))
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


def load_frontmatter(path):
    """Return (frontmatter_dict, error). Error is None on success."""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        return None, str(e)
    if not text.startswith("---"):
        return None, "no frontmatter block (file does not start with ---)"
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, "unterminated frontmatter block"
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        return None, f"YAML parse error: {e}"
    if not isinstance(fm, dict):
        return None, "frontmatter is not a mapping"
    return fm, None


def target_exists(brain, target):
    """A link target like 'papers/<slug>' or 'concepts/<slug>' exists as a page."""
    t = str(target).strip()
    t = t.strip("[]")
    if t.endswith(".md"):
        t = t[:-3]
    return os.path.isfile(os.path.join(brain, t + ".md"))


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
    return entries, None


def main():
    ap = argparse.ArgumentParser(description="Phase 10 verification for paper-ingest")
    ap.add_argument("slug", help="paper slug (papers/<slug>.md)")
    ap.add_argument("--instance", "--brain", dest="instance",
                    help="instance root (auto-detected from cwd if omitted); --brain is a deprecated alias")
    ap.add_argument("--offline", action="store_true",
                    help="skip the canonical-identity phase (network checks)")
    args = ap.parse_args()

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

    # Invariant 1: frontmatter parses
    fm, err = load_frontmatter(paper_path)
    if err:
        print(f"  Frontmatter: FAIL ({err})")
        failures += 1
    else:
        print("  Frontmatter: OK")
    fm = fm if isinstance(fm, dict) else {}

    # Invariant 2: links targets exist
    links = fm.get("links") or []
    bad = [t for t in links if not target_exists(brain, t)]
    if bad:
        print(f"  links: {len(links)} checked, {len(bad)} MISSING: {bad}")
        failures += len(bad)
    else:
        print(f"  links: {len(links)} checked, {len(links)} OK")

    # Invariant 5 (loaded early — invariant 3 needs the ledger): ledger parses,
    # no duplicate slugs
    entries, lerr = load_ledger(brain)
    entries = entries or []
    ledger_slugs = set()
    if lerr:
        print(f"  Ledger: FAIL ({lerr})")
        failures += 1
    else:
        from collections import Counter

        counts = Counter(
            e.get("slug") for e in entries if isinstance(e, dict) and e.get("slug")
        )
        dups = {s for s, n in counts.items() if n > 1}
        ledger_slugs = set(counts)
        if dups:
            print(f"  Ledger: {len(entries)} entries, DUPLICATE SLUGS: {sorted(dups)}")
            failures += len(dups)
        else:
            print(f"  Ledger: {len(entries)} entries, 0 duplicates")

    # Invariant 3: authors resolve to people/ pages or ledger entries
    authors = fm.get("authors") or []
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
            unresolved.append(t)
    if unresolved:
        print(f"  authors: {len(authors)} checked, {len(unresolved)} UNRESOLVED: {unresolved}")
        failures += len(unresolved)
    else:
        print(
            f"  authors: {len(authors)} checked, {len(authors)} OK "
            "(all resolve to people/ pages or ledger)"
        )

    # Invariant 4: cited_by targets exist
    cited_by = fm.get("cited_by") or []
    bad_cb = [t for t in cited_by if not target_exists(brain, t)]
    if bad_cb:
        print(f"  cited_by: {len(cited_by)} checked, {len(bad_cb)} MISSING: {bad_cb}")
        failures += len(bad_cb)
    else:
        print(f"  cited_by: {len(cited_by)} checked, {len(cited_by)} OK")

    # Invariant 6: canonical identity (network)
    if args.offline:
        print("  Canonical identity: SKIPPED (--offline)")
    else:
        try:
            findings, unverified = canonical_checks(fm)
        except Exception as e:
            findings, unverified = [("FAIL", f"canonical phase crashed: {e}")], False
        if unverified:
            print("  Canonical identity: UNVERIFIED — all canonical sources "
                  "unreachable. Re-run before commit, or pass --offline to "
                  "deliberately skip.")
            failures += 1
        elif findings:
            levels = [lvl for lvl, _ in findings]
            n_fail = levels.count("FAIL")
            n_warn = levels.count("WARN")
            head = "FAIL" if n_fail else ("WARN" if n_warn else "OK")
            print(f"  Canonical identity: {n_fail} FAIL, {n_warn} WARN" if (n_fail or n_warn)
                  else "  Canonical identity: OK")
            for lvl, msg in findings:
                if lvl != "OK":
                    print(f"    [{lvl}] {msg}")
            failures += n_fail

    print()
    if failures:
        print(f"FAIL: {failures} problem(s) found")
        sys.exit(1)
    print("PASS: All checks OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
