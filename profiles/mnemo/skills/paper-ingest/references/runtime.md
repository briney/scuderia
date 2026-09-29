# Manuscript ingestion runtime

Capability: manuscript-to-page. Hermes tool: `paper_ingest`.
The six operations are fixed; there is no nested command or processing mode.

| Operation | Inputs | Result |
|---|---|---|
| start | absolute paper page, optional resolved identity | opaque job ID; explicit title correction before staging reuses that job |
| sources | job ID, optional acquired inputs | retained source index; omitted inputs reuse archive |
| read | job ID, explicit source/page locations; optional inspection question or full-page transcription | bounded text or observation with partial/missing status |
| stage | job ID, Markdown, short source-review note, optional live snapshot token | revision, draft, factual-check findings, page blockers and deferred graph work; live page unchanged |
| publish | job ID and revision | preflight, archive read-back, guarded application, propagation and completion status |
| status | job ID | current state and next action; no dispatch |


A verified title-only correction before staging uses `start` again with the same
page and `identity: {"title": "Verified publication title"}`. The runtime retains
sources/reads, records old and new titles in external history, and still checks
canonical identity before publication. Identifiers/version cannot change, and a
title correction after staging begins is a hold. Never edit job JSON or its index;
never inspect or modify implementation files to bypass a rejected operation.

Acquired input rows use `path`, `role` (manuscript/body/supplement), and for manuscript
or body, `identity` (matching DOI/PMID/version) and a source-backed `basis`.
Optional `pages` limits a composite to verified manuscript physical pages.
Location rows use `source_id`, one-based `page`, optional `start_char` and
`max_chars` (up to 32000). At most eight locations per text read, four per inspection.
An inspection question consumes deployment-owned budget; callers cannot grant it.
A focused answer never counts as reading the whole page. For one deficient page,
`read` with `transcribe: true` requests full-page text through the same bounded
transport (mutually exclusive with `question`). A partial response remains partial;
readable native pages still require full text delivery. No automatic transcription
sweep or retry occurs.
Do not process supplements or recreate work directories after failed requests.

Every result has job_id, status, next_action, artifacts, warnings and blocking_reason.
States are working, needs-input, ready, publication-pending, integration-pending,
complete or held. Follow partial-text continuation. A warning alone is not a hold.

On a concurrent page edit, status/publish returns `artifacts.live_snapshot` with
an external snapshot path and opaque token. Read and reconcile that snapshot;
stage the revised candidate with the token as `base_revision`. A later edit makes
the token stale: check status again. Keep the same job and source/request history.
Supplying replacement source inputs still verifies and retains the prior archive
history; it does not reset earlier qualifications or correction provenance.

Runtime code is `<profile>/tools/manuscript_ingest/`, outside skill discovery.
The configured external runtime directory owns `config.json`, jobs and one shared
SQLite request ledger. The ordinary tool does not accept runtime, archive, model,
budget or authorization overrides. Use the configured Python 3.11+ environment
with existing PyMuPDF, Pillow and PyYAML. No dependency installation during ingestion.

The equivalent fixed CLI reads the same operation JSON from stdin:

    PYTHONPATH=<profile>/tools <pdf-python> -B -m manuscript_ingest.cli --runtime-root <configured-external-runtime>

Deploy only the `manuscript-ingest` native plugin, with operator settings tools_root,
runtime_root and python. Remove obsolete plugin registrations and console executors
at cutover; refresh actual loaded discovery at an idle boundary. Always set
HERMES_HOME explicitly for noninteractive trials. Retain existing unfinished jobs and immutable sources on their bound runtime.
Restage retained annotated drafts when adopting the fresh-page policy; do not
regenerate manuscripts merely to update the completion path.
Archive old runtime/config outside active skill/plugin discovery for offline rollback.
A failed cutover suspends new ingestion rather than reactivating exhaustive execution.

## Lightweight source locators

Text reads include raw `text`, `numbered_text`, and the retained `text_sha256`.
Character windows and `next_start` always count raw text characters; a continued
line retains its original line number. Prefix P/L positions refer to the current
source; unqualified draft `[P4:L12-L15]` markers name the selected manuscript.
For body aliases, qualify with the returned source ID:
`[s-<24-hex-digits>/P1:L2-L5]`. Single-line, grouped and cross-page ranges work.

Stage returns a clean draft plus external `annotated_draft` and `citations` paths.
The archive keeps `annotated-page.md` and `citations.json`, with code-retrieved
quotations bound to source text and draft/final page hashes. Invalid locators are
retained as unresolved evidence and removed from the clean page with warnings.
Absence of markers is a warning only. Locators do not certify factual support or
complete coverage, and do not cause new model requests. The independent factual
review is separate from deterministic publication checks.

## Archive receipt storage

`stage` assigns a compact remote `Article archive: r2://...` locator. `publish`
archives the full receipt in R2 and checks readback before applying the page.
Its returned `receipt` path is external working metadata; do not copy it into
the brain. Ordinary refresh resolves the locator through deployment-owned
archive settings and restores metadata and sources outside the instance.
Historical local receipts remain readable. Old unpublished drafts containing
local receipt filenames must be staged again within their existing job before
publication; retain existing sources and completed inspections.

## Frozen refresh campaigns

The external `campaign.py` CLI selects and reconciles existing jobs; it never
replaces these operations. `status` after a missing model summary, retained
sources, staged drafts and publication/integration artifacts support recovery.
Campaign completion additionally requires manuscript reading and matching final
page/archive evidence. Git publication is tracked separately. Resolve canonical
path corrections before `start`; never silently change a job's bound slug.
See `skills/ingest-pending-papers/references/corpus-refresh.md` for bounded runs.

### File-based staging

For substantial drafts, write the annotated Markdown to an external UTF-8 file
using the file-writing capability, then call `stage` with `markdown_path`, the
same `job_id`, and a short `review_note`. Supply exactly one of `markdown_path`
and inline `markdown`. The runtime reads the file and preserves its annotated
bytes; the live page remains untouched. Paths inside the brain, symlinks and
nonregular files are refused. The existing 2,000,000-character draft limit
applies; this is a transport boundary, not a model output token cap.

If a nested tool wrapper rejects JSON, use the file-path argument or the CLI
operation file immediately. Do not regenerate or shorten scientific content to
repair a serialization error.

### Amend a published page

For a small correction, keep the existing job and sources. Call `status`, read
its `live_snapshot.path` and the retained `annotated_draft`, and reconcile the
change there. Stage with `amend_revision` equal to the current published revision
and `base_revision` equal to that snapshot's opaque token. Publish the returned
new revision. An unchanged manuscript does not need another full read.

Edit the annotated draft, not the clean live page: preserve unchanged locators
and update or remove locators on changed claims. If an earlier restage lost
locators, recover the previous annotated revision; do not attach old citations
to new prose by positional guesswork. Prior archives remain immutable. A failed
upload leaves the old page intact; retry the new revision without regeneration.
An independent live edit requires a fresh snapshot and explicit reconciliation.
Complete metadata/link decisions before publication where possible. Never repair
archive equality by silently overwriting a human edit or mutating an archive.

Canonical identity checks use a per-job external `identity-cache` of successful
raw source responses, bound to their request URL and checksum, with a one-day
reuse window. When using `validate_identifiers.py` during acquisition, pass
`--identity-cache <job-work>/identity-cache` to share that evidence with final
publication. Cache reuse reruns comparisons against the current page; it never
turns a contradictory record into a pass. PubMed transient failures can use a
matching Europe PMC MED record with its complete author list.

A transient metadata outage leaves the same revision integration-pending with
`metadata-temporarily-unavailable`. End the attempt and return its job/revision;
retry publication during a later authorized run. Do not redraft, change identity,
start another job or wait through repeated model-authored sleep loops. A missing
record and a contradictory record remain different from service unavailability.

## Deterministic publication and factual checking

`integration_obligations` contains page/identity blockers only. `graph_follow_up`
contains deferred author associations/reverse edges and missing targets. Publication
does not require those repairs; the existing propagation event carries them forward.
No integration model is dispatched. The page retains complete source `author_names`
independently of verified `authors` graph links. `cited_by` is reconstructed from
explicit `cites` fields on other paper/grant pages, never from the old summary.

Configure `factual_check` in the operator-owned external runtime config with `model`,
`endpoint`, `credential_env`, `timeout_seconds` and `settings` (including the chosen
output cap). Use an independent fast model. No tool call can override these settings.
Stage sends one complete manuscript plus fresh annotated draft to the existing
single-POST text transport, with no images or tools. Its fixed prompt requests only
objective errors, exact claims/source passages and minimal corrections. The external
`factual-check/` artifacts retain the input binding, sanitized response and outcome.
Publication archives them. Missing configuration or a failed/partial request is
reported as an incomplete check; no automatic retry or clean verdict.

A returned finding report makes the first revision `factual-review-pending`.
The worker assesses the report against the manuscript, then stages once more with
corrections or a reasoned disposition in `review_note`; the checker does not run
again. Unresolved consequential claims use normal HOLD lines. Publication cannot
bypass the unassessed first revision. Amendments remain possible without re-reading
or rechecking the whole paper, with their own focused source review.

`source_retention` reports manuscript formats, supplementary file count and known
gaps. Attachment completeness is not certified by scientific-page completion.
All attempted-source notes remain external; successful XML reading is not evidence
that a manuscript PDF or every advertised supplement was archived.

Wrapped locator groups are accepted. Keep abstract quotations unchanged and place
locators outside that protected section. Optional locator warnings remain nonblocking.
Fresh pages have no Ingest log. Normal drafting never reads original.md, page.diff,
or sibling pages; snapshots and diffs remain available for recovery/operator audit.
