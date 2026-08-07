---
name: citation-fixer
description: Audit and fix citations across brain pages — find substantive claims with no source, repair malformed citations to the standard format, and honestly flag the genuinely uncitable. Runs as a focused fix or chains from maintain.
triggers:
  - "fix citations"
  - "fix broken citations"
  - "citation audit"
  - "check citations"
  - "citation fixer"
---

# Citation fixer — every claim sourced or flagged

A page where claims drift loose from their sources is a page that quietly lies.
This skill enforces the `SOUL.md` cite-or-flag rule across the brain: every
substantive claim carries a verifiable source or an honest `[needs-citation]`
flag — never a silent gap, never an invented citation. This is the
**citation-claim** member of the audit cluster; see `RESOLVER.md` "Audit
cluster" for the scope split — frontmatter shape lives in
`frontmatter-guard`, broad health lives in `maintain`.

> **Conventions:** `skills/conventions/quality.md` (the canonical citation forms and
> source precedence), `skills/conventions/test-before-bulk.md` (sweeping many pages),
> `_output-rules.md` (deterministic links — built from data, never composed),
> `skills/conventions/capabilities.md` (the harness contract).

## Capabilities

`brain-read`, `brain-write`, `fetch-url` (`pubmed-fetch`,
`crossref-fetch`) — for verifying citations against the literature.

## What this guarantees

- Every substantive claim on a scanned page is checked for an inline citation.
- Claims with no source are flagged at their exact location.
- Malformed citations are rewritten to match `skills/conventions/quality.md`.
- A genuinely uncitable claim is flagged `[needs-citation]` — never invented,
  never deleted.
- Results are reported with counts: pages scanned, citations fixed, gaps
  remaining.

## Phases

1. **Scan.** Read each page in scope. For a focused fix that is one page or a
   handful; for a sweep, search the brain to gather candidates (pages with many
   factual sentences and few `[Source: ...]` markers are the priority).
2. **Identify issues.** On each page, look for:
   - A substantive claim — a result, a number, an attribution — with no inline
     citation at all.
   - A citation missing its date.
   - A citation missing its source type (paper, Bryan, web, synthesis).
   - A citation in the wrong shape — not one of the forms in `quality.md`.
3. **Fix the malformed citations.** Rewrite each to the canonical form. For a
   claim that rests on a paper, prefer the page's DOI or PMID
   identifier: `[Source: papers/<slug>, doi:10.xxxx/...]`. The identifier
   resolves the claim to a real-world object; a publisher URL does not.
4. **Flag the genuine gaps.** When a claim is real but has no traceable source,
   mark it `[needs-citation]` inline. Do not invent a citation to make the page
   look complete. Do not delete the claim — the fact may be true and worth
   chasing later.
5. **Report.** Count pages scanned, citations fixed, claims newly flagged, and
   gaps remaining.

## Citation forms

The authoritative list is `skills/conventions/quality.md`. In brief:

- **Paper** — `[Source: papers/<slug>, doi:10.xxxx/...]` (DOI or PMID preferred
  over a URL).
- **Bryan, directly** — `[Source: Bryan, <context>, YYYY-MM-DD]`. Highest
  authority — never overwrite his words with a lower source.
- **Open web or API** — `[Source: <publication>, <URL>, YYYY-MM-DD]`.
- **Synthesis across pages** — `[Source: compiled from <slugs>]`.
- **Not yet sourced** — `[needs-citation]`.

When two sources conflict, record both citations and surface the contradiction;
do not silently pick a winner.

## Sweeping many pages

A brain-wide citation audit is a batch operation — follow
`skills/conventions/test-before-bulk.md`: fix 3-5 pages first, read the output, confirm
the citation shapes are right, then run the rest in committed batches so a bad
run is easy to revert.

Priority order for a sweep: recently created or updated pages first (fresh
context makes a missing source easy to recover), then high-traffic pages, then
the long tail.

Before editing any page, confirm it was not touched very recently in Obsidian.
If it was, hold rather than clobber.

## Output

```
Citation audit — <N> pages
  Citations fixed:   <N>
  Claims flagged [needs-citation]: <N>
  Remaining gaps:    <N>
```

## Chains with

- `skills/maintain/SKILL.md` — the broad brain-health audit; chain into this
  skill when it surfaces citation problems.
- `skills/frontmatter-guard/SKILL.md` — structural validation; a separate pass,
  run alongside this one for a full lint.

## Anti-patterns

- Inventing a citation for a claim that has no source — flag it instead.
- Deleting a claim because it lacks a citation — flag it; the fact may be true.
- Fixing a citation without reading enough of the page to know what the claim
  rests on.
- Composing a publisher URL by hand — use the DOI or PMID, the deterministic
  identifier.
- Batch-sweeping the whole brain without testing a few pages first.
- Silently resolving a conflict between two sources instead of recording both.
