---
name: skill-creator
description: Author a new skill or improve an existing one — a single SKILL.md in the house style, MECE-checked against the resolver, with a routing row added and an eval contract declared. Use when a recognizable job has no skill, or a skill needs a rewrite.
triggers:
  - "create a skill"
  - "new skill"
  - "improve this skill"
---

# Skill creator — author a skill in the house style

A skill is one file: `skills/<name>/SKILL.md` — plus optionally a `references/`
directory (`references/<topic>.md`), `templates/`, and `scripts/` for
session-specific detail and re-runnable helpers. The `SKILL.md` carries the
procedure; support files carry the detail. It captures how the mind works on
a recognizable job — a procedure, not a database entry and not a character
trait. This skill authors new skills and rewrites existing ones so they match
the house style and stay MECE with the rest of the set.

> **References:** `AGENTS.md` (the four-layer model — what a skill *is*),
> `skills/RESOLVER.md` (the routing table this extends), `skills/conventions/`
> (cross-cutting rules a skill cites rather than restates),
> `skills/conventions/capabilities.md` (the named capability list new skills
> should bind to), `skills/conventions/skill-hygiene.md` (the eval contract,
> the no-regression law, the scheduled-run gate — govern every edit to a
> skill). Match the style of the existing skills — `brain-ops`,
> `query`, `ingest` are the exemplars.

## Capabilities

`brain-read`, `brain-write`. Meta — operates on `skills/*/SKILL.md` and
`skills/RESOLVER.md`. Universal.

## What this guarantees

- A skill is one `SKILL.md` with frontmatter (`name`, `description`, `triggers`,
  optionally `eval_contract`) and a body in the house style — no other files.
- The new skill does not overlap an existing one — MECE against the resolver.
- The skill declares its `eval_contract` — the goal written before evaluating
  (`skill-hygiene.md`).
- The body references the character and the conventions by path; it never
  restates them.
- The resolver gets a routing row in the correct cluster.

## When it is a skill

A skill activates in response to a recognizable *task*. If you cannot name a
triggering situation, the behaviour belongs in the character (`SOUL.md`), not a
skill (`AGENTS.md`). Before authoring, confirm the job has a trigger.

Three questions, all must be yes, or it is a script (or a character trait), not
a skill:

- Will this be invoked 2+ times? (One-off work is not a skill.)
- Is there more than ~20 lines of real logic? (Trivial helpers do not need
  full skill infrastructure.)
- Does it have a trigger phrase the human would actually say?

**Scope bound — one skill, one capability, one trigger family.** If the target
spans several distinct intents the human invokes separately, do **not** build
one skill covering them all — stop and split. "Run the build" / "roll back" /
"notify" are three intents, not one skill.

## Modes

**Mode A — new.** No `SKILL.md` exists. Run the phases below and author from
scratch.

**Mode B — improve.** A `SKILL.md` exists; the human reported a bug, gave new
input, or asked for a quality pass. Do **not** rewrite from scratch — improve
idempotently:

1. Read all existing artifacts (the `SKILL.md`, any referenced script, the
   resolver row).
2. Identify the **delta** — a *bug fix* (add a test-to-hold for the exact
   bug, fix, add a HARD RULE + a `## Bug` entry), *new input* (extend the
   body, update any script, add coverage), or a *quality pass* (re-read
   against `skill-hygiene.md`, fill gaps).
3. Change surgically — edit files, do not rewrite them.
4. Run the no-regression + re-read gate from `skill-hygiene.md`. If the skill
   backs a scheduled job, re-run a representative task first.

A bug fix records a dated entry in the body:

```markdown
## Bug: [date] — [short description]
- **What happened:** [concrete failure]
- **Root cause:** [why]
- **Fix:** [what changed]
- **Hard rule added:** [new constraint to prevent recurrence]
```

**Mode C — streamline.** A skill has grown so large it is a context drain:
SKILL.md over ~500 lines / ~40KB, with case-specific "Observed:" provenance
annotations, a changelog, encyclopedic lookup tables, or implementation
detail that belongs in scripts. The procedure is sound but buried. This is
*not* a Mode B surgical patch — it is a full restructure, but preserving the
working procedure (not rewriting from scratch).

1. **Diagnose by category.** Read the entire SKILL.md. Categorize every
   section as one of: **core procedure** (keep), **pure provenance** /
   changelog / "Observed:" session logs (delete — this is what git history
   is for), **encyclopedic reference material** (move to
   `references/<topic>.md`), or **implementation detail** (move to a
   `scripts/<name>.py` that the agent runs instead of hand-typing).
2. **Extract first, cut second.** Create any new reference files and
   scripts *before* rewriting SKILL.md — the SKILL.md will point to them.
   Consolidate fragmented reference files into one coherent file per
   topic.
3. **Rewrite SKILL.md.** Keep the phase structure and every load-bearing
   rule. Cut every "Observed: PMID XXX, YYYY-MM-DD" annotation. Convert
   prose-dense hazard lists into compact tables. Delete the changelog and
   any redundant "Anti-patterns" section that restates positive
   instructions already in the body. Target: every line earns its
   context cost by being exercised in the majority of invocations.
4. **Verify.** Line/byte count drop; all `references/` and `scripts/`
   paths referenced in SKILL.md exist on disk; no "Observed:" annotations
   remain; no dangling references to deleted files; scripts compile.

The bar for Mode C: the skill's context footprint must drop substantially
(>50%) without losing any load-bearing procedure. If the procedure itself
needs rethinking, that is a Mode A rewrite, not a streamline.

**Mode D — retire.** A skill was built for a one-time campaign (a survey,
an enumeration, a profiling run). The campaign is complete. The
methodology, templates, and final outputs already live in a
`references/` corpus (e.g. `master.md`, `templates/`, `profiles/`). The
skill is now dead weight — it loads on every invocation but will never be
invoked again. Retire it:

1. **Confirm the skill is spent.** Was it used once for a campaign that's
   done? Do its outputs already exist in a `references/` directory? If
   both are yes, it's a retire, not a streamline.
2. **Rescue unique content.** Diff the skill against the reference
   corpus — does the skill contain anything NOT already captured there?
   Move only the un-duplicated pieces (typically a methodology note or
   API pattern) to the corpus's `notes/` directory. Most of the skill will
   be redundant with what the corpus already has.
3. **Delete the skill** and its skill directory. Remove the resolver row.
4. **Point any inbound references** (brain pages, other skills,
   `master.md` cross-references) at the reference corpus instead.

The bar for Mode D: the skill has no plausible future invocation AND its
load-bearing content is already preserved in a durable reference corpus.
If there's a reasonable chance the skill will be re-run (even with
modifications), that's a Mode C streamline, not a Mode D retire.

**The systematic library audit** — when asked "inventory all skills" or
"find bloated skills": measure every SKILL.md by bytes
(`find ... -name SKILL.md -exec wc -c {} \; | sort -rn`), then check
total directory size (`du -sh` — linked files add up). For any skill
over ~40KB, read section headers and compute per-section line counts;
the bloat pattern is always the same — observation/provenance sections
and narrative changelogs consuming >50% of the file while the actual
procedure is <350 lines. Check for duplication: inline observation
sections that also exist as `references/` files (diff filenames against
the `references/` directory). Check for template-vs-instance duplicates
(a skill in both `skills/atticus/` and `skills/` — the instance-local
copy is the evolved one; the template copy is stale). Full audit recipe
and cross-reference deletion checklist:
`references/skill-library-audit.md`.

**The bloat signal.** Skills that accumulate session outputs inline —
per-target observation sections (500-700 lines each), changelogs that are
actually full writeups (3,000+ lines), per-item profiles embedded as SKILL.md
sections — are the canonical Mode C/D signal. The SKILL.md should carry
the *procedure*, not the *outputs*. Outputs belong in `references/` (as
individual files) or in a reference corpus. A SKILL.md over ~40KB almost
always has session outputs mixed into the procedure; the fix is extraction
(Mode C) or retirement (Mode D), not compression.

## Phases

1. **Name the capability gap.** What recognizable job has no skill? What request
   would a session not know how to route? Apply the "when it is a skill" gate
   and the scope bound above first.
2. **MECE-check against the resolver.** Read `skills/RESOLVER.md`. If an existing
   skill already covers most of this job, **extend that skill** rather than
   create an overlapping one. A new skill is justified only when the job is
   genuinely distinct. If you create a separate skill despite overlap, record the
   one-sentence distinction in the new body. When improving an existing skill,
   this is the step where you decide whether the fix is a rewrite or a merge.
   Note also the **shared primitives**: a scheduling/looping discipline that
   spans several skills (e.g. the dispatch/yield/verify loop of `batch-drain`)
   is extracted as its own class-level skill and *referenced* by consumers, never
   restated inline in each — when a new skill's logic looks like "what several
   other skills each hand-roll", extract the common primitive instead of adding a
   fourth copy.
3. **Write the SKILL.md.** Use the template below. Keep it crisp and declarative
   — a fat-but-tight markdown procedure, roughly 60-160 lines. Cite conventions
   by path; do not duplicate them. Reference the character; do not restate it.
   Declare the `eval_contract` in frontmatter (`skill-hygiene.md`).
4. **Add a routing row to the resolver.** Add one row to `skills/RESOLVER.md` in
   the cluster the skill belongs to (thought-partner, research-logistics,
   brain-building and upkeep, or meta), with the trigger and the skill path.
   Keep the disambiguation rules consistent — the most specific skill wins.
5. **Re-read and re-verify.** Run the standing regression check from
   `skill-hygiene.md`: re-read the SKILL.md against the resolver and
   conventions, re-check any referenced script, and re-check every item that
   previously passed — not just the one you touched.

## The SKILL.md template

```markdown
---
name: <skill-name>
description: <One or two sentences — what the skill does and when it runs.>
triggers:
  - "<trigger phrase>"
  - "<trigger phrase>"
eval_contract:
  goal: |
    <What this skill is for, and what "excellent" looks like in the real world.>
  dimensions:
    - "<DIMENSION_NAME — the specific question this dimension answers for THIS skill>"
  hard_fails:
    - "<a failure mode that zeroes the contract>"
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

Frontmatter carries **only** `name`, `description`, `triggers` — plus the
optional `eval_contract` block (three required fields, one optional). The
`eval_contract` block carries exactly `goal`, `dimensions`, `hard_fails` — keep
those named keys, they are the future scoring-harness seam. No `version`, no
`tools`, no `mutating`, no `priority`.

## Output

- A new `skills/<name>/SKILL.md` in the house style (with its `eval_contract`),
  or an improved one.
- One new routing row in `skills/RESOLVER.md`.

## Anti-patterns

- Creating a skill that overlaps an existing one — extend the existing skill
  instead.
- Skipping the MECE check against the resolver.
- Restating the character or a convention in the skill body instead of citing it
  by path.
- Adding frontmatter fields beyond `name`, `description`, `triggers`,
  `eval_contract`.
- Adding extra keys inside `eval_contract` beyond `goal`, `dimensions`,
  `hard_fails`.
- Authoring a skill for a behaviour with no nameable trigger — that is character.
- Authoring a "skill" for a one-off, or bundling several intents into one skill.
- Creating extra files alongside `SKILL.md`. A skill is one file: **support files
  go in `references/` / `templates/` / `scripts/` subdirectories**, never
  alongside the `SKILL.md` as loose files. `references/<topic>.md` holds
  session-specific detail and condensed knowledge banks; `templates/` holds
  starter files meant to be copied and modified; `scripts/` holds statically
  re-runnable actions. The umbrella `SKILL.md` gains a one-line pointer to every
  support file so future agents know it exists.
- Authoring a task-agnostic skill into the instance-private profile. Skills that
  are generalizable (not specific to one instance's data) belong in the scuderia
  mnemo template (`~/git/scuderia/profiles/mnemo/skills/`), and `skill_manage`
  cannot write there — author directly in the scuderia checkout and add the
  `RESOLVER.md` row in that checkout too. Instance-private skills live in
  `skills/` inside the instance.
- Forgetting the resolver row — an unrouted skill is invisible.
- Forgetting the `eval_contract` — a skill without a stated bar has no
  regression baseline.
- Rewriting a skill from scratch to improve it — Mode B preserves what works.
- Keeping a spent one-time campaign skill alive when its outputs already
  live in a `references/` corpus — that's a Mode D retire. Dead skills
  still load on every invocation and crowd the resolver.
- Accumulating session outputs (observation writeups, per-item profiles,
  narrative changelogs) inline in SKILL.md — these are the bloat signal.
  Outputs go in `references/` files or a reference corpus, never in the
  procedure.
- Shipping an edit without the no-regression + re-read gate (for a
  schedule-backed skill, without re-running a representative task).
