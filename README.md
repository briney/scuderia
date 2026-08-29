# scuderia

**scuderia** is a platform kit for running a stable of personal AI agents:
each agent is a pure-markdown persistent state, a character, and a set of
skills, loaded by a harness (an AI agent runtime). Italian *scuderia*: the
racing team's stable — finely tuned cars, each built for its discipline,
each driven by a human.

scuderia is a **kit, not a runtime**: conventions + schema-driven tools + profile
templates + a setup CLI. No plugin registries, no discovery, no framework. A new
harness needs one adapter doc, not a port.

## Layout

```
core/            capability contract, agora contract, schema-driven tools
interface/       feed renderer + card contract (publisher-agnostic)
profiles/
  mnemo/         research-brain template (flagship): conventions + schema.yaml,
                 skills/, SOUL.md / STYLE.md / USER/ templates, example brain,
                 and the mnemo north-star pair (VISION.md / DESIGN.md)
  ergon/         doer template (craftsman): verified artifacts on commission
  oiko/          lab-manager template (stub)
docs/
  north-star/    the platform VISION and DESIGN — the stable, the driver,
                 the shared machinery (per-profile pairs live with each profile)
  harnesses/     per-harness capability bindings (Hermes, Claude Code)
setup/           the scuderia CLI: init / doctor / adopt / skill-check
```

## The model

- The **platform** (this repo) knows that instances have typed markdown pages
  with frontmatter and links. It does not know what a "paper" or a "protocol"
  is — that is profile-defined.
- A **profile template** (e.g. `mnemo`) defines page kinds, schema, conventions,
  skills, and character templates for a kind of agent.
- An **instance** is a private repo of actual content, bound to a scuderia checkout
  by an `instance.yaml`. Instances are sibling repos, never subdirectories or
  submodules: the unit of privacy is the repo.

## Quick start

```
setup/scuderia init --profile mnemo --name <your-agent-name> --path <dir>
setup/scuderia doctor --path <dir>
```

Then bind your harness per `docs/harnesses/<your-harness>.md`. See
`docs/north-star/VISION.md` for the why and `docs/north-star/DESIGN.md` for
the how — and `profiles/mnemo/VISION.md` for the flagship archetype.

## License

MIT — see [LICENSE](LICENSE).
