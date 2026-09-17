---
name: rem-cycle
description: >
  Offline consolidation of the knowledge graph — the "dreaming" counterweight to
  waking write-and-move-on. Decomposed (Spec B): each maintenance phase is its own
  cron job writing a machine-readable phase result; a thin aggregator job
  assembles the dream report. This skill is the contract owner and the phase
  registry — which job runs which phase, with which delegate. Runs nightly /
  weekly / monthly, or on demand ("run a rem cycle", "dream",
  "consolidate the brain").
triggers:
  - "run a rem cycle"
  - "dream"
  - "consolidate the brain"
  - "nightly maintenance"
  - "weekly maintenance"
eval_contract:
  goal: Consolidate the graph offline without destroying information — every phase runs a binary commit gate, writes a verifiable raw-YAML result, and reports honestly.
  dimensions:
    - "REGISTRY — one authoritative phase/delegate mapping consistent with the live schedule"
    - "BINARY GATE — facts commit with post-edit evidence; opinion never writes; drops are counted"
    - "ACCOUNTING — budgets, cursors, inbox, and lock discipline hold; missing phases are named"
    - "SERIALIZATION — phase results are raw YAML; example fences are documentation only"
  hard_fails:
    - Re-introducing a proposal lane, mutation-confidence gate, or review queue.
    - A scheduled read-only extraction delegate writing pages, or a primary writing another phase's result.
    - Accepting a result without the contract-required edited-page evidence or verified numeric signal basis.
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

**The phase registry** — the single authoritative table. Live scheduling config
is deployment truth for clock times, batches, and delivery; this registry names
each job, its phase, its delegate, its cadence tier, and the result-file stem the
aggregator reads. Do not duplicate or re-derive any of these elsewhere:

| Job | Phase | Delegate | Cadence | Result stem |
|---|---|---|---|---|
| rem-hygiene | 1 Hygiene | `frontmatter-guard` + `maintain` (scope `hygiene`; pending-stub / `status:unknown` backlog detect-only) | nightly | `hygiene.yaml` |
| rem-retro | 2 Retroactive linking | `retroactive-linking` (delegated shards) | nightly | `retro.yaml` |
| rem-reinforce | 6 Reinforce | `reinforce` (delegated shards) — facts-only `## Shifts` appends | nightly | `reinforce.yaml` |
| rem-intersect | 8 Intersect | `intersect` — single-item ranker; surface-only, never a page | nightly | `intersect.yaml` |
| rem-report-nightly | 9 Report | this skill (aggregator) | nightly | — |
| rem-entity-resolution | 3 Entity resolution | `entity-resolution` — verified duplicates merge; unverifiable pairs → notable or drop | weekly | `entity-resolution.yaml` |
| rem-consistency | 4 Consistency & staleness | `consistency-check` — unambiguous stale tags commit; contradictions → notable | weekly | `consistency.yaml` |
| rem-consolidation | 5 Consolidation | `concept-synthesis` + `topic-synthesis` — tier/map auto; exact-dup merges auto; ripeness → notable (never authored in the dream) | weekly | `consolidation.yaml` |
| rem-concept-refresh | 5b Thesis refresh | `concept-refresh` — detect ≥3 shifts since `thesis_updated` → notable; never drafts | weekly | `concept-refresh.yaml` |
| rem-coalesce | 5c Concept-coalesce | `concept-coalesce` — aggregate stub clusters into a `concept` (≥3 independent signals + "so what"; never a hypothesis) | weekly | `coalesce.yaml` |
| rem-importance | 7 Importance recompute | `maintain` (scope `importance`) — commits recomputes except downward on seminal/key-citation/pinned (skip + count) | weekly | `importance.yaml` |
| rem-report-weekly | 9 Report | this skill (aggregator) | weekly | — |
| rem-full-sweep | Monthly sweep | cursor completion + schema/eval review | monthly | `full-sweep.yaml` |
| rem-report-monthly | 9 Report | this skill (aggregator) | monthly | — |

Live job settings determine the dates/times, item caps, delivery destinations,
and model policy; do not alter them to match this registry. Nightly need not
mean every calendar night. All working phases use the binary gate; intersect
is surface-only and the report jobs own only reports/state.

## Run a phase

1. Read the phase skill, shared contract, and its deployment prompt. Check the
   phase coordination lock before mutation. A fresh foreign lock (under 45
   minutes) means skip and record its owner; never remove another job's lock.
   Acquire the assigned lock with job name/timestamp and refresh it between
   batches. Cleanup releases only this run's lock, including after failure.
2. Select the bounded frontier from the phase's inbox/cursor rules. Existing
   `stub-filled` packets matter: filling an old page does not add a Git file.
   Reinforce's added-paper date window uses `--diff-filter=A`; ordinary
   since-only history includes maintenance edits and falsely treats them as
   new ingests (the 2026-07-15 flood failure). Respect inbox acknowledgements
   and return the last processed cursor, not a frontier that was never read.
3. Read `budgets.by_phase` and the job's item cap. Cheap scans are unbudgeted;
   all LLM page reads, including delegates', count against `max_pages`, and
   mutations against `max_mutations`. Report scanned/read/mutated separately.
   Preserve protected pages, existing edges and frozen source text under the
   shared contract. Never lower seminal/key-citation/pinned/identity importance.
4. For scheduled retro/reinforce, load `batch-drain` and dispatch read-only
   extraction shards with explicit inputs, procedure, budgets and return shape.
   Discover the runtime schema/ceiling; yield, verify, then dispatch the next
   wave and remainder. The primary validates source evidence and writes
   serially. The separately invoked writable-shard skill is not a replacement
   for this scheduled read-only role; it requires an explicit write assignment.
5. Apply the binary gate: justified factual changes commit; uncertain work
   drops and is counted. Verified duplicate merges retain the shared identity,
   union and inbound-repair requirements. Opinion, hypotheses and Thesis/Frontier
   drafting remain outside unattended runs. Ripeness/contradictions become
   `notable:` observations for intersect, not proposals or a review queue.
6. Write the result at the registry's filename as raw YAML, never Markdown
   fences; parse and read it back. `committed[].target` is the edited page and
   `evidence` is captured after all edits to it. In retro extraction records,
   `page` is the edited page and `target` is the link destination; map the
   former into the result target. Numeric changes retain the contract's
   computed-signal-basis evidence. Account for held, skipped and partial work.
7. Validate the owned pages, inbox changes and result; close that coherent
   unit through `git-ops`. The phase primary owns Git; children do not stage,
   commit or push. A publication failure leaves a local commit, not a reason
   to repeat page edits or retain the phase lock indefinitely. Report it under
   the existing delivery policy; ordinary phase jobs deliver local-only.

If a phase stops after edits but before result emission, inspect the exact diff,
source evidence and lint output. Retain valid landed edits; reconstruct only
what can be verified and resume result writing rather than repeating mutations.
The aggregator records an absent result as `missing`; it does not perform that
recovery itself or claim a failed writer saved a file.

## Aggregate reports

1. Read the complete expected result files for the tier from the registry and
   deployment prompt. Distinguish `missing`, `skipped` and `partial`; record
   each gap. A child's summary or historical report is not a phase result.
2. Reassert the shared contract's checkable invariants: protected scope,
   ledger discipline, merge verification, budgets and evidence. Check each
   verbatim span against its declared edited page; verify numeric signal-basis
   evidence by its declared rule. Forward-only remains phase-attested with a
   diff spot-check. Reject and name failing results; do not silently substitute
   a destination page, historical source, or confidence claim for evidence.
3. Deduplicate cross-phase reporting on `(target, category)` per the contract;
   retain full entries and verification counts in the verbose audit. Lift
   intersect's actual `surfacing` into One thing, labeled opinion. If it is
   absent, report that absence, not a fabricated candidate.
4. Update only the aggregator-owned `_state.yaml` fields from verified results:
   accepted cursors, `last_run`, canonical/by-phase metrics, and connectivity
   history. Preserve budgets, existing fields and configured quality targets.
   The contract owns the rolling-history window and connectivity definitions;
   rotation uses the seven-night mean of retro reads, not tonight's slice.
5. Write concise and verbose reports under `docs/rem-cycle/history/` using
   the shared report contract. Concise: One thing, Done, and Machinery only
   for a gap/failure; weekly adds its per-phase roll-up. Monthly includes its
   targets-versus-actuals comparison and the full-sweep ratchet recommendations
   for the human's decision. No queue Flags section or separate Targets table.
   The verbose report retains every committed entry, verified N/M, notables,
   drop counts, budget actuals and connectivity. Deliver only the concise
   report to the configured destinations.
6. Read back both reports and state, then close only those owned paths through
   `git-ops`. Never collect unfinished phase edits or write a phase's result.

`docs/rem-cycle/QUEUE.md` remains frozen; the historical decision ledger has no
new writers. State-shape changes in this documentation do not authorize a
migration of production `_state.yaml`.

## Standalone and validation boundaries

A human may invoke an individual phase conversationally; its skill owns that
path and immediate report, without writing scheduled `runs/` artifacts. No
phase performs external research retrieval. Paper fills and source lookups are
waking work; authorized Git fetch/push is a separate closeout capability.

For edits to this scheduled procedure, inspect actual job prompts/logs and
replay a bounded real-source phase plus report path in scratch under
`skill-hygiene.md`. Read the produced artifacts against this contract; do not
fire a production job or deliver a test report. Structural checks or reading
old results alone do not satisfy this representative-run gate.
