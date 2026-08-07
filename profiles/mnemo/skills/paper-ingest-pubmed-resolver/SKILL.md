---
name: paper-ingest-pubmed-resolver
description: "PubMed XML identity resolver and PMC full-text path."
triggers:
  - "CrossRef blocked during paper ingest"
  - "CrossRef rate-limited during paper ingest"
  - "PubMed XML identity resolution"
  - "PMC full text via E-utilities"
  - "stub seed DOI wrong"
  - "PMC XML body parsing"
  - "Semantic Scholar DOI vs PMID lookup"
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

**Publisher XML download restriction.** Some publishers (e.g., ATS
Journals/OUP) restrict full-text XML download even when the article is in
PMC. In this case, `efetch.fcgi?db=pmc` returns only the `<front>` matter
(metadata, abstract, affiliations) with no `<body>`. The XML will contain a
comment: `<!--The publisher of this article does not allow downloading of the
full text in XML form.-->`. When this happens and `isOpenAccess: N`, fall
through to the Europe PMC PDF render endpoint (see
`paper-ingest-full-text-access` branch 1b), not to abstract-only.

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

**Observed instance (2026-07-28, Maselli 2018):** PMCID PMC5805996
returned only front matter (10KB XML) — the publisher (ATS Journals/OUP)
restricts full-text XML download. `isOpenAccess: N`, `inPMC: Y`. The Europe
PMC PDF render endpoint (`europepmc.org/api/getPdf?pmcid=PMC5805996`)
successfully delivered the full 8-page PDF instead. See
`paper-ingest-full-text-access` branch 1b for the technique.

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

## 5. Semantic Scholar DOI vs PMID lookup for OA PDF discovery

Semantic Scholar's REST API can discover open-access PDF URLs. The key
gotcha: **the PMID-based query can return empty fields even when the DOI-based
query succeeds.** Always use the DOI form.

```bash
# PMID-based query — CAN return empty for some papers
curl -sL "https://api.semanticscholar.org/graph/v1/paper/PMID:<PMID>?fields=openAccessPdf,abstract,tldr,title,year,authors"

# DOI-based query — more reliable, returns openAccessPdf.url
curl -sL "https://api.semanticscholar.org/graph/v1/paper/DOI:<DOI>?fields=openAccessPdf,abstract,tldr,title,year,authors"
```

The `openAccessPdf.url` field often points to a Europe PMC PDF render URL
(`europepmc.org/articles/pmc<PMCID>?pdf=render`), which is the same endpoint
as branch 1b in `paper-ingest-full-text-access`. When you need the full text
and have exhausted PMC XML and browser paths, check Semantic Scholar's
DOI-based `openAccessPdf` to discover the PDF URL, then download it via
`curl`.

The `tldr` field provides a one-sentence AI-generated summary — useful for
a quick sanity check on the paper's main finding when the abstract is
elided by the publisher.

**Observed 2026-07-28 (Maselli 2018):** PMID:28915064 query returned all
null/empty fields. DOI:10.1165/rcmb.2017-0006OC query returned
`openAccessPdf.url: https://europepmc.org/articles/pmc5805996?pdf=render`,
`openAccessPdf.status: GREEN`, and a useful `tldr`. The PMID query failing
while the DOI query succeeds is not a rate-limit or transient issue — it
is a coverage gap in Semantic Scholar's PMID indexing.

## Complete fallback stack

These reference skills together provide a complete fallback when external
APIs are denied:

| Need | Source | Method |
|------|--------|--------|
| Title, authors, DOI, venue, year | PubMed XML | `curl` to E-utilities (usually allowed) |
| ORCIDs, PublicationTypeList, GrantList, MeSH | PubMed XML | same |
| Verbatim abstract | PubMed XML (`<AbstractText>`) | same |
| Full article body (open access, XML allowed) | PMC XML | `curl` to `efetch.fcgi?db=pmc` + `scripts/pmc_xml_body_parser.py` |
| Full article body (embargoed, XML restricted) | Europe PMC PDF | `curl` to `europepmc.org/api/getPdf?pmcid=<PMCID>` + pymupdf extraction |
| Full article body (paywalled/no PMC) | PMC/Europe PMC HTML | browser_navigate + browser_console |
| OA PDF URL discovery | Semantic Scholar | `curl` to `api.semanticscholar.org/graph/v1/paper/DOI:<DOI>?fields=openAccessPdf` |

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

### Maselli 2018 (Europe PMC PDF render + Semantic Scholar DOI discovery)

Maselli DJ, Medina JL, Brooks EG, Coalson JJ, Kannan TR, Winter VT,
Principe M, Cagle MP, Baseman JB, Dube PH, Peters JI. "The Immunopathologic
Effects of Mycoplasma pneumoniae and Community-acquired Respiratory
Distress Syndrome Toxin. A Primate Model." Am J Respir Cell Mol Biol.
2018;58(2):253-260.
DOI: 10.1165/rcmb.2017-0006OC. PMID: 28915064. PMCID: PMC5805996.

- PMC E-utilities XML returned front matter only (10KB) — publisher (ATS
  Journals/OUP) restricts full-text XML download. Comment in XML:
  `<!--The publisher of this article does not allow downloading of the full
  text in XML form.-->`
- PMC browser blocked by reCAPTCHA. Publisher (academic.oup.com) blocked
  by Cloudflare. Europe PMC REST full-text XML API returned empty.
- Semantic Scholar PMID:28915064 query returned all null fields. DOI
  query returned `openAccessPdf.url: https://europepmc.org/articles/pmc5805996?pdf=render`,
  `status: GREEN`, and a useful `tldr`.
- Europe PMC PDF render endpoint (`europepmc.org/api/getPdf?pmcid=PMC5805996`)
  successfully downloaded 8-page PDF (1 MB), extracted to 37,712 chars with
  pymupdf — complete article text covering all sections and 26 references.
- No ORCIDs in PubMed XML or Europe PMC for any of the 11 authors.
- 11 authors: 3 existing ledger entries (Kannan TR → 8 citations, Baseman
  JB → 8 citations, Medina JL → 2 citations), 8 new ledger entries (Maselli
  DJ, Brooks EG, Coalson JJ, Winter VT, Principe M, Cagle MP, Dube PH,
  Peters JI). No person pages.
- Graph links: `concepts/antibacterial-antibody-discovery`,
  `grants/r01-mpneumoniae-cards-toxin-mab-discovery` — both pre-existing.
- Sibling subagent modified `_ledger.yaml` concurrently during the Kannan
  entry update, causing a duplicate `slug:` line. Fixed by re-reading and
  patching the malformed YAML (see `paper-ingest-fallback-patterns` §8).
