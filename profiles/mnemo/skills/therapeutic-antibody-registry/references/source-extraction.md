# Registry source extraction

Load when fetching/parsing the Antibody Society table or an ATW annual review.
Keep the response URL, retrieval date, raw text, and row/table identifiers.
Inspect Content-Type and actual bytes before parsing; challenge HTML is not a
source table or XML. Binary sources use the archive convention named in the
umbrella, not Git. Do not infer format from the URL extension alone.

## Antibody Society table

Fetch `https://www.antibodysociety.org/resources/approved-antibodies/` with a
User-Agent and bounded timeout. Inspect the current headers and footnotes;
do not assume one table, fixed column order, or a fixed row count. This small
parser handles simple HTML tables with `th` or `td` cells; merged/nested cells
need source-aware extraction rather than flattening them into wrong columns.

```python
import html
import re

def approved_table(html_text):
    def text(cell):
        cell = re.sub(r"<br\s*/?>", " ", cell, flags=re.I)
        return " ".join(html.unescape(re.sub(r"<[^>]+>", "", cell)).split())
    matches = []
    for table in re.findall(r"<table\b[^>]*>(.*?)</table>", html_text, re.I | re.S):
        rows = [[text(c) for c in re.findall(
            r"<t[dh]\b[^>]*>(.*?)</t[dh]>", row, re.I | re.S)]
            for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", table, re.I | re.S)]
        rows = [r for r in rows if r and any(r)]
        if not rows or rows[0][0].casefold() != "inn":
            continue
        if re.search(r"\b(?:rowspan|colspan)\s*=|<table\b", table, re.I):
            raise ValueError("merged/nested table: inspect source layout")
        headers, data = rows[0], rows[1:]
        if not data or any(len(r) != len(headers) for r in data):
            raise ValueError("empty or irregular source table")
        matches.append({"headers": headers, "rows": data})
    if len(matches) != 1:
        raise ValueError("expected one identifiable INN table; inspect source")
    return matches[0]
```

The returned `headers` are separate from `rows`; the first data row must not
be dropped as another header. Map the observed labels (INN, brand, target/format,
indication, regional approval/review) before writing entries. Whitespace cleanup
is for display/matching only; retain raw source names and annotations.

Interpret approval annotations against that capture's legend. The checked
source legend defines `*` as country-specific approval, not continued approval;
`#` means withdrawn or marketing discontinued for the first approved indication,
not necessarily withdrawal of the whole product. `NA` also carries region-specific
limits on review-status information. Preserve these qualifications. A cell such
as `2017; 2000#` retains both reapproval and withdrawal history. Check both
regions and dates rather than letting one `#` override a current approval.
The table alone does not enumerate all in-scope products; check regulatory/
official sources for missing modalities and regions.

## Antibodies to watch: PMID to PMCID

Resolve the desired annual article from a source-backed citation. Validate the
literal PMID before lookup, query the MED namespace explicitly, and confirm
the returned article title/identity. This example accepts digit-only PMID
strings and canonical `PMC`-prefixed PMCIDs; it does not strip prefixes,
spaces, punctuation, or a duplicated `PMC` to make a malformed token pass.
A supplied malformed identifier requires source correction, not normalization.

```python
import json
import re
import urllib.parse
import urllib.request

def atw_record(pmid, expected_title):
    if not isinstance(pmid, str) or not re.fullmatch(r"[1-9][0-9]*", pmid):
        raise ValueError("PMID must be a literal positive digit string")
    params = urllib.parse.urlencode({
        "query": f"EXT_ID:{pmid} AND SRC:MED",
        "format": "json", "resultType": "core"})
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + params
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.load(response)
    hits = [h for h in data.get("resultList", {}).get("result", [])
            if h.get("source") == "MED" and h.get("id") == pmid]
    if len(hits) != 1:
        raise ValueError("missing or ambiguous MED record")
    hit = hits[0]
    if hit.get("pmid") not in (None, pmid):
        raise ValueError("returned PMID disagrees")
    if " ".join(hit.get("title", "").split()).casefold() != " ".join(expected_title.split()).casefold():
        raise ValueError("title mismatch: inspect article identity")
    pmcid = hit.get("pmcid")
    if not isinstance(pmcid, str) or not re.fullmatch(r"PMC[1-9][0-9]*", pmcid):
        raise ValueError("missing or malformed PMCID; do not guess a prefix")
    return hit, f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
```

Title punctuation can trigger this conservative check (EPMC may add a terminal
period absent from XML). Inspect the intended citation and returned record before
changing `expected_title`; do not change identifiers to make a match pass.
Use the returned PMCID unchanged. Never derive it from the PMID or blindly
prepend `PMC`. Missing XML or PMCID is a retrieval gap, not an empty census.
After fetching, check the article's front-matter IDs/title against the resolved
record and parse XML natively:

```python
import xml.etree.ElementTree as ET
root = ET.fromstring(xml_text)
tables = root.findall(".//table-wrap")
for table in tables:
    caption = " ".join(table.findtext("label", "").split())
    caption += " " + " ".join(table.find("caption").itertext()) if table.find("caption") is not None else ""
    rows = [[" ".join(cell.itertext()).strip() for cell in row if cell.tag in {"td", "th"}]
            for row in table.findall(".//tr")]
    print(table.get("id"), caption, rows)
```

Identify approval, regulatory-review, and clinical tables by captions and
source dates, not table position, ID pattern, or an assumed number of tables.
Inspect merged cells and footnotes before assigning fields; the snippet exposes
cell text, not a reconstructed rowspan/colspan grid. Keep the source row and
caption with the extracted data so tier/status decisions remain checkable.
