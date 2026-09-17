# Borderline link examples

Load only when step 3 leaves a candidate ambiguous. These are illustrative
shapes, not real source evidence or extra eligibility rules.

- “We annotate with NamedTool” refers to a specific tool; if the verified
  target page describes that tool, link NamedTool. “Measured by BLI” uses
  generic technique vocabulary and gets no automatic link to a paper using BLI.
- “Our derivation extends Author 2020” can justify a `cites:` candidate to
  that verified source, but not a body wikilink on the shorthand. “Later,
  Author 2025 extended this derivation” does not justify the reverse edge.
  The same citation in an ingest log records provenance, not an argument.
- “This addresses Named Project (projects/named-project)” explicitly resolves
  the entity: `[[projects/named-project|Named Project]]`. Leave the parenthetical
  path or adjacent Markdown citation intact; no citation edge is implied.
- “Relevant to grants/named-study” can become
  `[[grants/named-study|Named study]]` after verifying the target and title.
  A grant number alone is insufficient; paper→grant navigation is not `cites:`.

If identity or direction remains uncertain, skip. Section labels alone do
not establish whether a citation is load-bearing.
