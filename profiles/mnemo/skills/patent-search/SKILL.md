---
name: patent-search
description: Enrich a therapeutic-antibodies corpus entry with US patent candidates — name-based search via Google Patents XHR plus sequence-derived composition-of-matter candidates via BLAST against the patent protein database — and rewrite the entry's machine-owned IP & exclusivity block. US-only v1; every expiry is labeled by estimation basis.
triggers:
  - "patent search for <antibody>"
  - "enrich patents"
  - "patent-search this entry"
  - "what's the IP situation on <antibody>"
eval_contract:
  goal: |
    Every enriched entry carries an IP & exclusivity block whose candidates are
    honestly sourced (name search and/or sequence BLAST), whose expiries are
    always labeled as estimates with a basis, and whose CoM-relevant signal is
    distinguished from the noise of full-text mentions — safe input for
    FTO-adjacent reasoning.
  dimensions:
    - "RECALL — were both name search AND sequence BLAST attempted (or the gap explicitly explained)?"
    - "HONESTY — is every expiry labeled estimated with a basis; are CoM vs MoU vs unknown claim types distinguished or marked pending?"
    - "PRECISION — are full-text-mention noise and assignee mismatches filtered or flagged?"
    - "BLOCK DISCIPLINE — was only the IP & exclusivity block rewritten?"
  hard_fails:
    - an expiry presented without an expiry_basis label
    - a patent number in the block that does not come from a cited query
    - declaring no-CoM-found after name search only (pre-INN blind spot)
---

# patent-search — corpus IP enrichment (US-only v1)

Fills the machine-owned `## IP & exclusivity` block of a
`references/therapeutic-antibodies/entries/<slug>.md` record. Two retrieval
modes, both mandatory: **name search** (Google Patents XHR — no key needed;
recall net for formulation / method-of-use / dosing-era patents) and
**sequence-derived search** (BLAST the VH/VL against NCBI's patent protein
database — the high-precision composition-of-matter signal, and the ONLY way
to reach pre-INN CoM filings, whose claims predate the name itself).
Distinct from `antibody-sequence-search` (Sequences block) and
`structure-search` (Structures block).

> **Conventions:** `references/therapeutic-antibodies/templates/entry-template.md`
> (block schema + expiry-labeling policy), `skills/conventions/raw-source-archive.md`.

## What this guarantees

- Every patent in the block traces to a cited query — never memory.
- Every expiry carries `expiry_basis` (`estimated-20y` |
  `estimated-gatt-transition`); estimates are never presented as actual
  expiration dates.
- US-only results (no EPO OPS credentials; PatentsView needs a key — both
  documented as v2 paths).
- Only the `## IP & exclusivity` block is written.

## Phases

1. **Identity.** From the entry: INN, aliases/brand names, developer and
   originator (assignee candidates). Note that assignee strings in patents
   vary (e.g. "Genentech, Inc." vs "Genentech Inc.") — the script
   post-filters, so run both with and without `--assignee`.

2. **Name-based candidates.** Run the lookup script in this skill's
   `scripts/`:
   ```bash
   python3 skills/patent-search/scripts/google_patents_lookup.py <INN> --all --max 2
   ```
   Full-text mode is the recall net (it matches every patent that *mentions*
   the molecule in the specification — expect heavy noise); claims mode
   (`CL=(INN)`) is the precision set. Rank candidates by claims-mode
   presence, assignee match to developer/originator, and filing era
   (CoM-era vs lifecycle-era).

3. **Sequence-derived CoM candidates.** Pull VH/VL from the entry's
   `## Sequences` block (run `antibody-sequence-search` first if absent).
   Two passes, in order:
   a. **PLAbDab first pass (local, instant).** PLAbDab (Oxford OPIG's Patent
      and Literature Antibody Database, ~177k paired chains) is
      antibody-specific and curated — it is the first place to look:
      ```bash
      python3 skills/patent-search/scripts/plabdab_lookup.py --vh <VH> --vl <VL> --resolve 12
      ```
      Exact chain matches against the local mirror
      (`references/therapeutic-antibodies/raw/mirrors/plabdab_paired_sequences.csv.gz`,
      ~11 MB gz — the full 5 GB DB tarball is NOT mirrored). `--resolve` maps
      GenBank-accession-shaped IDs to patent numbers via NCBI efetch (PDB and
      literature-name IDs don't resolve — by design). For fuzzy / CDR-region
      search use the full PLAbDab package (`pip install .` from
      github.com/oxpig/PLAbDab) — exact match is the v1 default.
   b. **pataa BLAST (broader net, queued).** Catches what PLAbDab's pairing
      and filtering drops:
      ```bash
      python3 skills/patent-search/scripts/blast_pat.py <VH>
      ```
      BLAST against `pataa` is a queued public service — expect minutes, poll
      at the script's interval, never hammer. A hit means the patent's
      sequence listing contains the chain: the CoM anchor. If Sequences are
      `not-found` / `not-public`, mark sequence search unavailable — that is
      precisely the handoff case where the patent listing may BE the
      sequence source (v2: sequence-listing extraction).

4. **Compose the block.** Table per the template spec: publication number,
   title, assignee, filed, granted, est. expiry + `expiry_basis`, claim types,
   legal status. Claim-type classification (CoM / method-of-use / formulation
   / dosing / manufacture / diagnostic) is **v2 (LLM claim distillation)** —
   in v1 write `pending v2` unless the title makes it unambiguous (e.g.
   "Subcutaneous formulations" → formulation). Legal status: `not queried
   (v1)`. Sequence-derived candidates get their own list with the BLAST RID
   for provenance.

5. **Write wholesale + report.** Replace an existing `## IP & exclusivity`
   block entirely; append otherwise. Report: name candidates kept/dropped,
   BLAST status (RID, hits, mapped patent numbers), and any entries deferred
   to v2.

## Output

- The entry file with a rewritten/appended `## IP & exclusivity` block.
- Console report per phase 5.

## Anti-patterns

- Presenting `estimated-20y` as an actual expiration date — PTA, PTE, and
  terminal disclaimers can move the real date by years.
- Name search alone for CoM: the INN does not exist in pre-INN filings;
  only sequence BLAST reaches them.
- Treating a full-text mention as relevance — most hits are prior-art
  citations of the molecule in unrelated patents.
- Ignoring GATT transition (pre-1995-06-08 filings): term is the LATER of
  20y-from-filing and 17y-from-grant.
- Claiming legal status without a legal-events source (v1 has none).
- Patching anything outside the `## IP & exclusivity` block.

## Pitfalls

- **PLAbDab VH-only hits can resolve to patent numbers.** The
  `plabdab_lookup.py` script reports `paired_hits` (both VH+VL match in the
  same row) and `vh_hits` (VH-only). The `--resolve` flag maps accession-shaped
  IDs to patent numbers via NCBI efetch. Resolved patents can come from
  VH-only hits, not just paired hits — in the 2026-08-25 pilot, 2 of 3
  entries with resolved patents (fresolimumab: US10730936, US9783604) got
  their patent numbers from VH-only hits, not from paired hits. When
  composing the block, always check the `resolved` dict from ALL hits
  (paired + VH-only), and include a "Resolved patent numbers" subsection
  listing every accession → patent mapping, noting whether it came from a
  paired or VH-only hit.

- **PLAbDab patent-number resolution rate is low (~30%).** In the
  2026-08-25 pilot, only 3/10 entries had any accessions resolve to patent
  numbers via NCBI efetch. Many PLAbDab IDs are PDB instance IDs or
  literature names that don't resolve by design. The `reference_title`
  field is the fallback — it carries the patent title, which identifies the
  patent family even without a number. Always include the reference titles
  in the block even when resolution fails.

- **Google Patents 503 is intermittent, not permanent.** In the pilot,
  4/10 queries succeeded and 6 returned 503 — not the "throughout" pattern
  seen in the Tier A sweep. Retry later or in smaller batches; the 503 is
  a rate-limit on bursts, not a service outage. When it hits, fall back to
  PLAbDab-only and flag the gap honestly — do not burn budget retrying
  in the same run.
