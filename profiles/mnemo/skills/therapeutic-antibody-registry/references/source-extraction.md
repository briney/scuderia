# Source extraction patterns for therapeutic-antibody-registry

Proven patterns for fetching and parsing the Tier A source data, validated
during the 2026-08-18 pilot batch (27 entries).

## 1. Antibody Society approved-antibody table

**URL**: `https://www.antibodysociety.org/resources/approved-antibodies/`

**Format**: HTML with one `<table>` element. 168 data rows + 1 header row.

**Scrape pattern** (Python urllib + regex):

```python
import urllib.request, re, html as html_mod, json

def fetch_and_parse():
    url = "https://www.antibodysociety.org/resources/approved-antibodies/"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        html_text = r.read().decode("utf-8", errors="replace")

    table_match = re.search(r'<table[^>]*>(.*?)</table>', html_text, re.DOTALL)
    table_html = table_match.group(0)

    tr_list = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
    rows = []
    for tr in tr_list:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', tr, re.DOTALL)
        cells = [html_mod.unescape(re.sub(r'<[^>]+>', '', c)).strip() for c in cells]
        if cells and any(cells):
            rows.append(cells)

    headers = rows[0]  # ['INN', 'Brand name', 'Target; Format', ...]
    data = rows[1:]
    return {"headers": headers, "rows": data}
```

**Columns**: INN, Brand name, "Target; Format" (semicolon-separated), 1st
indication approved/reviewed, 1st EU approval year, 1st US approval year.

**Approval year annotations**:
- `NA` = not approved in that region
- `*` = still approved
- `#` = withdrawn (e.g., `2000#` = approved 2000, later withdrawn)
- `2017;\n2000#` = originally approved 2000, withdrawn, re-approved 2017
- `Review` = filed/under review
- Newlines embedded in some INNs (e.g., `Gemtuzumab\nozogamicin`)

**Scope**: mAbs only. Does NOT include Fc-fusions (etanercept, aflibercept),
CAR-T products (tisagenlecleucel), or radioimmunoconjugates. Source those
separately from Purple Book / EMA EPAR / FDA labels.

## 2. "Antibodies to watch" annual series (Europe PMC)

**Lookup by PMID** to get PMCID:
```python
search_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={pmid}&format=json&resultType=core"
```

**Full text XML**:
```python
xml_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/PMC{pmcid}/fullTextXML"
```

**Parse 4 table-wrap elements**:
```python
tables = re.findall(r'<table-wrap[^>]*id="(t[^"]*)"[^>]*>(.*?)</table-wrap>', xml, re.DOTALL)
```

**ATW 2026 tables**: Table 1 (first approvals, ~20 rows), Table 2 (regulatory
review, ~27 rows), Table 3 (late-stage non-cancer, ~17 rows), Table 4
(late-stage cancer, ~6 rows).

**Known PMID list**: 41560619 (2026), 39711140 (2025), 38178784 (2024).
See antibody-target-hitlist skill's references/atw-series.md for full list.

## 3. Source probing (format check)

Always probe Content-Type before assuming text vs binary:

```python
def probe(name, url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        ct = r.headers.get("Content-Type", "")
        print(f"[{name}] {r.status} {ct}")
```

**Pilot results (2026-08-18)**: All sources returned text/HTML. No R2
archival needed for Tier A. This can change — always probe.
