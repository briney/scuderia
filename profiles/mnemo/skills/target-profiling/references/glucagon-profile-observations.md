# Glucagon (GCG) Profile — Session Observations

**Date**: 2026-08-17
**Profile**: working-docs/hitlist-profiles/glucagon.md (~52K chars, 234 lines)
**Tier assigned**: Preclinical (cardiovascular/metabolic)
**Papers reviewed**: 14 (all abstract-only — no full-text retrieval attempted)
**PMIDs cited**: 22 unique (225 total citations)
**UniProt**: P01275 (preproglucagon, 180 aa, 20.9 kDa)

## Target biology summary

Glucagon is a 29-aa secreted peptide hormone (residues 53–81 of preproglucagon)
produced by pancreatic α-cells and intestinal L cells. It is the principal
counterregulatory hormone to insulin — raises blood glucose via hepatic
glucagon receptor (GCGR, UniProt P47871, class B GPCR) → Gαs → cAMP → PKA →
gluconeogenesis and glycogenolysis. Hyperglucagonemia is present in every form
of diabetes and drives excessive hepatic glucose output.

The GCG gene also encodes GLP-1, GLP-2, glicentin, and oxyntomodulin via
tissue-specific prohormone processing (PCSK2 in α-cells → glucagon; PCSK1 in
L cells → GLP-1/GLP-2). These are separate therapeutic targets.

## PubMed search strategy

### Queries used (5 initial + 5 supplementary)

**Batch 1** (all succeeded, 4s sleep between calls):
1. `"glucagon antibody"[tiab] AND ("therapeutic"[tiab] OR "neutralizing"[tiab] OR "monoclonal"[tiab])` → 6 PMIDs
2. `"anti-glucagon antibody"[tiab]` → 10 PMIDs
3. `"GCG antibody therapeutic"[tiab]` → 0 PMIDs (gene symbol too narrow)
4. `glucagon[tiab] AND antibody[tiab] AND diabetes[tiab] AND (preclinical[tiab] OR clinical[tiab])` → 10 PMIDs
5. `glucagon[tiab] AND "monoclonal antibody"[tiab] AND (neutraliz*[tiab] OR antagonis*[tiab])` → 10 PMIDs

**Batch 2** (hit HTTP 429 on queries 2 and 4 — rate limiting):
1. `REGN1193[tiab]` → 2 PMIDs (succeeded)
2. `REMD-2.59[tiab] OR "REMD 2.59"[tiab]` → HTTP 429, 0 PMIDs
3. `"glucagon receptor antibody"[tiab] AND (diabetes[tiab] OR clinical[tiab])` → 9 PMIDs (succeeded)
4. `"anti-glucagon"[tiab] AND (antibody[tiab] OR monoclonal[tiab]) AND (preclinical[tiab] OR diabetes[tiab])` → HTTP 429 partial
5. `glucagon[tiab] AND immunoneutralization[tiab]` → 10 PMIDs (succeeded)

**Batch 3** (specific PMID efetch, succeeded after 3s pause):
- 8 additional key PMIDs fetched: 29283470, 25675519, 17003351, 1727732, 35649369, 27115412, 23744070, 26020795

### Key papers identified

| PMID | First author | Journal | Year | Topic |
|------|-------------|---------|------|-------|
| 7851693 | Brand CL | Diabetologia | 1994 | Glu-mAb immunoneutralization in STZ rats (landmark) |
| 8690155 | Brand CL | Diabetes | 1996 | Glucagon role in rabbits (Glu-mAb) |
| 7573424 | Brand CL | Am J Physiol | 1995 | Glucagon in fed/fasted rats (Glu-mAb) |
| 17003351 | Gu et al. | Diabetes | 2006 | Immunoneutralization in ob/ob mice |
| 1727732 | Holst et al. | Diabetes | 1992 | Immunoneutralization normalizes urea synthesis |
| 25675519 | Wang et al. | PNAS | 2015 | GCGR antibody suppresses T1D without insulin |
| 26020795 | — | Endocrinology | 2015 | REGN1193 in mice and monkeys |
| 28755409 | Kostic et al. | Diabetes Obes Metab | 2018 | REGN1193 first-in-human Phase 1 |
| 29283470 | — | Diabetes Obes Metab | 2019 | REMD-477 Phase 2 RCT in T1D |
| 31203188 | Wei et al. | iScience | 2019 | REMD 2.59 promotes α/β-cell proliferation |
| 35649369 | — | Cell Rep | 2022 | Anti-GcgR β-cell regeneration in NHPs |
| 27115412 | Unger & Cherrington | Diabetologia | 2017 | Glucagon as key factor in diabetes |
| 25924114 | Lefèbvre | Diabetes Obes Metab | 2015 | Review: inhibiting/antagonizing glucagon |
| 23744070 | — | J Biol Chem | 2013 | NOX-G15 aptamer (non-antibody validation) |

## UniProt data gathered (P01275)

- **Entry**: GLUC_HUMAN, preproglucagon
- **Length**: 180 aa, 20,909 Da
- **Function**: Key role in glucose metabolism; counterregulatory hormone to
  insulin; increases gluconeogenesis, decreases glycolysis; binds GCGR → Gαs
  → cAMP → downstream metabolic responses
- **Tissue specificity**: Secreted by A-cells of islets of Langerhans,
  enteroendocrine L cells throughout GI tract, selected neurons in brain
- **PTM**: Tissue-specific processing by PCSK2 (α-cells → glucagon) and
  PCSK1 (L cells → GLP-1, GLP-2, glicentin, oxyntomodulin)
- **PDB structures**: 39 cross-references including glucagon–GCGR complexes
  (6LMK, 6LML, 7KI0, 7KI1 — cryo-EM)
- **Key features**: Cleavage sites at 52-53, 83-84, 91-92, 97-98, 130-131,
  145-146; phosphoserine modifications; C-terminal amidation

## Two antibody strategies identified

### 1. Anti-glucagon ligand antibodies (immunoneutralization)

- **Glu-mAb** (Brand et al., 1994, PMID 7851693): Mouse IgG hybridoma,
  high-capacity (40 nmol/mL), high-affinity (Kd 0.6 × 10¹¹ L/mol).
  Completely abolished exogenous glucagon hyperglycemic effect in normal
  rats. Normalized postprandial hyperglycemia in moderately STZ-diabetic
  rats (10.5→9.3 mmol/L vs control 11.2→17.3 mmol/L).
- **Polyclonal anti-glucagon** (Holst et al., 1992, PMID 1727732): Weekly
  injection in STZ-diabetic rats normalized urea synthesis, decreased
  nitrogen wasting. Binding capacity 10–15× endogenous glucagon.
- **Glucagon mAb in ob/ob mice** (Gu et al., 2006, PMID 17003351): Reduced
  HGO, improved OGTT, increased hepatic glycogen synthesis, reduced HbA1c
  after 14 days.
- **Status**: All preclinical. No anti-glucagon ligand antibody has entered
  clinical trials. The high-capacity dosing requirement (4 mL/kg for Glu-mAb)
  is a practical barrier.

### 2. Anti-GCGR receptor antibodies (receptor antagonism)

- **REGN1193** (Regeneron): Fully human IgG, VelocImmune technology.
  Phase 1 completed (42 healthy volunteers, 0.05–0.6 mg/kg IV).
  Preclinical: normalized glucose in ob/ob mice, DIO mice, diabetic
  cynomolgus monkeys. Small transient ALT/AST elevations (<3× ULN).
  PMID 26020795, 28755409.
- **REMD-477 / REMD 2.59** (REMD Biotherapeutics): Human IgG.
  Phase 2 RCT completed (21 T1D patients, NCT02715193, single 70-mg dose):
  26% insulin reduction, 27 mg/dL lower average glucose, 25% more
  time-in-range, no hypoglycemia, no SAEs. Preclinical: α-cell proliferation,
  β-cell mass expansion, ductal neogenesis. PMID 29283470, 31203188,
  35649369.
- **mAb GCGR** (Lau et al., 2009, PMID 19851873): PK/PD modeling in
  ob/ob mice, dose-dependent glucose lowering at 0.6, 1, 3 mg/kg.

## Key observations for future profiles

### Ligand vs receptor targeting for secreted peptides
The glucagon profile revealed a fundamental distinction for secreted peptide
hormone targets: ligand-targeting antibodies (immunoneutralization) face a
pharmacokinetic barrier — continuously secreted peptides require stoichiometric
antibody capacity, not just receptor occupancy. The Glu-mAb needed 40 nmol/mL
capacity and 4 mL/kg dosing. Anti-GCGR receptor antibodies only need to occupy
the receptor, making dosing more practical. This generalizes to all secreted
peptide hormone targets (somatostatin, GLP-1, GIP, insulin, ANP).

### Cross-species conservation
Mature glucagon (29 aa) is 100% identical across all mammals. GCGR is ~90%
conserved human-to-mouse. The same antibodies worked across rats, rabbits,
mice, monkeys, and humans without re-engineering. This is a major
preclinical advantage for secreted peptide hormones — note the degree of
conservation in fields 2 and 4.

### PubMed E-utilities rate limiting
NCBI E-utilities enforce ~3 requests/second sustained. A burst of 10
esearch+efetch calls within ~60s can trigger HTTP 429. The 429 clears within
seconds, not minutes. When doing >5-6 sequential calls, increase sleep to
5-6s or split across two execute_code calls. Gene symbol queries
(`"GCG antibody therapeutic"[tiab]`) return 0 results — use full protein name
and receptor name queries instead.

### Tier recalibration pattern (repeated)
The target was labeled "preclinical" but had two clinical-stage anti-GCGR
antibodies (REGN1193 Phase 1, REMD-477 Phase 2). PubMed-only tier assignment
misses small-biotech clinical programs. This is the same pattern seen in
the alpha2-antiplasmin profile. Always search for specific program codes
(REGN, REMD) or ClinicalTrials.gov before assigning a tier.

### On-target transaminase elevation (class effect)
REGN1193 Phase 1 showed ALT/AST elevations. Small-molecule GCGR antagonists
from Merck, Pfizer, Lilly showed the same. Shared safety signal across
modalities = on-target mechanism-based toxicity. For field 8, when both
antibody and small-molecule antagonists exist, compare safety signals
across modalities.

### No hypoglycemia (counterintuitive safety)
GCGR blockade does not cause hypoglycemia despite blocking a
glucose-raising hormone. Compensation via ghrelin and amino acid metabolism
(PMID 28487437). For field 8, check whether predicted mechanism-based risks
materialize in actual data — counterintuitive findings are differentiation
signals.

## Profile structure notes

- All 11 fields present and verified
- No frontmatter (working doc, not brain page)
- Field 11 marked as judgment with italic header
- 22 unique PMIDs cited (225 total citations)
- No "Unknown"/"No data" — all fields filled from literature
- 3 occurrences of "Not publicly disclosed" (antibody epitope details)
- PDB structures listed from UniProt cross-references (39 structures)
