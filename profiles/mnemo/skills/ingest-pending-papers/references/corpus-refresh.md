# Refresh a frozen corpus

This is selection and recovery around `paper-ingest`, not another scientific
workflow. Load the current `paper-ingest` and runtime reference. Use only its six
operations. Do not load historical extraction instructions. The ordinary stub
queue and newly discovered bibliography papers remain outside this selection.

## Replacement contract

Write fresh from the complete selected manuscript, not from the old summary.
Retain supplements without processing. Reuse an existing archive with `sources`
without inputs first; acquire verified missing originals only as needed. An
abstract-only result or unavailable essential manuscript is an access hold.
Leave the old page intact until a valid replacement is archived and ready.

Keep the filename. Replace legacy prose and metadata wholesale, including manual
annotations; Git history and external original snapshots provide recovery. Workers
and factual checkers never read the legacy page, diff or sibling pages. Runtime
rebuilds citing edges from explicit citation fields elsewhere. Concurrent edits
still hold publication for explicit reconciliation; this policy does not authorize
overwriting edits made after the job starts.

Resolve identity and dedup before `start`, which binds the existing filename and
identity. A worker proposes a correction/merge; only the parent verifies it and
uses paper-ingest Phase 2 and the shared paper-stubs convention to preserve the
union of provenance/citations and repair inbound links. Do not rebind a job to a
new slug. A campaign `map` records a reviewed migration after it is finished; it
does not perform one. Before any merge/delete, retain the original bytes as
`<campaign>/originals/<item-id>.md`; map requires its frozen hash to match. A blocked correction does not stop other papers.

Workers read, draft, check central claims and assess the one configured independent
factual report, then stage. The campaign invokes deterministic publication directly.
No integration model, preservation review or shared graph repair is dispatched.
Deferred graph work travels with the existing propagation event. Missing summaries
are recovered from durable jobs; do not regenerate sources or drafts.

## External inventory and execution

Use the configured PDF Python and `<profile>/tools/manuscript_ingest/campaign.py`:

```sh
<pdf-python> <campaign.py> init --root <new-external-campaign> --instance <brain>
<pdf-python> <campaign.py> report --root <campaign>
<pdf-python> <campaign.py> reconcile --root <campaign> --runtime-root <runtime>
```

`inventory.json` freezes every original path/hash/identity, priority and archive
candidate; `state.json` records outcomes. Tagged stubs are counted separately,
malformed or unresolved identities are explicit exceptions. Do not edit inventory
or mass-toggle page flags. An archive pointer is only a candidate until matching
current runtime/archive/page evidence establishes completion. Legacy archives are
reusable originals, not proof of the current minimum standard.

Prepare an external `run-config.json` with:

- `hermes_command`: installed Hermes argv prefix, e.g. `["/absolute/bin/hermes"]`;
- `hermes_python`, `hermes_repo`: installed Hermes environment and source checkout
  for native cron controls; no credentials;
- `selection`: reviewed inventory item IDs, in execution order;
- `exclusive_window_until`: timezone-aware ISO end of an operator-confirmed quiet
  window. No interactive ingestion, manual page edits, other primary, or script
  writer may overlap. This is an operational reservation, not an automatic lock
  on Obsidian or every possible external writer;
- `git_closeout`: `hold-for-review` for a pilot, or `publish` after authorization.

Implementation approval does not authorize a pilot or bulk model calls. Present
named papers, bounds, annotation/rename issues and this controlled window first.
Once a run is authorized, use:

```sh
<pdf-python> <campaign.py> run --root <campaign> --runtime-root <runtime> --profile-home <hermes-profile> --limit 5 --concurrency 2 --max-seconds 7200
```

The launcher verifies idle gateway state and pauses enabled agent cron jobs in
that profile for the controlled window, keeping an external recovery snapshot.
This includes the ordinary queue and avoids another scheduled shared writer.
Jobs already paused remain paused; overdue jobs restore to their next future
slot, with no catch-up. Do not start interactive work during the window. Script
jobs remain under the operator's quiet-window check. A crash leaves a recovery
marker; another run restores scheduling and stops for inspection before admitting
new work. An orphaned coordinator retains the inherited process locks.

Each bounded wave launches per-paper noninteractive workers directly, with actual
process concurrency limited by the configured ceiling. The coordinator then
publishes ready jobs serially through runtime code, even after a sibling failure. Every worker has an external query/log; publication outcomes are recorded separately.
Before admission, the configured Hermes interpreter imports its actual model/client
stack once; a broken installation holds the run before workers start. A
wall-time deadline stops new waves, not an in-flight write. Native request/turn
limits and model pins remain unchanged. No monetary token optimization or new
output cap is introduced. A provider/coordinator failure or archive outage stops
new admissions; item-specific access holds leave the remainder eligible.

Workers own acquisition and manuscript generation. Shared institutional browser
acquisition remains a separate serial access task; a worker records the route and
needs-input hold rather than handing it to an integration agent. Ready jobs skip
worker generation entirely. Metadata outages defer the same publication revision.

Report worker overlap, worker/publication wall time and per-job timestamps. The
factual check is part of staging; its external evidence records its own duration.
Observer review and Git closeout are separate. Do not infer phase durations from
overlapping milestones. Report attachment gaps independently of scientific status.

After a run, reconcile and inspect `runs/*/observations.md`, logs and runtime
artifacts. Use these named commands only after reviewing the specific issue:

```sh
<pdf-python> <campaign.py> retry --root <campaign> --item <id> --reason '<reviewed resolution; what changed>'
<pdf-python> <campaign.py> map --root <campaign> --item <id> --canonical <existing-page> --reason '<source-backed correction and link repair>'
```

Retry accepts the current page hash; it never
clears runtime concurrency holds by itself. Reconcile a live edit through stage
with its snapshot token first. No recursive retries. A missing job after a
reservation is interrupted work, not a disappeared input. Resume unpublished
content through publication/Git, not another ingestion. Complete content and
page commit/push evidence are separate in reports; git-ops still verifies the
whole coherent unit, including shared edits. Remote queries use the configured
upstream without changing Git history.

Report every frozen input, distinct outputs, verified current exclusions,
exceptions, remaining integration and unpublished content. Wave wall time and
published papers/hour are measured; do not invent per-stage durations when the
underlying runtime did not record them. Review a five-paper pilot before its Git
closeout, then seek authorization for the measured 25-paper tranche. Later bulk
bounds follow measured full-pipeline throughput, not drafting-only timing.
