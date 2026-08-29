# CCR9 (C-C Chemokine Receptor Type 9) — Profile Observations

**Date**: 2026-08-16
**Tier**: Clinical-trial
**Area**: Immunology / Inflammation (IBD — gut-specific)
**Profile**: working-docs/hitlist-profiles/ccr9.md
**Papers**: 5 ingested (3/5 PMC XML OA — Front Cell Dev Biol, Clin Exp Gastroenterol, J Crohn's Colitis; 2/5 abstract-only — Taylor & Francis, Wiley)
**Full-text retrieval rate**: 60%
**Size**: ~29K chars profile, ~27K chars across 5 paper pages, 26 authors, 5 unique PMIDs cited

## Key new observations

### 1. Small-molecule Phase 3 failure with zero antibody development — the "tainted target" problem

CCR9 is the first clinical-trial tier profile where a small molecule (vercirnon/CCX282-B) reached Phase 3 and FAILED (SHIELD-1, terminated Aug 2013), yet NO antibody against CCR9 has ever entered clinical development. The target is clinically tested (small molecule) but the antibody space is completely virgin. This creates a unique competitive landscape (field 10): the target carries a "tainted" reputation from the Phase 3 failure, but the failure may have been molecule- and trial-design-specific rather than target-specific.

**Generalizable pattern for field 6 and field 10**: When a small molecule fails Phase 3 for a GPCR target, the failure modes must be dissected into target-level vs molecule-level vs trial-design-level causes. For CCR9: (a) wrong patient population (69% anti-TNF-experienced in SHIELD-1 vs 26% in the positive PROTECT-1), (b) wrong disease location (colonic vs small bowel — the target assumption was backwards), (c) small molecule PK limitations (250mg BID may have been suboptimal), (d) insufficient treatment duration (12 weeks may not deplete lamina propria effector cells). None of these are target-invalidating — an antibody with longer half-life, different dosing, and biomarker-selected patients could succeed where the small molecule failed. For field 11 (differentiation), the case must explicitly address WHY an antibody would succeed where the small molecule failed (format advantage, mechanism advantage, population advantage).

### 2. Disease-location mismatch — the target was tested in the wrong organ

The most critical CCR9 finding: CCR9+ T cell frequencies correlate with COLONIC disease activity, NOT small bowel disease activity (PMID 30137309). The entire SHIELD program was designed for Crohn's disease (primarily small bowel), based on the assumption that CCR9 mediates small bowel trafficking. The pre-specified subgroup analysis in SHIELD-1 showed efficacy specifically in colonic disease patients (CDAI response 25.4%/28.8% vercirnon vs 13% placebo). This is the opposite of the biological rationale used to justify the trial.

**Generalizable pattern for field 6 (failure modes)**: When preclinical models show target efficacy in one organ/disease subtype but the clinical trial enrolls a different organ/subtype, the failure may be a population/location mismatch, not target invalidation. Always check whether the clinical trial population matches the preclinical efficacy signal's organ/disease subtype. For chemokine receptor targets where expression patterns vary along the gut (CCL25 highest in duodenum, absent in normal colon but induced in colitis), the disease location within the GI tract is a critical stratification variable.

### 3. Dual role of CCR9 — effector trafficking AND Treg regulation

CCR9 is expressed on both pro-inflammatory effector T cells (Th1, Th17) AND regulatory T cells (FoxP3+ Tregs). CCR9 knockout mice are MORE susceptible to DSS colitis (not less), because CCR9+ Tregs protect against colonic inflammation. Blocking CCR9 may simultaneously inhibit effector trafficking AND disrupt Treg-mediated tolerance, potentially worsening outcomes. This is analogous to the CCR4 Treg depletion problem (mogamulizumab) but with the opposite therapeutic implication: for CCR4, Treg depletion is the GOAL (cancer immunotherapy); for CCR9, Treg depletion is an UNWANTED side effect (IBD therapy).

**Generalizable pattern for field 2 and field 6**: For chemokine receptors expressed on both effector and regulatory T cells, always characterize the dual role explicitly. A blocking antibody cannot distinguish between effector and regulatory CCR9+ cells — it blocks both. This is a fundamental limitation of receptor antagonism vs cell depletion. The leukapheresis approach (depleting CCR9+ cells from blood) showed efficacy in UC, suggesting that depletion (rather than blockade) may be the more effective mechanism — but depletion also removes Tregs. The key question for field 11: can an epitope be identified that is differentially expressed on effector vs regulatory CCR9+ cells?

### 4. Retinoic acid imprinting — the CCR9+ Treg connection

CCR9 imprinting is retinoic acid (vitamin A metabolite)-dependent, and in the presence of TGF-β, is associated with FoxP3 induction (PMID 30137309). CD4+ Tregs preferentially express CCR9 in the TNFΔARE model. This means the same signaling pathway (retinoic acid → CCR9 + α4β7) that drives effector T cell gut homing ALSO drives Treg gut homing. The CCR9/CCL25 axis is not simply pro-inflammatory — it is the gut mucosal immune regulation axis, with both effector and regulatory arms. For field 2, the biological mechanism section must capture this dual arm, not just the effector trafficking story.

### 5. PubMed search strategy for chemokine receptor targets — multiple query terms needed

The task specified two search queries: "CCR9 AND antibody AND review[pt]" (30 results) and "CCR9 AND IBD AND gut AND review[pt]" (10 results). The highest-value paper (PMID 30137309, Trivedi & Adams, the critical appraisal with SHIELD-1 subgroup analysis) appeared in the "CCR9 AND IBD AND gut AND review[pt]" query. Additional queries ("CCR9 AND CCL25 AND review[pt]" — 29 results; "CCR9 AND (inflammatory bowel disease OR Crohn disease) AND review[pt]" — 33 results) surfaced the tumor promotion review and the broad IBD review. The union of 4 queries yielded 45 unique PMIDs, from which 5 were selected.

**Pattern for chemokine receptor targets**: Use at least 4 search queries: (1) "[target] AND antibody AND review[pt]", (2) "[target] AND [disease] AND review[pt]", (3) "[target] AND [ligand] AND review[pt]", (4) "[target] AND ([disease synonyms]) AND review[pt]". The ligand query is particularly valuable for chemokine receptors because the ligand name (CCL25/TECK) may appear in titles more frequently than the receptor name.

### 6. 60% full-text retrieval — Frontiers and OUP/PMC are reliable; T&F and Wiley remain blocked

3/5 papers retrieved full text via PMC XML OA: Front Cell Dev Biol (PMID 34490243, 156 KB, 42K chars), Clin Exp Gastroenterol (PMID 25897254, 150 KB, 34K chars), J Crohn's Colitis (PMID 30137309, 176 KB, 42K chars). 2/5 were abstract-only: Expert Opin Ther Targets (PMID 19236152, Taylor & Francis, jina returned 27K chars of navigation chrome but no article body) and J Cell Physiol (PMID 32401349, Wiley, Cloudflare block, 514 bytes). The 60% rate is consistent with the immunology/inflammation journal mix pattern — Frontiers journals are reliably OA/PMC, OUP journals (J Crohn's Colitis) are often OA/PMC, while T&F and Wiley remain hard blocks.

**No new publisher block discoveries** — all blocks encountered (T&F Cloudflare, Wiley Cloudflare) are already documented in paper-ingest known-blocks table. The jina failure on T&F (returning 27K chars of navigation chrome rather than the ~489-byte block signature) is a variant worth noting: the response is large enough to pass the size check but contains zero article body text. This is a "navigation-chrome masquerade" — always validate jina output by checking for article body markers (abstract text, section headers) not just character count.
