---
name: literature-research
description: Brain-augmented current-state research — sends what the brain already knows into the query so the result is the delta, not a re-narration of settled fact. Use to scan the literature on a topic, check what changed, or surface new developments.
triggers:
  - "what's new about"
  - "current state of"
  - "what changed about"
  - "literature scan"
  - "surface new developments"
  - "what's the latest on"
---

# literature-research — brain-augmented current-state research

The brain almost always already knows something about a topic. This skill does
not start from a blank page — it loads the brain's existing knowledge, then
researches the **delta**: what is new, what is confirmed, what has changed
since the brain was last updated.

> **Conventions:** `skills/conventions/brain-first.md` (the lookup chain),
> `skills/conventions/quality.md` (every claim lands with a verifiable citation),
> `_brain-filing-rules.md` (file the result by subject),
> `skills/conventions/preprint-retrieval.md` (bioRxiv/medRxiv full text around the Cloudflare block),
> `skills/conventions/capabilities.md` (the harness contract).

## Capabilities

`brain-search`, `brain-read`, `brain-write`, `fetch-url` (`pubmed-fetch`,
`crossref-fetch`, `biorxiv-fetch`, `arxiv-fetch`). `brain-search` optional;
falls back to keyword scan and the skill notes the reduced recall.

## What this guarantees

- Brain context is loaded *first* and sent into the query — the research
  targets the gap, not the settled core.
- Every claim in the output carries a verifiable citation.
- Output is structured so Bryan can see at a glance what is new versus what
  merely confirms what the brain already holds.
- Contradictions with the brain are surfaced, never quietly absorbed.

## Phases

### 1. Pull brain context

Search the brain for the topic (`skills/conventions/brain-first.md`) and read the
relevant pages. This is the baseline — the body of fact the research must not
re-narrate.

### 2. Research the delta

Run the lookup with `fetch` against auth-free open sources and the open web.
No code — the endpoint knowledge is the prose here.

| Source | What it covers | Endpoint |
|---|---|---|
| PubMed E-utilities | Peer-reviewed biomedical literature | `eutils.ncbi.nlm.nih.gov/entrez/eutils/` |
| arXiv | Preprints — ML, physics, quantitative biology | `export.arxiv.org/api/query` |
| bioRxiv | Biology preprints | `api.biorxiv.org/details/biorxiv` |
| CrossRef | DOI metadata across publishers | `api.crossref.org/works` |
| NIH RePORTER | Funded grants, project abstracts | `api.reporter.nih.gov/v2/projects/search` |
| Open web | Lab pages, conference news, blog posts | direct `fetch` |

Frame the query around the delta: "Given that the brain already holds
[summary], find what is new since [date the brain was last updated] that the
brain does not reflect. Cite every claim." A dense brain context is the whole
point — it tells the research what *not* to repeat.

### 3. Structure the output

Compose the result against this shape — it is what makes the delta visible:

- **New developments** — what has appeared since the brain was last updated.
- **Confirming signals** — evidence that validates what the brain already
  holds.
- **Contradictions / updates** — findings that conflict with a brain page;
  these need a closer look.
- **Recommended brain updates** — specific edits: which page, what to add or
  change, the source.
- **Citations** — every claim resolves to a DOI, PMID, or URL with an access
  date.

### 4. File the result

File by subject (`_brain-filing-rules.md`):

- A standalone scan of a topic → a `note` under `notes/`, titled
  `"<topic> — literature scan, YYYY-MM-DD"`.
- A scan that primarily updates one existing page → fold the new material into
  that `paper`, `concept`, or `method` page directly, with citations.

When the scan surfaces a specific paper that warrants its own full `paper` page,
do not file it here — chain to `skills/paper-ingest/SKILL.md`, which owns paper
ingestion. This skill records the *delta*; a new paper page is a paper ingest.

Either way, link forward — `[[kind/slug]]` wikilinks and typed edges — and
chain to `enrich` for any notable author or lab the scan surfaces. Carry out
the recommended brain updates, or hand them to Bryan if a judgment call is
involved.

## Output format

```markdown
---
kind: note
slug: <topic>-literature-scan-YYYY-MM-DD
title: "<topic> — literature scan, YYYY-MM-DD"
importance: 0.4
date: YYYY-MM-DD
links: [<brain pages whose context framed the query>]
tags: [literature-scan]
---

# <topic> — literature scan, YYYY-MM-DD

> Two to three sentences on the delta between the brain and the current
> literature.

## New developments
## Confirming signals
## Contradictions or updates
## Recommended brain updates
## Citations
- [Source title](doi/URL) — accessed YYYY-MM-DD
```

## Anti-patterns

- Researching without loading brain context first — that is a blank-page
  search, not a delta scan.
- Re-narrating fact the brain already holds because the context was thin.
- Dropping citations — every claim must resolve to a DOI, PMID, or URL.
- Burying a contradiction with the brain inside "new developments" — call it
  out explicitly.
- Filing the scan by format ("research dump") instead of by subject.
