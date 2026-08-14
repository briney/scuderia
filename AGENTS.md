# AGENTS.md — working in the soma repo

soma is a **platform kit** for personal knowledge-graph minds: conventions +
schema-driven tools + profile templates + a setup CLI. There is no runtime
here — a *harness* (Hermes, Claude Code, …) loads an instance and runs it.
This repo is the public body; minds (instances) live elsewhere, in private
repos bound by config.

## The load-bearing rule

**The unit of privacy is the repo.** soma must never contain instance (brain)
content — no pages, no user models, no program state, no private specs. An
instance is a *sibling* repo, never a subdirectory or submodule of this
checkout, so no careless `git add -A` can ever stage private content into the
public repo. If you find yourself writing an instance's name, paths, or
content into a file here, stop: templates say "the brain", "your human", and
`<instance>`.

## Layout

| Path | What it is |
|---|---|
| `core/` | The capability contract (`capabilities.md`) and schema-driven tools (`tools/`) |
| `profiles/<name>/` | A profile template: `schema.yaml`, `conventions/`, `skills/`, `SOUL.md` / `STYLE.md` / `USER/` / `AGENTS.md` templates, `manifest.yaml`, `example-brain/` |
| `docs/north-star/` | What soma is for (`VISION.md`) and how it is built (`DESIGN.md`) |
| `docs/harnesses/` | Per-harness capability bindings — the adapter docs |
| `interface/` | The feed layer: card renderer + contract, publisher-agnostic |
| `setup/soma` | The CLI: `init` / `doctor` / `adopt` |

## Working norms

- **Profiles own semantics; the platform owns shape.** The platform knows
  instances have typed markdown pages with frontmatter and links; it does not
  know what a "paper" or a "protocol" is. If a change assumes a specific page
  kind exists, it belongs in a profile, not in `core/`.
- **Skills name capabilities, not tools** (`core/capabilities.md`); harnesses
  bind them (`docs/harnesses/`). A skill that hardcodes a harness-specific
  tool without naming the capability is a bug.
- **Templates are generic; minds are named.** Skill and convention prose never
  hardcodes an instance name — it says "the brain" / "your human" or reads
  `brain.yaml`.
- **Half-real templates rot.** Ship a profile stub (see `profiles/oiko/`)
  rather than an unexercised template.
- **No skill-name collisions across sources.** A profile-scoped skill must
  never reuse the frontmatter `name:` of a skill visible from another
  layer (a shared skill set, another profile, or harness built-ins). To
  change shared behavior, edit the shared skill; intentional
  profile-specific variants get a distinct name (e.g. `<name>-<profile>`).
  Skill resolvers refuse ambiguous names — and refusal means nobody can
  patch anything, which is how the 2026-08 patch-skill sprawl happened.
  `setup/soma skill-check` enforces this mechanically.
- **Patch skills are not a pattern.** Never create a skill whose purpose
  is to annotate another skill; patch the target directly. If a patch
  genuinely cannot be applied immediately (an interrupted session, a
  cross-profile guard), the finding goes in a working document with a
  TODO, not in the skill index. `setup/soma skill-check` flags
  patch-marker skills as warnings.
- **One canonical home per skill.** When a profile's skills are bound
  into a harness by symlink, no real skill directories may sit alongside
  the symlink — a real dir plus a symlinked dir with the same skill name
  is the collision that deadlocks resolvers.
- The linter is schema-driven: `core/tools/lint-frontmatter.py --brain
  <instance> [--schema profiles/<name>/schema.yaml]`. Changes to a profile's
  frontmatter contract land in *both* its `schema.yaml` and its
  `conventions/frontmatter.md` prose — the two must not drift.
- Commit promptly with descriptive messages. This repo is hand-committed like
  code; no auto-snapshotter watches it.

## The spec

`docs/north-star/VISION.md` fixes what soma is for; `docs/north-star/DESIGN.md`
is the implementation blueprint. Where anything here disagrees with them, they
are the intent.
