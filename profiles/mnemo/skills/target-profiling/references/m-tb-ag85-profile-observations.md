# M. tuberculosis Ag85 profile observations (2026-08-17)

Preclinical-tier infectious disease target. Antigen 85 complex (Ag85A/B/C)
— three secreted mycolyltransferases of *Mycobacterium tuberculosis*,
essential for cell wall biosynthesis (TDM/cord factor production, mycolic
acid transfer to arabinogalactan). ~30–32 kDa per monomer, α/β-hydrolase
fold, catalytic triad Ser124-Glu228-His260. Secreted AND cell-envelope-
associated; circulates in serum complexed to fibronectin and IgG. Two
Ag85-based vaccines failed in Phase 2b (MVA85A, H56:IC31) — both T-cell
vaccines. The passive antibody therapeutic approach is entirely untested.
Built via direct PubMed E-utilities (two-step urllib form). 6 PubMed
queries (2 primary [tiab] + 4 targeted for structure, vaccine trials,
mycolyltransferase, nanobody), 29+ candidate PMIDs screened, 14 landmark
abstracts fetched via efetch XML parsing with ElementTree. One HTTP 429
encountered — waited 16s per skill guidance, resumed successfully.
Abstract-only ingestion. UniProt P0A4S5/P0A4S4/P0A4S7 grounded field 1.
Crystal structures from PDB (1D0Z, 1M0Q) grounded field 9. 14 unique
PMIDs cited, ~49K chars,
working-docs/hitlist-profiles/m-tb-ag85.md.

## Key new patterns

### 1. Secreted enzyme target — "secreted but partially inaccessible" accessibility pattern

Ag85 is both secreted (into the extracellular milieu, circulates in
serum) AND cell-envelope-associated (embedded in the mycobacterial cell
wall). The 2026 review (PMID 42075259) explicitly flags "antigen
accessibility under physiological conditions" as a key challenge — Ag85
is accessible when secreted but less accessible when cell-wall-associated
or intracellular within infected macrophages. This is a NEW accessibility
pattern distinct from:
- **Secreted toxins** (PEA, anthrax PA): fully accessible in
  extracellular space
- **Surface glycolipids** (LAM): broadly surface-exposed and shed
- **Viral glycoproteins** (EBOV GP): surface-exposed on virions
- **Bacterial structural proteins** (PcrV): surface-exposed, contact-dependent

Ag85 is "secreted but partially inaccessible" — the secreted fraction is
antibody-accessible, but the cell-wall-associated and intracellular
fractions may not be. For field 2, explicitly describe both the secreted
and cell-envelope-associated pools. For field 6, antibody access may be
limited to the secreted fraction — the cell-wall-associated enzyme may
require a different delivery strategy (e.g., nanobody with tissue
penetration). For field 9, note that the crystal structure shows a
recessed active site (~21 Å hydrophobic tunnel) that is accessible to
small molecules (ebselen, PMID 24193546) but may not be accessible to
conventional IgG antibodies. Generalizes to any secreted enzyme that
also functions at the cell envelope (bacterial sortases, autotransporters,
cell-wall remodeling enzymes).

### 2. T-cell vaccine failures do NOT invalidate the antibody therapeutic approach

MVA85A (Ag85A viral vector, Phase 2b, 2797 infants, efficacy 17.3% — no
protection, PMID 23391465) and H56:IC31 (Ag85B fusion protein, Phase 2b,
831 adults, efficacy −73.8% — possible harm, PMID 40056922) both failed
as T-cell vaccines. But they targeted cellular immunity (Th1/CD4
responses), not antibody-mediated protection. The passive antibody
approach is entirely untested — no anti-Ag85 antibody has entered
clinical trials. For field 6, vaccine failures that target a DIFFERENT
immune mechanism (T-cell vs antibody) are NOT antibody failure modes —
they are orthogonal evidence that the target is immunologically relevant.
However, the H56:IC31 possible-harm signal (negative efficacy, possible
increased relapse risk) IS a cautionary flag for ANY immunological
intervention targeting Ag85, regardless of mechanism. For field 3, list
vaccine failures under disease evidence with the explicit note:
"T-cell-targeted; antibody approach untested." For field 11, the
differentiation opportunity is that a passive antibody bypasses the
failed T-cell mechanism entirely — but must be designed to avoid the
possible-harm signal's mechanism (unknown, possibly immune modulation
of granuloma containment). Generalizes to any target where T-cell
vaccines failed but antibody therapeutics are untested (TB, HIV, malaria).

### 3. Functionally relevant vs immunodominant epitopes — the "antigen recognition vs functional modulation" distinction

The 2026 review (PMID 42075259) makes an explicit, named distinction:
- **Antigen recognition**: conventional antibody responses target
  immunodominant but functionally irrelevant surface epitopes
- **Functional modulation**: a therapeutic antibody must target
  functionally critical regions (active site, substrate-binding tunnel)
  whose blockade disrupts enzymatic activity

For Ag85, the active site and ~21 Å hydrophobic tunnel are the
functionally critical regions, but they are recessed into the protein
core. The fibronectin-binding surface region (conserved across Ag85A/B/C)
is the immunodominant region — large, surface-exposed, but functionally
irrelevant for enzyme inhibition. This is the enzyme-target analog of
the LAM glycan-motif-level specificity pattern (PMID 37733444:
protective vs non-protective mAbs target different glycan motifs on the
same domain), but with a clearer mechanistic rationale: for enzymes,
the active site IS the functional epitope by definition. For field 5,
explicitly classify epitopes as "functionally relevant" (active
site/tunnel) vs "immunodominant but functionally irrelevant" (surface).
For field 6, "wrong epitope — immunodominant but functionally
irrelevant" is a distinct failure mode from "wrong epitope — wrong
glycan motif." Generalizes to any enzymatic target where the active
site is recessed and the surface is immunodominant (bacterial enzymes,
viral polymerases, toxin active sites).

### 4. Nanobody format as the solution for recessed active site access

The 2026 review (PMID 42075259) proposes nanobodies (~15 kDa)
specifically because conventional IgG (~150 kDa) cannot access the
recessed catalytic cleft and ~21 Å hydrophobic tunnel of Ag85. This is
a NEW format-differentiation pattern: the target's STRUCTURE (recessed
active site) dictates the antibody FORMAT (nanobody, not IgG). This is
distinct from:
- **PcrV/LAM Fc-effector pattern**: format determines MECHANISM (Fc
  effector function required for opsonophagocytosis)
- **Ag85 nanobody pattern**: format determines EPITOPE ACCESS (small
  size required to reach recessed active site)

For field 11, the format recommendation is structure-driven, not
mechanism-driven: if the functional epitope is in a recessed cleft or
tunnel, a nanobody (or small fragment) is required for access, and the
nanobody can then be fused to an Fc for effector function if needed.
For field 9, the crystal structure's active site geometry directly
informs the format choice — measure the tunnel/cleft depth and compare
to antibody CDR reach (~10–15 Å for IgG vs ~3–5 Å for nanobody).
Generalizes to any target where the functional epitope is recessed:
enzymes with deep active sites (Ag85, neuraminidases, proteases),
channels with internal binding sites (ion channels, porins).

### 5. Preclinical animal model unreliability as a strategic risk

The MVA85A preclinical animal studies (8 studies, 192 animals, 4
species: mice, guinea pigs, macaques, calves) FAILED to predict the
human Phase 2b failure (PMID 26351306). The studies were low quality
(no randomization, no blinding, no baseline comparability). No benefit
demonstrated for mortality, pathology, or bacterial load. The largest
macaque study showed MORE deaths in the vaccine group — published
AFTER the human infant trial had already started recruiting. For
field 6, when preclinical models are unreliable for a target, the
absence of predictive models is a STRATEGIC risk for ANY new
intervention (including antibodies), not just a tactical one. For
field 7, explicitly state which models have been used, their quality,
and whether they predicted human outcomes. For field 11, recommend
new biomarker-driven preclinical models or humanized models if
standard models have failed. Generalizes to any target where the
preclinical-to-clinical translation has failed (TB vaccines, Alzheimer's
immunotherapy, HIV vaccines).

### 6. Circulating antigen-antibody immune complexes as a safety risk

Ag85 circulates in serum of active TB patients complexed to fibronectin
and IgG (PMID 9916062) — uncomplexed Ag85 is present in <20% of
patients. An exogenous therapeutic anti-Ag85 antibody could exacerbate
immune complex formation, potentially causing glomerulonephritis or
vasculitis. This is a NEW safety pattern distinct from the CFH
autoantibody pattern (where autoantibody disease defines the toxicity
profile): here the RISK comes from the target's natural circulation
as pre-existing immune complexes, not from pathogenic autoantibodies.
For field 8, when the target naturally circulates as immune complexes,
flag immune complex-mediated toxicity (glomerulonephritis,
vasculitis) as a risk. For field 6, the immune complex risk is a
format-dependent failure mode: Fc-containing antibodies could worsen
immune complex deposition; nanobody format (no Fc) or Fc-silent
engineered antibodies could mitigate this. For field 11, recommend Fc
engineering (reduced FcγR binding) or nanobody format to avoid
exacerbating immune complex pathology. Generalizes to any target that
circulates as immune complexes in disease (autoantigens, shed tumor
antigens, viral antigens in chronic infection).
