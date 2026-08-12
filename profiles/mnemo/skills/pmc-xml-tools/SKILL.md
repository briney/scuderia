---
name: pmc-xml-tools
description: "Fix PMC XML ParseErrors and extract body text."
triggers:
  - "PMC XML ParseError"
  - "ElementTree not well-formed PMC"
  - "efetch.fcgi XML parsing"
  - "PMC XML entity fixing"
  - "pmc_xml_body_parser"
  - "PMC XML body extraction"
  - "PMC XML references"
  - "PMC XML no back tag"
  - "NIHMS body references delimiter"
---

# PMC XML entity-fixing and body-text extraction

Reference companion to the `paper-ingest`
vault skill. Covers the **recurring PMC XML parse failure** and the reusable
parser script that handles it.

## The problem

PMC XML returned by `efetch.fcgi?db=pmc` **frequently** breaks
`xml.etree.ElementTree.fromstring()` / `ET.parse()` with:

```
xml.etree.ElementTree.ParseError: not well-formed (invalid token): line 1, column NNNN
```

This is **publisher-dependent**, not universal. Root causes when it occurs:

1. **`<!DOCTYPE>` declaration** referencing an external DTD that ElementTree
   cannot resolve.
2. **Undefined HTML entities** (`&alpha;`, `&beta;`, `&deg;`, `&times;`, etc.)
   that are not declared in any DTD ElementTree knows about.
3. **Raw `&` in attribute values** (e.g. `vocab="credit"` → `&credit;`
   looks like an entity reference to the parser).

**Publishers observed to produce clean XML (no sanitization needed):**
MDPI (e.g., Denysenko 2025, PMC12371982, 137KB — `ET.parse()` succeeded
on first try).

**Publishers observed to require sanitization:** Frontiers, some Wiley/Elsevier
deposits, ATS Journals/OUP (which also restrict full-text XML download entirely).

The parser script tries `ET.parse()` first and only sanitizes on failure,
so it works for both clean and entity-laden XML.

## The fix — sanitize before parsing (only when direct parse fails)

Three-step sanitization, applied in order:

```python
import re, xml.etree.ElementTree as ET

with open(xml_path, 'r', encoding='utf-8', errors='replace') as f:
    xml_text = f.read()

# 1. Remove DOCTYPE
xml_text = re.sub(r'<!DOCTYPE[^>]*>', '', xml_text)

# 2. Replace common HTML entities with Unicode
entity_map = {
    '&alpha;': 'α', '&beta;': 'β', '&gamma;': 'γ', '&delta;': 'δ',
    '&epsilon;': 'ε', '&mu;': 'μ', '&deg;': '°', '&times;': '×',
    '&le;': '≤', '&ge;': '≥', '&plusmn;': '±', '&sim;': '∼',
    '&rarr;': '→', '&ndash;': '–', '&mdash;': '—',
    '&lsquo;': '\u2018', '&rsquo;': '\u2019',
    '&ldquo;': '\u201c', '&rdquo;': '\u201d',
    '&nbsp;': ' ',
}
for entity, char in entity_map.items():
    xml_text = xml_text.replace(entity, char)

# 3. Escape remaining bare & (not part of a valid XML entity)
xml_text = re.sub(
    r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)',
    '&amp;', xml_text
)

# 4. Parse
root = ET.fromstring(xml_text)
```

## The parser script

`scripts/pmc_xml_body_parser.py` — handles sanitization + section/paragraph
extraction + pagination + reference extraction in one invocation. Tries
direct `ET.parse()` first, falls back to sanitization only on ParseError.

```bash
# Step 1: download (curl -o, no pipe — tirith-safe)
curl -sL "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=<PMCID>&rettype=xml" -o /tmp/paper.xml

# Step 2: parse body text (first 15K chars by default)
python3 scripts/pmc_xml_body_parser.py /tmp/paper.xml

# Paginate
python3 scripts/pmc_xml_body_parser.py /tmp/paper.xml --range 15000 30000

# Full output
python3 scripts/pmc_xml_body_parser.py /tmp/paper.xml --full

# References only (for Phase 7 bibliography walk)
python3 scripts/pmc_xml_body_parser.py /tmp/paper.xml --refs
```

The `--refs` mode extracts the `<ref-list>` with authors, title, DOI,
year, and journal — useful for Phase 7 bibliography walks without separate
inline parsing.

## Inline parsing fallback (when script not available)

When `scripts/pmc_xml_body_parser.py` is not available, use this stdlib-only
inline pattern. For PubMed XML (metadata), direct `ET.parse()` works without
sanitization. For PMC XML (body text), try `ET.parse()` first, sanitize on
failure.

```python
import xml.etree.ElementTree as ET

# PubMed XML — metadata extraction (Phase 1)
tree = ET.parse('/tmp/pubmed.xml')
root = tree.getroot()
art = root.find('.//PubmedArticle/MedlineCitation/Article')

# Title, journal, year, DOI, PMCID, PMID, pubtypes
title = art.findtext('.//ArticleTitle')
journal = art.findtext('.//Journal/Title')
year = art.findtext('.//Journal/JournalIssue/PubDate/Year')
for el in art.findall('.//ELocationID'):
    if el.get('EIdType') == 'doi': doi = el.text
for artid in root.findall('.//PubmedData/ArticleIdList/ArticleId'):
    if artid.get('IdType') == 'pmc': pmcid = artid.text
    if artid.get('IdType') == 'pubmed': pmid = artid.text

# Authors with ORCIDs and affiliations
for au in art.findall('.//AuthorList/Author'):
    ln = au.findtext('LastName','')
    fn = au.findtext('ForeName','')
    orcid = ''
    for id in au.findall('.//Identifier'):
        if id.get('Source') == 'ORCID': orcid = id.text
    aff = au.findtext('.//AffiliationInfo/Affiliation','')

# Full abstract (all labeled sections)
for ab in art.findall('.//Abstract/AbstractText'):
    label = ab.get('Label','')
    text = ''.join(ab.itertext())

# PMC XML — body text extraction (Phase 4)
body = root.find('.//body')
def extract_text(elem):
    texts = []
    tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
    if tag == 'sec':
        title = elem.find('.//title')
        if title is not None and title.text:
            texts.append(f"\n## {title.text.strip()}\n")
    elif tag == 'p':
        text = ''.join(elem.itertext()).strip()
        if text: texts.append(text + "\n")
    for child in elem:
        texts.extend(extract_text(child))
    return texts

# PMC XML — reference extraction (Phase 7)
ref_list = root.find('.//ref-list')
for i, ref in enumerate(ref_list.findall('.//ref'), 1):
    citation = ref.find('.//element-citation') or ref.find('.//mixed-citation')
    if citation is not None:
        doi = None
        for el in citation.findall('.//pub-id'):
            if el.get('pub-id-type') == 'doi': doi = el.text
        title = citation.findtext('.//article-title') or citation.findtext('.//source')
        authors = [f"{au.findtext('given','')} {au.findtext('surname','')}" for au in citation.findall('.//name')]
        year = citation.findtext('.//year','')
        source = citation.findtext('.//source','')
```

## Pitfall: terminal stdout truncation vs file size

The Hermes `terminal` tool truncates stdout at 50KB. PMC XML files range
from 50KB to 230KB+. When using `execute_code`'s `terminal()`, the returned
`output` is truncated — but `curl -o file` writes the full content to disk.
**Always** use `curl -o /tmp/file.xml` and read/parse the file, never rely on
terminal stdout for the XML itself.

## Pitfall: NIHMS deposits with no `<back>` wrapper — body/references delimiter

Some PMC XML deposits (particularly NIHMS manuscripts) have **no `<back>`
element** and **no `<ref-list>` wrapper** around the references. The
references (`<ref id="R1">`, `<ref id="R2">`, ...) sit directly in the
body region or immediately after the body sections with no structural
delimiter. A body-extraction strategy that slices `xml[body_start:back_start]`
will grab the entire rest of the document (references + floats-group)
when `back_start` returns -1.

**The fix:** When `xml.find('<back>')` returns -1, fall back to finding
the **first `<ref id=` element** after `<body>` — that is the reliable
delimiter between body content and references:

```python
body_start = xml.find('<body>')
ref_start = xml.find('<ref id=', body_start)
if ref_start < 0:
    ref_start = xml.find('<floats-group', body_start)  # figures come after refs
body = xml[body_start + len('<body>'):ref_start]
```

Also check for `<floats-group>` as a secondary delimiter — figure
captions in the floats-group can contain `<p>` and `<title>` tags that
would pollute the body extraction if included.

**Observed instance (2026-08-05, Frasca 2020, PMCID PMC7371527):** The
NIHMS deposit had `<body>` but no `<back>` or `<ref-list>`. References
(174 entries) sat directly after the body sections. The initial
`xml[body_start:back_start]` slice (with `back_start = -1`) grabbed
49,906 chars including all references, polluting the body extraction
with citation text. Fix: slice to `xml.find('<ref id=', body_start)` —
body content was 13,018 chars, cleanly separated from references.

## When to use `lxml` instead

If `lxml` is available, `lxml.etree.XMLParser(recover=True)` handles
malformed XML without manual entity-fixing. But `lxml` is **not installed**
in the default Hermes Python environment. Prefer the stdlib sanitization
approach unless lxml is confirmed available.

## Session evidence

| Date | Paper | PMCID | XML size | ParseError? | Fix |
|------|-------|-------|----------|-------------|-----|
| 2026-07-17 | Tan 2018 | PMC6935424 | ~100KB | Yes | Entity replacement |
| 2026-07-25 | Leem 2022 | PMC9278498 | 128KB | Yes | Entity replacement |
| 2026-07-27 | Molinos-Albert 2025 | PMC12057666 | 229KB | Yes (line 1, col 4363) | Full 3-step sanitization |
| 2026-07-30 | Denysenko 2025 | PMC12371982 | 137KB | **No** (MDPI = clean XML) | Direct `ET.parse()` worked |
| 2026-08-05 | Frasca 2020 | PMC7371527 | 50KB | **No** (Wiley NIHMS = clean XML) | No `<back>` — slice to `<ref id=` |
