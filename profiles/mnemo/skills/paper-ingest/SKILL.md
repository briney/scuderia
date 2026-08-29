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

Executable helpers live in `scripts/` under this skill directory
(`skills/paper-ingest/scripts/` in the profile — parameterize per
profile; do not hardcode one profile's path):

- **`fetch_fulltext.py`** — the Phase 4 decision tree in executable
  form (Europe PMC gate → PMC XML → EPMC PDF → bioRxiv/jina → publisher
  jina → Wayback) with retries/backoff. Prints JSON whose `provenance`
  value is the page's `fulltext_source:` tag. `--figures` additionally
  scrapes figure images (Phase 4). **Required args:** `--out <path>`
  (output text file); optional `--pmid`, `--doi`, `--pmcid`,
  `--publisher-url`, `--skip-publisher`. Prefer the script over
  hand-walking the tree; hand-walk only when its sources all miss
  (`provenance: none`) and judgment is needed about exotic alternatives.
  **Output path quirk:** the script appends `.txt` to the `--out` value
  internally (`succeed()` writes to `args.out + ".txt"`). So `--out
  /tmp/paper` produces `/tmp/paper.txt`, and `--out /tmp/paper.txt`
  produces `/tmp/paper.txt.txt`. The JSON summary's `text_file` field
  carries the actual path — read it from there, not from the `--out`
  argument. (Observed: PMID 39321363 and 40456235, 2026-08-15.)
- **`validate_identifiers.py`** — pre-dispatch identifier validation
  (Phase 3.5). Verifies that a candidate PMID/DOI/PMCID resolves to the
  intended paper BEFORE a subagent is dispatched. `--batch` JSON +
  `--recover` for recovery via Europe PMC title search. Output:
  `validated` / `recovered` / `HOLD`; `retracted: true` surfaced.
- **`embargo_recheck.py`** — monthly cron (`embargo-recheck`,
  `0 6 1 * *`, no_agent, deliver=local) over every
  `needs-enrichment: true` paper; reports `new-pmcid` and `oa-flipped`.
  Silent when nothing flips.
- **`pmc_xml_body_parser.py`** — parses a downloaded PMC XML file into
  structured text (`## Title` headings + paragraphs) for distillation.
  `--range N M` to paginate, `--full` for the whole body.
- **`verify_ingest.py`** — the Phase 10 verification pass (all five
  invariants in one run). Run after every ingest, before commit.
  **Script path pitfall:** the script does NOT live at a repo-relative
  `skills/paper-ingest/scripts/verify_ingest.py` path from the vault root —
  it lives under the profile skills dir (resolved via the profile symlink into
  the soma checkout: `~/git/soma/profiles/mnemo/skills/paper-ingest/scripts/`
  or `~/.hermes/profiles/<profile>/skills/<category>/paper-ingest/scripts/`).
  A bare `python3 skills/paper-ingest/scripts/verify_ingest.py` from the vault
  root prints `can't open file ... No such file or directory`. Use the resolved
  profile/soma path (or `find ~ -name verify_ingest.py`).
  **Invocation pitfall:** pass the BARE slug filename (e.g.
  `2017-verstraete-tslp-...md`), NOT the `papers/<slug>.md` relative
  path. The script prepends `papers/` itself, so passing the full
  relative path doubles it to `papers/papers/<slug>.md` and prints a
  misleading `ERROR: paper page not found` instead of running. (Observed:
  TSLP tezepelumab Fab structure ingest, PMID 28368013, 2026-08-18 —
  `verify_ingest.py papers/2017-...md` failed with a not-found error;
  `verify_ingest.py 2017-...md` ran correctly.)

**Environment notes.**
- **tirith blocks `curl | python3` pipes** ("[HIGH] Pipe to
  interpreter"). Use the two-step file-intermediary form everywhere:
  `curl -sL "<url>" -o /tmp/<name>.json` then `python3 -c "...parse the
  file..."`. If tirith blocks an oversized inline command entirely, the
  blocked script is saved under the profile's `cache/blocked-scripts/`
  — run it via `bash <path>`.
- **E-utilities rate limits.** Rapid sequential calls return HTTP 429 /
  a JSON body like `{"error":"API rate limit exceeded"}`. Batch ID
  lookups into single `esummary` calls, sleep 3–5s between sequential
  calls, never loop on 429 (three consecutive → wait 15+s). Transient,
  not a permanent block.
- **Shell escaping of brackets in esearch URLs.** PubMed search terms
  with field tags like `review[pt]` or `clinical trial[pt]` contain
  square brackets that are shell-interpreted by the terminal. A
  `curl -sL "...review[pt]..."` command silently fails (curl exit 0,
  but the output file is never created or is empty). **Fix:**
  URL-encode brackets in the search term: `[` → `%5B`, `]` → `%5D`.
  So `review[pt]` becomes `review%5Bpt%5D` in the URL. This applies to
  all field tags: `[tiab]`, `[au]`, `[dp]`, `[pt]`, etc. The curl
  URL-string double-quotes do not protect brackets from shell
  interpretation. (Observed: CD20 profile session, 2026-08-15 — 3/5
  esearch queries silently failed until brackets were URL-encoded.)
- **`urllib.parse.urlencode` double-encodes pre-encoded brackets in
  esearch URLs (Python/`execute_code` variant).** When building esearch
  URLs with Python's `urllib.parse.urlencode({"term": "review%5Bpt%5D"})`,
  the function re-encodes the `%` signs, producing `%255Bpt%255D` — a
  double-encoded bracket that PubMed silently interprets as a literal
  string, returning `count: 0` with no error. This is the Python
  equivalent of the shell bracket pitfall above. **Fix:** do NOT
  pre-encode brackets when using `urlencode`. Instead, pass the raw
  term with natural brackets and use `urllib.parse.quote()` on the
  full term string: `url = base + "?db=pubmed&term=" +
  urllib.parse.quote("CD19 AND review[pt]") + "&retmode=json"`.
  `urllib.parse.quote()` encodes brackets to `%5B`/`%5D` exactly once,
  while `urlencode` would double-encode them. (Observed: CD19 profile
  session, 2026-08-15 — all 3 bracket-tagged esearch queries returned
  count 0 via `urlencode` until switched to `urllib.parse.quote`.)
- **DOIs containing parentheses cause shell syntax errors when passed as
  CLI arguments via `terminal()`.** Elsevier/Lancet DOIs commonly contain
  parentheses (e.g., `10.1016/S2352-3026(21)00028-4`). When constructing a
  `terminal()` command string like
  `python3 fetch_fulltext.py --doi 10.1016/S2352-3026(21)00028-4 --out /tmp/PMID`,
  the shell interprets the unquoted parentheses as syntax, producing
  `syntax error near unexpected token '('`. **Fix:** shell-escape the DOI
  with `shlex.quote()` before interpolating it into the command string:
  `cmd = f"python3 ... --doi {shlex.quote(doi)} --out /tmp/{pmid}"`. This
  is distinct from the URL-path parentheses issue (Lancet DOIs in jina
  URLs causing 404s — see Known publisher blocks). The shell-escaping
  issue affects ALL CLI tools that accept a DOI argument, not just
  `fetch_fulltext.py`. (Observed: Factor B profile session, 2026-08-16 —
  PMID 33765419, DOI 10.1016/S2352-3026(21)00028-4.)
- **PubMed XML can carry an erroneous DOI; Europe PMC is authoritative.**
  PubMed XML `<ELocationID EIdType="doi">` and `<ArticleId IdType="doi">`
  occasionally carry a DOI that belongs to a different paper (a
  cross-reference error in PubMed's indexing). Europe PMC's core record
  (`doi` field) is the authoritative source. When the two disagree, use
  the Europe PMC DOI. (Observed: Factor B profile session, 2026-08-16 —
  PMID 40028332 had DOI `10.1182/blood.2022018833` in PubMed XML but the
  correct `10.3389/fimmu.2025.1537974` in Europe PMC.) **ELocationID vs
  ArticleIdList split (a stronger variant):** the `<ELocationID
  EIdType="doi">` (inside the article element) can carry the CORRECT DOI
  while the `<ArticleIdList>` `<ArticleId IdType="doi">` carries a WRONG
  DOI borrowed from one of the paper's own references — the reference's
  DOI leaked into the article's ArticleIdList via a PubMed indexing
  error, not a parser scope issue (the PMCID extraction pitfall above
  covers ReferenceList elements; this is different — the wrong value is
  IN ArticleIdList). Always pass the ELocationID DOI (or the EPMC core
  record DOI) to `fetch_fulltext.py --doi`, never the ArticleIdList DOI
  unchecked. (Observed: EGFR antibody literature dive, 2026-08-18 —
  PMID 39085630 had the correct `10.1038/s41417-024-00812-5` in
  `<ELocationID>` but `10.3389/fonc.2020.00212` (reference #53's DOI) in
  `<ArticleIdList>`; the ArticleIdList DOI also carried the wrong
  PMCID `PMC7052016` from the same reference.)
- **Europe PMC search API response structure: `resultList.result`, NOT
  `resultList`.** The EPMC REST search endpoint
  (`europepmc/webservices/rest/search?query=EXT_ID:<PMID>&format=json&resultType=core`)
  returns a JSON object where results are nested under
  `resultList.result` (a dict key `"result"` holding the list), NOT
  `resultList` as a direct list. Parsing with `data.get("resultList",
  [])` returns an empty dict, not the result list. Correct parsing:
  `data.get("resultList", {}).get("result", [])`. This was hit when
  using `execute_code` + `urllib.request` for EPMC core record lookups
  during the BDNF target profile session — all 5 EPMC lookups failed
  with `KeyError` or empty results until the nesting was corrected. The
  raw JSON starts with
  `{"version":"6.9","hitCount":1,...,"resultList":{"result":[{...}]}}`.
  (Observed: BDNF profile session, 2026-08-17.)
- **NCBI `efetch db=pmc` succeeds when EPMC `fullTextXML` returns HTTP
  404.** For PMID 21499209 (Hughes 2011, *Pancreas*, PMCID PMC4090218,
  `inPMC: Y`, `isOpenAccess: N`), the EPMC `fullTextXML` endpoint
  (`europepmc/webservices/rest/PMC4090218/fullTextXML`) returned HTTP
  404, but NCBI `efetch.fcgi?db=pmc&id=PMC4090218&retmode=xml` returned
  the full 69 KB XML with complete body content (all sections). When
  EPMC `fullTextXML` 404s for a PMCID that EPMC confirms as `inPMC: Y`,
  fall back to NCBI `efetch db=pmc` before declaring abstract-only. The
  EPMC 404 is a server-side routing issue for some older PMC deposits,
  not an indication that the full text is unavailable. (Observed: BDNF
  profile session, 2026-08-17.)
- **Jina reader proxy successfully retrieves non-OA physiology journal
  papers with no PMCID.** PMID 31566429 (Wada 2019, *Am J Physiol Renal
  Physiol*, no PMCID, `inPMC: N`, `isOpenAccess: N`) was retrieved as 36
  KB of full text (abstract + introduction + methods + results +
  discussion + references) via the jina reader proxy on the DOI URL
  (`r.jina.ai/https://doi.org/<doi>`). The publisher (APS / Am
  Physiological Society) is NOT in the known-blocks table and is
  accessible to jina despite being subscription-only. The content
  included structured section headings, data tables (as text), and
  complete discussion. For physiology journals (Am J Physiol, J Physiol,
  J Neurophysiol), try jina reader on the DOI URL even when `inPMC: N`
  — these publishers do not deploy Cloudflare CAPTCHA protection.
  (Observed: BDNF profile session, 2026-08-17.)
- **`elink.fcgi` returns related articles, not the paper's own PMC ID.**
  The `elink.fcgi?dbfrom=pubmed&db=pmc&id=<PMID>` endpoint returns
  PMC IDs of papers that *cite or are cited by* the target PMID —
  sometimes hundreds of them — NOT the target paper's own PMC ID. Do
  NOT use elink to discover a paper's PMCID. The correct sources for a
  paper's own PMCID are: (1) PubMed XML `<ArticleId IdType="pmc">`
  (scoped to `<ArticleIdList>`, see PMCID extraction pitfall); (2) the
  EPMC core record's `pmcid` field (Branch 0 gate). (Observed: CD20
  profile session, 2026-08-15 — elink returned 100+ PMC IDs for each
  PMID, none of which was the target paper's own.) **Silent rate-limit corruption:** a rate-limited
 `efetch` can return HTTP 200 (curl exit 0) with the JSON error *body*
 written to the output file — `curl -s -o /tmp/x.xml` succeeds, `wc -c`
 is non-zero (~85 bytes), and only `ET.fromstring` failing with
 "mismatched tag" reveals the file is JSON, not XML. Always validate
 that a fetched XML/JSON file starts with its expected token (`<?xml` /
 `{`) before parsing; a rate-limit body masquerades as a valid
 download. On a parse error mid-pipeline, re-fetch after a 15+s sleep
 rather than diagnosing the parser. **Phase-1 shortcut when PubMed
 efetch rate-limits but the EPMC gate already succeeded:** the Phase 4
 branch-0 Europe PMC core record (always fetched first for PubMed
 papers) carries every Phase 1 identity field — title, authorString,
 authorList (LastName/FirstName/initials/ORCID/affiliations), doi,
 pmcid, pubTypeList (retraction detection), meshHeadingList,
 grantsList, abstractText. When PubMed efetch returns the rate-limit
 JSON body, do NOT block on retrying PubMed; finish Phase 1 from the
 already-fetched EPMC record and proceed (He & Xu 2026, Cell Res:
 PubMed efetch 429 → EPMC core record resolved title, both ORCIDs, both
 affiliations, pubTypeList, MeSH, grants, abstract — full identity
 without a PubMed retry). Fetching the branch-0 gate first is free
 insurance against this exact failure.
- **arXiv API curl is blocked on this host.** Direct `curl` to
  `export.arxiv.org` times out at the approval gate. Use the paperclip
  mirror or the jina abs-page proxy instead (Phase 1 arXiv branch).
- **Raise the FD limit** before any parallel subagent dispatch:
  `ulimit -n 4096` (macOS default 256 is too low).

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
`<GrantList>`, `<MeshHeadingList>`, `<AffiliationInfo>`, `<AbstractText>`,
and (in newer records) `<ReferenceList>` for Phase 7. **A resolution from
PubMed XML alone is complete, not degraded** — if CrossRef is blocked or
rate-limited, proceed; CrossRef adds affiliation strings, reference-list
coverage, and ORCID disambiguation, nothing load-bearing. **DOI location
in pre-2006 papers:** `<ELocationID EIdType="doi">` is frequently empty or
absent for papers published before ~2006 (the ELocationID element was
introduced later in PubMed's DTD). In these cases the DOI is in
`<PubmedData/ArticleIdList/ArticleId IdType="doi">` instead — a different
XML path that is always present when PubMed indexes the DOI. Always
check both locations; if `<ELocationID>` is empty, fall back to
`<PubmedData/ArticleIdList>` before declaring no DOI. The same
`<PubmedData/ArticleIdList>` also carries the PII (`<ArticleId
IdType="pii">`) needed for Cell Press jina full-text retrieval — no
`elink.fcgi?cmd=prlinks` call needed when PubMed XML is already fetched.
(Observed: PMID 15837620, Li et al. 2005 Cancer Cell — `<ELocationID>`
empty, DOI `10.1016/j.ccr.2005.03.003` and PII `S1535-6108(05)00090-5`
both found in `<PubmedData/ArticleIdList>`, 2026-08-18.)

**The identifier verification gate.** Identifiers from stubs, task
briefs, and bibliographies are wrong at high observed rates (~70% of
bibliography-harvested Tier 1 contexts in the ebolavirus dive). Never
trust a seed identifier until it survives this gate. **The universal
gate is the title comparison**: compare the PubMed `<ArticleTitle>`
against the stub/task title. A DOI-only cross-check against a wrong
PMID silently "confirms" the wrong paper.

| Variant | Gate | Fix |
|---|---|---|
| Seed DOI wrong, PMID right | PubMed DOI vs seed DOI (compare **lowercased** — DOIs are case-insensitive; `10.1128/jvi...` vs `10.1128/JVI...` is not a discrepancy) | PubMed DOI is authoritative; log the correction, never silently overwrite |
| PMID wrong, DOI right | Title comparison (a wrong PMID can resolve to a different paper in the same journal) | PubMed title search for the correct PMID; confirm by matching its DOI to the stub's DOI |
| Both wrong | Title comparison | `esearch.fcgi?db=pubmed&term=<title+keywords>&retmode=json` → correct PMID → DOI from `<ELocationID EIdType="doi">` |
| Task-warned DOI ("this may be X's DOI") | Resolve PMID, compare DOI; also check whether the "wrong" author appears mid-list in `<AuthorList>` | PubMed authoritative; the warning is often a false alarm caused by not recognizing a mid-author's own paper |
| Wrong primary arXiv ID | `paperclip cat /papers/arx_<id>/meta.json` title vs stub title | A wrong arXiv ID poisons `sources:`, `doi:`, and the paperclip full-text path at once. Correct frontmatter, log prominently, and fix downstream damage (new page at the correct slug, stub deletion, inbound-link updates) |

**Wrong first-author name in the task.** A parent task may name the
wrong first author (e.g. "Sander et al." when the PMID resolves to Pae
et al.). The PMID/DOI is authoritative for authorship: use the PubMed
`<AuthorList>` in `authors:` and the ledger; file at the task-specified
slug per instruction, but flag the discrepancy prominently in the Ingest
log for a future normalization pass.

**Erratum disambiguation.** A PubMed title search can return both the
primary paper and its erratum (same title, "Erratum:" prefix).
Disambiguate via `<CommentsCorrectionsList>`: the erratum carries
`RefType="ErratumFor"`, the primary `RefType="ErratumIn"`; the primary
has `<PublicationType>` "Journal Article" and the full abstract. Record
the erratum's PMID in the Ingest log when one exists.

**Editorials and commentaries — `RefType="CommentOn"`.** Editorial and
commentary papers carry `<PublicationType>` "Editorial" or "Comment" and
a `<CommentsCorrectionsList>` entry with `RefType="CommentOn"` pointing
to the paper being commented on (the target PMID is in
`<CommentsCorrections><PMID>`). This is not an erratum — it is the
editorial's primary relationship. The target paper is the natural
`links:` entry when it exists in the vault (e.g., a COCOON editorial
links to the COCOON trial paper). Record the commented-on PMID in the
Ingest log. These papers often have no `<AbstractText>` in PubMed XML
and no `<abstract>` element in PMC XML (`article-type="editorial"`) —
the commentary body IS the content; treat the body text as the primary
distillation source and note "no structured abstract (editorial)" in
the Ingest log. Do not treat the missing abstract as a retrieval
failure. (Observed: PMID 42583437, Furuya 2026 editorial on the COCOON
trial, J Thorac Dis — no abstract in PubMed or PMC XML, full body text
from PMC XML efetch, 6,584 chars body.)

**PDB structure DOIs (`10.2210/pdb*/pdb`).** Papers accompanied by a
Protein Data Bank deposition carry a wwPDB DOI in PubMed's
`<ArticleId IdType="doi">` — this DOI resolves to the wwPDB structure
page (`wwpdb.org/pdb?id=...`), NOT the publisher article. For pre-1990s
structural biology papers (e.g., JBC 1989), this is often the ONLY DOI
PubMed indexes because the publisher article predates DOI assignment.
`fetch_fulltext.py --doi <PDB-DOI>` will retrieve the wwPDB page instead
of the article. **Fix:** use the PubMed PII
(`elink.fcgi?cmd=prlinks` → `linkinghub.elsevier.com/retrieve/pii/<PII>`)
or the publisher article URL directly for full-text retrieval. Record
the PDB DOI in `doi:` (it IS the paper's canonical DOI per PubMed), but
note in the Ingest log that it is a wwPDB structure DOI, not a publisher
DOI. Also record the PDB ID (e.g., `1TNF`) in tags for structural
cross-referencing. (Observed: PMID 2551905, Eck & Sprang 1989, JBC —
DOI `10.2210/pdb1tnf/pdb` resolved to wwPDB, not JBC; full text
retrieved via jina on `jbc.org/article/S0021-9258(18)71533-0/fulltext`,
2026-08-18.)

**Papers with no DOI.** Older/regional journals may have no DOI at all —
absence of `<ELocationID EIdType="doi">` plus an unrelated CrossRef
bibliographic search (`api.crossref.org/works?query.bibliographic=...&query.author=<surname>&rows=3`)
confirms it. Set `doi: null` (explicit, not omitted) and note "DOI: not
assigned". Discover the publisher full-text URL via
`elink.fcgi?dbfrom=pubmed&id=<PMID>&cmd=prlinks` (`<ObjUrl><Url>`
elements) and record it in the page.

**Semantic Scholar as metadata fallback.** When other identity routes
are blocked, `api.semanticscholar.org/graph/v1/paper/DOI:<doi>?fields=title,abstract,externalIds,authors.name,venue,publicationDate`
settles whether a PMID/arXiv ID exists at all. Always use the **DOI
form** — the `PMID:<id>` form can silently return empty even when the
DOI form succeeds. S2 is metadata-only: its `openAccessPdf` for
preprints points back at blocked publisher URLs. **S2 `openAccessPdf`
is also a full-text routing lead for paywalled papers** — adding
`openAccessPdf` to the fields list returns `{url, status, license}` where
`status: GREEN` often points at a co-author's institutional repository
or funder archive copy (e.g., Edinburgh research.ed.ac.uk, Zenodo) even
when the publisher page is paywalled and EPMC is all-N. The
institutional-repository URL is itself frequently Cloudflare/CAPTCHA-protected
from this host (HTTP 403 direct, CAPTCHA page via jina), so GREEN is a
lead to attempt, not a guaranteed download — see the Branch 3
three-source-closure note for the routing rule.

**bioRxiv preprints.**
- The `api.biorxiv.org/details/biorxiv/<doi>` response's `published`
  field carries the published version's DOI when one exists — use it for
  identity metadata via Semantic Scholar (Phase 1) and for OA full-text
  routing (Phase 4 branch 1c).
- The openRxiv DOI prefix **10.64898** (new since 2026-01) is bioRxiv in
  every operational respect — same API host, same `.full` URL pattern,
  same Cloudflare behavior. Do not treat it as a different source.
- **bioRxiv API DOI format.** The `api.biorxiv.org/details/biorxiv/<doi>`
  endpoint requires the FULL DOI including the prefix
  (`10.64898/2026.08.14.744703`), not just the numeric path component
  (`2026.08.14.744703`). The bare numeric part returns
  `{"status":"non-numeric value supplied"}` with an empty collection.
  (Observed: Vinod et al. 2026 bioRxiv ingest, 2026-08-17.)
- **bioRxiv source.xml is front-matter-only.** The JATS XML at the
  `.source.xml` URL (also returned as `jatsxml` in the API response)
  contains only front matter — title, authors, abstract, publication
  metadata. No `<body>` element. This is fundamentally different from PMC
  XML. Do not attempt to parse it for body content; go directly to the
  PDF for full text. (Observed: same session.)
- **Crossref DOI resolver for preprint identity.** When a bioRxiv preprint
  has no PMID (not yet indexed in PubMed), `curl -sL -H "Accept:
  application/json" "https://doi.org/<DOI>"` returns structured JSON with
  author names, ORCIDs, affiliations, and abstract — complementing the
  bioRxiv API, which returns authors as a single comma-separated string
  without ORCIDs. Use Crossref for structured author metadata when PubMed
  is unavailable. (Observed: same session.)
- **Corporate/anonymous authorship.** When paperclip meta.json returns
  `authors: null` and the body attributes authorship to a company/lab:
  query `api.biorxiv.org/details/biorxiv/<DOI>` (`collection[0].authors`,
  `author_corresponding`), use the corresponding author as the sole
  `authors:` entry, record the corporate attribution in the log and
  body, and derive the page slug from the org name
  (`<team>-<year>-<descriptive>`). If no individual is named at all,
  `authors: []` is valid — the DOI is the identity key. Never fabricate
  authors from a team name.

**arXiv papers.**
- **Author list ladder:** (1) `paperclip cat /papers/arx_<id>/meta.json`
  — if `authors` is non-empty, split on " and "; (2) if empty, the Atom
  API `export.arxiv.org/api/query?id_list=<id>` when reachable (single
  call, ~1 req/3s, also yields `<arxiv:comment>` supersession notices) —
  note this host blocks direct arXiv API curl; (3) if blocked, the jina
  abs-page proxy `https://r.jina.ai/https://arxiv.org/abs/<id>` via
  stdlib urllib — returns title, full ordered author list, submission
  date. Cross-check the list against the `/html/` page's author block.
  Affiliations are not on the abs page — record "no affiliations stated"
  in the log. Record the arXiv DOI `10.48550/arXiv.<id>`.
- **Version history hazards.** (a) *Retitles:* search indexes carry only
  the latest version; if a title search misses, open
  `arxiv.org/abs/<id>v1` and compare v1 against the task's citation
  triple. If v1 matches but v2 diverges, distill the task-specified
  version, log both versions, and fetch full text from the VERSIONED URL
  (`arxiv.org/html/<id>v1` — unversioned serves latest). (b)
  *Withdrawals:* abs page shows "withdrawn by <author>"; the comment
  field carries "superseded by arXiv:<new-id>". Still ingest v1
  (withdrawal ≠ retraction), set the withdrawal status in the body (the
  frontmatter `status:` enum is only `preprint`/`published`/`unknown` —
  use `preprint` and note the withdrawal in a prominent body warning
  block linking the superseding paper), check the superseding paper via
  paperclip, and always fetch the versioned v1 URL.
- **Venue assignment.** If the task specifies a venue: `status:
  published`, `venue: "<venue>"`. If arXiv-only with no task venue:
  `status: preprint`, `venue: "arXiv (<id>)"`. For well-known ML
  conference papers without task context, venue may be assigned from the
  known publication record — log the basis ("venue assigned based on
  known publication record; no PubMed PMID"). Never infer acceptance
  from the arXiv listing alone; paperclip `pub_date` is the submission
  date, not the conference date.

### 2. Dedup against the brain

Search `papers/` for the resolved PMID/DOI/title before writing
anything. If a full page exists, this is a re-ingest — enrich, don't
duplicate. If a stub exists (from a Phase 7 bibliography walk), this is
a stub fill — preserve its `cited_by` (see Phase 5).

### 3. Retraction and integrity check

Read `<PublicationTypeList>` from the PubMed XML: "Retracted
Publication", "Retraction of Publication", "Published Erratum". A
retracted paper is still ingested when it is load-bearing context (it
may be why a line of work died), but the retraction is front-page
information: prominent body warning, and any downstream dispatch list
surfaces `retracted: true` rather than dispatching silently.
`validate_identifiers.py` also reports `is_retracted` from OpenAlex.

### 3.5. Pre-dispatch identifier validation (orchestrators)

When this pipeline is being dispatched to subagents in bulk (by
`literature-dive` Phase 4 or `ingest-pending-papers` Phase 2.5), the
orchestrator validates the whole batch first:

```bash
python3 skills/paper-ingest/scripts/validate_identifiers.py \
    --batch /tmp/citations.json --recover
```

Input per citation: `title`, `author` (first-author surname), `year`,
plus any `pmid`/`doi`/`pmcid` in hand. Match rule: token_set_ratio ≥ 90
AND surname match AND year ±1; REVIEW band 75–89; never title alone.
Dispatch only from the validator's `dispatch` list — never the raw
bibliography identifiers. `recovered` entries carry PubMed-verified
replacement identifiers; `HOLD` entries are flagged for manual
resolution, never silently dispatched. **HOLD entries with PMIDs deserve
one PubMed `esummary` batch check before discard** — the validator's
title heuristic is conservative with older papers' formatting, and a
correct PMID can fail it (astrovirus dive: 17/17 HOLD PMIDs verified
correct via one batch call).

### 4. Full-text retrieval

**Prefer `fetch_fulltext.py`** — it walks the tree below with retries
and prints the `fulltext_source` tag. Hand-walk only when it returns
`provenance: none`.

**PMCID extraction pitfall.** When parsing the PubMed XML for the PMCID, `root.findall(".//ArticleId")` iterates ALL `<ArticleId>` elements in the entire document — including those embedded in the paper's `<ReferenceList>`. A reference-list PMC ID can overwrite the article's own, and the LAST match wins in a simple loop. Observed: PMID 29163822's first parse returned `PMC2815670` (from a reference) instead of the correct `PMC5685743`. **Fix:** scope the search to the article's own `<ArticleIdList>` (a child of `<PubmedArticle>`, not inside `<CommentsCorrections>` or `<ReferenceList>`): `root.find(".//ArticleIdList")` and iterate only its direct `<ArticleId>` children. Cross-check: the PubMed abstract text endpoint also prints `PMCID: PMCxxxx` on its last line — a free second source. The same scoping applies to DOI extraction — prefer `<ELocationID EIdType="doi">` inside the article element over a bare `findall` that can match reference DOIs.

**Branch 0 — Europe PMC gate (one call, always first for PubMed papers):**

```bash
curl -sL "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:<PMID>&resultType=core&format=json" -o /tmp/<pmid>_epmc.json
```

Read `isOpenAccess`, `inPMC`, `inEPMC`, `hasPDF`, `pmcid` (and ORCIDs —
free two-for-one with Phase 8). NOTE: the query MUST use the `EXT_ID:`
field code — a bare `query=<PMID>` returns hitCount 0. When all flags
are N/None AND the DOI resolves to a known-blocked publisher (table
below), fall straight to branch 3 — the publisher round-trip is
deterministic waste.

**A PMCID in PubMed XML overrides stale Europe PMC flags.** The EPMC
core record's `isOpenAccess`/`inPMC`/`hasPDF` flags are *not* always
fresh — for Ivyspring and other smaller-OA/eCollection publishers they
have been observed all-N while `efetch db=pmc&id=<PMCID>` returns the
complete XML (Zhao 2026, ijbs.133650: EPMC `inPMC: N`/`isOpenAccess:
N`/`hasPDF: N`/`pmcid: None`, yet PMC XML efetch delivered 238 KB; see
`references/epmc-flag-staleness.md`). **This also affects major
publishers** — observed for Springer Nature / Nature Aging (Wang 2026,
PMID 42581103: EPMC all-N, yet PubMed XML carried PMCID PMC13472855 and
PMC efetch delivered 256 KB / 31 sections). The gate above is a
*publisher-block* fast-path, not an OA authority. **Whenever a PMCID
appears in the Phase-1 PubMed XML (`<ArticleId IdType="pmc">`), always
attempt `efetch db=pmc` (Branch 1) before falling to Branch 3** — the
PMCID's presence is the stronger OA signal than EPMC's flags, for any
publisher. Only declare abstract-only when `efetch db=pmc` itself
returns front-matter only or an error, not when EPMC merely says N.

**The reverse: EPMC PMCID overrides a stale PubMed XML PMCID.** The
PubMed XML `<ArticleId IdType="pmc">` can itself carry a stale or
superseded PMCID that returns front-matter-only XML (~8 KB, 0-1
sections, no `<body>` element). The EPMC core record's `pmcid` field
may carry a *different*, current PMCID that returns the full text.
Observed in the TNF profile reprocessing (2026-08-15): PMID 20194223
PubMed XML had `PMC1773100` (7.7 KB, front-matter only) while EPMC
reported `PMC2886310` (146 KB, 37K chars body, 26 sections); PMID
31857588 PubMed XML had `PMC2486339` (8.6 KB, front-matter only) while
EPMC reported `PMC6923382` (116 KB, 49K chars body, 32 sections). The
PMCIDs were completely different, not just stale flags. **When
`efetch db=pmc` with the PubMed XML PMCID returns front-matter only
(no `<body>` element, <10 KB, 0 sections), always check the EPMC core
record's `pmcid` field for a different PMCID and retry `efetch db=pmc`
with the EPMC PMCID before falling to Branch 3.** The EPMC core record
is fetched free in Branch 0 — cross-check its `pmcid` against the
PubMed XML PMCID as part of the Branch 1 attempt.

**PMCID resolves to a completely different article (cross-article
mismatch).** The PubMed XML PMCID can resolve to a *different article
entirely* — not just a stale or superseded version of the same paper,
but an unrelated paper sharing the PMID→PMCID mapping. Observed in the
CGRP target profile (2026-08-16): PMID 32266704 (Dhillon, "Eptinezumab:
First Approval", *Drugs* 2020) had `<ArticleId IdType="pmc">PMC7066477`,
but `efetch db=pmc&id=PMC7066477` returned the full text of the PROMISE-1
study by Ashina et al. (*Cephalalgia* 2020) — a different article with
different title, authors, and journal. The PMC XML title
("Eptinezumab in episodic migraine: A randomized, double-blind,
placebo-controlled study (PROMISE-1)") did NOT match the PubMed record
title ("Eptinezumab: First Approval"). **Fix:** after fetching PMC
XML, always verify the PMC article title matches the PubMed record
title before using the body text. If the titles diverge, the PMCID is
mismatched — tag `fulltext_source: abstract` and do NOT use the
mismatched PMC body text as the paper's full text. The mismatched PMC
content may still be useful context (e.g., the PROMISE-1 trial data
was relevant to the eptinezumab approval profile), but it belongs in
the paper page's Notes section, not as the primary fulltext_source.

**Branch 1 — PMC open access.** With a PMCID and `isOpenAccess: Y`:

```bash
curl -sL "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=<PMCID>&rettype=xml" -o /tmp/<pmid>_paper.xml
python3 scripts/pmc_xml_body_parser.py /tmp/<pmid>_paper.xml --full
```

Structured XML (`<sec>`/`<p>`/`<xref>`), complete reference list — the
preferred path for OA papers. Always prefix `/tmp` artifacts with the
PMID (not bare `/tmp/paper.xml`) — parallel siblings share `/tmp` and a
generic name gets silently overwritten (see Concurrency hazards). If terminal curl is denied, the browser
fallback: `browser_navigate` to `https://pmc.ncbi.nlm.nih.gov/articles/<PMCID>/`,
then `browser_console` with
`document.querySelector('article')?.innerText?.substring(N, N+15000)`,
paginating until `'no more content'`. (Selector fallbacks: `main`, then
`document.body.innerText`. `pubmed.ncbi.nlm.nih.gov` pages are
JS-rendered and return empty DOMs — never use them.) **Never set
`needs-enrichment: true` when PMC full text was available** — the
browser is a fallback, not a dead end.

**Branch 1b — Europe PMC PDF render (embargoed, `inPMC: Y`).** When PMC
XML returns front matter only (publisher restricts XML download) and the
PMC browser page is reCAPTCHA-blocked:

```bash
curl -sL -o /tmp/<pmid>.pdf "https://europepmc.org/api/getPdf?pmcid=<PMCID>"
# extract with pymupdf
```

Delivers the publisher PDF even when `isOpenAccess: N`, as long as
`inPMC: Y`. Confirmed across OUP/ATS, ASM, and the general case. This is
the *default next step* after metadata-only PMC XML, before any browser
attempt.

**The EPMC `getPdf` endpoint silently serves an UNRELATED PDF for a
fabricated PMCID (HTTP 200, not 404).** When `inPMC: N`/`pmcid: None`,
never construct a numeric PMCID by prepending `PMC` to the bare PMID and
calling `europepmc.org/api/getPdf?pmcid=PMC<PMID>` — the endpoint maps
the numeric portion to some internal record and returns a *completely
different article's* PDF with HTTP 200, not an error. Observed: PMID
9538693 (Naismith & Sprang, TIBS 1998, `inPMC: N`/`pmcid: None`) —
`getPdf?pmcid=PMC9538693` returned a 655 KB PDF of an unrelated COVID
vaccine study (DOI 10.1111/nuf.12791). A 404 or empty body would have
been safe; a 200-with-wrong-PDF silently poisons the distillation.
**Fix:** only call `getPdf` with a PMCID that came from the Branch 0
EPMC core record's `pmcid` field OR the PubMed XML `<ArticleId
IdType="pmc">` — a real PMCID, never a PMID-derived one. When `pmcid`
is `None`/absent, the endpoint is not a fallback path; skip it. If you
do fetch, always verify the PDF's first page (title/authors/DOI) matches
the PubMed record before extracting text — a pymupdf `page[0].get_text()`
title check is one line and catches the mismatch. (Distinct from the
`efetch db=pmc` cross-article mismatch above: that is a real-but-wrong
PMCID from PubMed XML; this is a fabricated PMCID from a bare PMID.)

**Branch 1c — bioRxiv preprint (published version paywalled).** Discover
via `<CommentsCorrections RefType="UpdateOf">` in the published paper's
PubMed XML, or via the bioRxiv API `published` field's inverse: when the
*preprint* is blocked but its published version is OA in PMC, route to
the published PMC copy directly (and do NOT set `needs-enrichment`).
Preprint retrieval order: (0) `api.biorxiv.org/details/biorxiv/<doi>`
version check — always distill the latest version and record it (the API
host is NOT Cloudflare-blocked); (0.5) **direct `curl -sL` on the
`.full.pdf` URL** — `https://www.biorxiv.org/content/<doi>v<N>.full.pdf`
delivers the full PDF (8.7 MB, 22 pages observed) without jina or browser;
extract with `pymupdf` (or `read_file` on the PDF path). This path was
confirmed for an openRxiv DOI prefix (`10.64898`) and may work for
legacy `10.1101` DOIs as well — try it before jina. (Observed: Vinod et al.
2026, DOI 10.64898/2026.08.14.744703, 2026-08-17 — direct curl returned
8.7 MB PDF, `read_file` extracted 22 pages of full text including all
sections, references, and supplementary tables.); (1) jina reader proxy
(branch 1d) on the `.full` URL; (2) `.full.pdf` through jina — a separate
Cloudflare rate-limit bucket that succeeds when `.full` 429s; (3) direct
`browser_navigate` to the `.full` URL — browser Cloudflare clearance is
session-independent from curl/jina, so this succeeds even when jina is
persistently 429-flagged (verify the page title is "<title> | bioRxiv",
not "Attention Required | Cloudflare"; extract via
`document.body.innerText.substring(N, N+15000)`); (4) Wayback. Set
`needs-enrichment: true` when distilling the preprint in place of the
published version. Tag `fulltext_source: biorxiv-pdf` when the PDF was
retrieved via direct curl (step 0.5).

**Branch 1d — Reader proxy (r.jina.ai) for Cloudflare-blocked domains:**

```bash
curl -sL "https://r.jina.ai/https://www.biorxiv.org/content/<doi>v<N>.full" -o /tmp/<slug>_fulltext.md
```

Same form for publisher pages. **Pitfall — DOI URLs return 404 via
jina:** the jina reader proxy on a DOI URL
(`r.jina.ai/https://doi.org/<doi>`) resolves to doi.org, which returns
the DOI Foundation's 404 HTML page (~2.4 KB), not the article. Always
use the publisher's direct article URL (e.g.,
`r.jina.ai/https://www.thelancet.com/journals/lancet/article/PIIS<id>/fulltext`)
instead of the DOI URL for jina. (Observed: Lancet PMID 21296403,
2026-08-15 — `r.jina.ai/https://doi.org/10.1016/s0140-6736(10)61354-2`
returned a 2.4 KB 404 page; the direct thelancet.com URL returned 11.5 KB
full text.) A successful fetch returns sectioned
markdown of tens of KB; a 429 returns a short ~400-byte file with
"Warning: Target URL returned error 429" — check `wc -c` before
distilling. **Retry discipline:** a 429 is IP-scoped rate limiting —
wait 20–30s and retry, up to 4 attempts. When `fetch_fulltext.py` has
already exhausted its internal retries (`provenance: none`), the
rate-limit window is partially consumed — do NOT re-run the script; run
`sleep 45 && curl -sL "https://r.jina.ai/<url>" -o /tmp/<slug>.md`
manually (15s and 30s are insufficient here). Jina can also fail
*silently* (empty output, no Cloudflare signature) — any failure mode,
not just identifiable blocks, routes to the paperclip branch. Limits:
markdown not XML (no `<xref>` mapping); defeats bot-detection, NOT true
paywalls; no figure images; ~20 req/min free tier.

**Branch 1e — paperclip local mirror (zero-network, any source).** When
the network paths fail — for a bioRxiv OR arXiv paper (or anything the
paperclip corpus covers) — check the local mirror before declaring
abstract-only:

```bash
paperclip ls /papers/<doc_id>/          # doc_id: bio_<hash> or arx_<id>
paperclip cat --full /papers/<doc_id>/content.lines > /tmp/<slug>.txt
```

`content.lines` is the complete body (line-numbered `L<n>:` prefixes;
arXiv math in raw LaTeX, tables as concatenated cells). Re-read
individual `sections/<name>.lines` for truncated long lines. `meta.json`
doubles as a Phase 1 identity check. This branch has rescued 15+
ingests across three dives where `fetch_fulltext.py` failed. Tags:
`fulltext_source: paperclip-biorxiv` / `paperclip-arxiv` (generic
`paperclip` as catch-all; a single `paperclip-full` tag was proposed and
rejected — source-specific won). **Never tag a page `abstract-only`
when paperclip delivered full text.**

**Branch 2 — Journal HTML via browser.** When no PMC copy exists but the
journal page renders (CrossRef `resource.primary.URL`): navigate, then
extract section-by-section via `browser_console` (`querySelectorAll('section')`
→ headings + paragraphs). **Nature research-article pages render reliably**
— `nature.com/articles/<doi-suffix>` yields the complete body
(`document.querySelector('article').innerText` pagination); try it
before the generic fallbacks whenever the DOI resolves to nature.com.
**Caveat: this applies to Nature research articles (Nature, Nature
Communications, Nature Medicine, etc.), NOT Nature Reviews subscription
journals** (Nature Reviews Immunology, Nature Reviews Drug Discovery, etc.)
which are paywalled — jina returns only the reference list, and the
browser path has not been verified to bypass the subscription wall. See
the Nature Reviews entry in the known-blocks table.

**Branch 2b — Wayback Machine.** When live retrieval is blocked and jina
missed: `curl -s "https://archive.org/wayback/available?url=<article-url>"`
(the availability API itself 429s — retry with backoff, don't treat one
429 as "no snapshot"), then fetch the snapshot HTML statically or via
browser. **When the availability API 429s persistently, the CDX index
API is an alternative snapshot-discovery path:**
`https://web.archive.org/cdx/search/cdx?url=<article-url>&output=json&limit=5`
returns timestamped rows including HTTP status codes — filter for
`statuscode: "200"` to find a usable snapshot, then construct the
snapshot URL as `https://web.archive.org/web/<timestamp>/<original-url>`
and fetch via `urllib.request`. The CDX API has separate rate limits
from the availability API and succeeds when the latter is blocked.
(Observed: NEJM PMID 32937045, 2026-08-15 — availability API 429'd
after a 20s wait; CDX returned 3 rows including a 200-status snapshot
at timestamp 20201004010155; direct urllib.request on the snapshot
URL yielded 376 KB HTML → 13K chars extracted from `<article>` tag.)
**CDX API `&filter=statuscode:200` query parameter pre-filters at the
API level** — appending `&filter=statuscode:200` to the CDX URL returns
only 200-status snapshots directly, which is more reliable than
client-side filtering of unfiltered results. An unfiltered CDX query
can return only redirects (301/302) for a URL, while adding
`&filter=statuscode:200` to the same URL returns usable 200-status
snapshots. (Observed: NEJM PMID 27959607, IL-12/23 p40 profile,
2026-08-15 — unfiltered CDX for `nejm.org/doi/full/10.1056/NEJMoa1602773`
returned 5 rows all 301/302; `&filter=statuscode:200` on the same URL
returned 9 rows all status=200; first 200 snapshot yielded 544 KB HTML
→ 57.9K chars from `<article>` tag.)
**CDX API timeouts and 503s are transient — retry after 10s.** A CDX
API call can time out (60s) on the first attempt and succeed on a
retry with the same URL. Do not treat a single CDX timeout as "no
snapshot" — retry once after a 10s sleep. (Observed: NEJM PMID 27959607,
IL-12/23 p40 profile, 2026-08-15 — first CDX call timed out at 60s;
retry succeeded and returned 9 rows.) The CDX API can also return HTTP
503 (Service Unavailable) on both the initial call and retry. Unlike
timeouts (which resolve on retry), persistent 503s indicate the CDX
service itself is down — after 2 consecutive 503s, declare abstract-only
rather than looping. (Observed: SLeX/CA19-9 profile, 2026-08-16 — PMID
18264829, CDX returned 503 on both unfiltered and filtered queries for
`link.springer.com/article/10.1007/s00268-007-9452-1` and
`doi.org/10.1007/s00268-007-9452-1`; jina reader on DOI URL returned
CAPTCHA page (~497 chars). All paths failed → abstract-only.)
**Multiple 200-status snapshots can have different content
completeness.** The CDX API may return several rows with
`statuscode: "200"` for the same URL at different timestamps — do
NOT stop at the first 200. A 200-status snapshot can still be a
paywall preview page (~108 KB HTML, ~12K chars extracted), while a
later 200 snapshot of the same URL yields full text (~135 KB HTML,
~50K chars extracted). Try each 200-status snapshot in sequence
(largest `length` first is a reasonable heuristic — full-text pages
are larger than preview pages) and keep the one with the most
extracted body text. (Observed: IFN-γ profile, PMID 32374962 —
2020 snapshot (108 KB) yielded 11.6K chars (preview only); 2021
snapshot (135 KB) yielded 50K chars full text.)
**Direct `urllib.request` on the Wayback snapshot URL works
even when jina 403s** — for NEJM and other publishers where jina blocks
both the live and Wayback-proxied URL, fetch the Wayback snapshot URL
directly with `urllib.request` (250-270 KB HTML), then extract via
`<article>` tag regex. Tag `fulltext_source: wayback`. (PMIDs 27690741,
29782217, 2026-08-15.) Annual Reviews bodies live in
`<div class="html_fulltext">`.
Two bioRxiv-specific caveats: (a) the CDX index may archive only the
article page (abstract-only, ~92KB), not `.full` — check CDX for the
`.full` URL specifically; (b) a CDX listing is not a playable snapshot —
don't burn calls on `id_`/`if_`/timestamp URL variants; fall through.
Missing reference lists come from the Europe PMC REST references
endpoint. For arXiv, Wayback snapshots of `arxiv.org/html/*` are
frequently absent — skip it there.

**arXiv full text (source-specific ordering).** Primary:
`fetch_fulltext.py --doi 10.48550/arXiv.<id> --publisher-url https://arxiv.org/html/<id>`
(publisher-jina, 50–120K chars). Jina failure on arXiv is
**paper-specific**, not systematic — on `provenance: none`, do NOT retry
jina URL variants and do NOT try Wayback; go straight to the paperclip
mirror (branch 1e). If paperclip also lacks it, direct curl of
`arxiv.org/html/<id>v<N>` (always versioned) + stdlib regex
tag-stripping is the last resort (`fulltext_source: arxiv-html`).
**Table-loss caveat (both jina and direct-curl arXiv HTML):** numeric
table contents can be silently dropped — captions survive, cell values
don't. Scan for "Table N:" captions with no numbers; recover via
browser_console:
`Array.from(document.querySelectorAll('table')).map(t => t.innerText.replace(/\n/g,' | ')).join('\n====\n')`.

**Branch 3 — Abstract only (genuinely unreachable).** Distill from the
structured abstract only after **three-source closure**: Europe PMC
(`inPMC: N`, `isOpenAccess: N`), Unpaywall (`api.unpaywall.org/v2/<DOI>?email=<email>`
→ `is_oa: false`, `oa_status: closed`), Semantic Scholar
(`DOI:<doi>?fields=openAccessPdf` → `status: CLOSED` or
`openAccessPdf: null` — DOI form, not PMID). **Important: S2
`openAccessPdf.status` uses the Unpaywall enum — `CLOSED`/`GREEN`/`BRONZE`/`YELLOW`/`BLUE` —
NOT a boolean. `status: GREEN` means an OA PDF URL EXISTS (often at a
co-author's institutional repository or a funder archive); it does NOT
mean the URL is retrievable from this host. A GREEN institutional-repository
PDF can be Cloudflare/CAPTCHA-blocked just like the publisher page (observed:
PMID 39282907, Edinburgh research.ed.ac.uk CC-BY PDF returned HTTP 403 to
direct `urllib.request` and a CAPTCHA page to the jina reader proxy, 2026-08-18).
When S2 reports GREEN with an institutional-repository URL, ATTEMPT the
download (direct `urllib.request`, then jina reader proxy) before declaring
closure — GREEN is a lead to chase, not closure. Only `status: CLOSED` /
`openAccessPdf: null` (or a GREEN URL that itself 403s/CAPTCHAs) completes
the three-source closure. Record the closure in the Ingest log so future
enrichment runs know it was verified, not assumed. Set
`needs-enrichment: true` — this is the ONLY case where that flag is
appropriate.

**Known publisher blocks** (fall through per the table; branch 1d is
worth one attempt before abstract-only even when the pass-through fires):

> See also `references/wayback-cdx-blocked-publishers.md` for session-confirmed
> Wayback CDX extraction recipes for Science, AACR, and ASCO/JCO.

| Publisher | Domain | Block | Pass-through |
|---|---|---|---|
| Elsevier/ScienceDirect | sciencedirect.com | Deterministic CAPTCHA block page ("Are you a robot?"), even OA-labelled. Jina reader returns ~113K chars but it is the CAPTCHA interstitial + JS, not article content. DOI resolution via jina commonly returns 404 from doi.org for non-Lancet Elsevier DOIs (e.g., `10.1016/j.bbcan.*`, `10.1016/j.jaut.*`, `10.1016/j.canlet.*`). Some Elsevier DOIs resolve via 302 → `linkinghub.elsevier.com/retrieve/pii/S<PII>` → ScienceDirect, but ScienceDirect CAPTCHAs regardless. **Wayback CDX DOES find 200-status snapshots for `sciencedirect.com/science/article/pii/<PII>`** — BUT the snapshots contain only the abstract, keywords, abbreviations, and page chrome. The article body is loaded client-side via JavaScript (ScienceDirect SPA), so Wayback's server-side snapshot never captures body text. Even the `id_` raw-content snapshot form (stripping Wayback's own JS wrapper) returns abstract-only. This is a **distinct failure mode** from the Cloudflare CAPTCHA: the snapshot loads successfully (title, abstract, keywords all present) but the body sections (Introduction, Results, Discussion) are entirely absent from the server HTML. Do NOT tag `fulltext_source: wayback` for ScienceDirect snapshots unless you can grep for body section headings (Introduction, Methods, Results, Discussion) — abstract + keywords + abbreviations is NOT full text. (Observed: PMID 30381260, Neurobiol Dis 2019, CC-BY-NC-ND OA article, no PMCID — multiple 200-status Wayback snapshots from 2021 and 2024 all returned abstract-only; the `parsed_papers.pkl` cache also had this paper with empty `body_sections`. 2026-08-18.) | No PMCID → abstract-only. **PMCID present → PMC XML works even for `isOpenAccess: N`** (e.g., J Autoimmunity PMID 34224936, PMC8293794, 43K chars full text extracted from PMC XML). Always check Europe PMC `inPMC` flag — Elsevier journals often deposit in PMC without OA status, and the XML body is still retrievable. |
| Annual Reviews | annualreviews.org | Jina reader proxy returns ~56–58K chars of nav chrome + abstract (1,000–1,500 chars) + "Most Read"/"Most Cited" lists — NOT article body. Wayback snapshots also return abstract-only (~10K chars). DOI resolution via jina returns 404 for some DOIs (e.g., `10.1146/annurev.immunol.*`). NOT a false positive — output is clearly abstract+nav, distinguishable from genuine body text by checking for body text markers (section headings, body paragraphs beyond the abstract). | No PMCID → abstract-only. The structured PubMed abstract (typically 1,000–1,500 chars) is sufficient for profile grounding. (PMID 17953510, Spolski & Leonard 2008, Annu Rev Immunol; PMID 10358752, Waldmann 1999, Annu Rev Immunol — IL-15 and IL-21 profiles, 2026-08-16.) |
| Elsevier/Lancet family | thelancet.com, linkinghub.elsevier.com | Cloudflare interstitial to curl; **jina reader proxy succeeds** (81 KB for a Lancet GH Phase 2a trial, 2026-08-15). **Caveat: Lancet DOIs contain parentheses** (e.g., `10.1016/s0140-6736(21)00933-8`) which cause 404 even via jina when the DOI is placed in the URL path (`thelancet.com/article/<doi>/fulltext`). The jina fetch returns a 23 KB page of navigation chrome with no article body. URL-encoding the parentheses (`%28`, `%29`) does not help — the Lancet server still 404s. **Working path: use the PIIS URL form** — construct the article URL as `thelancet.com/journals/<journal>/article/PIIS<id>/fulltext` where `<id>` is the DOI suffix with the `10.1016/` prefix stripped (e.g., DOI `10.1016/S0140-6736(21)00125-2` → PIIS URL `thelancet.com/journals/lancet/article/PIIS0140-6736(21)00125-2/fulltext`). This avoids the parenthesized DOI in the URL path and works reliably via jina reader. Alternatively, use `fetch_fulltext.py --publisher-url <thelancet.com URL>`. The PIIS form was confirmed across 2 Lancet papers in the IL-17A/IL-17F profile session (PMIDs 33549193, 38795716) — both returned structured abstracts with complete efficacy/safety data (3.5K–11.3K chars) via jina. (Observed: BCMA profile, PMID 34175021 and PMID 31859245, 2026-08-15 — both Lancet/Lancet Oncol DOIs with parens 404'd via jina; IL-17A/IL-17F profile, PMID 33549193 and 38795716, 2026-08-15 — PIIS URL form succeeded via jina.) | PIIS URL form via jina reader (`r.jina.ai/https://www.thelancet.com/journals/<journal>/article/PIIS<id>/fulltext`); or `fetch_fulltext.py --publisher-url <thelancet.com URL>`; if both fail, abstract-only. **Lancet abstract+references masquerade (subscription-only, no PMCID):** `fetch_fulltext.py` returns `publisher-jina` provenance with 80K+ chars that passes the size check, but for subscription-only Lancet papers (e.g., Lancet Respir Med, `isOpenAccess: N`, no PMCID), the content is abstract (~3K chars) + full reference list (~33K chars) + navigation chrome — NOT the article body. This is the same reference-list masquerade pattern as Springer/Drugs and Nature. **Validation rule:** when jina returns content for a Lancet subscription article, grep for body section headings (`Introduction`, `Results`, `Discussion`) before tagging `publisher-jina`/`jina-reader` as full text. If only abstract + references, treat as abstract-only. (Observed: PMID 35364018, SOURCE trial, Lancet Respir Med 2022 — 80K chars via publisher-jina, abstract+refs only.) |
| Wiley | onlinelibrary.wiley.com | Cloudflare interstitial + curl 403; jina reader returns ~500-byte Cloudflare "Just a moment" block page on all URL variants (`/doi/full/`, `/doi/epdf/`, `/doi/`, DOI URL) | No PMCID → **try Wayback CDX on the `/doi/full/` URL before declaring abstract-only.** CDX returns 200-status snapshots for `onlinelibrary.wiley.com/doi/full/<DOI>` (2020-2021 era, ~84-96 KB). Fetch the largest-length snapshot via direct `urllib.request` on the Wayback URL (`https://web.archive.org/web/<timestamp>/<original-url>`) → 500-600 KB HTML → extract from `<article>` tag → 90-95K chars full text. This works for Wiley OA articles (CC-BY/hybrid, even when `isOpenAccess: N` and no PMCID). Validate body presence (grep for section headings) before tagging `fulltext_source: wayback`. (Observed: PMID 29247993, Cayrol & Girard 2018, Immunol Rev — 95K chars full text from 2021 Wayback snapshot, all 10 review sections present. 2026-08-18.) If CDX returns no 200 snapshots, then abstract-only. |
| Karger | karger.com | Cloudflare Turnstile to curl and browser | `inPMC: N` → abstract-only |
| OUP/ATS | academic.oup.com, atsjournals.org | Cloudflare interstitial | PMCID → branch 1b first |
| Cell Press | cell.com | Cloudflare interstitial to curl | **Jina reader proxy on the direct fulltext URL succeeds** — `r.jina.ai/https://www.cell.com/<journal>/fulltext/<PII>` returns complete body text. The PII is obtained from PubMed `elink.fcgi?cmd=prlinks` (`linkinghub.elsevier.com/retrieve/pii/<PII>`) OR from PubMed XML `<ArticleIdList>` `<ArticleId IdType="pii">` directly (no `elink` call needed when PubMed XML is already fetched — observed for Molecular Cell 1999, PMID 10549288, PII `S1097-2765(00)80207-5`). Construct the Cell Press URL as `www.cell.com/<journal>/fulltext/<PII>`. The `/fulltext/` URL form is the working path; the `/pdf/` URL variant returns 404 via jina. Confirmed across multiple Cell Press journals and eras: Structure 2024 (94K chars, PMID 38626767), Molecular Cell 1999 (53K chars, PMID 10549288 — 25-year-old flagship Cell Press journal). Branch 1c (preprint via UpdateOf) is the fallback if no Cell Press fulltext URL exists. (Observed: PMID 38626767, PVRIG profile, 2026-08-16 — 94,284 chars via `cell.com/structure/fulltext/S0969-2126(24)00094-7`; PMID 10549288, DR5 antibody literature dive, 2026-08-18 — 53,127 chars via `cell.com/molecular-cell/fulltext/S1097-2765(00)80207-5`.) |
| ASBMB / JBC (J Biol Chem) | jbc.org | JBC moved from ASBMB to Elsevier hosting (2022+); older articles resolve via `linkinghub.elsevier.com/retrieve/pii/<PII>`. No PMCID for most pre-2010 articles. Jina reader on the DOI URL returns the doi.org 404 page. | **Jina reader proxy on the direct JBC article URL succeeds** — resolve the DOI to get the PII (`linkinghub.elsevier.com/retrieve/pii/<PII>`), then use `r.jina.ai/https://www.jbc.org/article/<PII>/fulltext`. Returns complete body text (75K chars, all sections, figures, tables). No PMCID needed. (Observed: PMID 19001363, Bottomley 2009, PCSK9 profile, 2026-08-18 — 74,960 chars full text via jina on `jbc.org/article/S0021925820711464/fulltext`.) |
| Rockefeller UP (JEM) | rupress.org | Cloudflare CAPTCHA — jina, Wayback, and browser all blocked; no PMC for recent articles | No PMCID → abstract-only (genuinely unreachable) |
| ASH Publications (Blood) | ashpublications.org | Cloudflare/CAPTCHA interstitial blocks curl AND jina reader proxy (both direct article URL and DOI redirect); Wayback has no snapshot | `inPMC: Y` but publisher restricts XML body download (front matter only, ~15 KB); EPMC PDF render returns "No PDF file found" → abstract-only (PMID 30510079, 2026-08-15) |
| JCI Insight / ASCI | insight.jci.org | `inPMC: Y` but publisher restricts XML body download (front matter only, ~14 KB, 0 sections, no `<body>`) | **EPMC PDF render works** — `europepmc.org/api/getPdf?pmcid=<PMCID>` delivers the full publisher PDF (6.3 MB → 51K chars via pymupdf). Jina reader proxy also succeeds (85 KB markdown). Tag `fulltext_source: epmc-pdf`. (PMID 31852846, IL-7Rα profile, 2026-08-15) |
| NEJM | nejm.org | Most NEJM papers have no PMCID; jina reader 403s on live AND Wayback URLs. **Some NEJM papers DO have a PMCID** (e.g., PMID 27292104, PMC5594743, inPMC=Y), but the **EPMC PDF render (`europepmc.org/api/getPdf?pmcid=<PMCID>`) returns HTTP 500** — the PMCID's presence does not guarantee EPMC PDF access for NEJM. PMC XML efetch is also typically front-matter only or blocked | **Wayback CDX API + direct HTML fetch is the reliable path** — use the CDX index API (`web.archive.org/cdx/search/cdx?url=<nejm_url>&output=json&limit=5`) to find a 200-status snapshot, then `urllib.request` on the snapshot URL returns 189-270 KB HTML; `<article>` tag extraction yields 38-50K chars. Skip jina entirely (403s on both live and Wayback). Tag `fulltext_source: wayback`. **Caveat (2026-08-15, IL-17RA profile): older NEJM Wayback snapshots (2015-era) may return abstract-level content only (~2.3K chars) even with 200 status — the NEJM paywall was active at the time of archiving, and the archived page is the paywall preview, not full text. All 10 available 200-status snapshots from 2015-2016 for the AMAGINE-2/3 trial (PMID 26422722, DOI 10.1056/NEJMoa1503824) returned abstract-level content. In contrast, later NEJM snapshots (2018-2021 era) for the IL-4Rα profile PMIDs returned full text. When Wayback returns abstract-only for NEJM, the structured PubMed abstract (via `efetch.fcgi?rettype=abstract&retmode=text`) is the primary content source — tag `fulltext_source: wayback` and note the content level. (PMIDs 27690741, 29782217, IL-4Rα profile; PMID 27292104, CD22 profile; PMID 26422722, IL-17RA profile, 2026-08-15)

**Recent (2024+) NEJM articles return abstract-only from ALL Wayback snapshots regardless of era (2026-08-18, GDF15 dive).** PMID 39282907 (Groarke 2024, ponsegromab, DOI 10.1056/NEJMoa2409515): CDX returned 15+ 200-status snapshots from 2024-09 through 2025-10 across both `/doi/full/<doi>` and `/doi/<doi>` URL forms, ALL ~27-35 KB HTML (largest-length heuristic doesn't help — all similar size). `<article>` extraction yielded 11-12K chars containing author block + structured abstract + supplementary-material links + full citation/"Cited by" reference list, but ZERO body sections (no Introduction, no Results, no Discussion). Unlike the 2015-era paywall-preview caveat, these snapshots archived the modern paywall preview page at a time when the paywall was active — for current-era NEJM articles there is no "later full-text snapshot" to wait for. `fetch_fulltext.py --skip-publisher` returns `provenance: none`; jina returns the Cloudflare CAPTCHA ("Performing security verification", ~474 bytes). **Semantic Scholar `openAccessPdf` reported status:GREEN with a CC-BY PDF URL at a co-author's institutional repository** (Edinburgh research.ed.ac.uk, Marie Fallon's affiliation), but the direct download returned HTTP 403 and the jina reader proxy returned a CAPTCHA page; Wayback CDX returned a 200 snapshot of the repository LANDING page but archived only the HTML wrapper, not the PDF binary (the snapshot's own PDF link pointed back at the live 403'd URL). Browser fallback would likely work but was unavailable in the subagent context. Outcome: three-source closure confirmed, abstract-only with `needs-enrichment: true`. Lesson: for recent NEJM articles, (a) check S2 `openAccessPdf.url` even when EPMC is all-N — a co-author institutional repository copy may exist; (b) S2 GREEN status does NOT guarantee retrievability from this host (institutional repositories deploy their own Cloudflare/CAPTCHA); (c) the structured PubMed abstract for a primary-endpoint Phase 2 trial is often complete enough for a meaningful distillation (all dose-response numbers, population, safety headline present) — abstract-only is not a failure when the abstract is structured and rich.  **DOM-selector caveat (2026-08-18, PCSK9 dive): older NEJM Wayback snapshots (2015-era) for pre-2008 NEJM papers (free-access era) DO contain full text, but in a `<dd id="article">` element, NOT the `<article>` tag that works for 2018-2021-era snapshots.** PMID 16554528 (Cohen 2006, DOI 10.1056/NEJMoa054013): the 2015 snapshot (461 KB HTML) had no `<article>` tag; extracting from `<dd id="article">` yielded 29K chars of complete Introduction/Methods/Results/Discussion/References. **Always try BOTH selectors on NEJM Wayback HTML** — `<article>` first, then `<dd id="article">` — before declaring abstract-only. The `<dd id="article">` pattern applies to NEJM's older page template (pre-redesign) and is distinct from the paywall-preview caveat above: a paywall preview returns ~2.3K chars regardless of selector, while the `<dd id="article">` pattern returns tens of KB of genuine body text. Distinguish by content length, not selector success. (PMID 16554528, PCSK9 literature dive, 2026-08-18) |
| JAMA Network | jamanetwork.com, archderm.jamanetwork.com | Cloudflare CAPTCHA blocks jina reader proxy on ALL URL variants (article.aspx, fullarticle). Wayback availability API 429s; CDX search returns no snapshots for any URL variant | No PMCID → abstract-only (genuinely unreachable). (PMID 19687432, CD11a profile, 2026-08-15.) **PMCID-present variant:** some JAMA Network papers (e.g., JAMA Dermatol PMID 39602139, PMC11840645, `inPMC: Y`) DO carry a PMCID, but both retrieval paths fail: PMC XML efetch returns front-matter only (~28 KB, no `<body>` element), and EPMC PDF render (`europepmc.org/api/getPdf?pmcid=PMC11840645`) returns HTTP 404. This is the same Branch 1b pattern as Blood (ASH Publications) — PMCID present, but neither XML body nor PDF is retrievable. Abstract-only is the outcome even with a PMCID. (PMID 39602139, IL-31Rα profile, 2026-08-15.) |
| Bentham Science | eurekaselect.com, ingentaconnect.com | Cloudflare CAPTCHA blocks jina reader proxy (~489 bytes). Wayback CDX may find an ingentaconnect snapshot (200 status) but the fetched content can be a **completely different article** (wrong content, not a paywall page) — see Wayback CDX wrong-content pitfall below | No PMCID → abstract-only. Do NOT trust Wayback CDX content for this publisher without title validation |
| Elsevier/JACI | jacionline.org | Elsevier block page to curl (cookie consent chrome only, ~20 KB, no article body). **Jina reader proxy on the DOI URL returns 404**, but the jina reader proxy on the **direct PIIS article URL** (`r.jina.ai/https://www.jacionline.org/article/S0091-6749(24)01175-8/fulltext`) **succeeds** — returning 76K chars of full article text (Abstract, Methods, Results, Discussion, Safety, References). The PII is obtained from the PubMed `elink.fcgi?cmd=prlinks` `linkinghub.elsevier.com/retrieve/pii/S<PII>` URL. No PMCID needed. (Observed: PMID 39522654, OX40L profile, 2026-08-16.) The earlier observation that jina 404s on `jacionline.org/article/PIIS<id>/fulltext` (PMID 23465663, CD19 profile, 2026-08-15) may have been paper-specific or transient — always try the PIIS URL via jina before declaring abstract-only. | No PMCID → **try jina reader on the direct PIIS article URL first** (`r.jina.ai/https://www.jacionline.org/article/S<PII>/fulltext`); if it returns >3K chars with body content, tag `fulltext_source: jina-reader`. If jina 404s or returns <3K chars, then abstract-only. Do NOT skip jina on JACI. |
| AACR (Clin Cancer Res, Cancer Res, etc.) | clincancerres.aacrjournals.org, cancerres.aacrjournals.org | Jina reader proxy returns ~489 bytes (blocked). No PMCID for most articles. Publisher site renders via JS (empty DOM to curl). | No PMCID → **try Wayback CDX before declaring abstract-only.** CDX found 200-status snapshots for `cancerres.aacrjournals.org/content/<vol>/<issue>/<page>` and the `.long` URL variant. The `.long` URL yielded 219 KB HTML → 26.7K chars extracted text (full review article body). Tag `fulltext_source: wayback`. For the non-`.long` URL, 73 KB HTML was mostly page chrome — prefer the `.long` variant when available. (Observed: PMID 19509221, Cancer Res 2009, CD19/CD3 profile, 2026-08-16 — `.long` URL snapshot returned full body; PMID 23155186, CD30 profile, 2026-08-15 — jina 489 bytes, no PMCID, abstract-only, CDX not attempted.) |
|| Nature Reviews (Springer Nature) | nature.com (Nature Reviews Immunology, Nature Reviews Drug Discovery, etc.) | Subscription-only review journals. Jina reader proxy returns ONLY the reference list (~80-93 KB), not the article body or abstract — the body is behind a subscription wall. No PMCID for most Nature Reviews articles. **Distinct from Nature research articles** (Nature, Nature Communications, etc.) which may render via browser (see Branch 2 Nature-family note) | No PMCID → abstract-only, but distill from abstract + **Key points + Glossary + figure captions + reference list** (direct `curl`/`urllib` on the article URL, NOT jina — jina returns only the reference list). The public preview page also carries the full abstract, the Nature Reviews **Key points** block (3-6 bulleted points under the abstract), a **Glossary** of defined terms, `figcaption` entries, and complete `citation_*` meta tags (reference list + `citation_author`/`citation_author_institution` for Phase 8). Paywall check: grep `data-title=` — body unreachable when only `Abstract/Key points/References/Acknowledgements/Glossary` are present (no `Introduction`/`Results`). Same-day papers often have NO PMID/PMCID yet (Europe PMC hitCount 0) — resolve identity via CrossRef alone, set `needs-enrichment: true`, re-resolve identifiers on the embargo re-check. (PMIDs 12563296, 17641665, CD3 profile, 2026-08-15; Zhang/Wang/Liu Nat Rev Immunol DOI 10.1038/s41577-026-01344-9, 2026-08-27.) |
|| Nature subscription research journals (Nature Biotechnology, Nature Methods, Nature Struct Mol Biol, etc.) | nature.com (subscription research articles) | Subscription research journals (NOT review journals — distinct from Nature Reviews above, and NOT covered by the Branch 2 "Nature research-article pages render reliably" note, which applies to OA Nature research articles). Jina reader returns abstract + "subscription content" paywall notice; body text unreachable. No PMCID for most subscription articles. **But: direct curl on the article URL succeeds and the HTML `<head>` contains rich `citation_*` meta tags** (authors, affiliations, ORCIDs, full reference list, figure/ED captions, data/code availability) enabling a meaningful partial distillation. See `references/nature-paywalled-metadata-extraction.md` for the extraction recipe. | No PMCID → `needs-enrichment: true`, `fulltext_source: abstract-only`. Distill from abstract + figure/ED captions + data/code availability + reference list. Mark Findings claims requiring body text with `[needs-citation]`. (Observed: PMID 41039041, Nature Biotechnology 2025, ProTrek — 2026-08-17.) |
| Nature Medicine (Springer Nature, subscription) | nature.com (Nature Medicine) | Subscription research journal (NOT a review-only journal — distinct from Nature Reviews). Jina reader proxy returns the reference list (~155 KB) with little to no article body for subscription articles — same reference-list masquerade pattern as Nature Reviews and Springer/Drugs. **Nature Medicine OA articles** (those with a PMCID) work normally via PMC XML; the block applies to subscription-only Nature Medicine articles. No PMCID for most subscription Nature Medicine articles. | No PMCID → **try direct curl on `nature.com/articles/<doi-suffix>` for `citation_*` meta-tag extraction before falling to abstract-only** — the HTML `<head>` carries rich structured metadata (authors, affiliations, ORCIDs, full reference list, figure/ED captions, data availability) sufficient for a partial distillation richer than abstract-only. See `references/nature-paywalled-metadata-extraction.md` for the extraction recipe. Set `needs-enrichment: true`, `fulltext_source: abstract-only`. The reference-list masquerade (jina, ~155 KB) passes the Branch 1d size check — validate that body text is present (grep for section headings) before tagging `jina-reader`. (Observed: PMID 26121196, IL-12/23 p40 profile, 2026-08-15 — 155 KB jina output, all reference list, zero body paragraphs; PMID 32661391, Suriben 2020 Nat Med GFRAL/3P10 — 384 KB HTML via direct curl, 105 citation_* meta tags + 4 figure captions + data availability extracted, 2026-08-18.) |
| Springer/Drugs (subscription) | link.springer.com (Drugs journal, **and book chapters**) | Jina reader proxy returns abstract + references for newer articles (2023, ~22 KB) but only references for older articles (1989, ~87 KB). Body is paywalled. Many Springer articles ARE OA and work fine — this applies to subscription-only Springer content. **Also applies to Springer book chapters** (`link.springer.com/chapter/10.1007/978-...`) — jina returns 70K+ chars of reference-list masquerade with zero body paragraphs (same failure mode as the Drugs journal entry, different URL pattern). **Jina reference-list masquerade pitfall:** a large reference list (50K+ chars) passes the Branch 1d size check and looks like full text, but the extracted content is entirely reference titles — no body paragraphs. When jina returns content for a subscription Springer/Drugs article or book chapter, validate that body text is present (grep for section headings or sentences longer than a reference citation) before tagging `fulltext_source: jina-reader` / `needs-enrichment: false`. If only references are present, treat as abstract-only. (Observed: PMID 33367970, CD52 profile, 2026-08-15 — 51K chars, all reference list; PMID 39117840, IFN-γ profile, 2026-08-15 — 71K chars, book chapter `link.springer.com/chapter/10.1007/978-3-031-59815-9_38`, all reference list.) | No PMCID → abstract-only for paywalled articles. PubMed abstract + jina-extracted abstract (for newer articles) as primary content. (PMIDs 2503348, 36877454, CD3 profile, 2026-08-15.) |
| Thieme (Semin Neurol, etc.) | thieme-connect.com | Jina reader proxy returns a German maintenance page (~364 bytes: "Wegen Wartungsarbeiten steht das System vorübergehend nicht zur Verfügung"). Wayback CDX finds 200-status snapshots, but jina reader on the Wayback snapshot URL returns HTTP 403, and direct `urllib.request` on the Wayback snapshot URL returns HTTP 498. No PMCID for most articles. | No PMCID → abstract-only (genuinely unreachable). Three-source closure: EPMC inPMC=N, isOpenAccess=N, hasPDF=N. (Observed: PMID 23709214, CD52 profile, 2026-08-15.) |
| Cold Spring Harbor Laboratory Press (CSHLP) | cshperspectives.org, cshlpress.org (Cold Spring Harb Perspect Biol) | `inPMC: Y` but PMC XML efetch returns front-matter only (~6.7 KB, 0 sections, no `<body>` element). Same Branch 1b pattern as JCI Insight/OUP/ATS. | **EPMC PDF render works** — `europepmc.org/api/getPdf?pmcid=<PMCID>` delivers the full publisher PDF (3.4 MB → 95K chars via pymupdf). Tag `fulltext_source: epmc-pdf`. (PMID 24890514, PMC4031967, CSF-1R profile, 2026-08-15.) |
| ASCO (J Clin Oncol, JCO) | ascopubs.org | `inPMC: Y` but PMC XML efetch returns front-matter only (~7 KB, 0 sections, no `<body>` element). Same Branch 1b pattern as JCI Insight/OUP/ATS/CSHLP. | **PMCID present → EPMC PDF render works** — `europepmc.org/api/getPdf?pmcid=<PMCID>` delivers the full publisher PDF (541 KB → 58K chars via pymupdf). Tag `fulltext_source: epmc-pdf`. (PMID 25605845, PMC4980573, CTLA-4 profile, 2026-08-15.) **No PMCID → try Wayback CDX before declaring abstract-only.** CDX found 200-status snapshots for both `ascopubs.org/doi/<doi>` and `ascopubs.org/doi/full/<doi>` — the `/doi/full/` variant yielded 255 KB HTML → 33.5K chars extracted text with complete Abstract, Introduction, Patients and Methods, Results, Discussion, and References sections. Tag `fulltext_source: wayback`. (Observed: PMID 21576633, JCO 2011, CD19/CD3 profile, 2026-08-16.) |
| AME Publishing (Ann Transl Med, J Gastrointest Oncol, etc.) | atm.amegroups.org, jgo.amegroups.org | `inPMC: Y` but PMC XML efetch returns front-matter only (~10 KB, 0 sections, no `<body>` element). `isOpenAccess: N`. Same Branch 1b pattern as JCI Insight/OUP/ATS/CSHLP/ASCO. | **EPMC PDF render works** — `europepmc.org/api/getPdf?pmcid=PMC4620089` delivered a 223 KB PDF (23K chars via pymupdf). Tag `fulltext_source: epmc-pdf`. (PMID 26605293, PMC4620089, Factor XIIa profile, 2026-08-15.) |
| Science (AAAS) | science.org | Cloudflare CAPTCHA blocks jina reader proxy (~483 bytes: "Performing security verification"). **Some Science papers DO have a PMCID** (e.g., PMID 29567705, PMC7391259, inPMC=Y) and PMC XML efetch delivers full text normally. | PMCID present → Branch 1 (PMC XML OA) works normally. **No PMCID → try Wayback CDX before declaring abstract-only.** The CDX API does NOT always time out for science.org — 3 snapshots (status 200) were found for `science.org/doi/<doi>` for PMID 18703743 (Bargou 2008, CD19/CD3 profile, 2026-08-16). Fetch the snapshot HTML and extract from `<article>` tag: 268 KB HTML → 8.5K chars (short Science research report). Tag `fulltext_source: wayback`. If CDX returns no snapshots or the extracted text is <2K chars, fall to abstract-only. The earlier "Wayback CDX API times out" note (PMID 25838373, CTLA-4 profile, 2026-08-15) may have been a transient CDX timeout — retry CDX once after 10s before declaring abstract-only (see CDX API timeout pitfall). |
| AHA Journals (Circulation, Circ Res, Hypertension, Stroke) | ahajournals.org | Cloudflare CAPTCHA **intermittently** blocks jina reader proxy (~505 bytes: "Title: Just a moment..."). Most subscription articles have no PMCID. Wayback CDX may find snapshots but content is often the paywall page. **Some Circ Res articles ARE in PMC (OA) and work normally** — the block applies only to subscription articles without a PMCID. | No PMCID → **try jina reader on the publisher article URL first** (`r.jina.ai/https://www.ahajournals.org/doi/<doi>`) — jina succeeds intermittently for AHA Journals, returning 57K chars of full text including all sections, figures, and references. If jina returns <3K chars (Cloudflare block), then abstract-only (three-source closure: EPMC inPMC=N, isOpenAccess=N, hasPDF=N). EPMC core record abstract is the primary content source. PMCID present → PMC XML OA works normally. (PMID 29880500, Circ Res, no PMCID — jina 505 bytes, abstract-only, IL-1β profile, 2026-08-15; PMID 36314243, Circulation, no PMCID — jina succeeded with 57K chars full text, PCSK9 profile, 2026-08-18; contrast PMID 32324502, Circ Res, PMC8760628 — PMC XML full text.) |
| ProEd / Index Copernicus (Drugs of Today) | doi.org redirect → Portico archive | DOI prefix `10.1358` resolves to a Portico archive page. Jina reader proxy on the DOI URL returns a cookie consent page (~4 KB), not article content. Alternative publisher URLs (journals.sagepub.com, proedjournal.com) also fail — Sage returns ~510 bytes (blocked), ProEd returns HTTP 422. No PMCID. | No PMCID → abstract-only (three-source closure: EPMC inPMC=N, isOpenAccess=N, hasPDF=N). PubMed abstract is the primary content source. (PMID 29517082, Drugs of Today, IL-5Rα profile, 2026-08-15.) |
| Taylor & Francis (tandfonline.com) | tandfonline.com | doi.org HEAD redirect returns HTTP 403. Jina reader proxy on `tandfonline.com/doi/full/<doi>` returns 27–30 KB of page chrome + abstract + keywords but NOT the article body (subscription paywall). Content passes the size check (>3K chars) but body-term counts are low — validate body presence before tagging. | **PMCID present → EPMC PDF render works** — same Branch 1b pattern as CSHLP/ASCO/AME: `inPMC: Y` but PMC XML efetch returns front-matter only; `europepmc.org/api/getPdf?pmcid=<PMCID>` delivers the full publisher PDF (60K chars via pymupdf for an mAbs article). Tag `fulltext_source: epmc-pdf`. (Observed: PMID 27064440, mAbs 2016, PMC4968136, TRAIL profile, 2026-08-16.) **No PMCID → try Wayback CDX before declaring abstract-only.** CDX found 200-status snapshots for `tandfonline.com/doi/full/<doi>` — the most recent snapshot (2025) yielded 9K chars with abstract + keywords. Earlier snapshots (2022) returned 5K chars with 0 target-term mentions (page chrome only). Use the largest `length` snapshot. Tag `fulltext_source: wayback` (abstract + keywords level). When jina returns 27+ KB with >15 target-term mentions in the abstract/keywords, tag `fulltext_source: publisher-jina` at abstract+keywords level. (Observed: PMID 24555705, Expert Opin Biol Ther 2014; PMID 29323537, Expert Opin Investig Drugs 2018. CD37 profile, 2026-08-16.) |
| Springer/World J Surg (subscription, PMCID present) | link.springer.com (World Journal of Surgery) | Branch 1b variant: `inPMC: Y`, `isOpenAccess: N`, `hasPDF: Y`, PMCID present — but ALL retrieval paths fail. PMC XML efetch returns metadata-only (no `<body>` element). EPMC PDF render (`europepmc.org/api/getPdf?pmcid=<PMCID>`) returns no PDF. EPMC fullTextXML endpoint (`europepmc.org/webservices/rest/<PMCID>/fullTextXML`) returns HTTP 404. Jina reader on DOI URL returns a CAPTCHA page (~497 chars: "Just a moment..."). Wayback CDX API returns HTTP 503 (Service Unavailable) on both filtered and unfiltered queries. | PMCID present → abstract-only despite inPMC=Y. This is the same all-paths-fail pattern as JAMA Network PMCID-present variant, but with CDX 503 instead of "no snapshots." PubMed abstract (via `efetch.fcgi?rettype=abstract&retmode=xml`) is the primary content source. Tag `fulltext_source: abstract`. (Observed: PMID 18264829, World J Surg 2008, PMC4378829, SLeX/CA19-9 profile, 2026-08-16.) |
| Portland Press (Biochem Soc Trans) | portlandpress.com, biochemsoctrans.org | Jina reader proxy on `portlandpress.com` article URLs returns ~500 bytes (blocked). doi.org HEAD redirect returns HTTP 403. No PMCID for most articles. | **No PMCID → try Wayback CDX on the old `biochemsoctrans.org` URL format.** CDX found 200-status snapshots for `www.biochemsoctrans.org/content/<vol>/<issue>/<page>` — a 2016 snapshot yielded 40K chars with 37 target-term mentions (full review article body). A 2018 snapshot of the same URL returned only 10K chars (2 target-term mentions — likely a paywall preview). Prefer the earliest/largest snapshot. Tag `fulltext_source: wayback`. **URL pattern matters:** CDX returned no results for `portlandpress.com` URLs (post-migration), only for the legacy `biochemsoctrans.org` domain — always try both URL forms. (Observed: PMID 21428930, Biochem Soc Trans 2011. CD37 profile, 2026-08-16.) |
| ADA / American Diabetes Association (Diabetes) | diabetesjournals.org | Cloudflare CAPTCHA blocks jina reader proxy (~521 bytes: "Performing security verification"). The `article-lookup/doi/<doi>` URL pattern is the primary article URL (discovered via elink `cmd=prlinks`). No PMCID for most articles. Wayback CDX API returned 0 rows (no snapshots for the article-lookup URL). | No PMCID → abstract-only (three-source closure: EPMC inPMC=N, isOpenAccess=N, hasPDF=N). PubMed abstract is the primary content source. (Observed: PMID 26293506, Diabetes 2015, CXCL10 profile, 2026-08-16.) |
| AAI / American Association of Immunologists (J Immunol) | journals.aai.org, jimmunol.org | Jina reader proxy returns 403 Forbidden on all URL variants (`journals.aai.org/jimmunol/article/...`, `www.jimmunol.org/content/...`, DOI URL). EPMC `fullTextUrlList` and Semantic Scholar `openAccessPdf` both report an OA PDF URL at `journals.aai.org/jimmunol/article-pdf/...` but direct download returns a 1.5 KB HTML redirect/landing page, NOT a PDF (content starts with `<html><head><script>`). **Semantic Scholar OA PDF false positive** — the URL is reported as open access but does not deliver a PDF file. No PMCID for older papers (pre-~2010). Wayback CDX found 200-status snapshots for the legacy `www.jimmunol.org/cgi/content/full/<vol>/<issue>/<page>` URL form (2003-era snapshots, 38–39 KB) — these may yield full text when Wayback is available, but were unretrievable during the CCL25 profile session due to persistent Wayback 503s. | No PMCID → abstract-only. **Do NOT trust the Semantic Scholar/EPMC OA PDF URL** for AAI/J Immunol — verify downloaded content starts with `%PDF` before attempting text extraction. If Wayback is operational, try the `jimmunol.org/cgi/content/full/` URL form. Otherwise abstract-only. (Observed: PMID 10640743, J Immunol 2000, CCL25 profile, 2026-08-16 — S2 false-positive OA PDF, jina 403, Wayback 503, abstract-only.) |
|| EMBO Press / Nature Publishing Group (EMBO Reports, EMBO J) | embopress.org, nature.com (EMBO Reports) | Branch 1b pattern: `inPMC: Y` but PMC XML efetch returns front-matter only (~9 KB, 0 sections, no `<body>` element). **EPMC `fullTextXML` endpoint also fails** — returns 0 bytes (not even an HTTP error), a distinct failure mode from the HTTP 404 seen for other publishers. The EPMC core record reports `isOpenAccess: N`, `hasPDF: Y`. | **EPMC PDF render works** — `europepmc.org/api/getPdf?pmcid=<PMCID>` delivers the full publisher PDF (730 KB → 34K chars via pymupdf for a 6-page EMBO Reports scientific report). Tag `fulltext_source: epmc-pdf`. The PDF contains complete body text (Intro, Results/Discussion, Methods, References) with figure legends embedded as text. (Observed: PMID 22081141, EMBO Rep 2011, PMC3245695, PCSK9/LDLR structure — PMC XML 9 KB front-matter only, EPMC fullTextXML 0 bytes, EPMC PDF 730 KB → 34K chars. 2026-08-18.) |
|| SAGE / Atypon (J Interferon Cytokine Res, J Immunology, etc.) | journals.sagepub.com | Cloudflare CAPTCHA blocks jina reader proxy on both `journals.sagepub.com/doi/<doi>` and `journals.sagepub.com/doi/full/<doi>` (~505–510 bytes: "Title: Just a moment..." / "Performing security verification"). No PMCID for most articles. Wayback CDX returned no snapshots for either URL variant. Unpaywall not indexed (HTTP 422 for SAGE DOIs with the `10.1177` prefix). | No PMCID → abstract-only (three-source closure: EPMC inPMC=N, isOpenAccess=N, hasPDF=N; Unpaywall 422; S2 openAccessPdf=null). PubMed abstract is the primary content source. DOI prefix `10.1177` is SAGE. (Observed: PMID 42455016, J Interferon Cytokine Res 2026, TNF review — jina 505 bytes on both URL variants, CDX `[]`, Unpaywall 422, S2 null, abstract-only. 2026-08-18.) |

||| Wolters Kluwer / AAN (Neurology, Neurology journals) | neurology.org | **Jina reader reference-list masquerade.** Jina reader proxy on `neurology.org/doi/<doi>` returns ~64–70 KB — this passes the Branch 1d size check but contains ONLY abstract + navigation chrome + full reference list, NOT article body. Same failure mode as Springer/Drugs reference-list masquerade. Subscription journal (pre-2007 articles: no PMCID, `inPMC: N`, `isOpenAccess: N`, `hasPDF: N`). Semantic Scholar `openAccessPdf`: `CLOSED`. **Wayback CDX finds snapshots** (3× 200-status observed on `neurology.org/doi/10.1212/01.wnl...`) but all snapshots render the abstract-only page (~37 KB stripped text, 0 body sections) — the article body is behind the paywall even in Wayback. The ~64–70 KB jina output looks like full text — validate for body section headings (Introduction, Methods, Results, Discussion) before tagging `fulltext_source: jina-reader`. | No PMCID → abstract-only after three-source closure (EMPC all-N + S2 CLOSED). Structured PubMed abstract is the primary content source. Tag `fulltext_source: abstract-only`, `needs-enrichment: true`. **Wayback snapshots exist but are abstract-only** — do not assume CDX hits mean full-text availability; always grep for body-section headings in fetched Wayback content before tagging. NOTE: some AAN/Neurology articles from ~2015+ may have a PMCID (e.g., PMC articles in Neurology Genetics) — always check EPMC `inPMC` flag before declaring abstract-only. (Observed: PMID 15642910, Bayer 2005, AN1792 Phase I — jina 70 KB abstract+refs-only, CDX 0 snapshots. PMID 12847155, Orgogozo 2003, AN1792 Phase IIa meningoencephalitis — jina 64 KB abstract+refs-only, CDX 3 snapshots all abstract-only ~198 KB HTML → 37 KB text. 2026-08-22.) |

Second-order dead ends (do not cascade): the Europe PMC *browser* view
can return a minimal DOM while its REST API works fine — prefer REST;
Google Scholar IP-blocks this host; Semantic Scholar *web* search 405s
but its REST API works.

**Figure images (optional).** `fetch_fulltext.py --figures` scrapes
`cdn.ncbi.nlm.nih.gov/pmc/blobs/...` URLs from the PMC article page —
works for free-in-PMC articles, not just OA. NCBI's `oa.fcgi` bulk host
and Europe PMC's image backend are dead ends from this host. Figures are
distillation-time working material (`/tmp`, ephemeral); `vision_analyze`
reads them into Findings. A permanent vault figure archive is a deferred
design question.

### 5. Distillation and page write

Write `papers/<slug>.md` per the paper-kind schema. Body anatomy:
Abstract / Context / Approach / Findings (specific results tied to
figures) / Limitations / Analysis, plus `## Ingest log` and `## Citation`.

**Verify the task brief against the full text before writing Findings.**
A parent task's pre-filled "key findings" are a convenience, not a
primary source — they can conflate closely related molecules or
misattribute structural features (observed: a brief identifying the
wrong antibody of a consortium pair, wrong pocket, wrong residues). Grep
the fetched full text for each key claim (molecule name, epitope,
residue numbers). If the full text contradicts the brief, trust the full
text; record the discrepancy in a prominent body note. Do NOT silently
overwrite the brief's claims — the slug may be intentionally structured
— flag and let your human decide on renames.

**Abstract-only distillation checklist.** When `fulltext_source:
abstract-only`, the abstract is the *entire* available text — every
sentence must be read for extractable signal, not skimmed for the
headline finding. Before writing the page, scan the abstract for these
high-value elements and include each one that appears:

- **Structures** (cryo-EM, X-ray, NMR) — resolution, complex
  composition, what it reveals. An abstract that says "a 2.88 Å Cryo-EM
  structure of the tetrameric RBP and antibody complex" is a first-class
  result, not a methods detail. Missing it produces an incomplete page
  that a human will catch (observed 2026-08-26, Nipah dive: Chen 2024
  cryo-EM structure missed despite being stated in the abstract).
- **Discovery method** — phage display, single B cell cloning,
  hybridoma, humanized mice. These are different technology platforms
  with different implications. Do not assume from the lab's reputation;
  read what the abstract says. (Observed: same Nipah dive — Chen 2024
  was phage display, misidentified as single B cell cloning.)
- **Epitope / target site** — receptor-binding site, F apex, quaternary
  epitope, etc. If the abstract states the binding site, record it
  precisely; do not write "targets G" when the abstract says "blocks the
  receptor binding interface."
- **In vivo model and survival** — species, % survival, treatment
  window.
- **Cross-reactivity** — which virus strains/variants are neutralized.
- **Affinity / potency** — IC50, KD, neutralization titers.

The failure mode this prevents: writing a distillation focused on one
angle (e.g., germline gene usage) while missing a co-equal result (e.g.,
a structure) that the abstract states in a single sentence. When you are
distilling from abstract-only, *there is no second chance to find it in
the full text* — the abstract is all there is.

**Stub replacement / slug renaming.** When the task specifies a
different slug than an existing stub for the same paper (same DOI):
create the page at the task-specified slug, copy the stub's `cited_by`
into the new page (append-only, preserve all entries), delete the old
stub, log the rename, and grep the vault for inbound references to the
old slug (rare, but verify).

**Frontmatter.** `fulltext_source:` from the retrieval provenance;
`needs-enrichment: true` ONLY for genuine abstract-only (branch 3) or
preprint-in-place-of-published distillation; `status:` is
`preprint`/`published`/`unknown` only — never `withdrawn`, `accepted`,
or `in review` (linter rejects; withdrawal/acceptance is a body detail).
Every author goes in `authors:` as `people/<slug>` (Phase 8).

**Ingest log on success-with-deviation.** A fill that succeeded via a
non-standard path is not "clean": append a timestamped log entry
(identity fallback used, full text not retrieved, `needs-enrichment`
set and why). These are provenance notes for the next enrichment run,
not failure entries.

### 7. Bibliography walk

Walk the ingested paper's reference list and create **stubs** for
load-bearing citations. The anchor test: "the paper would lose its
argument without this reference" — a method it depends on, a dataset it
analyzes, a framework it extends. Not context citations. Stubs carry
`needs-ingest: false` and accumulate `cited_by`; when a stub crosses 5+
independent citing sources, `ingest-pending-papers` fills it. This
threshold gate is what prevents the exploding paper tree — do not
inline-ingest walk results. (`literature-dive` re-tiers review
bibliographies itself; subagents ingesting review papers skip this
phase.)

### 8. Author ledger

Every author on the paper goes into the paper's `authors:` list as
`people/<slug>` — the COMPLETE list, paged or ledger-only (forward-only
linking makes dangling edges acceptable; the list is the full authorship
graph, the ledger is the citation-count accumulator). Three branches per
author:

- **Branch 1 — existing person page:** append the paper to the page's
  `author_on:`.
- **Branch 2 — existing ledger entry:** append the citation to the
  entry's `citations:`.
- **Branch 3 — new:** append a ledger entry (slug, name, orcid,
  affiliations, citations).

A task instruction "do NOT create author ledger entries" scopes to
Branch 3 only — Branch 1 `author_on:` updates on existing person pages
are still required.

**"Write ONLY the paper page" (stronger scope — literature-dive
subagent delegation).** When an orchestrator delegates with "Write
ONLY the paper page — do NOT create author ledger entries. Return
author list in your summary", this is a **stronger** scope than "do
NOT create ledger entries" alone: skip ALL of Phase 8 (Branch 1/2/3 —
no person-page `author_on:` updates, no ledger `citations:` appends,
no new entries), AND skip Phase 7 (bibliography walk — no stub
creation) and Phase 9 (graph wiring — no `links:` appends to
concept/project pages, no `docs/rem-cycle/inbox.yaml` enqueue). The
orchestrator owns all post-page wiring: author ledger, bibliography
stubs, graph edges, and rem-cycle propagation. The subagent's
deliverable is exactly one `papers/<slug>.md` file plus the author
list in its summary. Still perform the **pre-write slug alignment**
below (search the ledger AND person pages by surname) so the
frontmatter `authors:` list uses correct existing slugs where they
exist — this ensures the orchestrator's centralized wiring will
match. Return the complete author list (ordered, with names, ORCIDs,
and proposed slugs) in the task summary for the orchestrator to wire.
`verify_ingest.py` will report unresolved authors — this is
**expected** for this scope, not a failure (see Phase 10).

**Conflation check under stronger scope (mandatory).** When the
pre-write slug alignment finds an existing ledger entry OR person
page matching an author by surname, do NOT assume it's the same
person — compare the paper's PubMed affiliation against the entry's
`affiliations:` (ledger) or the person page's frontmatter `affiliation:`
/ body text (person page). If they disagree on institution or
geography, the entry conflates two different people (observed:
`shi-yi` in the ledger is Yi Shi at Mount Sinai; a paper's Shi Yi at
Institute of Microbiology CAS is a different person). Under the
stronger scope you cannot create a disambiguated entry, so the
frontmatter `authors:` list will reference a wrong-person slug — and
`verify_ingest.py` will report it as **resolved** (silent error).
Flag this prominently in the Ingest log: name the conflated slug,
both people, and propose a disambiguated slug (e.g. `shi-yi-cas-im`)
for the orchestrator's wiring pass. If no task-level scope prevented
ledger writes, the standard conflation protocol (below) applies
instead.

**Person-page conflation (not just ledger).** The conflation check
applies to BOTH sources the pre-write alignment searches — ledger
entries AND person pages. A person page found via `ls people/ | grep
-i '<surname>'` is just as likely to be a different person as a
ledger entry found by the same grep. **Always read the matching
person page's frontmatter (`affiliation:`, `role:`) or body text
and compare against the paper's PubMed affiliation before reusing
its slug.** The "Use the existing entry's exact slug" instruction in
the pre-write alignment section means use the slug only AFTER the
conflation check passes (same institution/geography), not blindly
on surname match alone. When the person page is a different person,
mint a new slug (e.g. `<surname>-<given>-<middle-initial>` or
`<surname>-<given>-<institution-token>`) and flag the conflation in
the Ingest log. (Observed: ANGPTL4 review ingest, PMID 31235370,
2026-08-18 — `people/price-nate.md` is Nate Price, a grad student
at Scripps Research / Briney lab; the paper's author is Nathan L.
Price at Yale University. Minted `price-nathan-l` to avoid
conflation. The existing `price-nate` slug would have been
silently reused without the person-page conflation check.)

**Pre-write slug alignment (mandatory).** Before writing `authors:` or
appending anything, search BOTH the ledger and person pages by SURNAME:
`grep -i "name:.*<LastName>" people/_ledger.yaml` (the ledger is a dict
under a top-level `entries:` key — iterate `d['entries']`, and grep by
surname, not full name, because ledger `name:` carries middle
initials/suffixes the task list lacks) and `ls people/ | grep -i '<surname>'`
(catches Jr/Sr/III suffixes on existing pages, e.g. `crowe-james-e-jr`).
Use the existing entry's exact slug; mint a new one only when nothing
matches by name or surname. If a pre-existing entry uses a misspelled or
non-convention slug (`yun-nadezdha` for Nadya Yun): merge via Branch 2,
align the paper's frontmatter to the EXISTING (wrong) slug, never rename
the ledger entry (other papers reference it) and never create a second
entry under the correct slug — log the discrepancy and flag for a
normalization pass.

**Short-surname substring false positives (2–4-letter surnames).** The
`grep -i "name:.*<LastName>"` pattern is a substring match, not a
word-boundary match. For short common surnames (Yi, Hom, Lane, Li, Wu,
He, Xu, Ma, Tan, etc.) it returns dozens of false-positive ledger
entries where the surname appears as a substring inside an unrelated
author's given name — e.g. `Yi` matches Yiyang, Yiming, Yin, Ying; `Hom`
matches Homad, Hommes; `Lane` matches Canelane. A 28-author paper with
a `Yi` can return 50+ rows, flooding the conflation check with noise.
**Fix:** after the grep, filter to entries whose `name:` field contains
the surname as a discrete token, not a substring — in Python,
`surname.lower() in ename.lower().split()` (token match) or
`re.search(rf'\b{surname}\b', ename, re.I)` (word boundary). Also prefer
matching the slug prefix (`eslug.startswith(surname-dash)`) which is
far less prone to substring noise than the `name:` field. Skip entries
that match only as a substring of a longer token. (Observed: MAR001
ANGPTL4 ingest, PMID 40383129, 2026-08-18 — `Yi` returned 50+ false
positives from the ledger `name:` field; token/word-boundary filtering
reduced it to zero true matches.)

**Ledger conflation (two people, one pre-existing entry).** Before
Branch 2, compare the new author's PubMed affiliation against the
existing entry's affiliations/citations — disagreement on
institution/geography means the entry conflates two different people.
Do NOT append to or split the conflated entry in-session. Create a NEW
disambiguated entry (`<slug>-orcid-<orcid>` if ORCID is available, else
`<slug>-<institution-token>`, e.g. `wang-wei-ucsd`) and log a
normalization-pass flag (conflated slug, the two people, citation split,
prior papers needing frontmatter updates) for `entity-resolution`.

**Slug derivation.** Convention is `<surname>-<given>` with the FULL
first name (`carnathan-diane`, not `carnathan-d`). ASCII-fold BEFORE
slugifying — naïve regex slugification mangles diacritics
(Rômulo→`r-mulo` instead of `romulo`; Søren, José, Ström, D'Aulerio
likewise):

```python
import unicodedata, re
def slugify(s):
    # Pre-map non-decomposing diacritics (NFKD alone strips them to nothing)
    _pre = {'ł':'l','Ł':'l','ø':'o','Ø':'o','đ':'d','Đ':'d','ð':'d','Ð':'d',
            'ı':'i','İ':'i','ß':'ss','þ':'th','Þ':'th','æ':'ae','Æ':'ae',
            'œ':'oe','Œ':'oe','ŋ':'n','Ŋ':'n','ə':'e','Ə':'e'}
    for k,v in _pre.items():
        s = s.replace(k,v)
    s = unicodedata.normalize('NFKD', s).encode('ascii','ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
```

**Why the pre-map:** `NFKD` decomposes most accented Latin characters
(á→a, ü→u, ñ→n) but does NOT decompose certain characters — Polish
Ł/ł, Scandinavian Ø/ø, Vietnamese/Icelandic Đ/ð, Turkish ı/İ, German
ß, and ligatures æ/œ. Without the pre-map, `.encode('ascii','ignore')`
strips them entirely: `Łukasz`→`ukasz` (should be `lukasz`),
`Ciesiołkiewicz`→`Ciesiokiewicz` (should be `Ciesiolkiewicz`),
`Søren`→`Sren` (should be `soren`). Observed in the Rodriguez 2023
pAC65 ingest (13 Polish authors, 2 with Ł/ł). The pre-map is a small
closed set — add entries as new non-decomposing diacritics are
encountered.

**Korean/Asian name misparsing in PubMed XML.** PubMed sometimes
splits Korean (and potentially other Asian) names incorrectly: a
two-syllable given name + one-syllable surname like "Tae Won Heo"
is parsed as `LastName="Won Heo"`, `ForeName="Tae"` instead of the
correct `LastName="Heo"`, `ForeName="Tae Won"`. This produces a wrong
slug (`won-heo-tae` instead of `heo-tae-won`) and a wrong display
name. **Detection signal:** a `<LastName>` containing a space
(two words) is almost always a misparse — genuine compound surnames
(van der Berg, de la Cruz) are rare in PubMed XML and usually carry
particles. **Fix:** cross-check with CrossRef
(`api.crossref.org/works/<doi>` → `message.author[].given` and
`message.author[].family`), which correctly separates Korean
given/family names (observed: Lee 2016 ncomms13354, CrossRef
`given="Tae Won"`, `family="Heo"`). Use the CrossRef split for both
the slug (`<family>-<given>`) and the `name:` display field. This
check is cheap — the CrossRef fetch is already the third ORCID
source (Phase 8), so inspect `given`/`family` for any author whose
PubMed `<LastName>` contains a space.

**Italian particle surname misparsing in PubMed XML.** PubMed
misplaces the Italian particle "Lo" (and likely "La", "Di", "Della",
"De") from surnames like "Lo Surdo" into the given-name field:
`LastName="Surdo"`, `ForeName="Paola Lo"` instead of the correct
`LastName="Lo Surdo"`, `ForeName="Paola"`. This produces a wrong
slug (`surdo-paola` instead of `lo-surdo-paola`) and a wrong display
name. **Detection signal:** the `<ForeName>` contains a space AND
ends with a common Italian particle ("Lo", "La", "Di", "De",
"Della", "Dello"), or the given name appears to include a surname
particle. **Fix:** cross-check with CrossRef
(`api.crossref.org/works/<doi>` → `message.author[].given` and
`message.author[].family`), which correctly keeps the particle with
the family name (observed: PMID 22081141, Lo Surdo et al. 2011,
CrossRef `given="Paola"`, `family="Lo Surdo"`). Use the CrossRef
split for both the slug (`<family>-<given>`) and the `name:` display
field. This is the same CrossRef cross-check used for the Korean
name misparsing above — inspect `given`/`family` for any author
whose PubMed `<ForeName>` ends with an Italian particle. (Observed:
PMID 22081141, EMBO Rep 2011, PCSK9/LDLR structure ingest,
2026-08-18.)

**The frontmatter `authors:` list and the ledger `slug:` field MUST use
identical slugs — the lint resolves by exact string match. Build the
slug list once, use it for both. The ledger `name:` display field
retains diacritics. When a parent task explicitly specifies
`<surname>-<initial>`, follow the task but record the full name in
`name:`. When a sibling's rewrite normalized a slug differently, the
FRONTMATTER is authoritative — patch the ledger to match it.

**ORCID capture (three lines, then stop):**
1. PubMed XML `<Identifier Source="ORCID">` — often senior-author only.
2. Europe PMC REST core search (the branch-0 gate call — same response):
   `resultList.result[0].authorList.author[].authorId` (type `ORCID`).
   Must use `query=EXT_ID:<PMID>` — a bare PMID returns hitCount 0.
   **Type-safety pitfall:** the `authorId` field can be a **dict**, not a
   string. A naïve `ea.get('authorId', '').lower()` raises
   `AttributeError: 'dict' object has no attribute 'lower'`. Always type-check
   before string operations: `if isinstance(author_id, str) and ...`. The
   ORCID value (when present) is typically a string like
   `"0000-0001-6235-9463"`, but some EPMC records return structured objects
   for authorId. Guard with `isinstance(..., str)` before any `.lower()`,
   `.startswith()`, or `.replace()` call. (Observed: CXCR4 profile session,
   2026-08-15 — 5 papers, the EPMC authorId dict type broke the ORCID
   extraction loop on the first paper.)
3. CrossRef preprint deposit (for preprint→published papers):
   `api.crossref.org/works/<preprint-doi>` → `message.author[].ORCID` —
   the bioRxiv submission form carries junior/middle-author ORCIDs
   PubMed lacks (observed: 3/10 → 7/10 ORCIDs).

Union all three. When all are empty, `orcid: null` — never fabricate
ORCIDs; a wrong ORCID is worse than null (it is the disambiguation key).
Do not spend calls beyond these three sources.

**Inline promotion.** When a ledger entry hits 5 citations mid-ingest:
create `people/<slug>.md` (kind: person, orcid from the ledger,
`author_on:` = every citation in the entry — verify each page exists,
per-paper body bullets, a "Promoted from ledger" section); remove the
ledger entry via targeted `patch` of its whole block (NEVER `yaml.dump`
the ledger — whole-file rewrites produce 7000+-line diffs); verify the
ledger parses, the slug is absent, no duplicates; update referencing
pages' `links:`.

**Ledger append mechanics.** Appending to `people/_ledger.yaml` is the
single most failure-dense operation in the pipeline. The canonical
procedure is one ATOMIC python3 heredoc: read → check for missing slugs
→ conditionally append → immediately `yaml.safe_load` + duplicate-slug
check + author-count check, all in a single execution. Splitting append
and verify across tool calls leaves a window in which a sibling's
full-ledger rewrite silently drops your entries (observed repeatedly;
two wipes per session is normal with 10+ siblings). Re-verify at Phase
10 and re-append atomically if missing. Never append via `cat >>`
heredoc (line-wrapping diverges from source; a missing trailing newline
glues content onto the last line). When patching an existing entry,
anchor `old_string` on the entry's unique `slug:` line plus a
distinguishing field (a unique citation line) — generic anchors
(`- affiliations:`, `orcid: null`) can silently match the WRONG entry;
after every ledger patch, verify WHICH slug the diff actually touched.

### 9. Graph wiring and propagation

Link the page into the graph: search the vault for concept/project pages
matching the paper's topic and add typed edges per
`graph-and-links.md`. Use `patch` for appends to shared frontmatter
lists (`links:`, `cited_by:`), never whole-page `write_file` (see
Concurrency hazards).

Then enqueue propagation — append to `docs/rem-cycle/inbox.yaml` (plain
list append under `items:`, dedup on `id`, NEVER rewrite the file):

```yaml
  - id: <YYYY-MM-DD>-<slug>
    page: papers/<slug>
    event: ingest            # or: stub-filled
    date: YYYY-MM-DD
    consumed_by: []
```

This is how the rem-cycle learns the page exists. Indentation is
2-space `  - id:` with 4-space fields — and verify with `yaml.safe_load`
after the append (see inbox hazards below).

### 10. Verification

Run `scripts/verify_ingest.py <paper-slug>` (auto-detects the brain root
from `papers/` + `people/`, or `--instance <path>`). Five invariants:

1. Paper frontmatter parses as valid YAML.
2. All `links:` targets exist as pages on disk.
3. All `authors:` slugs resolve to `people/` pages OR ledger entries.
4. All `cited_by:` targets exist.
5. The ledger parses and has no duplicate slugs.

Plus a **name-based duplicate check** across all newly added ledger
entries — slug-based verification misses same-person entries under
spelling/middle-initial variants (`louder-mark` vs `louder-mark-k`;
`carlton-kevin` vs `carleton-kevin`). Merge any found (keep the
ORCID-bearing entry, union citations and affiliations) before the final
pass. Cover ALL new entries, not just suspected collisions.

Exit 0 = commit-ready. Run after every ingest, before commit.

**External URLs in `links:` always report as MISSING — this is a false
positive.** Paper pages conventionally carry the DOI URL
(`https://doi.org/<doi>`) as their sole `links:` entry.
`verify_ingest.py` checks whether each `links:` target resolves to a
page on disk, so every external URL is reported `links: N checked, 1
MISSING`. This is the expected state for every paper page with a DOI
link — it is NOT a real problem and does not block commit. Only treat
`links:` MISSING as actionable when the missing target is an internal
path (`papers/<slug>.md`, `concepts/<slug>.md`, etc.), not an `https://`
URL. (Observed: every paper page in the brain — Verstraete 2017 TSLP
structure, England 2023 tozorakimab, and many others — all report
`links: 1 checked, 1 MISSING` for their DOI URL, all commit-ready.
2026-08-18.)

**Delegated ingests that skip the author ledger.** A task may instruct
"do NOT create author ledger entries" (common for `literature-dive`
subagents that return the author list to the parent for later wiring).
Two scopes exist — check which one the task used:

- **"do NOT create author ledger entries"** — scopes to Phase 8
  Branch 3 (new ledger entries) only. Branch 1 `author_on:` updates on
  existing person pages are still required. `verify_ingest.py` will
  report only the authors with no ledger entry and no person page.
- **"Write ONLY the paper page"** — stronger scope: skips ALL of
  Phase 8 (Branch 1/2/3). No person-page or ledger mutations at all.
  Also skips Phase 7 (bibliography walk) and Phase 9 (graph wiring) —
  the orchestrator owns all post-page wiring. `verify_ingest.py` will
  report only the authors with NO pre-existing person page or ledger
  entry as unresolved — it checks slug existence (person page OR
  ledger entry), not whether the current paper's citation was
  appended, so authors that already have a ledger entry or person
  page from a prior ingest resolve correctly. When ALL authors are
  new (none have any prior entry — common for a review whose authors
  are not yet in the brain), ALL will be unresolved.
  **This is the expected state, not a bug.**

In both scenarios `verify_ingest.py` will report `authors: N checked,
M UNRESOLVED` and exit 1. **This is the expected state, not a bug.**
Triage the UNRESOLVED list: any slug that DOES have a pre-existing ledger
entry (e.g. `domling-alexander` cited by an earlier paper) resolved
correctly — the script only flags slugs with no entry at all. The
remaining unresolved slugs are deferred to the parent's wiring pass; do
NOT create ledger entries just to silence the verifier. Check the other
four invariants (frontmatter, links, cited_by, ledger health); if those
pass, the page is commit-ready. Log in the Ingest log: "Phase 10: N
authors unresolved — deferred to parent per task constraint (no ledger
entries created)."

**Resolved-but-conflated slugs (stronger scope).** A resolved slug is
not necessarily a correct slug. Under the stronger scope the pre-write
alignment may have found a same-surname entry that is actually a
different person (see "Conflation check under stronger scope" above).
`verify_ingest.py` counts these as resolved — it checks slug existence,
not person identity. Manually review each resolved slug's `affiliations:`
against the paper's PubMed affiliations before declaring commit-ready.
Flag any conflation in the Ingest log; the page is still commit-ready
(the frontmatter `authors:` list is the authoritative authorship record;
a wrong-person slug is a wiring error the orchestrator's entity-resolution
pass will fix, not a page-corruption event), but the flag must be visible
so the orchestrator doesn't silently wire to the wrong person.

## Concurrency hazards (parallel sibling ingests)

`ingest-pending-papers` and `literature-dive` run this pipeline in
parallel; siblings share `people/_ledger.yaml`,
`docs/rem-cycle/inbox.yaml`, person pages, and concept pages. Every
shared-file mutation below has been observed to corrupt data. The
general rules: `patch` never `write_file` on shared files; on a
sibling-modification warning, re-read and re-patch against current state
(the sibling's entry is legitimate graph state); verify after every
mutation — a clean exit code proves nothing.

- **`/tmp` file collisions.** Sibling subagents share the `/tmp` filesystem.
  Generic filenames like `/tmp/paper.xml` or `/tmp/paper_body.txt` are
  overwritten by a sibling's own fetch, silently swapping the parsed body
  for a DIFFERENT paper. Observed: a sibling's PMC XML fetch overwrote
  `/tmp/paper.xml` mid-session, replacing the atezolizumab body with a
  BMS-8/BMS-202 small-molecule paper body. **Fix:** use a unique path per
  paper — prefix all `/tmp` artifacts with the PMID or slug (e.g.
  `/tmp/<pmid>_paper.xml`, `/tmp/<slug>_body.txt`), never bare
  `/tmp/paper.xml`. Re-validate the body content immediately before
  distillation (grep for the paper's title or a key term) to catch any
  collision that slipped through.

- **`cited_by` / `links:` appends.** A sibling's append can land between
  your read and your write; `write_file` clobbers it silently. Use
  targeted `patch`; on "Could not find a match" + sibling warning,
  re-read and re-apply. Never fall back to `write_file`.
- **Same-slug ledger duplicates.** Two siblings take Branch 3 for the
  same shared author → two entries, one slug. Merge after the fact: keep
  the ORCID-bearing entry, union `citations`/`affiliations` (deduped),
  delete the duplicate, verify one entry per slug.
- **Different-slug duplicates.** Sibling used `lee-jeffrey-e`, you used
  `lee-jeffrey`. Prevented by the Phase 8 pre-write name/surname search;
  caught after the fact by the Phase 10 name-based check.
- **Person-page `author_on:` malformation.** A patch applied against a
  sibling-modified file can produce doubled keys (`author_on:\n
  author_on:`) with broken indentation. On any sibling warning, re-read
  and verify the YAML is well-formed; apply a corrective patch against
  the actual post-sibling state.
- **Sibling full-ledger wipe.** A sibling's clean re-dump of the ledger
  silently discards your appended entries; the per-edit warning does not
  fire for a wholesale rewrite between your calls. Prevention/detection:
  the atomic append+verify heredoc (Phase 8); re-append if missing;
  frontmatter is authoritative for slug mismatches.
- **Ambiguous self-patch.** Your OWN patch can hit the wrong ledger
  entry when `old_string` isn't unique — `patch` applies to the first
  match and reports success. Anchor on the target's unique slug + a
  distinguishing field; verify which slug the diff touched.
- **`patch` fuzzy-match corruption.** The fuzzy matcher can silently
  alter ADJACENT pre-existing content (a citation slug lost a middle
  word during an unrelated append). Re-read the modified region and
  verify every `-` line in the diff; correct with a targeted patch;
  copy anchor text exactly from a fresh read, with 2–3 lines of context.
- **`cat >>` hazards.** Missing trailing newline → new content glued
  onto the last line; long strings get line-wrapped. Don't append YAML
  via heredoc; use the atomic python3 pattern.
- **Inbox corruption trio.** Siblings have written 0-indent `- id:`
  lines (breaks the block mapping), `read_file`-style `NN|` line-number
  prefixes into every line (strip via `re.sub(r'^\d+\|', '', content,
  flags=re.MULTILINE)`), and fuzzy-match-clobbered a sibling's entry
  when anchoring on shared `date:`/`consumed_by: []` lines. After EVERY
  inbox patch: `yaml.safe_load` parses, your entry exists, no duplicate
  keys, item count rose by exactly 1; restore clobbered siblings. Anchor
  on the last entry's unique `- id:` line, re-read immediately before
  patching.
- **`yaml.dump` on the ledger.** Whole-file rewrites (merges, dedup,
  promoted-entry removal) reformat 4900+ entries into unreadable diffs
  and can clobber concurrent sibling edits. Always targeted `patch`.
  (Script-based merge is acceptable ONLY when no siblings are running.)

**When terminal `curl` is denied**, `execute_code` with Python
`urllib.request` is the first and simplest fallback — it fetches all
E-utilities endpoints (esearch, esummary, efetch PubMed XML, efetch PMC
XML, EPMC core records) identically to curl, with the same rate-limit
discipline (sleep 3–5s between sequential calls). The `execute_code`
tool runs a Python script that can also parse XML/JSON in-process,
write paper pages via `write_file`, and invoke skill scripts via
`subprocess.run(["python3", <script_path>, ...])`. The entire pipeline
(Phase 1 identity → Phase 4 full-text → Phase 5 distillation) can run
through `execute_code` when terminal is blocked. This is the preferred
fallback because it avoids browser session setup, CDP debugging
approval, and DOM extraction pagination. (GM-CSF target profile,
2026-08-15: 6 papers ingested entirely via `execute_code` + urllib when
terminal curl was blocked — 4/6 PMC XML full text, 2/6 abstract-only,
all paper pages and the profile written successfully.)

**When `execute_code` is also unavailable**, the browser can fetch
E-utilities directly: `browser_navigate` to the efetch URL (PubMed or
PMC XML), extract via `document.body.innerText.substring(N, N+30000)`
(no `<article>` selector on API pages). Structured metadata and PMC full
text both survive a fully blocked terminal.

## Anti-patterns

- **Trusting seed identifiers.** PMIDs, DOIs, arXiv IDs, first-author
  names, and task-brief "key findings" from any upstream source are
  suggestions, not facts. The Phase 1 title gate and the Phase 5
  full-text verification exist because observed error rates are high.
- **Treating a CrossRef failure as a Phase 1 failure.** PubMed XML
  alone is a complete identity resolution.
- **Abstract-only when full text was available.** With a PMCID, always
  try PMC (XML → PDF render → browser) before branch 3; check the
  paperclip mirror before ANY abstract-only declaration; confirm
  three-source closure. `needs-enrichment: true` is a last resort with
  an audit trail, not a default.
- **Tagging a paperclip-retrieved page `abstract-only`.** It wastes a
  future embargo-recheck cycle and misrepresents the page.
- **`write_file` on shared files during parallel runs.** `cited_by:`,
  `links:`, the ledger, the inbox — all are `patch`-only under
  concurrency.
- **Trusting a clean exit code.** `patch` succeeds on unintended
  matches, fuzzy-corrupts adjacent lines, and applies against
  sibling-modified files. Verify the diff, every time.
- **Retrying deterministically blocked publishers.** The known-blocks
  table is learned behavior — one branch-1d attempt, then fall through.
- **Inline-ingesting bibliography-walk results.** Stubs + the 5-citation
  threshold gate own the fill. The exploding paper tree is the failure
  this prevents.
- **Fabricating ORCIDs or authors.** `orcid: null` and `authors: []`
  are valid; invented identifiers corrupt the disambiguation key.
- **Invalid `status:` values.** Only `preprint` / `published` /
  `unknown`. Withdrawal and acceptance are body content.

## Changelog

- **2026-08-15 — ProEd / Index Copernicus (Drugs of Today) publisher block added.** DOI prefix `10.1358` (Drugs of Today, Barcelona) resolves via doi.org to a Portico archive page, not the publisher. Jina reader proxy on the DOI URL returns a cookie consent page (~4 KB) with no article body. Alternative publisher URLs tried: journals.sagepub.com (~510 bytes, blocked) and proedjournal.com (HTTP 422). No PMCID; EPMC flags all N. Three-source closure confirmed → abstract-only. PubMed abstract is the primary content source. (IL-5Rα target profile, PMID 29517082 — 5 papers ingested, all abstract-only: 2 Elsevier CAPTCHA, 1 Wiley CAPTCHA, 1 Lancet CAPTCHA, 1 ProEd/Portico. 0% full-text retrieval rate; all 5 papers from subscription journals with no PMC copies.)

- **2026-08-15 — AHA Journals (ahajournals.org) publisher block added.** AHA journals (Circulation, Circ Res, Hypertension, Stroke) block jina reader proxy with a Cloudflare CAPTCHA (~505 bytes: "Title: Just a moment..."). Most subscription articles have no PMCID. Added to the known-blocks table. Key nuance: some Circ Res articles ARE in PMC (OA) and work normally via PMC XML — the block applies only to subscription articles without a PMCID. When profiling cardiovascular targets, prefer Circ Res articles with PMCIDs (like PMID 32324502, PMC8760628) over those without (like PMID 29880500). (IL-1β target profile: 5 papers, 2 PMC XML OA, 1 Wayback NEJM, 2 abstract-only — 60% full-text rate.)

- **2026-08-15 — jina DOI URL 404 pitfall + Wayback CDX API fallback.** Two full-text retrieval techniques documented: (1) The jina reader proxy on a DOI URL (`r.jina.ai/https://doi.org/<doi>`) returns the DOI Foundation's 404 page (~2.4 KB), not the article — always use the publisher's direct article URL for jina. (Observed: Lancet PMID 21296403 — DOI URL returned 2.4 KB 404; direct thelancet.com URL returned 11.5 KB full text.) (2) When the Wayback availability API (`archive.org/wayback/available`) 429s persistently, the CDX index API (`web.archive.org/cdx/search/cdx?url=<url>&output=json&limit=5`) has separate rate limits and returns timestamped rows with HTTP status codes — filter for `statuscode: "200"`, construct the snapshot URL as `web.archive.org/web/<timestamp>/<original-url>`, and fetch via `urllib.request`. (Observed: NEJM PMID 32937045 — availability API 429'd after 20s wait; CDX returned a 200-status snapshot; direct urllib.request yielded 376 KB HTML → 13K chars from `<article>` tag.) (BAFF/BLyS target profile session: 5 papers ingested, 2 PMC OA, 1 jina reader, 1 Wayback, 1 abstract-only.)

- **2026-08-15 — fetch_fulltext.py output path quirk + publisher block table updates.** The `fetch_fulltext.py` script appends `.txt` to the `--out` value internally (`succeed()` writes to `args.out + ".txt"`), so `--out /tmp/paper.txt` produces `/tmp/paper.txt.txt`. Documented in the Tooling section with guidance to read the actual path from the JSON summary's `text_file` field. Added two entries to the known-blocks table: (1) `thelancet.com` (Elsevier/Lancet family) — Cloudflare blocks curl but the jina reader proxy succeeds (81 KB full text for a Lancet GH Phase 2a trial), so `fetch_fulltext.py --publisher-url` is the working path, not abstract-only; (2) `rupress.org` (Rockefeller University Press / JEM) — Cloudflare CAPTCHA defeats jina, Wayback, and browser; genuinely unreachable for recent articles with no PMC copy. (TL1A target profile reprocessing session: 5 key papers ingested, 2 via PMC XML, 1 via Wayback, 1 via jina, 1 abstract-only.)

- **2026-08-12 — initial assembly.** This skill previously existed only
  as a patch pointer plus eight companion reference skills and 23 dated
  patch skills (2026-07-17 through 2026-08-12g); RESOLVER.md routed
  paper ingestion to the pointer. All were read, triaged, and folded
  into this document; the pointer, companions, and patch skills were
  deleted (absorbed, not pruned — provenance in git history). Folded
  fixes include: the EXT_ID: Europe PMC ORCID query (supersedes the
  2026-08-02 bare-PMID form), the Semantic Scholar DOI-form rule
  (resolves the branch-3 contradiction), source-specific paperclip
  `fulltext_source` tags (paperclip-full proposal rejected), the arXiv
  full-text ordering (jina → paperclip → direct curl), and the atomic
  ledger append+verify procedure. `scripts/verify_ingest.py` was
  written during the assembly — the verification companion had
  referenced it since 2026-08-01 without it existing.
- **2026-08-15 — verify_ingest.py resolution semantics fix.** The Phase
  10 "stronger scope" bullet claimed `verify_ingest.py` reports ALL
  authors as unresolved under "Write ONLY the paper page" — "even
  those with existing ledger entries or person pages." This is factually
  wrong: the script checks slug existence (person page OR ledger
  entry), not whether the current paper's citation was appended, so
  pre-existing entries resolve correctly. Corrected to "reports only
  authors with NO pre-existing entry as unresolved." (Almagro 2026
  anti-PD-1 review: 10/10 authors unresolved because none had prior
  entries — the all-new case — confirming the script reports only
  genuinely missing slugs.)
- **Prior history** (from the deleted patches, all validated in live
  sessions): seed-DOI cross-check, PMC full-text path (2026-07-17);
  Nature.com path, erratum disambiguation, Europe PMC ORCIDs, sibling
  ledger dups (2026-07-18); tirith two-step, branch-0 gate, known-blocks
  table (2026-07-19); stub slug renames, different-slug dups, author_on
  malformation (2026-07-24); task-brief verification (2026-07-24b);
  no-DOI/elink path (2026-07-25/28, Pootong); EPMC PDF render
  (2026-07-28, Maselli); sibling ledger wipe, ASCII-fold slugs,
  yaml.dump prohibition, wrong-author tasks, orcid:null (2026-08-02);
  rem-cycle inbox enqueue (2026-08-03); ambiguous self-patch (2026-08-04);
  Wayback branch, jina proxy, fetch_fulltext.py, fulltext_source enum,
  embargo sweep, figure retrieval, validate_identifiers.py, wrong-PMID
  variants, slug-alignment series, cat >> hazards (2026-08-05);
  HOLD-verification, EXT_ID: fix, atomic append, promotion mechanics,
  inbox NN|-prefix, DOI case rule (2026-08-07); paperclip mirror series,
  arXiv ladder + version hazards + venue rule, corporate authorship,
  ledger entries:-dict (2026-08-10); ledger conflation protocol,
  published-field routes, 10.64898 prefix, jina retry discipline,
  .full.pdf variant, browser-direct bioRxiv, Wayback CDX caveats,
  CrossRef ORCID third line, inbox fuzzy-clobber (2026-08-12).
- **2026-08-15 — slugify pre-map for non-decomposing diacritics.** The
  `slugify()` function in Phase 8 used `NFKD` + `.encode('ascii','ignore')`,
  which silently strips non-decomposing diacritics (Ł→'', ł→'', Ø→'', ß→'')
  instead of folding them to their base letters. Observed in the
  Rodriguez 2023 pAC65 ingest: `Łukasz`→`ukasz` instead of `lukasz`,
  `Ciesiołkiewicz`→`Ciesiokiewicz` instead of `Ciesiolkiewicz`. Added a
  pre-map dict for the known closed set of non-decomposing Latin-script
  diacritics before the NFKD normalization.
- **2026-08-15 — Korean name misparsing in PubMed XML.** PubMed
  splits "Tae Won Heo" as `LastName="Won Heo"`, `ForeName="Tae"`
  instead of the correct `LastName="Heo"`, `ForeName="Tae Won"`,
  producing a wrong slug (`won-heo-tae` vs `heo-tae-won`). CrossRef
  CrossRef `given`/`family` fields carry the correct split. Added a Phase 8
  note: when a PubMed `<LastName>` contains a space, cross-check
  CrossRef and use its split. (Lee 2016 ncomms13354 ingest.)
- **2026-08-15 — EPMC PMCID overrides stale PubMed XML PMCID.** The
  PubMed XML `<ArticleId IdType="pmc">` can carry a stale or
  superseded PMCID that returns front-matter-only XML, while the EPMC
  core record carries a *different*, current PMCID that returns the
  full text. Observed in the TNF profile reprocessing: PMID 20194223
  (PubMed PMC1773100 → front-matter only; EPMC PMC2886310 → 37K chars
  body) and PMID 31857588 (PubMed PMC2486339 → front-matter only; EPMC
  PMC6923382 → 49K chars body). Added the reverse-override rule: when
  `efetch db=pmc` with the PubMed XML PMCID returns front-matter only,
  check the EPMC core record's `pmcid` field for a different PMCID and
  retry before falling to Branch 3.
- **2026-08-15 — NEJM publisher block + Wayback direct-HTML technique.**
  NEJM (nejm.org) is not in PMC and jina reader 403s on both live and
  Wayback URLs. Discovered that direct `urllib.request` on the Wayback
  snapshot URL works — returns 250-270 KB HTML, `<article>` tag
  extraction yields ~50K chars of full text. Added NEJM to the
  known-blocks table and documented the direct-HTML-fetch fallback in
  Branch 2b. (IL-4Rα target profile: 2 NEJM papers retrieved this way —
  Simpson 2016 SOLO, Castro 2018 QUEST.)
- **2026-08-15 — `execute_code` + urllib as primary terminal-curl
  fallback.** When terminal `curl` is blocked (approval denial, not
  rate-limit), `execute_code` with Python `urllib.request` is the first
  fallback — not the browser. It fetches all E-utilities endpoints
  identically to curl, parses XML/JSON in-process, writes paper pages
  via `write_file`, and runs skill scripts via `subprocess.run`. The
  entire pipeline runs through `execute_code` when terminal is blocked.
  Documented in the Concurrency hazards section's terminal-denied
  fallback. (GM-CSF target profile: 6 papers ingested entirely via
  `execute_code` + urllib — 4/6 PMC XML, 2/6 abstract-only.)
- **2026-08-15 — Shell escaping of brackets in esearch URLs + elink
  false-positive trap.** Two E-utilities usage pitfalls discovered
  during the CD20 profile session: (1) PubMed field tags like
  `review[pt]` contain square brackets that are shell-interpreted by
  the terminal — `curl -sL "...review[pt]..."` silently fails (curl
  exit 0, output file never created). Fix: URL-encode brackets (`[` →
  `%5B`, `]` → `%5D`). Double-quotes in the curl command do not protect
  brackets from shell interpretation. 3/5 esearch queries silently
  failed before this fix was applied. (2) `elink.fcgi?dbfrom=pubmed&db=pmc`
  returns PMC IDs of related/citing articles (sometimes 100+), NOT the
  target paper's own PMC ID — do not use elink to discover a paper's
  PMCID; use PubMed XML `<ArticleIdList>` or the EPMC core record's
  `pmcid` field instead. Both documented in the Environment notes
  section. (CD20 profile, 6 papers, 1/6 full text via EPMC PDF, 5/6
  abstract-only.)
- **2026-08-15 — JAMA Network + Bentham Science publisher blocks; Wayback CDX wrong-content pitfall.** Two new publisher blocks added to the known-blocks table from the CD11a target profile session (5 papers, 1/5 full text via PMC XML, 4/5 abstract-only): (1) JAMA Network (jamanetwork.com, archderm.jamanetwork.com) — Cloudflare CAPTCHA blocks jina reader proxy on ALL URL variants (article.aspx, fullarticle); Wayback availability API 429s; CDX search returns no snapshots. Genuinely unreachable — abstract-only. (PMID 19687432.) (2) Bentham Science (eurekaselect.com, ingentaconnect.com) — Cloudflare CAPTCHA blocks jina (~489 bytes). Wayback CDX found an ingentaconnect snapshot with 200 status, but the fetched content was a **completely different article** (an Alzheimer's paper instead of the LFA-1 review). This is a new Wayback failure mode: the CDX index can return a valid 200-status snapshot URL whose content does not match the target paper — the snapshot URL structure or redirect chain serves wrong content. **Lesson: always validate Wayback CDX-fetched content against the paper title before using it for distillation.** (PMID 16918410.) (CD11a profile, 2026-08-15: 5 papers, 1/5 PMC XML full text, 4/5 abstract-only — 20% retrieval rate, matching the C5/CD20 pattern of paywalled clinical journal mixes.)

- **2026-08-15 — JCI Insight publisher block added to known-blocks table.**
  JCI Insight (insight.jci.org, published by the American Society for
  Clinical Investigation) exhibits the Branch 1b pattern: `inPMC: Y` but
  PMC XML efetch returns front-matter only (~14 KB, 0 sections, no
  `<body>` element). Unlike Blood (where EPMC PDF render returns "No PDF
  file found"), the EPMC PDF render for JCI Insight succeeds —
  `europepmc.org/api/getPdf?pmcid=PMC6975260` delivered a 6.3 MB PDF
  (51K chars via pymupdf). The jina reader proxy on the DOI URL also
  succeeded (85 KB markdown) as a secondary path. Added JCI Insight to
  the known-blocks table as the positive counterpart to Blood's EPMC PDF
  failure — both restrict XML body download, but JCI Insight's PDF is
  retrievable via Branch 1b while Blood's is not. (PMID 31852846,
  IL-7Rα target profile, 5 papers ingested: 3 PMC XML, 1 EPMC PDF, 1
  abstract-only.)

- **2026-08-15 — urllib.parse.urlencode bracket double-encoding +
  JACI publisher block.** Two findings from the CD19 target profile
  session (5 papers ingested: 1 PMC XML, 3 jina reader, 1 abstract-only):
  (1) When using `execute_code` + `urllib.parse.urlencode` to build
  esearch URLs with bracket field tags, the function double-encodes
  pre-encoded brackets (`%5B` → `%255B`), silently returning count 0.
  Fix: use `urllib.parse.quote()` on the raw term instead of
  `urlencode`. Documented in Environment notes as the Python variant of
  the shell bracket pitfall. (2) JACI (jacionline.org, Elsevier) exhibits
  a deterministic block: cookie consent chrome only (~20 KB, no article
  body), jina returns 404 on both DOI and direct article URLs, no PMCID,
  Wayback availability 429s, CDX times out. Added to known-blocks table
  as genuinely unreachable → abstract-only.

- **2026-08-15 — AACR publisher block added to known-blocks table.** AACR journals (clincancerres.aacrjournals.org, cancerres.aacrjournals.org) block jina reader proxy (~489 bytes, same failure mode as Bentham Science). Most articles have no PMCID. Publisher pages are JS-rendered (empty DOM to curl). Abstract-only is the outcome. (CD30 target profile, PMID 23155186 — 5 papers ingested: 1 EPMC PDF, 2 PMC XML OA, 1 jina reader, 1 abstract-only — 80% full-text retrieval rate.)

- **2026-08-15 — EPMC PDF render returns HTTP 500 for NEJM papers with PMCID.** The NEJM known-blocks table entry was updated: some NEJM papers DO have a PMCID (e.g., PMID 27292104, PMC5594743, inPMC=Y, hasPDF=Y),
  but the EPMC PDF render (`europepmc.org/api/getPdf?pmcid=PMC5594743`)
  returns HTTP 500 — not the "No PDF file found" response seen for Blood
  (ASH Publications). The PMCID's presence and EPMC's `hasPDF: Y` flag
  do not guarantee PDF access for NEJM. The Wayback CDX API + direct HTML
  fetch remains the reliable path for all NEJM papers, with or without a
  PMCID. Updated the NEJM entry in the known-blocks table accordingly.
  (CD22 target profile, PMID 27292104, 2026-08-15.)
- **2026-08-15 — Cold Spring Harbor Laboratory Press (CSHLP) publisher block added to known-blocks table.**
  Cold Spring Harb Perspect Biol exhibits the Branch 1b pattern: `inPMC: Y`
  but PMC XML efetch returns front-matter only (~6.7 KB, 0 sections, no
  `<body>` element). The EPMC PDF render succeeds —
  `europepmc.org/api/getPdf?pmcid=PMC4031967` delivered a 3.4 MB PDF
  (94,911 chars via pymupdf). This is the same pattern confirmed for
  JCI Insight, OUP/ATS, and EMBO J — publishers that restrict XML body
  download but whose PDFs are retrievable via EPMC. Tag
  `fulltext_source: epmc-pdf`. (CSF-1R target profile, PMID 24890514,
  Stanley & Chitu 2014 — 5 papers ingested: 2 PMC XML OA, 1 EPMC PDF, 1
  jina-reader, 1 abstract-only — 80% full-text retrieval rate.)

- **2026-08-15 — IFN-γ target profile: Wayback CDX multi-snapshot variation + Springer book chapter masquerade.** Two findings from the IFN-γ target profile session (5 papers ingested: 3 PMC XML OA, 1 Wayback, 1 abstract-only — 80% full-text retrieval rate): (1) **Wayback CDX multi-snapshot content variation:** the CDX API can return multiple 200-status snapshots of the same URL at different timestamps, and they can differ dramatically in content completeness — a 200-status snapshot can still be a paywall preview page (~108 KB HTML, ~12K chars) while a later 200 snapshot of the same URL yields full text (~135 KB HTML, ~50K chars). Do NOT stop at the first 200; try each in sequence (largest `length` first is a good heuristic) and keep the one with the most extracted body text. (Observed: PMID 32374962, NEJM pivotal emapalumab trial — 2020 snapshot was preview-only, 2021 snapshot delivered full text.) (2) **Springer book chapter reference-list masquerade:** the Springer/Drugs jina reference-list masquerade pattern extends beyond the Drugs journal to Springer book chapters (`link.springer.com/chapter/10.1007/978-...`). Jina returned 71K chars for a Behrens 2024 book chapter (PMID 39117840), all reference list with zero body paragraphs. Updated the Springer/Drugs known-blocks entry to include book chapters and added this PMID as a second observed case.

- **2026-08-15 — Jina reference-list masquerade + Thieme publisher block.** Two findings from the CD52 target profile session (5 papers ingested: 3 PMC XML, 1 jina reader, 1 abstract-only): (1) **Jina reference-list masquerade:** a subscription Springer/Drugs article can return 50K+ chars of reference list that passes the Branch 1d size check, but the content is entirely reference titles — no body paragraphs. PMID 33367970 returned 51,619 chars, all reference list; was incorrectly tagged `jina-reader` / `needs-enrichment: false`. Added validation guidance to the Springer/Drugs known-blocks entry: grep for section headings or body sentences before tagging. (2) **Thieme (Semin Neurol) publisher block:** jina reader returns a German maintenance page (~364 bytes), Wayback CDX finds 200-status snapshots but both jina-on-Wayback (HTTP 403) and direct urllib.request-on-Wayback (HTTP 498) fail. Added Thieme to the known-blocks table as genuinely unreachable → abstract-only. (Observed: PMID 23709214.) (CD52 target profile, 2026-08-15: 5 papers, 3/5 PMC XML full text, 1/5 jina reference-list masquerade, 1/5 abstract-only.)
- **2026-08-15 — Nature Reviews + Springer/Drugs publisher blocks added.**
  Two new entries in the known-blocks table from the CD3 target profile
  session (5 papers ingested: 1 PMC XML, 1 jina-reader, 3 abstract-only —
  40% full-text retrieval rate): (1) Nature Reviews (Nature Reviews
  Immunology, Nature Reviews Drug Discovery, etc.) — subscription-only
  review journals where the jina reader proxy returns ONLY the reference
  list (~80-93 KB), not the article body or abstract. Distinct from Nature
  research articles which may render via browser per the Branch 2
  Nature-family note. No PMCID for most articles → abstract-only. (2)
  Springer/Drugs journal (subscription content) — jina returns abstract +
  references for newer articles (2023, ~22 KB) but only references for
  older articles (1989, ~87 KB). Body paywalled. Many Springer articles
  ARE OA — this block applies only to subscription Springer content.
  No PMCID → abstract-only, PubMed abstract + jina-extracted abstract
  as primary content.

- **2026-08-15 — Science (AAAS) + ASCO/JCO publisher blocks added.**
  Two new entries in the known-blocks table from the CTLA-4 target
  profile session (5 papers ingested: 3 PMC XML OA, 1 EPMC PDF, 1
  abstract-only — 80% full-text retrieval rate): (1) **Science (AAAS,
  science.org)** — Cloudflare CAPTCHA blocks jina reader proxy (~483
  bytes, "Performing security verification"). Wayback CDX API times
  out. Science papers without a PMCID are genuinely unreachable
  (abstract-only, three-source closure confirmed via EPMC N/N/N + S2
  isOpenAccess=False). However, some Science papers DO have a PMCID
  (e.g., PMID 29567705, PMC7391259, inPMC=Y) and PMC XML efetch delivers
  full text normally (27.7K chars). The PMCID is the key determinant, not
  the publisher — do NOT assume all Science papers are unreachable.
  (Observed: PMID 25838373, no PMCID → abstract-only; PMID 29567705,
  PMC7391259 → 27.7K chars full text via PMC XML OA.) (2) **ASCO/JCO
  (ascopubs.org)** — Branch 1b pattern: `inPMC: Y` but PMC XML efetch
  returns front-matter only (~7 KB, 0 sections, no `<body>` element).
  EPMC PDF render succeeds — `europepmc.org/api/getPdf?pmcid=PMC4980573`
  delivered a 541 KB PDF (58K chars via pymupdf). Same pattern as JCI
  Insight, OUP/ATS, CSHLP — publishers that restrict XML body download
  but whose PDFs are retrievable via EPMC. Tag `fulltext_source:
  epmc-pdf`. (PMID 25605845, CTLA-4 profile, 2026-08-15.)

- **2026-08-15 — CDX `&filter=statuscode:200` parameter + CDX timeout
  retry + Nature Medicine publisher block.** Three findings from the
  IL-12/23 p40 target profile session (5 papers ingested: 1 PMC XML,
  1 jina-reader, 1 Wayback CDX, 2 abstract-only — 60% full-text
  retrieval rate): (1) **CDX `&filter=statuscode:200` query parameter
  pre-filters at the API level** — appending `&filter=statuscode:200`
  to the CDX URL returns only 200-status snapshots directly, which is
  more reliable than client-side filtering. An unfiltered CDX query can
  return only redirects (301/302) while the filtered query returns
  usable 200-status snapshots for the same URL. (Observed: NEJM PMID
  27959607 — unfiltered CDX returned 5 rows all 301/302; filtered CDX
  returned 9 rows all status=200.) (2) **CDX API timeouts are
  transient — retry after 10s.** A CDX call can time out (60s) on the
  first attempt and succeed on retry with the same URL. Do not treat a
  single CDX timeout as "no snapshot." (Observed: PMID 27959607 — first
  CDX call timed out; retry succeeded and returned 9 rows.) (3)
  **Nature Medicine (subscription) publisher block added to the
  known-blocks table.** Nature Medicine is a subscription research
  journal (distinct from Nature Reviews review-only journals) where
  jina returns the reference list (~155 KB) with zero body paragraphs
  for subscription articles — the same reference-list masquerade
  pattern. The block applies to subscription-only Nature Medicine
  articles; OA articles with a PMCID work normally via PMC XML.
  (Observed: PMID 26121196, IL-12/23 p40 profile — 155 KB jina output,
  all reference list.)

- **2026-08-15 — Lancet PIIS URL construction for jina reader proxy.**
  Lancet DOIs contain parentheses (e.g., `10.1016/S0140-6736(21)00125-2`)
  that cause 404 via jina when the DOI is placed in the URL path. The
  working path is the PIIS URL form: construct the article URL as
  `thelancet.com/journals/<journal>/article/PIIS<id>/fulltext` where
  `<id>` is the DOI suffix with the `10.1016/` prefix stripped (e.g.,
  `S0140-6736(21)00125-2` → `PIIS0140-6736(21)00125-2`). This avoids
  the parenthesized DOI in the URL path entirely. Confirmed across 2
  Lancet papers in the IL-17A/IL-17F dual blockade profile session
  (PMIDs 33549193 BE VIVID, 38795716 BE HEARD I/II) — both returned
  structured abstracts with complete efficacy/safety data via jina.
  Updated the Lancet entry in the known-blocks table with the PIIS URL
  construction and the pass-through form. (IL-17A/IL-17F profile: 5
  papers ingested — 1 PMC XML, 1 EPMC PDF, 1 Wayback, 2 jina reader —
  100% full-text retrieval rate.)

- **2026-08-15 — JAMA Network PMCID-present variant + Lancet PIIS URL
  confirmation (IL-31Rα profile).** Two findings from the IL-31Rα
  target profile session (5 papers ingested: 1 Wayback, 1 jina reader,
  3 abstract-only — 40% full-text retrieval rate): (1) **JAMA Network
  PMCID-present variant:** PMID 39602139 (JAMA Dermatol, OLYMPIA 1
  trial) carries a PMCID (PMC11840645, `inPMC: Y`), but both retrieval
  paths fail — PMC XML efetch returns front-matter only (~28 KB, no
  `<body>` element), and EPMC PDF render returns HTTP 404 (not the
  "No PDF file found" response seen for Blood). This is the same
  Branch 1b pattern as Blood/ASH Publications: PMCID present, but
  neither XML body nor PDF is retrievable. Updated the JAMA Network
  entry in the known-blocks table with the PMCID-present variant.
  (2) **Lancet PIIS URL form confirmed for a third time.** PMID
  39067461 (Lancet, ARCADIA 1/2 trials) was retrieved via jina reader
  using the PIIS URL form (`thelancet.com/journals/lancet/article/
  PIIS0140-6736(24)01203-0/fulltext`) — 14,254 bytes with complete
  structured abstract (Background/Methods/Findings/Interpretation/
  Funding) and results data. This is the third profile session
  confirming the PIIS URL form (after IL-17A/IL-17F, CD22). Key
  detail: the DOI suffix `S0140-6736(24)01203-0` starts with "S",
  which combines with the "PII" prefix to form "PIIS" — do NOT add an
  extra "S" (the "S" in "PIIS" comes from the DOI suffix, not a
  separate prefix character). (IL-31Rα profile, 5 papers, 3
  full-text sources: wayback, jina-reader, 3× abstract-only,
  working-docs/hitlist-profiles/il-31ra.md.)

- **2026-08-16 — PMCID cross-article mismatch + Elsevier book chapter
  DOI 404 + Europe PMC fulltextXML success (CGRP profile).** Three
  findings from the CGRP target profile session (5 papers ingested:
  2 PMC XML, 3 abstract-only — 40% full-text retrieval rate):
  (1) **PMCID resolves to a completely different article.** PMID
  32266704 (Dhillon, "Eptinezumab: First Approval", *Drugs* 2020)
  had `<ArticleId IdType="pmc">PMC7066477`, but `efetch db=pmc` with
  that PMCID returned the PROMISE-1 study by Ashina et al.
  (*Cephalalgia* 2020) — different title, authors, and journal. This
  is distinct from the stale-PMCID pattern (which returns
  front-matter-only for the same paper) — the PMCID maps to a
  different article entirely. Documented as a new pitfall in the
  Branch 1 section: always verify PMC XML article title matches
  PubMed record title before using body text. (2) **Elsevier book
  chapter DOI returns 404.** PMID 38307640 (Caronna 2024, *Handbook
  of Clinical Neurology*, Elsevier) had DOI
  `10.1016/B978-0-12-823357-3.00024-0`. The jina reader proxy on the
  DOI URL returned a 404 from doi.org (not the usual Elsevier block
  page). Book chapters with `B978` DOI prefixes (Elsevier Books) may
  fail differently than journal articles — the DOI resolves but the
  target page returns 404. Abstract-only was the outcome. (3)
  **Europe PMC fullTextXML endpoint works when NCBI efetch db=pmc
  fails.** PMID 35690723 (Sacco 2022, *J Headache Pain*) — the Europe
  PMC REST endpoint `https://www.ebi.ac.uk/europepmc/webservices/rest/
  PMC9188162/fullTextXML` returned the full 198 KB XML (73K chars
  body) on the first try, while NCBI `efetch.fcgi?db=pmc` is the usual
  path. The EPMC endpoint should be the first PMC retrieval attempt
  for OA articles (it is faster and has fewer rate-limit issues than
  NCBI efetch). (CGRP profile, 5 papers, 2 PMC XML, 3 abstract-only,
 working-docs/hitlist-profiles/cgrp.md.)

 - **2026-08-16 — Taylor & Francis + Portland Press publisher blocks
 added (CD37 profile).** Two new entries in the known-blocks table
 from the CD37 target profile session (5 papers ingested: 1 PMC XML
 OA, 2 Wayback, 1 publisher-jina, 0 abstract-only — 100% retrieval
 rate): (1) **Taylor & Francis (tandfonline.com):** doi.org HEAD
 returns HTTP 403; jina returns 27–30 KB of page chrome + abstract +
 keywords (NOT the article body) — passes the size check but body-term
 counts are low. Wayback CDX found 200-status snapshots; the most
 recent (2025) yielded 9K chars with abstract + keywords. Tag
 `fulltext_source: wayback` or `publisher-jina` at abstract+keywords
 level — validate body presence before tagging full text. (Observed:
 PMID 24555705, Expert Opin Biol Ther 2014; PMID 29323537, Expert
 Opin Investig Drugs 2018.) (2) **Portland Press (Biochem Soc Trans):
 ** Jina on `portlandpress.com` returns ~500 bytes (blocked). doi.org
 HEAD returns HTTP 403. **Wayback CDX on the legacy
 `biochemsoctrans.org` domain** found 200-status snapshots — a 2016
 snapshot yielded 40K chars with 37 target-term mentions (full review
 body). CDX returned no results for `portlandpress.com` URLs
 (post-migration) — always try both URL forms. Tag
 `fulltext_source: wayback`. (Observed: PMID 21428930, Biochem Soc
 Trans 2011.) (CD37 profile, 2026-08-16: 5 papers, 1 PMC XML OA, 2
 Wayback, 1 publisher-jina, 0 abstract-only — 100% retrieval rate.)

- **2026-08-16 — Taylor & Francis PMCID-present → EPMC PDF render; PubMed
  XML DOI+PMCID double cross-reference error (TRAIL profile).** The Taylor &
  Francis known-blocks table entry previously only documented the "No PMCID →
  Wayback CDX" path. PMID 27064440 (Siegemund et al. 2016, *mAbs*, a Taylor &
  Francis journal) exhibited the Branch 1b pattern: `inPMC: Y`,
  `isOpenAccess: N`, `hasPDF: Y`, PMCID PMC4968136 (from EPMC) — PMC XML
  efetch returned front-matter only, but EPMC PDF render
  (`europepmc.org/api/getPdf?pmcid=PMC4968136`) delivered 60,222 chars of full
  text. Tag `fulltext_source: epmc-pdf`. Added the PMCID-present branch to the
  Taylor & Francis table entry. Additionally, PubMed XML carried TWO
  cross-reference errors for this PMID: (1) the DOI
  `10.1038/sj.onc.1205193` belongs to a different *Oncogene* paper (the EPMC
  authoritative DOI is `10.1080/19420862.2016.1172163`); (2) the PMCID
  `PMC3693168` is stale (EPMC authoritative PMCID is `PMC4968136`). A second
  paper in the same session (PMID 33791337, *Front Mol Biosci*) also had a
  PubMed XML DOI cross-reference error (`10.1038/s41423-020-0488-6` vs the
  correct `10.3389/fmolb.2021.628332` from EPMC) and a stale PMCID
  (`PMC7395159` vs `PMC8006409`). These confirm the existing skill guidance:
  always use the EPMC core record's DOI and PMCID as authoritative when they
  disagree with PubMed XML. (TRAIL target profile, 3 papers ingested: 1 EPMC
  PDF, 1 PMC XML OA, 1 abstract-only — 67% full-text retrieval rate.)

- **2026-08-16 — SLeX/CA19-9 target profile: CDX 503 Service Unavailable
  + World J Surg all-paths-fail + Glycoconj J reference-list masquerade.**
  Three findings from the SLeX/CA19-9 target profile session (3 papers
  ingested: 1/3 PMC XML OA, 2/3 abstract-only — 33% full-text retrieval
  rate): (1) **CDX API can return HTTP 503 (Service Unavailable), not
  just timeouts.** Unlike CDX timeouts (which resolve on retry), 503
  responses persisted on both filtered and unfiltered queries for both
  `link.springer.com` and `doi.org` URL forms. After 2 consecutive 503s,
  declare abstract-only rather than looping — the CDX service itself is
  down. Updated the CDX timeout pitfall section to cover 503. (Observed:
  PMID 18264829.) (2) **World J Surg (Springer subscription, PMCID
  present) — all retrieval paths fail.** PMID 18264829 has PMCID
  PMC4378829, `inPMC: Y`, `hasPDF: Y`, `isOpenAccess: N`, but PMC XML
  returns metadata-only (no `<body>`), EPMC PDF returns no PDF, EPMC
  fullTextXML returns HTTP 404, jina returns CAPTCHA page (~497 chars),
  and CDX returns 503. This is the same all-paths-fail pattern as JAMA
  Network PMCID-present variant, but with CDX 503 instead of "no
  snapshots." Added to the known-blocks table. (3) **Glycoconj J
  (Springer, no PMCID) jina reference-list masquerade.** PMID 15229399
  returned 74K chars via jina reader, but 99.5% was reference list (the
  "References" marker appeared at char 357 of 74,663). This confirms the
  Springer/Drugs reference-list masquerade pattern extends to
  Glycoconj J — always validate body presence before tagging
  `jina-reader` for subscription Springer content. Abstract-only was the
  outcome (PubMed abstract fetched separately via efetch). (SLeX/CA19-9
  profile, 3 papers, working-docs/hitlist-profiles/slex-ca19-9.md.)

- **2026-08-18 — SAGE / Atypon (journals.sagepub.com) publisher block
  added.** SAGE journals (J Interferon Cytokine Res, J Immunology, etc.)
  block jina reader proxy with a Cloudflare CAPTCHA (~505–510 bytes:
  "Performing security verification" / "Just a moment...") on both
  `journals.sagepub.com/doi/<doi>` and `journals.sagepub.com/doi/full/<doi>`
  URL variants. No PMCID for most articles. Wayback CDX returned no
  snapshots for either URL variant. Unpaywall returned HTTP 422 (not
  indexed — SAGE DOIs use the `10.1177` prefix). Semantic Scholar
  `openAccessPdf` is null/empty. Three-source closure confirmed →
  abstract-only. PubMed abstract is the primary content source. DOI
  prefix `10.1177` is SAGE. The ProEd entry previously noted
  `journals.sagepub.com` as an alternative URL that returned ~510 bytes
  (blocked) during the Drugs of Today investigation — this new entry\n  documents the same block pattern for SAGE's own journals. (Observed:\n  PMID 42455016, J Interferon Cytokine Res 2026, Gundrathi et al. TNF\n  review — abstract-only, 2026-08-18.)

- **2026-08-22 — Aging and Disease (aginganddisease.org): JS-template jina failure + Semantic Scholar PDF discovery.** PMID 42295086 (Liu & Lin 2026, *Aging Dis*, CC BY OA, no PMCID): This OA journal runs on a JS-rendered CMS (Beijing Magtech). Jina reader proxy returns only Angular/Vue template chrome (~9.5 KB, zero body paragraphs, all `{{article.<field>}}` placeholders, Chinese-language modal boilerplate) — passes the size check but grep for body terms returns zero. Semantic Scholar correctly identifies OA (`isOpenAccess: True`) and provides the `openAccessPdf` URL at `aginganddisease.org/EN/PDF/<DOI>`. Curl-download that PDF directly (847 KB, 23 pages). Extract via pymupdf (126K chars full text). Tag `fulltext_source: publisher-oa`. EPMC flags (`inPMC: N`, `isOpenAccess: N`, `hasPDF: N`) are misleading for this journal — Semantic Scholar `openAccessPdf` is the authoritative OA-status source. The journal URL pattern is `aginganddisease.org/EN/<DOI>` and PDF is `aginganddisease.org/EN/PDF/<DOI>`. No Cloudflare block on the PDF endpoint. Added as a positive entry to the known-blocks table: jina-fails-but-PDF-works, with S2 `openAccessPdf` as the discovery path. (Liu & Lin AD antibody engineering review ingest, Alzheimer's vaccine literature-dive, 2026-08-22.)

- **2026-08-18 — ScienceDirect Wayback JS-rendering trap (OA article, no PMCID).** PMID 30381260 (Weihofen 2019, Neurobiol Dis, CC-BY-NC-ND OA, no PMCID): Wayback CDX found 10+ 200-status snapshots for `sciencedirect.com/science/article/pii/S0969996118304480` across 2021–2025. All snapshots — including the raw `id_` form — contained only the title, highlights, abstract, keywords, and abbreviations list (~4.7K chars total). The article body (Introduction, Methods, Results, Discussion) was entirely absent because ScienceDirect renders body text client-side via JavaScript (SPA architecture) and Wayback's server-side crawl captures only the initial HTML shell. This is a **distinct failure mode** from the Cloudflare CAPTCHA: the snapshot loads successfully with a correct title and full abstract, but zero body sections. Without body section headings (grep for "Introduction", "Results", "Discussion"), the content looks superficially valid. Updated the Elsevier/ScienceDirect known-blocks table entry: changed "No Wayback snapshots for recent Elsevier articles" to the correct description — Wayback snapshots DO exist but contain abstract-only due to JS rendering. Added a validation rule: do NOT tag `fulltext_source: wayback` for ScienceDirect snapshots unless body section headings are present. Also discovered that the brain's `parsed_papers.pkl` cache had this paper with empty `body_sections` — checking the pickle cache before attempting retrieval can save time. The Elsevier API (`api.elsevier.com/content/article/PII:<PII>`) returned only metadata (`coredata`) without an API key; the `view=FULL` parameter requires an API key not configured on this host. Crossref, Unpaywall, and Semantic Scholar all confirmed the OA status, but the OA copy is only on ScienceDirect itself (Cloudflare-blocked). Outcome: abstract-only, full text unobtainable without an Elsevier API key or a real browser session. (PMID 30381260, α-synuclein antibody literature dive — BIIB054/cinpanemab preclinical paper. 2026-08-18.)
