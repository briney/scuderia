#!/usr/bin/env python3
"""google_patents_lookup.py — US patent candidate search via the Google
Patents XHR JSON endpoint (no API key required).

    python3 google_patents_lookup.py NAME [--assignee X] [--claims] [--all] [--max N]

Modes:
  default:  q=NAME (+assignee)          — recall net (full-text)
  --claims: q=CL=(NAME) (+assignee)     — precision set (claims only)
  --all:    run both and merge

US-only: results are filtered to publication numbers starting with US
(PatentsView needs a key; EPO OPS needs credentials — v1 is US-only).

Expiry is ESTIMATED, never actual: filing + 20y; for pre-GATT filings
(before 1995-06-08), the later of filing+20y and grant+17y. Output carries
expiry_basis per row — `estimated-20y` | `estimated-gatt-transition`.
Applications without a grant date get `estimated-20y` and grant= null.

Output: JSON array of candidates.
"""
import datetime as dt
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

XHR = "https://patents.google.com/xhr/query"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Safari/537.36"}
GATT = dt.date(1995, 6, 8)


def fetch_json(url, tries=4):
    """GET with backoff — Google rate-limits bursts with bare 503s."""
    import time
    for attempt in range(tries):
        req = urllib.request.Request(url, headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < tries - 1:
                time.sleep(5 * (attempt + 1))
                continue
            raise
    raise RuntimeError(f"fetch failed after {tries} tries: {url}")


def strip_html(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


def parse_date(s):
    try:
        return dt.date.fromisoformat(s)
    except (TypeError, ValueError):
        return None


def estimate_expiry(filing, grant):
    f, g = parse_date(filing), parse_date(grant)
    if not f:
        return None, "unestimated (no filing date)"
    twenty = f.replace(year=f.year + 20)
    if f < GATT and g:
        seventeen = g.replace(year=g.year + 17)
        if seventeen > twenty:
            return seventeen.isoformat(), "estimated-gatt-transition"
    return twenty.isoformat(), "estimated-20y"


def query(name, assignee=None, claims=False, max_pages=1):
    q = f"CL=({name})" if claims else name
    params = f"q={urllib.parse.quote(q)}"
    if assignee:
        params += f"&assignee={urllib.parse.quote(assignee)}"
    url = f"{XHR}?url={params}&exp="
    out = []
    for page in range(max_pages):
        page_url = url + (f"&page={page}" if page else "")
        data = fetch_json(page_url)
        results = data.get("results", {})
        for cluster in results.get("cluster", []):
            for r in cluster.get("result", []):
                p = r.get("patent", {})
                pub = p.get("publication_number", "")
                if not pub.startswith("US"):
                    continue
                est, basis = estimate_expiry(p.get("filing_date"), p.get("grant_date"))
                out.append({
                    "publication_number": pub,
                    "kind": "grant" if re.search(r"B[12]$", pub) else "application",
                    "title": strip_html(p.get("title")),
                    "assignee": strip_html(p.get("assignee")),
                    "inventor": strip_html(p.get("inventor")),
                    "priority_date": p.get("priority_date"),
                    "filing_date": p.get("filing_date"),
                    "grant_date": p.get("grant_date") or None,
                    "estimated_expiry": est,
                    "expiry_basis": basis,
                    "query_mode": "claims" if claims else "fulltext",
                    "url": f"https://patents.google.com/patent/{pub}/en",
                })
        if results.get("num_page", 0) >= results.get("total_num_pages", 1) - 1:
            break
    return out


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    name, assignee, claims, allm = args[0], None, False, False
    max_pages = 1
    i = 1
    while i < len(args):
        if args[i] == "--assignee":
            assignee = args[i + 1]; i += 2
        elif args[i] == "--claims":
            claims = True; i += 1
        elif args[i] == "--all":
            allm = True; i += 1
        elif args[i] == "--max":
            max_pages = int(args[i + 1]); i += 2
        else:
            i += 1
    if allm:
        hits = query(name, assignee, False, max_pages) + query(name, assignee, True, max_pages)
    else:
        hits = query(name, assignee, claims, max_pages)
    seen, out = set(), []
    for h in hits:
        if h["publication_number"] in seen:
            continue
        seen.add(h["publication_number"])
        out.append(h)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
