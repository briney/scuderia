---
name: paper-ingest-full-text-access
description: "Full-text decision tree for paper-ingest."
triggers:
  - "full text access for paper ingest"
  - "PMC full text via browser"
  - "Europe PMC PDF render"
  - "needs-enrichment decision"
---

# Full-text access — decision tree and browser extraction patterns

This is a **reference companion** to the `paper-ingest` skill. It documents
the full-text access decision tree and the browser extraction patterns that
`paper-ingest` Phase 4 needs when terminal `curl` is user-denied or when no
PDF is in hand.

## The decision tree

**Executable form:** `skills/paper-ingest/scripts/fetch_fulltext.py` walks
this entire ladder (gate → PMC XML → EPMC PDF → bioRxiv/jina → publisher
jina → Wayback) with retries/backoff and prints a JSON summary whose
`provenance` value is the page's `fulltext_source:` frontmatter tag
(`pmc-xml`, `epmc-pdf`, `biorxiv-jina`, `publisher-jina`, `wayback`,
`none`). **Prefer the script over hand-walking the tree** — it exists
precisely to kill the "agent stopped early" failure class (see the Chen
2023 pitfall below). `--figures` additionally scrapes the PMC article
page for figure images (see "Figure images" at the end). Hand-walk only
when the script's sources all miss and judgment is needed about exotic
alternatives. The branches below are the reference for what the script
does and for the cases it doesn't cover.

When Phase 4 needs the full article body (not just the abstract), try these
sources **in order**:

### 0. Pre-check gate — Europe PMC REST before any browser round-trip

Before burning a browser round-trip on a possibly-paywalled article, call the
Europe PMC REST search API and read the OA-status flags in a single call. When
the flags say "no OA copy anywhere" *and* the DOI resolves to a known-blocked
publisher (see "Known publisher blocks" under branch 3), fall straight through
to Abstract-only — do not retry alternate URL forms, do not attempt the browser.

```bash
# Step 1: download (curl alone, no pipe — tirith-safe; see paper-ingest-fallback-patterns §5)
curl -sL "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:<PMID>&resultType=core&format=json" -o /tmp/<pmid>_epmc.json

# Step 2: parse the file
python3 -c "
import json
with open('/tmp/<pmid>_epmc.json') as f: d = json.load(f)
r = d.get('resultList',{}).get('result',[])
if r:
    r0 = r[0]
    print('isOpenAccess:', r0.get('isOpenAccess'))
    print('inPMC:', r0.get('inPMC'))
    print('inEPMC:', r0.get('inEPMC'))
    print('pmcid:', r0.get('pmcid'))
    print('hasPDF:', r0.get('hasPDF'))
    for au in r0.get('authorList',{}).get('author',[]):
        aid = au.get('authorId',{})
        if aid.get('type') == 'ORCID':
            print('  ORCID:', au.get('fullName'), aid.get('value'))
"
```

**Why this gate is durable:** the one REST call returns `inPMC`, `inEPMC`,
`isOpenAccess`, `hasPDF`, and `pmcid`. When all are `N`/`None`, there is no OA
copy in PMC, Europe PMC, or the publisher's OA program — the only remaining
full-text source is the publisher page, and for known-blocked publishers that
round-trip is deterministic waste. The gate turns "try the browser and see"
into "check the flags and decide." It also subsumes the "Europe PMC 'Full text'
link is a publisher redirect" trap: when `inPMC`/`inEPMC` are both `N`, that
link is guaranteed to be a publisher redirect, not a source — skip it without
clicking. The same call supplies ORCIDs PubMed XML omits — a free two-for-one.

### 1. PMC open-access full text via browser (first fallback)

PMC is the *first* full-text source — it is free, structured, and available
for any paper with a `pmcid`. The browser path works even when terminal `curl`
is user-denied.

1. `browser_navigate` to `https://pmc.ncbi.nlm.nih.gov/articles/<PMCID>/`
2. `browser_console` with:
   ```javascript
   document.querySelector('article')?.innerText?.substring(0, 15000) || 'no article found'
   ```
3. Paginate for long articles:
   ```javascript
   document.querySelector('article')?.innerText?.substring(15000, 30000) || 'no more content'
   ```
   Continue until `'no more content'`.

**Do NOT set `needs-enrichment: true` when the full text is available via PMC
OA** — the browser is the fallback, not a dead end. Distill from the full text
as normal.

### 1b. Europe PMC PDF render (embargoed articles with PMCID)

When the article has a `pmcid` but `isOpenAccess: N` (embargoed or
publisher-restricted), PMC E-utilities XML returns metadata-only (no
`<body>`), and the PMC browser page is reCAPTCHA-blocked, the **Europe PMC
PDF render endpoint** can still deliver the full PDF:

```bash
# Step 1: download the PDF via curl (works even for embargoed articles)
curl -sL -o /tmp/<pmid>.pdf "https://europepmc.org/api/getPdf?pmcid=<PMCID>"

# Step 2: extract text with pymupdf
python3 -c "
import pymupdf
doc = pymupdf.open('/tmp/<pmid>.pdf')
text = ''
for page in doc:
    text += page.get_text()
with open('/tmp/<pmid>_fulltext.txt', 'w') as f:
    f.write(text)
print(f'Pages: {len(doc)}, chars: {len(text)}')
"
```

This endpoint redirects through `europepmc.org/api/getPdf?pmcid=<PMCID>` and
returns the publisher's PDF even when `isOpenAccess: N` — as long as
`inPMC: Y` and the article has a PMCID. The PDF contains the complete article
body (Abstract, Introduction, Methods, Results, Discussion, references) with
figure captions, sufficient for full Phase 4 distillation.

**Discovering the PDF URL via Semantic Scholar.** When the Europe PMC REST
search does not obviously expose a PDF link, Semantic Scholar's DOI-based
query can reveal it:

```bash
curl -sL "https://api.semanticscholar.org/graph/v1/paper/DOI:<DOI>?fields=openAccessPdf" -o /tmp/s2.json
python3 -c "
import json
with open('/tmp/s2.json') as f: d = json.load(f)
pdf = d.get('openAccessPdf', {})
print('url:', pdf.get('url'))
print('status:', pdf.get('status'))
"
```

Note: the Semantic Scholar *PMID-based* query (`PMID:<PMID>`) can return
empty fields even when the *DOI-based* query succeeds — always use the DOI
form. The `openAccessPdf.url` often points to
`europepmc.org/articles/pmc<PMCID>?pdf=render`, which is the same PDF
render endpoint.

**Observed 2026-07-28 (Maselli 2018, PMC5805996):** `isOpenAccess: N`,
`inPMC: Y`. PMC E-utilities XML returned front matter only (publisher
restricts full-text XML download). PMC browser blocked by reCAPTCHA.
Publisher (OUP/ATS Journals, `academic.oup.com`) blocked by Cloudflare
("Just a moment..."). Europe PMC REST full-text XML API returned empty
(embargoed). The Europe PMC PDF render endpoint
(`europepmc.org/api/getPdf?pmcid=PMC5805996`) successfully downloaded an
8-page PDF (1 MB), extracted to 37,712 chars of complete article text
covering all sections and 26 references.

**Observed 2026-08-01 (Kwon 2016, PMC4907239):** `isOpenAccess: N`,
`inPMC: Y`, `hasPDF: Y`. PMC E-utilities XML returned front matter only
(18 KB, no `<body>` element — embargoed/restricted). Europe PMC PDF
render endpoint (`europepmc.org/api/getPdf?pmcid=PMC4907239`) successfully
downloaded a 16-page PDF (7.6 MB), extracted to 63,860 chars of complete
article text covering all Results, Discussion, Methods, and references.
Publisher: ASM (J Virol). This confirms the branch-1b path is not
publisher-specific — it works for OUP/ATS, ASM, and any publisher where
`inPMC: Y` and the article has a PMCID.

### 1c. bioRxiv preprint full text (published version paywalled)

When the published paper is unreachable but a bioRxiv preprint exists
(discovered via `<CommentsCorrections RefType="UpdateOf">` in the published
paper's PubMed XML), the preprint carries the same core findings. The full
technique — discovery, version discipline, retrieval — lives in the
`paper-ingest-biorxiv-preprint-fulltext` companion. Retrieval order there
is now: api.biorxiv.org version check → **jina reader proxy (branch 1d,
single curl, verified 2026-08-05)** → browser click-through as fallback.
Set `needs-enrichment: true` (distillation is from the preprint, not the
published version).

### 1d. Reader proxy (r.jina.ai) for Cloudflare-blocked domains

**Verified 2026-08-05.** The Jina AI reader proxy fetches a URL through
its own browser infrastructure and returns clean markdown — bypassing
Cloudflare bot-detection interstitials that block both `curl` and
`browser_navigate` from this host. No API key needed at the free tier.

```bash
curl -sL "https://r.jina.ai/https://www.biorxiv.org/content/<doi>v<N>.full" -o /tmp/<slug>_fulltext.md
```

Same form works for publisher pages: `https://r.jina.ai/<publisher-url>`.
Sanity-check the output — a successful fetch returns sectioned markdown
(## Introduction / ## Results / ## References) of tens of KB; an error
returns a short page (check `wc -c` and the first lines before distilling).

Observed 2026-08-05 (bioRxiv 10.1101/2025.10.27.684659, the Wang 2026 Cell
preprint): direct curl to biorxiv.org (.full, .full.pdf, .source.xml) all
returned Cloudflare 429 (error 1015). The jina reader returned 132K chars
of clean markdown — Introduction, all Results subsections, Discussion, 53
references, figure captions — in a single terminal call, no browser.

**Limitations.** (a) Rate-limited without an API key (~20 req/min free
tier); if jina returns 429, back off and retry, or fall through to the
Wayback branch. An optional free API key can be supplied via the
`X-Return-Format`/`Authorization: Bearer <key>` header from an env var —
never store keys in the vault. (b) Output is markdown, not structured XML —
no `<xref>` citation mapping; figure captions are present, figure images
are not. (c) It defeats bot-detection, **not true paywalls** — a page that
requires a subscription login returns only the free portion. (d) The URL
is fetched through third-party infrastructure; appropriate for public
papers, not for anything credential-gated.

**Where it sits in the tree.** Try branch 1d after the PMC paths (1/1b)
fail and before committing to browser scraping of a known-blocked
publisher. For bioRxiv specifically, 1d is now the *first* retrieval
attempt (see the preprint companion). Wayback (branch 2b) is the fallback
when jina misses or rate-limits.

### 2. Journal HTML via browser (no PMC copy)

When no PMC copy exists but the journal page is accessible (check the CrossRef
`resource.primary.URL` or `link` fields for the article URL):

1. `browser_navigate` to the article URL
2. `browser_console` with `document.querySelectorAll('section')` to discover
   the article's section structure
3. Extract paragraphs from each section:
   ```javascript
   JSON.stringify(
     Array.from(document.querySelectorAll('section'))
       .map(sec => ({
         heading: sec.querySelector('h1, h2, h3, h4')?.textContent?.trim() || '',
         paragraphs: Array.from(sec.querySelectorAll('p'))
           .map(p => p.textContent.trim())
           .filter(t => t.length > 50)
       }))
       .filter(s => s.heading || s.paragraphs.length > 0)
   )
   ```

### 2b. Wayback Machine snapshots (Cloudflare-blocked pages, incl. bioRxiv)

When a publisher page blocks both `curl` and `browser_navigate` with
Cloudflare bot-detection, no PMC copy exists, and the reader proxy (1d)
missed or rate-limited, the Internet Archive Wayback Machine may hold a
snapshot that renders the full article as static HTML — no JavaScript
hydration, no Cloudflare challenge. This applies to **bioRxiv pages and
PDFs as well as publisher pages** — the archive crawls biorxiv.org heavily,
including `.full` HTML and `.full.pdf` assets.

**Procedure:**
1. Query the availability API for the closest snapshot:
   `curl -s "https://archive.org/wayback/available?url=<article-url>"` —
   returns JSON with the `closest` snapshot timestamp and URL.
   **The availability API itself rate-limits (observed 429 on 2026-08-05) —
   retry with a few seconds' backoff; do not treat one 429 as "no
   snapshot."** If the API stays limited, try the CDX endpoint or guess
   `https://web.archive.org/web/2/<article-url>` (redirects to the nearest
   snapshot).
2. `browser_navigate` to the snapshot URL, or `curl` the snapshot HTML and
   parse statically (no browser needed for most snapshots).
3. Extract the body. For Annual Reviews, body text is in
   `<div class="html_fulltext">` (may be CSS-hidden but present in source).
   For bioRxiv `.full` snapshots, the article body is in the static HTML.
4. If the reference list is absent from the snapshot, get it from the
   Europe PMC REST references endpoint:
   `curl -s "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:<doi>&resultType=core&format=json"`.

**Limitations.** Snapshots can be stale (missing recent corrections or a
newer preprint version) or absent entirely for obscure pages. Prefer 1d
(reader proxy) first — it fetches live content; Wayback is the fallback
when live retrieval is blocked AND jina misses.

Observed 2026-08-05 (Greber & Flatt 2019, Annu Rev Virol): Annual Reviews
page blocked to both `curl` (Cloudflare 403) and `browser_navigate`. No
PMCID, no PMC OA, no Europe PMC PDF. Wayback snapshot (20221017074513)
delivered 990 KB HTML with 142K chars of article body covering all
sections; 153-entry reference list obtained separately from Europe PMC
REST. Full distillation completed from this text.

### 3. Abstract only (genuinely unreachable text)

If the article is paywalled, has no PMC open-access copy, and no accessible
journal HTML — *then* distill from the abstract only, set
`needs-enrichment: true`, and note the reason in `## Ingest log` (e.g.
"paywalled, no PMC OA, journal HTML inaccessible"). This is the only case
where `needs-enrichment: true` is appropriate.

**Confirm closure with three sources before accepting abstract-only.** Before
falling back, verify no OA copy exists anywhere via three independent sources.
This prevents a premature abstract-only call on a paper that is actually OA via
a source you didn't check. When all three agree the paper is closed,
abstract-only is the correct terminal state — not a degraded path.

1. **Europe PMC REST** — `inPMC: N` and `isOpenAccess: N` in
   `resultList.result[0]` from the branch-0 gate call. Prefer as the first
   source: one call covers OA flags + ORCIDs + PMCID.
2. **Unpaywall** — `is_oa: false` and `oa_status: closed` from
   `api.unpaywall.org/v2/<DOI>?email=<email>`. Aggregates OA copies from
   repositories, preprint servers, and publisher OA pages; a `closed` verdict is
   a strong "no OA copy anywhere it tracks" signal. Use the Crossref-registered
   DOI (typically lowercase); Unpaywall normalizes case.
3. **Semantic Scholar** — `openAccessPdf.status: CLOSED` (and empty
   `openAccessPdf.url`) from
   `api.semanticscholar.org/graph/v1/paper/PMID:<PMID>?fields=openAccessPdf`.
   Rate-limited (429 on first hit common); retry once after ~8s. Also returns
   `tldr` and `abstract` when the publisher hasn't elided them.

Record the three-source confirmation in the `## Ingest log` entry so future
enrichment runs know closure was verified, not assumed:

```markdown
- **YYYY-MM-DD** — successful ingest (abstract-only). Identity resolved via
  PubMed E-utilities (PMID <PMID>): DOI <DOI> confirmed. No PMCID; Europe PMC
  `inPMC: N`, `isOpenAccess: N`; Unpaywall `is_oa: false`, `oa_status: closed`;
  Semantic Scholar `openAccessPdf.status: CLOSED` — three-source closure
  confirmed. Full text not retrieved: <publisher> paywall, no PMC OA copy.
  Distillation from the structured PubMed abstract + MeSH headings.
  `needs-enrichment: true` set.
```

#### Known publisher blocks

These publisher domains block headless full-text retrieval deterministically —
recognize each and fall straight through to Abstract-only when the branch-0 gate
confirms no OA copy. Do **not** retry alternate URL forms.

| Publisher | Domain | Block mechanism | Pass-through condition |
|---|---|---|---|
| Elsevier / ScienceDirect | sciencedirect.com, elsevier.com | Deterministic block page ("There was a problem providing the content requested") to headless browsers; fires even for OA-labelled articles | No PMCID + DOI → Elsevier → Abstract-only |
| Wiley | onlinelibrary.wiley.com | Cloudflare bot-detection interstitial ("Just a moment..."); `curl` returns HTTP 403 independently | No PMCID + DOI → Wiley → Abstract-only |
| Karger | karger.com (doi.org/10.1159/...) | Cloudflare Turnstile to both `curl` (HTTP 403 `cf-mitigated: challenge`) and browser ("Just a moment...") | Europe PMC `inPMC: N` + DOI → Karger → Abstract-only |
| OUP / ATS Journals | academic.oup.com, atsjournals.org | Cloudflare bot-detection interstitial ("Just a moment...") to both `curl` and browser | No PMCID + DOI → OUP → Abstract-only (but try branch 1b first if PMCID exists) |
| Cell Press | cell.com | Cloudflare bot-detection interstitial ("Just a moment...") to both `curl` and browser | Try branch 1c (bioRxiv preprint via `<CommentsCorrections UpdateOf>`) before Abstract-only; Cell Press is an Elsevier imprint |

For any domain in this table, **branch 1d (reader proxy) is worth one
attempt before Abstract-only** even when the pass-through condition fires —
verified to defeat the Cloudflare tier on biorxiv.org 2026-08-05. It does
not defeat true subscription paywalls.

Second-order dead-ends observed alongside these blocks (do not cascade through
them): the Europe PMC *browser article view* can return "unable to retrieve the
citation details" or a minimal DOM — but the Europe PMC *REST API* still returns
abstract + ORCIDs + OA flags normally, so prefer REST over the browser page. The
PubMed browser page (`pubmed.ncbi.nlm.nih.gov/<PMID>/`) can return HTTP 403 —
use E-utilities `curl`, not the browser. Google Scholar IP-blocks on this host;
Semantic Scholar *web* search 405s but its *REST API* works.

**Positive counter-example — Nature family renders reliably.** `nature.com/articles/<doi-suffix>`
renders the full body to headless browsers (all Results subsections, Discussion,
Methods, figure captions). The branch-2 "Journal HTML via browser" step works
for Nature — try it before falling through. The blocks above are
publisher-specific, not a universal "journal HTML is unreachable" rule.

**Positive counter-example — OUP/ATS with PMCID.** When the OUP/ATS publisher
page is Cloudflare-blocked but the article has a PMCID and `inPMC: Y`, the
branch-1b Europe PMC PDF render endpoint bypasses the publisher entirely.
Observed 2026-07-28 (Maselli 2018): OUP page blocked, but
`europepmc.org/api/getPdf?pmcid=PMC5805996` delivered the full PDF.

**Positive counter-example — ASM/J Virol with PMCID.** When the ASM publisher
page is not attempted but the article has a PMCID and `inPMC: Y`, the
branch-1b Europe PMC PDF render endpoint delivers the full PDF.
Observed 2026-08-01 (Kwon 2016): `europepmc.org/api/getPdf?pmcid=PMC4907239`
delivered a 16-page PDF for an ASM/J Virol article with `isOpenAccess: N`.

## Common pitfall: abstract-only when full text was available

**Observed 2026-07-17 (Chen 2023 stub-fill):** The paper had `pmcid:
PMC10424567` (open access), but the agent distilled from the abstract only
because terminal `curl` was blocked and the agent did not try the browser
fallback for PMC. The `paper-ingest-browser-fulltext` skill (created earlier
that same day from the Pelanda 2022 session) documents exactly this technique,
but the `paper-ingest` SKILL.md did not point to it clearly enough. The result
was a lower-quality distillation — findings were inferred from the abstract
rather than extracted from the full text with figure citations.

**The fix:** When you have a `pmcid`, always try PMC via browser before falling
back to abstract-only. The browser is the fallback for terminal `curl`, not a
last resort.

**Observed 2026-07-28 (Maselli 2018):** A second variant — the article had a
PMCID (`inPMC: Y`) but `isOpenAccess: N` (embargoed). PMC E-utilities XML
returned front matter only, and the PMC browser page was reCAPTCHA-blocked.
The agent initially considered falling through to abstract-only, but the
Europe PMC PDF render endpoint (branch 1b) successfully delivered the full
PDF. **The fix:** When `inPMC: Y` but the PMC XML is metadata-only and the
browser is blocked, try the Europe PMC PDF render endpoint before accepting
abstract-only. The `isOpenAccess: N` flag means the article is not OA, but
`inPMC: Y` means Europe PMC still has the PDF.

**Observed 2026-08-01 (Kwon 2016):** A third instance of the same pattern —
PMC E-utilities XML returned only front matter (18 KB, no `<body>`), but the
Europe PMC PDF render endpoint delivered the full 16-page PDF. The branch-1b
path is now confirmed across three publishers (OUP/ATS, ASM, and the general
`inPMC: Y` case). It should be the *default* next step after PMC XML returns
metadata-only, before any browser attempt.

## Figure images (Phase 4, optional)

`fetch_fulltext.py --figures` downloads a paper's figure images from PMC
(when a PMCID exists) into `<out>_figures/`.

**Method, and why not the alternatives (all verified 2026-08-05):**
- The PMC article HTML page (`pmc.ncbi.nlm.nih.gov/articles/<PMCID>/`)
  embeds every figure as a `cdn.ncbi.nlm.nih.gov/pmc/blobs/.../<file>.jpg`
  URL. Scraping those URLs from the page HTML and downloading them works
  from this host — and works for free-in-PMC articles, not just the OA
  subset.
- NCBI's bulk-package host (`oa.fcgi` → `ftp.ncbi.nlm.nih.gov/...tar.gz`)
  refuses this host entirely: 404 over https, 550 over ftp, for two
  different OA packages. Do not route figure fetches through oa.fcgi.
- Europe PMC's image backend
  (`europepmc.org/backend/ptpmcrender.fcgi?...blobtype=image...`) dies with
  HTTP/2 stream errors from this host; the friendly
  `europepmc.org/articles/<PMCID>/bin/<file>.jpg` URL 301-redirects to that
  backend. Do not use.

**Using the figures.** With images in hand, `vision_analyze` can read key
figures directly — axis scales, panel-level results the text under-specifies
— and fold them into the page's Findings. Figure *captions* already arrive
with every full-text route; images add what's only in the pixels.

**Storage default: ephemeral.** Figures are distillation-time working
material, not vault artifacts — fetch, read, distill, then let `/tmp`
clean up. A permanent figure archive in the vault is a separate design
question (repo growth vs. reuse value) deferred to your human.

## Relationship to paper-ingest-browser-fulltext

The `paper-ingest-browser-fulltext` skill has the detailed step-by-step
technique (selectors, pagination, reliability notes) from the Pelanda 2022
session. This reference file provides the decision tree and the
`needs-enrichment` decision rule. Together they cover the full-text access
space.
