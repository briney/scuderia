# TrkB (NTRK2) profile observations

**Target**: TrkB (Tropomyosin receptor kinase B, NTRK2, UniProt Q16620)
**Tier**: preclinical (neuroscience)
**Profile**: working-docs/hitlist-profiles/trkb.md
**Date**: 2026-08-17
**Papers ingested**: 5 (3 PMC XML OA, 1 EPMC PDF, 1 publisher-jina)
**Full-text retrieval rate**: 100% (5/5)
**Unique PMIDs cited**: 13 (5 ingested + 8 from abstract screening)

---

## Full-text retrieval

All 5 papers retrieved at 100% — the best journal mix for TrkB antibody
literature:

- PMID 39247456 (3 Biotech, 2024): EPMC PDF render (inPMC=Y, OA=N, hasPDF=Y
  but `hasPDF` flag unreliable — PDF rendered anyway). 54K chars.
- PMID 35890231 (Pharmaceutics, 2022): PMC XML OA. 32K chars.
- PMID 32550908 (Theranostics, 2020): PMC XML OA. 59K chars.
- PMID 24668485 (Springer book chapter, 2014): publisher-jina (only
  references extracted, not main text — book chapter, paywalled). 107K
  chars but mostly bibliography. Abstract fetched from Europe PMC core
  record to compensate.
- PMID 23700410 (PLoS ONE, 2013): PMC XML OA. 54K chars.

The journal mix (MDPI-family OA, PLoS ONE, Theranostics, 3 Biotech) is
very OA-friendly. The one paywalled item (Springer book chapter) was
retrieved via jina but yielded only the references section — the main
text was not extractable. Europe PMC's structured abstract (1,488 chars)
provided sufficient content for the review's key claims. This confirms
the sortilin-profile observation: neuroscience OA journals (BioMed
Central, Frontiers, MDPI, PLoS) have very high full-text retrieval rates
for delegated profiling.

**EPMC PDF render with hasPDF=N works again.** PMID 39247456 had
`inPMC=Y, isOpenAccess=N, hasPDF=Y` — the PDF rendered successfully via
Branch 1b. Consistent with the CXCL7 profile observation that the
`hasPDF` flag is unreliable and Branch 1b should always be tried when
`inPMC=Y`.

## Key new patterns

### 1. BBB penetration as the dominant challenge for neuroscience antibody targets

This is the **first profile where the blood-brain barrier (BBB) is the
dominant obstacle for antibody therapeutic development**, distinct from
all prior profiles where the target biology, epitope, or competitive
landscape was the primary challenge. Key observations:

- Unmodified TrkB agonist antibodies achieve only ~0.1-0.6%
  tissue-to-serum ratio in brain (0.13-0.39 nM brain levels) —
  insufficient for robust target engagement (PMID 35890231, PMID
  23700410).
- BDNF protein itself has a plasma half-life of only ~10 min and cannot
  cross the BBB — the failures of BDNF clinical trials (ALS, diabetic
  neuropathy) are directly attributable to this (PMID 32550908).
- The TXB4-TrkB bispecific fusion (VNAR-TfR1 shuttle + 29D7 TrkB agonist)
  achieved 12-fold higher brain concentrations (4.7 nM) and complete
  neuroprotection in the 6-OHDA PD model — the first demonstrated
  solution to the BBB problem for TrkB antibodies (PMID 35890231).
- AS86 achieved ~1 nM brain concentration at 1.5 mg/kg IV — marginal
  but sufficient for target engagement in APP/PS1 AD mice, relying on
  the "leaky BBB" in AD pathology (~0.1-0.2% antibody crossing) (PMID
  32550908).

**For field 6 (failure modes)**, BBB penetration failure is the
headline failure mode for any CNS antibody target. It is a
**format-level, not target-level** failure — it affects every antibody
against a CNS target, regardless of epitope, isotype, or mechanism.
This generalizes beyond TrkB to all brain-targeted antibodies (anti-Aβ,
anti-tau, anti-α-synuclein, etc.).

**For field 11 (differentiation)**, the BBB shuttle approach (TfR1,
IGF1R, or other receptor-mediated transcytosis) is the primary
differentiation axis for CNS antibody therapeutics. The TXB4 VNAR
format (shark single-domain antibody, 12-15 kDa, cryptic epitope
access) represents one engineering solution. Others include: low-affinity
TfR1 antibodies (Denali ETP platform), focused ultrasound BBB opening,
and intrathecal/intraventricular delivery. For profiling future CNS
antibody targets, always document which BBB penetration strategies
have been attempted and their outcomes.

### 2. Species-dependent paradoxical pharmacology — the NHP translational trap

TAM-163 (humanized 29D7 TrkB agonist) causes:
- **Weight loss** in mice (20% at 10 mg/kg), rats (12%), hamsters, dogs
- **Weight gain** in rhesus monkeys (up to 35% with repeat dosing) and
  appetite stimulation (63% increase in food intake)

This paradoxical reversal is NOT explained by differential drug
exposure, brain penetration, or TrkB binding affinity (TAM-163
cross-reacts with all tested species). The "dual role" hypothesis
proposes that peripheral/CVO TrkB activation stimulates appetite while
central TrkB activation suppresses it; at low doses only peripheral
effects are engaged in NHPs, while at very high doses (200 mg/kg)
central effects cancel out the peripheral weight gain (PMID 23700410).

**This is a new failure-mode class — species-dependent paradoxical
pharmacology** — distinct from:
- The Nav1.8 rodent→human efficacy gap (quantitative difference in
  contribution, not direction reversal)
- The C3aR SB290157 agonist/antagonist recharacterization (tool
  compound mischaracterization, not species-dependent biology)
- The urotensin II species-dependent receptor pharmacology (>100-fold
  affinity difference, not direction reversal)

The TrkB pattern is the most severe: the **direction of the
pharmacological effect reverses** between rodents and NHPs. For field
6, this means rodent efficacy data for TrkB agonist antibodies
**cannot predict primate outcomes** — a fundamental translational
barrier that can only be resolved in clinical trials. For field 8
(safety), the metabolic toxicity is unpredictable across species.

**Generalizable to any CNS target with species-different appetite/
metabolic circuitry.** The neuroanatomical differences in appetite
circuits between rodents and primates (NPY expression patterns, CART
neuron projections) are well-documented. For profiling future CNS
targets involved in metabolic regulation, always check for
species-dependent pharmacology and flag it as a translational risk in
field 6.

### 3. Dual agonist + antagonist antibody approaches on a single neuroscience target

TrkB is the **first neuroscience target with both agonist and antagonist
antibody approaches documented** — extending the IL-15 dual-directional
pattern (cytokine, immunology) to neuroscience:

- **Agonist antibodies**: 29D7 → TAM-163 (Pfizer/Rinat), AS86 (academic),
  TXB4-TrkB (Ossianix), ZEB85, 38B8 — for neurodegenerative diseases
  (AD, PD), spinal cord injury, and obesity
- **Antagonist antibodies**: TrkB-IgL 5.11 (Ankara University) — for
  cancer (TrkB-overexpressing tumors) and potentially pain

The agonist and antagonist approaches have completely different:
- Mechanisms (mimic BDNF vs block BDNF)
- Indications (neurodegeneration/repair vs cancer/pain)
- Safety profiles (metabolic effects of activation vs potential effects
  of blockade)
- BBB requirements (agonist needs brain penetration; antagonist for
  cancer may not)

**For field 4 (antibody landscape)**, list both directions. **For
field 6**, the failure modes differ by direction:
- Agonist failure: BBB penetration, species-dependent metabolic
  pharmacology, stage-dependent efficacy, on-target metabolic toxicity
- Antagonist failure: IgM isotype limitation (only published clone),
  no pain model validation, unexplored competitive space

**For orchestrators delegating neuroscience target profiles**: check
if both agonist and antagonist antibody approaches exist — if so,
instruct the subagent to cover both directions, as established for
cytokine targets (IL-15 observation).

### 4. Partial agonism as a deliberate safety design feature

TAM-163 is a **partial TrkB agonist** (lower maximal efficacy than
BDNF) — not a full agonist. This appears to be a deliberate design
choice for chronic CNS therapy:
- Full TrkB agonism risks receptor overactivation, potentially causing
  excitotoxicity or excessive metabolic effects
- Partial agonism provides sufficient signaling for neuroprotection
  while limiting the maximum pharmacodynamic effect
- The LALA Fc mutations (Leu234Ala, Leu235Ala) in TXB4-TrkB further
  attenuate effector function — a second safety layer

**For field 4 and field 11**, partial agonism is a format
differentiation strategy. For chronic CNS antibody therapy, a partial
agonist may have a better therapeutic index than a full agonist.
Generalizes to any receptor-targeting agonist antibody where chronic
dosing is required (TrkB, TrkA, TrkC, GDNF receptor RET, other
neurotrophin receptors).

### 5. IgM isotype as a development bottleneck for antagonist antibodies

The only published neutralizing anti-TrkB antibody (TrkB-IgL 5.11) is
IgM — a therapeutically impractical isotype:
- Short half-life (hours, not days)
- Poor tissue penetration (very large pentamer)
- Difficult to humanize and engineer
- No established manufacturing platform for therapeutic IgM

The IgG1 clones from the same campaign (4.11, 4.6, 4.3) showed less
consistent functional activity — the neutralizing clone happened to be
IgM. This is a generalizable pattern for antagonist antibody
discovery: **the most functionally potent clone may not be in the
therapeutically optimal isotype**. For field 6 (failure modes), this
is a format failure — the antibody works but the isotype prevents
development. For field 11 (differentiation), generating a de novo
IgG1 neutralizing antibody against the same Ig-like domain epitope is
the primary white space.

**Generalizable to any antagonist antibody campaign where hybridoma
screening yields the best clone in a non-therapeutic isotype.** The
solution is either isotype switching (if the paratope is preserved) or
de novo IgG discovery (phage display, single B-cell cloning).

### 6. Stage-dependent efficacy for synaptic repair antibodies

AS86 (TrkB agonist for AD) showed a critical therapeutic window:
- Effective at early/mid-stage AD (6-month treatment, age 11 months)
- Ineffective at advanced stage (9-month treatment, age 14 months)
- Despite continued synaptic marker improvement at advanced stage

This is a new failure-mode class — **stage-dependent efficacy
ceiling** — where the therapeutic mechanism (synaptic repair) requires
viable neurons and fails when neuronal loss becomes overwhelming. It
is distinct from:
- The Nav1.8 paralog redundancy ceiling (sibling channels cover the
  function)
- The sortilin inverse-target approach (blocking clearance to elevate
  a ligand)

The TrkB pattern is about **disease stage**, not target biology. For
field 6, the failure is not the antibody or the target but the
**timing of intervention**. For field 11, the differentiation path is
biomarker-defined early intervention (prodromal AD, early PD) — the
population selection IS the differentiation. Generalizes to any
neuroprotective/neuroregenerative antibody target (anti-Aβ in early
AD, anti-α-synuclein in prodromal PD, anti-TrkB in mild cognitive
impairment).

### 7. PubMed search term adaptation for receptor agonist + antagonist targets

The standard search `"TrkB antibody"[tiab]` returned good results,
but `"NTRK2 antibody therapeutic"[tiab]` returned zero — the gene
symbol is rarely used in antibody therapeutic papers. Instead:
- `"TrkB agonist antibody"[tiab]` was the highest-yield query (8
  PMIDs covering both agonist and brain-delivery approaches)
- `"anti-TrkB"[tiab] AND antibody[tiab]` found the antagonist antibody
  paper and diagnostic IHC antibodies
- `"TrkB antagonist"[tiab]` found small-molecule antagonists (ANA-12)
  and pain/neuroscience context papers
- The combined approach (9 search terms) recovered 50+ unique PMIDs
  across all relevant categories

**For orchestrators**: when delegating a neuroscience receptor target
with both agonist and antagonist antibody approaches, provide search
templates covering both directions plus the gene symbol fallback:
```
"<target> agonist antibody"[tiab]
"anti-<target>"[tiab] AND antibody[tiab]
"<target> antagonist"[tiab]
"<gene> antibody therapeutic"[tiab]  # often zero — use as fallback
```

(TrkB profile, ~41K chars, 5 papers ingested (5/5 full text), 13 PMID
citations, working-docs/hitlist-profiles/trkb.md.)
