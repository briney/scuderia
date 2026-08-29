# CD27 (TNFRSF7) Profile Observations

**Profile**: working-docs/hitlist-profiles/cd27.md
**Tier**: Clinical-trial
**Therapeutic area**: Oncology (T cell co-stimulation)
**Date**: 2026-08-16
**Papers ingested**: 5 (PMID 32380537, 35940825, 24605266, 35288635, 40920567)
**Profile size**: ~37K chars, 277 lines, 5 unique PMIDs cited (plus PMID 34991665 from CD70 profile cross-ref)
**Full-text retrieval**: 5/5 PMC OA (100%) — all papers had PMC IDs with accessible full text

## Paper retrieval details

| PMID | Journal | Full text? | Method |
|------|---------|-----------|--------|
| 32380537 | Blood Adv (2020) | Yes (49K chars) | PMC HTML OA (PMC7218437) |
| 35940825 | J Immunother Cancer (2022) | Yes (67K chars HTML + 27K chars EPMC XML) | PMC HTML OA + Europe PMC XML (PMC9364417) |
| 24605266 | Oncoimmunology (2014) | Yes (14K chars HTML + 5K chars EPMC XML) | PMC HTML OA + Europe PMC XML (PMC3937191) |
| 35288635 | Commun Biol (2022) | Yes (88K chars HTML + 15K chars EPMC XML) | PMC HTML OA + Europe PMC XML (PMC8921514) |
| 40920567 | Clin Cancer Res (2025) | Yes (95K chars) | PMC HTML OA (PMC7618221) |

All 5 papers had PMC OA full text available. Europe PMC XML was also available for 3/5 papers (providing better-structured text than HTML scraping). No paywalled papers, no publisher blocks encountered.

## Key new patterns

### 1. First TNFRSF co-stimulatory AGONIST target profiled — agonist vs antagonist antibody design

CD27 is the first target profiled where the clinical antibody (varlilumab) is an **agonist** that stimulates the target, not an antagonist that blocks it. All prior profiles featured blocking/depleting antibodies. For TNFRSF co-stimulatory receptors (CD27, OX40, 4-1BB, GITR, CD40, ICOS), the antibody must **activate** the receptor, which requires fundamentally different design principles:

- **FcR cross-linking is ESSENTIAL**: The agonist signal requires Fc receptor-mediated cross-linking on APCs. Varlilumab's IgG1 FcR-binding-abrogated mutant completely lost agonist and antitumor activity (PMID 24605266). This is the opposite of antagonist antibodies where Fc effector function (ADCC/CDC) is the primary mechanism, not receptor clustering.
- **Epitope determines agonist potency**: Membrane-distal, externally-facing epitopes produce strong agonism; membrane-proximal, internally-facing epitopes produce weak agonism (PMID 35288635). This is the OPPOSITE of OX40, where membrane-proximal epitopes are superior. For TNFRSF agonist targets, epitope-agonism relationships must be empirically determined per target — there is no universal rule.
- **Fc isotype is critical**: IgG2 or FcγRIIb-enhanced IgG1 (V11/SE/LF mutations) > standard IgG1 for receptor clustering and agonism. Activatory FcγR engagement (m2a in mice) is detrimental — depletes CD8+ T cells (PMID 35288635). The wrong isotype converts an agonist into a depleting antibody.
- **Varlilumab may be suboptimal**: The clinical reagent uses IgG1 at the CRD2 (CD70-binding) epitope. Heckel et al. showed this delivers suboptimal agonism compared to IgG2 at membrane-distal epitopes (hCD27.15). The next-generation opportunity is clear and preclinically validated.

Generalizable: for any TNFRSF co-stimulatory agonist target, fields 4, 5, 6, and 11 must address: (a) FcR cross-linking requirement, (b) epitope-agonism relationship (membrane-distal vs proximal), (c) Fc isotype optimization (IgG2/FcγRIIb-enhanced > IgG1), (d) whether the clinical reagent is at the optimal epitope/isotype.

### 2. Bidirectional target-ligand axis: CD27 (receptor) and CD70 (ligand) both profiled

CD27 is the first target where both the receptor (CD27) and its ligand (CD70) have been independently profiled in the hit list. The CD70 profile (working-docs/hitlist-profiles/cd70.md) covers the antagonist/blocking side (cusatuzumab, SEA-CD70, CAR-T) while the CD27 profile covers the agonist side (varlilumab). The axis has fundamentally opposing roles:

- **Co-stimulatory (physiological)**: Transient CD70 on activated APCs → CD27 on T cells → NF-κB/JNK/PI3K → T cell proliferation, survival, effector function. Agonistic anti-CD27 exploits this.
- **Suppressive (pathological/tumor)**: Chronic CD70 on tumor cells → T cell exhaustion, Treg expansion, NK depletion, T cell apoptosis via Siva. Blocking anti-CD70 (cusatuzumab) eliminates this.

This means the same molecular axis can be targeted from two directions with opposite antibody mechanisms. Biomarker stratification determines which approach is appropriate: in tumors with chronic CD70 expression driving immunosuppression, block CD70; in tumors with intact T cell infiltration needing co-stimulation, agonize CD27. The profile should cross-reference the ligand/receptor partner profile explicitly.

Generalizable: for any receptor-ligand pair where both sides are therapeutic targets, cross-reference the partner profile in field 2, note the opposing mechanisms, and identify the biomarker framework for choosing agonist vs antagonist approach.

### 3. CD27+ B cell "sink" as a novel negative predictive biomarker

The RiVa trial (PMID 40920567) revealed that CD27-expressing B cells in B-cell malignancies correlated with NON-response to varlilumab + rituximab. The hypothesis: CD27+ B cells act as an agonist "sink," diverting varlilumab from its intended target (T/NK cells) and potentially providing unintended agonist signals to malignant B cells. This is a novel biomarker pattern — the target expressed on the "wrong" cell type undermines the therapeutic mechanism.

Generalizable: for agonist antibodies targeting receptors expressed on multiple cell types, field 3 (disease evidence) and field 6 (failure modes) must consider whether target expression on non-effector cells acts as a sink. The positive biomarkers (CD27+ T/NK cells, γδ T cells, inflamed TME) and negative biomarker (CD27+ B cells) were only discovered through single-cell analysis of on-treatment biopsies — biomarker discovery requires intratumoral profiling, not just peripheral blood.

### 4. γδ T cells as unexpected effector for CD27 agonism

Single-cell analysis in the RiVa trial showed activated γδ T cell signatures were associated with response to CD27 agonism (PMID 40920567). γδ T cells are an unconventional T cell subset that bridges innate and adaptive immunity. This was not predicted from the preclinical models (which focused on CD4+/CD8+ αβ T cells). CD27 is expressed on γδ T cells, and agonism may activate this population in the tumor microenvironment.

Generalizable: for co-stimulatory agonist targets, field 2 (cell types expressing) and field 6 (success factors) should consider unconventional effector populations (γδ T cells, NK cells, NKT cells) — not just conventional CD4+/CD8+ T cells. Single-cell RNA-seq of on-treatment biopsies is the discovery tool for unexpected effector populations.

### 5. Pharmacodynamic activity ≠ clinical efficacy — the TME modulation gap

Varlilumab + nivolumab induced measurable TME changes (increased CD8+ T cells, PD-L1 upregulation) in the Sanborn et al. trial (PMID 35940825), but this did NOT translate to improved ORR beyond nivolumab monotherapy. The RiVa trial showed the same pattern: varlilumab enhanced CD4+ T cell infiltration and immune signatures, but ORR was only 15.4% (PMID 40920567). This "TME modulation gap" — pharmacodynamic activity without clinical efficacy — is a recurring challenge for co-stimulatory agonists.

Generalizable: for co-stimulatory agonist targets, field 6 (failure modes) must distinguish between pharmacodynamic failure (no TME changes — target not engaged) and efficacy failure (TME changes present but no clinical response — insufficient biological effect). The TME changes are necessary but not sufficient. The gap may reflect: (a) insufficient agonist potency (wrong epitope/Fc), (b) wrong tumor context (cold tumors, no immune substrate), (c) redundant pathways compensating, (d) need for combination with additional immune modulation.

### 6. Hodgkin lymphoma as the ideal context for CD27 agonism — pre-existing immune infiltration

The single durable CR in the Phase 1 varlilumab trial was in Hodgkin lymphoma (PMID 32380537). Hodgkin lymphoma is characterized by a robust inflammatory T cell infiltrate surrounding Reed-Sternberg cells — a "hot" tumor with abundant CD27+ T cells. The RiVa trial later confirmed that pre-existing immune infiltration (inflamed tumor signatures) predicts response (PMID 40920567). This suggests that CD27 agonism works best in tumors that already have the immune substrate — it amplifies existing immunity rather than creating it de novo.

Generalizable: for co-stimulatory agonist targets, field 6 (success factors) should identify tumor types with naturally robust T cell infiltration as the most favorable context. "Hot" tumors with pre-existing immune priming are the ideal population; "cold" tumors are unlikely to respond without additional priming (vaccine, oncolytic virus, radiation).

### 7. Bystander myeloid activation as a combinatorial mechanism

CD27 agonism on T cells promotes activation of bystander myeloid cells via cytokine/chemokine release (CCL3, CCL4, CCL5, IFNγ), leading to increased ADCP of tumor-targeting antibody-coated cells (PMID 35288635). This was clinically validated in the RiVa trial: varlilumab + rituximab showed that CD27 agonism enhances macrophage-mediated killing of rituximab-coated tumor cells (PMID 40920567). This is a "bystander" mechanism — the CD27 agonist doesn't directly kill tumor cells but enhances the efficacy of a separate tumor-targeting antibody.

Generalizable: for co-stimulatory agonist targets, field 2 (biological mechanism) and field 11 (differentiation) should explore the bystander mechanism — CD27 agonism as an enhancer of other antibody modalities (anti-CD20, anti-HER2, anti-EGFR). The combination strategy (CD27 agonist + tumor-targeting antibody) leverages two mechanisms: direct T cell co-stimulation + indirect myeloid-mediated ADCP enhancement. This is a distinct combination rationale from CD27 agonist + checkpoint inhibitor.

### 8. 100% PMC OA retrieval rate — oncology co-stimulatory agonist papers

All 5 key papers had PMC OA full text (100% retrieval rate). The paper set spanned Blood Advances, J Immunother Cancer, Oncoimmunology, Commun Biol, and Clin Cancer Res — all PMC OA. This is the highest retrieval rate for any profile in the corpus (tied with IL-17A at 100%). Oncology immunotherapy papers, particularly from immunology-focused journals, have high OA rates. When pre-identifying landmark papers for oncology co-stimulatory target profiling, these journals are reliable full-text sources.

## TNFRSF co-stimulatory agonist family context

CD27 is one of several TNFRSF co-stimulatory receptors being targeted with agonist antibodies in oncology:

| Receptor | Ligand | Clinical antibody | Isotype | Phase | Single-agent ORR | Key issue |
|---------|--------|------------------|---------|-------|-------------------|-----------|
| CD27 (TNFRSF7) | CD70 | Varlilumab | IgG1 | Phase 1/2 | Low (1 CR in Hodgkin) | Suboptimal epitope/Fc; needs inflamed TME |
| OX40 (TNFRSF4) | OX40L | Multiple (PF-04518600, BMS-986178, etc.) | IgG1/IgG2 | Phase 1/2 | 0-6% | No biomarker selection; Fc format unresolved |
| 4-1BB (TNFRSF9) | 4-1BBL | Urelumab, Utomilumab | IgG1/IgG2 | Phase 1/2 | Low | Hepatotoxicity (urelumab); insufficient agonism (utomilumab) |
| GITR (TNFRSF18) | GITRL | BMS-986156, TRX518 | IgG1/IgG2 | Phase 1 | Low | Treg depletion vs co-stimulation balance |
| CD40 (TNFRSF5) | CD40L | SEA-CD40, APX005M | IgG1/IgG2 | Phase 1/2 | Low-moderate | Cytokine release syndrome; Fc format critical |

Common challenges across TNFRSF agonist antibodies: (1) low single-agent ORR, (2) Fc isotype/epitope optimization unresolved, (3) need for combination with checkpoint inhibitors, (4) narrow therapeutic index (4-1BB hepatotoxicity vs CD27's favorable safety), (5) TME context dependence (need inflamed tumors). CD27's favorable safety profile (no DLTs, no MTD, no hepatotoxicity) is a relative advantage over 4-1BB and CD40 agonists.
