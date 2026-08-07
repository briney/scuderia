# Convention: the graph layer — links and backlinks

The brain is a graph. Edges are expressed in two markdown-native ways, and
backlinks are **derived, never stored**. Authoritative source: `DESIGN.md` §2.4.

## Two edge forms

**1. Wikilinks in body prose** — the Obsidian-native form:

```markdown
This rests on [[methods/preferential-masking]] and contradicts the
drift model in [[concepts/repertoire-drift]].
```

Wikilinks keep the graph navigable directly in the Obsidian vault. Use them
freely wherever one page mentions another in running prose.

**2. Typed links in frontmatter** — structured, queryable edges:

```yaml
links: [methods/preferential-masking, concepts/repertoire-drift]
cites: [papers/foundational-result-2019]
supports: [hypotheses/masking-improves-generalisation]
refutes: [hypotheses/drift-is-purely-stochastic]
```

`links:` is the general typed-edge list on the spine. Edge-typed lists carry the
graphs that matter: `cites:` carries the citation graph; `supports:` / `refutes:`
carry the hypothesis evidence graph; `authors:` on a paper and `author_on:` on a
person carry the authorship graph. Use a typed edge when the *relationship*
needs to be queryable — not just the fact that two pages are related.

## Authorship is a co-written typed edge

The authorship graph is split across two pages: a `paper` page lists every
author under `authors:` (`people/<slug>` entries — every author, always —
see `paper-ingest`); the corresponding `person` page lists every paper
under `author_on:`. Both halves are forward edges; both halves are written
by `paper-ingest` at ingest time. The person-side half is **co-written by
the skill that authors the paper page**, not derived after the fact — this
keeps the forward-only discipline intact (a forward edge is owned by the
page it sits on, even when the same skill writes both pages in one run).

For authors without a `people/` page, the `author_on:` edge is not written
— there is nothing to write it to. The authorship signal is instead
accumulated in `people/_ledger.yaml` (`author-ledger.md`), and the typed
edge materializes when the ledger entry crosses the promotion threshold
and a page is created.

## The synthesis-layer edges

The concept → hypothesis → project/grant pipeline is wired with forward-only,
child-declares-parent typed edges. The child page owns the edge; the parent's
inbound view is a derived backlink.

```yaml
# on a hypothesis page — which concept intersection birthed it
draws_on: [concepts/data-constrained-generative-modeling, concepts/diffusion-language-models]

# on a project/grant page — the concepts it rests on, and the hypothesis it came from
rests_on: [concepts/data-constrained-generative-modeling]
promoted_from: [hypotheses/discrete-diffusion-ablm-data-efficiency]

# on a concept page — recorded sibling relationships
related_concepts: [concepts/diffusion-language-models]
```

The **hypothesis evidence graph** reuses the existing `supports:` / `refutes:`
edges: a `paper` (or `concept`) carries `supports: [hypotheses/<slug>]` or
`refutes: [hypotheses/<slug>]`, and the hypothesis accrues those as derived
backlinks. This graph was defined here from the start; the synthesis layer is its
first consumer. A concept's crystallized children, a hypothesis's promotions, and
a hypothesis's evidence are **all derived** — never hand-written.

## Backlinks are derived

A page's inbound edges are **computed by scanning the corpus**, never written by
hand. Link and timeline extraction over the brain is a mechanical pass — a body
capability provided by the harness, or surfaced live by Obsidian's own backlinks
pane. Do not maintain a backlinks section in markdown.

## Targets

Link targets are `kind/slug` references (e.g. `methods/preferential-masking`) —
the same identity used everywhere. A link to a page that does not exist yet is
acceptable: it marks an edge worth filling, not an error.
