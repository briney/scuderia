# CLAUDE.md — {{INSTANCE_NAME}} under Claude Code

**Read [`AGENTS.md`](./AGENTS.md) in full first.** It orients every agent
(human or otherwise) and is not Claude-specific. None of it is repeated here.

This file is *only* what differs when the harness is **Claude Code** — a
secondary harness; Hermes is the reference. Full capability mapping, error
behavior, and gotchas: `docs/harnesses/claude-code.md` in the scuderia checkout.

## Every session

- **Load the character and user model yourself.** Claude Code auto-loads only
  this file, so explicitly read `SOUL.md` and `USER/<name>.md` at the start of
  each session. `RESEARCH.md` and `STYLE.md` stay on-demand, as AGENTS.md
  describes.

## Capability → Claude Code tool

Skills name capabilities; under this harness they bind to:

- `brain-search` → **Grep / Glob** — no semantic ranking; phrase queries with
  the literal words a page would use
- `read/write/edit-file`, `brain-read/write` → Read / Write / Edit on `.md`
  pages
- `fetch-url` → WebFetch (Bash + `curl` for auth)
- `spawn-subagent` → Agent
- `schedule-job` → CronCreate / ScheduleWakeup, when surfaced
- **Not provided:** notification/messaging, calendar, voice — skills needing
  these refuse cleanly. The adapter doc lists which skills are supported,
  degraded, or unavailable.

## Skills

Run a skill with the Skill tool, or read the SKILL.md and follow it. The
profile's `skills/RESOLVER.md` routes a request to a skill.

## Workflow

- Git via Bash. Ask before committing unless told otherwise; once cleared,
  follow the commit norm in AGENTS.md.
