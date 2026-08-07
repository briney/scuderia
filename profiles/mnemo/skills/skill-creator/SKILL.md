---
name: skill-creator
description: Author a new skill or improve an existing one — a single SKILL.md in the house style, MECE-checked against the resolver, with a routing row added. Use when a recognizable job has no skill, or a skill needs a rewrite.
triggers:
  - "create a skill"
  - "new skill"
  - "improve this skill"
---

# Skill creator — author a skill in the house style

A skill is one file: `skills/<name>/SKILL.md`. It captures how the mind works on
a recognizable job — a procedure, not a database entry and not a character
trait. This skill authors new skills and rewrites existing ones so they match
the house style and stay MECE with the rest of the set.

> **References:** `AGENTS.md` (the four-layer model — what a skill *is*),
> `skills/RESOLVER.md` (the routing table this extends), `skills/conventions/`
> (cross-cutting rules a skill cites rather than restates),
> `skills/conventions/capabilities.md` (the named capability list new skills
> should bind to). Match the style of the existing skills — `brain-ops`,
> `query`, `ingest` are the exemplars.

## Capabilities

`brain-read`, `brain-write`. Meta — operates on `skills/*/SKILL.md` and
`skills/RESOLVER.md`. Universal.

## What this guarantees

- A skill is one `SKILL.md` with frontmatter (`name`, `description`, `triggers`)
  and a body in the house style — no other files.
- The new skill does not overlap an existing one — MECE against the resolver.
- The body references the character and the conventions by path; it never
  restates them.
- The resolver gets a routing row in the correct cluster.

## When it is a skill

A skill activates in response to a recognizable *task*. If you cannot name a
triggering situation, the behaviour belongs in the character (`SOUL.md`), not a
skill (`AGENTS.md`). Before authoring, confirm the job has a trigger.

## Phases

1. **Name the capability gap.** What recognizable job has no skill? What request
   would a session not know how to route?
2. **MECE-check against the resolver.** Read `skills/RESOLVER.md`. If an existing
   skill already covers most of this job, **extend that skill** rather than
   create an overlapping one. A new skill is justified only when the job is
   genuinely distinct. When improving an existing skill, this is the step where
   you decide whether the fix is a rewrite or a merge.
3. **Write the SKILL.md.** Use the template below. Keep it crisp and declarative
   — a fat-but-tight markdown procedure, roughly 60-160 lines. Cite conventions
   by path; do not duplicate them. Reference the character; do not restate it.
4. **Add a routing row to the resolver.** Add one row to `skills/RESOLVER.md` in
   the cluster the skill belongs to (thought-partner, research-logistics,
   brain-building and upkeep, or meta), with the trigger and the skill path.
   Keep the disambiguation rules consistent — the most specific skill wins.

## The SKILL.md template

```markdown
---
name: <skill-name>
description: <One or two sentences — what the skill does and when it runs.>
triggers:
  - "<trigger phrase>"
  - "<trigger phrase>"
---

# <Skill title> — <one-line framing>

<A short paragraph: what job this skill does and why it exists.>

> **Conventions:** <path> (<what it covers>), <path> (<what it covers>).

## What this guarantees

- <The contract — 3-5 bullets stating what the skill always ensures.>

## Phases

1. **<Phase name>.** <What happens in this step.>
2. **<Phase name>.** <...>

## Output

<What good output looks like — the shape, the citations, the format.>

## Anti-patterns

- <What not to do — 3-6 bullets.>
```

Frontmatter carries **only** `name`, `description`, `triggers`. No `version`, no
`tools`, no `mutating`, no `priority` — the schema is three fields.

## Output

- A new `skills/<name>/SKILL.md` in the house style, or a rewritten one.
- One new routing row in `skills/RESOLVER.md`.

## Anti-patterns

- Creating a skill that overlaps an existing one — extend the existing skill
  instead.
- Skipping the MECE check against the resolver.
- Restating the character or a convention in the skill body instead of citing it
  by path.
- Adding frontmatter fields beyond `name`, `description`, `triggers`.
- Authoring a skill for a behaviour with no nameable trigger — that is character.
- Creating extra files alongside `SKILL.md`. A skill is one file.
- Forgetting the resolver row — an unrouted skill is invisible.
