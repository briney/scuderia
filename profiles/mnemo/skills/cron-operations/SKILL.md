---
name: cron-operations
description: Use when scheduled jobs fail or stop delivering. Diagnose model resolution, delivery, and execution against the installed runtime.
triggers:
  - "cronjob failed"
  - "cron job error"
  - "rem-cycle failed"
  - "meeting sync failed"
  - "why did the scheduled job fail"
  - "the cron isn't delivering"
  - a scheduled job reporting last_status=error
eval_contract:
  goal: |
    Diagnose and remediate scheduled-job failures at the operational layer —
    model resolution, delivery, execution — without breaking live state.
  dimensions:
    - "DIAGNOSIS_FROM_EVIDENCE — the failed run's ## Error block is read before any hypothesis; current runtime/docs checked before remediation"
    - "STATE_SAFETY — jobs.json edits take the .jobs.lock flock and write atomically; live firing only per the incremental-validation rule"
    - "POLICY_RESPECT — preserve the user's model-selection policy; do not re-pin jobs or re-enable a disabled guard"
  hard_fails:
    - Hand-editing jobs.json without the flock or outside the documented shape.
    - Live-firing a graph-mutating job off-schedule just to test.
    - Treating a version-scoped failure mechanism as timeless.
---

# cron-operations — operating and troubleshooting the instance's cron jobs

The instance runs a fleet of scheduled cron jobs: the rem-cycle tiers (nightly /
weekly / monthly), the Granola meeting sync, the standing scans
(monitor-the-situation, funding-sweep), and the no_agent script jobs
(feed-refresh, qmd-reindex, drop-watcher). When one fails, the failure is almost
never in the job's *content* skill (rem-cycle, granola-meeting-sync) — it is in
the cron *operational* layer: model resolution, delivery, or the environment.
This skill is that operational layer. The content skills are loaded by the job;
this is what you load to fix the *job*.

> The cron state lives in `~/.hermes/profiles/<instance>/cron/jobs.json`
> (`{"jobs": [...]}`), per-run output under `cron/output/<job_id>/<timestamp>.md`
> (a FAILED run's file ends with an `## Error` block — read it first), and the
> scheduler code is in the Hermes install at
> `~/.hermes/hermes-agent/cron/{jobs.py,scheduler.py}`.

## The first move on any failure

1. `cronjob action=list` — find the failing job's `job_id` and confirm
   `last_status: "error"`. Note which jobs failed vs. succeeded *today* — the
   contrast is the fastest diagnostic (see the drift guard below: jobs created
   at different times behave differently).
2. Read the failed run's output file:
   `cron/output/<job_id>/<latest>.md`. The `## Error` block at the bottom is
   the verbatim exception. Do not guess — the message names the cause and often
   the exact fix command.
3. Classify: **model-selection** (drift guard), **delivery** (send failed but
   the run itself was `ok`), or **execution** (the agent errored mid-run). The
   three have completely different fixes.

## Failure mode 1 — model-selection drift guard (#44585)

**Symptom (as observed on the Hermes runtime this skill was written against,
2026-08):** `RuntimeError: Skipped to prevent unintended spend: global
inference config drifted since this job was created (model 'X' -> 'Y'), and
this job is unpinned. No inference call was made.`

**Mechanism — version-dependent; read the installed runtime before acting.**
When a job is created, `create_job` snapshots the model/provider an
*unpinned* job would resolve to at that moment, into
`provider_snapshot` / `model_snapshot` in jobs.json. What happens at fire
time has changed across Hermes versions:

- **Older runtimes:** the guard in `scheduler.py` compares the current
  global default against the snapshot; if an unpinned axis drifted, it
  **fails closed** — zero inference, a loud alert (the symptom above).
- **Current runtimes:** the snapshot is the unpinned axis's *effective pin*
  (`_snapshot_pin` in `scheduler.py`) — a drifted job keeps running on the
  model it was created under, logging one INFO line, and
  `cron.model_drift_guard` no longer exists (config migration 41→42 removes
  it). Resolution at fire time is per-job pin → `cron.model` fleet default
  → creation snapshot → global default; the docs
  (https://hermes-agent.nousresearch.com/docs/user-guide/features/cron)
  describe the snapshot-as-effective-pin behavior.

Check which behavior applies before remediating: read the installed
scheduler (`~/.hermes/hermes-agent/cron/scheduler.py`, search
`_snapshot_pin` / `model_drift_guard`) and the current cron docs. Never
assume the fail-closed symptom is still the failure mode on an updated
runtime. `no_agent` script jobs carry no snapshot and are exempt. Pinned
jobs (explicit `model`/`provider`) are exempt.

**Why some jobs fail and others don't the same morning (older runtimes):**
the guard keys on the snapshot, which is captured at *creation* time. A
job created while one model was the default snapshots that model; a job
created after a backstop became default snapshots the other. Swap the
default and only the first class fails. `cronjob action=update`
re-snapshots an unpinned axis **only when an inference axis value actually
changes** (`inference_fields_changed`).

**Three remediations — pick by intent, they are NOT equivalent** (historical,
pre-2026-08-14 policy; the standing policy below supersedes all three, and
on current runtimes the snapshot is a pin to *clear or set*, not a
failure to clear):

- **Pin** (`cronjob action=update job_id=... provider=<p> model=<m>`): runs now,
  but pinned = no longer follows the default at all. You must manually repin when
  the situation reverses. Least resilient; the *opposite* of "swap-proof."
- **Re-snapshot** (any inference-field update rewrites the snapshot to current):
  passes now, but re-breaks on the next swap in the other direction. Kicks the can.
- **Clear the snapshots** (null both `provider_snapshot` and `model_snapshot` in
  jobs.json): the back-compat path means a snapshot-less job never
  engages the old guard — it follows the global default **in either direction**.
  On current runtimes this follows the global default only when per-job
  pins and cron-fleet overrides are also absent. Clearing a snapshot opts
  the job into subsequent global-default changes; do so only under the
  user's standing policy or explicit authorization.

**Standing policy for this workflow:** the drift-guard behavior is DISABLED profile-wide on the
runtime where it was a config option — `cron.model_drift_guard: false` in
that profile's config.yaml (only the literal YAML boolean `false` disables
it; set via direct YAML surgery, not `hermes config set`, per the
hermes-config-editing skill). The intended end state holds on every runtime
version: agent jobs follow the global default. Verify per-job model/provider
pins and snapshots are null and no cron-fleet override changes that resolution.
The user accepts the spend risk of changing the global default. Removing the
old guard option does not establish this end state: newer runtimes still
create snapshots. Check actual resolution when creating or editing jobs;
do not change existing overrides without authorization.
**Do not "fix" a future model change by re-pinning jobs or re-enabling a
guard.** If inference config looks drifted, that is the intended state.

**Validate incrementally** (your human's standing preference): clear + live-fire
*one* light/idempotent job first (`cronjob action=run <job_id>`; confirm
`execution_success: true` and — critically — that inference actually ran, vs.
the earlier "No inference call was made"), then apply to the rest. Do **not**
live-fire graph-mutating jobs (rem-cycle) off-schedule just to test — they share
the identical guard code path, so a clean run on a light job proves the fix.

## Failure mode 2 — delivery failure (run ok, send failed)

**Symptom:** `last_status: "ok"` but `last_delivery_error` is set, e.g.
`Telegram send failed: ... [SSL: CERTIFICATE_VERIFY_FAILED] ... Hostname
mismatch, certificate is not valid for 'api.telegram.org'`.

**This is not a gateway bug.** If a *prior* alert delivered fine and a later one
didn't, delivery broke due to a **network-state change on your human's machine**, not
Hermes. On a filtered institutional network, `api.telegram.org` may be **DNS-sinkholed** to the
institutional block page: it resolves via CNAME chain to the institution's block hosts
(e.g. `blocked.<institution>.edu → web02.<institution>.edu → <internal-ip>`), serving a `*.<institution>.edu` cert — hence
the "hostname mismatch." Public resolvers (1.1.1.1, 8.8.8.8) are also walled off
(queries time out), so you can't escape by switching resolvers. The machine's
resolver is Tailscale MagicDNS (100.100.100.100) falling back to the institution's
resolvers (172.29.40.10/.9).

**The block is DNS-only — the IPs are reachable.** Confirm with a resolve
override: `curl --resolve api.telegram.org:443:149.154.167.220 https://api.telegram.org/`
returns HTTP 302 with a clean TLS handshake. Since only DNS is poisoned, the fix
is a static `/etc/hosts` pin (needs sudo):

```
149.154.167.220  api.telegram.org
```

This overrides only that one hostname, leaving all other (legitimate) institutional
DNS intact. Back up /etc/hosts first, flush the cache
(`dscacheutil -flushcache; sudo killall -HUP mDNSResponder`), then verify
resolution returns the real IP and a live `cronjob action=run` on a
Telegram-delivering job clears with `last_delivery_error: null`. Caveat: the pin
is static — if Telegram retires that IP (rare, stable for years) re-pin to a
current one. The full account is an instance-private record and diagnostic
transcript.

## Failure mode 3 — execution error mid-run

The agent started (inference ran) but errored during the job. Read the full
output file, not just the `## Error` block — the transcript above it shows how
far it got. Common causes: a content-skill bug, an MCP token expiry (granola),
a turn/iteration limit (rem-cycle — see that skill's own notes on turn budgets),
or a genuine tool failure. Fix in the *content* skill, not here.

## Editing jobs.json safely

Never hand-edit jobs.json without the lock. `load_jobs` reads fresh from disk
every call, so a lock-respecting edit is picked up on the next tick — but a
concurrent ticker write (drop-watcher fires every 1 minute) can tear an
unlocked write. Take the `.jobs.lock` flock (`~/.hermes/profiles/<instance>/cron/.jobs.lock`),
preserve `{"jobs": [...]}` and all other top-level fields. Prefer the current
`cronjob` tool or `hermes cron edit` for supported changes; inspect their
schema/help and the installed `cron/jobs.py` before use.

For an authorized field not exposed by those interfaces: acquire the profile's
`.jobs.lock` flock, read the current file while holding it, select exact job
IDs, and change only the approved fields. Preserve every unrelated value and
write a temporary file in the same directory, then replace jobs.json atomically
with `os.replace` before releasing the lock. Re-read the exact jobs and confirm
the intended delta. Abort if the lock cannot be acquired. A protection refusal
is not permission to use direct-file editing as a workaround.

## Anti-patterns

- Assuming a cron failure is a Hermes/gateway bug before reading the `## Error`
  block — it almost always names the exact cause and fix.
- Pinning a job to the current backstop model to "fix" a drift-guard skip —
  that freezes it on the paid model and re-breaks the resilience your human asked
  for. Clear the snapshot instead for maintenance jobs.
- Re-snapshotting to the current default and calling it resilient — it re-fails
  on the next swap in the other direction.
- Hand-editing jobs.json without the `.jobs.lock` flock — races the ticker.
- Live-firing a graph-mutating job (rem-cycle) off-schedule just to test a
  fix — it commits real changes; validate on a light idempotent job that shares
  the same code path.
- Diagnosing a delivery failure as a gateway problem when a prior alert
  delivered fine — the change is in the network path, not Hermes.
- Treating the Telegram DNS block as a cert problem — the cert mismatch is a
  *symptom* of the DNS sinkhole; fixing "the cert" is impossible and wrong.
