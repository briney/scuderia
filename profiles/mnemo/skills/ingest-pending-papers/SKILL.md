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

# Drain queued papers through manuscript-to-page ingestion

Load `skills/paper-ingest/SKILL.md` and its runtime reference. This skill owns
selection and accounting, not a second scientific acceptance protocol. Use only
`paper_ingest` start, sources, read, stage, publish and status. Supplementary
files are retained without routine processing. Full receipts and machine state
stay outside the brain; pages retain a compact remote archive locator.

Read `skills/conventions/paper-stubs.md`, `skills/batch-drain/SKILL.md` and
`skills/git-ops/SKILL.md`. Use current tool schemas and the configured child
ceiling; never change model pins or approval settings to rescue a run. Verify
parent and worker discovery of `paper_ingest` before dispatch. Missing deployment
is a hold, not a reason to use an older workflow.

## Selection and identity

For an ordinary queue run, use the named scanner with the configured PDF Python:

```sh
"<pdf-python>" "<profile>/tools/manuscript_ingest/campaign.py" scan-queue --instance "<brain>" --output "<existing-external-parent>/new-queue.json"
```

Read the output's `items` and `diagnostics`, paging through all records. Selection
uses parsed YAML `needs-ingest: true`, not prose matches or a truncated content
search. Diagnose malformed metadata explicitly. The scanner orders by citing
edges, then path. Freeze the selected paths for this run and account for every
one. A campaign or user-supplied explicit selection does not authorize draining
the rest of the ordinary queue or setting all old pages' queue flags.

Inspect prior access/identity failures before dispatch. A persistent blocker is
skipped with its reason; do not blindly repeat an unsuccessful request. Check
source identity with the existing `validate_identifiers.py --batch ... --recover`
helper on the selected group and `dedup_check.py --instance <brain> ... --json`.
Resolve candidates and heuristic HOLDs against primary records. A matching DOI
does not excuse a wrong title or PMID. Preserve literal source citations and
verified no-DOI or collective-only exceptions; do not fabricate identifiers or
individual authors to fit a helper. Surface retractions and unresolved identity
for explicit disposition. If the runtime cannot represent a verified identity,
report that limitation rather than bypassing it.

Deduplication and renames belong to the parent under paper-ingest Phase 2.
Keep every original input mapped to its canonical page; repair inbound links and
preserve citation/provenance unions before deleting a confirmed duplicate.

For a frozen legacy-paper refresh, load `references/corpus-refresh.md`. Its
explicit selection replaces ordinary queue scanning for that invocation.

## Worker and parent ownership

Prefer one isolated stage-only worker per paper. Give it the selected path,
verified identity, original citation/provenance, existing job ID when available,
and unique external work location. The worker acquires and reads the manuscript, drafts a
fresh source-grounded page, checks central claims and stages it. It does not
publish, mutate shared author/graph/inbox files, merge pages, or use Git.
Return job ID, revision and artifact paths plus concise remaining obligations.
Treat the return as a helpful report, not a required perfect output schema.

Use batch-drain's wave/yield discipline. Do not emit another wave while workers
are in flight. Inline work is allowed when delegation is unavailable or the
work is small, with the same ownership and completion requirements. Never load
historical extraction recipes into a worker to explain the new workflow.

## Read-back, publication and completion

1. Read back every item, including provider errors and missing summaries. Check
   `status` for the existing job and inspect its returned artifacts before
   restarting anything. A failed final message does not undo successful work.
2. A PAGE_READY report means an external staged draft, not a filled live page.
   Read its draft, review note, source evidence and current runtime state. The
   existing live page may correctly be unchanged. Preserve valid citing edges,
   provenance and concurrent additions. No summary or schema establishes truth.
3. The primary checks identity, complete authors, central findings, consequential
   numbers and material limitations against selected manuscript evidence. Do not
   duplicate the worker's full read or restart drafting for integration fixes. Missing optional
   citations or subjective emphasis differences are not new acceptance gates.
   Unavailable essential manuscript content is a needs-input/access outcome;
   do not declare an abstract-only result a completed manuscript ingest.
4. The parent calls `publish` on the reviewed revision. The runtime verifies the
   external archive before guarded page application. Complete paper-ingest
   Phases 7–9: bibliography decisions, author/graph wiring and one deduplicated
   propagation event. Source-backed identity corrections never rely solely on
   agreement between worker summaries. Workers do not perform shared writes.
5. Call `publish` again after integration as needed. Only runtime `complete`
   establishes completed ingestion; integration-pending is unfinished work.
   The runtime owns needs-ingest transitions. Use paper-ingest Phase 10's current
   page verifier with its external article manifest and publication receipt.
   Run the frontmatter linter before vault publication. Do not copy artifacts
   or receipts into the brain, and do not use obsolete handoff flags.
6. On storage or integration failure, retain the same job and completed source
   work. Resume the named missing step; never restart extraction for a failed
   push or missing worker summary. Preserve source failures and attempt history
   without counting a skip or duplicate diagnostic as another attempt.

The parent closes coherent verified work through git-ops under repository
permission. Preserve unrelated edits/staging, verify remote publication, and
report complete-but-unpublished units separately. A batch boundary alone does
not establish that its changes form a complete commit.

## Reporting and monitoring

Report the original input count and each item's canonical path/outcome: completed,
merged, blocked, failed or deferred. Distinct verified output pages are a separate
count. Preserve all remainder items and outstanding integration or Git obligations.
A missing original file alone is not proof of a successful merge.

`references/kickoff-and-monitoring.md` contains user-facing kickoff/monitoring
examples. For procedural changes, follow the profile's skill-hygiene convention:
read back affected callers and exercise changed deterministic behavior with
isolated fixtures; never use an unbounded production drain as a maintenance test.
