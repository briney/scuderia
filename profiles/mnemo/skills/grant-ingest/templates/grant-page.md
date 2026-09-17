# Grant page template

Copy-and-fill when writing the `grant` page during a grant-ingest. The
frontmatter spine and section order are the contract; the comments mark
what each field carries. Source: `skills/grant-ingest/SKILL.md` (owner);
`skills/conventions/frontmatter.md` (the `grant` schema),
`skills/conventions/raw-source-archive.md` (the `sources:` entries).

```markdown
---
kind: grant
slug: <slug>
title: "<grant title>"
funder: institutions/<slug>
mechanism: "R01"            # or the foundation program — free text, not an enum
role: PI                    # PI | co-PI | co-I | consultant
status: scored-not-funded   # full lifecycle enum in skills/conventions/frontmatter.md
score: 34                   # impact score, if reviewed — else omit
percentile: 22              # if scored — else omit
submitted: YYYY-MM-DD
decision_date: YYYY-MM-DD   # if reviewed — else omit
deadline: YYYY-MM-DD        # next actionable deadline — the attention contract reads this
importance: 0.0
links: [people/<pi-slug>, people/<co-i-slug>, projects/<slug>, methods/<slug>, concepts/<slug>]
tags: []
sources:
  - role: research-strategy
    hash: sha256-...
    r2_key: grants/....pdf
    filename: "..."
    ingested: YYYY-MM-DD
    provenance: "ingested grant package, YYYY-MM-DD"
  - role: summary-statement
    hash: sha256-...
    r2_key: grants/....pdf
    filename: "..."
    ingested: YYYY-MM-DD
    provenance: "ingested grant package, YYYY-MM-DD"
---

# <Title>

## Summary
The project summary, distilled — against what the brain already holds.

## Specific Aims
Each aim's goal, in the mind's words. The verbatim aims sit in `## Verbatim`.

## Significance & Innovation
What the grant claims is significant and new, distilled.

## Preliminary Data
Each preliminary result, tied to its figure or caption — and where it
propagated (which `concept` or `method` page).

## Approach
The key methods and experimental designs, linked to `method` / `concept` pages.

## Future Directions
Work the grant proposes beyond the current period.

## Review
Scores, percentile, outcome. Critique themes paraphrased. Actionable
resubmission concerns called out separately. Omit the section if unreviewed.

## Analysis
Where this lands on your human's active threads — what it advances, what it
contradicts, what it opens. What your human would not have noticed.

## Key citations
One bullet per key citation. Each bullet has three pieces: the wikilink to the
paper page (a stub or a full page), a one-line why-foundational, and the
verbatim citation entry as a blockquote child.

- [[papers/<slug>]] — <one-line why this is foundational to the grant>.
  > <Authors>. <Title>. <Venue>. <Year>;<volume>(<issue>):<pages>.
  > doi:<doi-if-present>

## Verbatim
your human's preserved prose — the corpus the grant-writing skills learn their voice
from. One subsection per science document, intact, figure captions kept.

### Specific Aims (verbatim)
> ...

### Research Strategy (verbatim)
> ...the prose, with critiques interleaved:
> [!critique] Reviewer 2 — Approach
> "Aim 3 is overambitious for the timeline." Recurs in R21-XXXXXX review.
```
