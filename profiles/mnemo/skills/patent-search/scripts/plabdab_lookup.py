#!/usr/bin/env python3
"""plabdab_lookup.py — query the local PLAbDab paired-sequences mirror.

Modes:
  python3 plabdab_lookup.py --vh SEQ [--vl SEQ] [--max N] [--resolve K]
  python3 plabdab_lookup.py --keyword TERM [--max N]

Sequence mode is exact-match on heavy_sequence / light_sequence against the
paired mirror (for fuzzy / CDR-region search, use the full PLAbDab package —
see the patent-search skill). When both --vh and --vl are given, hits are
split into PAIRED (both chains match in the same row) and heavy-only.

--resolve K maps up to K hit accessions to source patent numbers via NCBI
E-utilities efetch (db=protein) — PLAbDab IDs are GenBank patent-division
accessions whose record titles read "Sequence N from patent US ...".
Polite: one batched efetch call, no API key.

Output: JSON {vh_hits, paired_hits, keyword_hits, resolved, mirror_rows}.
"""
import csv
import gzip
import json
import os
import re
import sys
import urllib.parse
import urllib.request

DEFAULT_MIRROR = os.path.join(
    "references", "therapeutic-antibodies", "raw", "mirrors",
    "plabdab_paired_sequences.csv.gz",
)
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def load(path):
    with gzip.open(path, "rt") as f:
        return list(csv.DictReader(f))


def slim(r):
    return {"id": r["ID"], "reference_title": (r.get("reference_title") or "").strip(),
            "update_date": r.get("update_date"),
            "targets_mentioned": (r.get("targets_mentioned") or "").strip() or None,
            "organism": (r.get("organism") or "").strip() or None}


# PLAbDab ID space is mixed: GenBank patent-division accessions (ABH71318,
# QFN55342), PDB instance IDs (6BI2_I_M), and literature names (Anbenitamab_2).
# Only accession-shaped IDs resolve to patent numbers via NCBI.
ACCESSION_SHAPE = re.compile(r"^[A-Z]{2,3}\d{5,8}(\.\d)?$")


def resolve_patents(accessions):
    """Batch-resolve accessions -> patent numbers via NCBI efetch."""
    if not accessions:
        return {}
    params = {"db": "protein", "id": ",".join(accessions), "rettype": "gb",
              "retmode": "text", "tool": "patent-search-skill",
              "email": "atticus@localhost"}
    url = EFETCH + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=120) as resp:
        text = resp.read().decode("utf-8", "replace")
    out = {}
    # split records; each starts with LOCUS <acc>
    for chunk in re.split(r"\n//\n", text):
        m_acc = re.search(r"^LOCUS\s+(\S+)", chunk, re.M)
        m_pat = re.search(r"[Ss]equence\s+\d+\s+from\s+patent\s+([A-Z]{2})\s*(\d[\d,\s]*[A-Z0-9]*)", chunk)
        if m_acc and m_pat:
            num = re.sub(r"[,\s]", "", m_pat.group(2))
            out[m_acc.group(1)] = m_pat.group(1) + num
    return out


def main():
    args = sys.argv[1:]
    mirror = DEFAULT_MIRROR
    vh = vl = keyword = None
    max_n, resolve_k = 50, 10
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--mirror":
            mirror = args[i + 1]; i += 2
        elif a == "--vh":
            vh = args[i + 1]; i += 2
        elif a == "--vl":
            vl = args[i + 1]; i += 2
        elif a == "--keyword":
            keyword = args[i + 1]; i += 2
        elif a == "--max":
            max_n = int(args[i + 1]); i += 2
        elif a == "--resolve":
            resolve_k = int(args[i + 1]); i += 2
        else:
            print(__doc__); sys.exit(1)
    if not os.path.exists(mirror):
        print(json.dumps({"error": f"mirror not found: {mirror}",
                          "hint": "run from the brain root, or pass --mirror PATH"}))
        sys.exit(2)
    rows = load(mirror)
    out: dict = {"mirror_rows": len(rows)}

    hits = []
    if vh or vl:
        vh_hits = [r for r in rows if vh and r["heavy_sequence"] == vh]
        if vl:
            paired = [r for r in vh_hits if r["light_sequence"] == vl]
            out["paired_hits"] = [slim(r) for r in paired[:max_n]]
            out["paired_count"] = len(paired)
        out["vh_hits"] = [slim(r) for r in vh_hits[:max_n]]
        out["vh_count"] = len(vh_hits)
        hits = vh_hits
    if keyword:
        kw = keyword.lower()
        khits = [r for r in rows
                 if kw in ((r.get("reference_title") or "") + " "
                           + (r.get("targets_mentioned") or "")).lower()]
        out["keyword_hits"] = [slim(r) for r in khits[:max_n]]
        out["keyword_count"] = len(khits)
        hits = hits or khits

    if resolve_k and hits:
        # resolve most recent first (update_date desc), accession-shaped IDs
        # only — PDB/literature-name IDs don't resolve via NCBI
        def datekey(r):
            return r.get("update_date") or ""
        accs, seen = [], set()
        for r in sorted(hits, key=datekey, reverse=True):
            if r["ID"] not in seen and ACCESSION_SHAPE.match(r["ID"]):
                seen.add(r["ID"])
                accs.append(r["ID"])
            if len(accs) >= resolve_k:
                break
        try:
            out["resolved"] = resolve_patents(accs)
            out["resolved_note"] = (
                "only GenBank-accession-shaped PLAbDab IDs resolve; PDB and "
                "literature-name IDs are excluded from resolution")
        except Exception as e:
            out["resolve_error"] = str(e)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
