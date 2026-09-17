---
name: academic-verify
description: Verify a research claim by tracing it — claim → publication → methodology → raw-data availability → independent replication — and recording a verdict. Use when a paper, book, talk, or conversation cites a study and you want to confirm it is real, replicated, and accurately characterized.
triggers:
  - "verify this claim"
  - "is this study real"
  - "check this paper"
  - "trace this to source"
  - "validate this citation"
  - "has this been replicated"
  - "is this retracted"
eval_contract:
  goal: Record an honest, source-grounded verdict on a research claim, traced to primary data rather than the citing author's characterization.
  dimensions:
    - "TRACE — publication, methodology, raw data, and replication are each checked at a primary source"
    - "INTERMEDIARIES — claims cited through another paper are re-anchored to the primary before verdicting"
    - "HONESTY — 'unverifiable' is recorded when the figure cannot be traced; a shallow search is not"
    - "FILING — the verdict lands where the subject lives, with a cited trace table"
  hard_fails:
    - Inventing a lookup or a citation instead of fetching real sources.
    - Saying "verified" without raw-data availability or independent confirmation.
    - Quoting an intermediary's paraphrase as primary evidence.
---

# academic-verify — trace a claim to its source

A research claim is only as good as the chain behind it. This skill traces a
claim from how it was stated, back through the publication, the methodology,
the raw data, and any independent replication — then records a verdict where
the subject of the claim lives.

```
claim → publication → methodology → raw-data availability → independent replication
```

> **Conventions:** `skills/conventions/brain-first.md` (check the brain before going
> external), `skills/conventions/quality.md` (every verdict cites the source data,
> not the author's claim about it), `_brain-filing-rules.md` (file by subject),
> `skills/conventions/capabilities.md` (the harness contract).

## Capabilities

`brain-search`, `brain-read`, `brain-write`, `fetch-url` (`pubmed-fetch`,
`crossref-fetch`, `biorxiv-fetch`, `arxiv-fetch` as needed). `brain-search`
optional; falls back to keyword scan.

## What this guarantees

- A prior verification of the same claim is reused, not redone.
- The verdict rests on the source data — methodology and replication — not on
  the citing author's characterization.
- The verdict is one of five values; an honest "unverifiable" beats a
  confident guess.
- The verdict is filed where the subject lives, with citations.

## Phases

### 1. Scope the claim

Pin down exactly what is being asserted:

- **Quote** — who said what, in what wording?
- **Source** — which paper, dataset, or survey is cited?
- **Quantity** — what specific number or effect is claimed?
- **Baseline / period** — a reduction *from what*, over *what* time range?

A vague claim cannot be verified. Sharpen it first.

### 2. Brain-first lookup

Search the brain for the paper, the authors, and the claim keywords
(`skills/conventions/brain-first.md`). If a `paper` page or a prior verification
`note` already records this trace, reuse it — re-verifying settled work is
wasted effort.

### 3. Trace it externally

For what the brain does not hold, run the lookup with `fetch` against
auth-free open sources. No code — the API knowledge is the prose below.

| Source | What it answers | Endpoint |
|---|---|---|
| PubMed E-utilities | The publication exists; metadata, abstract | `eutils.ncbi.nlm.nih.gov/entrez/eutils/` |
| CrossRef | DOI metadata, publication record | `api.crossref.org/works` |
| OpenAlex | Open citation graph, institutional affiliations | `api.openalex.org/works` |
| Semantic Scholar | Citation analysis, papers that cite this one | `api.semanticscholar.org/graph/v1` |
| Retraction Watch | Retractions, corrections, expressions of concern | `retractionwatch.com` / RW database |
| PubPeer | Post-publication peer review, documented critique | `pubpeer.com/search?q=` |

At each step, answer: where does the number come from? What is the baseline?
Is the raw data public, proprietary, or "available on request"? Has an
independent lab confirmed it? Are there confounds or an unfair comparison
group? When the claim needs broad open-web context beyond these databases,
chain to `literature-research`.

**Claims cited through an intermediary.** When the claim arrives via
paper B paraphrasing a figure from paper A ("approximately X% as
reported in [A]"), do not stop at B's wording:

- Pull B's actual reference entry and resolve A by title, authors, year and
  verified identifiers where available. Identifier agreement alone does not
  excuse a title mismatch, and absence of a DOI does not make a source unreal.
- Fetch A itself and locate the figure in A's own text.
- Paraphrase distortion is a documented failure mode: intermediaries
  round, reframe, or silently drop the qualifying contrast. A short
  worked counterexample: a review paraphrasing a primary as
  "approximately half of the subjects were positive" is not quotable
  when the primary's own abstract reports a majority in the subjects
  *and a nearly as large fraction in the controls* — the contrast the
  paraphrase implied does not survive the primary source.
- If the figure exists only in the primary source's body and full
  text is inaccessible, the verdict is **unverifiable as stated**;
  anchor the downstream claim to a different, verifiable primary
  source and record the discrepancy on the intermediary's or
  primary's brain page so the paraphrase is never quoted uncritically
  again.

### 4. Decide the verdict

| Verdict | When |
|---|---|
| **verified** | The paper exists, raw data is public *or* an independent lab confirmed the result, and the citing source characterizes it accurately. |
| **partial** | The paper is real and the finding stands, but the citation oversells it — "causes" for a correlation, "all studies" for one underpowered result. Record the limit explicitly. |
| **unverifiable** | The number cannot be traced to source data; no replication, no independent confirmation. Not the same as wrong — say "could not verify." |
| **misattributed** | The citation points to a paper, but the paper does not say what the claim asserts. |
| **retracted** | The paper is retracted, carries a major expression of concern, or has well-documented critique contradicting the headline finding. |

### 5. File the verdict

File by subject (`_brain-filing-rules.md`):

- The claim is about a specific paper already in the brain → annotate that
  `paper` page with a **Verification** section.
- The claim is the evidence for a tracked hypothesis → annotate that
  `hypothesis` page in its `supports:` / `refutes:` reasoning.
- A standalone claim with no home page → write a `note` under `notes/`.

Carry the trace as a table; cite every row. Chain to `enrich` for any notable
author who lacks a `person` page.

## Verdict section format

```markdown
## Verification — YYYY-MM-DD

**Verdict: verified | partial | unverifiable | misattributed | retracted**

> The claim, verbatim, with its source attribution.

| Step | Finding | Source |
|---|---|---|
| Publication | Title, authors, year | doi:10.xxxx/... |
| Methodology | One-line summary; flag obvious limits | doi / URL |
| Raw data | Public repo / proprietary / on-request | URL |
| Replication | Independent confirmations and their results | doi / URL |
| Critique | Retraction Watch / PubPeer hits | URL |

One to two paragraphs on *why* the verdict, with specific evidence. Then an
honest caveat: what could not be verified, what would change the verdict.
```

## Closeout

The completed unit is the source-grounded verdict, trace and its owned page
updates, read back and schema-checked. Use `skills/git-ops/SKILL.md`; a child
returns exact paths, checks and unresolved evidence to its parent rather than
performing Git operations.

## Anti-patterns

- Skipping the brain-first lookup and re-running a verification already done.
- Inventing the lookup instead of fetching real sources — the citations *are*
  the evidence.
- Saying "verified" without confirming raw-data availability or replication.
- Saying "unverifiable" when the real problem is a shallow search — the
  verdict is on the source, not on search effort.
- Treating this as a takedown. The point is rigor; if the claim holds, say so
  plainly.
