# Gap Map Template

> Working document for Phase 6.1. Write to `working-docs/gap-map-<topic>.md`.
> Each gap must satisfy: existence (high-confidence gap), addressability
> (literature likely exists to close it), and meaningfulness (leaving it
> unfilled means incomplete understanding). No minimum or maximum — zero
> is a valid count.

## Meaningful Gaps

### 1. <Short gap title>

<One paragraph describing the gap: what specifically is missing, why the
ingested reviews don't cover it, and why leaving it unfilled would mean
incomplete understanding. Be concrete — name the missing paper, the
unanswered mechanistic question, or the unexplored axis.>

**Query:** <The natural-language query that will be run in the supplementary
pass — against the available semantic search (paperclip, when present)
and a domain-appropriate keyword index (PubMed for biomedical topics). Phrase it as a specific
research question, not keywords.>

---

## Worked example (illustrative shape)

### 1. Mechanism B behind an observed phenomenon A

Paper X demonstrated phenomenon A, and the review cites it as
established, but the proposed mechanism B is contested: two ingested
papers assume it while a third's data are equally consistent with an
alternative mechanism C that no ingested paper tests directly. The
review names mechanism B without discussing the competing evidence,
and no Phase 1 query targeted C's vocabulary.

**Query:** What evidence distinguishes mechanism B from mechanism C in
<system>? Which predictions of B have been directly tested?

### 2. Quantitative constraint the corpus asserts but never measures

The corpus repeatedly describes <quantity> qualitatively ("large",
"dominant") without a measured value. A methods or benchmarking paper
that quantifies it would change how the corpus's comparative claims are
read, but no ingested paper measures it and the review's coverage of
measurement approaches is thin.

**Query:** How is <quantity> measured in <system>, and what values are
reported across conditions?
