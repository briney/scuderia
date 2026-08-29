# VEGF-A/Ang-2 bispecific (faricimab) — profile observations

**Session**: 2026-08-16
**Profile**: working-docs/hitlist-profiles/vegf-a-ang-2.md (~31K chars)
**Tier**: Approved (ophthalmology — wet AMD, DME)
**Papers**: 5 ingested (2 PMC XML OA, 3 abstract-only)
**PMIDs**: 35085502, 35085503, 35474059, 38847896, 37746113

## Full-text retrieval summary

| PMID | Paper | Journal | OA? | fulltext_source |
|------|-------|---------|-----|-----------------|
| 35085502 | Heier 2022 (TENAYA/LUCERNE) | Lancet | No | abstract |
| 35085503 | Wykoff 2022 (YOSEMITE/RHINE) | Lancet | No | abstract |
| 35474059 | Shirley 2022 (First Approval) | Drugs (Springer) | No | abstract |
| 38847896 | Agostini 2024 (Preclinical→Ph3) | Graefes Arch (Springer) | Yes (PMC11584429) | pmc-xml (38.7K chars) |
| 37746113 | Panos 2023 (Comprehensive review) | Drug Des Devel Ther (DovePress) | Yes (PMC10516184) | pmc-xml (41.9K chars) |

Retrieval rate: 40% (2/5 full text). The 3 abstract-only papers were all Elsevier/Lancet or Springer paywalled with no PMCID. The 2 OA papers were both comprehensive reviews that provided the bulk of the content for grounding fields 2 (biology), 3 (disease evidence), and 6 (failure modes/success factors).

## Key new patterns

### 1. Bispecific dual-ligand target profiling — two genes, two pathways, one profile

This is the first profile for a bispecific antibody targeting **two secreted ligands** (VEGF-A and Ang-2), not a single target or a T-cell engager (tumor antigen × CD3). Key structural differences from prior profiles:

- **Field 1 (target identity)**: Must list two gene symbols (VEGFA, ANGPT2), two UniProt IDs (P15692, O15123), two protein families. The "target" is the bispecific antibody's dual binding, not a single protein.
- **Field 2 (biological mechanism)**: Must describe two pathways (VEGF-A/VEGFR2 and Ang-2/Tie-2) and their interaction — Ang-2 sensitizes vessels to VEGF-A, and compensatory upregulation of one when the other is inhibited provides the dual-inhibition rationale.
- **Field 4 (antibody landscape)**: The bispecific antibody (faricimab) is the primary entry, but prior failed approaches (nesvacumab + aflibercept combination) and the monotherapy competitors (aflibercept, ranibizumab, bevacizumab) must all be listed.
- **Field 5 (epitope landscape)**: Two epitope sites (VEGF-A receptor-binding interface + Ang-2 Tie-2-binding interface), each potentially competing with different antibody sets.

For future bispecific dual-ligand profiles, field 1 should list both targets with their respective gene/UniProt/family, and fields 2-5 should address both targets throughout.

### 2. Compensatory pathway upregulation as dual-inhibition rationale

A generalizable disease-mechanism pattern: when inhibiting one pathway (VEGF-A), the complementary pathway (Ang-2) is compensatorily upregulated, explaining waning efficacy of monotherapy over time. This is the biological rationale for dual inhibition and should be explicitly stated in field 2 (biological mechanism) and field 6 (failure modes of monotherapy). This pattern may apply to other dual-pathway targets where compensatory upregulation limits monotherapy durability.

### 3. Failed combination vs successful bispecific — format as success factor

The nesvacumab (anti-Ang-2) + aflibercept (anti-VEGF-A) combination as **two separate molecules** failed in phase 2 (RUBY, ONYX) — anatomic benefits but no vision superiority. Faricimab as a **single bispecific molecule** succeeded in phase 3. This is a distinct format success pattern:

- Prior format patterns: ADC succeeded where naked Ab failed (CD30); BiTE succeeded where ADC failed (DLL3).
- New pattern: Bispecific (single molecule) succeeded where combination (two molecules) failed.

The proposed advantage of the bispecific format: co-formulated pharmacokinetics, single-injection convenience, and potentially superior tissue penetration of a single 150-kDa molecule vs two separate antibodies. For field 6, when a prior combination approach failed but a bispecific against the same targets succeeded, the format (single molecule vs two molecules) is the differentiating success factor.

### 4. Lancet jina reader — full landing page but body text paywalled

The jina reader proxy on the Lancet PDF URL (`thelancet.com/article/PII.../pdf`) returned 146K chars of the article landing page, including:
- Full structured abstract (Background/Methods/Findings/Interpretation/Funding)
- Figure captions with full descriptive text
- Complete reference list (27 references for Heier 2022)

But NOT the article body text (Introduction, Results, Discussion sections) — those are behind the "Get full text access" login wall.

For Lancet clinical trial papers, the structured abstract is self-sufficient for profile grounding — it contains trial design, patient numbers, primary endpoint results, safety data, and interpretation. Tag `fulltext_source: abstract` and note the jina retrieval in the ingest log. The figure captions add anatomic outcome context (CST reductions, dosing interval distributions).

This is consistent with prior Lancet observations (IL-5 profile, IL-17A/IL-17F profile) where the PIIS URL form or PDF URL form returned the landing page via jina. The Lancet structured abstract is consistently the richest abstract format for clinical trial papers.

### 5. Fc engineering for intravitreal use — a route-specific format design pattern

Faricimab's Fc is engineered with three modifications for the intravitreal route:
1. **FcγR binding site removed** → eliminates ADCC, ADCP, CDC (prevents inflammatory toxicity in the eye)
2. **Neonatal Fc receptor binding site deleted** → prevents IgG recycling, reduces systemic half-life (~7.5 days), reduces systemic exposure
3. **Faster systemic clearance** → minimizes systemic anti-VEGF effects (hypertension, proteinuria)

This is a route-specific Fc engineering pattern distinct from therapeutic antibodies designed for systemic IV/SC administration. For field 4 (antibody landscape) and field 6 (success factors), intravitreal antibodies require Fc modifications to minimize systemic exposure — the eye is a privileged immune site and systemic anti-VEGF activity is undesirable. This pattern applies to all intravitreal antibody formats (faricimab, brolucizumab's single-chain format, ranibizumab's Fab fragment).

### 6. CrossMAb technology — bispecific IgG assembly platform

Faricimab uses CrossMAb technology (Roche) for correct heavy-chain/light-chain pairing in the bispecific IgG1 format. This is the first profile documenting CrossMAb as the assembly platform. For field 4, the bispecific assembly technology (CrossMAb, DVD-Ig, FIT-Ig, common light chain, Knobs-into-Holes) is a key differentiator for bispecific antibodies and should be documented alongside the format and isotype.
