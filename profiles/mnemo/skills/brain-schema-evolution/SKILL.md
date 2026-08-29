---
name: brain-schema-evolution
description: Use when a proposal adds page kinds or expands brain scope.
triggers:
  - new page kind or new page type proposal
  - should X be a page
  - scope expansion proposal (can the brain also track ...)
  - directory or frontmatter schema restructuring
---

# Brain schema evolution

The highest-blast-radius change the brain can take. A page kind is forever:
directories, the linter, ingest wiring, and every skill's templates all bind
to it. Treat every proposal as an architecture decision, not a feature
request. Worked examples: `references/lab-management-expansion-2026-07.md`,
`references/email-modality-2026-08-01.md`,
`references/hitlist-concept-promotion-2026-08-18.md`.

## Step 1 — Read the scope boundary before designing anything

`VISION.md` §6 and `skills/conventions/page-kinds.md` ("Scope boundary").
Exclusions there are deliberate and *structural* — the brain excludes material
by having nowhere to file it, not by filtering it. If the proposal crosses a
documented exclusion, say so explicitly: this is a north-star revision, and
your human should approve it as one. Never let a scope change slide in sideways as
a schema tweak.

## Step 2 — Decompose mixed proposals against the scope line

Most expansion proposals bundle in-scope and out-of-scope material. Split them
before designing. The test: does this feed the research program (grantwriting,
progress reports, brainstorming, who-can-do-what) or is it operational churn?
In the lab-management case: org structure, member expertise, and project
status are research-program knowledge; ordering, 1:1 cadence, and equipment
logistics are churn. The two halves get different answers.

## Step 3 — Extend existing kinds before adding new ones

Three rules, in order:

1. **Identity survives lifecycle — status is a field, not a kind.** Precedent:
   `paper` covers preprint and published via a `status` field, so a
   publication flip doesn't break inbound wikilinks. Same for people: one page
   per human, with relationship typing in frontmatter (`role`, `member_of`,
   `lab_status`). Splitting by relationship type (lab-member vs collaborator)
   gives one human two pages and breaks the author-ledger and
   entity-resolution wiring.
2. **The graph-hub test.** A new kind is justified only when its entities need
   inbound edges from many directions. An attribute of exactly one parent (a
   project's milestone, a grant's deadline) stays a frontmatter field on the
   parent page. If the proposed pages would be thin and singly linked, they
   are fields.
3. **Relationship distinctions belong in frontmatter edges, not directories.**
   "Which people are lab members" is a query over `member_of`, not a
   `lab-members/` directory.

## Step 4 — Roll out pilot-first

Design note → conventions (`page-kinds.md`, `frontmatter.md`) → linter
(`.github/scripts/lint-frontmatter.py`) → skill templates (`enrich`, ingests)
→ pilot on 3–5 real pages → your human reviews the shape → full pass. Never
full-scale without the pilot. Schema before skills: a template that writes
fields the linter doesn't know produces failing pages.

## Step 5 — Move the line explicitly

When scope changes, revise `VISION.md`, `DESIGN.md`, and `page-kinds.md` in
the same unit of work as the schema change. The failure mode is silent drift:
future sessions enforcing a boundary that no longer exists, or refusing to
file material that a stale boundary still calls out of scope.

## Anti-patterns

- Proposing a new kind for something queryable via a frontmatter field.
- Splitting one real-world entity across two pages by relationship or
  lifecycle stage.
- Patching skill templates with fields the conventions and linter don't know
  yet.
- Treating "no page kind exists for X" as an oversight rather than a
  deliberate exclusion — check `VISION.md` §6 first.
- Declaring the pilot done without your human reviewing the shape of the pilot
  pages.
