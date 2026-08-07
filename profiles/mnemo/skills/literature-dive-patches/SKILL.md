---
name: literature-dive-patches
description: "Patch pending literature-dive: batching, selection, race."
triggers:
  - "patch literature-dive skill"
---

# literature-dive — profile-side patches

The authoritative `literature-dive` SKILL.md lives in the vault at
`skills/literature-dive/SKILL.md` and is loaded by `skill_view`
from there. When `skill_manage` cannot patch the vault copy directly, record
the patch here so a future vault-edit session can fold it in.

## Patch 2026-08-04: Batching guidance contradicts the pool limit

### Fix in Phase 4 (Batching paragraph)

The current SKILL.md says "If Tier 1 has ≤5 papers, delegate all at once.
If 6–15, batch in groups of 3–5." This contradicts the lower
"Delegation pool limits" paragraph ("the concurrent delegation pool is 3
by default"). A 4-or-5-paper single `delegate_task` call is **rejected**
at dispatch with "Too many tasks: max_concurrent_children is 3" — the
runtime error, not a soft queue. Observed 2026-08-04: a 4-paper batch was
rejected; the dive had to split into a 3-paper call plus a separate
single-task call.

Replace the Batching paragraph with:

```markdown
**Batching.** The concurrent delegation pool is 3 (`max_concurrent_children`).
Dispatch at most 3 papers per `delegate_task` call — a 4-paper call is
rejected with "Too many tasks: max_concurrent_children is 3." If Tier 1
has ≤3 papers, delegate all at once. If 4–9, send in batches of 3 (or
dispatch the overflow as a separate single-task `delegate_task` call, which
queues and runs when a slot frees). If >10, pause after the first batch
and check quality before continuing — this is the `test-before-bulk`
convention.
```

The "Delegation pool limits" paragraph further down already states the 3
default; the fix is to make the Batching paragraph agree with it and give
the concrete dispatch shape (separate single-task call for overflow).

## Patch 2026-08-04: Non-duplicative Tier 1 selection (user preference)

### Add to Phase 3 (Tier classification) and the Tier 1 bar

Bryan's explicit filter for large dives (stated 2026-08-04, after the
bacterial-toxins dive): **"prioritize load-bearing papers that are
non-duplicative. We want only the highest-value primary literature to be
ingested. If it doesn't add something new, no need to ingest."**

The current "discusses in detail" bar gates *how much the review discusses
a paper*, not *whether ingesting it adds new signal to the brain*. For a
broad multi-axis dive (e.g. bacterial toxins across diversity, mechanism,
evolution, and intervention axes), several Tier 1 candidates will
recapitulate toxin biology the brain already holds from prior dives. The
bar must be tightened by a dedup-against-the-brain-and-against-sibling-axes
step:

Add to Phase 3, after "Dedup against the brain":

```markdown
**Non-duplicative filter (Bryan's explicit preference for large dives).**
Before ingesting a Tier 1 candidate, ask: does this paper add something
the brain does not already hold, and does it add something a sibling
Tier 1 paper in the same dive does not already cover? A review that
"discusses in detail" a toxin whose structure, mechanism, and
neutralization the brain already ingested in a prior dive (e.g. the
antibacterial-antibody-discovery dive already covered C. difficile TcdA/B,
anthrax PA, Shiga, pertussis toxin) does **not** need a second full
ingest — note it as already-covered and drop it from the dispatch list.
The Tier 1 bar is "discusses in detail AND adds new signal," not
"discusses in detail" alone. When the dive spans multiple axes (diversity,
mechanism, evolution, intervention), prefer one load-bearing paper per
axis over several papers that recapitulate the same axis.
```

This is a *preference encoded into the skill*, not a memory-only note:
Bryan stated it as a standing rule for how dives should select, so the
skill that governs Tier 1 selection carries it.

## Patch 2026-08-04: Ledger read-back race condition (concurrency hazard)

### Add to the concurrency-hazard section (Phase 4 read-back)

A new failure mode beyond "subagent reports completed without writing the
file": the subagent writes the **page** but has not yet appended the
**author ledger entries** when the orchestrator's read-back check runs
mid-flight. The orchestrator, seeing the authors as "missing from ledger,"
appends them — and the subagent, finishing its Phase 8 moments later,
appends the same authors. The result is **duplicate ledger entries by
slug**, requiring a dedup pass. Observed 2026-08-04 (bacterial-toxins
wave-3): knight-2015 and he-2013 subagents had written their pages but
not their ledger entries at the orchestrator's first read-back; the
orchestrator appended 39 entries; the subagents then appended the same
39; the ledger went from 3261 → 3399 with 39 duplicate slugs.

Add to the "Subagent failures" / read-back subsection:

```markdown
**The ledger-read-back race.** A subagent can write the paper page *before*
it writes the author ledger entries. If the orchestrator's read-back
checks the ledger mid-flight and finds the authors "missing," then
appends them, it will duplicate entries the subagent adds moments later
when it completes Phase 8. The safe read-back for ledger completeness
is: wait until the batch's consolidated result message has arrived
(the delegation returns only after ALL children finish), THEN check the
ledger. Do not check the ledger while the batch is still in flight. If
you must check early, treat "authors missing from ledger" as "not yet
written," not "failed" — do not append on an early negative; re-check
after the batch completes. If duplicates do occur, dedup by slug keeping
one entry (union citations/affiliations, keep the ORCID-bearing entry);
a `yaml.dump` whole-file rewrite is acceptable for the dedup but
produces a large diff — prefer a targeted script that reads, dedups in
memory, and writes back only if no siblings are concurrently editing.
```

This complements the existing `paper-ingest` concurrency patches
(sibling ledger wipe, same-slug/different-slug duplicates) — it is the
*orchestrator-side* cause of duplicates, not a sibling-side cause.

## Companion vault-side skills that should absorb these patches

- `literature-dive/SKILL.md` — Phase 4 Batching, Phase 3 non-duplicative
  filter, Phase 4 read-back race.
