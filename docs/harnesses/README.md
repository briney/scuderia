# `docs/harnesses/` — per-harness adapter docs

A scuderia instance is pure markdown and runs inside a **harness** — a process
that loads the instance content + character + skills and becomes the agent
(`docs/north-star/DESIGN.md` §6). Each supported harness has an adapter
doc here that maps scuderia's named capabilities
(`skills/conventions/capabilities.md`) to that harness's actual tools.

## Supported harnesses

| Harness | Adapter doc | Status |
|---|---|---|
| **Hermes** | [`hermes.md`](./hermes.md) | Reference harness. Most fully capable; provides the full capability surface (scheduling, messaging gateway, voice transcription, R2 archive via rclone). Install runbook: `SETUP.md` at the root. |
| **Claude Code** | [`claude-code.md`](./claude-code.md) | Secondary. Provides the universal substrate (file IO, fetch, subagents) plus brain operations via Read/Write/Edit. Lacks Gmail/Calendar, messaging gateway, and voice transcription. Thought-partner, grant-writing, and user-model skills work natively (the user-model layer is at full parity with Hermes); research-logistics is largely unavailable. |

## How an adapter doc is structured

Each adapter doc carries:

1. **Capability binding table.** Every named capability from
   `skills/conventions/capabilities.md` mapped to the harness's real
   tool, or marked unavailable / degraded.
2. **Error behavior.** What a capability does on failure under this
   harness — exception, return shape, retry behavior.
3. **Install prerequisites.** What needs to exist on the host before the
   harness can serve a given capability (e.g., `rclone` configured for
   `raw-source-archive-upload` under Hermes).
4. **Skill availability summary.** Which skills work natively, which
   degrade, which are unavailable and why.
5. **Harness-specific behaviors.** Anything the agent needs to know about
   how this harness loads files, sessions, plan modes, etc.

## Adding a new harness

1. Author `docs/harnesses/<name>.md` mirroring `hermes.md`'s structure.
2. For each capability in `skills/conventions/capabilities.md`, declare
   the binding (or mark unavailable).
3. Add a row to the per-harness matrix in
   `skills/conventions/capabilities.md`.
4. If the harness has its own entry-point convention (a file it
   auto-loads on session start — like Claude Code's `CLAUDE.md`),
   author that file at the instance root so the harness finds it.
5. Update `AGENTS.md` if the new harness changes anything universal.

## Why per-harness docs exist (and why they don't bloat)

The temptation is to scatter harness notes into every skill ("under
Hermes, this skill uses qmd; under Claude Code, it falls back to
ripgrep…"). That would make each skill harder to read and would
duplicate the same harness facts across 31 files. The capability
contract lets skills stay clean — they name capabilities, never tools
— and the per-harness mapping lives here, once.
