---
name: enrich
description: Create and update person and institution pages — who someone is, their research focus, the work relevant to your human's program, and an honest assessment where it helps. Scale effort to importance.
triggers:
  - "enrich"
  - "create person page"
  - "update institution page"
  - "who is this person"
  - "look up this lab"
  - "a new collaborator or funder is mentioned"
eval_contract:
  goal: Turn a named person or institution into a brain page with real, cited content, gated correctly by how it arrived and scaled to its importance.
  dimensions:
    - "GATING — ledger-promoted authors page deterministically; every other entity passes the judgment gate"
    - "LEDGER DISCIPLINE — paper authors below threshold stay in the ledger; page-or-entry, never both"
    - "PROVENANCE — every substantive fact is cited or flagged; the human's own assessments are never overwritten"
    - "TIERING — effort matches the entity's load-bearingness"
  hard_fails:
    - Creating a paper-author page without a satisfied promotion condition or explicit human override, or racing another writer's ledger pass.
    - Leaving a promoted author's source ledger entry in place, or writing the page without `author_on:` from `citations:`.
    - Overwriting your human's own words with external boilerplate.
---

# Enrich — person and institution pages

Turn a name into a useful brain page. A `person` page records who someone is and
how their work touches your human's program; an `institution` page records what a lab,
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
- your human's own assessments are never overwritten with external boilerplate.
- Links run forward only — wikilinks in prose, typed edges in frontmatter.

## Entry and identity

- **Normal enrichment:** identify whether the subject is a person or institution;
  search existing pages and, for paper authors, the ledger before going external.
  Existing page → UPDATE. New subject → apply `quality.md`'s notability gate.
  Collaborators, grant personnel and research-relevant institutions have their
  own source-backed roles; incidental author mentions do not bypass the ledger.
- **Ledger promotion:** the paper-ingestion parent supplies the fixed slug and
  seed (`name`, `orcid`, `affiliations`, `citations`) after the threshold in
  `author-ledger.md` fires, or after an explicit human override. Do not reapply
  the judgment gate. An existing ledger entry does not prove it is below
  threshold; inspect its verified citations and the caller's authorization.

For promotion, load `skills/paper-ingest/references/author-ledger-mutation.md`
and perform this operation under the parent's exclusive mutation ownership:

1. Verify the source entry and identity against the cited papers and any
   available ORCID, name variants, and affiliations. Each citation must really
   name this author; count alone is not identity evidence. Keep the verified
   incumbent slug; conflicts return to the parent for resolution, not re-slugging.
2. Recheck the ledger and exact person-page path immediately before writing.
   If another writer owns the pass, hold. If the page now exists, verify the
   same identity and UPDATE, unioning verified authorship without losing its
   existing content. Otherwise gather and CREATE as below.
3. Carry every verified ledger citation into `author_on:` and preserve supplied
   ORCID/affiliation evidence. Read back its YAML, source claims and complete
   `author_on:` list; return its exact path, slug and outstanding obligations.
4. The parent verifies the page and removes only the source ledger entry using
   the shared mutation procedure, then reads back the transition and unrelated
   entries. Run scoped frontmatter lint on the page and ledger after that
   transition: the linter rejects their temporary coexistence even with
   `--paths`. A written person page alone is not a completed promotion. A
   standalone manual-override run owns that parent work itself.

Paper authors below threshold remain in the ledger unless a deliberate human
promotion or independently established non-author role authorizes their page.
No concurrent worker writes the ledger or creates authors out of band.

## Scale and source gathering

| Tier | Subject | Effort |
|---|---|---|
| Key | Close collaborator, co-PI, or active funder | Research focus, relevant papers, collaboration context, and a sourced assessment |
| Notable | Recurring author or tracked institution | A substantive identity/relevance summary and selected forward links |

Ledger promotion defaults to Notable; a separately established key role can
justify more. Do not create a thin author page merely to resolve a graph edge.

### Gather what the tier needs

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

## Write the page

#### CREATE path

1. File it by kind — `person` → `people/<slug>.md`, `institution` →
   `institutions/<slug>.md` (`_brain-filing-rules.md`). Slug form is
   canonical per `skills/conventions/page-kinds.md`: `<surname-firstname>` for
   people (e.g. `setliff-ian`, `de-carvalho-renan` — particles stay with
   the surname token), readable short form for institutions. Never use
   `<firstname-surname>` for a person; the back-link wiring in
   `paper-ingest` and `grant-ingest` depends on surname-first. For a
   promote-from-ledger call, the verified slug from the promotion
   operation arrives pre-fixed — use it as-is.
2. Set the shared frontmatter spine and per-kind fields (`skills/conventions/frontmatter.md`).
   Set a reasonable initial `importance`, or leave it for the recompute pass.
   For a promote-from-ledger person page, `author_on:`, `orcid`, and
   `affiliations` come from the ledger seed per the promotion operation.
3. Write the body to the template below — depth matched to tier.
4. Cite every substantive fact, or flag it `[needs-citation]`.
5. Link forward: wikilink the papers, labs, and projects the entity connects to;
   add typed edges (`author_on:` for paper authorship on a person page;
   `links:` for everything else).
6. Omit a section rather than filling it with boilerplate. A short honest page
   beats a padded one.

#### UPDATE path

1. Read the page's current state first — never blind-overwrite. If it was edited
   very recently, append or hold (`brain-ops/SKILL.md`).
2. Add the new signal where it belongs; revise the assessment only if the new
   information materially changes the picture.
3. **Never overwrite your human's own words or assessments** with an external source.
   His direct statements are the highest-authority source (`skills/conventions/quality.md`).
4. When a new fact contradicts what the page holds, record both with their
   citations — do not silently pick one.
5. Add any new forward links the update implies.

## Cross-link

When enriching a person, update their lab's `institution` page if new signal
surfaced, and vice versa. Link forward only — never hand-write a backlinks
section; inbound edges are derived (`skills/conventions/graph-and-links.md`).

## Close out with the parent

A chained enrich (from `paper-ingest`, `grant-ingest`, `academic-verify`, or any
other parent that owns a ledger pass or a batch) reports back to that parent:
the exact paths created or updated, the verification results (read-back,
scoped lint), and — for a ledger promotion — the signal that the parent must
remove the source ledger entry and verify the removal. The parent owns the
coherent commit; this skill's own standalone runs close their pages through
`skills/git-ops/SKILL.md` as usual.

## Page templates

Templates are a ceiling, not a quota. Drop any section you have nothing real for.

### Person page

```markdown
---
kind: person
slug: researcher-jane
title: "Jane Researcher"
role: PI                                     # or Staff Scientist | postdoc | student | collaborator | etc.
affiliation: institutions/example-university # primary institutional home
orcid: "0000-0001-2345-6789"                 # when known
importance: 0.5
author_on:                                   # typed authorship edge — papers this person authored
  - papers/some-paper-2024
  - papers/another-paper-2025
# Lab membership (optional — only for members of your human's lab):
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

# Jane Researcher

> One paragraph: who they are, their research focus, and how their work touches
> your human's program.

## Research focus
What they work on, in their own scientific terms.

## Relevance to the program
Which of your human's threads their work bears on, and how (tie to `RESEARCH.md`).

## Key papers
Forward links to `paper` pages — `[[papers/<slug>]]`. The narrative
selection of standout work; the full authorship list lives in
`author_on:`.

## Collaboration context
How your human knows them — co-author, lab alum, meeting contact, prospective
collaborator — and the current state of that relationship.

## Assessment
An honest read where one is useful: strengths, where their work is strong or
thin, how it complements your human's. Omit if there is nothing substantive to say.
```

### Institution page

```markdown
---
kind: institution
slug: example-lab
title: "Example Lab, University of Somewhere"
importance: 0.5
links: [people/researcher-jane]
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
*Funders only.* Its role in your human's funding picture and the relevant programs
or mechanisms (cite NIH RePORTER or the funder's own pages).

## Relevance to the program
Why this institution sits on the research program — collaboration, output your human
tracks, or a funding relationship.
```

## Anti-patterns

- Calling promotion complete before the identity, authorship, and parent-owned
  ledger transition in the promotion operation are verified.
- Creating a thin author page to resolve an edge rather than retaining a ledger
  entry; apply the normal notability gate to non-author people and institutions.
- Going external before searching the brain.
- Writing a fact with neither a citation nor a `[needs-citation]` flag.
- Overwriting your human's own assessment with external boilerplate.
- Padding a notable-tier entity into a full dossier.
- Hand-writing a backlinks section instead of linking forward.
- Creating a page for a non-notable one-off mention.
