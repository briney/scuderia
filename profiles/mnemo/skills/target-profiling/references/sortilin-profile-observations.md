# Sortilin (SORT1) — profile observations

**Date**: 2026-08-16
**Tier**: clinical-trial
**Therapeutic area**: neuroscience (FTD, AD, ALS)
**Profile**: `working-docs/hitlist-profiles/sortilin.md`
**Size**: ~50K chars, 204 PMID citations, 48 unique PMIDs from PubMed search
**Papers ingested**: 5/5 full text via PMC XML (100% retrieval rate)

## Ingested papers

| PMID | First author | Year | Journal | PMCID | Provenance | Chars |
|------|-------------|------|---------|-------|------------|-------|
| 38356474 | Ward | 2024 | Alzheimer's Dementia | PMC10865485 | pmc-xml | 25K |
| 37322482 | Kurnellas | 2023 | J Transl Med | PMC10268535 | pmc-xml | 55K |
| 21092856 | Hu | 2010 | Neuron | PMC2990962 | pmc-xml | 27K |
| 40713730 | Budda | 2025 | Alzheimer's Res Ther | PMC12291526 | pmc-xml | 61K |
| 39185427 | Ek | 2024 | Front Immunol | PMC11342335 | pmc-xml | 40K |

## PubMed search strategy

Five topic-area queries were used (esearch, retmax=15, sort=relevance):
1. `sortilin[Title/Abstract] AND antibody[Title/Abstract]` — 15 results
2. `latozinemab[Title/Abstract] OR (SORT1[Title/Abstract] AND AL001[Title/Abstract])` — 4 results
3. `sortilin[Title/Abstract] AND (frontotemporal dementia[Title/Abstract] OR frontotemporal lobar degeneration[Title/Abstract])` — 15 results
4. `sortilin[Title/Abstract] AND progranulin[Title/Abstract]` — 15 results
5. `(SORT1[Title/Abstract] OR sortilin[Title/Abstract]) AND neurodegeneration[Title/Abstract]` — 15 results

48 unique PMIDs after deduplication. All esummary metadata fetched in a single batch call.

## Paper selection rationale

From 48 unique PMIDs, 5 were selected as landmark papers spanning all required topics:
- **Latozinemab Phase 1 FTD** (PMID 38356474) — clinical trial data in symptomatic FTD-GRN patients
- **Latozinemab mechanism/preclinical** (PMID 37322482) — comprehensive drug discovery to first-in-human, includes in vitro, mouse, NHP, and clinical data
- **Sortilin-progranulin endocytosis** (PMID 21092856) — the landmark Hu et al. 2010 Neuron paper that identified sortilin as the PGRN clearance receptor
- **AL101 development for AD** (PMID 40713730) — GSK's anti-SORT1 antibody for Alzheimer's disease (Phase 1 FIH + preclinical)
- **Anti-sortilin affibody** (PMID 39185427) — alternative scaffold approach (affibody-peptide fusion)

## Key new patterns observed

### 1. Inverse-target profiling

Sortilin is the clearance receptor for progranulin (PGRN). The disease (FTD-GRN) is caused by PGRN haploinsufficiency, not by sortilin overexpression. The therapeutic antibody strategy is to **block sortilin** (the clearance receptor) in order to **increase PGRN** (the deficient protein). This inverts the standard antibody target profile:

- **Field 2 (biological mechanism)**: "Effect of blockade" describes a *beneficial* outcome (PGRN elevation), not an on-target pharmacology to be managed. The blockade prevents degradation, not signaling.
- **Field 6 (failure modes/success factors)**: Success factors include "dual mechanism (competitive blockade + receptor down-regulation)" — the antibody both blocks PGRN binding and depletes cell surface sortilin. This is a mechanism-of-action success factor, not a standard "right epitope" consideration.
- **Field 8 (safety)**: Safety is framed around PGRN over-supplementation risks (metabolic: dyslipidemia, visceral obesity; oncologic: pro-tumorigenic), not sortilin loss. Sortilin deficiency is actually protective (Sort1-/- mice protected from age-dependent neurodegeneration).
- **Field 11 (differentiation)**: The narrow therapeutic window is between insufficient PGRN restoration (no efficacy) and over-supplementation (metabolic/oncologic risk).

This pattern generalizes to any target where the antibody blocks a clearance/degradation pathway to elevate a deficient protein. The progranulin.md profile (same session) covers the same axis from the PGRN (disease protein) side.

### 2. Alternative scaffold in the antibody landscape

The sortilin profile is the **first** to include a non-IgG alternative scaffold in field 4 (antibody landscape): the affibody-peptide fusion ABD-A3-PGRNC15* (Ek et al., PMID 39185427).

Key characteristics:
- Format: 58-aa affibody (~6.5 kDa) + albumin-binding domain (ABD) for half-life extension + PGRN C-terminal peptide (PGRNC15*, 15 aa with A588G mutation)
- Biparatopic binding: the affibody A3 moiety binds one epitope on sortilin, while the fused PGRN peptide occupies the natural ligand-binding site (beta-propeller inner tunnel)
- Affinity: Kd 185 pM (>380-fold improvement over affibody alone, via avidity from biparatopic binding)
- Activity: EC50 1.30 +/- 0.30 nM in PGRN clearance assay, comparable to latozinemab biosimilar (EC50 0.68 +/- 0.20 nM, not significant)
- Advantages: bacterial production (lower cost), small size (higher binding site density, smaller injection volumes), no Fc (no effector function risk, no Fc-mediated ADA)

For future profiles: include alternative scaffolds (affibody, nanobody, DARPin, receptor-Fc fusion) as distinct entries in field 4 when they target the same epitope class with a different format. The HBV profile's CR2-Fc fusion (receptor-body) is another example of this pattern.

### 3. 100% full-text retrieval for neuroscience OA journals

All 5 papers were retrieved via PMC XML with no paywall issues. Journal mix:
- J Transl Med (BioMed Central/Springer) — OA, PMC XML
- Front Immunol (Frontiers) — OA, PMC XML
- Alzheimer's Res Ther (BioMed Central) — OA, PMC XML
- Alzheimer's Dementia (Wiley) — inPMC=Y, PMC XML available despite non-OA
- Neuron (Cell Press/Elsevier) — inPMC=Y (PMC2990962), PMC XML available

This 100% retrieval rate contrasts with:
- C5 profile: 20% (1/5) — NEJM, J Immunol, Blood paywalled
- HBV profile: 40% (2/5) — J Hepatol, Antiviral Res (Elsevier) paywalled with CAPTCHA
- ApoC-III profile: 33% (2/6) — NEJM, JAMA Cardiol, ATVB paywalled

**Implication for delegation**: Neuroscience targets with papers in OA-friendly journals (BioMed Central, Frontiers, Springer) are very low-risk for the paywall timeout problem. When pre-identifying landmark papers for delegated profiling, prefer OA journals. Cell Press/Neuron papers with PMC IDs are also retrievable via PMC XML even when not OA.

### 4. Cross-species surrogate antibody pattern

Latozinemab (AL001) does not cross-react with rodent sortilin. A mouse cross-reactive surrogate (S15JG) was used for all mouse studies. Key points:
- S15JG binds the beta-propeller region (same as PGRN binding site) but at a slightly different epitope from latozinemab
- S15JG was used for the Grn+/- mouse efficacy studies (social dominance tube test, brain ISF PGRN via microdialysis)
- Latozinemab was tested in cynomolgus monkeys (which it does cross-react with) for PK/PD
- AL101 was tested in both rats and cynomolgus monkeys

The surrogate's different epitope is a caveat: the mouse efficacy data (behavioral rescue, ISF PGRN elevation) supports the target biology but does not directly validate the clinical antibody's epitope. For field 4, document the surrogate as a separate entry. For field 7, note the surrogate as the tool used for specific in vivo models.

This is the same pattern as in the progranulin.md profile — both profiles cover the same latozinemab/S15JG data.

### 5. Trans signaling paradigm

Sortilin and PGRN are expressed on different cell types in the CNS:
- **PGRN**: secreted by activated microglia (not neurons, not astrocytes — confirmed by sciatic nerve injury model)
- **Sortilin**: expressed by neurons (cortical neurons, spinal motoneurons), NOT by microglia

The endocytosis occurs in trans: microglial PGRN to neuronal sortilin to lysosomal delivery. This was demonstrated by:
- Immunohistochemistry: Sortilin on motoneurons, PGRN in surrounding activated microglia after axotomy
- C13-NJ microglial cell line secretes PGRN but expresses little sortilin
- PGRN and sortilin show little colocalization in cortical neuronal soma (different cell compartments)

For field 2, document the cell-type separation and trans signaling. For field 11, the cell-type-specific expression is a targeting advantage — the antibody needs to engage sortilin on neurons only, and microglia (which don't express sortilin) are not directly affected by anti-sortilin therapy.

### 6. Sibling profile cross-referencing

The progranulin.md profile (progranulin, the PGRN disease protein) was created in the same session batch. It already contained:
- The same latozinemab and AL101 clinical trial data
- The same Sort1-/- mouse data (2.5-5x PGRN elevation)
- The same Furuichi et al. epitope bin system (7 bins)
- The same Fc-silencing mutation details (L234A/L235A/P331S)

When profiling a target that is the binding partner or clearance receptor of an already-profiled target, **read the sibling profile first** to:
1. Avoid redundant PubMed searches and paper ingestion
2. Ensure consistent cross-referencing (same PMID citations, same clinical trial NCT IDs)
3. Identify the complementary framing (disease protein vs. clearance receptor)
4. Borrow structural and epitope information that applies to both targets

The two profiles are complementary:
- progranulin.md: disease-causing protein, therapeutic goal is to elevate it
- sortilin.md: clearance receptor, antibody target, therapeutic goal is to block it

## Related profiles

- `working-docs/hitlist-profiles/progranulin.md` — progranulin (PGRN), the disease protein; sortilin is its clearance receptor. Created in the same session batch. Contains overlapping clinical data (latozinemab, AL101, Sort1-/- mice) from the PGRN perspective.
