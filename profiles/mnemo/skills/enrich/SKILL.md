---
name: enrich
description: Create and update person and institution pages — who someone is, their research focus, the work relevant to Bryan's program, and an honest assessment where it helps. Scale effort to importance.
triggers:
  - "enrich"
  - "create person page"
  - "update institution page"
  - "who is this person"
  - "look up this lab"
  - "a new collaborator or funder is mentioned"
---

# Enrich — person and institution pages

Turn a name into a useful brain page. A `person` page records who someone is and
how their work touches Bryan's program; an `institution` page records what a lab,
university, consortium, or funder is and why it matters. The page is a research
artifact, not a contact card — facts are table stakes, the value is the read on
how the work connects.

> **Conventions:** `_brain-filing-rules.md` (file by subject),
> `skills/conventions/brain-first.md` (check the brain before going external),
> `skills/conventions/quality.md` (citations, forward linking, the notability gate),
> `skills/conventions/graph-and-links.md` (the edge forms),
> `skills/conventions/importance-scoring.md` (the salience score),
> `skills/conventions/author-ledger.md` (promotion path from `people/_ledger.yaml`),
> `skills/conventions/capabilities.md` (the harness contract).

## Capabilities

`brain-search`, `brain-read`, `brain-write`, `fetch-url` (open-API
lookups when warranted — PubMed for publications, institutional sites).

## What this guarantees

- Every page has real content — drawn from the brain and, when warranted, from
  open APIs — never a bare stub.
- Every substantive fact carries a citation or an honest `[needs-citation]` flag.
- Effort scales to importance — a key collaborator gets depth, an occasional
  author gets a few lines.
- Bryan's own assessments are never overwritten with external boilerplate.
- Links run forward only — wikilinks in prose, typed edges in frontmatter.

## Two entry paths, two gates

Page creation reaches `enrich` two ways. The gate it applies depends on
how it arrived.

**Promote-from-ledger (paper-ingest, deterministic).** When
`skills/paper-ingest/SKILL.md` Phase 8 Branch 2 sees an author's ledger
entry cross the 5-citation threshold, it chains here with the slug and
the seed data (`name`, `orcid`, `affiliations`, `citations`) from the
ledger entry. **The gate has already fired** — citation count is the
operational rule for paper authors (`skills/conventions/author-ledger.md`).
Do not re-apply a judgment-style notability check; create the page,
write the `author_on:` field from `citations:`, and signal back to
paper-ingest so it can remove the ledger entry. Effort is the **notable**
tier (a recurring author by definition — five papers in the brain
agree).

**Judgment gate (every other caller).** When `enrich` is invoked
directly, or chained from a non-paper-ingest source — meeting attendees,
grant program officers, idea entities, signal-detector mentions,
institutions — apply the gate in `skills/conventions/quality.md`:

- **A person** — a collaborator, student, postdoc, or an author whose
  work recurs on Bryan's threads. Not every name in an acknowledgements
  list. For paper authors specifically, defer to the ledger threshold
  rather than judging directly; the ledger flow exists so this gate is
  not a hot-path decision.
- **An institution** — a lab, university, consortium, or funder that
  sits on the research program: somewhere Bryan collaborates, a funder
  he applies to, a lab whose output he tracks.

When in doubt, do not create. A missing page is cheap; a junk page
buries the ones that matter.

## Scale to importance

Match effort to how load-bearing the entity is:

| Tier | Who | Effort |
|---|---|---|
| Key | Close collaborator, a co-PI, a funder Bryan actively applies to | Full page — research focus, key papers, collaboration context, an assessment |
| Notable | A recurring author (or a ledger-promoted author), a lab whose work Bryan tracks | Moderate — who they are, the relevant work, a forward link or two |

Two tiers, not three. The old "Light" tier (a few honest lines for an
occasional author so the graph resolves) is now the **ledger's** job —
non-paged authors are tracked in `people/_ledger.yaml` and only
materialize as a page when the citation threshold fires. If you find
yourself reaching for the light tier, the right move is to leave the
author in the ledger and stop, not to write a thin page.

## The protocol

### 1. Identify the entry path

How `enrich` was invoked determines the rest of the flow:

- **Promote-from-ledger** — paper-ingest passed a slug plus seed data
  from a ledger entry whose citation count crossed the threshold.
  Skip the brain-first dedup against the ledger (paper-ingest already
  resolved that the page doesn't exist), skip the notability gate (it
  fired in `author-ledger.md`), and go directly to step 3 with the
  ledger seed in hand. The slug is fixed by the ledger entry — do not
  re-slug from the name.
- **Direct or non-paper-ingest call** — name the entity from the
  incoming signal (a message, a meeting, a grant package, a free-form
  "look up this lab"). Distinguish a person from their lab; both may
  earn a page.

### 2. Search the brain first

For each entity from a non-promote call, run `brain-search`. Does a
page already exist?

- **Page exists** → UPDATE path.
- **No page** → CREATE path, after the judgment gate. For a person,
  if the entity is a paper author, check `people/_ledger.yaml` first
  — if an entry exists, the citation count hasn't crossed the
  threshold yet; do not create a page out-of-band. The ledger is the
  staging area for paper authors; circumventing it for one judgment
  call defeats the curation discipline.

Brain-first is not optional (`skills/conventions/brain-first.md`). The brain — and pages
that already mention the entity — is often the richest source.

### 3. Gather what the tier needs

Stop as soon as you have enough signal for the entity's tier.

- **Brain cross-reference (every tier).** Search the brain and follow the graph.
  A person's papers, a lab's people, prior meetings — much of the page is already
  in the corpus.
- **External research (key and notable tiers).** Use `fetch` against auth-free
  open APIs. Send what the brain already knows as context so the result is the
  *delta*, not a rehash:
  - **Authorship, affiliations, publication record** — OpenAlex, Semantic
    Scholar, CrossRef.
  - **Funders — grants and programs** — NIH RePORTER.
  - **Lab or institution facts** — the institution's own website.

Cite every external fact (`skills/conventions/quality.md`). The brain is the floor;
external research fills the gap.

### 4. Write the page

#### CREATE path

1. File it by kind — `person` → `people/<slug>.md`, `institution` →
   `institutions/<slug>.md` (`_brain-filing-rules.md`). Slug form is
   canonical per `skills/conventions/page-kinds.md`: `<surname-firstname>` for
   people (e.g. `setliff-ian`, `de-carvalho-renan` — particles stay with
   the surname token), readable short form for institutions. Never use
   `<firstname-surname>` for a person; the back-link wiring in
   `paper-ingest` and `grant-ingest` depends on surname-first. For a
   promote-from-ledger call, the slug arrives pre-fixed — use it as-is.
2. Set the shared frontmatter spine and per-kind fields (`skills/conventions/frontmatter.md`).
   Set a reasonable initial `importance`, or leave it for the recompute pass.
   For a promote-from-ledger person page, **populate `author_on:` from
   the ledger entry's `citations:`** — the typed authorship edge
   materializes the moment the page exists. Copy `orcid` and
   `affiliations` from the ledger seed when present.
3. Write the body to the template below — depth matched to tier.
4. Cite every substantive fact, or flag it `[needs-citation]`.
5. Link forward: wikilink the papers, labs, and projects the entity connects to;
   add typed edges (`author_on:` for paper authorship on a person page;
   `links:` for everything else).
6. Omit a section rather than filling it with boilerplate. A short honest page
   beats a padded one.
7. For a promote-from-ledger call: after the page is written
   successfully, **signal back to paper-ingest** so it can remove the
   source ledger entry. The two writes are paired — a page exists or a
   ledger entry exists for the slug, never both
   (`skills/conventions/author-ledger.md`).

#### UPDATE path

1. Read the page's current state first — never blind-overwrite. If it was edited
   very recently, append or hold (`brain-ops/SKILL.md`).
2. Add the new signal where it belongs; revise the assessment only if the new
   information materially changes the picture.
3. **Never overwrite Bryan's own words or assessments** with an external source.
   His direct statements are the highest-authority source (`skills/conventions/quality.md`).
4. When a new fact contradicts what the page holds, record both with their
   citations — do not silently pick one.
5. Add any new forward links the update implies.

### 5. Cross-link

When enriching a person, update their lab's `institution` page if new signal
surfaced, and vice versa. Link forward only — never hand-write a backlinks
section; inbound edges are derived (`skills/conventions/graph-and-links.md`).

## Page templates

Templates are a ceiling, not a quota. Drop any section you have nothing real for.

### Person page

```markdown
---
kind: person
slug: jane-researcher
title: "Jane Researcher"
role: PI                                     # or Staff Scientist | postdoc | student | collaborator | etc.
affiliation: institutions/example-university # primary institutional home
orcid: "0000-0001-2345-6789"                 # when known
importance: 0.5
author_on:                                   # typed authorship edge — papers this person authored
  - papers/some-paper-2024
  - papers/another-paper-2025
# Lab membership (optional — only for members of Bryan's lab):
member_of: institutions/example-lab          # the lab, distinct from affiliation (the university)
lab_status: current                          # current | alumni — alumni keep pages and edges
pillar: ai-research-engineering              # lab pillar, free-text token
pillar_role: lead                            # lead | co-lead | member
expertise: [antibody language models, model training]
works_on:                                    # typed edge to projects — same pattern as author_on
  - projects/antibody-language-models
links: [institutions/example-university, projects/repertoire-modeling]   # everything that isn't authorship or works_on
tags: []
---
```

# Jane Researcher

> One paragraph: who they are, their research focus, and how their work touches
> Bryan's program.

## Research focus
What they work on, in their own scientific terms.

## Relevance to the program
Which of Bryan's threads their work bears on, and how (tie to `RESEARCH.md`).

## Key papers
Forward links to `paper` pages — `[[papers/<slug>]]`. The narrative
selection of standout work; the full authorship list lives in
`author_on:`.

## Collaboration context
How Bryan knows them — co-author, lab alum, meeting contact, prospective
collaborator — and the current state of that relationship.

## Assessment
An honest read where one is useful: strengths, where their work is strong or
thin, how it complements Bryan's. Omit if there is nothing substantive to say.
```

### Institution page

```markdown
---
kind: institution
slug: example-lab
title: "Example Lab, University of Somewhere"
importance: 0.5
links: [people/jane-researcher]
tags: []
---

# Example Lab, University of Somewhere

> One paragraph: what this is — a lab, university, consortium, or funder — and
> why it matters to the program.

## What it is
The nature of the institution and its research scope.

## Relevant people and labs
Forward links to `person` pages and, for a university or consortium, the
specific labs that matter — `[[people/<slug>]]`, `[[institutions/<slug>]]`.

## Funding role
*Funders only.* Its role in Bryan's funding picture and the relevant programs
or mechanisms (cite NIH RePORTER or the funder's own pages).

## Relevance to the program
Why this institution sits on the research program — collaboration, output Bryan
tracks, or a funding relationship.
```

## Anti-patterns

- **Creating a `people/` page for a paper author who hasn't crossed
  the ledger threshold.** Paper authors are gated by the ledger
  citation count, not by judgment. If an entry exists in
  `people/_ledger.yaml` for the slug, the right thing to do is let
  the next paper-ingest pass accumulate citations until promotion
  fires — not to short-circuit the gate from here.
- **Leaving the source ledger entry in place after a successful
  promote-from-ledger create.** The pairing is a hard contract from
  `author-ledger.md`: page exists *or* ledger entry exists, never
  both. Signal back to paper-ingest so it removes the entry in the
  same write.
- **Failing to populate `author_on:` from `citations:` on a
  promote-from-ledger page.** The typed authorship edge is the whole
  reason for the ledger split; writing the page without it loses the
  citation data the threshold was built on.
- Creating a thin page with no real content (the old "light tier" —
  use the ledger instead for paper authors; for institutions or
  non-author people, judge the gate and skip if marginal).
- Going external before searching the brain.
- Writing a fact with neither a citation nor a `[needs-citation]` flag.
- Overwriting Bryan's own assessment with external boilerplate.
- Padding a notable-tier entity into a full dossier.
- Hand-writing a backlinks section instead of linking forward.
- Creating a page for a non-notable one-off mention.
