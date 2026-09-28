# Manuscript ingestion runtime

Capability: manuscript-to-page. Hermes tool: `paper_ingest`.
The six operations are fixed; there is no nested command or processing mode.

| Operation | Inputs | Result |
|---|---|---|
| start | absolute paper page, optional resolved identity | opaque job ID |
| sources | job ID, optional acquired inputs | retained source index; omitted inputs reuse archive |
| read | job ID, explicit source/page locations; optional inspection question or full-page transcription | bounded text or observation with partial/missing status |
| stage | job ID, Markdown, short source-review note, optional live snapshot token | revision, draft and diff; live page unchanged |
| publish | job ID and revision | archive read-back, guarded application and integration status |
| status | job ID | current state and next action; no dispatch |

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
HERMES_HOME explicitly for noninteractive trials. Hold existing unfinished jobs on
their bound runtime; never reinterpret their state with this replacement.
Archive old runtime/config outside active skill/plugin discovery for offline rollback.
A failed cutover suspends new ingestion rather than reactivating exhaustive execution.
