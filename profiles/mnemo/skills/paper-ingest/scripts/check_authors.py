#!/usr/bin/env python3
"""Pre-write author slug alignment for paper-ingest Phase 8 — the definitive check.

Greps miss ledger entries two ways (both observed in the wild):
  1. name-order variants  — "Yi Zhou" vs "Zhou Yi" (2026-08-31)
  2. indentation variants — "- name: X" (entry start, 0-indent) vs
     "  name: X" (mid-entry, 2-space); indent-anchored greps like
     `grep -E "^  name:"` silently skip every 0-indent entry (2026-09-02:
     three existing authors were wrongly declared "new" this way during
     the Lightman ingest before a full-ledger scan caught them)

This script sidesteps both by yaml.safe_load-ing the whole ledger and
comparing full-name token sets, order-independently. It also lists
same-surname entries as conflation-review candidates
(check their affiliations before concluding "different person").

Usage:
    python3 check_authors.py --ledger <vault>/people/_ledger.yaml \
        [--people-dir <vault>/people] "Hunter Lightman" "Karl Cobbe" ...
    # or one name per line on stdin:
    printf 'Hunter Lightman\nKarl Cobbe\n' | \
        python3 check_authors.py --ledger <vault>/people/_ledger.yaml

Per author, prints EXISTING (slug, person-page presence, affiliations,
citation count) or NEW (mint a slug via slugify_name.py). Report-only;
always exits 0.
"""
import argparse
import os
import sys

import yaml


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Definitive pre-write author existence check against people/_ledger.yaml"
    )
    ap.add_argument("--ledger", required=True, help="path to people/_ledger.yaml")
    ap.add_argument("--people-dir", default=None,
                    help="people/ dir for person-page existence (default: ledger's dir)")
    ap.add_argument("names", nargs="*", help='author names, e.g. "Hunter Lightman"')
    args = ap.parse_args()

    with open(args.ledger) as f:
        data = yaml.safe_load(f)
    entries = data["entries"] if isinstance(data, dict) else data

    people_dir = args.people_dir or os.path.dirname(os.path.abspath(args.ledger))
    todo = args.names or [ln.strip() for ln in sys.stdin if ln.strip()]

    for raw in todo:
        name = " ".join(raw.split())
        if not name:
            continue
        want = set(name.lower().replace(",", " ").split())
        surname = name.split()[-1].lower()
        hits, near = [], []
        for e in entries:
            if not isinstance(e, dict):
                continue
            en = e.get("name")
            if not isinstance(en, str) or not en:
                continue
            etoks = set(en.lower().replace(",", " ").split())
            if etoks == want:
                hits.append(e)
            if surname in etoks:
                near.append(e)

        if hits:
            print(f"EXISTING  {name}")
            for e in hits:
                slug = e.get("slug")
                page = "yes" if slug and os.path.exists(
                    os.path.join(people_dir, f"{slug}.md")) else "no"
                cits = e.get("citations") or []
                print(f"  -> slug={slug}  person_page={page}")
                print(f"     ledger name={e.get('name')!r}")
                print(f"     affiliations={e.get('affiliations')}")
                print(f"     citations={len(cits)} (e.g. {cits[:3]})")
        else:
            print(f"NEW       {name}")
            print("  -> no ledger entry; mint slug via slugify_name.py")

        review = [e for e in near if e not in hits]
        if review:
            shown = [e.get("name") for e in review[:8]]
            print(f"  surname-review ({len(review)} same-surname "
                  f"entr{'y' if len(review) == 1 else 'ies'}, conflation check): {shown}")


if __name__ == "__main__":
    main()
