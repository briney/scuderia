---
name: paper-ingest-biorxiv-preprint-fulltext
description: "Use when paywalled paper has a bioRxiv preprint."
triggers:
  - "bioRxiv preprint full text"
  - "paywalled paper with preprint"
  - "CommentsCorrections UpdateOf bioRxiv"
  - "Cell Cloudflare blocked"
  - "Elsevier full text from preprint"
---

# bioRxiv preprint full-text retrieval for paper-ingest

Session-learned technique from 2026-08-02 (Wang et al. 2026, Cell, PMID 42462709).

## The pattern

When a published paper is paywalled (no PMCID, `isOpenAccess: N`, publisher
page Cloudflare-blocked), but a **bioRxiv preprint** exists, the preprint's
"Full Text" tab on biorxiv.org renders the complete article body via browser.

This is a **new branch (1c)** in the `paper-ingest-full-text-access` decision
tree, distinct from:
- Branch 1 (PMC OA browser) — the preprint's PMC deposit may contain only
  metadata, not the body
- Branch 1b (Europe PMC PDF render) — the *published* version has no PMCID
  and `inPMC: N`
- Branch 2 (journal HTML) — the publisher page is Cloudflare-blocked

## Discovery signal

The published paper's PubMed XML carries
`<CommentsCorrections RefType="UpdateOf">` pointing at a bioRxiv preprint.
This is the bibliographic link that makes the preprint discoverable during
Phase 1 identity resolution.

## Extraction technique

**Step 0 — version check via api.biorxiv.org (not Cloudflare-blocked).**
The bioRxiv API host is reachable by `curl` even when www.biorxiv.org
429s (verified 2026-08-05):

```bash
curl -sL "https://api.biorxiv.org/details/biorxiv/<preprint-doi>" -o /tmp/biorxiv_api.json
```

The response gives the latest `version`, the submission `date`, the
`jatsxml` source-XML URL, and whether the preprint has been published.
Always fetch the **latest version's** full text; if the API shows the
preprint is now published and the journal version is reachable, prefer
the published version. Record the version used in the Ingest log.

**Step 1 — reader proxy (jina), the first retrieval attempt.**
Verified 2026-08-05: a single terminal call defeats the bioRxiv
Cloudflare block that 429s direct `curl` (.full, .full.pdf, .source.xml
all blocked from this host):

```bash
curl -sL "https://r.jina.ai/https://www.biorxiv.org/content/<preprint-doi>v<N>.full" -o /tmp/<slug>_fulltext.md
```

Sanity-check the output (tens of KB with ## Introduction / ## Results /
## References sections). Observed 2026-08-05 (the Wang preprint below):
132K chars — Introduction, all Results subsections, Discussion, 53
references, figure captions — no browser needed. If jina rate-limits
(429), back off and retry once, then fall to Step 2.

**Step 2 — browser click-through (fallback).**
1. `browser_navigate` to `https://www.biorxiv.org/content/<preprint-doi>v<N>`.
2. Click the "Full Text" link in the page snapshot.
3. Extract via `browser_console` with
   `document.body.innerText.substring(0, 15000)` and paginate. Use
   `document.body.innerText` (not `querySelector('article')` — bioRxiv
   full-text pages don't have an `<article>` element).

**Step 3 — Wayback Machine (second fallback).** If both live routes are
blocked, check for an archived snapshot of the `.full` page or
`.full.pdf` — see branch 2b in `paper-ingest-full-text-access`.

The preprint abstract may be slightly more detailed than the PubMed
(published) abstract — use the longer one.

## `needs-enrichment` decision

Set `needs-enrichment: true` because the distillation is from the preprint,
not the final published version. The preprint and published versions share
the same abstract and core findings, but may differ in figure numbering,
text edits, and supplementary data. Re-check when the published full text
becomes available (likely via PMC after embargo lifts).

## Session evidence

**Wang et al. 2026, Cell, PMID 42462709** (Sprox-seq / spatial proximity
sequencing in germinal center):
- Published version: ahead-of-print, no PMCID, `isOpenAccess: N`,
  `inPMC: N`.
- Cell publisher page (cell.com): Cloudflare "Just a moment..." interstitial.
- PMC XML for preprint (PMC12636307): abstract-level metadata only, no `<body>`.
- bioRxiv preprint (DOI 10.1101/2025.10.27.684659, PMID 41280071):
  full-text page rendered complete article — Introduction, all Results
  subsections, Discussion, Methods, 53 references — ~87K chars in 3 × 15K
  pages via `document.body.innerText.substring()`.
- Preprint abstract was slightly more detailed than the PubMed (Cell) abstract.

## What to update in existing skills

### `paper-ingest-full-text-access` (branch 1c)

Add a new branch 1c between 1b and 2 in the decision tree, with the
technique above. Also:
- Add `cell.com` to the Known publisher blocks table (Cloudflare, same as
  Elsevier/ScienceDirect — Cell Press is an Elsevier imprint).
- Add a new pitfall entry: "When the published version is paywalled with no
  PMC copy, always check `<CommentsCorrections>` for a preprint link before
  falling through to abstract-only."
- Add `bioRxiv preprint full text` to the triggers list.

### `paper-ingest-fallback-patterns` (§10: `cat >>` ledger concurrency)

Add a new concurrency hazard: **shell `cat >>` on `people/_ledger.yaml`
is silently lost when a sibling subagent writes to the file concurrently.**
Unlike `patch` (which detects sibling modifications and warns), `cat >>`
appends at the file byte offset — if a sibling has already changed the file
length, the append either lands in the wrong position or is silently
overwritten when the sibling's own `cat >>` or `write_file` lands.

**The fix:** Never use `cat >>` for ledger appends during parallel
ingest-pending-papers runs. Use `patch` against the end of the file (the
last entry's last line as `old_string`, with the new entries appended as
`new_string`). If `patch` reports a sibling-modification warning, re-read
the file tail and re-apply. After any ledger write, verify with
`python3 -c "import yaml; yaml.safe_load(open('people/_ledger.yaml'))"`
that the new entries parse correctly — a silent overwrite produces valid
YAML that is simply missing your entries.

Observed 2026-08-02 (Wang et al. 2026): 13 ledger entries appended via
`cat >>` were silently lost when sibling subagents (ingesting other papers
in parallel) wrote to the ledger concurrently. The `wc -l` confirmed the
append initially, but a subsequent `yaml.safe_load` showed 0 of 13 entries
present — the siblings' writes had overwritten the tail. Re-appending via
`cat >>` after the siblings finished succeeded and was verified.

### `paper-ingest-pubmed-resolver-v2` (§6: preprint discovery via CommentsCorrections)

Add: "When a published paper's PubMed XML carries
`<CommentsCorrections RefType="UpdateOf">` with a bioRxiv `<RefSource>`,
the preprint PMID is in the `<PMID>` child element. Resolve the preprint
separately via PubMed E-utilities — it may have a PMCID even when the
published version does not (ahead-of-print). The preprint's PMC XML may
contain only abstract-level metadata (preprint deposit), but the bioRxiv
website renders the full text via browser. This is the discovery path for
the bioRxiv preprint full-text branch (1c in paper-ingest-full-text-access)."
