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
  `--publisher-url`, `--skip-publisher`, `--figures`. Prefer the script
  over hand-walking the tree; hand-walk only when its sources all miss
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
- **`check_authors.py`** — the definitive Phase 8 pre-write existence
  check (added 2026-09-02). Greps miss ledger entries two ways —
  name-order variants, and the 0-indent `- name:` entry-start shape that
  indent-anchored greps skip — so this script `yaml.safe_load`s the whole
  ledger and compares full-name token sets order-independently. Per
  author: EXISTING (slug, person-page presence, affiliations, citations)
  or NEW, plus same-surname entries as conflation-review candidates.
  `--ledger <vault>/people/_ledger.yaml`, names as args or stdin.
- **`ledger-append.py`** — the Phase 8 Branch-3 single-writer append
  (read → dedup-check → candidate build + YAML validation → atomic
  publish → verify, all under one deterministic `fcntl.flock` on a hash
  of the resolved ledger path in the temp dir — safe among parallel
  workers; POSIX only). Publication writes the validated candidate to a
  temp sibling file, fsyncs, preserves the ledger mode, then
  `os.replace`s it in — the live ledger is never truncated before the
  candidate validates, and a second same-slug invocation rereads the
  ledger under the lock and aborts. Copy to `/tmp/`, edit the block
  list, run with a ≥3.10 interpreter. The template enforces plain-text
  append (never `yaml.safe_dump`).
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
  `python3 -c "...parse the file..."`. It also blocks multi-line
  `python3 -c` AND heredocs (`python3 - <<'EOF'` is rejected with a
  false "uses '&' backgrounding" error even when the body contains no
  `&`). For any "atomic python3 heredoc" procedure below
  (`people/_ledger.yaml` appends especially): `write_file` the script
  to `/tmp/<name>.py`, then run `python3 /tmp/<name>.py`.
- **tirith also hardline-blocks nested `$(...)` command substitution** —
  `sed -n "$(grep -n 'X' f | cut -d: -f1),+8p" f` is rejected as a
  malformed payload and auto-saved to `cache/blocked-scripts/`.
  Recovery: run the grep first, then sed on the resolved line number —
  or replace the pipeline with `search_files`/`read_file`. Do not
  retry the identical command; repeated same-tool failures also trip
  the tool-loop warning.
- **Interpreter version** — the skill's `scripts/` use `str | None`
  union syntax (needs Python ≥3.10). Hosts whose system `python3` is
  older (e.g. macOS 3.9) raise `TypeError` inside the helpers — run
  every script with an explicit ≥3.10 interpreter
  (e.g. `~/.local/bin/python3.11`).
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
  Plain curl of `arxiv.org/abs/<id>` and `arxiv.org/html/<id>` DOES work —
  the block is specific to the API endpoint.
- **jina domain-level 403 ≠ source outage** (observed 2026-09-05):
  r.jina.ai can refuse `arxiv.org` anonymously —
  `{"code":403,"name":"AbuseAlleviationError","message":"Anonymous
  access to domain arxiv.org blocked until <timestamp> ... DDoS attack
  suspected"}`. That is a jina-side rate limit with an explicit expiry
  timestamp in the message; direct curl of the same arxiv.org pages
  still works. Route around jina (paperclip mirror, direct arXiv HTML)
  rather than treating the 403 as closure evidence for the source.
- **Never fetch JSON APIs through r.jina.ai** — jina wraps any page,
  raw JSON included, in its `Title:/URL Source:/Markdown Content:`
  preamble, and `json.load` then fails on line 1 (observed on a DBLP
  `publ/api` call, 2026-09-05). API JSON goes through plain curl.
- **DBLP is a cheap, curl-able published-twin check from this host**
  (`dblp.org/search/publ/api?q=<title-words>&format=json`): a
  conference record (`conf/nips/...`, `conf/iclr/...`) alongside the
  CoRR record (`journals/corr/...`) confirms a published twin;
  CoRR-only means preprint. Useful fallback when OpenAlex holds only
  the arXiv record (per published-twin detection, Phase 1). DBLP also
  returns plain-HTML 503s ("No server is available to handle this
  request", ~107 bytes) under load — a service error, not closure
  evidence for or against a twin. For preprints days old, all three
  oracles lag: no Crossref deposit, no S2 DOI record, OpenAlex
  arXiv-only — a 200-result OpenAlex check plus absence of any task
  venue is enough to settle `status: preprint`; re-check the twin
  only at enrichment time.
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

**Wrong venue in the task.** A brief can name the wrong venue while
its identifiers match. For example, verify a claimed Molecular Cell venue
against the PubMed journal record rather than trusting the brief. Compare the
brief's venue against PubMed `<Journal/Title>` /
`<ISOAbbreviation>` during the gate; PubMed is authoritative for the
page's `venue:`, and the correction is logged in the Ingest log.
Title + all identifiers matching with only a venue mismatch is NOT a
wrong-paper signal — do not re-resolve identity over it.

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
- **Author list ladder:** (0) **plain curl of the abs page** —
  `curl -sL "https://arxiv.org/abs/<id>"` returns the full
  `<meta name="citation_author" content="Family, Given">` set plus
  `citation_title`, `citation_date`, `citation_abstract`,
  `citation_pdf_url` (cheapest source when the page is reachable; note
  the `Family, Given` format for slug derivation); (1)
  `paperclip cat /papers/arx_<id>/meta.json`
  — split on " and "; (2) jina abs-page proxy
  (`r.jina.ai/https://arxiv.org/abs/<id>`) when the API is blocked;
  (3) Crossref DOI resolver (`doi.org/<10.48550/arXiv.<id>>`) for
  structured author metadata with ORCIDs.
- **Days-old preprints have no Crossref deposit.**
  `api.crossref.org/works/10.48550/arXiv.<id>` returns "Resource not
  found." for a preprint deposited days ago — this is normal, not a
  retrieval failure. Set `orcid: null` for all authors (never
  fabricate), log the missing deposit in the Ingest log, and let a
  later enrichment pass re-check ORCIDs.
- **Version history:** search indexes carry only the latest version. If
  a title search misses, open `arxiv.org/abs/<id>v1` and compare. Always
  fetch full text from the VERSIONED URL (`arxiv.org/html/<id>v1`).
  Withdrawals: still ingest v1 (withdrawal ≠ retraction), note the
  withdrawal in a prominent body warning, check the superseding paper.
- **Venue assignment:** task-specified venue → `status: published`; no
  task venue → `status: preprint`, `venue: "arXiv (<id>)"`. Never infer
  acceptance from the arXiv listing alone.
- **Published-twin detection (observed 2026-09-02, Lightman ingest):**
  "no task venue" does not mean "no twin" — check for a conference
  version before settling on preprint. OpenAlex
  (`api.openalex.org/works/doi:10.48550/arXiv.<id>`) often holds ONLY
  the arXiv record even for published papers; the confirming pair is
  DBLP (`dblp.org/search/publ/api?q=<title-words>&format=json` — look
  for a conference record like `conf/iclr/...` distinct from the CoRR
  record) plus Semantic Scholar
  (`.../paper/DOI:<doi>?fields=venue,publicationVenue`, which names the
  conference). DBLP+S2 are also the working fallback when OpenAlex
  rate-limits on its daily API budget. When the conference version has
  no Crossref DOI (ICLR/OpenReview venues): keep the arXiv DOI as
  canonical `doi:`, set `status: published`, `venue: "<CONF> <year>
  (arXiv:<id>)"`, and use the CONFERENCE year in the slug (2023 v1 →
  `lightman-2024-...`). Vault pages citing the paper by its arXiv year
  ("Lightman et al. 2023") stay untouched — note the mismatch in the
  Ingest log for the orchestrator.

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

**Manuscript PDF and supplements are independent retrieval obligations.**
Getting readable text (any branch below) does not discharge them: after
text is settled, still attempt the original manuscript PDF and any
supplements separately (Branch 2c browser route below, EPMC PDF,
repository copies). Text acquired from one route never implies the PDF
was retrieved, and vice versa — record which obligations remain open.
Keep structured APIs (PubMed XML, EPMC, Crossref, bioRxiv API) as the
identity source in every route: browser retrieval is for source bytes
and never a replacement for identity resolution.

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

**Day-old papers: EPMC lags PubMed.** A paper published within the last
day or two can carry a complete PubMed XML record and Crossref deposit
while EPMC returns an EMPTY `resultList` (observed 2026-09-01: EMM
review published 2026-08-31, PubMed and Crossref complete, EPMC zero
hits). An empty EPMC result is not closure evidence — never read it as
`inPMC: N` for the Branch 3 abstract-only gate, which requires an
actual EPMC record. Proceed with PubMed XML + publisher retrieval;
re-check EPMC later for ORCIDs and PMCID.

**PMCID overrides stale EPMC flags.** EPMC flags are not always fresh.
A PMCID in the PubMed XML (`<ArticleId IdType="pmc">`) is the stronger
OA signal — **always try `efetch db=pmc` (Branch 1) when PubMed XML
carries a PMCID, even if EPMC reports all-N.** Only declare abstract-only
when `efetch db=pmc` itself returns front-matter only or an error. The
reverse also holds: if the PubMed XML PMCID returns front-matter only,
check the EPMC `pmcid` field for a different PMCID and retry.

**Unpaywall overrides EPMC flags for publisher-hosted OA (observed
2026-09-05, Park et al., Nature flagship).** EPMC can report all-N
(`isOpenAccess: N, inPMC: N`) for a hybrid-OA article whose full text
lives on the publisher site — Unpaywall's `is_oa: true` /
`oa_status: hybrid` with `host_type: publisher` is the stronger
signal. Read the two together before routing: EPMC all-N + Unpaywall
OA-at-publisher → skip the PMC branches, go to the publisher (for
nature.com, direct curl works — see
`references/nature-metadata-extraction.md`). The Branch 3 closure
gate already requires Unpaywall `is_oa: false`, which is what prevents
a wrong abstract-only call in this shape.

**Branch 1 — PMC open access.** With a PMCID and `isOpenAccess: Y`:

```bash
curl -sL "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=<PMCID>&rettype=xml" -o /tmp/<pmid>_paper.xml
python3 scripts/pmc_xml_body_parser.py /tmp/<pmid>_paper.xml --full
```

Structured XML (`<sec>`/`<p>`/`<xref>`), complete reference list — the
preferred path for OA papers. Always prefix `/tmp` artifacts with the
PMID (not bare `/tmp/paper.xml`) — parallel siblings share `/tmp`.

**Cell Press XML quirks (observed 2026-09-04).** Figure legends sit
inline as text runs after the paragraph they illustrate
(`Figure 1High-affinity...` — digit immediately followed by a capital,
no space), NOT in a separate caption block; recover with
`re.finditer(r'Figure\s(\d)(?=[A-Z])', text)` (the capital distinguishes
a legend from an in-text `Figure 1A` citation), and re-wrap long
paragraphs before grepping for truncated legend tails. PDB IDs in the
STAR★Methods key-resources table run into the next sentence
(`PDB: 8F9ECrystal structure of...`) — extract with a fixed-length
pattern `PDB:\s*([0-9][A-Za-z0-9]{3})`, never `([0-9A-Z]+)`.

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

**Mirror-staleness triage.** The mirror can hold a STALE or PARTIAL copy while
`meta.json` looks fine. Three failure shapes, all with the same recovery:
(1) `content.lines` holds the abstract only (1–8 KB) — check byte size
before distilling, not just that the file exists; (2) the mirror holds an
OLD VERSION's body (v1/v2 text) while `meta.json` carries the current
abstract — cross-check the body's date/version markers against the abs
page; (3) `meta.json` has an empty `authors` field or a `pub_date` that
disagrees with the abs page (a later index-ingest date, not publication).
Recovery in all three: direct versioned curl of `arxiv.org/html/<id>v<N>`
(plain curl works even when jina is domain-blocked) → tag-strip →
`fulltext_source: arxiv-html`, with the abs page as the authority for
authorship and dates. When the mirror IS current, it remains the preferred
source — verify by checking that section headings and reference lists are
present, not just byte count.

**Branch 2 — Journal HTML via browser.** When no PMC copy exists but the
journal page renders: navigate, extract section-by-section via
`browser_exec` `js(...)` DOM reads.
Nature research-article pages render reliably
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

**Branch 2c — local CDP browser for the original manuscript PDF and
supplements.** When the ladder misses a publisher PDF (403/WAF, viewer
renders but won't download, or the PDF URL serves HTML to plain HTTP):
attach `browser_exec` to the loopback CDP browser and follow the exact
recipe in `web/blocked-page-recovery` Route 5 (launch command,
`Browser.setDownloadBehavior` + anchor-click for downloads, cookie-
bridged curl fallback, and the acceptance bar: `%PDF` magic bytes +
pymupdf parse + paper-specific strings — a page-print or challenge
HTML saved as `.pdf` is NEVER the manuscript). For per-publisher
escalation order (cookie-bridged curl → in-page `fetch()` → bounded
challenge handling), see
`research/publisher-fulltext-workarounds/references/cdp-publisher-route-matrix.md`.
Attempt the manuscript PDF and each supplement as separate
obligations; supplements are often non-PDF (XLSX/TIFF/CSV) — accept
by magic bytes, not extension. R2 archiving is optional follow-up,
not part of retrieval.

**arXiv full text.** Primary:
`fetch_fulltext.py --doi 10.48550/arXiv.<id> --publisher-url https://arxiv.org/html/<id>`.
On `provenance: none`, go straight to the paperclip mirror (branch 1e).
If paperclip also lacks it, direct curl of `arxiv.org/html/<id>v<N>`
(always versioned) + regex tag-stripping is the last resort
(`fulltext_source: arxiv-html`). Numeric table contents can be silently
dropped from arXiv HTML — scan for "Table N:" captions with no numbers;
recover via browser.

**Paperclip mirror staleness on arXiv versions (observed 2026-09-05,
AIRA₂ ingest).** The mirror can hold only the abstract for a paper
whose `content.lines` should carry full text — `meta.json` showed an
empty `authors` field and a `pub_date` matching a later version (v2)
than the versioned body it lacked. Diagnosis: `wc -c` the
`cat --full` output; ~1.4 KB (abstract-length) means the mirror
ingested the abstract page, not the paper. Recovery: direct curl of
the (unversioned) `arxiv.org/html/<id>` URL — plain curl works even
when jina is domain-blocked (see Environment notes). Also
cross-check the mirror's `meta.json` author list against the abs-page
`citation_author` ladder when both exist; on mismatch the abs page is
authoritative for authorship.

**Branch 3 — Abstract only (genuinely unreachable).** Distill from the
structured abstract only after **three-source closure**: Europe PMC
(`inPMC: N`, `isOpenAccess: N`), Unpaywall (`is_oa: false`, `oa_status:
closed`), Semantic Scholar (`openAccessPdf: null` or `status: CLOSED`).
S2 `status: GREEN` means an OA PDF URL exists — attempt the download
before declaring closure. **S2 `status: BRONZE` likewise means attempt**
(observed 2026-09-05, Wang 2021 Immunity: Unpaywall `closed` + EPMC
all-N, yet S2 BRONZE pointed at a free-at-publisher cell.com copy that
retrieved in full — 89k chars). The oracles are independent, not
redundant: `BRONZE` is publisher-discretionary free-to-read that
Unpaywall often lags on. Contradiction between any two oracles means
ATTEMPT the retrieval; only agreement (all sources closed, S2 actually
saying CLOSED or null) licenses the abstract-only call. See
`references/publisher-blocks.md` § "Unpaywall `closed` vs S2 `BRONZE`".
Record the closure in the Ingest log. Set `needs-enrichment: true` — this
is the ONLY case where that flag is appropriate.

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

**Nature flagship caveat (observed 2026-09-05, Park et al. ingest):**
Nature research articles use THEMATIC section headings ("Existence of
T_FH cells in the skull BM"), not Introduction/Results/Discussion — the
heading grep above returns ~0 hits on a COMPLETE body and is
uninformative there. For nature.com HTML, verify by extracting the
actual `<h2>` set (expect Abstract / Main / themed Results sections /
Discussion / Methods / Data availability / References) and counting `<p>`
paragraphs inside `div.c-article-body` (~100+ paragraphs for a full
Article). See `references/nature-metadata-extraction.md` for the
confirmed OA-flagship recipe.

**Figure images (optional).** `fetch_fulltext.py --figures` scrapes
figure images from the PMC article page. Figures are distillation-time
working material (`/tmp`, ephemeral); `vision_analyze` reads them into
Findings.

### 5. Distillation and page write

Write `papers/<slug>.md` per the paper-kind schema. Body anatomy:
Abstract / Context / Approach / Findings (specific results tied to
figures) / Limitations / Analysis, plus `## Ingest log` and `## Citation`.

**Schema-exemplar read.**
Before writing, read one recent sibling paper page in the target vault —
ideally from the same dive — and match its conventions instead of
inventing them: body section emphasis, Ingest-log phrasing, `tags:`
style, `importance:` calibration, how ORCIDs and slug-alignment
findings are recorded. A sibling page is the cheapest schema reference
there is, and the frontmatter linter does not catch stylistic
divergence.

**Dive working-doc cross-reference.** When dispatched as part of a
literature dive, grep the dive's working doc (typically
`working-docs/<dive>-*.md`) for the paper's PMID or DOI before writing.
A hit names the row or role this page fills (an mAb-list row for an
antibody paper, a gap-map entry, a Tier-1 citation); state that role in
the page's Context so the parent can audit the fill, and carry over any
open question the working doc attaches to the paper. A miss is fine —
not every dive paper is pre-listed.

**Verify the task brief against the full text before writing Findings.**
A parent task's pre-filled "key findings" are a convenience, not a
primary source — they can conflate closely related molecules or
misattribute structural features. Grep the fetched full text for each
key claim. If the full text contradicts the brief, trust the full text;
record the discrepancy in a prominent body note. Do NOT silently
overwrite the brief's claims — flag and let your human decide.

**Terminology-provenance check.** A brief can use vocabulary the paper
never uses while carrying correct identifiers. Compare its framing against
the actual full text; imported terminology can conflate related papers. When a brief's framing term
is absent from the full text (`grep -ci <term>` → 0), classify it
before distilling:
1. **Real in sibling papers** — EPMC full-text search
   (`"exact phrase" AND <domain keyword>`); the brief is conflating two
   papers in the dive. Name the likely true source in the Ingest log.
2. **Same concept, paper's own synonym** — distill under the paper's
   vocabulary, note the synonym mapping.
3. **Not real anywhere in the domain** — treat as a bad seed term,
   flag for the parent's working-doc correction.
Distill what the paper claims; never write the brief's term into
Findings as the paper's claim. See
`../paper-ingest-vault-modes/references/brief-vs-fulltext-verification.md`
for the worked case.

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

**Stub fills do not reset failure counters (observed 2026-09-06).** A
stub created by `literature-sweep` carries only `needs-ingest`,
`cited_by`, `stub_source`, `tags` — no `ingest_attempts`, no
`last_ingest_attempt`. When the fill succeeds on the first try, carry
the queue/provenance fields the *schema* defines (`ingest_attempts: 0`,
`last_ingest_attempt` if other siblings in the vault set it) rather
than only the stub's original fields, so the page's frontmatter matches
its filled siblings and the counter semantics stay uniform. The linter
does not catch this — a filled page silently missing `ingest_attempts`
passes every graph invariant and the schema lint.

**Ingest log on success-with-deviation.** A fill that succeeded via a
non-standard path is not "clean": append a timestamped log entry
(identity fallback used, full text not retrieved, `needs-enrichment`
set and why). These are provenance notes for the next enrichment run.

### 7. Bibliography walk

Walk the ingested paper's reference list and create **stubs** for
load-bearing citations. The anchor test: "the paper would lose its
argument without this reference" — a method it depends on, a dataset it
analyzes, a framework it extends. Not context citations.
Stubs carry `needs-ingest: false` and accumulate `cited_by`; when a stub crosses 5+
independent citing sources, `ingest-pending-papers` fills it. This
threshold gate is what prevents the exploding paper tree — do not
inline-ingest walk results.

**Deferred-stubs option for direct ingests (observed 2026-09-05).**
When a human-handed single paper opens a thread the vault may not
pursue (no project page, no dive working-doc), minting anchor stubs
creates single-citation pages that wait indefinitely. The lighter
alternative: record the anchor references with DOIs and one-line
descriptions in a `### Deferred stubs` subsection of the page's
Ingest log. The information is preserved, the next citing page can
mint the stub from the log entry, and the page count stays honest.
Use only for direct ingests; dive dispatches still mint stubs (the
parent's gap-map audits them by slug).

**The deferred-stubs → dive round trip (observed 2026-09-05).** A
deferred-stubs list is not just an archive — it is a validated
seed corpus for a later dive. When your human asks for a dive on the
thread the paper opened, the log's DOI+description entries ARE the
anchor set: resolve each DOI to PMID/PMCID via PubMed XML (title
match gates the resolution), run the standard dedup gate and
`validate_identifiers.py` over the set, then hand the validated list
to `literature-dive`'s seed-corpus entry (Phase 1 "anchor sets").
Prefer identifiers copied from the paper's `citation_reference` metadata,
not memory. Still run the validator: transcription can introduce an error,
and an incorrect identifier at this handoff would seed the wrong paper.

**Subagent summaries are not durable storage for wiring data.**
A delegated ingest's return summary is context-trimmed in transit
("[SUMMARY TRUNCATED]"), and a page's Ingest log can record a COUNT
("ORCIDs captured: 22 of 25") without the VALUES. When the
orchestrator (or a later pass) needs author names, slugs, ORCIDs, or
affiliations for ledger wiring, re-fetch them from the durable
sources — the paper page's frontmatter `authors:` slugs plus the
EPMC core record's `authorList` (authoritative and re-fetchable) —
rather than mining the summary. Record in the page's Ingest log the
fact that data was captured, but treat the external record as the
copy of record, never the summary text.

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
**Name-order pitfall (observed 2026-08-31):** a ledger `name:` can be
stored in either order — `"Gilchrist Cameron L M"` (surname-first) or
`"Yi Zhou"` (given-first) — and one grep pattern catches only one
order. Run BOTH `grep -i "name:.*<Surname>"` AND
`grep -i "name: <GivenName> <Surname>"` (or grep the surname token
alone and eyeball the hits) before concluding an author is new; a
missed match produces a duplicate-slug append that Phase 10 rejects.
When the search is large (surname Zhou/Wang/Li with hundreds of
hits), a small python filter over `yaml.safe_load` output, keyed on
affiliation, is cheaper than eyeballing grep output.

**Ledger indentation-shape pitfall (observed 2026-09-02):** `name:`
lines come in two shapes — 2-space `  name: X` mid-entry and 0-indent
`- name: X` at entry start — and an indent-anchored grep
(`grep -E "^  name:"`) silently skips every 0-indent entry. Three
existing authors were wrongly declared "new" this way during the
Lightman ingest (their entries sat at 0-indent) before a full-ledger
scan caught them. Never anchor a surname grep to an indent level; run
`scripts/check_authors.py` for the definitive answer — a whole-ledger
`yaml.safe_load` comparing full-name token sets order-independently
which also surfaces same-surname conflation candidates in the same pass.

**Abbreviated-name blindspot in `check_authors.py` (observed 2026-09-05,
Park et al. ingest).** The NEW verdict compares full-name token sets —
but legacy ledger entries store abbreviated names (`Kipnis J`,
`Smirnov I`, `Jackson S. Turner`), so the paper's `Jonathan Kipnis`
fails the match and reports NEW for an EXISTING person. Three authors
were wrongly reported NEW this way in one ingest. The surname-review
candidates list is the designed rescue: READ it, and grep the ledger
for `Surname <initial>` forms (punctuation variants — `Jackson S.
Turner` vs `Jackson S Turner` — also break token matching) before
minting. Two confirmation signals when an abbreviated entry looks
like the same person: (a) exact ORCID match against the paper's
author ORCIDs; (b) shared citation lineage — the entry's `citations:`
includes related papers from the same lab. Do not trust the per-author NEW
verdict until the surname-review list has been eyeballed.

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
most failure-dense operation. The file's top level is a mapping with a
single `entries:` key — `yaml.safe_load` returns a dict, and the entry
list is `data['entries']`, NOT a bare top-level list (a custom append
script that iterates the load result directly raises `TypeError: string
indices must be integers`). The canonical procedure is one
single-writer script execution: under a deterministic `fcntl.flock` on
a hash of the resolved ledger path (temp dir), read → check for missing
slugs → build the full candidate text → validate it (`yaml.safe_load` +
duplicate-slug check + author-count check) → publish atomically via a
temp sibling file + `os.replace` → read-back verify, all in a single
run (see `scripts/ledger-append.py` for the ready-to-copy form — write
it to `/tmp/` and run it; heredocs are blocked, see Environment notes;
POSIX only — the flock requires `fcntl`). Parallel paper-ingest workers
are serialized by the lock: the second invocation for the same slug
rereads the new ledger and aborts on the dedup check without changing
it. Splitting append and verify across
tool calls leaves a window in which a sibling's full-ledger rewrite
silently drops your entries. Re-verify at Phase 10 and re-append
atomically if missing. Never append via `cat >>` heredoc. **The append
itself must be a plain-text append of pre-rendered blocks, never
`yaml.safe_dump` of the re-loaded file** — a `yaml.safe_dump` round-trip
re-flows every long line and re-orders keys, turning a 9-entry append
into a whole-file rewrite that can clobber siblings. If damage occurs,
preserve the current file and compare against a known-good version; recover
only the damaged entries after accounting for concurrent edits, per git-ops.
Never restore the shared ledger wholesale as an automatic recovery. When patching
an existing entry, anchor `old_string` on the entry's unique `slug:` line
plus a distinguishing field — generic anchors can silently match the
wrong entry.

**String-interpolation trap in appended blocks (observed twice
2026-08-31).** Every line in a pre-rendered block is plain text — an
unexpanded `slug: {slug}` (a Python f-string mistakenly written as a
plain string) silently appends 10 entries whose `slug:` YAML-parses as
a nested mapping, and the breakage surfaces only at the next
`safe_load`. Symptom when it slips through: `TypeError: unhashable
type: 'dict'` from the duplicate-slug check. Rule: after ANY ledger
mutation, `yaml.safe_load` must succeed AND
`isinstance(entry['slug'], str)` must hold for the tail entries before
declaring the append verified. Write blocks with explicit per-author
text, not a shared template string.

**Branch 2 (append citation to existing entry) mechanics.** Entry
blocks come in two shapes: `citations:` may be a 2-space
`  citations:` mid-entry key or a 0-indent `- citations:` entry-start
key (older entries). A matcher that handles only the 2-space form
reports `not found` on the other shape. Bound the entry FIRST: entries
begin at any 0-indent `- ` list line — key order inside entries is
arbitrary, and legacy entries can START with `- citations:` before
`name:`/`slug:` — so an entry block spans from its 0-indent start line
to the next 0-indent `- ` line or EOF. Never bound by walking back from
the slug line to `\n- name:` — that grabs the PREVIOUS entry when the
target begins `- citations:`; this can place citations under the wrong
author and make a later repair remove correct citations. With the
block correctly bounded, find the last `- papers/…` line WITHIN it and
insert the new citation after it (alphabetical is not enforced; append
order is fine).

**Match the entry's citation indent.** Legacy entries use 2-space
`  - papers/` lists; newer blocks use 4-space `    - papers/`. A 4-space
insert under a 2-space list still YAML-parses but the citation silently
drops out of the parsed list — the file loads, the count check fails,
nothing looks broken (observed 2026-09-05). Read the indent of the last
citation line in THAT entry and match it.

**Batch wiring: collect all edits, apply bottom-up once.** Gather every
(position, text) splice against the ORIGINAL raw string, sort descending
by position, apply in a single pass. Never recompute `find()` offsets
inside a mutation loop — stale offsets compound into a quadratic blowup
(observed 2026-09-05: a 4.8 MB ledger ballooned to 1.85 GB / 66.8M lines
before the process was killed).

**Verification** (all three, per paper): re-load and check `PAPER in
entry['citations']` for the target entry; check `PAPER` is absent from
every OTHER entry (a mis-anchored append shows up as a citation gained
by the wrong author); duplicate-slug and string-type checks on the tail
entries. Recovery follows the scoped, non-destructive git-ops procedure; a
validation failure is not permission to overwrite concurrent ledger changes.

**Same-name disambiguation convention (observed 2026-08-31).** When a
new author's natural slug (`zhou-yi`) is already taken by a DIFFERENT
person (the BioMap Yi Zhou, not the PolyU one), mint an
institution-suffixed slug (`zhou-yi-polyu`) for the NEW entry, keep the
incumbent untouched, use the suffixed slug in the page `authors:` list
AND the ledger, and flag the pair in the Ingest log as an
`entity-resolution` candidate. Suffix choice: short, stable,
institution-anchored (`-polyu`, `-biomap`), never a year. The
ORCID-bearing entry wins any future merge; until then both entries
carry their own citations.

### 9. Graph wiring and propagation

Link the page into the graph: search the vault for concept/project pages
matching the paper's topic and add typed edges per `graph-and-links.md`.
Use `patch` for appends to shared frontmatter lists (`links:`,
`cited_by:`), never whole-page `write_file`.

Then enqueue propagation — append to `docs/rem-cycle/inbox.yaml` (plain
list append under `items:`, dedup on `id`, NEVER rewrite the file):

```yaml
- consumed_by: []
  date: YYYY-MM-DD
  event: ingest            # or: stub-filled
  id: <YYYY-MM-DD>-<slug>
  page: papers/<slug>
```

Items sit at **column 0** with 2-space fields, keys in alphabetical
order (`consumed_by, date, event, id, page`) — the real file uses this
shape, and a 2-space-indented `  - id:` breaks `yaml.safe_load` against
it. Verify with `yaml.safe_load` after the append.

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
unfinished write, not debt to fix later. Gate the commit on the
linter's exit code and its read output: piping the lint through `tail`
masks its exit code, and sequencing it before `git commit` with `;`
commits straight through a red lint (observed 2026-09-05: seven
ledger citation-shape errors landed in a batch commit and needed a
follow-up fix commit).

On this host the platform repo is `~/git/scuderia` — run
`python3 ~/git/scuderia/core/tools/lint-frontmatter.py --instance
<brain> --paths papers/<slug>.md people/_ledger.yaml` (same checkout
the skill scripts resolve through, see Tooling). A second copy lives at
`<vault>/.github/scripts/lint-frontmatter.py`.

**Git closeout.** Follow `skills/git-ops/SKILL.md`. Standalone ingestion
closes the verified paper, required author/graph wiring, and propagation packet
as one coherent unit. A delegated/page-only fill returns its paths and remaining
wiring obligations; the parent owns the completed commit and push. A partial
child result is not a complete standalone ingest. Never amend or force-push
existing history to improve a commit message.

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
