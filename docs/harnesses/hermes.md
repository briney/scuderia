# Hermes — capability adapter

Hermes is the **reference harness** for scuderia. It is fat (not thin) by
design — it ships its own scheduler, MCP-client support, messaging
gateways, voice transcription, and an embedded search index (qmd). When
Hermes loads the instance content + character + skills, it becomes the
agent (`DESIGN.md` §6).

The install runbook is **[`SETUP.md`](../../SETUP.md) at the root** — this
file is the *capability mapping*, not the install procedure. They are
complements: SETUP.md says how to set up the binding; this doc says what
each capability resolves to once it's set up.

## The binding (one-liners; SETUP.md has the prose)

- **Character:** `~/.hermes/profiles/<instance>/SOUL.md` symlinks to the
  instance's SOUL.md. (If that target ever goes missing, the gateway
  regenerates a default 513-byte stub — stop the gateway before moving
  character files.)
- **Skills:** one symlinked category per layer under
  `~/.hermes/profiles/<instance>/skills/`: core layer →
  `<scuderia>/core/skills`; template layer → `<scuderia>/profiles/<profile>/skills`;
  instance layer → `<instance>/skills`. Instance overrides template
  overrides core by skill name.
- **Conventions:** reachable as `skills/conventions/…` — the template skills
  dir carries a `conventions` symlink to the profile's conventions. An
  optional host overlay (`<instance>/skills/conventions`, git+sync ignored)
  makes the same path resolve from the brain root as cwd.
- **cwd:** `terminal.cwd` (config.yaml) and `MESSAGING_CWD` (.env) both
  point at the brain root. Interactive `hermes chat` inherits the invoking
  shell's cwd.

## Capability bindings

| Capability | Bound to | Notes |
|---|---|---|
| `fetch-url` | Native Hermes HTTP client | Standard; auth handled per-skill where needed |
| `read-file` / `write-file` / `edit-file` | Native filesystem | Honors the "never blind-overwrite" rule (`SOUL.md` §2) |
| `spawn-subagent` | `delegate_task` | Subagent inherits the parent's model (see `SOUL.md` §2 carve-out for paper-ingest queue drain) |
| `brain-search` | **qmd** (HTTP MCP server) | Hybrid vector + keyword + reranker; runs as a daemon (see Install) |
| `brain-read` / `brain-write` | Filesystem via cwd = vault root | `terminal.cwd` / `MESSAGING_CWD` point at the vault |
| `schedule-job` | `hermes cron` | Cron-cadence strings (`"every 10m"`, `"daily at 7am"`); `--no-agent` for shell-only jobs |
| `send-notification` | Telegram gateway | Other channels (Discord, Signal, email, voice) also available |
| `deliver-message` | `schedule-job` + `send-notification` | The standard pattern for the morning brief, deadline nudges |
| `pubmed-fetch` / `crossref-fetch` / `biorxiv-fetch` / `arxiv-fetch` / `nih-reporter-fetch` | Skill markdown + `fetch-url` | No SDKs; API knowledge lives in skill prose |
| `user-model-query` | Filesystem read of `USER/<name>.md` | Returns `{declared}`; `USER/<name>.md` is the entire user model the mind consults in conversation |
| `read-conversation-history` | Hermes session store | Returns windowed transcripts; consumed by `user-model-reflect` on manual invocation |
| `gmail-read` / `calendar-read` | Spark IPC bridge (`spark-cli`) | Read-only; Spark Desktop runs on the host; no OAuth against Google directly |
| `messaging-send` | Telegram (or whichever gateway is configured) | The reverse of `send-notification` for outbound from skills |
| `raw-source-archive-upload` | **`rclone copyto`** to Cloudflare R2 | Configured per host; see `conventions/raw-source-archive.md` |
| `voice-transcribe` | Native voice pipeline | Audio in, transcript out; the original goes to R2 |
| `agent-message` | **Bot Chat** | `hermes -p <profile> chat --in ~ -c "Bot Chat" --create-if-missing -Q -q "Message from <instance>: …"`; run backgrounded, reply arrives on stdout. Verified working 2026-08-24 (round-trip ~1 min) |
| `agora-deposit` / `agora-resolve` | Filesystem under `AGORA_ROOT` | `AGORA_ROOT` set in the profile's `.env` (absolute path — the agent shell's HOME is shimmed; quote paths containing spaces). Reference substrate: Dropbox folder pinned available-offline |

## Error behavior

- **`brain-search` lag.** qmd does not auto-reindex; a freshly written
  page is searchable only after the next `qmd embed` (cron, default 10m).
  Skills that write-then-immediately-query must read the page directly,
  not re-query. The `paper-ingest` queue drain documents this pitfall.
- **`raw-source-archive-upload` round-trip.** Always verify via
  `rclone lsf` before deleting from `_drop/`; a silent upload failure
  plus a confident `rm` is how raw sources go missing. Always pass
  `--timeout` and `--contimeout` on every `rclone` call.
- **`schedule-job` semantics.** `hermes cron create "10m"` schedules a
  **one-shot** job. Use `"every 10m"` for recurring. `--script` requires
  a bare filename relative to `~/.hermes/scripts/`, not an absolute path.
- **`spawn-subagent` model selection.** Delegated subagents inherit the
  parent's model (no per-task model selection today). Until that lands,
  the `SOUL.md` §2 "delegate under oversight" carve-out is the only
  sanctioned delegation pattern.
- **`agora-*` on a cloud-drive File Provider root.** During the sync
  client's first-run/initial indexing, directory *listing* under the
  provider root can block for minutes while `stat` and writes still
  succeed. Let initial sync settle (or exclude everything but the agora
  via selective sync) before assuming a broken store. Online-only
  placeholder files look present but fail on open — keep the agora
  pinned available-offline on agent hosts.
- **`agent-message` requires the target profile to be configured.** A
  profile with a model but no provider fails with "Provider resolver
  returned an empty base URL." Check `model.provider` in the target's
  config.yaml before diagnosing the transport.

## Install prerequisites

The full runbook is in [`SETUP.md`](../../SETUP.md). The capability-level
summary:

| Capability | Requires |
|---|---|
| `brain-search` | qmd installed; `qmd embed` run; HTTP MCP daemon (LaunchAgent or systemd) |
| `raw-source-archive-upload` | `rclone` installed; R2 remote configured (object-scoped token, `no_check_bucket = true`); `bucket = <instance>-drops` (or your equivalent) |
| `user-model-query` | Nothing — filesystem read of `USER/<name>.md` in the brain's `USER/` dir |
| `gmail-read` / `calendar-read` | Spark Desktop running on the host; `spark-cli` shim available |
| `send-notification` / `messaging-send` | Bot token + `TELEGRAM_ALLOWED_USERS` in `.env`; `hermes gateway` running as a service |
| `voice-transcribe` | Whatever voice provider is configured in `.env` |
| `agent-message` | Target profile created (`hermes profile create`) with a working `model.provider` |
| `agora-deposit` / `agora-resolve` | Shared synced folder (e.g. Dropbox) reachable by all agents; `AGORA_ROOT` (absolute) in each profile's `.env`; folder pinned available-offline on agent hosts |

## Skill availability summary

**Fully supported (all clusters):**
- Thought-partner: `query`, `academic-verify`, `literature-research`,
  `concept-synthesis`.
- Grant-writing: `grant-plan`, `grant-section`, `grant-coherence`,
  `grant-citations`, `grant-finalize`, `grant-ingest`.
- Brain-building: `ingest`, `paper-ingest`, `ingest-pending-papers`,
  `idea-ingest`, `media-ingest`, `meeting-ingestion`,
  `voice-note-ingest`, `enrich`, `restructure-thin-page`, `maintain`,
  `frontmatter-guard`, `citation-fixer`.
- Always-on: `brain-ops`, `signal-detector`.
- Meta: `skill-creator`, `ask-user`, `migrate`.

**Research-logistics (Hermes-only by nature):**
- `briefing`, `daily-task-prep`, `daily-task-manager` — all depend on
  `gmail-read` / `calendar-read` / `send-notification`.

## Harness-specific behaviors and gotchas

These are runbook nuggets carried forward from the (deleted)
`template-vault-sync` skill — the contents that survived the brain-merge
collapse and still matter under Hermes:

- **`vault-auto-push` cron snapshots content paths only.** The
  `~/.hermes/profiles/<instance>/scripts/auto_push.sh` cron stages and
  commits only content paths (page dirs + program state + rem-cycle
  runtime state); body work is hand-committed. It has no merge-marker
  guard — if a botched merge leaves `<<<<<<<` inside a *content* file, the
  snapshot will carry it. Pause it before any rebase / manual-merge work:
  `cronjob action=pause job_id=<vault-auto-push>`, and always resume
  after — the rem-cycle gates it via a lock file, not scheduler pauses.
- **The agent's `HOME` is shimmed.** Inside an agent session, `$HOME`
  points at `~/.hermes/profiles/<instance>/home/`, not the real home. `git`,
  `gh`, `rclone`, and anything else that reads config from `$HOME` will
  fail to find credentials. Prefix the command:
  `HOME=<real-home> git push origin main`. For rclone, set
  `RCLONE_CONFIG=<real-home>/.config/rclone/rclone.conf` once at
  session top.
- **Prompt-builder loads one project-context file from `cwd`.** Order is
  `.hermes.md` → `AGENTS.md` → `CLAUDE.md` → `.cursorrules`; first match
  wins, no fallback. The vault's `AGENTS.md` is what reaches the prompt;
  there is no second file loaded automatically. Anything host-specific a
  human or agent needs to know about the scuderia install belongs in
  `~/.hermes/profiles/<instance>/INTEGRATION.md` and must be loaded
  explicitly.
- **qmd token is object-scoped, not bucket-scoped.** `rclone lsd
  `<instance>-r2:` returns HTTP 403 (it tries `ListBuckets`, which the token
  doesn't grant). That is normal and not a sign of broken credentials.
  Test connectivity with a round-trip into a specific key, never with
  `lsd` at the bucket root.

## See also

- [`SETUP.md`](../../SETUP.md) — the install runbook
- [`../../skills/conventions/capabilities.md`](../../skills/conventions/capabilities.md) — the capability contract
- [`../../skills/conventions/raw-source-archive.md`](../../skills/conventions/raw-source-archive.md) — the R2 + rclone convention (Hermes-flavored; the capability is harness-agnostic, the implementation is Hermes-specific)
- [`../north-star/DESIGN.md`](../north-star/DESIGN.md) §6 — the harness seam
