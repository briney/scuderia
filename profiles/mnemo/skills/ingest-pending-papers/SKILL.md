---
name: ingest-pending-papers
description: "Drain the paper-ingest queue — find every paper page with `needs-ingest: true` and fill it in. Orchestrates one `delegate_task` per stub so each paper-ingest runs in an isolated subagent context, by design, so the queue size cannot compact this session and a single bad DOI cannot derail the drain."
triggers:
  - "ingest pending papers"
  - "process the key citations"
  - "fill in the stub paper pages"
  - "drain the paper-ingest queue"
  - a scheduled queue-drain run
eval_contract:
  goal: Drain queued papers with verified per-item outcomes and complete parent-owned wiring.
  dimensions:
    - "ACCOUNTING — every original input has a verified outcome and canonical path"
    - "ISOLATION — workers fill assigned pages; parent owns all shared writes"
    - "VERIFICATION — source-backed exceptions and completed-page checks agree with paper-ingest"
    - "RECOVERY — incomplete work stays queued and provider errors do not erase completed writes"
  hard_fails:
    - Counting a child report or PAGE_READY result as a completed ingest without read-back and wiring.
    - Requeueing a valid fill solely because a verified DOI is absent or authorship is collective-only.
    - Losing citing edges, provenance, or original queue items from final accounting.
---

# ingest-pending-papers — drain the paper-ingest queue

> **Git closeout:** Follow `skills/git-ops/SKILL.md`. The drain parent closes each verified group of fills, required wiring, and propagation packets; children never perform Git operations. Incomplete fills remain outside the completed unit. The final accounting identifies any local-only commits or held changes.

Drain queue entries with the same paper-ingest workers used for direct
requests and dives. Read `skills/conventions/paper-stubs.md` for provenance
and lifecycle. The drain can follow a producer in the same session and can
resume page-only results awaiting shared wiring; no new selection gate applies.

> **Conventions:** `skills/conventions/frontmatter.md` (the `needs-ingest`,
> `cited_by`, `ingest_attempts`, `last_ingest_attempt` fields on `paper`),
> `skills/conventions/brain-first.md` (the consumer is brain-first by construction
> — it reads existing pages and updates them),
> `skills/conventions/preprint-retrieval.md` (bioRxiv/medRxiv full text around the Cloudflare block),
> `skills/conventions/capabilities.md` (the harness contract).

## Capabilities

`brain-read` (scan `papers/` for `needs-ingest: true`), `brain-write`
(via delegated `paper-ingest`), `spawn-subagent` (one per stub — the
context-isolation lever this whole producer/consumer split exists for).
Each delegated subagent in turn needs `paper-ingest`'s capabilities.

## What this guarantees

- The queued pages created upstream by the supported producers get
  distilled and wired into complete `paper` pages without
  accumulating full extraction conversations in the producer’s context.
- A single failed ingest does **not** halt the queue. The skill continues
  through the remaining stubs and reports per-paper status at the end.
- Failures are recorded on the failing page (via `paper-ingest`'s
  `## Ingest log` mechanism), so the next run of this skill can read the
  log and skip known-broken DOIs instead of retrying blindly.
- `cited_by` and provenance survive fills and parent-owned merges under
  the shared stub contract. Children never perform cross-page merges.

## Why this is its own skill rather than a flag on `paper-ingest`

A single-paper invocation (`paper-ingest`) and a queue-drain invocation are
different jobs with different failure semantics and different reporting
formats. The queue drainer is a thin orchestrator; `paper-ingest` is the
per-paper worker; the shared producer/consumer contract, including why
producers queue rather than distill inline, is owned by
`skills/conventions/paper-stubs.md` — read it rather than restating it here.

## Concurrency and ownership

Load `skills/batch-drain/SKILL.md`; it owns batch sizing, runtime call shape,
yield/return discipline, and remainder accounting. Use the current tool schema
and configured ceiling, never a frozen pool size or a nonexistent `toolsets`
parameter. Do not dispatch a new wave while one remains in flight.

Prefer one isolated page-only worker per queued paper. The parent owns
bibliography decisions and shared-file writes, including author wiring,
propagation, and merges. Inline work is also possible when small or when
delegation is unavailable; keep the same verification and completion checks.
Follow the runtime’s configured models and limits without changing pins.

## Phases

1. **Find the queue.** The canonical method is an `execute_code` script
   that reads each `papers/*.md` file, parses the YAML frontmatter with
   `yaml.safe_load`, and filters on `fm.get('needs-ingest') is True`.
   This yields the true stub set in one pass — and also extracts
   `cited_by`, `ingest_attempts`, `last_ingest_attempt`, and `title` for
   sorting. Order by `len(cited_by)` descending — high-edge stubs first,
   since they have the most evidence of being worth the time.

   Do **not** use `search_files target=content` for `needs-ingest: true`
   as the primary method. It has two known bugs observed on 2026-08-05:

   - **False positives:** the content search matches `needs-ingest: true`
     appearing *inside body text* — particularly in `## Ingest log`
     entries that quote the field name. A 2026-08-05 drain found 121
     content matches but only 84 YAML-verified stubs.
   - **Silent truncation:** the default `limit=100` silently truncates
     queues over 100 stubs. A 2026-08-05 queue of 121 was read as 100,
     hiding 21 stubs from the orchestrator. Always specify `limit=500`
     if you do use `search_files` as a secondary check.

   The `execute_code` approach avoids both bugs because it parses the
   actual YAML frontmatter (not body text) and has no artificial limit.

2. **Read each stub's `## Ingest log`.** A stub may have failed previous
   attempts. If the log shows a terminal-looking diagnostic ("DOI
   unresolvable; suggest manual lookup", "paywalled with no PMC and no
   OA"), skip the stub in this run and note it in the final report. The
   user decides whether to manually intervene or to tag the page
   `unresolvable` and remove from the queue. Do *not* silently retry
   what previously failed for a documented terminal reason.

2.5. **Validate stub seed identifiers before delegating.** Stub seeds are
   transcribed by producer skills from citing papers' reference lists and
   can carry the wrong DOI, PMID, or both (observed: the McCaleb 2024 stub
   carried a different paper's DOI from the same reference list;
   literature-dive Tier-1 task contexts were ~70% wrong on 2026-08-05).
   Run the pre-dispatch validator over the whole queue in one batch:

   ```bash
   python3 skills/paper-ingest/scripts/validate_identifiers.py \
       --batch /tmp/queue_citations.json --recover
   ```

   Build the batch JSON from each stub's `## Citation` entry and
   frontmatter: `title`, `author` (first-author surname), `year`, plus
   whatever of `pmid`/`doi`/`pmcid` the stub carries (~2s per citation;
   this step runs once per drain, not per delegation batch). Then:

   - `validated` — dispatch as normal.
   - `recovered` — patch the stub's seed identifiers (frontmatter
     `doi`/`pmid` and the `## Citation` entry) to the corrected values,
     note the correction in the stub's `## Ingest log`, then dispatch
     with the corrected identifiers in the task context.
   - `HOLD` — do not dispatch. Note in the final report for manual
     resolution (same treatment as a terminal-diagnostic skip).
   - `retracted: true` — surface in the final report; do not dispatch
     without asking the user (a retracted paper may still warrant a
     page, but that is a human call).

   Also run the pre-write dedup gate over the queue before dispatching —
   a stub whose DOI already has a FULL page on disk is a duplicate-in-
   waiting, and dispatching it wastes a subagent on a merge that Phase 4
   verification then has to untangle:

   ```bash
   python3 skills/paper-ingest/scripts/dedup_check.py \
       --doi <doi> --pmid <pmid> --title <title> --json
   ```

   Confirmed matches to full pages are parent-owned merges under
   paper-ingest Phase 5 and the shared stub contract. Verify the canonical
   page, union provenance/citing edges, and repair inbound references before
   deleting a duplicate; include this original input in final accounting.
   Title-only matches are REVIEW, not identity verdicts.

3. **Delegate one page-only fill per queue item.** Use batch-drain
   and include the existing absolute input path, source citation, validated
   identifiers, input `cited_by` and provenance snapshot, expected canonical
   target, and a unique scratch prefix. Tell the leaf to load paper-ingest,
   use `venue` (not `journal`) and `year`, resolve the complete author list,
   and write only its assigned paper and scratch/source files. No shared
   ledger/person/concept/stub/inbox mutations and no Git operations.

   Require paper-ingest's return record: `status`, `input_path`,
   `canonical_path`, `changed_paths`, `remaining_obligations`, `diagnostic`.
   A written distillation returns PAGE_READY with `needs-ingest: true` and
   the stub tag removed; it is not a SUCCESS until the parent finishes the
   remaining work. A suspected duplicate returns its proposed canonical
   target without deleting or renaming another page.

4. **Read back every returned item, including reported failures.** Wait for
   the wave's consolidated result before inspecting shared state. Resolve
   the actual page path from the return record; if a report is absent after
   a provider error, inspect the assigned path before retrying. Missing files,
   malformed frontmatter, wrong identities, or partial bodies are failures,
   not successful summaries. A missing original alone is not proof of merge.

   Apply the canonical completed-page checks in paper-ingest Phase 10, using
   `verify_ingest.py <bare-slug> --instance <brain> --require-filled
   --page-only` for the intermediate. Verify the page against source evidence:
   identity, complete individual authors, substantive body sections, and
   enrichment provenance must agree. Explicit null DOI and collective-only
   empty authors are evidence-backed exceptions defined there; do not restore
   the old unconditional nonempty-DOI/nonempty-authors gate.

   Parse `cited_by` from YAML, not a fixed grep context window. Preserve all
   snapshot entries in order and any valid concurrent additions. For a merge,
   preserve the union with the canonical page and repair inbound references
   before deleting the duplicate. Every citing entry is a paper/grant, not a
   concept/project relevance edge. Never repair source identifiers solely
   from agreement between two worker summaries; check the canonical records.

   If a provider failed after a complete page write, the same verification
   can establish PAGE_READY; do not re-run extraction merely because its final
   summary is missing. If an incomplete page was incorrectly marked false,
   retain/restore `needs-ingest: true`, record the diagnostic, and continue
   accounting for the other entries. Inspect existing Ingest-log counters
   before adding a parent diagnostic so one attempt is not counted twice.

5. **Complete parent-owned wiring and final verification.** For each
   PAGE_READY item, perform paper-ingest Phases 7–9: verify source-linked
   bibliography candidates and decide anchor stubs, resolve/write every author citation
   using `paper-ingest/references/author-ledger-mutation.md`, and finish
   graph links plus the propagation packet. Parent-owned merges use the
   canonical path throughout; no shared file is edited by an in-flight leaf.

   Set `needs-ingest: false` only after those obligations are satisfied, then
   run full `verify_ingest.py --require-filled` without `--page-only` and
   scoped schema lint. If completion checks fail, keep the item queued and
   report the remaining obligation. A valid abstract-only fill can succeed
   with `needs-enrichment: true`; do not repeatedly requeue it as a failure.

   The propagation packet is owned by paper-ingest Phase 9, not a second
   independent append recipe here. Dedup its ID and use `event: stub-filled`
   for a filled queued page. Existing files do not appear in an added-files
   Git scan, so omitting this packet loses the fill event. Close the verified
   unit through git-ops; required wiring, not wave size, defines completion.

6. **Final report.** When the queue is drained (or every remaining stub
   has been deliberately skipped), produce a single summary:

   ```
   ingest-pending-papers — run summary

   Queue size at start:        N stubs
   Successfully ingested:      X
   Failed (logged on page):    Y
   Skipped (prior terminal):   Z
   Held (identity/retraction): H
   Deferred (not attempted):   D
   Merged input items:         M
   Distinct verified pages:    P

   Failures:
     - papers/<slug-1> — phase 1 (resolve identity): CrossRef returned no
       match; PubMed lookup also failed. Suggest manual DOI.
     - papers/<slug-2> — parent wiring incomplete; remains queued.
       State the exact unfinished obligation and canonical output path.

   Skipped:
     - papers/<slug-3> — last attempt 2026-05-15 logged "DOI 10.x/y
       unresolvable; no record in CrossRef, PubMed, or bioRxiv. Likely
       malformed citation in the source grant." Suggest manual
       intervention.
   ```

   Account for every original input exactly once across verified fills,
   verified merges, failures, holds, skips, and deferrals; compute counts
   programmatically. Distinct output pages are counted separately from
   processed inputs. Report canonical paths and remaining obligations.
   Page/ledger/graph changes and propagation are the persistent output;
   report local-only commits separately from verified publication.

## Anti-patterns

- **Halting the queue on a single failure.** A bad DOI on stub #3 should
  not block stubs #4 through #N. `paper-ingest` logs the failure on the
  per-paper page; this skill reports it in the summary and moves on.
- **Reimplementing the stub-fill logic here.** This skill is an
  orchestrator. The actual work of filling a stub — DOI resolution,
  abstract extraction, body distillation, `cited_by` preservation,
  `needs-ingest` flip, `## Ingest log` append — belongs to `paper-ingest`.
  This skill calls it; it does not duplicate it.
- **Retrying a stub that previously failed with a terminal diagnostic.**
  The `## Ingest log` on the stub records why a prior run gave up. Read
  it; skip the stub and note the skip in the report; don't burn cycles
  on a known-broken DOI.
- **Rewriting citation history during a fill or merge.** The parent may
  perform the canonical merge procedure, but cannot discard prior citing
  edges or invent citations from topic relevance.
- **Changing delegation model settings to rescue a drain.** Model policy is
  user-owned; provider failures do not justify new pins or cheaper models.
- **Skipping Phase 4 verification.** Worker reports are self-reports;
  verify the artifacts and source evidence before counting completion.
- **Ignoring the current runtime schema or ceiling.** Follow batch-drain
  and account for rejected dispatches explicitly; no silently lost items.

## Running this skill — kickoff and monitoring

The user-facing kickoff prompt and the tool-stream monitoring signals live
in `references/kickoff-and-monitoring.md`. Load that reference when the
human invokes the drain from chat or asks how to verify a running drain;
the orchestrator itself does not load it.

## Procedure-change verification

Apply skill-hygiene’s read-back and representative-run gate. Capture validation
output without live delivery; exercise parent completion in an isolated copy
rather than running an unbounded production drain as a maintenance test.
