---
name: paper-ingest-pubmed-resolver-v2
description: "PubMed XML identity resolver and PMC full-text path."
triggers:
  - "CrossRef blocked during paper ingest"
  - "CrossRef rate-limited during paper ingest"
  - "PubMed XML identity resolution"
  - "PMC full text via E-utilities"
  - "stub seed DOI wrong"
  - "PMC XML body parsing"
  - "paper has no DOI"
  - "DOI not assigned"
  - "find full-text URL without DOI"
---

# PubMed XML and PMC E-utilities as identity resolver and full-text source

This is a **reference companion** to the `paper-ingest` skill (which lives in
the brain vault at `skills/paper-ingest/SKILL.md` — no extra segment
under `skills/`). It documents techniques discovered across stub-fill
sessions on 2026-07-17, 2026-07-25, and 2026-07-28.

## 1. Cross-check the stub's seed DOI against the PMID

A stub's `## Citation` block or frontmatter `doi` can carry the **wrong DOI**.
This happens when the stub was created from a citation that referenced a
*different* paper by the same authors — a companion primary research paper,
a preprint→published pair, or an erratum.

**The fix:** if the stub carries a `pmid`, resolve it via PubMed and compare
the PubMed-returned DOI to the stub's seed DOI. If they disagree, the PubMed
DOI is authoritative (PubMed is the canonical record). Log the correction in
the page's Analysis section or a brief note; do not silently overwrite
without flagging the discrepancy.

**Observed instance (2026-07-17, Tan 2018 review):** Stub
`tan-2018-self-reactivity-spectrum` carried DOI
`10.4049/jimmunol.1801565` (the companion J Immunol primary research paper
by the same authors, PMID 30962292). But the stub's PMID 31631352 resolved to
DOI `10.1111/imr.12818` (the Immunological Reviews review article). The
companion paper was a *reference inside* the review, not the review itself —
the stub creator conflated the two. The PMID was the authoritative
disambiguator.

## 2. PMC E-utilities as a full-text source (not just metadata)

PubMed E-utilities also provide **full article body text** for open-access
articles via the PMC database endpoint — a third full-text path distinct from
both browser scraping (the `paper-ingest-browser-fulltext` reference) and
PubMed abstract-only XML.

```bash
# Full article body as structured XML (requires PMCID, not just PMID)
curl -sL "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=<PMCID>&rettype=xml"
```

The response contains the complete `<body>` with `<sec>` sections, `<p>`
paragraphs, `<xref>` cross-references, and figure captions — sufficient for
Phase 4 structural distillation without browser scraping. This is the
**preferred full-text path for open-access papers** (NIHMS manuscripts,
fully OA articles) because:

1. It returns structured XML, not rendered HTML — easier to parse reliably.
2. It works via terminal `curl` (usually allowed even when CrossRef is
   blocked — both go to government APIs).
3. It includes the complete reference list with DOIs and PMIDs, useful for
   Phase 7 bibliography walks.

For paywalled articles with no PMC copy, fall back to browser-based
extraction per the `paper-ingest-browser-fulltext` reference skill.

**Observed instance (2026-07-17, Tan 2018 review):** PMCID PMC6935424
returned the full 24-page review article body via `efetch.fcgi?db=pmc`,
including all 7 sections (Introduction through Concluding Remarks) and 130+
references with DOIs. This was sufficient for complete distillation of the
review's Context, Approach, Findings, Limitations, and Analysis sections
without any browser calls.

**Observed instance (2026-07-25, Leem 2022):** PMCID PMC9278498 returned
128KB of structured XML. The `scripts/pmc_xml_body_parser.py` script (see
§4 below) extracted 67K chars of body text covering Introduction, Results
(with figure captions and benchmark tables), Discussion, and full
Experimental Procedures — sufficient for complete distillation without
browser calls.

## 3. PubMed XML as a standalone identity resolver (when CrossRef is blocked)

If CrossRef is unavailable (blocked, rate-limited, or down), PubMed XML
alone is a sufficient Phase 1 resolver. It carries every field Phase 1 and
Phase 8 need:

- **Title** — `<ArticleTitle>`
- **Authors** — `<AuthorList>` with `<LastName>`, `<ForeName>` (for slug
  derivation)
- **ORCIDs** — `<Identifier Source="ORCID">` on each `<Author>` element
- **DOI** — `<ELocationID EIdType="doi">`
- **PMCID** — `<ArticleId IdType="pmc">`
- **PublicationTypeList** — retraction detection (Phase 3)
- **GrantList** — funding agencies
- **MeshHeadingList** — controlled vocabulary
- **Affiliations** — `<AffiliationInfo><Affiliation>` per author

Do not treat a CrossRef failure as a Phase 1 failure when PubMed XML is in
hand — the identity resolution is complete. Slugify authors from
`<LastName>`/`<ForeName>`, extract ORCIDs from `<Identifier Source="ORCID">`,
and proceed normally through Phase 8.

### Fetch commands (both formats, always fetch both)

```bash
# Text abstract (verbatim)
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=<PMID>&rettype=abstract&retmode=text"

# Full XML (structured metadata)
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=<PMID>&rettype=xml&retmode=text"
```

Both should always be fetched per the skill's Phase 1. The XML is the
load-bearing one for structured fields; the text is for the verbatim
abstract (though the XML `<AbstractText>` also carries it).

**E-utilities rate-limiting.** `efetch.fcgi` can return
`{"error":"API rate limit exceeded"}` when calls are rapid. Retry after a
brief delay (3–5 s) — the limit is per-API-key and resets quickly. This is
transient, not a permanent block. Observed 2026-08-02: first PubMed XML
fetch returned a rate-limit error; retry after 5 s succeeded with 40 KB of
XML.

### ORCID capture when PubMed XML has none — Europe PMC REST core search

PubMed XML `<Identifier Source="ORCID">` often carries only the
senior/corresponding author's ORCID, or none at all. When PubMed XML lacks
ORCIDs, the second-line source is **Europe PMC REST core search** (not the
LITE endpoint, which returns only an `authorString` with no per-author
ORCIDs):

```bash
curl -s "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=<PMID>&resultType=core&format=json"
```

Parse `resultList.result[0].authorList.author[].orcid` — each author
object has an `orcid` field (empty string when absent). This is a
terminal curl call (no browser needed) and supplements PubMed XML for
Phase 8 ORCID capture.

**When both PubMed XML and Europe PMC core search lack ORCIDs** (both
return empty for all authors), set `orcid: null` for all new ledger
entries. Do not fabricate ORCIDs from memory or additional external
searches — the `orcid` field is the disambiguation key, and an incorrect
ORCID is worse than null.

Observed 2026-08-02 (Pae 2020, PMID 33332554): neither PubMed XML nor
Europe PMC core search returned ORCIDs for any of the 13 authors. All 11
new ledger entries set `orcid: null`.

## 4. Reusable PMC XML body parser script

`scripts/pmc_xml_body_parser.py` — a statically-runnable script that takes a
downloaded PMC XML file and outputs structured text (section headings as
`## Title`, paragraphs below) ready for Phase 4 distillation. Handles the
ElementTree iteration, section/paragraph extraction, and pagination.

```bash
# Step 1: download PMC XML (curl alone, no pipe — tirith-safe)
curl -sL "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=<PMCID>&rettype=xml" -o /tmp/paper.xml

# Step 2: parse and print (first 15k chars by default)
python3 scripts/pmc_xml_body_parser.py /tmp/paper.xml

# Or paginate: print chars 15000-30000
python3 scripts/pmc_xml_body_parser.py /tmp/paper.xml --range 15000 30000

# Or print the full body
python3 scripts/pmc_xml_body_parser.py /tmp/paper.xml --full
```

The script extracts all `<sec>` sections and `<p>` paragraphs from the
`<body>` element, preserving section structure as markdown headings. This
replaces the ad-hoc inline `python3 -c` ElementTree parsing that every
session was reinventing. Observed 2026-07-25 (Leem 2022, PMC9278498): 128KB
XML → 67K chars of structured body text covering Introduction, Results,
Discussion, and Experimental Procedures.

## 5. Papers with no DOI — `doi: null` and the elink full-text URL path

Some papers — especially older regional or society journals — have **no
assigned DOI at all**. PubMed XML will have no `<ELocationID EIdType="doi">`,
and a CrossRef bibliographic search will return no match. This is not a
resolution failure; it is a legitimate state. Set `doi: null` in the paper
page frontmatter and note "DOI: not assigned" in the Citations section.

### Confirming the absence

1. **Check PubMed XML** — absence of `<ELocationID EIdType="doi">` confirms
   no DOI in the PubMed record.
2. **CrossRef REST API bibliographic search** — a second check that also
   serves as a DOI *discovery* fallback when the DOI exists but isn't in
   PubMed's XML (e.g. a recently registered DOI):

```bash
# Search CrossRef by bibliographic data (title + author) — two-step, tirith-safe
curl -s "https://api.crossref.org/works?query.bibliographic=<title-url-encoded>&query.author=<surname>&rows=3" \
  -o /tmp/crossref_search.json
python3 -c "
import json
with open('/tmp/crossref_search.json') as f: d = json.load(f)
for item in d['message']['items'][:3]:
    print(item.get('DOI','no DOI'), '|', item.get('title',['?'])[:1])
"
```

If the top results are unrelated papers, the DOI genuinely does not exist.
If a matching DOI appears, use it. The `curl -o file + python3 -c` two-step
form is tirith-safe (see fallback-patterns §5).

### Finding the full-text URL via elink

When no DOI exists, the publisher full-text URL can still be discovered via
PubMed's elink API with `cmd=prlinks`:

```bash
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&id=<PMID>&cmd=prlinks"
```

The response XML contains `<ObjUrl><Url>` elements pointing to the
publisher's full-text page (often a direct PDF link). This is useful for:
- Recording the full-text URL in the paper page's Citations section.
- Finding a free PDF source for browser-based full-text extraction (Phase 4)
  when neither DOI nor PMCID is available.

**Observed instance (2026-07-28, Pootong 2007):** PMID 17891920, *Asian
Pacific Journal of Allergy and Immunology* (a Thai society journal). No DOI
in PubMed XML; CrossRef bibliographic search returned only unrelated papers.
`elink.fcgi?cmd=prlinks` returned the publisher's free PDF URL:
`http://apjai-journal.org/wp-content/uploads/2018/01/6MonoclonalAntibodythatNeutralizesPertussisVol25No1March2007P37.pdf`.
Paper page created with `doi: null`; full-text URL recorded in Citations.

### Frontmatter and ledger handling

- **Frontmatter:** `doi: null` (explicit null, not omitted — the field is
  first-class per `conventions/frontmatter.md`).
- **Ledger:** Authors from no-DOI papers are handled identically to DOI'd
  papers — slug from `<LastName>`/`<ForeName>`, affiliation from
  `<AffiliationInfo>` (often only the first author carries one; remaining
  authors get `affiliations: []`).

## Complete fallback stack

These reference skills together provide a complete fallback when external
APIs are denied:

| Need | Source | Method |
|------|--------|--------|
| Title, authors, DOI, venue, year | PubMed XML | `curl` to E-utilities (usually allowed) |
| ORCIDs, PublicationTypeList, GrantList, MeSH | PubMed XML | same |
| Verbatim abstract | PubMed XML (`<AbstractText>`) | same |
| Full article body (open access) | PMC XML | `curl` to `efetch.fcgi?db=pmc` + `scripts/pmc_xml_body_parser.py` |
| Full article body (paywalled/no PMC) | PMC/Europe PMC HTML | browser_navigate + browser_console |
| Full-text URL when no DOI | elink API | `curl` to `elink.fcgi?cmd=prlinks` |
| DOI discovery (not in PubMed XML) | CrossRef REST API | `curl` to `api.crossref.org/works?query.bibliographic=...` |

## Session evidence

### Zhao 2019 (PubMed XML as identity resolver)

Zhao J, Nussinov R, Ma B. "Antigen binding allosterically promotes Fc
receptor recognition." mAbs. 2019;11(1):58-74.
DOI: 10.1080/19420862.2018.1522178. PMID: 30212263. PMCID: PMC6343797.

CrossRef was user-blocked. All three author ORCIDs extracted from PubMed XML:
- Zhao Jun: 0000-0002-1226-3882
- Nussinov Ruth: 0000-0002-8115-6415
- Ma Buyong: (no ORCID in PubMed XML — absent, not empty)

### Tan 2018 (seed DOI correction + PMC full text)

Tan C, Noviski M, Huizar J, Zikherman J. "Self-reactivity on a spectrum: A
sliding scale of peripheral B cell tolerance." Immunol Rev. 2019;292(1):37-60.
DOI: 10.1111/imr.12818. PMID: 31631352. PMCID: PMC6935424.

- Seed DOI `10.4049/jimmunol.1801565` was wrong (companion J Immunol paper,
  PMID 30962292). Corrected to `10.1111/imr.12818` via PMID 31631352 lookup.
- Full text obtained via `efetch.fcgi?db=pmc&id=PMC6935424&rettype=xml` —
  complete 24-page review body with all sections and 130+ references.
- Authors: Tan Corey (ORCID 0000-0002-5696-6766), Noviski Mark (ORCID
  0000-0001-8072-1059), Huizar John (no ORCID), Zikherman Julie (ORCID
  0000-0002-0873-192X, already in ledger as Branch 2).

### Pelanda 2022 (browser fallback for full text)

Pelanda R, et al. "B-cell intrinsic and extrinsic signals that regulate
central tolerance of mouse and human B cells." Immunol Rev. 2022;307(1):12-26.
DOI: 10.1111/imr.13062. PMID: 34997597. PMCID: PMC8986553.

Three external API `curl` calls (CrossRef, Europe PMC REST, PMC HTML) were
user-denied. PubMed XML (via allowed `curl`) provided metadata + abstract.
Full text extracted from PMC (PMCID: PMC8986553) via browser in 3 x 15,000-
character pages. Documented in the `paper-ingest-browser-fulltext` reference.

### Leem 2022 (PMC XML full text via E-utilities + parser script)

Leem J, Mitchell LS, Farmery JHR, Barton J, Galson JD. "Deciphering the
language of antibodies using self-supervised learning." Patterns. 2022;3(7):100513.
DOI: 10.1016/j.patter.2022.100513. PMID: 35845836. PMCID: PMC9278498.

- PMC XML (128KB) retrieved via `efetch.fcgi?db=pmc&id=PMC9278498&rettype=xml`.
- Parsed with `scripts/pmc_xml_body_parser.py` → 67K chars of structured body
  text (Introduction, Results with benchmark tables, Discussion, full
  Experimental Procedures). Sufficient for complete distillation without
  browser calls.
- ORCIDs from Europe PMC REST: Leem (0000-0002-7817-3644), Barton
  (0000-0002-1244-9484). PubMed XML had no ORCIDs for this paper.
- 5 authors, all at Alchemab Therapeutics, London. All new ledger entries
  (Branch 3). No existing person pages.
- Graph links: `projects/antibody-language-models`, `concepts/antibody-language-models`,
  `concepts/general-protein-language-models` — discovered by vault search
  for concept/project pages matching the paper's topic (see Phase 9 patch
  in the `paper-ingest` pointer).

### Pootong 2007 (no DOI, elink full-text URL discovery)

Pootong A, Budhirakkul P, Tongtawe P, Tapchaisri P, Chongsa-nguan M, Chaicumpa W.
"Monoclonal antibody that neutralizes pertussis toxin activities." Asian Pac J
Allergy Immunol. 2007;25(1):37-45. PMID: 17891920. No DOI.

- PubMed XML had no `<ELocationID EIdType="doi">` — confirmed no DOI.
- CrossRef bibliographic search (`api.crossref.org/works?query.bibliographic=...`)
  returned only unrelated papers — DOI genuinely absent.
- `elink.fcgi?cmd=prlinks` returned the publisher's free PDF URL from the
  Allergy and Immunology Society of Thailand.
- Paper page created with `doi: null`; full-text URL recorded in Citations
  section.
- 6 authors; only first author (Pootong) had an affiliation in PubMed XML;
  remaining 5 got `affiliations: []`.
- Literature-dive context: Tier 1 paper from anti-bacterial antibodies survey.
  Linked to the instance's `docs/surveys/` pages and related
  papers already in the vault.

### He 2026 (non-ASCII author slug derivation, sibling ledger wipe)

He M, D'Aulerio R, Pinho LG, ..., Westerberg LS. "AID and TET2 cooperate
to demethylate Irf4 for plasma cell fate in germinal center B cells."
J Exp Med. 2026;223(6):e20260096. DOI: 10.1084/jem.20260096.
PMID: 42043375. PMCID: PMC13116153.

- PMC XML (270 KB) retrieved via `efetch.fcgi?db=pmc&id=PMC13116153`.
  Parsed with `scripts/pmc_xml_body_parser.py` — full Introduction, all 9
  Results subsections, Discussion, Methods. JEM is open access; no browser
  calls needed.
- **Seed DOI correction:** task context gave a truncated seed DOI
  ("10.1084/jem.2024"); PubMed's DOI 10.1084/jem.20260096 is authoritative
  (same pattern as the 2026-07-17 Tan 2018 seed-DOI correction).
- **Non-ASCII author slugs (5 of 21 authors):** Rômulo→romulo, Søren→soren,
  José→jose, Ström→strom, D'Aulerio→d-aulerio. Naïve
  `re.sub(r'[^a-z0-9]+','-',s.lower())` mangles these (Rômulo→`r-mulo`).
  Fix: ASCII-fold via `unicodedata.normalize('NFKD',s).encode('ascii','ignore')`
  before slugifying, OR hand-build the slug list for a known author set.
  The frontmatter `authors:` and ledger `slug:` MUST match exactly (lint
  resolves by string equality). The `name:` display field retains
  diacritics; only the slug is ASCII-folded.
- **Sibling ledger wipe:** a sibling subagent rewrote the entire
  `people/_ledger.yaml` mid-session, dropping 19 of 21 newly-appended
  author entries. Discovered on re-verification (`grep`/`yaml.safe_load`).
  Fix: re-append dropped entries; re-merge any duplicates the sibling's
  reset re-introduced; reconcile slug mismatches by aligning the ledger
  to the frontmatter (frontmatter is authoritative for lint resolution).
  See the `paper-ingest` pointer Patch 2026-08-02 for the full protocol.
- 21 authors; all ORCIDs present in PubMed XML. 19 new ledger entries
  (Branch 3); 2 merged into existing entries (Degn, Dosenovic — same
  ORCID, different prior citations).
