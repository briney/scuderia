# SETUP.md — installing a soma brain

The runbook for going from zero to a running instance. Two paths cover the
same ground: `soma init` scaffolds a new brain; `soma adopt` binds an
existing one. Both are defined by the profile's `manifest.yaml`, so the paths
cannot drift. A third path — agent-guided install — is the same steps with
the harness agent doing the interview and invoking the CLI.

## 1. Get the kit

```
git clone <soma-remote> ~/git/soma
cd ~/git/soma
```

Dependencies: Python 3.10+ with PyYAML (for the CLI and the linter). That's
all the platform needs.

## 2. Scaffold or adopt the instance

New brain:

```
setup/soma init --profile mnemo --name <your-brain-name> --path ~/git/<name>
cd ~/git/<name> && git init && git add -A && git commit -m "birth"
```

Existing vault of markdown:

```
setup/soma adopt --path <existing vault> --name <name>
```

Either way, finish with:

```
setup/soma doctor --path <instance dir>
```

`doctor` is the shared definition of done — it exits nonzero with one
complaint per unmet contract item.

## 3. Bind the harness

The CLI touches only soma-owned things; harness bindings are these
one-liners, performed once per host. (`doctor` prints them as reminders.)

### Hermes (reference harness)

```
# character: the profile loads the instance's SOUL.md
ln -sfn <instance>/SOUL.md ~/.hermes/profiles/<instance>/SOUL.md

# skills: one symlinked category per layer (template shown; the instance's
# own skills/ dir can be bound as a second category when it has content)
ln -sfn <soma>/profiles/mnemo/skills ~/.hermes/profiles/<instance>/skills/<category>

# sessions run with the brain root as cwd
#   config.yaml:  terminal.cwd: <instance abs path>
#   .env:         MESSAGING_CWD=<instance abs path>
```

Optional host overlay (lets `skills/conventions/…` references resolve from
the brain root as cwd): symlink `<instance>/skills/conventions` →
`<soma>/profiles/mnemo/conventions`, and add it to the instance's
`.gitignore` and `.stignore` — it is host-only glue, never committed or
synced.

### Claude Code (secondary harness)

No install beyond the checkout: run sessions with the instance root as cwd;
`CLAUDE.md` auto-loads and points at `AGENTS.md`. Capability differences are
in `docs/harnesses/claude-code.md`.

## 4. Capability prerequisites (per host, as needed)

| Capability | Requires |
|---|---|
| `brain-search` | qmd installed; `qmd embed` run; HTTP MCP daemon |
| `raw-source-archive-upload` | rclone + an R2 remote (object-scoped token) |
| `send-notification` / `messaging-send` | gateway bot token + allowed users in `.env` |
| `gmail-read` / `calendar-read` | Spark Desktop on the host + the `spark-cli` shim |

The per-capability mapping and error behavior: `docs/harnesses/<harness>.md`.

## 5. Verify

- `setup/soma doctor --path <instance>` is green.
- A live session loads the character and template skills through the
  binding, and brain paths resolve from cwd.
- `python3 core/tools/lint-frontmatter.py --brain <instance>` runs (findings
  are the instance's own, not the install's).
