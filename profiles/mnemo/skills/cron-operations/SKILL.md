---
name: cron-operations
description: Diagnose and remediate the instance's scheduled cron jobs when they fail — the model-selection drift guard that skips unpinned jobs after a default-model swap, delivery failures (e.g. a messaging API DNS-sinkholed by an institutional network), and the general "why did this job fail this morning" diagnostic path. Use when a cron job reports last_status=error, stops delivering, or your human asks to investigate a scheduled-job failure.
triggers:
  - "cronjob failed"
  - "cron job error"
  - "rem-cycle failed"
  - "meeting sync failed"
  - "why did the scheduled job fail"
  - "the cron isn't delivering"
  - a scheduled job reporting last_status=error
---

# cron-operations — operating and troubleshooting the instance's cron jobs

The instance runs a fleet of scheduled cron jobs: the rem-cycle tiers (nightly /
weekly / monthly), the Granola meeting sync, the standing scans
(monitor-the-situation, funding-sweep), and the no_agent script jobs
(auto-push, qmd-reindex, drop-watcher). When one fails, the failure is almost
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

**Symptom:** `RuntimeError: Skipped to prevent unintended spend: global
inference config drifted since this job was created (model 'X' -> 'Y'), and
this job is unpinned. No inference call was made.`

**Mechanism (this is a Hermes feature, not a bug):** when a job is created,
`create_job` snapshots the model/provider an *unpinned* job would resolve to at
that moment, into `provider_snapshot` / `model_snapshot` in jobs.json. At fire
time, the guard in `scheduler.py` compares the current default against the
snapshot; if an unpinned axis drifted, it **fails closed** — zero inference, a
loud alert. The point is to stop an unpinned job silently switching to a pricier
model (e.g. a free local default → a paid backstop). `no_agent` script jobs
carry no snapshot and are exempt. Pinned jobs (explicit `model`/`provider`) are
exempt.

**Why some jobs fail and others don't the same morning:** the guard keys on the
snapshot, which is captured at *creation* time. A job created while GLM was the
default snapshots `glm-5.2`; a job created after the Opus backstop became
default snapshots `claude-opus-4-8`. Swap the default and only the first class
fails. `cronjob action=update` re-snapshots an unpinned axis **only when an
inference axis value actually changes** (`inference_fields_changed`).

**Three remediations — pick by intent, they are NOT equivalent** (historical,
pre-2026-08-14 policy; the standing policy below supersedes all three):

- **Pin** (`cronjob action=update job_id=... provider=<p> model=<m>`): runs now,
  but pinned = no longer follows the default at all. You must manually repin when
  the situation reverses. Least resilient; the *opposite* of "swap-proof."
- **Re-snapshot** (any inference-field update rewrites the snapshot to current):
  passes now, but re-breaks on the next swap in the other direction. Kicks the can.
- **Clear the snapshots** (null both `provider_snapshot` and `model_snapshot` in
  jobs.json): the guard's back-compat path means a snapshot-less job never
  engages the guard — it follows the global default **in either direction**.
  This is the only option that survives arbitrary future swaps. Cost: those jobs
  permanently opt out of the spend guard.

**Standing policy (Bryan, 2026-08-14, superseding the same-day pin-to-local
guidance):** the guard is DISABLED profile-wide — `cron.model_drift_guard:
false` in this profile's config.yaml (only the literal YAML boolean `false`
disables it; set via direct YAML surgery, not `hermes config set`, per the
hermes-config-editing skill). All agent jobs are unpinned (`model`/`provider`
null) and all `*_snapshot` fields are nulled, so every job follows the global
default model and a default swap never blocks the fleet. Bryan accepts the
spend risk explicitly: ending up on a paid model after a default swap is his
deliberate decision, not something to guard against. **Do not "fix" a future
model change by re-pinning jobs or re-enabling the guard.** If inference
config looks drifted, that is the intended state.

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
current one. (The full account is an instance-private record.)
diagnostic transcript.

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
preserve the `{"jobs": [...]}` top-level shape (a bare list triggers
auto-repair), write atomically (tmp + `os.replace`), release. The
`scripts/clear_cron_snapshot.py` helper does exactly this for the drift-guard
remediation and is the template for any other field edit.

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
