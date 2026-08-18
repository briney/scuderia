#!/usr/bin/env python3
"""sabdab_lookup.py — find structures for an antibody via the local SAbDab
summary mirror (name/compound match) and, optionally, the SAbDab
sequence-similarity API (catches structures deposited under code names).

Usage:
    python3 sabdab_lookup.py NAME [NAME ...] [--mirror PATH]
    python3 sabdab_lookup.py --vh SEQ [--vl SEQ] [--threshold N] [--region R]
    python3 sabdab_lookup.py --pdb 3wd5 [--mirror PATH]

Name mode matches NAME (case-insensitive, substring) against the mirror's
`compound` column — OR across multiple NAMEs. Sequence mode POSTs to the
SAbDab API (canonical host https://sabdab.opig.stats.ox.ac.uk — the
/webapps/ path 301-redirects and downgrades POST to GET) and resolves the
returned instance IDs against the mirror for full metadata.

Output: JSON {"name_hits": [...], "seq_hits": [...]} where each hit carries
pdb (bare 4-char id), instance, h_chain, l_chain, antigen_chains,
antigen_name, resolution, method, compound, date. Missing metadata is null.
"""
import csv
import json
import os
import re
import sys
import urllib.request

DEFAULT_MIRROR = os.path.join(
    "references", "therapeutic-antibodies", "raw", "mirrors",
    "SAbDab_all_summary.tsv",
)
API = "https://sabdab.opig.stats.ox.ac.uk/api/sequence-similarity-search"
MISSING = {"", "na", "none", "n/a", "nan"}


def bare_pdb(pdb_field: str) -> str:
    m = re.search(r"([0-9][a-z0-9]{3})$", pdb_field.lower())
    return m.group(1) if m else pdb_field


# Crystallization additives (haptens/ions/sugars) and chaperones are not
# therapeutic antigens. SAbDab records them in antigen_* columns anyway.
BIO_TOKENS = {"PROTEIN", "PEPTIDE", "NA", "DNA", "RNA", "NUCLEOTIDE"}
ARTIFACT_NAMES = re.compile(
    r"immunoglobulin g[- ]binding protein|maltose/maltodextrin-binding", re.I)


def classify_state(antigen_chain, antigen_type, antigen_name) -> str:
    if not antigen_chain:
        return "unliganded"
    tokens = set((antigen_type or "").upper().split("|")) - {"", "NA"}
    if not tokens:
        return "complex-untyped"  # older rows with no antigen_type annotation
    if tokens & BIO_TOKENS:
        if antigen_name and ARTIFACT_NAMES.search(antigen_name):
            return "complex-artifact"  # protein A / MBP chaperone — not an epitope
        return "complex"
    return "additive-only"  # hapten/ion/sugar crystallization additives


def clean(v: str):
    v = (v or "").strip()
    return None if v.lower() in MISSING else v


def row_to_hit(r, via: str):
    ag_chain = clean(r["antigen_chain"])
    return {
        "via": via,
        "pdb": bare_pdb(r["PDB"]),
        "instance": r["INSTANCE"],
        "h_chain": clean(r["Hchain"]),
        "l_chain": clean(r["Lchain"]),
        "antigen_chains": [c for c in (ag_chain or "").split(":") if c],
        "antigen_name": clean(r["antigen_name"]),
        "antigen_type": clean(r["antigen_type"]),
        "resolution": clean(r["resolution"]),
        "method": clean(r["method"]),
        "compound": clean(r["compound"]),
        "date": clean(r["date"]),
        "heavy_species": clean(r["heavy_species"]),
        "state": classify_state(ag_chain, clean(r["antigen_type"]), clean(r["antigen_name"])),
    }


def load_mirror(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def name_search(rows, names):
    pats = [n.lower() for n in names]
    hits = []
    for r in rows:
        comp = (r.get("compound") or "").lower()
        if any(p in comp for p in pats):
            hits.append(row_to_hit(r, "name"))
    return hits


def seq_search(vh, vl, threshold, region, n, rows):
    body = {"n": n, "threshold": threshold, "region": region}
    if vh:
        body["heavy_seq"] = vh
    if vl:
        body["light_seq"] = vl
    req = urllib.request.Request(
        API, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read())
    by_instance = {r["INSTANCE"]: r for r in rows}
    hits = []
    for h in data.get("results", []):
        inst = h.get("antibody_instance_id")
        r = by_instance.get(inst)
        if r:
            hit = row_to_hit(r, "sequence")
        else:
            hit = {"via": "sequence", "instance": inst, "pdb": bare_pdb(inst or ""),
                   "mirror_row": None}
        hit["identity"] = h.get("score")
        hits.append(hit)
    return hits, data.get("warning")


def main():
    args = sys.argv[1:]
    mirror = DEFAULT_MIRROR
    vh = vl = region = pdb = None
    threshold, n = 90, 50
    names = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--mirror":
            mirror = args[i + 1]; i += 2
        elif a == "--vh":
            vh = args[i + 1]; i += 2
        elif a == "--vl":
            vl = args[i + 1]; i += 2
        elif a == "--threshold":
            threshold = float(args[i + 1]); i += 2
        elif a == "--region":
            region = args[i + 1]; i += 2
        elif a == "--pdb":
            pdb = args[i + 1]; i += 2
        elif a == "--n":
            n = int(args[i + 1]); i += 2
        else:
            names.append(a); i += 1
    if not os.path.exists(mirror):
        print(json.dumps({"error": f"mirror not found: {mirror}",
                          "hint": "run from the brain root, or pass --mirror PATH"}))
        sys.exit(2)
    rows = load_mirror(mirror)
    out: dict = {"name_hits": [], "seq_hits": []}
    if pdb:
        out["name_hits"] = [row_to_hit(r, "pdb") for r in rows
                            if bare_pdb(r["PDB"]) == pdb.lower()]
    elif names:
        out["name_hits"] = name_search(rows, names)
    if vh or vl:
        if not region:
            region = "Full variable region" if (vh and vl) else ("VH" if vh else "VL")
        try:
            out["seq_hits"], out["seq_warning"] = seq_search(
                vh, vl, threshold, region, n, rows)
        except Exception as e:
            out["seq_error"] = str(e)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
