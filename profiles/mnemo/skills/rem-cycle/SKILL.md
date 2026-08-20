---
name: rem-cycle
description: >
  Offline consolidation of the knowledge graph — the "dreaming" counterweight to
  waking write-and-move-on. Decomposed (Spec B): each maintenance phase is its
  own cron job writing a machine-readable phase result; a thin aggregator job
  assembles the dream report. This skill is the contract owner and the phase
  registry — which job runs which phase, on what schedule, with which delegate.
  Runs nightly / weekly / monthly, or on demand ("run a rem cycle", "dream",
  "consolidate the brain").
triggers:
  - "run a rem cycle"
  - "dream"
  - "consolidate the brain"
  - "nightly maintenance"
  - "weekly maintenance"
---

# Rem-cycle — offline knowledge consolidation ("dreaming")

While waking, the mind optimizes for your human: fast answers, write-and-move-on. That
is correct, but it accrues graph debt — pages under-linked because their targets
came later, duplicates, stale facts. The rem-cycle is the counterweight: it runs
when nobody is waiting and spends idle compute to make future retrieval better,
**without ever destroying information**.

> **Conventions:** `skills/conventions/rem-cycle-contract.md` (**read it first** — the
> phase result file, the binary commit gate, the delegation pattern, notable
> signals, protected classes, the `docs/rem-cycle/` artifacts),
> `skills/conventions/graph-and-links.md` (forward-only edges),
> `skills/conventions/importance-scoring.md` (signal-based salience, never use-decay),
> `brain-ops` (never-blind-overwrite). Character: `SOUL.md`.

## Architecture — the decomposed dream (Spec B)

Each phase is its own Hermes cron job; a thin aggregator job assembles the dream
report from phase-result files. There is no orchestrator process.

| Job | Phase | Schedule | Delegate |
|---|---|---|---|
| rem-hygiene | 1 Hygiene | nightly 02:00 | frontmatter-guard + maintain |
| rem-retro | 2 Retroactive-linking | nightly 02:30 (delegated: ≤12 shards × 5 pages) | retroactive-linking |
| rem-reinforce | 6 Reinforce | nightly 03:15 (delegated: ≤12 shards × 5 papers) | reinforce |
| rem-intersect | 8 Intersect | nightly 04:05 | intersect |
| rem-report-nightly | 9 Report | nightly 04:30 | this skill (aggregator) |
| rem-entity-resolution | 3 | Mon 04:00 | entity-resolution |
| rem-consistency | 4 | Mon 04:25 | consistency-check |
| rem-consolidation | 5 | Mon 04:50 | concept-synthesis + topic-synthesis |
| rem-concept-refresh | 5b | Mon 05:00 | concept-refresh (ripeness detection → notable) |
| rem-coalesce | 5c | Mon 05:05 | concept-coalesce |
| rem-importance | 7 | Mon 05:15 | maintain (importance) |
| rem-report-weekly | 9 Report | Mon 06:15 | this skill (aggregator) |
| rem-full-sweep | monthly sweep | 1st 05:00 | cursor completion + schema review |
| rem-report-monthly | 9 Report | 1st 06:30 | this skill (aggregator) |

Every phase job: take the lock → work within its `budgets.by_phase` slice →
write `docs/rem-cycle/runs/<date>/<phase>.yaml` → commit → release the lock.
The aggregator validates the checkable invariants on the full results (it holds
the files, not summaries — it verifies more than the old orchestrator could),
dedupes across phases on `(target, category)`, writes the concise + verbose
reports to `docs/rem-cycle/history/`, updates `_state.yaml` (`last_run`,
canonical metrics, connectivity), commits, and delivers the concise report.

**Current state (2026-08-15): the binary-gate refactor.** The queue era is over:
there is no drain phase, no propose lane, no confidence scores, no QUEUE.md
writes, no Flags section. Phases run a clean binary gate — a change that adds
value commits (with a post-edit evidence span); anything else drops silently
(counted). Observations worth attention travel as `notable:` signals in the
run files; intersect reads them and they compete for the report's One-thing
slot. Verified duplicate merges (same-DOI, exact-duplicate ledger/stub pairs)
commit in the phase that finds them. Opinion (Thesis/Frontier prose,
hypotheses, synthesis authoring) is never written by the dream — phases detect
ripeness and emit `notable:` instead. Retro and reinforce parallelize by
delegation: shard delegates extract compact structured entries and never write;
the primary validates and writes serially.

Delivery routing (live config is the source of truth; this documents intent):
- **Report jobs** (`rem-report-nightly`, `rem-report-weekly`,
  `rem-report-monthly`) deliver the concise report to the Reports channel and
  the Buzz DM. The verbose report lives only in `history/`.
- **Individual phase jobs** deliver `local` — no gateway delivery at all.

Model policy: all jobs are unpinned and follow the global default model; the
model-drift spend guard is disabled profile-wide (`cron.model_drift_guard:
false` in config.yaml) per Bryan's standing call — a default-model swap must
never block the fleet.

## What this guarantees

- **Failure isolation.** A phase that dies writes no result file; the aggregator
  records it as `missing` and every other phase's work stands.
- **Trust nothing blindly.** The aggregator re-asserts the invariants on each
  result file and checks every evidence span verbatim against its target page.
  A result that fails is dropped and named in the verbose report.
- **Budgeted, idempotent, resumable.** Per-phase budgets and cursors live in
  `_state.yaml`; an interrupted job resumes from the cursor, a re-run over
  untouched data is a no-op.
- **One concise report per tier; one commit per phase job.** The concise report
  is the only thing delivered; the verbose report and run files are the audit.

## Cadence tiers

| Cadence | Phases | Scope |
|---|---|---|
| Nightly | 1, 2, 6, 8, 9 | Hygiene + delegated retro slice + delegated reinforce + intersect + report |
| Weekly | + 3, 4, 5, 5b, 5c, 7 | Entity resolution, consistency, consolidation, ripeness detection, concept-coalesce, importance |
| Monthly | full sweep | Cursor completion + schema/eval review |

The delegated shard pattern is the scaling trick: retro and reinforce each
process up to 60 items/night (4 batches × 3 delegates × 5 items), so the whole
corpus rotates in about a month and the ingest backlog drains in days, while
every write stays serial and validated in the primary. Dispatch mechanics follow
`skills/batch-drain/SKILL.md`: yield and wait between delegate batches (never
dispatch a batch while a prior one is in flight — see the core invariant),
verify extraction results on disk before the primary writes, and dispatch the
remainder shard as a single-task call rather than dropping it.

## The phase pipeline

| # | Phase | Delegate | Mode |
|---|---|---|---|
| 1 | Hygiene | `frontmatter-guard` + `maintain` (scope `hygiene`); pending-stub / `status:unknown` backlog is detect-only (verbose counts) | binary |
| 2 | Retroactive linking | `retroactive-linking` (delegated shards) | binary |
| 3 | Entity resolution | `entity-resolution` — verified duplicates merge; unverifiable pairs → notable or drop | binary |
| 4 | Consistency & staleness | `consistency-check` — unambiguous stale tags commit; contradictions → notable | binary |
| 5 | Consolidation | `concept-synthesis` + `topic-synthesis` — tier/map auto; exact-dup merges auto; synthesis ripeness → notable (never authored in the dream) | binary |
| 5b | Thesis refresh | `concept-refresh` — detect ≥3 shifts since `thesis_updated` → notable; never drafts | binary |
| 5c | Concept-coalesce | `concept-coalesce` — aggregate stub clusters into a `concept` (≥3 independent signals + "so what"; auto-commit; never a hypothesis) | binary |
| 6 | Reinforce | `reinforce` (delegated shards) — facts-only `## Shifts` appends | binary |
| 7 | Importance recompute | `maintain` (scope `importance`) — commits all recomputes except downward on seminal/key-citation/pinned (skip + count) | binary |
| 8 | Intersect | `intersect` — the single-item ranker: corpus scan + that night's `notable:` signals → one surfacing into the report's "One thing" (surface-only, never a page) | surface |
| 9 | Report + commit | this skill (aggregator) | — |

**No external I/O.** Phases consolidate what is already in the graph. Fetching,
filling paper stubs (`ingest-pending-papers`), and resolving `status:unknown` by
lookup are **waking** concerns — the dream *detects and counts* those backlogs
(phase 1, verbose report) but never reaches outside the vault.

## Budget

Budgets are **per-phase** in `_state.yaml → budgets.by_phase.<phase>` — no
shared pie. Three kinds of work, only two budgeted: **scanned** (cheap grep /
index / clustering reads — *unbudgeted*), **read** (LLM page reads, including
delegate reads — counts against `max_pages`), **mutations** (writes — counts
against `max_mutations`). Phase jobs honor their own budget; the aggregator
sums actuals into the verbose report. Ratchets are a monthly-review decision:
the full-sweep emits recommendations, the monthly report carries them, Bryan
decides.

`_state.yaml` shape (current):

```yaml
cursors:
  retroactive-linking: <kind/slug of last re-linked page>
  reinforce: <date watermark>
briefing:
  last_surfaced: []            # qids shown in recent briefs (legacy)
autonomy:
  mode: binary                 # commit-or-drop; facts auto, opinion never
budgets:
  by_phase: { <phase>: { max_pages, max_mutations }, ... }
last_run:
  date: null
  tier: nightly
metrics:                       # canonical health counters, for the delta
  orphans: null
  dead_links: null
  edges_added: null
  by_phase: {}                 # per-phase detail, keyed by phase name
```

## Output

- `docs/rem-cycle/history/<date>-<tier>.md` — the concise dream report (the
  only delivered artifact): **One thing** up top, one-line **Done**, a one-line
  **Machinery** note only when something broke.
- `docs/rem-cycle/history/<date>-<tier>-verbose.md` — the full audit report:
  every committed entry, evidence verification N/M, drop counts, notable
  signals, budget actuals, connectivity trend.
- `docs/rem-cycle/runs/<date>/<phase>.yaml` — the machine-readable phase results.
- `docs/rem-cycle/_state.yaml` — advanced cursors, refreshed metrics.
- One commit per phase job; the aggregator commits the reports + state.

## Running a phase by hand

Any phase can be run standalone in conversation ("re-link the brain", "reinforce
the concepts") — the delegate skills handle that path and report
conversationally. The contract governs the scheduled path. A standalone run does
**not** write to `runs/` — it is off the audit pipeline by design (your human asked;
the answer is immediate).

## Anti-patterns

- Doing a phase's work inline in the aggregator — the aggregator validates and
  routes results, it does not perform the phases.
- Applying a phase result without re-asserting the invariants first.
- Re-introducing a proposal lane, a confidence score, or a review queue "just
  for this one class" — the binary gate is the design; if a class feels too
  dangerous to auto-commit, the fix is tightening the phase's commit bar, not
  rebuilding the queue.
- Emitting `notable:` signals for trivia — notables compete for the single
  One-thing slot; a phase that cries wolf drowns real signal. When in doubt,
  drop to the verbose counters.
- Delegates writing pages — extraction is delegated, writes are not. The
  primary writes serially, or same-page edits clobber.
- **Dispatching a delegate batch while a prior one is still in flight** — follow
  `skills/batch-drain/SKILL.md`: yield and wait, or the overeager re-dispatch
  triggers a truncation loop and a dropped shard.
- Delegates returning raw prose — compact structured entries only, or the
  primary's context compacts mid-run.
- Double-counting a change two phases both surfaced — dedup on `(target,
  category)` before routing, or the headline counts lie.
- Counting a cheap corpus **scan** against the page budget — only LLM `read`s
  and `mutations` are budgeted.
- Claiming to re-verify an evidence span the result file doesn't carry — the
  aggregator checks what the file contains; a missing span is a failed entry,
  not an attested one.
- Exceeding `_state.yaml` budgets, or forgetting to advance the cursor — that
  breaks resumability and idempotency.
- Committing under a generic message, or leaving the report for the snapshotter.
- Use-based forgetting, or lowering a protected page's importance.
- **Leaving the auto-push lock file in place** — each job creates the lock
  (content: `<job-name> <timestamp>`) at the start, refreshes it between
  delegate batches, and removes it after its commit. A fresh foreign lock
  (<45 min) means another job is running: skip and log.
- **Ignoring truncated phase output** — if a phase job dies mid-run, its writes
  may have landed without a result file. Reconstruct from git diff + linter;
  the aggregator records the phase `missing` and names the gap.

## Lessons appendix (monolith era, 2026-07; queue era, 2026-08)

Preserved from the retired architectures; scoped now to whichever job they
apply to.

- The parent orchestrator's turn limit (90 → 150 → 200) was the binding
  constraint, eaten by dispatch/poll overhead. The decomposed design removes the
  parent entirely.
- `child_timeout_seconds` (1800s) truncated LLM-heavy phases mid-write;
  truncated structured results were reconstructed from git diff + linter.
- Phase 6's flood bug (2026-07-15): `git log --since=<cursor>` without
  `--diff-filter=A` picked up retroactive-linking edits as "new papers" —
  40 files for 3 real ingests. Reinforce uses `--diff-filter=A`.
- Embedding full procedures in subagent prompts (never "read the skill first")
  stays true for phase-job prompts: each cron prompt carries its phase's
  complete procedure, budget, cursor, and result-file path.
- The queue era (2026-08-04 → 2026-08-15): a ≥0.9 confidence whitelist on the
  drain meant zero items ever auto-executed while proposals accumulated
  unbounded — 62 items mass-rejected at retirement. The confidence-threshold
  gate was judgment theater: the phases picked the number, the drain enforced a
  cutoff, and nobody ever made a decision. The binary gate puts the decision
  back in the phase where it belongs.
- Comparison mode (2026-08-04 → 2026-08-14): running a shadow aggregator
  alongside the monolith produced two contradictory reports per night and
  confused ownership of QUEUE.md/_state.yaml. Staggered rollouts of this
  machinery are worse than bandaid cuts — cut over completely.
