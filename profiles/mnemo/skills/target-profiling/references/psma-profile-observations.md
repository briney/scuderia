# PSMA (FOLH1) Profile Observations

**Profile**: working-docs/hitlist-profiles/psma.md
**Tier**: Clinical-trial
**Therapeutic area**: Oncology (prostate cancer)
**Date**: 2026-08-16
**Papers ingested**: 5 (PMID 34161051, 36469000, 38300720, 32803984, 34167925)
**Profile size**: ~41K chars, 371 lines, 6 unique PMIDs cited
**Full-text retrieval**: 4/5 PMC OA (NEJM VISION, Clin Cancer Res FDA summary, Clin Cancer Res acapatamab, Mol Pharm 5D3-DM1), 1/5 abstract-only (Eur Urol Focus — Elsevier block)

## Key new patterns

### 1. Non-antibody approved modality: small-molecule radioligand as the foundational therapeutic

PSMA is the **first target profiled where the approved drug is a small-molecule
radioligand, not an antibody**. 177Lu-PSMA-617 (Pluvicto) is a urea-based PSMA
inhibitor conjugated to lutetium-177 via a DOTA chelator — it binds the
enzymatic active site (binuclear zinc center), not a surface epitope. This
creates a structural mismatch with the 11-field template's "antibody landscape"
(field 4): the approved drug does not have an isotype, an epitope, or a
conventional Fc. The profile handled this by listing the radioligand in field 4
with "Format: Radioligand (small-molecule) — not an antibody" and "Isotype:
N/A," then separately listing antibody-based approaches (HuJ591
radioimmunotherapy, 5D3-DM1 ADC, acapatamab bispecific) as distinct entries.

**Generalizable**: When the approved drug for a target is a non-antibody
modality (small molecule, radioligand, peptide-drug conjugate), include it in
field 4 with explicit "not an antibody" annotations, then list antibody
approaches separately. Field 5 (epitope landscape) must distinguish small-
molecule binding sites (active site, catalytic pocket) from antibody surface
epitopes — they are different "bins" that do not compete. Field 6 (failure/
success modes) should compare the modality formats head-to-head: for PSMA, the
small-molecule radioligand succeeded where antibody radioimmunotherapy (90Y/
177Lu-J591) had limited success — advantages include rapid clearance (less
marrow exposure), no immunogenicity, and simpler manufacturing.

### 2. Task-context antibody identity errors: verify before trusting

The delegation context for this profile stated "xaluritamig/AMG 160" as the
PSMA bispecific. PubMed verification revealed that xaluritamig is actually
AMG 509, a STEAP1×CD3 bispecific — NOT a PSMA-targeting molecule. AMG 160
(acapatamab) is the correct PSMA×CD3 bispecific. The names were conflated in
the task context, likely because both are Amgen bispecific T-cell engagers in
prostate cancer. The profile correctly used acapatamab (AMG 160) and did not
propagate the error.

**Generalizable**: Delegation contexts (hit list entries, task briefs,
context blocks) can contain wrong antibody-target associations — especially
for molecules from the same company in the same indication. The profiler must
verify every antibody identity claim (INN → target → company) via PubMed or
UniProt before incorporating it into the profile. Do not blindly copy
antibody names from task contexts into field 4. A 30-second PubMed search
("xaluritamig target" or "AMG 160 target") confirms or corrects the
association. This is particularly important for clinical-trial-tier targets
where the pipeline is fast-moving and INN assignments change.

### 3. Theranostic paradigm: companion diagnostic co-approval

PSMA is the **first target profiled with a theranostic companion diagnostic
co-approval**. 68Ga-PSMA-11 (Locametz) was approved simultaneously with
Pluvicto as the companion diagnostic for patient selection — PSMA-positive
status (uptake > liver parenchyma in ≥1 lesion) was a VISION trial enrollment
criterion. This creates a field 7 (assay systems) entry that is also a
regulatory requirement: the companion diagnostic IS the biomarker assay. For
field 6 (success factors), companion-diagnostic-guided patient selection was
the headline success factor — it ensured only patients whose tumors
expressed the target were treated, maximizing the therapeutic index.

**Generalizable**: When a target has an approved companion diagnostic, the
diagnostic-test-and-therapy pair is a single theranostic system. Profile
both in field 7 (biomarker assays) and note the regulatory linkage in field 6.
For field 11 (differentiation), the theranostic pair creates a barrier to
entry for new antibodies — a new PSMA-targeted antibody would need to work
with the existing 68Ga-PSMA-11 PET selection paradigm or propose a better
biomarker. This pattern applies to any target where imaging-based selection
is standard (HER2, EGFR T790M, and now PSMA).

### 4. Crossfire effect as a heterogeneity mitigation strategy

PSMA is the **first target profiled where the therapeutic modality has a
built-in bystander killing mechanism**. 177Lu beta radiation has a path
length of ~0.5-2 mm, enabling killing of PSMA-negative cells adjacent to
PSMA-positive cells (crossfire/bystander effect). This partially addresses
the challenge of PSMA expression heterogeneity — a key failure mode for all
PSMA-targeted modalities. ADCs and bispecifics lack this advantage: they kill
only the cells they bind.

**Generalizable**: When profiling a target with known expression
heterogeneity, analyze whether any modality has a bystander mechanism
(radiation crossfire, bystander effect of cleaved payload from ADCs). If yes,
this is a field 6 success factor AND a field 11 differentiation dimension —
modalities with bystander killing have an inherent advantage over those
without in heterogeneous-expression targets. For field 11, a differentiated
approach could be an ADC with a cleavable linker (releasing cell-permeable
payload that kills neighboring cells) to mimic the crossfire effect.

### 5. On-target off-tumor toxicity from normal tissue expression

PSMA is expressed on benign tissues (salivary glands, kidney proximal
tubules, lacrimal glands, small bowel) — and the radioligand's on-target
radiation to these tissues causes the characteristic toxicities (dry mouth
38.8%, renal toxicity dose-limiting with impaired clearance). This is a
target-inherent limitation, not a format limitation — it cannot be solved by
a better antibody or a better linker. For field 8 (safety), this defines
the safety ceiling for ALL PSMA-targeted modalities. For field 11, the only
mitigation is a prodrug/conditionally-activated approach that releases
payload only in the tumor microenvironment.

**Generalizable**: For any target with normal tissue expression, field 8
must enumerate the specific normal tissues and their physiological functions.
The toxicity is on-target (the target is real on those tissues) not
off-target. The therapeutic index is bounded by the ratio of tumor
expression to normal tissue expression, not by the antibody's selectivity.
This is distinct from off-target toxicity (cross-reactivity with a different
antigen) which can be engineered away.

### 6. High PMC OA rate for oncology clinical-trial papers

4/5 papers (80%) had accessible full text via PMC XML OA — the highest rate
observed for a clinical-trial tier profile. NEJM (VISION trial, PMID
34161051), Clin Cancer Res (FDA summary, PMID 36469000; acapatamab Phase 1,
PMID 38300720), and Mol Pharm (5D3-DM1, PMID 32803984) all had PMC OA copies.
Only the Eur Urol Focus review (Elsevier, PMID 34167925) was abstract-only.
This contrasts sharply with immunology/inflammation profiles (C5: 20%
full-text rate) and suggests oncology clinical-trial papers in NEJM, Clin
Cancer Res, and ACS journals have higher OA rates. When pre-identifying
landmark papers for oncology target profiling, these journals are
preferred over Elsevier/Wiley titles.
