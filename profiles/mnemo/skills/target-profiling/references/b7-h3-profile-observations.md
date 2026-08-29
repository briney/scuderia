# B7-H3 (CD276) Profile Observations

**Profile**: working-docs/hitlist-profiles/b7-h3.md
**Tier**: Clinical-trial
**Therapeutic area**: Oncology
**Date**: 2026-08-16
**Papers ingested**: 5 (PMID 28399408, 28685773, 40946079, 41926962, 41086386)
**Profile size**: ~40K chars, 16 unique PMIDs cited
**Full-text retrieval**: 2/5 PMC XML OA (Seaman 2017 Cancer Cell, Rudin 2026 JCO), 3/5 abstract-only (Lee 2017 Cell Research, Corrigan 2025 Trends Pharmacol Sci, Johnson 2026 Lancet Oncol)

## Key new patterns

### 1. Dual-mechanism target: immune checkpoint + ADC antigen

B7-H3 is the **first target profiled where the same molecule serves two
fundamentally different therapeutic roles simultaneously**: (a) a T cell
checkpoint whose blockade enhances anti-tumor immunity (Lee 2017, PMID
28685773), and (b) a tumor-associated antigen overexpressed on both tumor
cells AND tumor vasculature, serving as an ADC delivery target (Seaman 2017,
PMID 28399408). These two mechanisms require different antibody properties:

- **Checkpoint blockade** needs a surface-retaining, signaling-disrupting
  antibody (like anti-PD-1/PD-L1 antibodies).
- **ADC targeting** needs a rapidly internalizing antibody that delivers
  payload regardless of signaling effect.

Clinical development has overwhelmingly favored the ADC approach (ifinatamab
deruxtecan, vobramitamab duocarmazine) over the checkpoint approach
(enoblituzumab). The naked Fc-enhanced antibody (enoblituzumab) showed only
modest tumor growth delays -- B7-H3's checkpoint function is "largely
redundant for tumor growth" (PMID 28399408). The ADC format is necessary for
meaningful efficacy. For field 2 (biological mechanism) and field 6 (failure
modes), the profile must explicitly state which mechanism is clinically
tractable and why -- dual-mechanism targets may have one mechanism that is
biologically real but therapeutically impractical.

**Generalizable**: When a target has both immune-checkpoint and
antigen-delivery functions, profile both mechanisms but flag which is
clinically validated. The ADC approach may dominate even when the checkpoint
biology is more mechanistically elegant.

### 2. Dual-compartment targeting: tumor cells + tumor vasculature

B7-H3 is the **first target profiled with expression on both tumor cells AND
tumor vasculature** (tumor endothelial cells, 51% of tumors strongly
positive). This creates a "dual-compartment" targeting opportunity -- an ADC
can kill both the tumor and its blood supply simultaneously. However, the
warhead choice determines whether vasculature targeting works:

- **MMAE (tubulin inhibitor)**: completely ineffective against CD276+
  tumor endothelial cells because they express P-glycoprotein (P-gp/ABCB1/MDR1),
  which effluxes MMAE. Only kills tumor cells.
- **PBD dimers (DNA crosslinkers)** and **DXd (topoisomerase I inhibitor)**:
  not P-gp substrates, effectively target both compartments. 60% cure rate
  in preclinical dual-compartment models vs. single-compartment only (PMID
  28399408).

The clinical success of ifinatamab deruxtecan (DXd payload) validates this
preclinical finding -- DNA-damaging payloads are superior for B7-H3 ADCs
because they enable vascular targeting.

**Generalizable**: For any target expressed on tumor vasculature, the
warhead must be non-P-gp-substratable. This is a warhead selection rule, not
a target biology rule. Include P-gp efflux status in field 6 (success
factors) for any ADC target with vascular expression.

### 3. Warhead class effect (ILD) vs. target-specific safety

The most significant adverse event for ifinatamab deruxtecan is interstitial
lung disease (ILD): 12.4% treatment-related, 4.4% grade >=3, 1.5% grade 5
(PMID 41086386). This is a DXd ADC class effect shared with T-DXd
(trastuzumab deruxtecan) and Dato-DXd (datopotamab deruxtecan) -- NOT a
B7-H3-specific toxicity. The profile must distinguish:

- **Class effects** (ILD, nausea, neutropenia from DXd payload): would
  occur with any DXd ADC regardless of target. Managed by dose, schedule,
  surveillance, corticosteroids.
- **Target-specific effects**: B7-H3 has low normal tissue expression,
  and the >20,000 antibody binding sites/cell threshold protects normal
  cells. No target-specific toxicity has emerged clinically.

For field 8 (safety), separate class-from-target toxicity. This distinction
matters for differentiation: a non-DXd payload (e.g., duocarmycin in
vobramitamab) may have different (better or worse) ILD risk, and the B7-H3
target itself has a favorable safety profile.

### 4. Broad expression eliminates biomarker barrier -- a pan-tumor strategy

B7-H3 is overexpressed in >=50% of samples across every solid tumor type
examined (1,342 tumor samples, PMID 28399408). In SCLC specifically, 95% of
cells show B7-H3 staining, and no clinically meaningful association between
expression level and response was observed in IDeate-Lung01 (PMID
41086386). This eliminates the need for companion diagnostics and enables
pan-tumor enrollment -- a major strategic advantage over biomarker-selected
trials.

However, broad expression creates a competitive positioning question: if
any B7-H3+ tumor is eligible, differentiation comes from payload, format, and
indication selection rather than from target exclusivity. The IDeate-PanTumor01
trial (34% ORR across 10 tumor types, PMID 41926962) validates the pan-tumor
approach.

**Generalizable**: For targets with near-universal expression in the
indication, biomarker selection is unnecessary and pan-tumor enrollment is
the strategic default. Note this in field 3 (disease evidence) and field 7
(biomarker assays).

### 5. Receptor orphan status -- checkpoint biology incompletely understood

B7-H3's receptor remains unidentified -- it is an "orphan" member of the B7
family (PMID 40946079). This has practical consequences for profiling:

- **Field 2 (pathway)**: the signaling pathway is incompletely characterized.
  Transcriptome analysis shows B7-H3 blockade downregulates exhaustion/anergy
  genes in CD8+ T cells (PMID 28685773), but the proximal signaling events are
  unknown.
- **Field 5 (epitope landscape)**: without knowing the receptor-binding
  interface, "neutralizing" vs "non-neutralizing" epitopes cannot be defined
  by receptor-competition. Instead, epitope functionality is defined by
  internalization (for ADCs) or by T cell functional assays (for checkpoint
  blockade).
- **Field 7 (assay systems)**: no receptor-binding assay exists; functional
  readouts are cell-based (T cell proliferation, cytokine production,
  cytotoxicity).
- **Field 11 (differentiation)**: an antibody that blocks the unidentified
  receptor interaction would be a true checkpoint blocker, but without
  knowing the receptor, rational epitope design is impossible.

**Generalizable**: For orphan-receptor targets, the profile must note the
receptor status explicitly and adapt epitope/function definitions accordingly.

### 6. Antibody binding site threshold as built-in safety mechanism

A key preclinical finding from the Seaman 2017 paper: >20,000 antibody
binding sites per cell are needed for cytotoxicity with PBD-ADCs (PMID
28399408). This threshold effect protects normal cells with low B7-H3
expression from ADC-mediated killing, providing a built-in safety mechanism.
This is a target-level property, not a payload property -- it arises from the
relationship between antigen density and ADC efficacy.

For field 8 (safety) and field 11 (differentiation), this threshold is a
quantifiable therapeutic index parameter. More potent payloads may lower the
threshold and erode the safety margin; less potent payloads may raise it and
reduce efficacy. The threshold should be documented as a design constraint.

### 7. Full-text retrieval rate: 40% (2/5)

Two of five papers had PMC XML OA access: Seaman 2017 (Cancer Cell, PMID
28399408) and Rudin 2026 (JCO, PMID 41086386). The JCO paper is notable -- JCO
is an ASCO journal that provides PMC OA for recent oncology trials, making
it one of the most reliable full-text sources for clinical trial data. The
other three (Cell Research, Trends Pharmacol Sci, Lancet Oncol) were
abstract-only but had rich structured abstracts (1,000-2,500 chars)
sufficient for profile grounding.

**Generalizable**: JCO (Journal of Clinical Oncology) is a reliable PMC OA
source for oncology clinical trial papers. Cancer Cell is also frequently OA.
Lancet Oncology and Cell Research abstracts are typically self-sufficient for
profile grounding. For oncology targets, prefer JCO and Cancer Cell papers
for full-text retrieval.
