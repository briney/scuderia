# Output Rules

Cross-cutting output quality standards for all brain-writing skills.

## Deterministic Links

All links MUST be deterministic — built from actual data, not composed by the
LLM. Never guess a URL or path. Build it from the slug, the identifier, the
commit hash, or the API response.

- Brain page → brain page: a `[[kind/slug]]` wikilink (see
  `skills/conventions/graph-and-links.md`).
- A reference in delivered output (chat, a brief): a markdown link, or a
  commit-pinned GitHub permalink — `[abc1234](https://github.com/{owner}/{repo}/commit/abc1234)`.
- External links: use the actual URL from the source, never reconstruct it.
- A paper: prefer the DOI/PMID identifier over a guessed publisher URL.

## No Slop

Brain pages are not chat output. They are durable knowledge artifacts.

- No filler phrases ("It's worth noting that...", "Interestingly...")
- No hedging when facts are cited ("According to the source, X is true" not "X might be true")
- No LLM preamble ("I've created...", "Here's the updated...", "Certainly!")
- No placeholder dates ("YYYY-MM-DD", "recently", "in the near future")
- Short paragraphs. Concrete facts. Inline citations.

## Exact Phrasing Preservation

When capturing your human's original thinking — a hypothesis, an objection, a framing
— use his exact words. Don't paraphrase. Don't clean up grammar. The language IS
the insight.

- Direct quotes: preserve verbatim in quote blocks
- Ideas and framings: use your human's own terminology for slugs and titles
- Observations: capture the phrasing, not a sanitized version

## Title Quality

Page titles should be:
- Descriptive enough to identify the page from a search result
- Short enough to scan in a list (under 60 characters)
- NOT sentences ("Preferential masking ablation" not "A meeting where we discussed the preferential masking ablation results")
- NOT generic ("Repertoire drift under chronic antigen exposure" not "Hypothesis page")
