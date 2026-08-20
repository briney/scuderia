---
name: batch-drain
description: "Dispatch subagent batches in waves, yield-and-wait between them, verify on disk before advancing. Use whenever sharding a large list of work items across delegate_task batches (enrichment sweeps, literature dives, corpus backfills, rem-cycle phases)."
aliases:
  - "batch-drain primitive"
  - "drain the delegation batches"
  - "dispatch in waves"
  - "yield and wait"
eval_contract:
  goal: |
    Drive a sharded, multi-batch delegation campaign so that every work item is
    dispatched exactly once, no batch is emitted while a prior batch is still in
    flight, and no shard is counted done until its output is verified against the
    filesystem. Excellent looks like: N items in, N verified artifacts out,
    committed in batches, zero truncation loops and zero silently dropped shards.
  dimensions:
    - "YIELD_AND_WAIT — does the orchestrator emit zero new dispatches while any prior batch is still in flight?"
    - "REMAINDER_INTEGRITY — is every leftover shard (list size not a multiple of batch size) dispatched via a single-task call, never dropped, never pushed through batch mode?"
    - "DISK_VS_REPORT — is every shard's completion verified against the filesystem (files exist, content correct), never against the subagent's self-reported 'completed'?"
    - "COMMIT_CADENCE — is each returned batch committed with a descriptive message before the next dispatch, beating the auto-snapshotter?"
  hard_fails:
    - "Any new delegate_task dispatch emitted while a prior batch is still in flight."
    - "Any shard counted as done without a filesystem verification of its output."
    - "Any leftover shard silently dropped (neither dispatched nor explicitly recorded as deferred)."
---

# batch-drain — the sharded-delegation primitive

The one invariant that governs every task where the orchestrator breaks a large
list of work items into `delegate_task` batches and dispatches them in waves.
This is the *scheduling discipline only*. What each subagent *does* is specified
by the calling skill (`literature-dive` ingests Tier 1 papers; `therapeutic-antibody-registry`
enriches entry blocks; `retroactive-linking` re-links a shard of pages). This
skill owns the loop that moves items through those workers without dropping any,
re-dispatching early, or building on incomplete results.

## The core invariant

> **After dispatching a batch, the orchestrator STOPS GENERATING until that
> batch's consolidated result returns. Do not emit a new `delegate_task` while
> any prior batch is in flight.**

"In flight" and "returned" are different states. A batch has *returned* only when
its consolidated result has re-entered the conversation as a new message — not
when it was dispatched, not when a "Background N tasks running" notice appears.

**Mechanics of waiting (this runtime).** There is no explicit blocking `wait()`
to call here. Background child results *re-enter the conversation* as their own
message when they finish. Therefore "yield and wait" is: **end your turn after
dispatching.** Do not emit further tool calls and do not emit prose that would
trigger another dispatch, until the consolidated result message arrives. In this
runtime, yielding *is* waiting.

The most common failure — and the one this rule exists to kill — is the
overeager loop: dispatch batch 1 → see "Background 3 tasks running" → emit batch
2 anyway → each new response overflows the completion API's output-token cap
(`finish_reason='length'`) → a truncation lands mid-`delegate_task` arguments →
a malformed batch is rejected and its shard vanishes. One missing yield cascades
into a token-truncation storm *and* silent work loss. Yield breaks the cascade at
its root.

## Foreground work while a batch is in flight — narrow and gated

Permitted **only** when the work does not depend on the in-flight batch's
outputs. The test: "do I need anything these children are still producing to do
this correctly?" If yes, it waits.

- **Permitted:** work whose inputs are already in hand — reading existing pages
  to map what is already known, compiling a working doc that *informs* later
  synthesis but does not consume the running results. (`literature-dive`'s
  "read existing concept pages → compile the virus/entry-mechanism/receptor
  list" is the canonical example.)
- **Forbidden:** building a downstream artifact whose inputs the running children
  are still producing. A concept page synthesized before its evidence papers
  finish ingesting is built on missing inputs and must be rebuilt; the rebuild
  costs more than the wait ever did. The same holds for an index regenerated
  before every entry exists, a profile synthesized before its papers land.

Foreground work is not a way to fill dead time. If the only "work" available is
the thing that depends on the batch, the correct action is to yield and wait.

## Batch sizing

- `delegate_task` enforces a `max_concurrent_children` ceiling (currently 3).
  A batch larger than the ceiling is rejected at dispatch ("Too many tasks").
  Size batches at or under the ceiling.
- Batch in whole multiples. When the list size is not a multiple of the batch
  size, the **remainder** is dispatched as a **single-task call** — never via
  batch mode (batch mode rejects fewer than 2 tasks: a 1-item batch errors and
  its item is dropped). A single-task call queues and runs when a slot frees.
- Never drop a shard. Every item is either dispatched (whole batch, or remainder
  as single-task) or explicitly recorded as deferred with its own slot.

## The drain loop

1. **Size and shard** the item list into batches at or under the ceiling, with
   the remainder held out as a single-task call.
2. **Dispatch one batch.** Then yield and wait (see core invariant).
3. **On return, verify on disk.** Count artifacts on the filesystem — files
   exist, frontmatter parses, required content present — never against the
   subagent's self-reported "completed." A subagent can report success without
   writing (see failure table), and can time out *after* writing correctly:
   disk is truth, not the report and not the exit.
4. **Commit the returned batch** with a descriptive message before the next
   dispatch. The auto-snapshotter can commit unfinished work under a generic
   message if it fires mid-wave; commit promptly so intent survives.
5. **Dispatch the next batch.** Repeat 2-4 until all batches are out. Dispatch
   the remainder single-task call last (or fold it into the final wave).
6. **Bulk read-back at the end.** After the last batch returns, one aggregate
   verification (a script checking every artifact at once) before declaring the
   campaign complete.

## Failure-mode table

| Syndrome | Cause | Fix |
|---|---|---|
| `finish_reason='length'` truncation storm | Overeager re-dispatch — new batches emitted while prior ones in flight, overflowing the completion API's output-token cap | Yield and wait (core invariant) |
| `[Batch mode requires at least 2 tasks]` on a `1x` dispatch | Remainder shard pushed through batch mode | Dispatch the remainder as a single-task call |
| Item silently missing from final accounting | A shard dropped in a truncation or malformed batch | Verify count in/out at the end; re-run any shard with no disk artifact |
| Reported "completed," no file on disk | Trusted the subagent's self-report | Verify on disk, not on the report |
| Subagent timed out, files actually written | Assumed timeout == failure | Treat timeout as "check disk"; re-run only what's absent |
| Index/concept page built, then rebuilt | Foreground built a downstream artifact on in-flight inputs | Narrow-and-gated foreground rule |

## Conventions

- `skills/conventions/test-before-bulk.md` — never a full campaign without
  validating on a small pilot (3-5 items) first.
- `skills/conventions/skill-hygiene.md` — this skill's own edits obey the eval
  contract and the no-regression law above.

## Cross-references

Consumers (edit these to point here rather than restating the loop inline):

- `skills/literature-dive/SKILL.md` — multi-batch ingestion during a deep dive.
- `skills/therapeutic-antibody-registry/references/enrichment-sweep-recipe.md` —
  bulk enrichment sweeps of the antibody registry.
- `skills/retroactive-linking/SKILL.md` and `skills/retroactive-linking-shard-worker/SKILL.md` —
  corpus sharding for re-link passes.
- `skills/rem-cycle/SKILL.md` — nightly phases dispatched 4x3x5.
- `skills/antibody-target-hitlist/templates/full-run-prompt.md` — target-profile
  build at scale.
