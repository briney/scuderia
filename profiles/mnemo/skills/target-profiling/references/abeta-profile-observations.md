# Amyloid Beta (Aβ) profile observations (2026-08-16)

Twenty-fifth level-2 profile (approved tier, neuroscience — Alzheimer's
disease). Aβ (amyloid beta, beta-amyloid) is a 38-43 amino acid peptide
cleavage product of APP (amyloid precursor protein) by sequential
β-secretase (BACE1) and γ-secretase processing. This is the **first
neuroscience target profiled** and the **canonical graveyard-to-success
story** referenced in the `antibody-target-hitlist` skill. Three approved
anti-Aβ antibodies (aducanumab/Aduhelm 2021, lecanemab/Leqembi 2023,
donanemab/Kisunla 2024) — the first disease-modifying therapies for
Alzheimer's disease. Five failed (bapineuzumab, solanezumab, gantenerumab,
crenezumab, ponezumab — all failed Phase 3). 5 key papers ingested, 5 new
paper pages written. ~50K chars (profile), 5 unique PMIDs cited.
Full-text retrieval: 3/5 PMC XML OA (Kim 2025, Cummings 2024, Jucker 2023),
1/5 EPMC PDF (Chen 2017 — Acta Pharmacol Sin, PMC XML front-matter only
→ EPMC PDF 2.9 MB, 170K chars), 1/5 jina-reader Lancet PIIS URL (Heneka
2024 — abstract + 62-reference list). 80% full-text retrieval rate.

New observations:

## 1. The graveyard-to-success archetype: epitope/conformation selectivity, not target invalidity

The Aβ target is the canonical example referenced in the
`antibody-target-hitlist` skill ("The graveyard wasn't dead — it was
waiting for a better antibody"). The five graveyard antibodies failed
for antibody-specific reasons, not target-specific reasons:

- **Solanezumab** targeted soluble Aβ monomers — the wrong species.
  Monomeric Aβ is abundant (picomolar in CSF); complete neutralization
  requires stoichiometric antibody amounts. Toxicity is linked to the
  *aggregated* state, not monomers. Failed in 4 Phase 3 trials. (PMID
  37729908, PMID 39865265.)
- **Ponezumab** targeted the C-terminus — buried within fibrillar
  structures, limiting epitope accessibility to aggregated forms. (PMID
  28713158.)
- **Crenezumab** used IgG4 isotype — weak FcγR binding, minimal
  complement activation, decreased microglial phagocytic function.
  Reduced ARIA but also reduced efficacy. No drug-placebo difference in
  Phase 2 or 3. (PMID 39865265.)
- **Gantenerumab** had the right epitope (fibrils, aa 3-11 + 18-27)
  and isotype (IgG1) but insufficient dose/brain exposure —
  subcutaneous administration with gradual 9-month titration
  (120→225→510→1020 mg) failed to reduce Aβ to the 15-25 centiloid
  threshold for clinical benefit. A dosing/PK failure, not an epitope
  failure. (PMID 37955845, PMID 39865265.)
- **Bapineuzumab** targeted N-terminus (aa 1-5) and plaques but had
  high ARIA even at low doses and no clinical benefit. Wrong
  population (mild-moderate AD, no biomarker confirmation). (PMID
  37955845, PMID 39865265.)

The three successful antibodies each targeted a different Aβ species
with IgG1 isotype: aducanumab (N-terminus aa 3-7, fibril preference),
lecanemab (protofibrils, aa 1-16 + 21-29, 100:1 over monomers),
donanemab (N3pE pyroglutamate, plaque-specific).

For field 6 (failure modes) of graveyard-to-success profiles, each
graveyard antibody's failure must be diagnosed as target-specific vs
antibody-specific. The Aβ profile is the cleanest example: all 5
graveyard failures were antibody-specific (wrong epitope, wrong
species, wrong isotype, wrong dose), and the target was validated by
3 subsequent successes. (PMID 28713158, 37729908, 37955845, 39865265.)

## 2. The centiloid threshold — amyloid reduction must cross a critical level for clinical benefit

A key insight from the Cummings 2024 review: "slowing of clinical
decline has been observed when the β-amyloid lowering reaches 15-25
centiloids." Gantenerumab failed because its subcutaneous dosing did
not achieve sufficient amyloid reduction to cross this threshold,
despite 80% of participants becoming amyloid-negative in the open-label
extension. The cognitive benefit was absent during the Phase 3 period
when amyloid reduction was insufficient.

For field 6 (failure modes) and field 7 (assay systems/biomarkers) of
anti-amyloid profiles, the centiloid threshold is a critical concept:
(1) amyloid PET centiloid reduction is the primary surrogate endpoint;
(2) the 15-25 centiloid threshold defines the minimum amyloid clearance
needed for clinical benefit; (3) a dosing/PK failure (insufficient
brain exposure) can prevent crossing this threshold even with the
correct epitope and isotype. This is a generalizable lesson for
CNS-targeted antibodies: the brain's unique PK constraints (BBB
penetration, CSF clearance) create a dose threshold that peripheral
targets do not face. (PMID 37955845.)

## 3. ARIA is mechanism-inherent, not antibody-specific — the isotype/epitope tradeoff

Amyloid-related imaging abnormalities (ARIA-E edema, ARIA-H hemorrhage)
are the primary dose-limiting toxicity of all anti-amyloid antibodies
targeting aggregated Aβ. ARIA is linked to the mechanism of action —
Fc-mediated microglial phagocytosis of antibody-opsonized plaques near
blood vessels, including vascular amyloid (CAA).

The isotype/epitope tradeoff is the key pattern:
- **IgG4 antibodies** (crenezumab): low ARIA (IgG4 weakly binds FcγR,
  minimal complement), but also low efficacy (insufficient microglial
  phagocytosis for plaque clearance).
- **IgG1 antibodies targeting monomers** (solanezumab): low ARIA (no
  plaque clearance), no efficacy.
- **IgG1 antibodies targeting aggregates** (aducanumab, lecanemab,
  donanemab): higher ARIA (10-24% ARIA-E) but clinical efficacy.

The tradeoff: targeting aggregated Aβ with IgG1 is necessary for both
efficacy (microglial clearance) and ARIA (vascular amyloid removal).
The ARIA risk is inherent to the mechanism — any antibody clearing
amyloid plaques will produce some ARIA. APOE ε4 carriers have higher
ARIA risk (higher CAA burden). Oligomer-selective antibodies (ACU193,
>500-fold selectivity, ARIA-E 7.1%) may offer a better therapeutic
index by targeting toxic soluble species without aggressive vascular
plaque clearance.

For field 6 (failure modes), field 8 (safety), and field 11
(differentiation) of anti-amyloid (and potentially other plaque-
clearing) profiles: (1) ARIA is on-target, mechanism-based, not
antibody-specific; (2) the isotype choice (IgG1 vs IgG4) trades ARIA
for efficacy; (3) the epitope choice (aggregate-targeting vs
monomer-targeting) determines whether the antibody engages the
ARIA-causing mechanism at all; (4) APOE ε4 carrier status is a patient
selection variable; (5) oligomer-selective antibodies with silenced
Fc may decouple efficacy from ARIA. (PMID 39865265, PMID 37955845,
PMID 37729908.)

## 4. N3pE pyroglutamate — a post-translational modification creates a stage-specific epitope

Donanemab targets N3pE (pyroglutamate-modified Aβ at position 3),
a post-translational modification that enhances aggregation propensity
and emerges predominantly in later stages of cerebral β-amyloidosis.
This makes donanemab highly effective at removing established plaques
in symptomatic patients, but its specificity for a late-arising epitope
may limit utility for immunoprevention in preclinical disease (where
N3pE has not yet formed).

For field 5 (epitope landscape) of targets with disease-stage-
dependent post-translational modifications: (1) the epitope's
temporal emergence in disease progression determines whether the
antibody is suitable for treatment (late-stage epitope OK), prevention
(early-stage epitope needed), or both; (2) a PTM-specific antibody is
highly selective for pathological forms (avoiding normal Aβ), which
may reduce off-target effects but creates a stage-dependent efficacy
window; (3) the next-generation antibody remternetug targets the same
N3pE epitope, confirming this as a validated epitope bin. (PMID
37729908, PMID 37955845.)

## 5. Lancet PIIS URL form confirmed for a fifth profile session

PMID 39549715 (Heneka 2024, Lancet — "Passive anti-amyloid β
immunotherapy") was a subscription Lancet article with no PMCID and
EPMC all flags N. The jina reader proxy on the PIIS URL form
(`thelancet.com/journals/lancet/article/PIIS0140-6736(24)01883-X/
fulltext`) returned 14K chars — the abstract and complete 62-reference
list (including all key aducanumab/lecanemab/donanemab trial
publications). The DOI suffix `S0140-6736(24)01883-X` starts with "S",
combining with "PII" to form "PIIS" without an extra "S" (the initial
attempt with `PIISS0140-...` returned 404). This is the fifth
confirmation of the Lancet PIIS URL technique (after IL-17A/IL-17F,
CD22, IL-31Rα, IL-5). (PMID 39549715.)

## 6. PMC XML front-matter-only → EPMC PDF render works for Acta Pharmacologica Sinica (Nature/APS)

PMID 28713158 (Chen 2017, Acta Pharmacologica Sinica) had PMCID
PMC5589967 with `inPMC: Y`, but PMC XML efetch returned front-matter
only (8.2 KB, no `<body>` element). The EPMC PDF render
(`europepmc.org/api/getPdf?pmcid=PMC5589967`) succeeded — 2.9 MB PDF,
170K chars extracted via pymupdf. This is the same Branch 1b pattern
confirmed across multiple publishers (JCI Insight, OUP/ATS, EMBO J,
CSHLP, ASCO/JCO, AME Publishing). Acta Pharmacologica Sinica (published
by Springer Nature on behalf of CPS/SIMM) follows this pattern when
the PMC XML body is restricted but the PDF is available via EPMC.
Tag `fulltext_source: epmc-pdf`. (PMID 28713158.)

(Aβ profile, ~50K chars, 5 papers, 5 unique PMIDs cited, 23 authors,
working-docs/hitlist-profiles/abeta.md.)
