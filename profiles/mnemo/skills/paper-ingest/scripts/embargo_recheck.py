#!/usr/bin/env python3
"""embargo_recheck.py — re-test needs-enrichment paper pages for newly available full text.

Monthly sweep (cron). For every papers/*.md page with `needs-enrichment: true`,
queries the Europe PMC REST gate and reports pages whose full text has likely
become available since ingest:

  new-pmcid   — the page carries no pmcid, but Europe PMC now reports one
                (NIH public-access deposit landed after ingest)
  oa-flipped  — the page's pmcid now shows isOpenAccess=Y (embargo lifted)

Silent when nothing has flipped (watchdog pattern). Enrichment itself is NOT
performed here — the output is a work list for an ingest-pending-papers or
paper-ingest run, which will re-verify via fetch_fulltext.py.

Stdlib only. Rate-limited to ~2 req/s out of courtesy to EBI.
"""

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

VAULT = Path(__file__).resolve().parents[3]
UA = "mnemo-embargo-recheck/1.0"
SLEEP = 0.4

FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)


def parse_frontmatter(text):
    m = FM_RE.match(text)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^([a-z0-9_-]+):\s*(.*)$", line)
        if kv:
            fm[kv.group(1)] = kv.group(2).strip().strip('"').strip("'")
    return fm


def epmc_gate(pmid=None, doi=None):
    if pmid:
        q = "EXT_ID:%s" % pmid
    else:
        q = 'DOI:"%s"' % doi
    url = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=%s"
           "&resultType=core&format=json" % urllib.parse.quote(q))
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            res = json.load(r).get("resultList", {}).get("result", [])
        return res[0] if res else {}
    except Exception:
        return None  # transient failure — skip silently


def main():
    papers = sorted((VAULT / "papers").glob("*.md"))
    flipped = []
    checked = 0
    for path in papers:
        try:
            fm = parse_frontmatter(path.read_text())
        except Exception:
            continue
        if fm.get("needs-enrichment") != "true":
            continue
        pmid = fm.get("pmid") or None
        doi = fm.get("doi") or None
        if doi in ("null", "none", ""):
            doi = None
        if pmid in ("null", "none", ""):
            pmid = None
        if not pmid and not doi:
            continue
        gate = epmc_gate(pmid=pmid, doi=doi)
        checked += 1
        time.sleep(SLEEP)
        if gate is None or not gate:
            continue
        page_pmcid = fm.get("pmcid") or None
        if page_pmcid in ("null", "none", ""):
            page_pmcid = None
        gate_pmcid = gate.get("pmcid") or None
        rel = "papers/" + path.name
        if gate_pmcid and not page_pmcid:
            flipped.append((rel, "new-pmcid", gate_pmcid))
        elif page_pmcid and gate.get("isOpenAccess") == "Y":
            flipped.append((rel, "oa-flipped", page_pmcid))

    if not flipped:
        return  # silent — watchdog pattern
    print("embargo re-check: %d of %d needs-enrichment papers now have full text available"
          % (len(flipped), checked))
    print("re-enrich via paper-ingest (fetch_fulltext.py will re-verify):\n")
    for rel, reason, pmcid in flipped:
        print("  %-60s %-10s %s" % (rel, reason, pmcid))


if __name__ == "__main__":
    main()
