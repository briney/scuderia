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
  goal: Drain queued papers with verified per-item outcomes and deterministic publication and deferred graph maintenance.
  dimensions:
    - "ACCOUNTING — every original input has a verified outcome and canonical path"
    - "ISOLATION — workers fill assigned pages; runtime serializes publication and propagation"
    - "VERIFICATION — source-backed exceptions and completed-page checks agree with paper-ingest"
    - "RECOVERY — incomplete work stays queued and provider errors do not erase completed writes"
  hard_fails:
    - Counting a child report or PAGE_READY result as a completed ingest without durable runtime publication evidence.
    - Requeueing a valid fill solely because a verified DOI is absent or authorship is collective-only.
    - Losing original queue items, overwriting concurrent edits, or misreporting source gaps.
---

# Drain queued papers through manuscript-to-page ingestion

Load current `paper-ingest` and its runtime reference. This skill owns selection
and accounting, not another scientific acceptance protocol. Use only start,
sources, read, stage, publish and status. Never load historical exhaustive recipes.

For ordinary queues, run the configured PDF Python with
`<profile>/tools/manuscript_ingest/campaign.py scan-queue --instance <brain>`.
For an explicitly authorized corpus refresh, use `references/corpus-refresh.md`.
Freeze the selected inputs and validate identity/dedup before dispatch; a selected
existing target is not a duplicate to delete. Stubs outside the selection and new
bibliography candidates remain outside the run. Source-backed renames/merges require
inbound-link repair and retained original snapshots before removing a page.

Use one isolated worker per paper, within the configured native concurrency ceiling.
Each worker reads only its verified sources, current template and identity seed.
It must not read legacy/sibling pages or reconcile old metadata and manual notes.
It acquires the complete manuscript, retains supplements without processing, drafts,
checks central facts and assesses the one independent factual report if configured.
It stages only; no shared graph edits, nested delegation, Git or publication.
Return job/revision and concise observations, not a rigid output schema.

Read durable job status after every worker, including missing final summaries or
provider errors. Already-staged work is retained. The campaign publishes ready
revisions serially through runtime code, even if another worker failed. There is
no integration agent, second broad review, bibliography walk or graph repair on
the critical path. Standalone queue orchestration likewise calls publish directly.
An unassessed factual report or material HOLD stays with that paper.

Publication verifies retained archive bytes, protects against concurrent edits,
checks canonical identity, records propagation once and clears the queue flag.
Author associations and missing graph targets remain explicit follow-up; they are
not proof of an incomplete scientific page. A metadata/archive outage defers the
same revision without redrafting or sleep loops. A missing full manuscript is an
access hold, never abstract-only success. Complete source author names are required;
uncertain person identities must not be guessed to make a graph check pass.

Keep sources, review artifacts, receipts, hashes and transient diagnostics outside
the brain. Pages carry science and one remote archive locator, no Ingest log or
sidecars. Report manuscript formats and attachment gaps separately from page status.

The parent runs frontmatter lint once and closes owned changes with git-ops under
repository authorization, preserving unrelated edits. Campaign publication does not
commit or push. Report every original input, distinct completed pages, failed/held
items, deferred graph/attachment work and complete-but-unpublished changes. A failed
Git push does not restart ingestion. Do not expand a bounded pilot into a bulk drain.
