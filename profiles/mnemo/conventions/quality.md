# Convention: page quality

Cross-cutting quality rules for every skill that writes to the brain. These
operationalize the `SOUL.md` spine (cite-or-flag, no fabricated confidence) for
the page; they do not restate it.

## Citations

Every substantive claim on a page carries a verifiable source or an explicit
needs-citation flag. This is the `SOUL.md` cite-or-flag rule applied to the page
— never softened, never skipped.

Inline citation forms:

- **A paper** — peer-reviewed or preprint — cite the page and its identifier:
  `[Source: papers/<slug>, doi:10.xxxx/...]`. The DOI/PMID resolves the claim to
  a real-world object.
- **Your human, directly** — `[Source: your-human, <context>, YYYY-MM-DD]`. Their direct
  statements are the highest-authority source.
- **The open web or an API** — `[Source: <publication>, <URL>, YYYY-MM-DD]`.
- **Synthesis across pages** — `[Source: compiled from <slugs>]`.
- **Not yet sourced** — `[needs-citation]`. An honest flag, never a silent gap.

When two sources conflict, record the contradiction with both citations. Do not
silently pick one — surfacing the conflict is the point.

Source precedence, highest to lowest: your human's direct statements → the primary
literature → a brain page's compiled synthesis → the open web.

## Quoted figures are verified against the primary source

A figure quoted in produced prose — a percentage, a case count, an efficacy
number — is verified against the primary source before it is quoted, not
inherited from a secondary source's paraphrase. Secondary sources paraphrase
loosely: a review's "approximately 50% of children had detectable CARDS
toxin" may rest on a primary study reporting 64% organism detection in cases
against 56% in healthy controls — a different and weaker claim (a real
observed instance: Maselli 2018 paraphrasing Wood 2013). Where the figure cannot be verified against the
primary text (paywall, abstract-only), either quote the primary source's own
abstract language, or flag the mismatch and withhold the figure until the
body text is in hand. A paraphrase mismatch that survives into prose is a
citation error even when the citation is real.

## Verbatim and distillation

A brain page distills — it is the mind's analysis, not a dump of the source. But
"distill" governs the *analysis*; it is not a blanket ban on verbatim text.
Verbatim is correct, and required, when the exact wording is itself the
information and paraphrase would corrupt it:

- **An author's own abstract** — the authors' canonical summary of their own
  work. Preserve it verbatim rather than risk distorting their framing.
- **Your human's own writing** — grant prose, their stated reasoning. Their voice is a
  source the mind learns from; paraphrase destroys it.
- **A quotable line** worth referencing later — a literal quote, never reworded.

A page may carry both: a verbatim block (the source's words, preserved intact)
*and* a distilled analysis section (the mind's own read). They are different
sections doing different jobs — not a contradiction.

## Linking — forward only

Link generously, and link **forward only**. When a page mentions another page,
add the edge *on the page you are writing*: a `[[<kind>/<slug>]]` wikilink in the
prose, or a typed edge (`links:`, `cites:`, `supports:`, `refutes:`) in the
frontmatter. See `graph-and-links.md` for which form to use.

**Never hand-write a backlinks section.** Inbound edges are *derived* — computed
by scanning the corpus, or shown live by Obsidian's backlinks pane. An unlinked
mention is a thin page; a hand-maintained backlink list is a stale one.

## The notability gate

Not everything earns a page. Before creating one, ask whether it is load-bearing
for the research program:

- **A paper / method / concept** — will the mind or your human reference it again?
  Does it sit on a thread in `RESEARCH.md`?
- **A person** — for **paper authors specifically**, the gate is the
  citation threshold in `conventions/author-ledger.md`: non-paged authors
  accumulate in `people/_ledger.yaml`, and a `people/` page is created
  when the count crosses 5. Do not judge paper-author page creation case-
  by-case — that is what the ledger replaces. For **non-paper-author
  people** (a meeting attendee, a grant program officer, a lab head
  mentioned in passing), the judgment still applies: a collaborator,
  student, postdoc, or recurring figure earns a page; one-off mentions
  do not.
- **An institution** — a lab, university, consortium, or funder that sits
  on the research program: somewhere your human collaborates, a funder they
  applies to, a lab whose output he tracks.
- **A hypothesis** — a genuinely testable claim worth tracking evidence on?

When in doubt, do not create. A missing page is cheap to add later; a junk page
dilutes search and buries the pages that matter.
