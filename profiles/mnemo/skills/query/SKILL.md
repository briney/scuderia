---
name: query
description: Answer a question from the brain's knowledge — search, read, synthesize, cite. Use when Bryan asks what the brain knows about a topic, a paper, a person, or how pages connect.
triggers:
  - "what do we know about"
  - "tell me about"
  - "background on"
  - "who is"
  - "what's the evidence on"
  - "how does X connect to Y"
  - "what links to"
---

# Query — answer from the brain

Answer a question using what the brain knows, grounded and cited. The job is not
to recite a search result — it is to synthesize an answer and trace every claim
back to a page.

> **Conventions:** `skills/conventions/brain-first.md` (the lookup chain),
> `skills/conventions/quality.md` (citations), `skills/conventions/graph-and-links.md` (the
> graph), `skills/conventions/capabilities.md` (the harness contract).

## Capabilities

`brain-search`, `brain-read`. `brain-search` is optional — under harnesses
without it, falls back to keyword scan over the corpus (loses semantic
ranking).

## What this guarantees

- Every answer is grounded in brain content — no fabricated confidence.
- Every claim traces to a specific page slug or real-world identifier.
- Gaps are stated plainly, never papered over.
- When pages conflict, the conflict is surfaced, not silently resolved.

## Phases

1. **Decompose the question.** A factual lookup, a conceptual question, or a
   relational/graph question — each wants a different search.
2. **Search the brain.** Run the question through `brain-search`. Search
   returns ranked *excerpts*, not whole pages — often the excerpt alone answers
   the question.
3. **Read the pages.** When an excerpt confirms a page is relevant, open the file
   for the full picture. "Tell me about X" wants the whole page; "is there
   anything on Y" is answered by the excerpt.
4. **Follow the graph for relational questions.** "How does X connect to Y",
   "what supports this hypothesis", "what cites this paper" — walk the `links:` /
   `cites:` / `supports:` / `refutes:` edges and the wikilinks. Inbound edges
   (backlinks) are found by searching the corpus for `[[kind/slug]]` references.
5. **Synthesize and cite.** Compose the answer; attach a citation to every claim
   — the page slug, or the DOI/PMID the page rests on. When pages disagree,
   present both with their citations.
6. **Flag the gaps.** If the brain has nothing on part of the question, say so —
   "the brain has nothing on X" — and offer to research it. An honest gap beats
   a confident guess.

## Source precedence

When sources conflict, weight them: Bryan's direct statements → the primary
literature → a brain page's compiled synthesis → the open web. Surface the
contradiction with both citations; do not silently pick a winner.

## Output

- A direct answer to the question.
- Inline citations: "...as shown in [[papers/<slug>]] [Source: doi:10.xxxx/...]".
- Explicit gap flags where the brain is thin.
- Conflict notes where pages disagree.

## Anti-patterns

- Answering from general knowledge when the brain has relevant pages.
- Stating a claim the brain does not support.
- Silently choosing one source when sources conflict.
- Loading whole pages when a search excerpt already answers the question.
- Treating a thin brain as a complete one — name the gap.
