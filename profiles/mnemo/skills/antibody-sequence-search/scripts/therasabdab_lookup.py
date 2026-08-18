#!/usr/bin/env python3
"""therasabdab_lookup.py — query the local Thera-SAbDab mirror by antibody name.

Usage:
    python3 therasabdab_lookup.py NAME [NAME ...] [--mirror PATH]

Resolution ladder (per NAME, in order):
  1. exact/normalized match on `Therapeutic` or `Alternative Therapeutic Names`
  2. suffix-strip: drop trailing target suffixes (muromonab-cd3 -> muromonab)
  3. cocktail split: hyphenated multi-INN names -> look up each component
     (only when the whole name misses; requires every component to be a
     plausible INN stem, i.e. end in -mab/-cept or be >=6 chars)

Output: JSON array, one object per NAME. Missing sequences are null, never
invented. Sequences are variable domains only (mature) — see the mirror
manifest in the brain's references/therapeutic-antibodies/raw/mirrors/.

Default mirror path is brain-root-relative (run from the brain root, or pass
--mirror explicitly).
"""
import csv
import json
import os
import re
import sys

DEFAULT_MIRROR = os.path.join(
    "references", "therapeutic-antibodies", "raw", "mirrors",
    "TheraSAbDab_SeqStruc_OnlineDownload.csv",
)
MISSING = {"", "na", "none", "n/a", "nan"}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def clean(seq: str):
    s = (seq or "").strip()
    if s.lower() in MISSING:
        return None
    # sanity: amino acids only
    if not re.fullmatch(r"[A-Z]+", s):
        return None
    return s


def build_index(path: str):
    with open(path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    idx = {}
    for r in rows:
        names = [r["Therapeutic"]]
        names += re.split(r"[;,]", r.get("Alternative Therapeutic Names", "") or "")
        for n in names:
            key = norm(n)
            if key:
                idx.setdefault(key, r)
    return rows, idx


def row_to_result(query: str, r, match_kind: str):
    vh, vl = clean(r["HeavySequence"]), clean(r["LightSequence"])
    vh2, vl2 = clean(r["HeavySequence(ifbispec)"]), clean(r["LightSequence(ifbispec)"])
    targets = [t.strip() for t in re.split(r"[;/]", r.get("Target", "") or "") if t.strip()]
    arms = []
    if vh or vl:
        arms.append({
            "arm": 1,
            "target_hint": targets[0] if targets else None,
            "vh": vh, "vl": vl,
            "vh_len": len(vh) if vh else None,
            "vl_len": len(vl) if vl else None,
        })
    if vh2 or vl2:
        arms.append({
            "arm": 2,
            "target_hint": targets[1] if len(targets) > 1 else None,
            "vh": vh2, "vl": vl2,
            "vh_len": len(vh2) if vh2 else None,
            "vl_len": len(vl2) if vl2 else None,
        })
    si100 = r.get("100% SI Structure", "").strip()
    si99 = r.get("99% SI Structure", "").strip()
    return {
        "query": query,
        "found": True,
        "match_kind": match_kind,
        "matched_name": r["Therapeutic"].strip(),
        "format": r.get("Format", "").strip() or None,
        "ch1_isotype": r.get("CH1 Isotype", "").strip() or None,
        "targets": targets,
        "genetics": r.get("Genetics (Bispecifics delimited with semicolon)", "").strip() or None,
        "arms": arms,
        "structures_100si": None if si100.lower() in MISSING else si100,
        "structures_99si": None if si99.lower() in MISSING else si99,
        "sequence_scope": "variable-domain only (mature; no signal peptide / constant region)",
        "source": "Thera-SAbDab",
    }


def lookup(name: str, idx):
    # 1. exact/normalized
    r = idx.get(norm(name))
    if r:
        return row_to_result(name, r, "exact")
    # 2. suffix-strip (muromonab-cd3 -> muromonab)
    stem = re.sub(r"-[a-z0-9]{2,5}$", "", name.lower())
    if stem != name.lower():
        r = idx.get(norm(stem))
        if r:
            return row_to_result(name, r, f"suffix-strip:{stem}")
    # 3. cocktail split
    parts = [p for p in name.lower().split("-") if p]
    if len(parts) >= 2 and all(
        re.search(r"(mab|cept)$", p) or len(p) >= 6 for p in parts
    ):
        comps, all_found = [], True
        for p in parts:
            r = idx.get(norm(p))
            if r:
                comps.append(row_to_result(p, r, "cocktail-component"))
            else:
                all_found = False
                comps.append({"query": p, "found": False})
        if any(c.get("found") for c in comps):
            return {
                "query": name,
                "found": True,
                "match_kind": "cocktail-split" + ("" if all_found else "-partial"),
                "components": comps,
                "source": "Thera-SAbDab",
            }
        return {
            "query": name,
            "found": False,
            "match_kind": "cocktail-split-all-miss",
            "components": comps,
        }
    return {"query": name, "found": False}


def main():
    args = sys.argv[1:]
    mirror = DEFAULT_MIRROR
    if "--mirror" in args:
        i = args.index("--mirror")
        mirror = args[i + 1]
        del args[i : i + 2]
    if not args:
        print(__doc__)
        sys.exit(1)
    if not os.path.exists(mirror):
        print(json.dumps({
            "error": f"mirror not found: {mirror}",
            "hint": "run from the brain root, or pass --mirror PATH",
        }))
        sys.exit(2)
    _, idx = build_index(mirror)
    out = [lookup(n, idx) for n in args]
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
