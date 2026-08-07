# Brain filing rules — shared reference for every skill that writes a page

Where a new page goes. The companion to `skills/conventions/page-kinds.md`
(the page kinds and their directories) and `frontmatter.md` (the schema).

## The rule

**The primary subject of the content determines the page kind.** Not the format
it arrived in, not the source it came from, not the skill that is running. A PDF
about a method is a `method` page; an email mentioning a collaborator updates a
`person` page. The container is irrelevant — the subject is everything.

## Decision protocol

1. Name the primary subject: is it a paper, a technique, a principle, a testable
   claim, a research thread, a funding application, a meeting, a person, an
   institution, a piece of first-person thinking, a deadline?
2. File it under the matching kind (`page-kinds.md` maps kind → directory).
3. Set `kind` in frontmatter to agree with the directory.
4. Link it to neighbouring pages (`graph-and-links.md`) — forward edges only.
5. Tie-breaker: what would you search for to find this page again? File it there.

## One source, several pages

A single raw source often distills into more than one page — a paper introduces
a method *and* supports a hypothesis. File each facet under its own kind and link
them. Do not force one page to carry subjects that belong to different kinds.

The raw source itself is **never** a brain page: it goes to the raw-source
archive, and each page distilled from it carries the git pointer in its
`sources:` frontmatter. See `conventions/raw-source-archive.md`.

## Scope boundary

There is no kind — and therefore nowhere to file — personal-life content or
lab-state management (student cadence, ordering, equipment). If content has no
home among the page kinds, that is the structural signal it is out of scope
(`page-kinds.md`, `VISION.md` §6). Do not invent a directory for it.

## The notability gate

Filing a page is a commitment. Apply the notability gate in
`conventions/quality.md` before creating one — a missing page is cheap, a junk
page is not.
