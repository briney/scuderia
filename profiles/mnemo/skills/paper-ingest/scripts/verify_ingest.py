#!/usr/bin/env python3
"""verify_ingest.py — Phase 10 verification for paper-ingest.

Checks all five Phase 10 invariants for one ingested paper page:

  1. Paper frontmatter parses as valid YAML.
  2. All `links:` targets exist as pages on disk.
  3. All `authors:` slugs resolve to existing people/ pages OR ledger entries.
  4. All `cited_by:` targets exist.
  5. people/_ledger.yaml parses and has no duplicate slugs.

Usage:
  python3 verify_ingest.py <paper-slug> [--brain /path/to/brain]

The brain root is auto-detected by walking up from the cwd looking for a
directory containing both papers/ and people/. Exit code 0 = all pass;
non-zero = failures found.
"""

import argparse
import os
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("ERROR: PyYAML is required (pip install pyyaml)\n")
    sys.exit(2)


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
    # tolerate wikilink-style or .md-suffixed targets
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
    # the ledger is a dict with a top-level 'entries:' key
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

    print()
    if failures:
        print(f"FAIL: {failures} problem(s) found")
        sys.exit(1)
    print("PASS: All checks OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
