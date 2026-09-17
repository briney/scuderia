---
name: therapeutic-antibody-registry
description: "Use when building or maintaining the molecule-level therapeutic-antibody registry corpus — one record per drug product, Tier A-D."
triggers:
  - "therapeutic antibody registry"
  - "antibody molecule database"
  - "build antibody entries"
  - "antibody registry"
  - "Tier A antibody"
  - "approved antibody list"
  - "references/therapeutic-antibodies"
eval_contract:
  goal: |
    Build and maintain the molecule-level registry with one record per drug
    product, correct tiering, and curated blocks that survive enrichment.
  dimensions:
    - "IDENTITY — one record per drug product/INN; extracted names are candidates, never merged on sequence identity alone"
    - "BLOCK_DISCIPLINE — curated blocks intact in every enriched entry; machine-owned blocks written only by their owner skills"
    - "SOURCE_HONESTY — unknown fields marked Unknown; no completeness claim beyond what the run record verifies"
  hard_fails:
    - Fabricating registry fields from domain knowledge instead of a source.
    - An enriched entry losing its curated (`## Identity`-bearing) header blocks.
    - Pointing at recipe files that no verified record backs.
---

# Therapeutic-antibody registry

Build and maintain the instance's `references/therapeutic-antibodies/` corpus,
one record per drug product. This is the molecule-side complement to the
`references/antibody-target-hitlist/` target corpus, not a graph page type.

## Scope and identity

- **In:** therapeutics with an antibody-derived binding or structural domain
  (Fab, scFv, VH/VL, VHH) or an antibody-isotype Fc domain. Includes naked
  antibodies, conjugates, multispecifics, fragments, Fc-fusions, and CAR cell
  products with antibody-derived binders.
- **Out:** non-antibody scaffolds without an antibody-derived domain, small
  molecules, peptides, antisense/siRNA, oncolytic viruses, and TCR therapeutics
  without an antibody-derived domain.
- **Record key:** drug product/INN, or public code name when no INN exists;
  never target, program, brand, or sequence identity. Keep naked parents,
  conjugates, radioisotope-labeled products, and licensed fixed combinations
  distinct and linked. A multispecific is one record, not one per arm.
  Biosimilars normally remain a sub-list on the originator; follow the corpus
  contract for exceptions.
- **Tiers:** A = approved or filed; B = active clinical Phase 1–3, not already
  approved/filed; C = discontinued/withdrawn after reaching Phase 2 or later;
  D = named preclinical with a public identifier. Preserve region-specific
  approval/withdrawal history; withdrawn means previously approved,
  discontinued means development stopped before approval.
- **Tier D floor:** at least one trial-registry ID, peer-reviewed publication,
  named candidate in an official company disclosure, or WHO INN/USAN.
  An unidentified discovery binder is outside this corpus's standing scope.

Raw intervention names, prefix-stripped forms, and fuzzy matches are lookup
candidates, not identity authority. Preserve the source name; verify identity
and status before creating or merging records. Fold only confirmed aliases;
identical VH/VL does not authorize a merge. Do not discard a naked-parent
candidate because a conjugate exists. Search code names and current WHO names,
not only `-mab`; suffixes establish neither modality nor development stage.

## Entry contract and write ownership

Read the instance corpus's `master.md` before work: it owns the full scope,
status vocabulary, failure taxonomy, and directory/index definitions. Read
`templates/entry-template.md` when writing an entry, plus only the relevant
appendices: `adc-template.md` for conjugates, `multispecific-template.md` for
multiple specificities, `car-template.md` for CAR products, and
`failed-template.md` for discontinued/withdrawn records or failure history.
These paths are relative to `references/therapeutic-antibodies/`; skill-local
recipes below are relative to this skill. Profile paths follow `skills/RESOLVER.md`.

This skill owns curated fields. The separate enrichment skills own exactly:

| Header | Owner |
|---|---|
| `## Sequences` | `antibody-sequence-search` |
| `## Structures` | `structure-search` |
| `## IP & exclusivity` | `patent-search` |

Each owner replaces only its block; unenriched entries may lack those blocks.
All other content is protected during enrichment, including Identity,
Provenance, Regulation, Mechanism, ADA, Relations, Sources, and modality/failure
appendices. Require `## Identity` and compare non-owned content before/after;
block presence alone is not completion. One writer owns an entry file at a
time, even when workers target different blocks. Run sequence enrichment first;
structure and patent searches use its verified VH/VL. They may research in
parallel from the same snapshot, but writes to that entry must be serialized.

## Procedure

1. **Inspect the requested records and sources.** Read existing entries before
   editing; resolve INN/code-name aliases against the product contract. Keep
   source-backed fields, source dates, and unresolved conflicts. Never fill
   facts from domain knowledge; use `Unknown` / `No data` when unsupported.
   Tier describes development status, not confidence or field completeness.
2. **Acquire only the sources needed.** The Antibody Society approved table
   (`https://www.antibodysociety.org/resources/approved-antibodies/`) supplies
   INN, brand, target/format, indication, and regional approval/review data.
   ATW annual reviews supply approval, regulatory-review, and clinical tables;
   classify them by caption and date. FDA Purple Book/labels, EMA EPAR, PMDA,
   NMPA, and official disclosures cover omitted products and curated details
   such as developer, regulatory IDs, biosimilars, ADC chemistry, and CAR
   constructs. Verify non-table product fields against regulatory/official
   sources; neither historical candidate lists nor model memory supply facts.
   Load `references/source-extraction.md` when fetching/parsing table or ATW
   sources. Preserve raw text captures in `raw/`; inspect response type and
   bytes. For binaries, load `skills/conventions/raw-source-archive.md`, use
   the configured archive binding and `therapeutic-antibodies/<sha256>.<ext>`,
   and retain the verified source pointer; no binaries in Git.
3. **Build or update curated records.** For Tier A table work, load
   `references/tier-a-sweep-recipe.md`. Test a representative pilot before a
   new bulk run, covering the modalities and identity/status edge cases in
   that run; verify template fills, source mappings, multi-area assignment,
   and target pointers before scaling. Measure actual inputs and coverage.
   Existing slugs require identity comparison, not blind overwrite or skip.
4. **Enrich only through the block owners.** Load the relevant sequence,
   structure, or patent skill. For bulk enrichment or interrupted-sweep
   resumption, also load `references/enrichment-sweep-recipe.md`; it owns
   execution, integrity checks, and recovery. Unknown curated fields remain
   curated work; populated machine blocks do not verify the whole entry.
5. **Verify and regenerate views.** Check claims against cited source rows or
   passages, identities, tiers, template fields, and protected content. Resolve
   target pointers against actual hit-list filenames: common-name slugs such
   as `pd-1.md` and `her2.md`, not assumed gene-symbol filenames. Pointers are
   plain paths, one per applicable target, not wikilinks. Areas use the corpus's
   six-value vocabulary, primary-first and multi-tag; match indication terms
   at word boundaries to avoid `sma` inside `melanoma`. Regenerate the area
   lists and master index from canonical entries, never as a second authority.
6. **Report and close the verified unit.** Record measured coverage, source
   gaps, and material corpus changes in the instance's existing run record or
   `CHANGELOG.md`. History stays private, not in reusable skill instructions.
   Follow `skills/git-ops/SKILL.md`: standalone work closes verified entries
   and required index changes; a sweep parent owns shared writes and coherent
   closeout. Children return paths and source-linked evidence, never stage,
   commit, or publish independently.

## Tier B discovery limit

ATW late-stage clinical tables and ClinicalTrials.gov intervention names supply
candidates. Regulatory-review rows belong to Tier A. Before fresh registry
extraction, check current API filters, pagination, and fields on a small real
response; record the query, retrieval date, and coverage. An active trial may
contain approved comparators; a terminated sub-study does not by itself prove
that a product was discontinued. Verify product-level status from sources.

This skill supports source-backed individual Tier B entries and a bounded
pilot, not a validated exhaustive enumeration recipe. Before scaling a new
bulk run, verify extraction and identity handling on the pilot and report
coverage gaps. Prior snapshots in `raw/` and historical counts in `CHANGELOG.md`
are evidence of earlier runs, not completeness criteria.
