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

## Enrichment gap (next pass)

The first-pass entries carry only the Antibody Society table fields: INN, brand,
target, format, indication, approval year. The following fields are marked
`Unknown` and need enrichment from Purple Book / EMA EPAR / company disclosures:

- Developer / originator
- BLA / MAA / NDA numbers
- ADC payload, linker, DAR
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

## Relationship to other skills

- **`antibody-sequence-search`** (and its siblings `structure-search`,
  `patent-search`): per-entry enrichment passes that each own one
  machine-generated block (`## Sequences`, `## Structures`,
  `## IP & exclusivity`) and rewrite it wholesale. This skill builds and
  maintains the corpus's curated fields; the enrichment skills never touch
  them, and this skill never writes their blocks.
- **`antibody-target-hitlist`**: Target-side enumeration. This skill is the
  molecule-side complement. The hit-list's `profiles/` cross-reference to this
  corpus's `entries/` via target **common-name** slugs (not gene symbols — see
  "Cross-referencing to the hit-list" above).
- **`target-profiling`**: Builds deep per-target profiles. The profiles carry an
  "Antibody landscape" field that lists known antibodies — this corpus is the
  authoritative source for that field.
- **`literature-dive`**: Depth-first on one topic. This skill is breadth-first
  across all molecules.

## Changelog

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
