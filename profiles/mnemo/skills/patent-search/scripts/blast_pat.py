#!/usr/bin/env python3
"""blast_pat.py — sequence -> US patent candidates via NCBI BLAST against the
patent protein database (pataa). This is the high-precision
composition-of-matter signal: a patent whose sequence listing contains the
antibody's VH/VL is a CoM candidate, including pre-INN filings that name
search can never find (the INN did not exist yet).

    python3 blast_pat.py SEQ [--program blastp] [--max-hits 20] [--poll 30]

Flow (NCBI URL API, no key):
  1. PUT CMD=Put&PROGRAM=blastp&DATABASE=pataa&QUERY=<seq> -> RID (+RTOE est.)
  2. Poll CMD=Get&FORMAT_OBJECT=SearchInfo&RID=... every --poll seconds
  3. CMD=Get&FORMAT_TYPE=Tabular (comment lines carry hit accessions/titles)
  4. Patent protein record titles look like "Sequence 12 from patent US 6407213"
     — extract the US publication numbers from hit titles directly.

Runtime is minutes (queued public service). Do not run in a tight loop;
NCBI asks for >=3 s between polls and off-peak consideration. One sequence
per invocation.

Output: JSON {rid, hits: [{accession, title, identity, patent_numbers}]}
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request

BLAST = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"


def http_get(params, timeout=90):
    url = BLAST + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def submit(seq, program):
    html = http_get({"CMD": "Put", "PROGRAM": program, "DATABASE": "pataa",
                     "QUERY": seq}, timeout=120)
    rid = re.search(r"RID = ([A-Z0-9]+)", html)
    rtoe = re.search(r"RTOE = (\d+)", html)
    if not rid:
        raise RuntimeError("BLAST PUT failed: no RID in response")
    return rid.group(1), int(rtoe.group(1)) if rtoe else 300


def wait_ready(rid, poll):
    while True:
        time.sleep(poll)
        info = http_get({"CMD": "Get", "FORMAT_OBJECT": "SearchInfo", "RID": rid})
        m = re.search(r"Status=(\w+)", info)
        status = m.group(1) if m else "UNKNOWN"
        if status == "READY":
            if "ThereAreHits=no" in info:
                return False
            return True
        if status in ("FAILED", "UNKNOWN", "EXPIRED"):
            raise RuntimeError(f"BLAST search {status}")


def fetch_hits(rid, max_hits):
    text = http_get({"CMD": "Get", "FORMAT_TYPE": "Tabular", "RID": rid,
                     "ALIGNMENTS": str(max_hits), "DESCRIPTIONS": str(max_hits)},
                    timeout=180)
    hits = []
    for line in text.splitlines():
        # tabular-with-comments: description lines start with '# ' and list hits
        m = re.match(r"#\s+(\S+)\s+(.*?)\s*$", line)
        if not m or "acc.ver" in line.lower():
            continue
        acc, title = m.group(1), m.group(2)
        pats = sorted(set(re.findall(
            r"patent\s+(?:WO|US|EP)?\s*([A-Z]{2}\s?\d{5,}[A-Z0-9]*)", title, re.I)))
        hits.append({"accession": acc, "title": title.strip(),
                     "patent_numbers": [p.replace(" ", "") for p in pats]})
        if len(hits) >= max_hits:
            break
    return hits


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    seq = args[0]
    program, max_hits, poll = "blastp", 20, 30
    i = 1
    while i < len(args):
        if args[i] == "--program":
            program = args[i + 1]; i += 2
        elif args[i] == "--max-hits":
            max_hits = int(args[i + 1]); i += 2
        elif args[i] == "--poll":
            poll = int(args[i + 1]); i += 2
        else:
            i += 1
    rid, rtoe = submit(seq, program)
    print(json.dumps({"rid": rid, "rtoe_estimate_s": rtoe, "status": "submitted"}),
          file=sys.stderr)
    has_hits = wait_ready(rid, poll)
    hits = fetch_hits(rid, max_hits) if has_hits else []
    patents = sorted({p for h in hits for p in h["patent_numbers"]})
    print(json.dumps({"rid": rid, "hits": hits,
                      "us_patent_candidates": [p for p in patents if p.startswith("US")],
                      "all_patent_candidates": patents}, indent=2))


if __name__ == "__main__":
    main()
