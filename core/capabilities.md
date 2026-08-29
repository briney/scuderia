# Convention: capabilities — the harness-agnostic tool contract

Skills name **capabilities**, not tools. A capability is a named contract
(input shape, output shape, error behavior); the harness binds each one to
a real tool. The same skill runs under any harness that provides the
capabilities it names; degrades gracefully or refuses cleanly when a
capability is unavailable.

Authoritative source: `docs/north-star/DESIGN.md` §5 (capability tiers)
and §6 (the harness seam). The per-harness mapping lives in
`docs/harnesses/`.

## Why named capabilities

Two reasons. **Portability** — a skill that says "shell out to `qmd
query`" is locked to Hermes; one that says "uses `brain-search`" runs
under any harness that provides a brain-search binding (qmd, ripgrep,
a future engine). **Honesty about degradation** — a skill that names
`gmail-read` makes its harness-dependency explicit, so a session under
Claude Code (no Gmail integration) refuses cleanly instead of
fabricating.

This rule is **engineering hygiene, not iron law** (`DESIGN.md` §5).
Where binding to a specific tool's rich surface makes the skill
meaningfully better, bind directly and document the coupling.

## The capability list

### Universal — present in any reasonable harness

| Capability | Contract |
|---|---|
| `fetch-url` | HTTP GET/POST against a URL; returns body + status. Wraps the harness's HTTP client. |
| `read-file` | Read a file from the filesystem; returns text or bytes. |
| `write-file` | Write a file to the filesystem; creates parent directories as needed. |
| `edit-file` | In-place edit of an existing file (find-and-replace semantics). |
| `spawn-subagent` | Run a delegated agent in an isolated context; receive its final report. |
| `brain-search` | Hybrid (semantic + keyword) search over the brain; returns ranked matches. Reference implementation: qmd under Hermes. Substitute: `grep` + `find` over the markdown corpus where qmd is absent (degrades — no semantic ranking, no reranker). |
| `brain-read` | Read a brain page by `<kind-dir>/<slug>` (resolves to `<kind-dir>/<slug>.md`). Wraps `read-file`. |
| `brain-write` | Write or create a brain page by `<kind-dir>/<slug>`. Wraps `write-file` and `edit-file`. Honors the "never blind-overwrite" rule (`SOUL.md` §2). |

### Scheduling and delivery

| Capability | Contract |
|---|---|
| `schedule-job` | Schedule a job to run on a cron-like cadence (e.g., "every 10m", "daily at 7am"). Hermes: native `hermes cron`. Claude Code: closest analog is the CronCreate tool when available, or external cron with the session ferried by a one-shot driver. |
| `send-notification` | Push a message to the user out-of-band (Telegram, etc.). Hermes: messaging gateway. Claude Code: not provided — the session is the channel. |
| `deliver-message` | Push a composed artifact (a brief, a nudge) on a scheduled cadence. Built on `schedule-job` + `send-notification`. Hermes-only at present. |

### Open-API research — all bound to `fetch-url`

| Capability | Contract |
|---|---|
| `pubmed-fetch` | Fetch PubMed records (E-utilities). Documented in the skill that uses it; no auth. |
| `crossref-fetch` | Fetch CrossRef metadata. No auth. |
| `biorxiv-fetch` | Fetch bioRxiv/medRxiv records. No auth. Metadata + abstract only (`api.biorxiv.org`); preprint full text is Cloudflare-blocked on `www.biorxiv.org` — get it via `conventions/preprint-retrieval.md` (Europe PMC). |
| `arxiv-fetch` | Fetch arXiv records. No auth. |
| `nih-reporter-fetch` | Fetch NIH RePORTER records. No auth. |

These are skill-level conveniences, not capabilities the harness has to
provide separately — any harness with `fetch-url` has them by
construction. They are listed so skills can declare the dependency by
name.

### User-model — markdown reads, present everywhere

| Capability | Contract |
|---|---|
| `user-model-query` | Returns the agent's model of its human: `{declared: USER/<name>.md}`. Same shape on every harness — `USER/<name>.md` lives in the instance's `USER/` directory and is read off disk. See the platform `DESIGN.md` §8 and the reference binding in `profiles/mnemo/DESIGN.md` §7. |
| `read-conversation-history` | Returns recent session transcripts (windowed by the caller). Consumed by `user-model-reflect` on manual invocation. Hermes: native session store. Claude Code: transcript files under `~/.claude/projects/<encoded-cwd>/*.jsonl` (one JSONL per session; user/assistant records carry `message.content` plus `timestamp` and `sessionId`). Skills that name it as required refuse cleanly on harnesses that don't expose conversation history. |

### Authenticated / infrastructural — Hermes-only unless the harness wires equivalents

| Capability | Contract |
|---|---|
| `gmail-read` | Read your human's research mail. Hermes: Spark IPC bridge. Not provided under Claude Code. |
| `calendar-read` | Read your human's calendar. Hermes: Spark IPC. Not provided under Claude Code. |
| `messaging-send` | Send a Telegram/Discord/etc. message. Hermes: messaging gateway. Not provided under Claude Code. |
| `raw-source-archive-upload` | Upload a binary to R2 and return a content-addressed pointer (`conventions/raw-source-archive.md`). Hermes: `rclone copyto` to the configured R2 remote. Claude Code: requires rclone + R2 creds on the host; available via Bash, configured per host. |
| `voice-transcribe` | Transcribe an audio file. Hermes: native voice pipeline. Not provided under Claude Code. |

### Inter-agent collaboration — see `core/agora.md` (DRAFT)

| Capability | Contract |
|---|---|
| `agent-message` | Send a message to a sibling agent (another instance on the same host); receive its reply asynchronously. Hermes: Bot Chat (`hermes -p <profile> chat --in ~ -c "Bot Chat" --create-if-missing -Q -q "…"`), reply on stdout. Claude Code: not provided. |
| `agora-deposit` | Create a bundle or artifact directory in the shared store under the agora write rules (temp-then-rename; write-once; manifest last). Wraps `write-file`; adds the rules. Requires `AGORA_ROOT` configured per host. |
| `agora-resolve` | Resolve an `agora://` URI to a local path under `AGORA_ROOT`; for artifacts, check readiness (manifest present) before reading. Wraps `read-file`; adds URI resolution + the readiness check. |

## The per-harness matrix

Each harness's adapter doc carries the authoritative table for that
harness; this section is the cross-harness summary. `docs/harnesses/`
holds the per-harness detail (binding, error behavior, install
prerequisites).

| Capability | Hermes | Claude Code |
|---|---|---|
| `fetch-url` | ✓ | ✓ (WebFetch / Bash + curl) |
| `read-file` / `write-file` / `edit-file` | ✓ | ✓ (Read / Write / Edit) |
| `spawn-subagent` | ✓ | ✓ (Agent) |
| `brain-search` | ✓ (qmd) | ⚠ (Grep + Glob — no ranking) |
| `brain-read` / `brain-write` | ✓ | ✓ |
| `schedule-job` | ✓ (`hermes cron`) | ⚠ (CronCreate when available; ScheduleWakeup for in-conversation pacing) |
| `send-notification` | ✓ (Telegram gateway) | ✗ |
| `deliver-message` | ✓ | ✗ |
| Open-API research (`*-fetch`) | ✓ | ✓ |
| `user-model-query` | ✓ | ✓ |
| `read-conversation-history` | ✓ (native session store) | ✓ (transcript files under `~/.claude/projects/<encoded-cwd>/*.jsonl`) |
| `gmail-read` / `calendar-read` | ✓ (Spark IPC) | ✗ |
| `messaging-send` | ✓ | ✗ |
| `raw-source-archive-upload` | ✓ (rclone+R2) | ⚠ (available if host has rclone+R2 configured) |
| `voice-transcribe` | ✓ | ✗ |
| `agent-message` | ✓ (Bot Chat) | ✗ |
| `agora-deposit` / `agora-resolve` | ✓ (filesystem + `AGORA_ROOT`) | ⚠ (filesystem, if a shared store is configured) |

Legend: ✓ provided; ⚠ degraded substitute or conditionally available;
✗ not provided.

## Substitution rules

When a capability has a documented substitute, a skill that names it as
**optional** can run under the degraded mode and note the reduced
fidelity in its output. A skill that names it as **required** refuses
cleanly when the capability is absent — it never fabricates a result.

The standard substitutions:

- `brain-search` → `grep -r` + `find` over the page-kind directories.
  Loses semantic ranking and reranking; keyword recall remains.
- `schedule-job` → none (a skill that requires recurring scheduling
  refuses cleanly under a harness that lacks it; the session can
  emulate one-shot scheduling via `ScheduleWakeup`-style mechanisms
  but that does not satisfy `schedule-job`'s recurring contract).
- `read-conversation-history` → none. A skill that requires it refuses
  cleanly under harnesses that don't expose conversation history.
  `user-model-reflect` writes a dated no-op stub to
  `USER/OBSERVATIONS.md` so the absence is auditable rather than
  silent.

## How a skill names its capabilities

A skill's body carries a `## Capabilities` section near the top. The
short form is one line:

```markdown
## Capabilities

`brain-read`, `brain-write`, `fetch-url`
```

The fuller form distinguishes required from optional:

```markdown
## Capabilities

- **Required:** `brain-read`, `brain-write`, `user-model-query`
- **Optional:** `brain-search` (falls back to keyword scan)
- **Hermes-only:** `gmail-read` — under Claude Code this skill refuses
  cleanly with a stub report.
```

Skills that only use universal capabilities (read/write/fetch/spawn,
brain-read/write) may omit the `Hermes-only` line. The section is for
discovery and refusal logic, not for restating what the skill body
already explains.

## Adding a new capability or harness

A new capability is added here first, with its contract; then bound by
each harness's adapter doc; then the skills that need it cite it.

A new harness is added by writing a new `docs/harnesses/<name>.md`
that mirrors `hermes.md`'s structure: capability-by-capability
binding, error behavior, install prerequisites. The matrix above gains
a column.
