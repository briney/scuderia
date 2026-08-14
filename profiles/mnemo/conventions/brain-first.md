# Convention: brain-first lookup

**Read this before any lookup — an entity, a paper, a fact, a thread of work.**

The brain almost always already knows something. External research fills gaps;
it does not start from scratch. Check the brain first, every time.

## The lookup chain

1. **Search the brain.** Run the topic, name, or question through
   `brain-search` (`conventions/capabilities.md`). Under the reference
   harness (Hermes) this binds to qmd's hybrid keyword + vector search
   with a reranker (`DESIGN.md` §2.7); under harnesses without qmd it
   degrades to keyword scan. Search returns ranked excerpts, not whole
   pages.
2. **Read the page.** When an excerpt confirms a page is relevant, open the file
   directly — `<kind>/<slug>.md` — for the full picture.
3. **Follow the graph.** A page's `links:` / `cites:` / `supports:` edges and its
   wikilinks lead to neighbouring pages; inbound edges (backlinks) are found by
   searching the corpus for `[[<kind>/<slug>]]` references.
4. **Only then go external.** Open-API research (PubMed, arXiv, bioRxiv,
   CrossRef, NIH RePORTER) and the open web are for what the brain does not yet
   hold — not a substitute for steps 1–3.

## Rules

- **The brain answered → use it.** Do not reach for an external API when a brain
  page already covers the question.
- **The user model is separate from the brain.** For who-your-human-is questions
  (taste, blind spots, how to engage him) use `user-model-query` — returns
  `{declared: USER/<name>.md}` on every harness. The brain holds the *work*
  (papers, methods, hypotheses, grants, threads); the user model holds the
  *person*. See `DESIGN.md` §7.
- **Cite what you find.** A fact carried out of the brain keeps its citation back
  to the page slug or the real-world identifier (DOI, PMID) it rests on.
- **A missing page is signal.** If the brain has nothing on a topic that matters,
  that gap is itself worth surfacing — and often worth filling.

## Propagating the convention

When a skill spawns a sub-agent that will touch the brain, point it here:

> Read `skills/conventions/brain-first.md` before starting.
