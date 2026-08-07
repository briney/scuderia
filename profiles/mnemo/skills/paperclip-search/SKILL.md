---
name: paperclip-search
description: "Use when semantic/recall-oriented literature search is needed beyond keyword templates. Paperclip CLI patterns, sources, pitfalls."
triggers:
  - "semantic literature search"
  - "paperclip search"
  - "keyword search missed papers"
  - "corpus-wide grep for a term"
  - "recall-oriented paper search"
---

# paperclip-search — semantic literature search via the Paperclip CLI

Reference companion for retrieval skills (`literature-dive`,
`literature-sweep`, `literature-research`, `paper-ingest`). Paperclip
(GXL, https://paperclip.gxl.ai) is a hosted agent-native index of
scientific literature: **11M+ full-text papers** (PMC, bioRxiv, medRxiv,
arXiv), **150M+ abstracts** (OpenAlex-backed), plus FDA documents,
clinical trials, and protein databases (UniProt, PDB, ChEMBL). It fills
the brain's one missing retrieval mode: **semantic search** — catching
relevant papers whose vocabulary differs from the query's. Everything
else in the stack (PubMed E-utilities, S2 keyword) is keyword-based.

**Vendor posture (decided 2026-08-05):** pre-1.0 single vendor, free
tier unverified. Paperclip is an *optional enhancement*, never
load-bearing. Every workflow that uses it must degrade gracefully to
keyword templates when the binary or key is absent:

```bash
if command -v paperclip >/dev/null && [ -n "$PAPERCLIP_API_KEY" ]; then
    # paperclip path
else
    # keyword-template fallback
fi
```

## Auth and install state

- Auth: `PAPERCLIP_API_KEY` env var (documented non-interactive path;
  sent as `X-API-Key`, never written to disk). Bryan's key lives in
  `~/.hermes/profiles/<instance>/.env`, loaded at session start. Global
  `--api-key KEY` flag also works but avoids shell history is preferred.
- Installed 2026-08-05 at `~/.local/bin/paperclip` (wheel extracted to
  `~/.paperclip/lib`). The official installer's browser `login` and
  skill-installer steps were deliberately skipped.
- **Pitfall — Python version.** The wrapper's stock `#!/usr/bin/env
  python3` shebang hits macOS system Python 3.9 and dies
  (`TypeError: unsupported operand type(s) for |` — the code needs
  3.10+). Pin the wrapper to a concrete 3.10+ interpreter
  (e.g. `#!/Users/<you>/.local/bin/python3.11`). A Paperclip self-update will likely rewrite the wrapper
  and revert the shebang — if `paperclip` suddenly crashes with that
  TypeError, re-pin the shebang.

## Verified command patterns (live-tested 2026-08-05)

### Semantic search over full texts (~180ms)

```bash
paperclip search -s pmc,biorxiv,medrxiv "broadly neutralizing antibodies against ebolavirus glycoprotein" -n 6
```

- `-s/--source` is **required**. Sources: `pmc`, `biorxiv`, `medrxiv`,
  `arxiv`, `abstracts`, `fda`, `trials[/us|eu|jp|cn]`, `proteins`.
  Comma-combine.
- Hybrid scoring: flags `--min-embedding-similarity 0.7` and
  `--min-bm25-score 5` tighten precision.
- Each result: title, authors (truncated), paper id + source, date,
  DOI/PMC URL, one-line AI summary. Results are saved to a handle
  (`[s_39953bc5]`) for follow-up `map --from s_xxx "question"` (AI
  reader over the result set — not yet used in mnemo workflows).
- Quality observation: for the ebolavirus-bNAb query, top hits were the
  exact load-bearing papers (Flyak 2018 HR2/MPER, Gilchuk 2018
  EBOV-520), plus semantically-generalized neighbors (bNAbs of other
  viruses) that tighter phrasing would filter.

### Broad recall over the abstract layer

```bash
paperclip search -s abstracts "antibody language models for repertoire analysis" -n 3
```

- 150M abstracts, OpenAlex-backed — result ids are `oa_W<OpenAlexId>`.
- Use for recall beyond the full-text corpus (paywalled journals appear
  here as abstracts). Pair the `oa_W` id with the OpenAlex API
  (`api.openalex.org/works/W<id>?mailto=...`) for full metadata.

### Identity lookup by DOI

```bash
paperclip lookup doi "10.1016/j.immuni.2018.06.018"
```

- Form is `lookup FIELD VALUE`. Shared fields: `doi`, `title`,
  `author`, `abstract`, `source`; bioRxiv/medRxiv add `month_year`.
- Exact-record retrieval — a *supplement* to
  `validate_identifiers.py` recovery, not a replacement (Paperclip
  covers only its own corpus; NCBI/OpenAlex remain authoritative).

### Structured metadata and full text

```bash
paperclip cat /papers/PMC6104738/meta.json       # pmid, doi, authors, abstract, journal, keywords
paperclip head -30 /papers/PMC6104738/content.lines   # full text, line-numbered (L1:, L2:, ...)
paperclip cat /papers/PMC6104738/content.lines        # whole body
```

- `meta.json` is clean structured JSON (~20ms). `content.lines` is the
  complete article text with line numbers and section headings.
- This is a **supplementary full-text branch** for PMC/preprint papers
  in the `paper-ingest` ladder — it does not cover paywalled journals
  (Nature Reviews, Annual Reviews), so jina/Wayback remain necessary.
  Not yet wired into `fetch_fulltext.py`; candidate for a future branch.

### Corpus-wide grep

```bash
paperclip grep -il "KZ52" /papers/
```

- Paragraph-level matches across the full-text corpus in seconds
  (KZ52: 77 papers). Returns paper dirs + snippet context.
- False positives exist (an optics paper's "PKZ52 Scott glass") —
  eyeball snippets before acting on matches. Use for named entities
  (antibody names, assay terms) that keyword search handles poorly.

## Precision filter (reduce off-topic semantic neighbors)

Semantic search casts a wider net than keyword search — that's the
recall benefit, but it also pulls in semantically adjacent papers that
are NOT on-topic (e.g., influenza polymerase papers when searching for
ebolavirus polymerase). Observed 2026-08-05: 12 of 37 Paperclip
results (32%) were off-topic analogs from other virus families.

Three filters, applied in order:

1. **Add a topic anchor to the query.** Include "ebolavirus" or
   "filovirus" as an explicit term in every semantic query — not as a
   keyword filter, but to bias the embedding toward the target domain.
   Example: `"ebolavirus VP30 phosphorylation transcription replication
   switch polymerase complex"` not `"VP30 phosphorylation transcription
   replication switch polymerase complex"`. This alone cuts most
   cross-family analogs.

2. **Post-hoc title scan.** After results return, scan titles for the
   topic anchor ("ebola", "filovir", or the specific protein/gene
   name). Papers whose titles contain neither the anchor nor a known
   on-topic term are likely analogs — flag for Tier 2 (context) or
   Dropped, not Tier 1. This is the same triage the dive already does
   in Phase 3, just applied to semantic results.

3. **Source scoping.** `-s pmc,biorxiv,medrxiv` covers the full-text
   corpus. For tighter precision, search a single source at a time
   (`-s pmc` for published, `-s biorxiv` for preprints). The `abstracts`
   source (150M OpenAlex) is for recall, not precision — expect more
   noise there.

**Do NOT over-filter.** Some analogs are genuinely valuable comparative
context (paramyxovirus bipartite promoter models informing the EBOV
promoter; RSV LLPS mechanisms informing EBOV inclusion body biology).
The triage should classify them as Tier 2 (load-bearing for a Tier 1
paper's argument) or Dropped (background), not discard them
automatically. The point is to not dispatch them as Tier 1 ebolavirus
papers — they go through the standard tier classification, same as any
other result.

## Where it plugs into mnemo workflows

1. **literature-dive Phase 5 (wired 2026-08-05).** Semantic searches
   for the review's named open questions and thin-evidence areas —
   queries that are awkward as PubMed keyword strings.
2. **literature-sweep (candidate, not yet wired).** Semantic queries
   alongside the keyword templates for watched topics. Wire after
   result quality is confirmed on real sweep topics.
3. **Targeted recall.** Corpus-wide grep for named entities during
   brainstorming ("every paper mentioning <antibody>").
4. **paper-ingest supplements (not wired).** `lookup doi` as a recovery
   aid; `content.lines` as a full-text branch for PMC/preprint papers.

## Pitfalls

- **`--sort date` lets corrupt metadata top every query.** Observed
  2026-08-06: a record with a future pub_date (2027-08-01 — an upstream
  metadata error) ranked #1 on every `--sort date` query regardless of
  relevance. Date-sorted output is not relevance-ranked — scan all N
  results and apply the precision filter; drop records with implausible
  (future) dates. The relevant fresh hits are usually present, just not
  first.
- **`--since` appears to filter on index-recency, not strict pub
  date.** Observed 2026-08-06: `--since 35d` returned papers 4–6 months
  old — consistent with "added to the Paperclip index within the
  window" (i.e., the last monthly update). That is the desired behavior
  for the literature-sweep semantic arm (catches each monthly batch),
  but the semantics are undocumented — verify if the behavior changes.
- **`created_at` in `paperclip sql` is a bulk-load artifact.** All
  records in a shard share the import timestamp (e.g., all 3M arXiv
  records show one date). Useless for detecting monthly deltas — use
  `--since` + brain-dedup instead.
- **Search requires `-s`.** No default source; forgetting it errors.
- **`abstracts` ids are OpenAlex, not PubMed.** Convert via OpenAlex
  API before using with NCBI tools.
- **grep snippets need review.** Literal substring match across 11M
  papers will catch coincidental strings.
- **Rate limits unknown.** Docs publish no numbers; observed latencies
  are ~20–200ms. On HTTP 429 (SDK: `RateLimitError`), back off
  exponentially and reduce batch pace.
- **Free tier may be temporary.** If the service pivots or disappears,
  delete this skill's workflow hooks; the keyword-template fallback
  must always be the default path.
- **Self-update reverts the shebang pin.** See Auth/install above.
- **`map`/`repo` features deliberately unused.** They duplicate what
  the mind does better (delegation with read-back, the vault itself).
  Paperclip is used strictly for search and retrieval.
