---
name: grant-citations
description: Manage a grant's references — resolve every needs-citation flag, verify each citation actually supports its claim, and build the Bibliography & References Cited in one consistent, complete format.
triggers:
  - "fix the grant's citations"
  - "resolve the citation flags"
  - "build the bibliography"
  - "check the references"
  - the pre-submission citation pass
---

# Grant citations — resolve, verify, and format the references

A grant's references are a spine commitment, not a formatting chore: every
substantive claim carries a verifiable citation or an explicit needs-citation
flag (`SOUL.md` §2). This skill closes that loop on a grant in progress — it
resolves the `[needs-citation]` flags `grant-section` and `grant-coherence`
left, verifies that every citation actually supports the sentence it sits on,
and assembles the Bibliography & References Cited.

> **Conventions:** `SOUL.md` §2 (cite-or-flag — spine), `skills/conventions/quality.md`
> (citation discipline, no fabricated citations),
> `skills/conventions/preprint-retrieval.md` (bioRxiv/medRxiv full text around the Cloudflare block),
> `skills/conventions/capabilities.md` (the harness contract),
> `skills/grant-formats/` (the bibliography format and PMCID rule). Chains to
> `skills/query/SKILL.md` and `skills/literature-research/SKILL.md` to find
> sources, `skills/academic-verify/SKILL.md` to confirm they hold, and
> `skills/paper-ingest/SKILL.md` for a foundational reference worth a brain
> page.

## Capabilities

`brain-read`, `brain-write`, `fetch-url` (`pubmed-fetch`, `crossref-fetch`).

## What this guarantees

- Every `[needs-citation]` flag in the grant's `## Draft` is resolved — to a
  real, verified source, or escalated to Bryan as a claim that cannot stand.
- Every citation already in the draft is verified: a real work that actually
  supports the claim it is attached to. No fabricated or misattributed
  citations.
- The Bibliography & References Cited is built in one consistent, complete
  format, with PMCIDs for NIH-funded publications.
- A claim with no real source is surfaced as a **claim problem**, never
  papered over with an invented citation.

## Phases

1. **Collect.** Every in-text citation in the grant's `## Draft`, plus every
   unresolved `[needs-citation]` flag left by `grant-section` and
   `grant-coherence`.

2. **Resolve the flags.** For each `[needs-citation]`: find the source in the
   brain (`skills/query/SKILL.md`), or externally
   (`skills/literature-research/SKILL.md`). If no real source supports the
   claim, that is not a citation problem — it is a claim problem: surface it to
   Bryan and route it to `grant-section`. Never invent or guess a citation to
   clear a flag.

3. **Verify.** Each citation — the one already in the draft and each one just
   added — is a real work that actually supports the sentence it sits on. Chain
   to `skills/academic-verify/SKILL.md`. A citation that does not support its
   claim is a flag back to `grant-section`, not a fix in place.

4. **Format the bibliography.** Assemble Bibliography & References Cited in one
   consistent, complete style — the funder's if the NOFO names one, otherwise a
   standard one held consistent. Include a PMCID for every cited NIH-funded
   publication (`grant-formats/`). Dedup; keep the in-text citation form
   consistent. The bibliography has no page limit.

5. **Write back and report.** Update the in-text citations and the bibliography
   in the grant's `## Draft`; log the pass in `## Drafting log`. Report every
   claim that could not be sourced — those go to Bryan and `grant-section`, and
   they block submission until resolved.

A foundational reference the grant leans on that is not yet a brain page can
chain to `skills/paper-ingest/SKILL.md`, notability-gated — but the job here is
the grant's reference list, not brain-building.

## Output

A grant `## Draft` with every claim cited or escalated, every citation
verified, and a complete, consistently formatted Bibliography & References
Cited. A `## Drafting log` entry. A list — ideally empty at submission — of
claims that could not be sourced.

## Anti-patterns

- Inventing or guessing a citation to clear a `[needs-citation]` flag — an
  unsourced claim is a claim problem, escalated, not a citation to fabricate
  (`SOUL.md` §2).
- Citing a paper without verifying it actually supports the claim it is
  attached to.
- Leaving `[needs-citation]` flags unresolved at submission.
- Imposing a citation style the NOFO or funder does not require — match what
  the announcement asks for, then hold it consistent.
- Treating a claim with no real source as a formatting problem instead of
  escalating it to Bryan.
