---
name: paper-ingest
description: "Ingest a scientific paper into the brain — identity resolution, full-text retrieval, distillation, bibliography walk, author ledger, and verification. Use for single papers (DOI, PMID, PDF, or link), stub fills, and delegated ingests from literature-dive or ingest-pending-papers."
triggers:
  - "ingest this paper"
  - "ingest a paper"
  - "paper ingest"
  - "fill a paper stub"
  - "stub fill"
  - "ingest this DOI"
  - "add this paper to the brain"
---

# paper-ingest — single-paper ingestion pipeline

Ingest one scientific paper into the brain: resolve its identity, retrieve
full text, distill it into a `papers/<slug>` page, walk its bibliography
into stubs, wire its authors into the people ledger, link it into the
graph, and verify the result.

This skill is per-paper. Its callers:

- **Direct** — your human shares a DOI, PDF, link, or PMID.
- **`literature-dive`** — dispatches Tier 1 papers to subagents running
  this pipeline.
- **`ingest-pending-papers`** — drains the stub queue (papers with
  `needs-ingest: true`), one invocation of this pipeline per stub.

First contact with material entering the brain is spine work (`SOUL.md`
§2): when you are the agent that decided this paper exists, run this
pipeline yourself. When an upstream vetted decision already exists (a
review's Tier 1 citation, a queued stub), delegation with read-back
verification is sanctioned.

> **Conventions:** `skills/conventions/frontmatter.md` (paper-kind
> schema, `fulltext_source` enum), `skills/conventions/author-ledger.md`
> (Phase 8), `skills/conventions/page-kinds.md` (slug forms),
> `skills/conventions/graph-and-links.md` (typed edges, forward-only
> linking), `skills/conventions/quality.md`.

## Tooling

Executable helpers live in `scripts/` under this skill directory.
Parameterize per profile — do not hardcode one profile's path. Resolve
via the profile symlink into the scuderia checkout
(`~/git/scuderia/profiles/mnemo/skills/paper-ingest/scripts/`).

- **`fetch_fulltext.py`** — the Phase 4 decision tree in executable
  form (Europe PMC gate → PMC XML → EPMC PDF → bioRxiv/jina → publisher
  jina → Wayback) with retries/backoff. Prints JSON whose `provenance`
  value is the page's `fulltext_source:` tag. **Required args:**
  `--out <path>`; optional `--pmid`, `--doi`, `--pmcid`,
  `--publisher-url`, `--skip-publisher`. Prefer the script over
  hand-walking the tree; hand-walk only when its sources all miss
  (`provenance: none`) and judgment is needed about exotic alternatives.
  **Output path quirk:** the script appends `.txt` to the `--out` value
  internally — `--out /tmp/paper` produces `/tmp/paper.txt`, and
  `--out /tmp/paper.txt` produces `/tmp/paper.txt.txt`. Read the actual
  path from the JSON summary's `text_file` field, not from `--out`.
- **`validate_identifiers.py`** — pre-dispatch identifier validation
  (Phase 3.5). Verifies candidate PMID/DOI/PMCID resolves to the intended
  paper BEFORE a subagent is dispatched. `--batch` JSON + `--recover` for
  recovery via Europe PMC title search. Output: `validated` /
  `recovered` / `HOLD`; `retracted: true` surfaced.
- **`dedup_check.py`** — the pre-write dedup gate (Phase 2). Scans
  `papers/` frontmatter for an existing page with the same DOI, PMID, or
  near-identical title before a new page is written. Exit 0 = safe to
  create; exit 1 = existing page found (STUB/FULL state shown per match);
  exit 2 = usage error. `--json` for machine-readable output. Run with
  the *resolved* identifiers from Phase 1, never the seed identifiers.
- **`slugify_name.py`** — author slug derivation (Phase 8). Handles
  diacritic folding (Ł→l, ø→o, ß→ss), PubMed name misparsing (Korean
  `LastName="Won Heo"` → `heo-tae-won`; Italian `ForeName="Paola Lo"`
  → `lo-surdo-paola`), and short-surname token filtering for ledger
  searches. `--pubmed-xml <file>` for batch; `--family`/`--given` for
  single; `--filter-surname` with `--ledger-file` for token-match queries.
- **`embargo_recheck.py`** — monthly cron (`embargo-recheck`, `0 6 1 * *`,
  no_agent, deliver=local) over every `needs-enrichment: true` paper;
  reports `new-pmcid` and `oa-flipped`. Silent when nothing flips.
- **`pmc_xml_body_parser.py`** — parses a downloaded PMC XML file into
  structured text (`## Title` headings + paragraphs) for distillation.
  `--range N M` to paginate, `--full` for the whole body.
- **`verify_ingest.py`** — the Phase 10 verification pass (five graph
  invariants + the canonical-identity phase in one run). Run after every
  ingest, before commit. **Invocation:** pass the BARE slug filename
  (e.g. `2017-verstraete-tslp-...md`), NOT the `papers/<slug>.md` path —
  the script prepends `papers/` itself. Network checks resolve the DOI
  (DataCite → OpenAlex → Crossref; arXiv `10.48550/*` DOIs try DataCite
  first — OpenAlex has wrong-paper collisions there), cross-check the
  PMID's DOI against the page DOI, compare the author count against the
  canonical list (PubMed individuals; collectives don't count), and
  surface retractions. `--offline` skips the network phase for
  airgapped work — do not use it to wave a failing check through;
  re-run online before commit.

**Environment notes:**
- **tirith blocks `curl | python3` pipes** — use the two-step
  file-intermediary form: `curl -sL "<url>" -o /tmp/<name>.json` then
  `python3 -c "...parse the file..."`.
- **E-utilities rate limits** — batch ID lookups into single `esummary`
  calls, sleep 3–5s between sequential calls, never loop on 429 (three
  consecutive → wait 15+s). Transient, not permanent.
- **URL-encode brackets in PubMed field tags** — `review[pt]` contains
  brackets that the shell interprets. In curl: use `%5B`/`%5D`. In
  Python: use `urllib.parse.quote()` (NOT `urlencode`, which
  double-encodes pre-encoded brackets).
- **DOIs with parentheses** — Elsevier/Lancet DOIs commonly contain
  parens (`10.1016/S2352-3026(21)00028-4`). Shell-escape with
  `shlex.quote()` before interpolating into CLI command strings.
- **EPMC search response** — results are under
  `resultList.result` (a dict key `"result"` holding the list), NOT
  `resultList` as a direct list. Parse:
  `data.get("resultList", {}).get("result", [])`.
- **EPMC DOI is authoritative** — PubMed XML `<ELocationID>` and
  `<ArticleIdList>` can carry a wrong DOI from a cross-reference error.
  When PubMed and EPMC disagree, use the EPMC core record's `doi`.
  Prefer `<ELocationID>` over `<ArticleIdList>` for the article's own DOI.
- **`elink.fcgi` returns related articles** — NOT the paper's own PMCID.
  Use PubMed XML `<ArticleId IdType="pmc">` or the EPMC core record's
  `pmcid` field instead.
- **arXiv API curl is blocked** on this host — use the paperclip mirror
  or the jina abs-page proxy (`r.jina.ai/https://arxiv.org/abs/<id>`).
- **`ulimit -n 4096`** before parallel subagent dispatch (macOS default
  256 is too low).

## Phases

### 1. Identity resolution

Resolve the paper's canonical identity before anything else.

**Primary source: PubMed XML.** Always fetch both forms:

```bash
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=<PMID>&rettype=abstract&retmode=text" -o /tmp/<pmid>.txt
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=<PMID>&rettype=xml&retmode=text" -o /tmp/<pmid>.xml
```

The XML carries every field the pipeline needs: `<ArticleTitle>`,
`<AuthorList>` (`<LastName>`/`<ForeName>` for slugs), `<Identifier
Source="ORCID">`, `<ELocationID EIdType="doi">`, `<ArticleId
IdType="pmc">`, `<PublicationTypeList>` (retraction detection, Phase 3),
`<GrantList>`, `<MeshHeadingList>`, `<AffiliationInfo>`,
`<AbstractText>`, and (in newer records) `<ReferenceList>` for Phase 7.
**A resolution from PubMed XML alone is complete, not degraded** — if
CrossRef is blocked or rate-limited, proceed; CrossRef adds affiliation
strings, reference-list coverage, and ORCID disambiguation, nothing
load-bearing. **DOI location in pre-2006 papers:**
`<ELocationID EIdType="doi">` is frequently empty or absent for papers
published before ~2006. Fall back to
`<PubmedData/ArticleIdList/ArticleId IdType="doi">`. The same
`<PubmedData/ArticleIdList>` also carries the PII
(`<ArticleId IdType="pii">`) needed for Cell Press / Elsevier full-text
retrieval — no `elink.fcgi?cmd=prlinks` call needed when PubMed XML is
already fetched.

**The identifier verification gate.** Identifiers from stubs, task
briefs, and bibliographies are wrong at high observed rates. Never trust
a seed identifier until it survives this gate. **The universal gate is
the title comparison**: compare the PubMed `<ArticleTitle>` against the
stub/task title. A DOI-only cross-check against a wrong PMID silently
"confirms" the wrong paper.

| Variant | Gate | Fix |
|---|---|---|
| Seed DOI wrong, PMID right | PubMed DOI vs seed DOI (compare lowercased — DOIs are case-insensitive) | PubMed DOI authoritative; log correction |
| PMID wrong, DOI right | Title comparison | PubMed title search for correct PMID; confirm by DOI match |
| Both wrong | Title comparison | `esearch.fcgi?db=pubmed&term=<title+keywords>&retmode=json` → correct PMID → DOI |
| Task-warned DOI | Resolve PMID, compare DOI; check whether "wrong" author appears mid-list | PubMed authoritative; warning is often a false alarm |

**Wrong first-author name in the task.** The PMID/DOI is authoritative
for authorship: use the PubMed `<AuthorList>` in `authors:` and the
ledger; file at the task-specified slug, but flag the discrepancy in the
Ingest log.

**Erratum disambiguation.** A PubMed title search can return both the
primary paper and its erratum. Disambiguate via
`<CommentsCorrectionsList>`: the erratum carries `RefType="ErratumFor"`,
the primary `RefType="ErratumIn"`. Record the erratum's PMID in the
Ingest log.

**Editorials and commentaries (`RefType="CommentOn"`).** These carry
`<PublicationType>` "Editorial" or "Comment" and a
`<CommentsCorrectionsList>` entry pointing to the commented-on paper.
The target paper is the natural `links:` entry when it exists in the
vault. These papers often have no abstract — the commentary body IS the
content; treat body text as the primary distillation source and note
"no structured abstract (editorial)" in the Ingest log.

**PDB structure DOIs (`10.2210/pdb*/pdb`).** Papers with a wwPDB DOI
resolve to the structure page, NOT the publisher article. Use the PII
or publisher URL for full-text retrieval. Record the PDB DOI in `doi:`
(it is canonical per PubMed) and note it is a wwPDB structure DOI.

**Papers with no DOI.** Older/regional journals may have no DOI at all —
set `doi: null` (explicit, not omitted). Discover the publisher URL via
`elink.fcgi?dbfrom=pubmed&id=<PMID>&cmd=prlinks`.

**Semantic Scholar as metadata fallback.** When other routes are
blocked, `api.semanticscholar.org/graph/v1/paper/DOI:<doi>?fields=title,abstract,externalIds,authors.name,venue,publicationDate`
settles identity. Always use the DOI form — the PMID form can silently
return empty. S2 `openAccessPdf` (add to fields list) is also a
full-text routing lead: `status: GREEN` often points at a co-author's
institutional repository or funder archive copy (attempt the download,
but these URLs can be Cloudflare-blocked too).

**bioRxiv preprints.**
- The `api.biorxiv.org/details/biorxiv/<doi>` response's `published`
  field carries the published version's DOI when one exists.
- The openRxiv DOI prefix **10.64898** (since 2026-01) is bioRxiv in
  every operational respect. Do not treat it as different.
- The bioRxiv API requires the FULL DOI including prefix
  (`10.64898/2026.08.14.744703`), not just the numeric path.
- bioRxiv `source.xml` is front-matter-only — no `<body>` element. Go
  directly to the PDF for full text.
- For corporate/anonymous authorship: use the corresponding author as
  the sole `authors:` entry, or `authors: []` if no individual is named.

**arXiv papers.**
- **Author list ladder:** (1) `paperclip cat /papers/arx_<id>/meta.json`
  — split on " and "; (2) jina abs-page proxy
  (`r.jina.ai/https://arxiv.org/abs/<id>`) when the API is blocked;
  (3) Crossref DOI resolver (`doi.org/<10.48550/arXiv.<id>>`) for
  structured author metadata with ORCIDs.
- **Version history:** search indexes carry only the latest version. If
  a title search misses, open `arxiv.org/abs/<id>v1` and compare. Always
  fetch full text from the VERSIONED URL (`arxiv.org/html/<id>v1`).
  Withdrawals: still ingest v1 (withdrawal ≠ retraction), note the
  withdrawal in a prominent body warning, check the superseding paper.
- **Venue assignment:** task-specified venue → `status: published`; no
  task venue → `status: preprint`, `venue: "arXiv (<id>)"`. Never infer
  acceptance from the arXiv listing alone.

### 2. Dedup against the brain

Run the mechanical gate BEFORE writing anything:

```bash
python3 skills/paper-ingest/scripts/dedup_check.py \
    --doi <doi> --pmid <pmid> --title <resolved title>
```

Exit 0 = no existing page (safe to create). Exit 1 = existing page found —
the output names each match with its STUB/FULL state, so the path is
unambiguous: a FULL match means this is a re-ingest — enrich, don't
duplicate; a STUB match means this is a stub fill — preserve its
`cited_by` (see Phase 5). A title-only match (`title~<score>`) is a
REVIEW signal, not a verdict — corrections, replies, and sister papers
share titles; confirm against DOI/PMID before treating it as the same
paper.

The gate matters because the citation-form search it replaces fails on
near-duplicate slugs: full pages and stubs for the same DOI have been
filed under different slugs. Run it after Phase 1 (with the *resolved*
identifiers, not the seed) and before the Phase 5 page write.

### 3. Retraction and integrity check

Read `<PublicationTypeList>` from the PubMed XML: "Retracted
Publication", "Retraction of Publication", "Published Erratum". A
retracted paper is still ingested when it is load-bearing context, but
the retraction is front-page information: prominent body warning, and
any downstream dispatch list surfaces `retracted: true` rather than
dispatching silently. `validate_identifiers.py` also reports
`is_retracted` from OpenAlex.

### 3.5. Pre-dispatch identifier validation (orchestrators)

When this pipeline is being dispatched to subagents in bulk, the
orchestrator validates the whole batch first:

```bash
python3 skills/paper-ingest/scripts/validate_identifiers.py \
    --batch /tmp/citations.json --recover
```

Match rule: token_set_ratio ≥ 90 AND surname match AND year ±1; REVIEW
band 75–89; never title alone. Dispatch only from the validator's
`dispatch` list. `HOLD` entries with PMIDs deserve one PubMed `esummary`
batch check before discard — the heuristic is conservative with older
papers.

### 4. Full-text retrieval

**Prefer `fetch_fulltext.py`** — it walks the tree below with retries
and prints the `fulltext_source` tag. Hand-walk only when it returns
`provenance: none`.

**PMCID extraction pitfall.** When parsing PubMed XML for the PMCID,
scope to the article's own `<ArticleIdList>` — a bare
`root.findall(".//ArticleId")` iterates ALL `<ArticleId>` elements
including those in `<ReferenceList>`, and a reference PMC ID can
overwrite the article's own (last match wins). Cross-check: the PubMed
abstract text endpoint prints `PMCID: PMCxxxx` on its last line.

**Branch 0 — Europe PMC gate (one call, always first for PubMed papers):**

```bash
curl -sL "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:<PMID>&resultType=core&format=json" -o /tmp/<pmid>_epmc.json
```

Read `isOpenAccess`, `inPMC`, `inEPMC`, `hasPDF`, `pmcid` (and ORCIDs —
free two-for-one with Phase 8). The query MUST use the `EXT_ID:` field
code — a bare `query=<PMID>` returns hitCount 0.

**PMCID overrides stale EPMC flags.** EPMC flags are not always fresh.
A PMCID in the PubMed XML (`<ArticleId IdType="pmc">`) is the stronger
OA signal — **always try `efetch db=pmc` (Branch 1) when PubMed XML
carries a PMCID, even if EPMC reports all-N.** Only declare abstract-only
when `efetch db=pmc` itself returns front-matter only or an error. The
reverse also holds: if the PubMed XML PMCID returns front-matter only,
check the EPMC `pmcid` field for a different PMCID and retry.

**Branch 1 — PMC open access.** With a PMCID and `isOpenAccess: Y`:

```bash
curl -sL "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=<PMCID>&rettype=xml" -o /tmp/<pmid>_paper.xml
python3 scripts/pmc_xml_body_parser.py /tmp/<pmid>_paper.xml --full
```

Structured XML (`<sec>`/`<p>`/`<xref>`), complete reference list — the
preferred path for OA papers. Always prefix `/tmp` artifacts with the
PMID (not bare `/tmp/paper.xml`) — parallel siblings share `/tmp`.

After fetching PMC XML, **verify the article title matches the PubMed
record** before using the body. If titles diverge, the PMCID maps to a
different article — tag `fulltext_source: abstract` and do not use the
mismatched body. (The mismatched content may still be useful context in
the Notes section.)

**Branch 1b — Europe PMC PDF render (embargoed, `inPMC: Y`).** When PMC
XML returns front matter only and the PMC browser page is blocked:

```bash
curl -sL -o /tmp/<pmid>.pdf "https://europepmc.org/api/getPdf?pmcid=<PMCID>"
# extract with pymupdf
```

Delivers the publisher PDF even when `isOpenAccess: N`, as long as
`inPMC: Y`. Only call `getPdf` with a real PMCID from the EPMC core
record or PubMed XML — never fabricate a PMCID by prepending `PMC` to a
bare PMID (the endpoint silently serves an unrelated PDF with HTTP 200).
If you do fetch, verify the PDF's first page matches the PubMed record.

**Branch 1c — bioRxiv preprint.** Preprint retrieval order: (0)
`api.biorxiv.org/details/biorxiv/<doi>` version check; (0.5) direct
`curl -sL` on the `.full.pdf` URL
(`https://www.biorxiv.org/content/<doi>v<N>.full.pdf`) — works for
openRxiv (`10.64898`) and legacy (`10.1101`) prefixes; (1) jina reader
on the `.full` URL; (2) `.full.pdf` through jina (separate rate-limit
bucket); (3) browser direct (session-independent Cloudflare clearance);
(4) Wayback. Set `needs-enrichment: true` when distilling the preprint
in place of the published version.

**Branch 1d — Reader proxy (r.jina.ai) for Cloudflare-blocked domains:**

```bash
curl -sL "https://r.jina.ai/https://www.biorxiv.org/content/<doi>v<N>.full" -o /tmp/<slug>_fulltext.md
```

**Pitfall — DOI URLs return 404 via jina:** always use the publisher's
direct article URL, not `r.jina.ai/https://doi.org/<doi>`. A successful
fetch returns tens of KB; a 429 returns ~400 bytes — check `wc -c`
before distilling. **Retry discipline:** wait 20–30s and retry, up to 4
attempts. When `fetch_fulltext.py` has exhausted its internal retries,
run `sleep 45 && curl -sL "https://r.jina.ai/<url>" -o /tmp/<slug>.md`
manually. Jina can fail silently (empty output) — any failure mode
routes to the paperclip branch.

**Branch 1e — paperclip local mirror (zero-network, any source).**
When network paths fail, check the local mirror before declaring
abstract-only:

```bash
paperclip ls /papers/<doc_id>/          # doc_id: bio_<hash> or arx_<id>
paperclip cat --full /papers/<doc_id>/content.lines > /tmp/<slug>.txt
```

**Branch 2 — Journal HTML via browser.** When no PMC copy exists but the
journal page renders: navigate, extract section-by-section via
`browser_console`. Nature research-article pages render reliably
(`nature.com/articles/<doi-suffix>`). **This applies to OA Nature
research articles only — NOT Nature Reviews or subscription Nature
research journals** (see `references/publisher-blocks.md`).

**Branch 2b — Wayback Machine.** When live retrieval is blocked and
jina missed: `curl -s "https://archive.org/wayback/available?url=<article-url>"`
(the availability API itself 429s — retry with backoff), then fetch the
snapshot HTML. When the availability API 429s persistently, use the CDX
index API
(`web.archive.org/cdx/search/cdx?url=<article-url>&output=json&limit=5&filter=statuscode:200`)
— separate rate limits, returns timestamped rows with HTTP status codes.
Construct the snapshot URL as
`web.archive.org/web/<timestamp>/<original-url>` and fetch via
`urllib.request`. See `references/publisher-blocks.md` for the full CDX
extraction recipe and per-publisher guidance.

For arXiv, Wayback snapshots of `arxiv.org/html/*` are frequently
absent — skip it there.

**arXiv full text.** Primary:
`fetch_fulltext.py --doi 10.48550/arXiv.<id> --publisher-url https://arxiv.org/html/<id>`.
On `provenance: none`, go straight to the paperclip mirror (branch 1e).
If paperclip also lacks it, direct curl of `arxiv.org/html/<id>v<N>`
(always versioned) + regex tag-stripping is the last resort
(`fulltext_source: arxiv-html`). Numeric table contents can be silently
dropped from arXiv HTML — scan for "Table N:" captions with no numbers;
recover via browser.

**Branch 3 — Abstract only (genuinely unreachable).** Distill from the
structured abstract only after **three-source closure**: Europe PMC
(`inPMC: N`, `isOpenAccess: N`), Unpaywall (`is_oa: false`, `oa_status:
closed`), Semantic Scholar (`openAccessPdf: null` or `status: CLOSED`).
S2 `status: GREEN` means an OA PDF URL exists — attempt the download
before declaring closure. Record the closure in the Ingest log. Set
`needs-enrichment: true` — this is the ONLY case where that flag is
appropriate.

**Known publisher blocks.** See `references/publisher-blocks.md` for
the full table of publisher-specific retrieval behavior, CDX recipes,
and per-pattern guidance. The general decision for any blocked
publisher: PMCID present → PMC XML → EPMC PDF → Wayback CDX; no PMCID
→ jina reader on publisher URL → Wayback CDX → abstract-only.

**Reference-list masquerade** (all subscription Springer/Nature/Wolters
Kluwer content): jina returns 50K+ chars that passes the size check but
the content is entirely reference titles — no body paragraphs. Always
grep for body section headings (Introduction, Methods, Results,
Discussion) before tagging `fulltext_source: jina-reader`. If only
references, treat as abstract-only.

**Figure images (optional).** `fetch_fulltext.py --figures` scrapes
figure images from the PMC article page. Figures are distillation-time
working material (`/tmp`, ephemeral); `vision_analyze` reads them into
Findings.

### 5. Distillation and page write

Write `papers/<slug>.md` per the paper-kind schema. Body anatomy:
Abstract / Context / Approach / Findings (specific results tied to
figures) / Limitations / Analysis, plus `## Ingest log` and `## Citation`.

**Verify the task brief against the full text before writing Findings.**
A parent task's pre-filled "key findings" are a convenience, not a
primary source — they can conflate closely related molecules or
misattribute structural features. Grep the fetched full text for each
key claim. If the full text contradicts the brief, trust the full text;
record the discrepancy in a prominent body note. Do NOT silently
overwrite the brief's claims — flag and let your human decide.

**Abstract-only distillation checklist.** When `fulltext_source:
abstract-only`, the abstract is the *entire* available text — every
sentence must be read for extractable signal, not skimmed for the
headline finding. Before writing the page, scan for these high-value
elements and include each one that appears:

- **Structures** (cryo-EM, X-ray, NMR) — resolution, complex
  composition, what it reveals.
- **Discovery method** — phage display, single B cell cloning, hybridoma,
  humanized mice. Do not assume from the lab's reputation.
- **Epitope / target site** — receptor-binding site, F apex, quaternary
  epitope, etc.
- **In vivo model and survival** — species, % survival, treatment window.
- **Cross-reactivity** — which strains/variants are neutralized.
- **Affinity / potency** — IC50, KD, neutralization titers.

The failure mode this prevents: writing a distillation focused on one
angle while missing a co-equal result that the abstract states in a
single sentence. When distilling from abstract-only, there is no second
chance to find it in the full text.

**Stub replacement / slug renaming.** When the task specifies a
different slug than an existing stub for the same paper (same DOI):
create the page at the task-specified slug, copy the stub's `cited_by`
into the new page (append-only, preserve all entries), delete the old
stub, log the rename, and grep the vault for inbound references.

**Frontmatter.** `fulltext_source:` from the retrieval provenance;
`needs-enrichment: true` ONLY for genuine abstract-only (branch 3) or
preprint-in-place-of-published distillation; `status:` is
`preprint`/`published`/`unknown` only — never `withdrawn`, `accepted`,
or `in review` (linter rejects). Every author goes in `authors:` as
`people/<slug>` (Phase 8).

**Ingest log on success-with-deviation.** A fill that succeeded via a
non-standard path is not "clean": append a timestamped log entry
(identity fallback used, full text not retrieved, `needs-enrichment`
set and why). These are provenance notes for the next enrichment run.

### 7. Bibliography walk

Walk the ingested paper's reference list and create **stubs** for
load-bearing citations. The anchor test: "the paper would lose its
argument without this reference" — a method it depends on, a dataset it
analyzes, a framework it extends. Not context citations. Stubs carry
`needs-ingest: false` and accumulate `cited_by`; when a stub crosses 5+
independent citing sources, `ingest-pending-papers` fills it. This
threshold gate is what prevents the exploding paper tree — do not
inline-ingest walk results.

### 8. Author ledger

Every author on the paper goes into the paper's `authors:` list as
`people/<slug>` — the COMPLETE list, paged or ledger-only. Three
branches per author:

- **Branch 1 — existing person page:** append the paper to the page's
  `author_on:`.
- **Branch 2 — existing ledger entry:** append the citation to the
  entry's `citations:`.
- **Branch 3 — new:** append a ledger entry (slug, name, orcid,
  affiliations, citations).

A task instruction "do NOT create author ledger entries" scopes to
Branch 3 only — Branch 1 `author_on:` updates on existing person pages
are still required. The stronger scope "Write ONLY the paper page"
skips ALL of Phase 8 (no person-page or ledger mutations), Phase 7
(bibliography walk), and Phase 9 (graph wiring) — the orchestrator owns
all post-page wiring. Still perform the pre-write slug alignment below
so the `authors:` list uses correct existing slugs. Return the complete
author list in the task summary. `verify_ingest.py` will report
unresolved authors — this is **expected** for this scope, not a failure.

**Pre-write slug alignment (mandatory).** Before writing `authors:` or
appending anything, search BOTH the ledger and person pages by SURNAME:
`grep -i "name:.*<LastName>" people/_ledger.yaml` and
`ls people/ | grep -i '<surname>'`. Use the existing entry's exact slug;
mint a new one only when nothing matches. For short surnames (Yi, Hom,
Li, Wu, etc.), use `slugify_name.py --filter-surname` for token-match
filtering — bare grep returns dozens of substring false positives.

**Conflation check (mandatory).** When the pre-write alignment finds an
existing ledger entry OR person page matching by surname, do NOT assume
it's the same person — compare the paper's PubMed affiliation against
the entry's `affiliations:` or the person page's `affiliation:`/body.
If they disagree on institution or geography, the entry conflates two
different people. Under the stronger scope, flag prominently in the
Ingest log (name both people, propose a disambiguated slug). Otherwise,
create a NEW disambiguated entry
(`slugify_name.py` handles slug derivation) and log a normalization-pass
flag for `entity-resolution`.

**Slug derivation.** Use `slugify_name.py` — it handles diacritic
folding (Ł→l, ø→o, ß→ss), PubMed name misparsing (Korean,
Italian-particle), and corporate authorship. When a pre-existing entry
uses a misspelled or non-convention slug: merge via Branch 2, align
frontmatter to the EXISTING slug, never rename the ledger entry.

**The frontmatter `authors:` list and the ledger `slug:` field MUST use
identical slugs** — the lint resolves by exact string match. Build the
slug list once, use it for both. The ledger `name:` display field
retains diacritics.

**ORCID capture (three lines, then stop):**
1. PubMed XML `<Identifier Source="ORCID">` — often senior-author only.
2. Europe PMC REST core search (the branch-0 gate call):
   `resultList.result[0].authorList.author[].authorId` (type `ORCID`).
   Guard with `isinstance(..., str)` before string ops — `authorId` can
   be a dict.
3. CrossRef preprint deposit: `api.crossref.org/works/<preprint-doi>` →
   `message.author[].ORCID` — carries junior/middle-author ORCIDs
   PubMed lacks.

Union all three. When all empty, `orcid: null` — never fabricate ORCIDs.

**Inline promotion.** When a ledger entry hits 5 citations mid-ingest:
create `people/<slug>.md` (kind: person, orcid from the ledger,
`author_on:` = every citation in the entry); remove the ledger entry via
targeted `patch` of its whole block (NEVER `yaml.dump` the ledger);
verify the ledger parses, the slug is absent, no duplicates.

**Ledger append mechanics.** Appending to `people/_ledger.yaml` is the
most failure-dense operation. The canonical procedure is one ATOMIC
python3 heredoc: read → check for missing slugs → conditionally append
→ immediately `yaml.safe_load` + duplicate-slug check + author-count
check, all in a single execution. Splitting append and verify across
tool calls leaves a window in which a sibling's full-ledger rewrite
silently drops your entries. Re-verify at Phase 10 and re-append
atomically if missing. Never append via `cat >>` heredoc. When patching
an existing entry, anchor `old_string` on the entry's unique `slug:` line
plus a distinguishing field — generic anchors can silently match the
wrong entry.

### 9. Graph wiring and propagation

Link the page into the graph: search the vault for concept/project pages
matching the paper's topic and add typed edges per `graph-and-links.md`.
Use `patch` for appends to shared frontmatter lists (`links:`,
`cited_by:`), never whole-page `write_file`.

Then enqueue propagation — append to `docs/rem-cycle/inbox.yaml` (plain
list append under `items:`, dedup on `id`, NEVER rewrite the file):

```yaml
  - id: <YYYY-MM-DD>-<slug>
    page: papers/<slug>
    event: ingest            # or: stub-filled
    date: YYYY-MM-DD
    consumed_by: []
```

Indentation is 2-space `  - id:` with 4-space fields — verify with
`yaml.safe_load` after the append.

### 10. Verification

Run `scripts/verify_ingest.py <paper-slug>` (auto-detects the brain root
from `papers/` + `people/`, or `--instance <path>`). Five graph invariants:

1. Paper frontmatter parses as valid YAML.
2. All `links:` targets exist as pages on disk.
3. All `authors:` slugs resolve to `people/` pages OR ledger entries.
4. All `cited_by:` targets exist.
5. The ledger parses and has no duplicate slugs.

Plus a **canonical-identity phase** (network; `--offline` skips it):

6. The page's real-world identity reads back against canonical sources —
   the DOI resolves and its title matches the page title (wrong-DOI
   defects land silently without this: a DOI can resolve cleanly to a
   *different* paper), the PMID's DOI agrees with the page DOI, the
   author list is complete against PubMed (truncated lists are the
   classic silent failure — an ingest that resolved the first few
   authors and stopped passes every graph check), and retractions are
   surfaced. A page whose `authors: []` is collective-only
   (trial-group authorship) passes — collectives are excluded from the
   canonical count.

**Name-based duplicate check** across all newly added ledger entries —
slug-based verification misses same-person entries under
spelling/middle-initial variants. Merge any found (keep the
ORCID-bearing entry, union citations and affiliations).

**Schema lint (required, non-delegable).** The invariants above are
graph-level; they do not check the schema. A page with a missing
`status:` or a slug that mismatches its filename passes all five and
lands in CI red (this exact gap shipped chomicz-2026 without `status`
on 2026-08-30). After `verify_ingest.py`, run the platform linter in
scoped mode on exactly the files this ingest touched:

```bash
python3 <platform-repo>/core/tools/lint-frontmatter.py \
  --instance <brain> \
  --paths papers/<slug>.md people/_ledger.yaml
```

Sub-second (structure everywhere, field checks on the listed files
only). Exit 0 = commit-ready. A page that fails its own lint is an
unfinished write, not debt to fix later.

**External URLs in `links:` always report as MISSING** — this is a false
positive. Paper pages conventionally carry the DOI URL as their sole
`links:` entry. Only treat `links:` MISSING as actionable when the
target is an internal path, not an `https://` URL.

**Delegated ingests that skip the author ledger.** Two scopes exist:

- **"do NOT create author ledger entries"** — scopes to Branch 3 only.
  `verify_ingest.py` reports only authors with no ledger entry and no
  person page.
- **"Write ONLY the paper page"** — stronger scope: skips ALL of Phase 8,
  Phase 7, and Phase 9. `verify_ingest.py` reports authors with NO
  pre-existing entry as unresolved — **this is expected, not a bug.**
  Triage the UNRESOLVED list; check the other four invariants; if those
  pass, the page is commit-ready. Log: "Phase 10: N authors unresolved —
  deferred to parent per task constraint."

**Resolved-but-conflated slugs.** A resolved slug is not necessarily
correct. Under the stronger scope, manually review each resolved slug's
`affiliations:` against the paper's PubMed affiliations. Flag any
conflation in the Ingest log; the page is still commit-ready, but the
flag must be visible so the orchestrator doesn't silently wire to the
wrong person.

## Concurrency hazards (parallel sibling ingests)

`ingest-pending-papers` and `literature-dive` run this pipeline in
parallel; siblings share `people/_ledger.yaml`,
`docs/rem-cycle/inbox.yaml`, person pages, and concept pages.

| Shared file | Mutation rule | Verification |
|---|---|---|
| `people/_ledger.yaml` | Atomic python3 heredoc (read→append→verify in one call). NEVER `yaml.dump` (whole-file rewrites produce unreadable diffs and clobber siblings) | `yaml.safe_load` + duplicate-slug check + author-count check |
| `docs/rem-cycle/inbox.yaml` | `patch` on unique `- id:` anchor, never `write_file` | `yaml.safe_load` + item count +1 + no duplicate keys |
| Person pages (`author_on:`) | `patch`, never `write_file` | YAML well-formed after patch |
| `cited_by:` / `links:` | `patch` on shared frontmatter | Re-read after sibling warning |
| `/tmp` artifacts | Prefix with PMID/slug (never bare `/tmp/paper.xml`) | grep title before distillation |

General rules: `patch` never `write_file` on shared files; on a
sibling-modification warning, re-read and re-patch against current
state; verify after every mutation — a clean exit code proves nothing.
On `patch` "Could not find a match" + sibling warning, re-read and
re-apply. Anchor `old_string` on unique context (the target's slug +
distinguishing field), and verify the diff touched the right entry.

**When terminal `curl` is denied**, `execute_code` with Python
`urllib.request` is the first fallback — it fetches all E-utilities
endpoints identically to curl, with the same rate-limit discipline. The
entire pipeline (Phase 1 → Phase 4 → Phase 5) can run through
`execute_code` when terminal is blocked. When `execute_code` is also
unavailable, the browser can fetch E-utilities directly.
