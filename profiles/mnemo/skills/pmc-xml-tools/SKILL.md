---
name: pmc-xml-tools
description: "Use when PMC XML parsing or content extraction needs repair."
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
eval_contract:
  goal: Extract source-faithful PMC content and diagnose omissions without changing originals.
  dimensions:
    - "FIDELITY — body, references, tables, and captions retain source attribution and limitations"
    - "REPAIR — diagnosed changes are made to a derived copy and checked against the original"
  hard_fails:
    - Claiming the helper sanitizes XML or supports a nonexistent reference flag.
    - Accepting incomplete or repaired content without source read-back.
---

# PMC XML repair and extraction

Load when PMC XML cannot be parsed, or when body extraction omits references,
tables, or captions. PubMed identity-field parsing belongs to paper-ingest's
`references/pubmed-pmc-retrieval.md`; do not parse a PubMed root as PMC body XML.

## Existing parser contract

The helper is owned by paper-ingest at
`skills/paper-ingest/scripts/pmc_xml_body_parser.py`. Invoke it with an XML
filename and `--full` or `--range START END`; default output is only the
first 15,000 characters. There is no `--refs` mode and no sanitization.
It calls `fetch_fulltext.pmc_xml_to_text`, which uses `ET.fromstring` and
returns empty on ParseError or missing body. Its successful exit is not
proof that full text was extracted. It emits sections, paragraphs, and some
captions, not table cells or a complete reference list; floats outside body
can be omitted. Keep executable helpers/tests at their existing owner.

Save the complete XML to a unique file and parse it there. Terminal/read-tool
output can truncate even when the file is intact. Read through the actual
source with bounded chunks; check warnings and extracted coverage before use.

## Repair only a diagnosed parse failure

Try direct stdlib ElementTree parsing first. Keep the downloaded original
unchanged and work on a clearly named derived copy. Inspect the reported
line/column: malformed/undefined entities and literal ampersands have caused
ParseErrors, but a DOCTYPE alone does not prove corruption, and a paywall or
HTML response is not XML to repair into a paper.

For a diagnosed entity failure, replace only known HTML named entities with
their intended Unicode characters (for example `&alpha;`→α, `&mu;`→μ,
`&le;`→≤, `&ge;`→≥, `&times;`→×, `&plusmn;`→±). Preserve XML entities
(`&amp;`, `&lt;`, `&gt;`, `&quot;`, `&apos;`) and numeric references. Escape a
confirmed bare ampersand as `&amp;`; do not silently reinterpret an unknown
entity or destroy inequalities/units. If a declaration itself must be removed,
inspect its complete boundary, including any internal subset; a regex ending
at the first `>` is not a general DOCTYPE parser. Do not fetch an untrusted
external DTD to make the parse succeed.

Reparse the derived copy and compare affected passages with the original or
rendered paper. Record the repair and any unresolved loss. An available lxml
recovery parser is an alternative, but its error log and recovered content
still need review; neither silently dropped nodes nor fabricated replacement
text are acceptable. Check installed dependencies instead of assuming lxml
is universally present or absent.

## References and table cells from a parsed PMC tree

This stdlib example handles ordinary non-namespaced JATS; inspect the root
and adapt paths if the document uses namespaces. It reads the PMC file anew,
not a PubMed metadata tree. Keep structural reference/table IDs as locators.

```python
import xml.etree.ElementTree as ET
root = ET.parse(xml_path).getroot()

def text_of(element):
    return ''.join(element.itertext()) if element is not None else ''

references = []
for ref in root.iter('ref'):
    citation = ref.find('element-citation')
    if citation is None:
        citation = ref.find('mixed-citation')
    references.append({
        'id': ref.get('id'),
        'text': text_of(citation if citation is not None else ref),
        'ids': [(x.get('pub-id-type'), text_of(x)) for x in ref.iter('pub-id')],
    })

tables = []
for table in root.iter('table-wrap'):
    rows = []
    for row in table.iter('tr'):
        rows.append([text_of(cell) for cell in row if cell.tag in ('td', 'th')])
    tables.append({'id': table.get('id'), 'caption': text_of(table.find('caption')), 'rows': rows})
```

Do not infer DOI/PMID validity from extracted citation strings. Validate them
through paper-ingest. Table text alone does not resolve rowspan/colspan,
footnotes, superscripts, or image-only tables; inspect original layout for
any result that depends on those relationships. Preserve lexical values and
explicitly report content the extraction cannot represent.

## Body, references, and floats

Prefer structural traversal of `<body>` and its sections, excluding reference
nodes while extracting references separately. Some NIHMS deposits omit `<back>`
or `<ref-list>`; `root.iter('ref')` still finds their individual references.
Never slice to a missing delimiter's `-1` offset and call the result body.
If a text-slice fallback is unavoidable, inspect `<body>`, closing body,
reference, and floats boundaries, confirm their presence/order, and keep
separate outputs. Do not assume every `<ref>` is preceded by a `<back>`.

Inspect `<fig>`, caption, and `<floats-group>` content independently; a complete
body parse can omit figures whose source elements are elsewhere. Source title,
version, body coverage, and quantitative claims still require the main skill's
acceptance checks.

## Cell Press/resource-table quirks

In a 2026-09-04 extraction, flattened caption text ran into surrounding text
as `Figure 1High-affinity...`. A marker such as `Figure\s(\d+)(?=[A-Z])`
can locate candidates but also matches citations such as `Figure 1A`; verify
the XML/context before classifying it as a legend. Wrapping a long paragraph
for reading can reveal text hidden by line-display truncation; it cannot
recover text absent from the source or parser output.

Legacy four-character PDB accessions can join the next word (`PDB: 8F9ECrystal...`).
For that observed form, `PDB:\s*([0-9][A-Za-z0-9]{3})` prevents swallowing
following letters; verify the extracted accession at its source. Do not use
this as a universal identifier parser for other formats. Deposited-name typos
shared by PubMed and publisher XML still need source-aware author resolution;
keep the citable spelling and flag the ambiguity rather than silently guessing.

## Scoped prior observations

| Date | Source | Observation |
|---|---|---|
| 2026-07-17 | PMC6935424 | Entity replacement was needed in the retrieved XML. |
| 2026-07-25 | PMC9278498 | Entity replacement was needed. |
| 2026-07-27 | PMC12057666 | ParseError required a manually repaired copy. |
| 2026-07-30 | PMC12371982 | Direct parsing succeeded; no repair needed. |
| 2026-08-05 | PMC7371527 | NIHMS references lacked the expected back/ref-list wrapper; delimiter-based extraction included reference text. |

These observations distinguish repair conditions; they do not classify every
article from the corresponding publisher as malformed or inaccessible.
