---
name: therapeutic-antibody-registry
description: "Build the molecule-level antibody registry corpus."
triggers:
  - "therapeutic antibody registry"
  - "antibody molecule database"
  - "build antibody entries"
  - "antibody registry"
  - "Tier A antibody"
  - "approved antibody list"
  - "references/therapeutic-antibodies"
---

# therapeutic-antibody-registry — molecule-level therapeutic antibody corpus

Build and maintain `references/therapeutic-antibodies/` — a structured corpus of
known therapeutic antibodies, one record per distinct **drug product** (INN), across
all modalities (naked IgG, ADC, bispecific, CAR-T, Fc-fusion, fragments) and all
development stages (approved through pre-clinical). This is the **molecule-side
complement** to `antibody-target-hitlist` (target-side): the hit-list asks "what
targets exist?"; this corpus asks "what molecules got built, and how far did they
get?"

## Scope (locked decisions)

- **In**: any therapeutic with at least one antibody-derived binding or structural
  domain (IGH/IGL/IGK-derived Fab, scFv, VH/VL, VHH) or an Fc domain from an
  antibody isotype. Includes Fc-fusions (tagged `modality: fc-fusion`).
- **Out**: non-antibody scaffolds (DARPin, Affibody, Anticalin, knottin), small
  molecules, peptides, antisense/siRNA, oncolytic viruses, TCR-based therapeutics
  without an antibody-derived domain.
- **Record key**: drug product / INN, NOT the target or program. ADCs split from
  their naked parent (trastuzumab / emtansine / deruxtecan = 3 records). Biosimilars
  are a sub-list on the originator record, not separate records.
- **Tiers**: A (approved+filed), B (active clinical), C (discontinued/withdrawn
  Phase 2+), D (named pre-clinical with a public identifier).
- **Tier D floor**: at least one of: trial-registry ID, peer-reviewed publication,
  named candidate in an official company disclosure, or WHO INN/USAN.

See `references/therapeutic-antibodies/master.md` for the authoritative scope,
tier definitions, status vocabulary, failure taxonomy, and directory layout.

## Directory anatomy

```
references/therapeutic-antibodies/
  README.md            # corpus overview + locked scope decisions (YAML metadata)
  CHANGELOG.md         # structural/contract changes with downstream-impact notes
  master.md            # the keystone guide — scope, tiers, identity, conventions
  entries/             # one record per drug product (slug-named .md)
  index/               # six per-area molecule lists (mirrors hit-list categories/)
  templates/           # entry-template (base) + 4 appendix templates
  raw/                 # fetched source captures (text only; binaries to R2)
```

Templates: `entry-template.md` (base, always), `adc-template.md`,
`multispecific-template.md`, `car-template.md`, `failed-template.md` (appendix
blocks, applied per modality/status).

## Source hierarchy (Tier A)

1. **Antibody Society approved-antibody table** — the backbone. Scrape
   `antibodysociety.org/resources/approved-antibodies/` via urllib, parse the HTML
   table with regex. ~168 rows (INN, brand, target, format, indication, EU/US
   approval years). See `references/source-extraction.md` for the proven scrape
   pattern and `references/tier-a-sweep-recipe.md` for the full 182-entry
   generation recipe.
2. **"Antibodies to watch" annual series** (mAbs, open access via Europe PMC) —
   pipeline census. PMID 41560619 for 2026 (PMCID PMC12826703). Fetch
   `fullTextXML` from Europe PMC, parse `<table-wrap>` elements. 4 tables:
   first approvals, regulatory review, late-stage non-cancer, late-stage cancer.
3. **FDA Purple Book** — regulatory IDs (BLA numbers), biosimilar lists. Web app
   at `purplebooksearch.fda.gov` (HTML, not a clean API).
4. **EMA EPAR** — European regulatory details. `ema.europa.eu/en/medicines`.
5. **NMPA / PMDA** — China/Japan-only approvals (toripalimab, sintilimab,
   camrelizumab, etc.). Not in the Antibody Society table's EU/US columns;
   check the INN column for these molecules, then supplement from company
   disclosures.
6. **ClinicalTrials.gov** — Tier C (discontinued/withdrawn) source. REST API v2
   with `filter.overallStatus=TERMINATED,WITHDRAWN,SUSPENDED`.

**Probe source format before fetching.** All Tier A sources returned text/HTML in
the pilot — none required R2 archival. But this can change; always check
Content-Type before assuming text.

## R2 / binary source convention

Binary sources (PDF, XLSX, DOCX) go to R2, not the repo. The convention mirrors the
grants page type exactly:

```
remote:  atticus-r2
prefix:  atticus-drops
key:     therapeutic-antibodies/<sha256-hash>.<ext>
```

Frontmatter `sources:` block (one entry per binary source):
```yaml
sources:
  - role: <registry-pull | epar-table | nmpa-notice | other>
    hash: sha256-<64-char-hex-digest>
    r2_key: therapeutic-antibodies/<64-char-hex-digest>.<ext>
    filename: "<original filename>"
    ingested: YYYY-MM-DD
    provenance: "<what this source is and where it came from>"
```

See `references/conventions/raw-source-archive.md` in the vault for the full
convention. Do NOT invent the R2 addressing scheme — it mirrors grants exactly.

## Cross-referencing to the hit-list

Each entry carries a `target_hitlist` pointer to the corresponding target profile
in `references/antibody-target-hitlist/profiles/<slug>.md`. The pointer is a
plain-text path, NOT a wikilink.

**Critical**: hit-list profile filenames use **common-name slugs**, not gene
symbols. `pd-1.md` not `pdcd1.md`. `her2.md` not `erbb2.md`. Always resolve the
slug against the actual `profiles/` directory before writing a pointer — never
assume the slug from the gene symbol. Bispecific targets may have pair slugs
(`cd19-cd3.md`, `egfr-cmet.md`).

## Index generation

`index/` mirrors the hit-list's `categories/`: six per-area molecule lists using
the same six area names and filenames:

```
index/
  oncology.md
  immunology-inflammation.md
  infectious-disease.md
  neuroscience.md
  cardiovascular-metabolic.md
  ophthalmology-rare.md
```

**Area is a multi-tag, not a partition.** A molecule appears in every area file
where it has an approved/filed indication. The `therapeutic-area` field in each
entry (closed six-value vocabulary, comma-separated, primary-first) drives index
membership. Index files are compiled views over `entries/` — regenerate from
canonical records, do not edit directly.

Area assignment uses word-boundary matching on the indication text (regex `\b`)
to avoid substring false positives (e.g., "sma" matching inside "melanoma").

## Workflow: pilot-batch validation

Before the full Tier A sweep (~150 records), build a **pilot batch** of 20-25
entries across all modalities and edge cases to validate the template set:

1. Fetch the Antibody Society table + ATW XML into `raw/`.
2. Build entries spanning: anti-TNF, anti-PD-1/PD-L1, anti-HER2 (incl. ADCs),
   anti-CD20, anti-VEGF, anti-EGFR — the major commercial classes.
3. Include edge cases: Fc-fusions (etanercept, aflibercept), CAR-T
   (tisagenlecleucel), withdrawn/re-approved (gemtuzumab ozogamicin), global
   approvals (toripalimab, tislelizumab, camrelizumab).
4. Generate all six `index/` files + master index.
5. Verify: template fills cleanly, index membership is correct, hit-list
   pointers resolve, multi-area tagging works.
6. Only after the pilot validates, proceed to the full sweep.

This matches Bryan's preference for incremental validation before large ops.

## Workflow: full Tier A sweep

After the pilot validates, process the remaining ~141 rows of the approved
table in a single `execute_code` pass. Key steps:

1. **Load the parsed table JSON** from `raw/_antibodysociety_approved_table.json`.
   Row 0 is the header; rows 1-168 are data.
2. **Skip existing entries** by slug. The pilot batch entries already exist.
3. **For each row**: parse target/format from the semicolon-separated "Target;
   Format" column. Determine modality (adc/bispecific/fragment/immunoconjugate/
   radioimmunoconjugate/naked-igg) from the format string. Determine status
   (approved/filed/withdrawn) from the EU/US year columns — `#` = withdrawn,
   `Review` = filed, year = approved. Use the `determine_areas()` function with
   word-boundary regex (`\b`) to assign therapeutic areas from the indication
   text.
4. **Write each entry** to `entries/<slug>.md` using the base template. Add
   appendix blocks for adc/bispecific/radioimmunoconjugate/withdrawn per the
   template files.
5. **Add non-table entries** (Fc-fusions, CAR-T products) from domain knowledge
   with `source_quality: medium`.
6. **Regenerate all six index files** + master index from the complete entry
   set by parsing each entry's `Therapeutic area(s)` field.
7. **Update CHANGELOG** with the sweep statistics.

The full sweep is a single `execute_code` call (no subagents needed). It takes
seconds, not minutes — the table is only 168 rows.

## Enrichment pipeline (deep profiling)

First-pass entries carry only the Antibody Society table fields: INN, brand,
target, format, indication, approval year. Deep profiling adds sequences,
structures, epitope contacts, and patent landscape via three dedicated
enrichment skills, each owning one machine-generated block. The pipeline was
validated end-to-end on nivolumab and trastuzumab (2026-08-18).

### Block discipline: curated vs machine-owned

The entry template has two kinds of blocks:

- **Curated blocks** (Identity, Provenance, Regulation, Mechanism, Relations,
  Source quality, Sources) — owned by THIS skill. Hand-authored from the
  Antibody Society table, regulatory documents, and the literature. The
  enrichment skills NEVER touch these.
- **Machine-owned blocks** (Sequences, Structures, IP & exclusivity) — each
  owned by its respective enrichment skill, which rewrites it wholesale on
  each run. THIS skill NEVER writes these blocks. Entries pre-enrichment
  simply lack them.

### The enrichment sequence (per entry)

1. **`antibody-sequence-search`** — resolve the molecule against the local
   Thera-SAbDab mirror (`raw/mirrors/TheraSAbDab_SeqStruc_OnlineDownload.csv`),
   verify against PDB structures, write the `## Sequences` block. Modality
   gate: `fc-fusion` -> `not-applicable`; `car-t` -> expect `not-public` (verify
   anyway). ADCs inherit the parent mAb's sequences (look up parent, not
   conjugate name).
2. **`structure-search`** — resolve against SAbDab mirror by name AND by VH/VL
   sequence (both modes mandatory -- code-name deposits are the norm for
   therapeutics). Compute epitope contacts from coordinates (4.5 A cutoff).
   Write the `## Structures` block. Chains from the SAbDab row, not from
   inspecting the file.
3. **`patent-search`** -- name search (Google Patents XHR) + sequence-derived
   search (PLAbDab exact match, then BLAST pataa). Write the `## IP &
   exclusivity` block. Every expiry carries `expiry_basis`.

Run sequence-search first (structures chain on VH/VL; patents chain on VH/VL
for PLAbDab/BLAST). The three skills are independent writes to different blocks,
so they can run in parallel after the sequence block is written.

### Remaining curated-field enrichment gap

After the three machine-owned blocks are filled, these curated fields are still
`Unknown` and need manual enrichment from Purple Book / EMA EPAR / FDA labels /
company disclosures:

- Developer / originator
- BLA / MAA / NDA numbers
- ADC payload, linker, DAR (curated -- the ADC appendix)
- Biosimilar lists
- CAR-T construct details (hinge, transmembrane, costimulatory domains)

The 14 non-table entries (etanercept, aflibercept, tisagenlecleucel + 11 added
during the full sweep) carry `source_quality: medium` and need full regulatory
verification before they reach Tier A confidence.

## Pitfalls

- **Assuming hit-list slugs from gene symbols.** Hit-list profiles use common-name
  slugs (`pd-1.md`, `her2.md`, `tnf.md`), not gene symbols (`pdcd1.md`,
  `erbb2.md`). Always `ls` the profiles directory and resolve against actual
  filenames.
- **Substring false positives in area tagging.** "sma" matches inside "melanoma";
  "als" matches inside "false". Use `\b` word boundaries in regex for short area
  keywords.
- **Newlines in the Antibody Society table.** Some INNs have embedded newlines
  (e.g., "Gemtuzumab\nozogamicin", "Inotuzumab\nozogamicin"). Strip/replace
  newlines before matching.
- **The Antibody Society table is mAbs only.** Fc-fusions (etanercept,
  aflibercept, romiplostim), CAR-T products (tisagenlecleucel,
  axicabtagene ciloleucel), and radioimmunoconjugates are NOT in the table or
  have incomplete entries. Source these from Purple Book / EMA EPAR / FDA labels
  separately, with `source_quality: medium`.
- **First-pass entries are sparse.** The Antibody Society table gives INN, brand,
  target, format, indication, and approval year — but NOT developer/originator,
  regulatory IDs (BLA numbers), ADC payload/linker details, or biosimilar lists.
  Mark unknown fields `Unknown`, never guess. Enrichment from Purple Book / EMA
  EPAR is a separate pass.
- **Circling on conventions instead of probing.** Don't block on the R2 format
  or the raw-source-archive convention before checking whether any binary
  source actually exists. Probe source Content-Types first — if everything is
  text (as in the pilot), the R2 path isn't triggered and the convention is
  irrelevant for that batch.
- **`references/` vs `resources/`.** The durable non-graph corpus layer is
  `references/`, not `resources/`. Always check the existing layer before
  creating a new directory. The registry lives at
  `references/therapeutic-antibodies/`.
- **Google Patents 503 is transient; PLAbDab is the reliable fallback.** The
  Google Patents XHR endpoint returns 503 intermittently. When it does, the
  patent-search skill falls back to PLAbDab sequence-derived candidates only
  and flags the name-search gap honestly in the IP block. Do not treat a 503
  as permanent or block the enrichment pipeline on it.
- **Delegated subagents falsely report `completed` under PubMed-429.** When a
  fan-out has each subagent do its own PubMed E-utilities lookups, a subagent
  that hits HTTP 429 (3 req/s burst) can burn its whole tool budget in a retry
  loop *before writing a single file*, then emit `status=completed` with a
  summary ending mid-research ("now I need to look up PMIDs…"). The batch still
  reports "ALL tasks ✓." **Never trust the batch report — verify files exist on
  disk** (`ls`/count the target directory) and re-dispatch or fill the gap
  yourself. This bit the virus-families sweep (2026-08-22): 5 of 15
  subagents false-completed, leaving 9 family folders empty. Two mitigations:
  (1) **pre-resolve PMIDs yourself** (title-verified esearch/esummary with
  ~0.8–1.2 s delays + User-Agent) and either write directly or hand subagents
  the verified PMID list so they don't re-search; (2) the orchestrator runs a
  bulk `PMID → esummary` audit over the *final* corpus — every PMID must
  resolve — because wrong/fabricated PMIDs cluster in memory-carried citations,
  not in freshly-looked-up ones.
- **Canonical raw-source-archive path.** The canonical raw-source-archive
  convention lives at `~/git/soma/profiles/mnemo/conventions/raw-source-archive.md`,
  not `references/conventions/raw-source-archive.md` (a mirror). Both exist;
  the soma-level one is authoritative.
- **compute_contacts.py multi-chain antigen syntax.** When the SAbDab row
  lists multiple antigen chains (e.g., `A|G` for a glycosylated target + NAG
  artifacts), pass them comma-separated (`--antigen A,G`), not pipe-separated.
  The pipe format causes a chain-mismatch failure.
- **IP block header is `## IP & exclusivity`, not `## Patents`.** The
  patent-search skill owns a block called `## IP & exclusivity`. Scanning
  entries for `## Patents` finds zero matches and produces a false negative.
  Always use the exact header string. See
  `references/enrichment-sweep-recipe.md` §Block header reference.
- **Complex shell one-liners trigger the command-size blocker.** When
  inventorying enrichment state across 100+ entries, write a Python script
  to `/tmp/` and run it, rather than building a multi-clause grep/awk
  one-liner. The inline command parser blocks oversized payloads.
- **Commit completed work before resuming delegation.** Interrupted sweeps
  leave enriched entries uncommitted. Commit them first so the auto-pusher
  doesn't bury real intent under a generic snapshot, and new subagent writes
  don't interleave with old ones in the same diff.
- **Subagent header-clobbering.** A delegated subagent told to "append
  enrichment blocks at end of file" may instead overwrite the entire file
  with only the enrichment blocks, destroying the curated header (Identity,
  Provenance, Mechanism, Sources). This happened to 5 Tier A entries
  (livmoniplimab, lparomlimab, lu-labeled-girentuximab, lutikizumab,
  manfidokimab) and was not caught until the index regeneration showed
  "Unknown" modality for those entries — the post-sweep block-coverage
  check passed because the enrichment blocks were present, but the curated
  blocks above them were gone. Post-sweep verification MUST check that
  curated blocks (at minimum `## Identity`) are still present in every
  enriched entry, not just that the 3 machine-owned blocks exist. Recovery:
  `git show <skeleton-commit>:<path>` to retrieve the original header,
  split the current file at `## Sequences`, and reassemble
  `original_header + "\n\n" + enrichment_blocks`. See
  `references/enrichment-sweep-recipe.md` §Post-sweep cleanup step 7.

## Relationship to other skills

- **`antibody-sequence-search`** (and its siblings `structure-search`,
  `patent-search`): per-entry enrichment passes that each own one
  machine-generated block (`## Sequences`, `## Structures`,
  `## IP & exclusivity`) and rewrite it wholesale. This skill builds and
  maintains the corpus's curated fields; the enrichment skills never touch
  them, and this skill never writes their blocks. The enrichment pipeline is
  documented in the "Enrichment pipeline" section above -- run
  sequence-search first, then structures and patents can run in parallel.
- **`antibody-target-hitlist`**: Target-side enumeration. This skill is the
  molecule-side complement. The hit-list's `profiles/` cross-reference to this
  corpus's `entries/` via target **common-name** slugs (not gene symbols — see
  "Cross-referencing to the hit-list" above).
- **`target-profiling`**: Builds deep per-target profiles. The profiles carry an
  "Antibody landscape" field that lists known antibodies — this corpus is the
  authoritative source for that field.
- **`literature-dive`**: Depth-first on one topic. This skill is breadth-first
  across all molecules.

## Tier B enumeration (active clinical)

Tier B (active clinical, Phase 1-3) is a different scale problem from Tier A.
The Antibody Society table gives ~168 approved molecules; Tier B needs
1,200-1,800 distinct molecules. Two sources, combined:

1. **ATW 2026 tables** (regulatory review + late-stage clinical) — 46 entries
   with target/format/indication. These are the highest-confidence Tier B
   entries (late-stage or filed). Parse from the already-fetched
   `_atw2026_fulltext.xml`. See `references/tier-b-recipe.md` for the full
   extraction pattern including the new -art/-tug/-bart INN naming convention.

2. **ClinicalTrials.gov REST API v2** — paginate through all active/recruiting
   mAb trials and extract unique -mab INNs from intervention names. This is
   the bulk Tier B source (~100-150 additional molecules). See
   `references/tier-b-recipe.md` for the pagination + INN extraction + dedup
   pattern.

**INN cleaning is critical.** ClinicalTrials.gov intervention names contain
radioisotope prefixes (131i-, 177lu-), combination-therapy concatenations
(FOLFOX+bevacizumab), code names (HX008), and misspellings (ipililumab,
tocilicumab). Extract -mab-ending words with regex, strip prefixes, then
fuzzy-match against existing Tier A entries (cutoff=0.85) to remove
misspellings. Also manually filter Tier A parent names (brentuximab is the
parent of brentuximab vedotin, already a Tier A entry).

**New INN naming convention.** The WHO has shifted antibody INN suffixes:
-mab is being replaced by -art (antagonist/receptor), -tug (targeted
inhibitor), -bart (antagonist), and other suffixes. ATW 2026 tables contain
many of these (e.g., crusekitug, rademikibart, tozorakimab). Search for
both -mab and the new suffixes when extracting INNs.

## Changelog

- **2026-08-19 — Tier B enrichment sweep complete (134 entries, all 3 blocks).**
  All 134 Tier B entries now carry Sequences + Structures + IP & exclusivity.
  First wave enriched 107 entries (all 3 blocks) + 5 with Sequences + Structures
  only. API interruption left 117 files uncommitted; resumption committed
  these, pre-checked Thera-SAbDab hits for the remaining 27 entries (20 exact,
  2 cocktail splits, 1 not-found), then dispatched 7 parallel batches (6
  full-pipeline + 1 IP-only). Post-sweep discovered 5 Tier A entries from the
  prior sweep whose curated headers had been clobbered by a subagent —
  recovered from skeleton commit, merged with enrichment blocks. Added the
  header-clobbering pitfall and post-sweep cleanup step 7 (curated-block
  integrity check) to the skill and recipe. Final corpus: 321 entries
  (182 Tier A + 139 Tier B), all enriched. Coverage: 112/134 with sequences
  (84%), 8 with complex structures, 108 with IP candidates.

- **2026-08-18 — Tier B skeleton (139 entries).** Built 139 Tier B entry
  skeletons from ATW 2026 tables (39 with target/format/indication) +
  ClinicalTrials.gov (100 INN-only, source_quality: low). 3,761 active mAb
  trials paginated, 263 INNs extracted, fuzzy-matched against Tier A,
  manually filtered. Fixed line-number prefix corruption in 5 Tier A
  entries. Total corpus: 321 entries. See `references/tier-b-recipe.md`.

- **2026-08-18 — full Tier A enrichment sweep (182 entries, all 3 blocks).**
  All 182 Tier A entries enriched via 35 delegated subagent batches. 162
  with complete sequences (89%), 97 with complex structures + computed
  epitope contacts (53%), 162 with IP candidates (89%). 8 Fc-fusions marked
  not-applicable, 6 CAR-T marked not-public, 5 not-found. Google Patents 503
  throughout — PLAbDab + BLAST fallback. Post-sweep: normalized status values
  (backtick-wrapped, trailing periods), wrote not-applicable/not-public
  blocks, cleaned temp files, regenerated indexes with enrichment columns.

- **2026-08-18 — enrichment pipeline validated.** The three enrichment skills
  (`antibody-sequence-search`, `structure-search`, `patent-search`) were run
  end-to-end on nivolumab and trastuzumab. The pipeline produces a full deep
  profile: VH/VL sequences (Thera-SAbDab, structure-verified), PDB structures
  with computed epitope contacts (4.5 A cutoff), and patent candidates
  (PLAbDab + Google Patents). Replaced the "Enrichment gap" section with a
  proper "Enrichment pipeline" section documenting the block-discipline model
  (curated vs machine-owned blocks), the enrichment sequence, and the
  remaining curated-field gap. Added pitfalls: Google Patents 503 transient
  fallback, canonical raw-source-archive path, compute_contacts multi-chain
  antigen syntax.

- **2026-08-18 — full Tier A sweep (182 entries).** All 168 rows from the
  Antibody Society approved-antibody table processed (171 after dedup/slug
  resolution), plus 14 non-table entries: 8 Fc-fusions (etanercept,
  aflibercept, romiplostim, dulaglutide, albiglutide, efanesotocoz,
  rurioctocoz, eftrenonacoz) and 6 CAR-T products (tisagenlecleucel,
  axicabtagene ciloleucel, brexucabtagene autoleucel, lisocabtagene
  maraleucel, idecabtagene vicleucel, ciltacabtagene autoleucel). Six index
  files regenerated. Modality: naked-igg 132, adc 15, bispecific 14,
  fc-fusion 8, car-t 6, fragment 6, immunoconjugate 1. Status: approved
  163, filed 11, withdrawn 8. Index: oncology 95, immunology-inflammation
  48, infectious-disease 16, ophthalmology-rare 14, neuroscience 12,
  cardiovascular-metabolic 6. Also created
  `references/conventions/raw-source-archive.md` mirroring the grants
  page-type R2 convention, added `therapeutic-area` field to base
  template, and added `index/` spec to master.md. Non-table entries
  carry `source_quality: medium` and need regulatory verification.

- **2026-08-18 — initial creation.** Built during the therapeutic-antibodies
  registry pilot: 27 Tier A entries across all modalities, 6 index files, 11 raw
  source captures. Scope decisions locked with Bryan: Tier D floor = public
  identifier; separate records per drug product; Fc-fusions in, non-antibody
  scaffolds out; flat entries/ with modality field; conventions folded into
  master.md.
