# Paper-ingest runtime

The canonical runtime is this skill's resolved, absolute `scripts/` directory.
It contains `pdf_source_package`, `pdf_enrichment`, `qualified_enrichment`, their
assets, `entry.py`, `operate.py`, the adapters, and the native plugin sources.
Use a nonsymlink path. Inputs, jobs, receipts, model caches and private regression
fixtures live outside the skill. Historical experiment trees are not import roots.

## Deployment

Use the instance's PDF Python interpreter (Python >=3.11) with the dependency
versions pinned in `scripts/pyproject.toml`. For an existing environment with
those versions, install the source checkout without resolving/upgrading dependencies:

    <pdf-python> -m pip install --no-deps --no-build-isolation -e <scripts>

This is a source-checkout deployment: retain the complete scripts tree, including
`entry.py`, `operate.py` and the plugin directories. The editable installation
provides `pdf-source-package` and `pdf-workflow`; it is not a portable wheel
containing the adapters or harness configuration.

For portable operations, explicitly set all three trusted roots to that same path:

    export PDF_ENRICHMENT_METHOD=<scripts>
    export REENRICH_ENRICHMENT_ROOT=<scripts>
    export REENRICH_INTEGRATION_ROOT=<scripts>
    export PYTHONDONTWRITEBYTECODE=1

Set `REENRICH_PROCESSOR_CACHE` (or `PDF_PROCESSOR_CACHE`) in the launching
harness environment to the instance's accepted local processor cache. Initial
continuations resolve this environment setting; without it, sealing returns
`processor_cache` as a missing input. Verify inheritance in a fresh process.
Never take executable paths or credentials from archived evidence.

The Hermes binding installs the reviewed `scripts/paper-workflow/` and
`scripts/paper-enrichment/` plugin sources into the active profile's plugins
location. Preserve other plugins and their settings. Configure:

| Plugin | Settings |
|---|---|
| paper-workflow | `method_dir: <scripts>`, `python: <pdf-python>` |
| paper-enrichment | `integration_dir`, `enrichment_root`, `method_dir`, `adapter_dir`: all `<scripts>`; `python: <pdf-python>` |

The independent visual-inspection capability uses `scripts/paper-vision/`.
Copy its `__init__.py`, `client.py`, `cli.py`, `plugin.yaml` and `prompt.txt` into
`plugins/paper-vision/`, preserving the instance-owned `recipe.json` already there.
That recipe pins the approved endpoint, credential variable name, settings and
request limits. It stays outside the public skill; it is not replaced by test
configuration. A fresh installation requires an explicitly reviewed instance
recipe before invocation. The synthetic recipe under `tests/paper_vision/` is
only for offline tests. No route/model change or paid inspection is implied.

Before changing settings, identify active or resumable jobs. Finish them with
their bound implementation or explicitly hold them; do not rebind saved jobs or
retry uncertain requests. Retain the old configuration, plugin bytes and code
until cutover checks pass. Refresh the harness's loaded plugin registry at an
idle boundary; editing configuration does not change an already-loaded tool.
Check fresh native discovery and a bounded offline dispatch from the installed
profile. Rollback restores the prior settings/plugins and interpreter binding;
it never rewrites job records or approvals.

Standalone enrichment uses the same five settings in a trusted JSON file:

    <pdf-python> -B <scripts>/operate.py --deployment <deployment.json> --arguments <operation.json>

Follow `source-package-integration.md` for source preparation and the v4 source-evidence handoff,
then `qualified-enrichment.md` for new-ingest review/export and the v5 completion handoff.
Follow `portable-articles.md` for existing-article refresh. Operation/submission
schemas are in `qualified-enrichment-schema.md`. Native tools remain the normal
production route; these paths do not authorize spending or scientific approval.

## Operator continuations and detached execution

After identity resolution and dedup, before constructing source commands, use the configured `paper_enrichment` capability with
`operation: article` and `arguments: {command: route, article: <slug>,
page: <absolute-page>, work_root: <new-durable-dir>}`. Supply `manifest` when
available and `elements` only for an explicitly selected refresh. The route
persists its decision before drafting. An absent page or a genuine unfilled
`stub` with a citation uses initial ingestion; an ambiguous stub holds. A rich
page still uses refresh even if `needs-ingest` is true. A legacy text-only page uses refresh:
fresh source preparation, `adopt`, review, reconciliation, publication and
`reenrich.verify_completion`. Never substitute an initial-ingest finalizer.
The initial route writes `plan.json` and `acquisition.template.json`. Its exact
continuations cover retention, source phases, enrichment, batched review, final
products and publication. Fixed `initial-*` article commands adapt existing
operations; they do not authorize inference or scientific acceptance. Drafting
the page cannot change the saved route or final verifier. Attempt directories
are generated beside the work root, outside the retained source tree. Active or
uncertain workers return status, never replacement execution.
An explicit metadata-only request may stop at metadata; an ingestion/refresh request
may not be silently reduced to metadata work because a full page already exists.

Each native call needs a fresh external `attempt_dir`. Article status uses
`operation: article`, `arguments: {command: execute, work_root: ...}`.
Read `receipt.details.next_operation`: it contains the exact continuation,
available artifact paths and missing inputs. Missing scientific review and
approval remain operator work. Runtime roots come from configured deployment,
not copied environment assignments. The standalone `operate.py` accepts the
same argument object with the existing explicit deployment file.

For long operations, set `background: true`. The returned `attempt_dir` is the
durable job identifier. Reattach with `{operation: status, attempt_dir: ...}`;
request cancellation with `{operation: cancel, attempt_dir: ...}`. These two
controls take no other fields. A lost conversation or tool wait does not cancel
the worker. Repeating the identical background start attaches to that attempt;
changed arguments require a new attempt and do not overwrite it. A missing
terminal receipt is uncertain, never successful or permission to redispatch.
Cancellation retains request reservations; possibly sent requests remain
uncertain. Status/reattachment never approves or sends a model request.
Use this job-scoped status, not `pgrep`, counts of log lines or guessed `worker/`
paths. Prefer completion notifications; if polling is necessary, wait at most 30
seconds. Give the user a phase/completed-count/elapsed-time update at least once
per minute while interacting, and answer status questions promptly. A finished
worker advances via the returned article continuation; it is not a reason to sleep.

Use configured runtime/cache paths and the generated approval/packet templates.
Do not search old private runs to reconstruct configuration or copy their approvals.
For parser/runtime bugs, preserve the failed evidence and diagnose in an isolated
checkout under the Git rules. Never stash/pop unrelated edits, restore shared files,
or pipe a test command through a success-returning command that masks its exit.
Use verified downstream reuse when its code bindings match; a binding mismatch is
an explicit repair/migration hold, not permission to relabel old evidence or repeat
all model calls automatically.

Review packets are generated from the current dossier roster. Portable reviews
write `review/packets.json`; when split, pass its exact packet path as `packet`
on `review-import`. Oversized individual elements remain listed under
`source_inspection_required`, with a separate source-inspection packet requiring
an attributed usable-evidence assessment and source references. Do not invent
model results, truncate tables, copy old roster IDs or use an accidental empty
selection. Ordinary native review-packet rejects empty selections when the
dossier contains elements. Export derives completeness from the sealed dossier
and imported decisions; editing or removing the packet index cannot waive review.

Archive upload, read-back and manifest restore canonicalize their internally owned temporary
root; external source symlinks/hardlinks remain forbidden. No shell TMPDIR
workaround is required. Path failures identify the rejected component.

## Inference concurrency

Normal execution **omits `vlm_concurrency`** and inherits
`PAPER_INGEST_VLM_CONCURRENCY` from the launching environment. Three is only the
fallback when that variable is unset, not a value to copy into tool arguments.
Set an explicit positive-integer override only for intentional user/operator
instructions (CLI: `--vlm-concurrency`); it takes precedence over the environment.
Historical approvals, run logs and example values never establish current settings.
No model, prompt, token allowance, request budget or timeout changes are implied.

The worker records effective `vlm_concurrency` and `concurrency_source`
(`argument`, `environment`, `fallback`); native status exposes these after execution
starts. Check that record instead of assuming a caller's shell setting was inherited.
No unrelated environment values should be printed. Per-request reservations retain
settings for enrichment continuations, which may change the limit for never-sent
requests without retrying consumed requests. Phase boundaries and result processing
remain serial; a one-request phase cannot use additional slots.

A failure classified as shared by the executor stops new dispatch; already-dispatched calls are drained and
their results retained. A reservation remains consumed even if delivery or
response retention is uncertain; concurrency never authorizes a retry. Abrupt
process termination can still leave uncertain reservations requiring inspection.
Changing only the runtime limit does not require resealing prepared work; changing
executor code still requires the normal original-binding/idle-cutover discipline.

## Focused maintenance checks

From any working directory, the default synthetic subprocess controls need no
network, model cache, credentials or historical fixtures:

    <pdf-python> -B <scripts>/tests/run_tests.py

The visual inspector has a separate synthetic suite with transport doubles:

    <pdf-python> -B <scripts>/tests/run_tests.py --suite-dir <scripts>/tests/paper_vision

The grouped retained-record suites use an explicitly supplied external fixture
bundle (`manifest.json` plus the checked archives), never a historical run tree:

    PAPER_INGEST_FIXTURE_BUNDLE=<private-fixture-bundle> <pdf-python> -B <scripts>/tests/run_tests.py --suite-dir <scripts>/tests/pdf_enrichment
    PAPER_INGEST_FIXTURE_BUNDLE=<private-fixture-bundle> <pdf-python> -B <scripts>/tests/run_tests.py --suite-dir <scripts>/tests/qualified_enrichment

The runner verifies archive hashes, protects inputs, blocks network and creates
disposable outputs. Source-specific private regressions stay with the instance;
they may use the same external fixture corpus and this trusted runtime. Do not
copy their research content into the public skill. Exact local processor checks
and installed-harness checks are separate opt-ins, not a paid acceptance campaign.

## Timing and failed attempts

Keep every failed and replacement attempt until finalization. For article `publish`,
pass `source_attempts: [<source-package-dir>, ...]` and
`enrichment_attempts: [<earlier-enrichment-job>, ...]`. Initial finalization
automatically includes the current source package and enrichment job. Register
additional current-workflow attempts through `initial-record-attempt`; source
identity is checked. For standalone initial finalization, use repeatable
`final_products.py ingest --source-attempt <dir> --enrichment-attempt <dir>` flags.
Include reused forks as well as their originals. These are explicit registrations,
not a filesystem search: omitted attempts are outside the reported scope.

The final manifest/refresh receipt retains a `timing` snapshot after scratch cleanup.
Native completion output gives counts, token totals, overlapping request wall time
and summed request time separately. Detailed request timestamps and per-phase
settings stay in that external manifest, never in the paper page. Unknown legacy
values stay unknown; failed responses with no usage are counted as missing usage.
Refresh receipt intervals include operator wait. The snapshot ends before
publication; receipts record upload/read-back in a separate publication interval.
Initial operation intervals start at the saved routing decision. Per-phase status
reports planned, pending, successful, failed and uncertain counts plus effective
concurrency and its origin. Archive uploads use an independent bounded pool of
four; this is unrelated to VLM concurrency. The manifest is published last after
all objects verify; failure drains active uploads without scheduling more.
Timing is diagnostic and never satisfies a scientific acceptance or replay gate.
