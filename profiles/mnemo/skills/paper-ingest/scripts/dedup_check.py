#!/usr/bin/env python3
"""dedup_check.py — pre-write dedup gate for paper-ingest Phase 2.

Scans papers/*.md frontmatter (not bodies) for an existing page with the
same DOI, PMID, or a near-identical title, BEFORE a new page is written.

Motivation: the Phase 2 dedup search was prose guidance ("search papers/
for the resolved PMID/DOI/title") with no mechanical support. A
citation-form search fails on near-duplicate slugs — the 2026-08-30
ingestion audit found full-paper pages and stubs for the same DOI filed
under different slugs. This gate is one command with an exit code, so
it is gate-able from any producer (paper-ingest direct, stub fills,
literature-dive dispatches, grant-ingest citation stubs).

Match channels (all case-insensitive where applicable):
  doi    exact match on the normalized bare DOI (strong key)
  pmid   exact match on the normalized integer (strong key)
  title  token-set fuzzy match, reported at >= 85 (weak key — REVIEW
         only; corrections/replies/sister papers share titles)

Output: one line per matching page, with needs-ingest status, then a
summary. Exit 0 = no existing page (safe to create); 1 = existing page
found (do NOT create — re-ingest/enrich/fill per paper-ingest Phase 2);
2 = usage error.

Usage:
  python3 dedup_check.py --doi 10.1038/nature12345 [--pmid 12345678] \
      [--title "Some paper title"] [--instance /path/to/brain]

Stdlib only. Scanning ~4000 pages takes ~2s.
"""

import argparse
import difflib
import html
import json
import os
import re
import sys
import unicodedata

try:
    import yaml
except ImportError:
    sys.stderr.write("ERROR: PyYAML is required (pip install pyyaml)\n")
    sys.exit(2)

TITLE_REVIEW = 85.0
STOP = set(
    "the a an of in on for and or to with by from at as is are was were "
    "be been its their we our".split()
)


def norm_title(t):
    t = html.unescape(re.sub(r"<[^>]+>", " ", t or ""))
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", t.lower()).split())


def content_tokens(t):
    return [x for x in norm_title(t).split() if x not in STOP]


def token_set_ratio(a, b):
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


def clean_id(value):
    if value is None or isinstance(value, bool):
        return None
    s = str(value).strip()
    if s.lower() in ("", "null", "none", "n/a"):
        return None
    return s


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


def load_fm(path):
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None
    return fm if isinstance(fm, dict) else None


def main():
    ap = argparse.ArgumentParser(description="Pre-write dedup gate (paper-ingest Phase 2)")
    ap.add_argument("--doi")
    ap.add_argument("--pmid")
    ap.add_argument("--title")
    ap.add_argument("--instance", "--brain", dest="instance",
                    help="instance root (auto-detected from cwd if omitted)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = ap.parse_args()

    doi = clean_id(args.doi)
    pmid = clean_id(args.pmid)
    title = args.title
    if doi is None and pmid is None and not title:
        ap.error("provide at least one of --doi / --pmid / --title")

    brain = args.instance or find_brain_root(os.getcwd())
    if not brain:
        sys.stderr.write("ERROR: could not auto-detect instance root; pass --instance\n")
        sys.exit(2)

    doi_key = doi.lower() if doi else None
    matches = []
    papers_dir = os.path.join(brain, "papers")
    for fn in sorted(os.listdir(papers_dir)):
        if not fn.endswith(".md"):
            continue
        fm = load_fm(os.path.join(papers_dir, fn))
        if fm is None or fm.get("kind") != "paper":
            continue
        reasons = []
        page_doi = clean_id(fm.get("doi"))
        if doi_key and page_doi and page_doi.lower() == doi_key:
            reasons.append("doi")
        page_pmid = clean_id(fm.get("pmid"))
        if pmid and page_pmid and page_pmid == pmid:
            reasons.append("pmid")
        score = None
        if title:
            score = round(token_set_ratio(title, fm.get("title") or ""), 1)
            if score >= TITLE_REVIEW:
                reasons.append(f"title~{score}")
        if reasons:
            matches.append({
                "file": fn,
                "slug": fm.get("slug"),
                "title": fm.get("title"),
                "needs_ingest": bool(fm.get("needs-ingest")),
                "stub_tag": "stub" in (fm.get("tags") or []),
                "matched_on": reasons,
                "title_score": score,
            })

    if args.json:
        print(json.dumps({"matches": matches, "count": len(matches)}, indent=1))
    else:
        for m in matches:
            state = "STUB" if (m["needs_ingest"] or m["stub_tag"]) else "FULL"
            print(f"{state}  {m['file']}  matched: {', '.join(m['matched_on'])}")
            if not args.json and m["title"]:
                print(f"      title: {str(m['title'])[:90]}")
        print(f"dedup_check: {len(matches)} existing page(s) "
              f"{'FOUND — do NOT create a duplicate' if matches else '— safe to create'}")

    sys.exit(1 if matches else 0)


if __name__ == "__main__":
    main()
