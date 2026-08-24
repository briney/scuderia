# soma

**soma** is a platform kit for running a personal research brain: a pure-markdown
knowledge graph, a character, and a set of skills, loaded by a harness (an AI
agent runtime). Greek *soma*: body — the reusable body of machinery that houses
and sustains a mind.

soma is a **kit, not a runtime**: conventions + schema-driven tools + profile
templates + a setup CLI. No plugin registries, no discovery, no framework. A new
harness needs one adapter doc, not a port.

## Layout

```
core/            capability contract, schema-driven tools
interface/       feed renderer + card contract (publisher-agnostic)
profiles/
  mnemo/         research-brain template (flagship): conventions + schema.yaml,
                 skills/, SOUL.md / STYLE.md / USER/ templates, example brain
  oiko/          lab-manager template (stub)
docs/
  north-star/    what soma is for (VISION) and how it is built (DESIGN)
  harnesses/     per-harness capability bindings (Hermes, Claude Code)
setup/           the soma CLI: init / doctor / adopt
```

## The model

- The **platform** (this repo) knows that instances have typed markdown pages
  with frontmatter and links. It does not know what a "paper" or a "protocol"
  is — that is profile-defined.
- A **profile template** (e.g. `mnemo`) defines page kinds, schema, conventions,
  skills, and character templates for a kind of brain.
- An **instance** is a private repo of actual content, bound to a soma checkout
  by an `instance.yaml`. Instances are sibling repos, never subdirectories or
  submodules: the unit of privacy is the repo.

## Quick start

```
setup/soma init --profile mnemo --name <your-brain-name> --path <dir>
setup/soma doctor --path <dir>
```

Then bind your harness per `docs/harnesses/<your-harness>.md`. See
`docs/north-star/VISION.md` for the why and `docs/north-star/DESIGN.md` for
the how.

## License

MIT — see [LICENSE](LICENSE).
