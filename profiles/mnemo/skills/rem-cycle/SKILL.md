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
> phase result file, the two commit tiers, run mode, graduated autonomy, the
> decision ledger, protected classes, the `docs/rem-cycle/` artifacts),
> `skills/conventions/graph-and-links.md` (forward-only edges),
> `skills/conventions/importance-scoring.md` (signal-based salience, never use-decay),
> `skills/conventions/test-before-bulk.md` (grow phases one at a time), `brain-ops`
> (never-blind-overwrite). Character: `SOUL.md`.

## Architecture — the decomposed dream (Spec B)

Each phase is its own Hermes cron job; a thin aggregator job assembles the dream
report from phase-result files. There is no orchestrator process. Design:
the instance's private `docs/specs/` and `docs/plans/`.

| Job | Phase | Schedule | Delegate |
|---|---|---|---|
| rem-drain | 0 Drain | nightly 02:40 | queue-drain |
| rem-hygiene | 1 Hygiene | nightly 03:00 | frontmatter-guard + maintain |
| rem-retro | 2 Retroactive-linking | nightly 03:25 | retroactive-linking |
| rem-reinforce | 6 Reinforce | nightly 03:50 | reinforce |
| rem-report-nightly | 9 Report | nightly 04:30 | this skill (aggregator) |
| rem-entity-resolution | 3 | Mon 04:00 | entity-resolution |
| rem-consistency | 4 | Mon 04:25 | consistency-check |
| rem-consolidation | 5 | Mon 04:50 | concept-synthesis + topic-synthesis |
| rem-concept-refresh | 5b | Mon 05:00 | concept-refresh |
| rem-importance | 7 | Mon 05:15 | maintain (importance) |
| rem-intersect | 8 | Mon 05:40 | intersect |
| rem-report-weekly | 9 Report | Mon 06:15 | this skill (aggregator) |
| rem-full-sweep | monthly sweep | 1st 05:00 | cursor completion + schema review |
| rem-report-monthly | 9 Report | 1st 06:30 | this skill (aggregator) |

Every phase job: take the lock → work within its `budgets.by_phase` slice →
write `docs/rem-cycle/runs/<date>/<phase>.yaml` → commit → release the lock.
The aggregator validates the checkable invariants on the full results (it holds
the files, not summaries — it verifies more than the old orchestrator could),
dedupes across phases on `(target, category)`, writes the dream report,
prepends QUEUE.md (qid'd, deduped against decisions.yaml), updates `_state.yaml`
(`last_run`, canonical metrics, health delta), commits, delivers.

Phase jobs deliver `local`; only report jobs deliver to the rem-cycle topic.

**Current state (2026-08-03):** `rem-drain` and `rem-report-nightly` (comparison
mode) are live. Nightly phases 1/2/6 still run inside the `rem-cycle-nightly`
monolith, which writes phase-result files for the aggregator (shim). Weekly and
monthly monoliths unchanged. Peels proceed one phase per week per the plan.

## What this guarantees

- **Failure isolation.** A phase that dies writes no result file; the aggregator
  records it as `missing` and every other phase's work stands. There is no
  parent turn limit to hit — each job owns a full budget for one phase.
- **Trust nothing blindly.** The aggregator re-asserts the invariants on each
  result file — no protected-page write, no destructive op, an evidence span
  checked verbatim on every edge, budget held. A result that fails is dropped
  and flagged, not applied.
- **Budgeted, idempotent, resumable.** Per-phase budgets and cursors live in
  `_state.yaml`; an interrupted job resumes from the cursor, a re-run over
  untouched data is a no-op.
- **Non-destructive, dry-run by default** until a phase earns trust.
- **One report per tier; one commit per phase job.** Proposals accumulate in
  `QUEUE.md`, drained by your human directly or via `queue-drain` — never auto-cleared.

## Cadence tiers

The tier selects the phase set; the job table above is the schedule.

| Cadence | Phases | Scope |
|---|---|---|
| Nightly | 0, 1, 2, 6, 9 | Queue drain + hygiene + retroactive slice + reinforce on new papers + report |
| Weekly | + 3, 4, 5, 5b, 7, 8 | Entity resolution, consistency, consolidation, Thesis refresh, importance, intersect |
| Monthly | full sweep | Cursor completion + schema/eval review |

The rotating slice (phase 2) is the scaling trick: a cursor over the whole
corpus, a fixed window per run, so every old page is periodically reconsidered
without any single run exploding in cost.

## The phase pipeline

| # | Phase | Delegate | Wired? | Trial-confirmed? |
|---|---|---|---|---|
| 0 | **Drain** | `queue-drain` (mode detect-and-log until armed) | **yes** | — |
| 1 | Hygiene | `frontmatter-guard` + `maintain` (scope `hygiene`); the pending-stub / `status:unknown` backlog is **detect-only** | **yes** | **yes** (2026-07-08) |
| 2 | **Retroactive linking** | `retroactive-linking` | **yes** | **yes** (2026-07-08) |
| 3 | Entity resolution | `entity-resolution` | **yes** | — |
| 4 | Consistency & staleness | `consistency-check` | **yes** | — |
| 5 | Consolidation | `concept-synthesis` + `topic-synthesis` (generative → **propose**; tiering / `concepts/README.md` map auto) | **yes** | — |
| 5b | Thesis refresh | `concept-refresh` (≥3 shifts since `thesis_updated` → propose rewrite) | — | — |
| 6 | **Reinforce** | `reinforce` — concept `## Shifts` from recent papers; auto-append high-confidence, propose borderline / promote / contradict | **yes** | **yes** (2026-07-08) |
| 7 | Importance recompute | `maintain` (scope `importance`) | **yes** | — |
| 8 | **Intersect** | `intersect` — cross-concept hypotheses (weekly); propose bet × bet intersections that clear the promise + discriminating-test + novelty gates | **yes** | — |
| 9 | Report + commit | this skill (aggregator) | **yes** | — |

**No external I/O.** Phases consolidate what is already in the graph. Fetching,
filling paper stubs (`ingest-pending-papers`), and resolving `status:unknown` by
lookup are **waking** concerns — the dream *detects and reports* those backlogs
(phase 1) but never reaches outside the vault.

## Budget

Budgets are **per-phase** in `_state.yaml → budgets.by_phase.<phase>` — no
shared pie. Three kinds of work, only two budgeted: **scanned** (cheap grep /
index / DOI-grouping reads — *unbudgeted*), **read** (LLM page reads — counts
against `max_pages`), **mutations** (writes — counts against `max_mutations`).
Phase jobs honor their own budget; the aggregator sums actuals into the report.
Ratchets are a monthly-review decision (see the overhaul plan, Phase IV) — a
quality target missed twice running gets +50% budget, capped at 2× the trial
value; one met with <50% consumption twice running gets trimmed.

`_state.yaml` shape (current):

```yaml
cursors:
  retroactive-linking: <kind/slug of last re-linked page>
briefing:
  last_surfaced: []            # qids shown in recent briefs
autonomy:
  mode: detect-and-log         # detect-and-log | armed
  whitelist: []
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

- `docs/rem-cycle/history/<date>-<tier>.md` — the dream report, skimmable in
  under a minute, connectivity health up top, proposals highest-impact first.
- `docs/rem-cycle/QUEUE.md` — the review queue, this run's proposals prepended
  (qid'd, deduped against the queue **and** `decisions.yaml`).
- `docs/rem-cycle/_state.yaml` — advanced cursors, refreshed canonical +
  per-phase metrics.
- `docs/rem-cycle/runs/<date>/<phase>.yaml` — the machine-readable phase results
  (audit record, git-tracked).
- One commit per phase job; the aggregator commits the report/queue/state.

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
- Running a not-yet-wired phase's job by hand to "fill the gap" — skip it and
  log it; a run must not claim work it did not do.
- Auto-clearing or rewriting `QUEUE.md` — only your human drains it (directly or via
  `queue-drain`). On a re-run, **prepend and dedup**; never re-queue a proposal
  already there or already rejected (`decisions.yaml`).
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
- Use-based forgetting, or decaying a protected page's importance.
- Defaulting to `normal` mode before a phase has earned trust; arming autonomy
  before the ledger earns it (`_state.yaml → autonomy` is detect-and-log until
  the track record clears the gates).
- **Leaving the auto-push lock file in place** — each job creates the lock
  (content: `<job-name> <timestamp>`) at the start and removes it after its
  commit. A fresh foreign lock (<45 min) means another phase is running: skip
  and log; the aggregator reports it.
- **Ignoring truncated phase output** — if a phase job dies mid-run, its writes
  may have landed without a result file. Reconstruct from git diff + linter;
  the aggregator records the phase `missing` and names the gap.

## Lessons appendix (monolith era, 2026-07)

Preserved from the orchestrated architecture; scoped now to whichever job they
apply to. The failure modes that forced decomposition:

- The parent orchestrator's turn limit (90 → 150 → 200) was the binding
  constraint, eaten by dispatch/poll overhead. The decomposed design removes the
  parent entirely.
- `child_timeout_seconds` (1800s) truncated LLM-heavy phases mid-write;
  truncated structured results were reconstructed from git diff + linter.
- Phase 6's flood bug (2026-07-15): `git log --since=<cursor>` without
  `--diff-filter=A` picked up retroactive-linking edits as "new papers" —
  40 files for 3 real ingests. Reinforce uses `--diff-filter=A` and caps at 5.
- Embedding full procedures in subagent prompts (never "read the skill first")
  stays true for phase-job prompts: each cron prompt carries its phase's
  complete procedure, budget, cursor, and result-file path.
