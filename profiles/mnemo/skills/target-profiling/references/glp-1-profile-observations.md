# GLP-1 (Glucagon-like peptide 1) — profile observations

**Date**: 2026-08-16
**Tier**: clinical-trial
**Therapeutic area**: cardiovascular / metabolic (diabetes, obesity, CVD)
**Profile**: `working-docs/hitlist-profiles/glp-1.md`
**Size**: ~39K chars, 6 unique PMIDs cited
**Papers ingested**: 5 total (3/5 full text via PMC XML, 2/5 abstract-only) — 60% retrieval

## Ingested papers

| PMID | First author | Year | Journal | PMCID | Provenance | Chars |
|------|-------------|------|---------|-------|------------|-------|
| 38316982 | Véniant | 2024 | Nature Metab | PMC10896721 | pmc-xml | 58K |
| 33068776 | Nauck | 2021 | Mol Metab | PMC8085572 | pmc-xml | 90K |
| 34626851 | Drucker | 2022 | Mol Metab | PMC8859548 | pmc-xml | 56K |
| 35015037 | Rubino | 2022 | JAMA | PMC8753508 | abstract | 7K |
| 24467746 | Pyke | 2014 | Endocrinology | — | abstract | 2K |

## PubMed search strategy

Four topic-area queries (esearch, retmax=8, sort=relevance):
1. `GLP-1 antibody` — 1,052 results, top 8 returned
2. `glucagon-like peptide 1 diabetes` — 21,068 results, top 8 returned
3. `semaglutide liraglutide obesity` — 713 results, top 8 returned
4. `GLP-1 agonist cardiovascular` — 5,676 results, top 8 returned

31 unique PMIDs after deduplication. All esummary metadata fetched in a
single batch call (31 IDs in one esummary request).

## Paper selection rationale

From 31 unique PMIDs, 5 were selected spanning all four search topics:
- **AMG 133 Phase 1 clinical trial** (PMID 38316982) — the only antibody-based
  GLP-1 system therapeutic in clinical development; Nature Metab, OA
- **GLP-1 RA T2D state-of-the-art review** (PMID 33068776) — comprehensive
  review with CVOT meta-analysis data; Mol Metab, OA
- **GLP-1 physiology and obesity pharmacotherapy** (PMID 34626851) — Drucker
  review with STEP trial data and CNS mechanisms; Mol Metab, OA
- **STEP 8 head-to-head trial** (PMID 35015037) — semaglutide vs liraglutide
  Phase 3b; JAMA (paywalled, abstract-only)
- **GLP-1R tissue localization** (PMID 24467746) — foundational IHC mapping
  with validated mAb; Endocrinology (paywalled, abstract-only)

## Key new patterns observed

### 1. Peptide-ligand target profiling — FIRST OCCURRENCE

GLP-1 is the **first peptide-ligand target** profiled (a 30-amino-acid
secreted hormone, not a receptor or large surface protein). This creates
distinct profiling challenges:

- **Field 1 (target identity)**: The "target" is a cleavage product of a
  larger precursor (proglucagon/GCG gene). The UniProt ID is for the
  precursor (P01275), not the active peptide. Document the processing
  pathway (proglucagon → GLP-1(7-36)amide + glucagon + GLP-2 + others).
- **Field 1 (localization)**: The peptide is secreted and circulates at
  picomolar levels with a half-life of ~2 min (DPP-4 degradation). This
  makes direct antibody targeting of the peptide impractical — the
  therapeutic strategy targets the RECEPTOR (GLP-1R), not the ligand.
  The profile must explain this distinction clearly.
- **Field 1 (MW)**: ~3.3 kDa — orders of magnitude smaller than any
  prior profiled target. The "oligomerization" and "key domains" fields
  are reinterpreted as functional domains of a 30-aa peptide (N-terminal
  activation region, α-helical binding region, C-terminal amidation).
- **Field 4 (antibody landscape)**: No anti-GLP-1 ligand antibodies in
  development. The antibody landscape is entirely about GLP-1R-targeting
  approaches or antibody-peptide conjugates where the antibody provides
  PK extension and the peptide provides pharmacology.
- **Field 5 (epitope landscape)**: Not applicable in the traditional sense
  for a 30-aa peptide. The "epitope" concept maps to the peptide's
  functional domains (DPP-4 cleavage site at position 8, receptor-binding
  α-helix at residues 15-28).

Generalizable to any peptide-ligand target (GIP, glucagon, GLP-2,
oxyntomodulin, PYY, NPY) where the therapeutic strategy targets the
receptor or uses antibody-peptide conjugates rather than anti-ligand
antibodies.

### 2. Antibody-peptide conjugate format — distinct from agonistic antibody

AMG 133 (maridebart cafraglutide) represents a format pattern distinct
from both the FGF21 agonistic-antibody approach and standard
neutralizing-antibody approaches:

- **The antibody provides PK, not pharmacology.** The anti-GIPR antibody
  in AMG 133 extends half-life to 14-24 days (vs ~2 min for native GLP-1,
  ~13 h for liraglutide). The GLP-1 peptide payload provides the
  GLP-1R agonism. This is fundamentally different from the FGF21 39F7
  agonistic antibody, where the antibody ITSELF activates the receptor.
- **The antibody targets a DIFFERENT receptor than the peptide.** AMG
  133's antibody targets GIPR (antagonist); the GLP-1 peptide targets
  GLP-1R (agonist). The bispecific mechanism (GIPR antagonism + GLP-1R
  agonism) is achieved through a conjugate, not a dual-epitope antibody.
- **Field 4 implications**: Document the conjugate format separately from
  both naked antibodies and peptide agonists. The format entry should
  specify: antibody target, peptide target, linker chemistry,
  drug-to-antibody ratio (2 GLP-1 peptides per antibody in AMG 133),
  and conjugation site (E384C).
- **Field 6 implications**: The success factor is PK extension (monthly
  dosing) + dual mechanism (GIPR antagonism adds weight loss beyond
  GLP-1R agonism alone). The GI tolerability pattern (68% TEAEs after
  first dose → 9% after subsequent) suggests that dosing frequency
  affects tolerance development — a potential advantage over daily/
  weekly peptide dosing.

Generalizable to any peptide-ligand system where an antibody conjugate
can extend PK beyond what peptide engineering (fatty acid acylation,
PEGylation) achieves.

### 3. CVOT meta-analysis as a high-value profiling source

The Nauck et al. review (PMID 33068776) contains a comprehensive
meta-analysis of ALL GLP-1 RA cardiovascular outcome trials (ELIXA,
LEADER, SUSTAIN-6, EXSCEL, REWIND, HARMONY Outcomes, PIONEER-6). This
type of review is extremely high-value for cardiovascular/metabolic
profiles because:

- **It provides class-effect data.** Individual CVOTs are underpowered
  for individual endpoints (MI, stroke, CV death); the meta-analysis
  pools across all trials to show significant 9-16% reductions.
- **It identifies the negative trial (ELIXA/lixisenatide).** The one
  CVOT that failed is critical for field 6 (failure modes).
- **It provides the mechanism.** The review includes a detailed
  mechanistic section on how GLP-1R activation in the vasculature
  produces anti-atherosclerotic effects — directly grounding field 2
  in full-text content.

Generalizable to any cardiovascular/metabolic target with multiple
CVOTs (SGLT-2 inhibitors, PCSK9 antibodies).

### 4. Existing GLP-1R profile as a cross-reference

The GLP-1R receptor profile (`working-docs/hitlist-profiles/glp-1r.md`)
already existed, built with neurodegeneration-focused papers. The GLP-1
ligand profile complements it by focusing on metabolic/CV. When profiling
a ligand whose receptor has already been profiled, read the sibling
receptor profile first to avoid redundant search and ensure consistent
cross-referencing.
