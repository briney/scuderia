---
name: retroactive-linking-shard-worker
description: "Use when handed a shard of page paths to re-link."
triggers:
  - "retroactive-linking shard"
  - "stage_b shard"
  - "linking worker shard"
  - "process this shard of pages for links"
---

# Retroactive linking — sharded worker

The deep re-linking pass (`retroactive-linking`) is the most expensive rem-cycle
phase and is parallelized by sharding the corpus. A shard worker is a
self-contained, bounded sub-agent that owns a fixed list of page paths, does
its own read-adjudicate-write loop, and emits a machine-readable result file a
thin aggregator merges. This skill is the **contract** for that worker — the
page-processing order, the adjudication rules, the result schema, and the
budget discipline.

## The shard contract (input)

A shard is a plain text file (e.g. `/tmp/stage_b_shard_5.txt`) with one vault
path per line, paths **relative to the vault root** (e.g.
`papers/watson-2013-igh-complete-haplotype-cnv.md`). The worker:

1. Reads the shard file → ordered list of ≤10 page paths.
2. For each page, in order, runs the loop below.
3. Writes a single result file (`/tmp/stage_b_result_<N>.yaml`) in the fenced
   shape given below.
4. Respects the budget: max 12 page reads, max 30 mutations. On budget
   exhaustion, write results for completed pages with `status: partial` and
   list the rest in `skipped`.

## Per-page loop (5 steps)

### 1. Read in full
Read body + frontmatter in one pass. No partial reads — the adjudication
needs the whole page. A recently-edited page is held (re-read before any
overwrite per `brain-ops` never-blind-overwrite).

**Shard path prefix strip.** Shard files list paths with a vault-scope
prefix (e.g. `<vault>/papers/chang-2011-....md`). That prefix is the repo
name, not a vault subdirectory — the file lives at
`<vault-root>/papers/chang-2011-...md`, NOT `<vault-root>/<vault>/papers/...`.
Strip the vault-scope prefix (and the `.md` suffix for result `target`
fields) before constructing read paths. If a read returns "File not found"
for the naively joined path, strip and retry; a quick
`find <vault-root> -maxdepth 3 -name "<slug>*"` confirms the real path.
(Observed shards 14 and 37 — wasted reads both times.)

### 2. Candidate generation (CHEAP — no exhaustive reading)
Shortlist ≤8 candidate link targets per page. Sources, cheapest first:
- **Exact title/alias mentions** of other vault pages in the prose (Grep the
  vault's `papers/`, `methods/`, `grants/`, `concepts/` dirs for the mention
  string as a filename slug).
- **Concepts/methods/papers named in prose without a wikilink** — the named
  entity, not generic vocabulary.
- **`qmd` semantic search** if available (semantic neighbours); degrades to
  Grep-only gracefully.

Do NOT read every candidate page. Existence is checked by filename match
against the vault dir listing, not by reading.

**Existence-check mechanics (shard 36).** `search_files target='files'`
uses glob patterns (`file_glob`), NOT regex — a regex alternation in the
`pattern` field returns 0 results even when files exist. For batch
existence checks, use one `terminal` call:
`ls papers/ methods/ concepts/ grants/ projects/ hypotheses/ | grep -iE 'slug1|slug2|...'`,
then confirm each hit with `ls <dir>/<slug>.md` before LINKing.

### 3. Adjudicate (expensive, shortlist only)
For each candidate, three dispositions:

**LINK (auto — body wikilink):** the target's subject is named verbatim (or by
canonical alias) in prose, AND the mention refers to the entity — not generic
vocabulary. The sense-check: **"If the target page didn't exist, would the
sentence still make sense unchanged?"** → if yes, SKIP. Generic terms (BLI,
FACS, cryo-EM, "the grant") are not links even if a page shares the name.

**TYPED-EDGE CANDIDATE (`cites:`):** the citation is analytically load-bearing —
a predecessor, motivating result, something the page builds on or refutes —
AND the target page EXISTS. Otherwise leave it out entirely (burst precision
mode). A benchmark or incidental citation is never a `cites:` edge.

**SKIP everything ambiguous** — precision over recall.

**People-mentions default to SKIP.** The authorship graph lives in frontmatter
`authors:`; prose people-mentions are rarely links in this vault's style. LINK
a person only if the mention is clearly about the person as an entity AND not
already in the page's `authors:` list.

### 4. Apply LINKs (write step)
Insert `[[target|surface]]` at the FIRST unlinked mention in the body. The
surface is human-readable display text — the entity's common name or the
exact prose token (`[[papers/watson-2023-rfdiffusion|RFdiffusion]]`), NOT
the raw path (`[[papers/foo|papers/foo]]`). Frozen
zones — never edit inside these:
- `## Verbatim` sections
- blockquoted `>` lines
- numbered reference-list lines
- frontmatter (the `links:` list is populated separately, below)

After each edit, **re-read the edited sentence** and capture the evidence span
POST-EDIT (including the `[[...]]` markup). Evidence spans must be exact
substrings of the page as committed — never elide with `...` or paraphrase. If
the span is long, quote a shorter verbatim sub-span that still locates the link.

### 5. Populate frontmatter `links:`
Mirror every body wikilink target (newly added or pre-existing) into the page's
frontmatter `links:` list. Many pages — especially stubs — carry body
wikilinks (often inside `> [!info] Stub` callouts) that were never mirrored into
`links: []`. Populating `links:` is part of the write step, not an afterthought.
If no body wikilinks exist and none were added, leave `links:` as-is.

**Frontmatter links may be forward references (shard 36).** Many pages carry
`links:` pointing to concept/method pages not yet created. Do NOT assume a
target exists because it appears in another page's frontmatter — verify via
the dir listing before LINKing. And do NOT remove existing links to
non-existent pages: they are forward references placed by the ingest process
(forward-only linking), not errors.

## Result schema

Write to `/tmp/stage_b_result_<N>.yaml` in this exact fenced-yaml shape:

```yaml
shard: <N>
status: complete   # or: partial
committed:
  - target: papers/<page-edited>
    category: forward-link          # or frontmatter-links-populated
    target_exists: true
    change: "added [[<target>|<surface>]] in <section>"
    evidence: "<post-edit verbatim span>"
candidates:
  - target: papers/<page>
    category: typed-edge
    change: "add cites: <target>"
    evidence: "<verbatim span>"
metrics:
  pages_read: <n>
  edges_committed: <n>
  edge_candidates: <n>
  candidates_examined: <n>
skipped: []
```

- `committed[]` records every mutation: body wikilinks (category
  `forward-link`) AND frontmatter `links:` population (category
  `frontmatter-links-populated`).
- Typed-edge `cites:` candidates are returned for the primary to validate and
  write (load-bearing + target exists), never written by the shard worker.
- `skipped[]` lists pages processed but with no changes, with a one-line
  reason (e.g. "pure stub, citation-only, no linkable prose").
- `anomalies[]` (optional, informational): entity-resolution flags, e.g.
  two pages in the shard sharing one PMID under different slugs (see
  Pitfalls). The aggregator treats these as informational — not committed
  or proposed edges — and safely ignores the field if it does not expect it.

## Hard constraints

- **No git commands.** The aggregator handles commit.
- **No edits to protected files:** `docs/rem-cycle/QUEUE.md`,
  `docs/rem-cycle/_state.yaml`, `people/_ledger.yaml`, `USER/<name>.md`, `SOUL.md`,
  `STYLE.md`, `RESEARCH.md`.
- **No edits to pages outside the shard.**
- **Budget:** max 12 page reads, max 30 mutations. Hitting either → write
  partial results and list the rest in `skipped`.

## Pitfalls (observed 2026-08-04, shards 5 and 28)

- **Stub pages are mostly citation-only.** A stub with a `## Citation` block
  and no other prose has no linkable text — the citation line is a frozen
  reference record, not a mention. Do not link inside it. These pages are
  correctly skipped (record in `skipped` with reason).
- **Pre-existing body wikilinks unmirrored in `links:`.** Stub pages often
  carry an info-block wikilink (`[[papers/foo]]` inside the `> [!info] Stub`
  callout) that was never copied into frontmatter `links:`. Catch and mirror
  these even when no new body link is added — it's a valid `committed` entry
  with category `frontmatter-links-populated`.
- **People-mentions ≠ links.** A rich page (e.g. a conference report) may name
  Jesse Bloom, Pamela Bjorkman, Florian Krammer in prose — all are co-authors
  already in `authors:`. SKIP. The authorship graph is in frontmatter, not
  prose.
- **Tool-name mentions are borderline.** "annotation using IgBLAST" names the
  tool (subject of `ye-2013-igblast`) verbatim and refers to the entity —
  LINK. "biolayer interferometry (BLI)" names a technique, not a page — SKIP
  even if a `bli`-ish page existed. Apply the sense-check: does the sentence
  still make sense if the target page didn't exist?
- **`cites:` precision.** The direct structural predecessor a paper extends
  (e.g. zhao-2023 builds on yuan-2020's CR3022 structure) is a load-bearing
  `cites:`. A paper merely listed in a limitations section ("later studies by
  Barnes et al. 2020…") is not — no page exists, and even if it did, it's
  incidental. Return a candidate only when load-bearing AND the target exists.
- **Mature paper pages arrive already body-wikilinked (shard 28).**
  Well-established pages (importance 0.65–0.85, full Context/Approach/
  Findings/Limitations/Analysis sections) typically already carry body
  wikilinks for their key references. The primary value-add for these pages
  is **frontmatter `links:` synchronization** — body wikilinks that were
  never mirrored into the frontmatter list. Budget adjudication time
  accordingly: expect ~0 new body LINKs and ~2–5 frontmatter-sync entries
  per mature page. Do not force body links that don't meet the verbatim
  standard just to justify the shard.
- **Result schema: frontmatter updates go in `committed[]`, not in notes
  (shard 28).** Every frontmatter `links:` addition is a committed mutation
  and must appear as a `committed[]` entry with `category:
  frontmatter-links-populated`, a `target` (the page edited), `change`
  describing what was added, and `evidence` (the frontmatter span). Do NOT
  bury frontmatter updates in a `notes` field or `metrics` prose — the
  aggregator parses `committed[]`, not free text. Similarly, any candidate
  entries must follow the exact field schema (`target`, `category`,
  `change`, `evidence`) — not ad-hoc field
  names like `page`, `reason`, `evidence_span`, `adjudication`.
- **Citation shorthand → candidate, not LINK (shard 28).** An "Author Year"
  citation shorthand in body prose (e.g. "Jardine 2016" referring to
  `papers/jardine-2016-vrc01-precursor-germline-targeting`) is NOT a verbatim
  entity name and thus not a LINK. But if it is load-bearing (provides
  context the argument depends on) AND the target page EXISTS,
  return it as a typed-edge candidate with `category: typed-edge` and `change:
  "add cites: <target>"`. Apply the same standard as any `cites:` edge.
- **EMFILE on batched file operations (shard 28).** Batching 3+ parallel
  `read_file` or `patch` calls can hit `[Errno 24] Too many open files` on
  macOS. If a batched call fails with EMFILE, retry it individually — the
  retry always succeeds. To avoid it, batch ≤2–3 file operations at a time
  when processing a shard of mature, full-length paper pages (each ~5–20 KB).
- **EMFILE total lockout under parallel burst-wave workers (shard 31).** A
  more severe variant: with many shard workers running concurrently, the
  host fd table saturates so completely that EVERY file/shell/process tool
  returns `[Errno 24]` for minutes. `skill_view` and `session_search`
  keep working (persistent connections / already-open handles) — that
  distinguishes fd exhaustion from total system failure. Recovery: retry a
  trivial `terminal` command (`true`) every ~30–60 s; `terminal` recovers
  first and the rest follow within seconds. Do NOT abandon the shard —
  wait it out, then run strictly sequential file ops. If `write_file`
  still fails after `terminal` recovers, write the result file via
  `cat > <path> << 'EOF' ... EOF` through `terminal` (fewer fds; observed
  working in shard 31).
- **`cites:` edge directionality — successors ≠ predecessors (shard 14).**
  `cites:` runs FROM the page TO a predecessor it builds on. When prose
  names a successor ("concept used in He et al. 2025"), the successor
  cites THIS page — already captured in this page's `cited_by` (populated
  by the successor at its ingest). A `cites:` from this page to the
  successor is a reversed edge; never propose it. Test: does the named
  paper build on / motivate / refute THIS page, or does THIS page build
  on the named paper? Only the latter is a `cites:`.
- **Duplicate-PMID pages within a shard (shard 14).** Two pages may share
  a PMID (and near-identical title) under different slugs — the same
  paper ingested twice. Detect by comparing `pmid:` fields while reading.
  Do NOT merge or deduplicate — `entity-resolution` owns that, outside
  shard scope. Record the pair in the result `anomalies:` list and
  process each page on its own merits.
- **Abstract blockquotes are the most common frozen zone (shard 36).**
  The `## Abstract` section is a `>` blockquote of the paper's verbatim
  abstract — the first place entity names appear, and tempting to link.
  Do NOT: it is frozen source text. Link the entity in a non-blockquoted
  section (Context, Approach, Findings, Analysis, Limitations). If the
  only mention is in the Abstract blockquote, SKIP the body link.
- **Parenthetical full-path references → LINK (shard 37).** Mature pages
  frequently name an entity followed by its full vault path in
  parentheses with no wikilink markup: "connects to ProteinEBM
  (papers/roney-2025-proteinebm)." These are strong LINK candidates —
  verbatim entity name + explicit path; the sentence WOULD change meaning
  if the target didn't exist. Convert at the entity name:
  `[[papers/roney-2025-proteinebm|ProteinEBM]]`. When a markdown link to
  the same page follows separately (`([Pacesa et al., 2025](papers/...))`),
  wikilink the entity name and leave the markdown link intact. Distinct
  from citation shorthand ("Author Year" → PROPOSE) and external-URL
  markdown links (→ SKIP). Frequency: ~1–3 per mature analytical page.
- **Grant pages as LINK targets — full path vs identifier shorthand.**
  SKIP grant-identifier shorthand ("R01AI000000", "R01 AI171438") — those
  are labels, not verbatim entity names (the page slug is
  `r01ai180120-...`, not the identifier). But grants referenced by FULL
  VAULT PATH in analytical prose ARE valid LINK targets when the
  sentence's argument depends on the grant — convert to `[[grants/<slug>]]`
  and mirror into frontmatter. A `cites:` edge paper→grant is always the
  wrong direction (grants cite papers via `cited_by`), but a body
  wikilink paper→grant is a navigational link, not a citation edge.
- **Mature-page frontmatter sync: scan the whole body; methods/projects
  count too (shards 31, 37).** The shard-28 pattern (~0 new body LINKs,
  ~2–5 frontmatter-sync entries per mature page) held at scale — and the
  high end is real: pages with rich Analysis sections had 4–5 pre-existing
  body wikilinks unmirrored in `links:`. Scan the ENTIRE body for
  `[[...]]` markup, not just the sections you edited. `methods/` and
  `projects/` targets are valid frontmatter `links:` entries, not just
  `papers/` and `concepts/`.
- **All-stub shard pattern (shard 15).** If the first 2–3 pages are all
  stubs (`needs-ingest: true`, only Citation/Stub/Ingest-log sections),
  the rest of the shard is likely the same. Expected outcome: 0 new body
  LINKs, 0 PROPOSEs, 1–3 frontmatter-sync entries from `> [!info] Stub`
  callout wikilinks. Accelerate by skipping deep candidate generation —
  scan for pre-existing body wikilinks and sync `links:`.
- **Ingest-log citation shorthand ≠ analytical mention (shard 15).** An
  "Author Year" mention inside an `## Ingest log` is bibliographic
  metadata (provenance of why the stub was created), not an analytical
  claim — SKIP for both LINK and PROPOSE, even when the target exists and
  the relationship is real. The same mention in a Findings/Analysis
  section arguing something would be a PROPOSE candidate. Same reasoning
  for antibody-name mentions in ingest logs (the name denotes the
  molecule in a trial description, not the paper).
- **Pages with zero body wikilinks are not gaps to force-fill.** A rich,
  mature page may carry NO `[[...]]` markup — discussing grants and
  projects by shorthand label with relationships living in frontmatter
  `links:`. That is a filing-style variation, not a defect. SKIP.

## Relationship to `retroactive-linking`

That skill owns the *concept* (re-read a page against the current graph, the
two edge forms, the evidence rule, the cursor). This skill owns the *shard
execution contract* — the input/output schema, the per-page loop sequence, the
budget, and the burst-precision adjudication rules a parallel worker needs to
run autonomously. Load `retroactive-linking` for the why and the conventions;
load this for the how when handed a shard file.
