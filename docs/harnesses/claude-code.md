# Claude Code — capability adapter

Claude Code is a **secondary supported harness** for soma. It provides a
clean universal substrate (file IO, fetch, subagents) plus brain operations
via Read/Write/Edit, and is excellent for thought-partner and grant-writing
work. It does **not** provide the integrations that the research-logistics
cluster depends on (Gmail, Calendar, messaging gateway, voice transcription);
those skills are unavailable or refuse cleanly under Claude Code. The
user-model layer is at full parity with Hermes — `USER/<name>.md` is a markdown
read off the brain root and is the entire user model the mind consults in
conversation.

The entry point is **`CLAUDE.md` at the brain root**, which Claude Code
auto-loads on session start. `CLAUDE.md` redirects to `AGENTS.md` for the
four-layer model and references this file for the capability mapping.

## Capability bindings

| Capability | Bound to | Notes |
|---|---|---|
| `fetch-url` | `WebFetch` (or `Bash` + `curl`) | WebFetch handles most cases; `curl` for anything with non-trivial auth |
| `read-file` / `write-file` / `edit-file` | `Read` / `Write` / `Edit` | First-class; Edit honors exact-string-match semantics |
| `spawn-subagent` | `Agent` | Subagents have full tool access; cost/context isolation |
| `brain-search` | ⚠ **Grep + Glob over the markdown corpus** | No qmd; no semantic ranking; no reranker. Keyword recall is good and case-insensitive is the default. Skills that name `brain-search` as optional fall back to this transparently; skills that name it as required refuse cleanly. |
| `brain-read` / `brain-write` | Filesystem; `Read` / `Write` / `Edit` on `.md` files | Identical surface to Hermes |
| `schedule-job` | ⚠ `CronCreate` (when surfaced as a deferred tool) | Not part of the always-on tool set; surfaces conditionally. `ScheduleWakeup` is available for in-conversation pacing in `/loop` mode but does **not** satisfy `schedule-job`'s recurring contract. |
| `send-notification` | ✗ | The session is the channel; there is no out-of-band push surface. Skills that need to notify your human asynchronously refuse cleanly. |
| `deliver-message` | ✗ | Depends on `send-notification`. |
| `pubmed-fetch` / `crossref-fetch` / `biorxiv-fetch` / `arxiv-fetch` / `nih-reporter-fetch` | Skill markdown + `WebFetch` | Same as Hermes — these are skill conveniences over `fetch-url` |
| `user-model-query` | Filesystem read of `USER/<name>.md` | Returns `{declared}` — same shape as Hermes. `USER/<name>.md` lives in the brain's `USER/` directory and is auto-loaded into context via the `CLAUDE.md` entry point. |
| `read-conversation-history` | Transcript files under `~/.claude/projects/<encoded-cwd>/*.jsonl` | One JSONL per session; each record carries `type`, `timestamp`, `sessionId`, and (for user/assistant turns) `message.content`. Consumed by `user-model-reflect` on manual invocation. |
| `gmail-read` / `calendar-read` | ✗ | No native Gmail/Calendar integration. The research-logistics cluster (`briefing`, `daily-task-prep`, `daily-task-manager`) is unavailable. |
| `messaging-send` | ✗ | No outbound channel from the session. |
| `raw-source-archive-upload` | ⚠ Available if host has `rclone` + R2 configured | Bash + `rclone copyto`; the convention in `conventions/raw-source-archive.md` works identically. Without rclone configured, the capability is unavailable and ingest skills refuse cleanly. |
| `voice-transcribe` | ✗ | No native audio pipeline. |

## Error behavior

- **`brain-search` substitute (Grep + Glob).** Returns keyword matches
  with no ranking. Skills that lean heavily on semantic search (e.g.,
  `literature-research`, `concept-synthesis`) work but with reduced
  recall on conceptually-adjacent material. Skills should phrase queries
  literally (the words a paper would use) rather than abstractly.
- **`spawn-subagent` cost.** Subagents are first-class but expensive.
  The `SOUL.md` §2 "delegate under oversight" carve-out still applies —
  delegate for context-isolation and for the paper-ingest queue drain;
  don't delegate first-contact ingest of new material.
- **`schedule-job` absent.** Skills that *require* scheduling (e.g.,
  the morning brief, scheduled qmd reindex) cannot run autonomously
  under Claude Code alone. They are still useful when invoked
  synchronously — "give me the brief now" works; "give me the brief
  every morning at 7am" doesn't, unless an external cron drives a
  one-shot session. `user-model-reflect` is invokable on demand and
  does not require scheduling to be useful; if a regular cadence ever
  proves worth it, the `/schedule` skill or `CronCreate` is the path.

## Install prerequisites

Claude Code itself has no soma-specific install. On a fresh checkout:

1. Clone the brain.
2. Open Claude Code with the brain root as `cwd`.
3. Claude Code auto-loads `CLAUDE.md`, which redirects to `AGENTS.md`.

Optional, for full capability surface:

| Capability | Add-on |
|---|---|
| `raw-source-archive-upload` | Install `rclone` and configure the R2 remote per `conventions/raw-source-archive.md`. Then ingest skills that upload binaries work end-to-end via Bash. |
| `brain-search` upgrade | Install `qmd` locally and embed the corpus. Skills can shell out to `qmd query` via Bash. (This effectively binds the capability the same way Hermes does, just without the daemon — query latency includes model load.) |
| `schedule-job` for autonomous runs | External `cron` or launchd that fires `claude-code` against a saved session, with a one-shot prompt. Out of scope for the in-session adapter. |

## Skill availability summary

**Fully supported:**
- Thought-partner: `query`, `academic-verify`, `literature-research`,
  `concept-synthesis` (the last two with degraded `brain-search`).
- Grant-writing: `grant-plan`, `grant-section`, `grant-coherence`,
  `grant-citations`, `grant-finalize`, `grant-ingest`.
- Brain-building (filesystem-only): `ingest`, `paper-ingest`,
  `ingest-pending-papers`, `idea-ingest`, `enrich`, `restructure-thin-page`,
  `maintain`, `frontmatter-guard`, `citation-fixer`.
- Always-on: `brain-ops`, `signal-detector`.
- Meta: `skill-creator`, `ask-user`, `migrate`, `user-model-reflect`
  (manual invocation only).

**Degraded (work with caveats):**
- Anything that uses `brain-search` heavily — runs against Grep/Glob.
- `media-ingest`, `voice-note-ingest` — work for the markdown
  distillation phase; the audio-transcription and R2-upload phases
  require optional add-ons.

**Unavailable (refuse cleanly):**
- Research-logistics cluster: `briefing`, `daily-task-prep`,
  `daily-task-manager` — depend on `gmail-read` / `calendar-read` /
  `send-notification`.

## Harness-specific behaviors and gotchas

- **Plan mode.** Claude Code's plan mode is available for any
  multi-step structural change (a new skill, a sweep across the
  corpus). Use it for any work that would benefit from explicit
  approval before file edits begin.
- **Permission prompts.** Bash and read/write tool calls may prompt for
  approval. The `fewer-permission-prompts` skill scans transcripts and
  suggests an allowlist for `.claude/settings.json` to reduce friction
  on read-only operations.
- **No autocommit.** Hermes auto-commits the vault on a cron; Claude
  Code does not. Commits are explicit (`git commit` via Bash) and
  follow the standard "ask before committing" pattern unless the user
  has authorized otherwise.
- **Frontmatter lint runs in CI, not in-session.** The GitHub Action
  `.github/workflows/frontmatter-lint.yml` runs on push/PR; locally a
  developer can run `python3 .github/scripts/lint-frontmatter.py` to
  check before pushing.

## See also

- [`../../CLAUDE.md`](../../CLAUDE.md) — the auto-loaded entry point
- [`../../skills/conventions/capabilities.md`](../../skills/conventions/capabilities.md) — the capability contract
- [`./hermes.md`](./hermes.md) — the sibling adapter for Hermes
