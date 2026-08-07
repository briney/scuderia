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

### 3. Adjudicate (expensive, shortlist only)
For each candidate, three dispositions:

**LINK (auto — body wikilink):** the target's subject is named verbatim (or by
canonical alias) in prose, AND the mention refers to the entity — not generic
vocabulary. The sense-check: **"If the target page didn't exist, would the
sentence still make sense unchanged?"** → if yes, SKIP. Generic terms (BLI,
FACS, cryo-EM, "the grant") are not links even if a page shares the name.

**PROPOSE (typed edge `cites:`):** the citation is analytically load-bearing —
a predecessor, motivating result, something the page builds on or refutes —
AND confidence ≥ 0.9 AND the target page EXISTS. Below 0.9 or target missing →
leave it out entirely (burst precision mode). A benchmark or incidental
citation is never a `cites:` edge.

**SKIP everything ambiguous** — precision over recall.

**People-mentions default to SKIP.** The authorship graph lives in frontmatter
`authors:`; prose people-mentions are rarely links in this vault's style. LINK
a person only if the mention is clearly about the person as an entity AND not
already in the page's `authors:` list.

### 4. Apply LINKs (write step)
Insert `[[target|surface]]` at the FIRST unlinked mention in the body. Frozen
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
proposed:
  - target: papers/<page>
    category: typed-edge
    target_exists: true
    change: "add cites: <target>"
    evidence: "<verbatim span>"
    confidence: 0.9
metrics:
  pages_read: <n>
  edges_committed: <n>
  edges_proposed: <n>
  candidates_examined: <n>
skipped: []
```

- `committed[]` records every mutation: body wikilinks (category
  `forward-link`) AND frontmatter `links:` population (category
  `frontmatter-links-populated`).
- `proposed[]` records typed-edge `cites:` proposals only.
- `skipped[]` lists pages processed but with no changes, with a one-line
  reason (e.g. "pure stub, citation-only, no linkable prose").

## Hard constraints

- **No git commands.** The aggregator handles commit.
- **No edits to protected files:** `docs/rem-cycle/QUEUE.md`,
  `docs/rem-cycle/_state.yaml`, `people/_ledger.yaml`, `USER.md`, `SOUL.md`,
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
  (e.g. zhao-2023 builds on yuan-2020's CR3022 structure) is a high-confidence
  `cites:`. A paper merely listed in a limitations section ("later studies by
  Barnes et al. 2020…") is not — no page exists, and even if it did, it's
  incidental. Propose only when load-bearing AND target exists AND conf ≥ 0.9.
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
  aggregator parses `committed[]`, not free text. Similarly, `proposed[]`
  entries must follow the exact field schema (`target`, `category`,
  `target_exists`, `change`, `evidence`, `confidence`) — not ad-hoc field
  names like `page`, `reason`, `evidence_span`, `adjudication`.
- **Citation shorthand → PROPOSE, not LINK (shard 28).** An "Author Year"
  citation shorthand in body prose (e.g. "Jardine 2016" referring to
  `papers/jardine-2016-vrc01-precursor-germline-targeting`) is NOT a verbatim
  entity name and thus not a LINK. But if it is load-bearing (provides
  context the argument depends on) AND the target page EXISTS AND conf ≥ 0.9,
  it is a valid `proposed[]` entry with `category: typed-edge` and `change:
  "add cites: <target>"`. Apply the same standard as any `cites:` edge.
- **EMFILE on batched file operations (shard 28).** Batching 3+ parallel
  `read_file` or `patch` calls can hit `[Errno 24] Too many open files` on
  macOS. If a batched call fails with EMFILE, retry it individually — the
  retry always succeeds. To avoid it, batch ≤2–3 file operations at a time
  when processing a shard of mature, full-length paper pages (each ~5–20 KB).

## Relationship to `retroactive-linking`

That skill owns the *concept* (re-read a page against the current graph, the
two edge forms, the evidence rule, the cursor). This skill owns the *shard
execution contract* — the input/output schema, the per-page loop sequence, the
budget, and the burst-precision adjudication rules a parallel worker needs to
run autonomously. Load `retroactive-linking` for the why and the conventions;
load this for the how when handed a shard file.

## References

- `references/shard-28-observations.md` — session-specific detail from shard 28
  (mature-page pattern, result schema violations, citation shorthand
  adjudication, EMFILE batching issue).
