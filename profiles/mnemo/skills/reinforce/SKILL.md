---
name: reinforce
description: >
  New and changed papers report sourced facts onto the concept layer's `## Shifts`
  evidence log — facts only, no opinion, no approval. Routes a recent paper to the
  concepts it touches and appends what the source *showed*, with a citation.
  Interpretation is deferred to the grant draft / brainstorm. Runs as a rem-cycle
  phase (offline, cursored) or standalone.
triggers:
  - "reinforce the concepts"
  - "update concepts from recent papers"
  - "what recent papers moved our concepts"
---

# reinforce — keep the concept evidence log current as papers arrive

A concept's `## Shifts` log is its **fact ledger** — grounded, cited, no opinion
(`synthesis-layer-pages.md`). This skill keeps it current: as papers are ingested,
it reports what each one **showed** about a concept, so when your human comes to
discuss or draft on that concept days later the sourced facts are already there.
The opinion — what the fact *means*, whether it overturns a thesis — is explicitly
**not** this skill's job; it surfaces later, in the grant draft or the brainstorm,
where it has context.

> **Conventions:** `synthesis-layer-pages.md` (**the facts-only `## Shifts` entry
> format** this writes), `rem-cycle-contract.md` (the fact/opinion line; facts
> auto-commit; the phase result), `graph-and-links.md` (forward-only),
> `quality.md` (cite-or-flag — a claim that cannot be grounded in the source is
> not written). Character: `SOUL.md` — no fabricated confidence; factual accuracy
> is the one unbreakable guardrail.

## Capabilities

- **Required:** `brain-read`, `brain-write`.
- **Optional:** `brain-search` (semantic routing for papers without explicit
  concept edges; degrades to keyword scan under Claude Code).

Universal; **no external I/O** — reinforce consolidates papers already in the graph,
it never fetches.

## What this guarantees

- **Facts only, no opinion.** An entry states what the source showed, in its own
  terms, with a citation. No "this establishes", no "this overturns", no
  maturity-marker bumps, no classification of reinforce/complicate/contradict.
- **Fully autonomous.** Every entry is a fact and commits under the binary gate
  (no approval, no proposal). The git commit and the phase result's
  `committed[]` record (with post-edit evidence spans) are the audit trail.
- **Factual accuracy is the one hard line.** The "Shown" line must be true to the
  source. If a claim cannot be grounded in the source, it is not written — there
  is no hedge large enough to license a wrong fact (`SOUL.md` spine).
- **No-op is the default.** A paper that doesn't actually *show* something new
  about a concept (merely relevant) produces no entry. Relevance is not a fact
  worth logging; the paper's `links:` edge already records it.
- **Never writes `hypotheses/`, never opines.** A bet mature enough to spin out is
  conversation's job, not this skill's.
- **Non-destructive, idempotent.** Append-only; dedup on `(concept, source)`;
  `dry-run` until the phase earns trust.

## Phases

1. **Select.** The recent-paper window — the union of (a) pages under `papers/`
   **added to git since the cursor date** (`git log --since=<cursor>
   --diff-filter=A -- papers/`) and (b) **`stub-filled` packets** in
   `docs/rem-cycle/inbox.yaml` not yet consumed by reinforce — a filled stub
   never appears in the git-added log (the file already existed), so the
   packet is the only way it enters the pipeline. After processing, append
   `reinforce` to each packet's `consumed_by`.
   Use `--diff-filter=A` (added files only) — **not** plain `--since`, which picks
   up retroactive-linking edits to old papers and floods the subagent with 40
   files when only 3 are new. The cursor (`cursors.reinforce` in
   `docs/rem-cycle/_state.yaml`) is a **date watermark**; a re-run over an
   unchanged window is a no-op.
   **Hard cap: 5 papers per run.** If more than 5 new papers are found, process
   only the 5 most recent and advance the cursor to the date of the 5th — the
   remainder will be picked up on the next run.
2. **Route.** For each paper, the concepts it touches, in priority order: its
   `links: concepts/…` edges → its `## Analysis` section → keyword/semantic match
   of its abstract/analysis against the concept's `## Thesis` / `## Frontier`.
3. **Extract the shown facts.** For each `(paper × concept)` pair, read what the
   source actually **demonstrated** — a result, a measurement, a mechanism — not
   what it implies. One entry per fact that is new to the concept's log.
4. **Apply.** Append the facts-only entry (format below), auto-committed. If the
   paper shows nothing new (merely relevant), no-op. No classification, no
   propose lane — facts auto-commit; anything that would require *interpretation*
   is simply not written here.
5. **Return** the phase result (below) or, standalone, a conversational summary.

## The facts-only entry

```markdown
### 2026-07-07 — <short factual tag>
**Source:** [[papers/<slug>]]
**Shown:** <one factual claim, in the source's own terms>
```

## As a rem-cycle phase

Phase 6 of the pipeline (`rem-cycle-contract.md`), run as its own cron job.
The scheduled job parallelizes by delegation (contract § Delegation) — shard
delegates extract compact entries, the primary validates and writes serially.
This skill returns the fenced-yaml phase result:

- **`committed[]`** — the appended entries (`category: evidence-append`), each
  carrying the cited source and the post-edit shown-fact span. There is no
  propose lane for facts.
- **`cursor`** — the date watermark, advanced to this run's date; **`metrics`** —
  `papers_scanned`, `concepts_touched`, `entries_committed`, `no_ops`,
  `dropped`.

## Output

- **Auto-appended entry** — a facts-only `## Shifts` entry in the canonical format
  (`synthesis-layer-pages.md`).
- **Standalone** — a conversational summary: what was appended, what was no-op'd.

## Anti-patterns

- Writing an opinion into the entry — "this establishes"/"this overturns" belongs
  in the grant draft, not the evidence log.
- Logging a merely-relevant paper — no-op is the default; the `links:` edge
  already records relevance.
- Writing a fact you cannot ground in the source — factual accuracy is the one
  unbreakable guardrail; omit rather than hedge.
- Writing a `hypotheses/` page, or proposing one — hypotheses fall out of
  conversation only.
- Re-appending a fact a prior run already logged — dedup on `(concept, source)`.
- Fetching anything — reinforce consolidates ingested papers, it never reaches
  outside the vault.
