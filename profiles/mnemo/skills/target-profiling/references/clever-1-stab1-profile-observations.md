# Clever-1 (Stabilin-1, STAB1) — Profile Observations

**Date**: 2026-08-16
**Tier**: Clinical-trial
**Area**: Immunology / inflammation (immuno-oncology — macrophage targeting)
**Profile**: working-docs/hitlist-profiles/clever-1.md
**Papers**: 5 ingested (2/5 PMC XML OA — Cell Rep Med, Mol Cancer Ther; 1/5 EPMC PDF — ScientificWorldJ; 2/5 abstract-only — Clin Cancer Res ×2, AACR paywalled)
**Full-text retrieval rate**: 60% (3/5)
**Size**: ~31K chars profile, 138 PMID citations, 14 unique PMIDs, 49 authors across 5 papers

## Key new observations

### 1. Macrophage-reprogramming target — the first "reprogram not deplete" mechanism profile

Clever-1 is the **first target profile where the therapeutic mechanism is macrophage reprogramming (M2→M1 conversion), NOT macrophage depletion**. This is mechanistically distinct from CSF-1R antibodies (which deplete macrophages) and from ADCC-mediated depletion targets (CD20, CCR8 Tregs). The key design consequence is **Fc-silencing as a functional requirement, not a preference**: bexmarilimab uses IgG4 with L248E mutation to eliminate FcγR and C1q binding, preventing ADCC/CDC. This avoids depleting Clever-1-expressing macrophages and endothelial cells — the therapeutic mechanism requires the cells to survive and be reprogrammed.

**Generalizable pattern for field 4 (antibody landscape) and field 6 (failure/success modes)**: For macrophage-reprogramming targets, the isotype choice (IgG4 Fc-silenced) is mechanistically motivated — an IgG1 (ADCC-competent) format would be counterproductive because it would deplete the very cells being reprogrammed. This is the opposite of Treg-depletion targets (CCR8, anti-CTLA-4) where IgG1 with enhanced FcγRIIIa is the baseline requirement. Always state whether the therapeutic mechanism is depletion or reprogramming, and match the isotype rationale accordingly. The skill already documents this for soluble targets (IgG4 to avoid Fc-mediated depletion of target-coated cells) — macrophage-reprogramming targets are a second class where Fc-silencing is a functional requirement.

### 2. Bell-shaped dose-response for immunostimulatory antibodies

Bexmarilimab's nonclinical characterization (PMID 35500016) revealed a **bell-shaped dose-response curve for TNFα secretion** — moderate doses were more effective than very high doses. This is a distinct PK/PD pattern for immunostimulatory antibodies: at high concentrations, negative feedback loops (e.g., LPS tolerance, IFNγ suppression at high doses) can suppress the desired immune activation. This has direct clinical dosing implications — the MATINS trial's receptor occupancy data (70% engagement for 8-15 days at 3-10 mg/kg) suggests the optimal biological dose may be lower than the maximum tolerated dose.

**Generalizable pattern for field 6 (failure/success modes) and field 7 (assay systems)**: For immunostimulatory antibodies (anti-Clever-1, anti-OX40, anti-4-1BB, anti-GITR, anti-CD40), dose-escalation should include functional readouts (cytokine secretion, immune activation markers) at multiple dose levels, not just safety. The MTD may exceed the optimal biological dose (OBD). This is the inverse of conventional antibody dosing where "more is better" — for immunostimulatory antibodies, the dose-response curve has a peak, and exceeding it may reduce efficacy. Include this in field 6 as a dosing-specific success factor.

### 3. Biomarker-guided patient selection from Phase I/2 data

The MATINS trial (PMID 38056464) identified two predictive biomarkers from early-phase data: (1) high pre-treatment intratumoral Clever-1 positivity (IHC), and (2) low baseline systemic cytokine levels (particularly IFNγ). Disease control (DC) rates of 25-40% were concentrated in patients with high Clever-1 and low cytokines. Spatial transcriptomics confirmed that bexmarilimab-induced macrophage activation (IFN signaling, M1-like gene expression) occurred selectively in DC patients.

**Generalizable pattern for field 7 (assay systems) and field 6 (success factors)**: For clinical-trial-tier targets with Phase I/2 data, the biomarker strategy can be defined from early-phase correlatives before Phase 3. This is particularly important for immunostimulatory antibodies where response may be limited to a biomarker-defined subset. The pattern of "high target expression + low baseline immune activation = responder" is intuitive for reprogramming targets (the cells must be present and must be suppressible). Include IHC-based target expression as a companion diagnostic candidate in field 7, and note the biomarker-response correlation in field 6 as a success factor.

### 4. Scavenger receptor target class — blocking clearance function, not signaling

Clever-1 is a **multifunctional scavenger receptor** (280 kDa type I transmembrane, EGF-like + 7 fasciclin + 1 X-link domains). The therapeutic mechanism is blocking the receptor's scavenger function (endocytosis of acLDL, SPARC, apoptotic cells via phosphatidylserine) — not blocking a signaling pathway. This is a distinct target class from: (a) cell-surface signaling receptors (HER2, CD20, PD-1), (b) soluble ligands (TNF, IL-17, C5a), (c) GPCRs (C5aR1, CCR8), and (d) T cell engagers (CD3 bispecifics). The scavenger receptor mechanism means: blocking clearance of "unwanted-self" components leaves proimmunogenic material in the extracellular space, which promotes immune activation.

**Generalizable pattern for field 2 (biological mechanism)**: For scavenger receptor targets, the "effect of blockade" is indirect — the antibody does not directly activate or inhibit a signaling cascade but rather prevents clearance of immunogenic material. The mechanism description should include: (1) what the receptor clears (ligands), (2) what happens when clearance is blocked (accumulation of immunogenic material), (3) how this translates to therapeutic effect (immune activation via antigen persistence). This is distinct from direct receptor antagonism (blocking ligand-receptor binding) or depletion (killing target cells).

### 5. AACR publisher block — Clin Cancer Res papers consistently paywalled

Both AACR/Clinical Cancer Research papers (PMID 25320356 Karikoski 2014, PMID 30755440 Viitala 2019) were paywalled with no PMC copy, jina reader blocked by Cloudflare/CAPTCHA, and no Wayback Machine snapshot. This confirms AACR as a **hard publisher block** for full-text retrieval, alongside ASH/Blood, Elsevier, Wiley, and Karger. The AACR block is notable because Clinical Cancer Research publishes high-impact preclinical immunotherapy papers — the foundational and mechanistic papers for many immuno-oncology targets will be in this journal.

**Generalizable pattern for paper selection**: When pre-identifying landmark papers for delegation, prefer papers from OA-friendly journals (Cell Rep Med, Mol Cancer Ther — both OA-accessible) over AACR journals for full-text retrieval. However, for immuno-oncology targets, the foundational preclinical papers are often in Clin Cancer Res — accept abstract-only as the expected outcome for these, and rely on the structured AACR abstract (which includes Purpose/Experimental Design/Results/Conclusions) for profile grounding. The AACR abstract format is well-structured and sufficient for fields 2, 3, and 6 at the level-2 rigor standard.

### 6. EPMC PDF render as reliable fallback for older OA papers

The Kzhyshkowska 2010 review (PMID 20953554, ScientificWorldJournal, PMC5763786) had `inPMC: Y` but PMC XML returned no `<body>` (metadata-only or blocked). The fetch_fulltext.py script automatically fell back to EPMC PDF render (Branch 1b), successfully extracting 63K chars via pymupdf. This confirms the Branch 1b path as reliable for older OA papers where PMC XML is front-matter-only. The EPMC PDF path has now been confirmed across multiple profiles (CD20/Alduaij 2011, C5aR1/JASN papers, and now Clever-1/Kzhyshkowska 2010).

### 7. PubMed search strategy — review queries + drug-name queries for clinical-trial targets

The task specified two review-focused queries ("Clever-1 AND antibody AND review" → 2 results; "STAB1 AND stabilin AND macrophage AND review" → 8 results). The most valuable papers were found through supplementary queries: "bexmarilimab" (13 results, surfaced all clinical trial papers) and "Clever-1 AND cancer AND macrophage" (20 results, surfaced foundational and mechanistic papers). The review queries alone (10 total results) would have missed the key clinical trial papers (MATINS, nonclinical characterization) and the mechanistic CD8+ T-cell paper.

**Generalizable pattern for clinical-trial-tier targets**: Always add drug-name queries ("bexmarilimab", "FP-1305") alongside review/biology queries. The drug name is the most specific search term and surfaces all clinical publications, manufacturing/characterization papers, and combination studies. For targets with a named drug in trials, the drug-name query often yields the highest-value papers for fields 4 (antibody landscape), 6 (failure/success modes), and 8 (safety). This complements the existing observation from the IL-17A profile that "delegation with search instructions (not pre-identified PMIDs) works" — providing both review queries AND drug-name queries gives the subagent the best coverage.

### 8. Combination synergy with checkpoint inhibitors — preclinical to clinical translation

The Viitala 2019 paper (PMID 30755440) demonstrated that anti-Clever-1 + anti-PD-1 provides **synergistic benefit in aggressive, nonresponsive tumors** — the key translational finding. This synergy is mechanistically rational: anti-Clever-1 reprograms the suppressive TME (macrophage activation, CD8+ T-cell priming), while anti-PD-1 releases T-cell checkpoints. The combination addresses complementary mechanisms of immune evasion. Multiple 2025 papers (PMID 41339106, PMID 40404204) confirmed this in gastric cancer models.

**Generalizable pattern for field 6 (success factors) and field 11 (differentiation)**: For macrophage-reprogramming targets, the combination-with-checkpoint-inhibitor rationale is the primary clinical development strategy. The preclinical synergy data (comparable monotherapy efficacy to PD-1 blockade + synergy in resistant models) is the strongest evidence for clinical combination trials. For field 11, a bispecific Clever-1 × PD-1 antibody is a natural format differentiation that combines both mechanisms in a single molecule. This pattern applies to any macrophage/myeloid-targeting immunotherapy where the mechanism is complementary to T-cell checkpoint blockade.
