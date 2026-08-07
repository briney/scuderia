---
name: paper-ingest-verification
description: "Verify completed paper-ingest runs — Phase 10 checks."
triggers:
  - "verify paper-ingest run"
  - "Phase 10 verification"
  - "check ingested paper frontmatter"
  - "ledger duplicate check"
  - "authors list representation large author count"
---

# Phase 10 verification and authors-list representation

Reference companion to the `paper-ingest` vault skill
(`skills/paper-ingest/SKILL.md`). The workflow-reconstruction
protocol (Patch 2026-07-19 in the pointer) names Phase 10 as "YAML parses,
ledger valid, links resolve, no dup slugs" but provides no implementation.
This companion carries the reusable script and the authors-list
representation rule discovered in the 2026-07-24 Gilchuk 2021 session.

## 1. Phase 10 verification script

**The script checks all five Phase 10 invariants in one pass:**
1. Paper frontmatter parses as valid YAML.
2. All `links:` targets exist as pages on disk.
3. All `authors:` slugs resolve to existing `people/` pages **or** ledger entries.
4. All `cited_by:` targets exist.
5. Ledger (`people/_ledger.yaml`) parses and has no duplicate slugs.

Exit code 0 = all pass; non-zero = failures found. Auto-detects the brain
root from cwd (looks for `papers/` + `people/` subdirectories), or takes
`--brain <path>`.

**Usage:**
```bash
python3 scripts/verify_ingest.py gilchuk-2021-pan-ebolavirus-two-antibody
# or with explicit brain path:
python3 scripts/verify_ingest.py gilchuk-2021-pan-ebolavirus-two-antibody --brain /path/to/brain
```

**Expected output on success:**
```
Paper: gilchuk-2021-pan-ebolavirus-two-antibody
  Frontmatter: OK
  links: 5 checked, 5 OK
  authors: 7 checked, 7 OK (all resolve to people/ pages or ledger)
  cited_by: 1 checked, 1 OK
  Ledger: 525 entries, 0 duplicates

PASS: All checks OK
```

The script lives at `scripts/verify_ingest.py` under this skill directory.
Run it after every paper-ingest, before commit.

**Note:** As of 2026-08-01, the script file has not yet been written to disk.
The verification logic was run inline via `python3 -c` blocks in the
2026-07-24 Gilchuk 2021 and 2026-08-01 Kwon 2016 sessions. Future sessions
should either run the inline check or create the script file.

**Session evidence (2026-07-24, Gilchuk 2021):** The inline version of this
script caught all links/authors/cited_by as OK, confirmed 525 ledger entries
with 0 duplicates, and gave a clean PASS before commit.

**Session evidence (2026-08-01, Kwon 2016):** The inline verification checked
paper YAML, ledger YAML (2,623 entries, 0 duplicate slugs), all 38 author
slugs resolved in ledger, all 8 links resolved on disk, and cited_by on
huang-2012 confirmed. A name-based duplicate check caught two
different-slug duplicates (louder-mark vs louder-mark-k, carlton-kevin vs
carleton-kevin) that were merged before the final verification pass.

## 2. Authors-list representation for papers with many authors

**Rule:** The frontmatter `authors:` list carries **every author** on the
paper as `people/<slug>` entries, regardless of whether a `people/` page
exists. This follows the forward-only linking convention
(`graph-and-links.md`: "A link to a page that does not exist yet is
acceptable: it marks an edge worth filling, not an error") and the
`paper-ingest` contract ("Every author on an ingested paper goes into the
paper's `authors:` list as `people/<slug>`"). Authors without pages are
tracked in the ledger (`people/_ledger.yaml`) — the ledger is the citation
count accumulator, the `authors:` list is the complete authorship graph.

**Observed 2026-08-01 (Kwon 2016, 38 authors):** All 38 authors listed in
frontmatter `authors:`, all 38 resolved to ledger entries (26 existing
Branch 2, 12 new Branch 3). No `people/` pages existed for any author;
the `authors:` list carries the full set of forward edges regardless.

**Observed 2026-07-24 (Gilchuk 2021, 19 authors):** The paper page lists 7
authors in frontmatter who have existing people pages (Gilchuk, Murin,
Cross, Ilinykh, Bukreyev, Ward, Crowe) and 12 additional authors who are
ledger-only entries. Both sets are in the `authors:` list — the split is
about page vs ledger, not about inclusion in `authors:`.

**Prior incorrect guidance (corrected 2026-08-01):** An earlier version
of this section stated the `authors:` list carries only authors with
existing `people/` pages. That is wrong — it contradicts
`graph-and-links.md` ("forward-only linking allows targets that don't
exist yet"), the exemplar `papers/caskey-2015-3bnc117-viremia.md` (lists
all 25 authors including ledger-only ones), and the `paper-ingest` skill's
Phase 8 contract. The `authors:` list is always the complete author list.

## 3. Name-based duplicate check during Phase 10

After the ledger update (Phase 8), before the final verification pass, run
a name-based duplicate check across all newly-added entries. Slug-based
searching misses entries where the same person is registered under a
different slug (spelling variant, middle-initial variant, abbreviated
name). See `paper-ingest-fallback-patterns` §8a for the full hazard
description.

**Observed 2026-08-01 (Kwon 2016):** Two different-slug duplicates caught:
- `louder-mark` (new, this session) vs `louder-mark-k` (existing) — same
  person (Mark K. Louder, VRC)
- `carlton-kevin` (new, this session) vs `carleton-kevin` (new, this
  session) — same person (Kevin Carlton, VRC), spelling variant from
  PubMed XML `ForeName` vs prior ledger entry

Both merged before final verification. The name-based check should cover
**all** new entries, not just the ones where you suspect a collision.

## Patch pointer entry

Add the following to the `paper-ingest` profile-side pointer SKILL.md under
a new `## Patch 2026-08-01` section (for folding into the vault SKILL.md on
the next direct edit pass):

- Phase 10 should reference `scripts/verify_ingest.py` from the
  `paper-ingest-verification` companion skill as the reusable verification
  tool, rather than naming the checks without an implementation.
- The `authors:` list representation rule (all authors, not just paged
  ones) should be added to Phase 8 as an explicit convention.
- A name-based duplicate check should be part of Phase 10, not just
  Phase 8 — the ledger update can create spelling-variant duplicates that
  slug-based verification misses.
