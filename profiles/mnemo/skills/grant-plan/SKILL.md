---
name: grant-plan
description: Open a grant-writing engagement — read the NOFO, gather the brain substrate, design and pressure-test the Specific Aims as a go/no-go filter, lay out the section plan, and create the grant page the rest of the cluster drafts into.
triggers:
  - "let's write an R01"
  - "start a grant"
  - "plan this grant"
  - "new application for"
  - a funding announcement dropped with intent to apply
---

# Grant plan — open and scope a grant-writing engagement

This is the entry point to the grant-writing cluster. Grant writing is
multi-week and multi-section (`VISION.md` §2.2); this skill sets the engagement
up so the whole application stays in view. It identifies the application,
gathers what the brain already holds, designs the Specific Aims — and uses that
design as a **go/no-go filter** — then lays out the section plan and creates the
`grant` page that `grant-section`, `grant-coherence`, and `grant-citations`
draft into.

> **Conventions:** `skills/conventions/brain-first.md` (search before creating),
> `skills/conventions/frontmatter.md` (the `grant` schema and status enum),
> `skills/conventions/raw-source-archive.md` (archiving the NOFO),
> `skills/conventions/graph-and-links.md` (typed links to projects),
> `skills/conventions/quality.md` (cite-or-flag, the notability gate),
> `skills/conventions/capabilities.md` (the harness contract),
> `skills/grant-formats/` (R01 / R21 structure and page limits),
> `skills/ask-user/SKILL.md` (gate scope decisions). Loads `STYLE.md` — the
> whole cluster does — but the section-by-section prose discipline is
> `grant-section`'s; this skill produces structure and the go/no-go call.

## Capabilities

`brain-search`, `brain-read`, `brain-write`, `user-model-query` (Bryan's
domain priors inform the Aims pressure-test), `raw-source-archive-upload`
(archiving the NOFO PDF). `brain-search` optional.

## What this guarantees

- A grant-writing engagement becomes **one** `grant` page in `status: drafting`
  — never a scattered set of per-section files.
- The Specific Aims are designed and pressure-tested **before** section
  drafting begins. A weak idea is shelved cheaply, not expanded into a
  half-application the mind then treats as active work.
- The application is scoped against the **actual NOFO** — sections, page
  budget, mechanism fit — with `grant-formats/` as the fallback only.
- The page carries a section plan: what `grant-section` drafts, in what order,
  from which brain pages, with the open gaps already flagged.
- The NOFO is archived to R2; no binary enters git.

## Phases

1. **Identify the application.** Mechanism and funder; new vs. resubmission vs.
   renewal. Get the NOFO from Bryan and read it — it is authoritative. With no
   NOFO yet, fall back to `grant-formats/nih-r01.md` or `nih-r21.md`. Confirm
   the mechanism *and* the project(s) the grant serves with Bryan via
   `skills/ask-user/SKILL.md` — a grant touches several projects and the wrong
   call is expensive to unwind.

2. **Brain-first.** Search the brain for an existing `grant` page — a planned
   stub, or a prior submission this resubmits. Page exists → UPDATE, never
   blind-overwrite. A resubmission loads the prior page and its `[!critique]`
   annotations (placed there by `grant-ingest`); those drive the Introduction.

3. **Gather the substrate.** Read `RESEARCH.md` for the active threads and
   funding context. Pull the `project`, `hypothesis`, `concept`, and `method`
   pages the grant builds on — chain to `skills/query/SKILL.md` and, for the
   intellectual arc, `skills/concept-synthesis/SKILL.md`. Check the field state
   behind the Significance pitch with `skills/literature-research/SKILL.md`.
   The output is an inventory: what the brain already supports, what is thin,
   what is missing.

4. **Design the Specific Aims — the go/no-go filter.** With Bryan, frame the
   central hypothesis and two or three aims: the arc, each aim's goal, how the
   aims stay independent yet connected. This is the character running a
   brainstorm, given structure. Pressure-test it honestly (`SOUL.md` — no
   fabricated confidence, never suppress a flaw): do the aims actually
   separate; is the innovation real or merely incremental; for an R01 is the
   feasibility evidence in hand, and for an R21 is the idea genuinely
   exploratory (`grant-formats/`). If the idea does not hold — the aims collapse
   into one, there is no real innovation, an R01 rests on preliminary data that
   does not exist — **say so plainly** and go to 5b.

5a. **Lay out the section plan.** Idea holds → build the outline from the NOFO
   (or the format file): every section, its page budget, the brain pages
   feeding it, and the gaps — needs-citation, needs-data — flagged for
   `grant-section` and `grant-citations`. Order it Aims-first.

5b. **Shelve, cleanly.** Idea does not hold → set `status: shelved`, clear
   `deadline`, and log the reason and date in `## Drafting log`. Starting the
   plan is cheap and abandoning is clean — that is the point of running the
   filter, and it keeps the attention contract honest. A shelved grant stays
   queryable and revivable; it does not surface as active work.

6. **Create or update the grant page.** `status: drafting` (or `shelved`).
   Frontmatter per the `grant` schema (`skills/conventions/frontmatter.md`). Body: the
   section plan, an empty `## Draft` working section, a `## Drafting log`, and
   the analysis skeleton. Wire typed links to the `project` pages.

7. **Archive the NOFO.** `_drop/` → R2; one `sources:` entry, `role: nofo`. The
   binary never enters git (`skills/conventions/raw-source-archive.md`).

8. **Hand off to `grant-section`.** The section plan is the handoff. Aims
   first — nothing downstream is stable until the Aims page is locked.

## Output

The `grant` page during drafting — converging on the shape `grant-ingest`
produces, with three drafting-phase additions (`## Section plan`, `## Draft`,
`## Drafting log`):

```markdown
---
kind: grant
slug: <slug>
title: "<working title>"
funder: institutions/<slug>
mechanism: "R01"           # R01 | R21 — free text, see grant-formats/
role: PI                   # PI | co-PI | co-I | consultant
status: drafting           # full enum in skills/conventions/frontmatter.md
deadline: YYYY-MM-DD       # submission target — cleared when status: shelved
importance: 0.0
links: [projects/<slug>]
tags: []
sources:
  - role: nofo             # the NOFO, per skills/conventions/raw-source-archive.md
    hash: sha256-...
    r2_key: grants/....pdf
    filename: "..."
    ingested: YYYY-MM-DD
    provenance: "grant-plan, YYYY-MM-DD"
---

# <Working title>

## Section plan
Each section, its page budget, the brain pages feeding it, the open gaps.
grant-section drafts against this; grant-coherence checks against it.

## Draft
The working application prose, section by section — filled by grant-section.
Fenced from `## Verbatim`: not voice corpus until Bryan approves it and the
grant is submitted, at which point this section promotes to `## Verbatim` and
the page becomes what `grant-ingest` produces (see `grant-ingest/SKILL.md`).

## Drafting log
Dated entries — decisions, scope changes, and the shelve reason if shelved.

## Analysis
The grant-ingest analysis sections — Summary, Significance & Innovation,
Preliminary Data, Approach — written and finalized as the draft matures.
```

## Anti-patterns

- Expanding a weak idea into a full application instead of shelving it — the
  Aims design exists to be a filter; running it and ignoring the result wastes
  the filter.
- Drafting polished section prose here — that is `grant-section`. This skill
  produces structure and the go/no-go call.
- Treating a `grant-formats/` file as authoritative when a real NOFO is in hand
  — the NOFO wins (`grant-formats/README.md`).
- Splitting the engagement across per-section files — one `grant` page holds
  the whole application.
- Skipping the brain-first search and creating a duplicate page over an
  existing stub or a prior submission.
- Leaving a shelved grant with a live `deadline` — the attention contract will
  nag about dead work.
- Committing the NOFO binary into git instead of archiving it to R2.
