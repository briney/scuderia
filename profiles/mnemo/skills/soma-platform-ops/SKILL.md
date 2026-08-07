---
name: soma-platform-ops
description: Use for soma/atticus repo or host-service operations.
triggers:
  - structural changes to the soma or atticus repos
  - pausing/resuming host services for maintenance
  - verifying the instance binding after a change
  - stray cleanup at the repo roots
---

# soma platform operations

Operating the soma platform + atticus instance on Bryan's host: repo layout,
quiescence for structural moves, the instance binding, and verification.

The two-repo world (post-2026-08-06 migration):

- `~/git/soma` — the platform kit (private GitHub `briney/soma` until the
  redaction pass; the public flip is a separate explicit Bryan decision).
  Template skills + conventions live at `profiles/mnemo/`; edit them there
  directly and commit promptly. `setup/soma` CLI: init / doctor / adopt.
  Schema-driven linter: `core/tools/lint-frontmatter.py --brain <dir>`.
- `~/git/atticus` — Bryan's private mnemo instance; the brain is the inner
  `atticus/` dir with `brain.yaml` (`name: atticus, profile: mnemo`).
  `atticus/skills/` is the instance-private layer (kept empty-ish).
- Binding: `~/.hermes/profiles/atticus/skills/atticus` symlinks to
  `~/git/soma/profiles/mnemo/skills`; the profile `SOUL.md` symlink points at
  the vault's own SOUL.md (character stays instance-private).
- **The unit of privacy is the repo.** Never write instance content into soma;
  never nest one repo inside the other. soma templates say "the brain" /
  "your human" / `<instance>`, never a real instance's name or paths.

Design specs (private): `atticus/docs/specs/2026-08-06-soma-platform-design.md`
and `2026-08-06-card-contract-design.md` in the vault.

## Quiescence before any structural move (load-bearing — July 2026 lessons)

Structural moves (moving/renaming dirs the harness or sync layer watches)
require the whole host quiet first, in this order:

1. **Pause ALL enabled Hermes cron jobs**, not just auto_push — list with the
   cronjob tool, pause each, record which were already paused (leave those).
   Exception to remember when resuming: `auto_push.sh`'s own header says never
   scheduler-pause it to gate the *rem-cycle* (that uses `rem-cycle.lock`);
   scheduler pauses are for maintenance windows only — always resume after.
2. **Stop the gateway**: `hermes --profile atticus gateway stop`. The gateway
   regenerates a 513-byte SOUL.md stub if the profile SOUL.md symlink target
   goes missing mid-move.
3. **Unload Syncthing**: `launchctl bootout gui/$(id -u)/ai.syncthing.atticus`.
   Syncthing re-litters the old layout from peers mid-move.
4. Confirm all three are actually down (pgrep, cronjob list) BEFORE touching
   files.

Re-enable in reverse order after verification: Syncthing
(`launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.syncthing.atticus.plist`),
gateway (`hermes --profile atticus gateway start`), then resume each paused
cron job individually.

## Gotchas learned the hard way

- **Orphaned gateway process**: `launchctl list` can show a service with a PID
  while `launchctl print`/`bootout` report "No such process" — the process is
  an orphan (PPID 1) from a previous bootout, and the list entry is stale.
  Don't fight launchd; `hermes --profile atticus gateway stop` handles it.
- **Mixed cron workdirs create strays**: rem-cycle jobs historically ran with
  `workdir` = repo container root while others used the vault root; cwd-relative
  writes then produced duplicate `docs/rem-cycle/` state at both roots. All
  jobs now use the vault root. If new strays appear at a repo root, check job
  workdirs first.
- **Drift-check before a move**: when material was copied earlier and is moved
  later, diff source vs copy first (`diff -rq`) and check `git log --since` —
  automated jobs may have fired in between.
- **Strays may be live dependencies**: the container-root
  `skills/atticus/granola-meeting-sync/scripts/granola_mcp.py` stray was the
  ONLY copy of a script the cron job invoked. File-or-kill requires checking
  references, not just staleness.
- **Tirith hardline**: oversized inline shell payloads get blocked; blocked
  scripts land in `~/.hermes/profiles/atticus/cache/blocked-scripts/` — run
  via `bash <path>`. Put migration/syncer scripts in files, never inline.
- **File tools resolve relative paths against a drifted terminal cwd** — use
  absolute paths during multi-repo operations.

## Verification checklist after a binding change

1. `~/git/soma/setup/soma doctor --path ~/git/atticus/atticus` → OK.
2. `skill_view` a template skill — confirm it resolves through the repointed
   symlink and returns the soma copy.
3. Brain paths resolve from a session at the vault root (cwd-relative page
   reads).
4. Linter parity: `python3 ~/git/soma/core/tools/lint-frontmatter.py --brain
   ~/git/atticus/atticus` — compare against prior baseline (36 pre-existing
   errors / ~3700 warnings as of 2026-08-06).
5. auto_push origin guard: script hardcodes the vault repo and requires
   `briney/atticus` in the origin URL; `briney/soma` can never match.
6. Commit promptly in BOTH repos; the auto_push cron is a safety net, not a
   commit strategy.

## Known follow-ups (as of migration day)

- `conversations/` is missing from auto_push CONTENT_PATHS (pre-existing gap,
  Bryan's call).
- Template skills say `USER.md`; atticus's user model stays `BRYAN.md` —
  naming resolution is part of the path-decoupling sweep.
- Vault `SETUP.md` still describes the pre-migration monorepo (stale).
- Vault CI uses the old hardcoded linter; wiring it to the schema-driven one
  needs a private-repo checkout in CI.
- Redaction pass (manual read + gitleaks) gates any public flip of soma.
