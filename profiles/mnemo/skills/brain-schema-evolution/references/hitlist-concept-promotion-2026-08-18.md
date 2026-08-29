# Worked example: hitlist profile → concept promotion (2026-08-18)

The third live exercise of `brain-schema-evolution`: your human proposed a
`resources` page kind for large compendium-style working docs (the ~580
per-target hitlist profiles, bacterial-toxin surveys, enveloped-virus
surveys). The decision was to use the existing `concept` kind instead —
no new page kind. This note records the analysis, the decision, and the
full migration technique including PMID→wikilink conversion.

## The proposal (Step 1)

The pain point: large survey/compendium documents lived in `working-docs/`,
which the brain does not index, link, or query. These are not ephemeral
scratch — they are permanent, data-rich reference corpora (the hitlist
profiles contain 11-field deep dives with PMID citations, structural data,
epitope maps, competitive landscapes). The `working-docs/README.md` rule
("if content is load-bearing, promote it to a real page") was being
honored in letter but not in spirit: the profiles were too numerous and
too structured for `note`, too data-heavy for `concept`, and no kind meant
"reference compendium."

## Decomposition (Step 2)

The proposal bundled two distinct things:

| What | Example | Shape |
|---|---|---|
| **Compendium index** — the master list/survey page | hitlist-master, toxin-survey | One page, linkable, a hub |
| **Per-target profiles** — the structured data pages | 580 × `hitlist-profiles/<slug>.md` | Many pages, each a graph node |

The first question was whether the compendium index itself warranted a new
`resource` kind. The second — and load-bearing — question was what the
580 per-target profiles become.

## The decision: concept, not a new kind (Step 3)

your human decided: all per-target profiles become `concept` pages. This
follows a broader decision that "concepts should flourish" — the concept
layer is not a small curated collection (that's for projects/grants); it is
the living knowledge graph where ideas, targets, and lenses proliferate.
The expectation is many more concepts than projects.

**Rule 1 — status is a field, not a kind.** A survey/compendium is not a
distinct entity class from a concept; it is a concept with a different body
shape. No lifecycle or identity argument justifies splitting it.

**Rule 2 — graph-hub test.** Each per-target profile is a graph node with
potential inbound edges from papers, grants, hypotheses, and other
concepts. It passes the hub test as a `concept`.

**Rule 3 — relationship distinctions in frontmatter, not directories.** The
"resource-ness" of a compendium concept is a tag (`hitlist-profile`,
`antibody-target`), not a separate kind or directory.

**What was rejected:** a `resource` kind. The argument for it was that no
existing kind means "a reference corpus, not a living bet." The argument
against — and the one that won — is that the concept layer is explicitly
designed to hold a diversity of page shapes, and the `thesis_updated` /
`## Shifts` anatomy is optional (the linter only warns if `## Shifts`
exists without `thesis_updated`; a profile with neither is clean). Adding
`resource` would create a dumping ground that risks becoming the new
`working-docs/`.

## Schema changes

None. The existing `concept` kind already supports everything needed:
- `kind: concept`, `slug`, `title`, `importance`, `status: active`,
  `links`, `tags`, `related_concepts` — all in the existing spine.
- No new frontmatter fields required.
- The linter's `concept` entry requires only `kind`, `slug`, `title`; `status`
  is enum-validated as `active|dormant`; `importance` is range-validated.

## Migration technique: working-docs → concepts with PMID→wikilink

The hitlist profiles had 5+ different header format variations across 580
files. A robust parser was needed. The migration was completed in one
session, including full PMID→wikilink conversion. Key details:

### Header format variations encountered

The profiles were built over multiple sessions with evolving templates. The
parser must handle all of these:

1. `# Target Profile: <Name>` with blockquote `> **Tier**: ...` / `> **Therapeutic area**: ...`
2. `# <Name> Target Profile` (title suffix) with blockquote `> Tier: ...` / `> Area: ...`
3. `# Target Profile: <Name>` with inline `**Target: ... | Tier: ... | Area: ...**` (pipe-delimited, bold, not blockquote)
4. `# <Name> Target Profile` with `**Tier: ...** | **Therapeutic area: ...**` (bold, pipe-delimited, not blockquote)
5. Mixed formats where `**Key papers**` may be `**Key papers ingested**`, may
   include PMID annotations in parentheses, or may be absent entirely (~135
   profiles have no key-papers line).

### Frontmatter generation

- **Title**: extracted from the first `#` heading, with "Target Profile"
  suffix stripped.
- **Importance**: mapped from tier (approved=0.80, clinical-trial=0.70,
  failed-clinical=0.65, preclinical=0.50). This is a heuristic — adjustable.
- **Tags**: `antibody-target`, `hitlist-profile`, `tier-<tier>`, plus
  area-derived tags (immunology, oncology, neuroscience,
  cardiovascular-metabolic, infectious-disease, ophthalmology) when the area
  field is parseable.
- **status**: `active` (all profiles start active).
- **related_concepts**: for 10 targets that already have curated
  `*-antibody-landscape` concept pages (pcsk9, il-33, tnf, tau, tslp, egfr,
  dr5, angptl4, gdf15, alpha-synuclein), add a `related_concepts` cross-link
  so both pages coexist and are discoverable from each other. The profile is
  the structured reference; the landscape page is the living thesis.

### Body preservation

The 11-field profile body is preserved verbatim — no restructuring into
Thesis/Frontier/Shifts anatomy. The concept anatomy is for evolving bets;
these are structured reference compendiums. The linter does not require the
anatomy sections (it only warns if `## Shifts` exists without
`thesis_updated`, and these don't have `## Shifts`).

### PMID→wikilink conversion (completed)

7,033 PMID references across 580 profiles were converted from
`PMID 12345678` to `[[papers/<slug>]]`. This required:

1. **Batch PMID resolution via PubMed esummary** — 6,807 unique PMIDs
   across 580 profiles. 1,461 already had `papers/` pages (21.5% coverage).
   The remaining 5,346 were resolved in 27 batched esummary calls (200
   PMIDs per call, ~0.4s delay between batches, total ~68s). Only 5 PMIDs
   (0.07%) could not be resolved — bad IDs with leading zeros or not in
   PubMed.

2. **Slug generation** — `<first-author-surname>-<year>-<topical-tag>`.
   Surname extracted from esummary's `authors[0].name` field (format:
   "Surname FM" — initials are the trailing 1-2 char uppercase tokens).
   Topical tag: first 2-3 significant words from the title (stopwords
   filtered). Collision handling: append numeric suffix `-2`, `-3`, etc.
   Check against both existing `papers/` slugs and new slugs in the same
   batch. 9 papers with no author (consortium/drug monograph entries) got
   hand-crafted slugs from the title.

3. **Paper stub creation** — 5,341 minimal stub files written to `papers/`:
   `kind: paper`, `slug`, `title`, `status: unknown`, `pmid`, `doi`,
   `year`, `authors: []`, `importance: 0.30`, `needs-ingest: true`,
   `tags: [stub]`. These enter the `ingest-pending-papers` queue.

4. **Wikilink replacement** — string replace per profile using the
   PMID→slug mapping.

5. **Verification** — all 580 concept pages and 5,341 stubs pass the
   frontmatter linter with zero errors/warnings.

### Key technique: esummary batch resolution

The `pubmed_esummary_batch(pmids)` function (from
`paper-ingest/scripts/validate_identifiers.py`) accepts up to 200 PMIDs per
call and returns title, first author, year, DOI, PMCID for each. For bulk
PMID resolution (thousands of PMIDs), batch at 200/call with 0.4s delay
between batches. The esummary `authors[0].name` field is in "Surname FM"
format — extract the surname by taking all tokens before the first 1-2
char all-caps token.

### Slug collision check

Before any migration, check for slug collisions between the working-docs
profiles and existing concept pages. In this case: zero exact collisions,
but 10 near-matches (substring pairs) where a profile slug matches an
existing `*-antibody-landscape` concept. These get `related_concepts`
cross-links, not mergers — both pages serve different purposes.

### Pilot-first (Step 4)

5 diverse profiles (ace2, 4-1bb, il-4, vegf-c, diphtheria-toxin) were
promoted first, covering: different header formats, different tiers,
different areas, a profile with no blockquote header, and a profile with
inline pipe-delimited metadata. Verified by reading back the generated
frontmatter and running the linter — zero errors/warnings.

### Files NOT promoted

- `TEMPLATE.md` and `FULL-RUN-PROMPT.md` — pipeline scaffolding. Deleted.
- `papers/` subdirectory — 233 paper text files. Raw-source backup. Kept.
- `_*.json` sidecar files — UniProt/paper metadata. Not brain pages. Kept.
- `hitlist-master.md` — compendium index. Promotion decision deferred.

### Working-docs cleanup

After the concept pages were committed and pushed, the 582 original .md
files (580 profiles + TEMPLATE + FULL-RUN-PROMPT) were deleted from
`working-docs/hitlist-profiles/`. The `papers/` subdirectory and JSON
sidecars were retained as raw-source backup.

## Rollout — completed

1. This design note.
2. Pilot: 5 profiles → concepts/ (verified).
3. your human reviewed the pilot shape and approved.
4. Full batch: 5,341 paper stubs + 575 concept pages created (5 pilot
   pages updated).
5. PMID→wikilink conversion: 7,033 references across 580 profiles.
6. Linter verification: zero errors/warnings on all new pages.
7. Committed and pushed (2 commits: creation + working-docs cleanup).
8. 582 .md files removed from working-docs/hitlist-profiles/.

## Open items

- The `hitlist-master.md` compendium index: promote to a concept with
  `links:` to all 580 children, or keep as a working-doc? Decision deferred.
- The 5,341 paper stubs are in the `ingest-pending-papers` queue, ready to
  be drained by the paper-ingest pipeline for full-text ingestion.
- The concept pages do not carry `thesis_updated` or `## Shifts` anatomy.
  If a profile later becomes a living thesis, it should gain the anatomy
  at that point — the `concept-refresh` skill will not fire without
  `thesis_updated`, which is fine for dormant reference pages.
