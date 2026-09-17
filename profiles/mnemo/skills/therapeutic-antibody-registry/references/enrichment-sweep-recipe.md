# Bulk enrichment and resumption

Load for a bulk sequence/structure/IP sweep or its resumption. The umbrella
owns scope and block boundaries; the three enrichment skills own retrieval,
acceptance, and block schemas. This reference owns their orchestration.

## Prepare and assign

1. Read the corpus contract, entry template, and mirror manifest. Inventory
   the selected entries, exact machine-block headers from the umbrella,
   statuses, refresh dates, and source evidence. Headers locate blocks; they
   do not prove a successful search or intact curated content. Classify work
   as verified/current, missing, stale, conflicted, or awaiting a source.
2. The parent validates/refreshes shared mirrors and updates their manifest
   once before dispatch; workers use the same snapshot read-only. Validate
   formats and actual parsed rows, not historical row counts. Preserve the
   existing mirror if a download is HTML, truncated, or otherwise invalid.
3. Assign disjoint entry paths and the blocks each worker may change. Keep a
   pre-write copy or diff base for each entry's protected content. The parent
   owns shared mirrors, manifests, indexes, corpus history, and Git. Workers
   must not update them or their skill instructions; report discovered issues.
4. Choose batch sizes from the pilot workload and service limits, counting
   the short final batch. When delegating multiple batches, load
   `skills/batch-drain/SKILL.md` for its dispatch/yield/verify loop and runtime
   ceiling. Give workers absolute entry/helper/mirror paths, source inputs,
   requested blocks, and ownership. Do not impose a fixed worker count here.

## Run the per-entry owners

- Run `antibody-sequence-search` first, including identity/target checks,
  source-independence rules, and structure verification. A bulk
  `therasabdab_lookup.py` pre-check can supply candidates, not final verdicts:
  misses still require the skill's parent/component and fallback searches.
  Sparse Tier B targets do not justify accepting an unverified ladder match.
- Then run the requested `structure-search` and `patent-search` passes.
  Name and sequence searches follow those owners; a missing sequence limits
  recall but does not excuse available name searches. Patent work includes
  PLAbDab and pataa BLAST as specified by `patent-search`; record unavailable,
  deferred, or pending searches explicitly rather than silently skipping them.
- Determine modality outcomes from the actual construct and source search.
  A construct without an Fv can have `not-applicable` sequences; that does
  not establish absent structures or patents. CAR binders are not automatically
  `not-public`. Do not write placeholder blocks in place of the owner skills.
- One worker writes a given entry at a time. Independent structure/IP research
  may run from the verified sequence snapshot, but separate block ownership
  does not make concurrent whole-file replacement safe. Replace each requested
  level-two section only up to the next level-two heading; preserve everything
  else, including appendices after machine blocks. Re-read before writing.

Workers return exact changed paths, block statuses, source-linked evidence,
conflicts, and uncompleted searches. A service error or timeout is not a
negative result; follow the owner's bounded fallback and report the gap.

## Verify, recover, and close

1. Read the actual files and source-linked results. Check exact headers,
   status meaning, sequence provenance/arm assignments, structure chains and
   contact evidence, and patent search/expiry labels as applicable. Open
   original source passages or records when needed; do not accept the worker
   summary or an all-blocks-present count as verification.
2. Require `## Identity` and compare **all non-owned content** with the
   pre-write copy/diff, including ADA, sources, and modality/failure appendices.
   Header presence is only a minimal corruption alarm. If content was lost,
   preserve the current file, recover only the proven missing content from
   the latest verified copy/history, and reconcile intervening edits. Do not
   restore a whole old file or concatenate everything before/after Sequences:
   block order may differ and later curated edits must survive. Reverify.
3. Correct malformed status presentation only within the responsible owner's
   block, preserving notes; do not apply broad replacements across the corpus.
   Exclude owned scratch and coordinate caches from commits; never remove
   unrelated files. The parent regenerates indexes from verified records and
   records actual per-status coverage, denominators, and unresolved work.
4. Close coherent verified entry/index units through `skills/git-ops/SKILL.md`.
   Children return evidence; the parent stages/commits only completed owned
   changes. Source-limited results must retain their limitations.

For resumption, repeat the inventory and verification above on the actual
changed entries. Complete only missing/stale/invalid blocks; do not rerun good
blocks unnecessarily. Close verified units, leave unfinished or unrelated dirt
alone, and dispatch the remaining work under the same ownership. Neither Git
status, old run totals, nor block presence determines completion.
