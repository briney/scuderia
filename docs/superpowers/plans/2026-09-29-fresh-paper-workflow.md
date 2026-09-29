# Fresh paper workflow implementation plan

Use executing-plans for inline implementation. Approved design: generate fresh
manuscript-derived pages at stable filenames, without legacy content reconciliation;
replace model-driven integration with deterministic publication and deferred graph work.

## Constraints

Sources, receipts and recovery snapshots remain external. Preserve manuscript
identity, complete reading, immutable revisions, archive readback, material scientific
holds, concurrent-edit guards and deduplicated propagation. No new dependencies,
exhaustive extraction, model output cap reduction, or production corpus writes.
Complete author names are source metadata; person associations are separate graph work.

## Tasks

- [x] Runtime: remove inherited content/metadata gates; separate graph follow-up from
  publication blockers; regenerate citation backlinks from actual citation fields;
  accept complete author_names independently of verified authors links; drop Ingest log.
  Verify malformed legacy metadata replacement, identity failures, graph deferral,
  concurrent edits, archive failure and event idempotency.
- [x] Scientific check: one configured text-only independent check per job, free-text
  findings, one worker assessment/correction stage, no automatic retries. Reuse transport
  and external request ledger. Preserve XML table rows/headers and clean locator output.
  Verify truncated/failing responses, request reuse, evidence binding and table layout.
- [x] Campaign: serial deterministic publication of ready jobs even after sibling failure;
  actual Hermes import preflight before workers; existing locks/window/recovery retained.
  Verify no integration model dispatch, isolated failures and interrupted recovery.
- [x] Acquisition/instructions: bounded validated attachment routes, explicit archive gaps;
  current skills/template/conventions consistently describe fresh generation and deferred
  graph work. Read back affected callers; exercise helper and verifier suites.
- [x] Review and validate isolated retained-job replay plus fresh bounded scientific sample;
  report timing and correctness separately. No automatic production rollout or bulk drain.

## Execution ledger

Baseline: 93 runtime tests pass on merged main. Work occurs in an isolated worktree.

Runtime regression cases: malformed old metadata is replaceable, actual citation
edges are reconstructed, graph obligations defer, Ingest log is optional, XML tables
retain columns. Factual checker returns free text and cannot be automatically retried;
first report requires assessment before publication. Campaign directly publishes
ready siblings on nonzero exit and process-launch exception.

Whole-branch review: corrected launch-exception handling and included source-bound
scanned-page transcriptions (both reproduced RED then GREEN). Updated authoritative
graph convention to match deferred associations; this is required consistency, not
optional polish. No reviewer findings deferred.

Standalone replay exposed canonical verifier imports relying on caller PYTHONPATH;
added its repository tools path and a standalone import regression (RED then GREEN).
104 runtime tests and 85 verifier tests pass; seven acquisition helper tests pass.
Verifier tests use TMPDIR=/private/tmp to avoid the system /var symlink in historical
archive fixtures. Live validation remains isolated; publication is not deployment.


Final isolated validation: three retained drafts replayed and four fresh items
published (one fresh worker stopped before creating a job and needed an explicit
recovery using its retained PDF). Initial results remain separate from post-run
repairs; there were no hidden automatic manuscript restarts. Publication took
26–53 seconds per fresh item, without an integration model. Acquisition/drafting
remain the dominant and variable cost. One independent check timed out; successful
checks caught objective errors but also missed known errors. They are observations,
not correctness certificates.

Observed runtime fixes: stacked locator removal; current-revision citation warnings;
default empty graph lists; omitted invalid optional importance rather than inventing
a score; implied supplement role in the supplement-only operation; canonical
candidate identity verification before page application, with a second live-edit
check afterward. Regression cases reproduced failures before fixes. Existing draft
amendments exercised real archive readback without repeating manuscript generation.

Final verification: 109 runtime tests, 86 verifier tests, seven acquisition tests;
skill-check covers 82 skills without collisions. Isolated final pages pass scoped
frontmatter lint; missing graph targets in the deliberately sparse fixture remain
warnings. Active instructions were read back and stale author-maintenance phase
references removed. Implementation remains on its local branch; production deployment
and bulk corpus processing are outside this validation.
