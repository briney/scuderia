# ANP (NPPA) Profile — Detailed Observations

> 51st level-2 profile. Preclinical tier → confirmed preclinical (cardiovascular).
> Target: ANP (Atrial Natriuretic Peptide), gene NPPA, UniProt P01160.
> Profile: `working-docs/hitlist-profiles/anp.md` (~61K chars, 49 PMIDs cited).
> Built via delegated subagent, lightweight retrieval pipeline (direct PubMed
> E-utilities via urllib, no paper-ingest scripts). Abstract-only ingestion.
> 11 PubMed queries (3 specified + 8 supplementary), 25+ abstracts fetched,
> 2 PubMed HTTP 429s recovered with backoff.

## Profile at a glance

- **Target type**: Secreted peptide hormone (28 aa, ~3 kDa)
- **Receptor**: GC-A (NPR-A / NPR1), particulate guanylyl cyclase, type I transmembrane
- **Antibody approach**: Anti-*receptor* PAM antibody (NOT anti-peptide)
- **Key antibody paper**: PMID 41942428 (Nature Communications 2026) — XX16 (ligand-independent agonist) + REGN5308 (ligand-dependent PAM), cryo-EM structures, in vivo antihypertensive efficacy in obese-hypertension mice
- **Approved drugs**: Carperitide (recombinant ANP, Japan, acute HF — controversial), sacubitril/valsartan (ARNI — augments endogenous ANP/BNP via neprilysin inhibition)
- **Clinical pipeline**: MANP (designer ANP analog, Phase 1/2 hypertension + metabolic syndrome), cenderitide (chimeric dual GC-A/GC-B agonist, Phase 1 HF)
- **Genetic evidence**: NPPA knockout mice (hypertension, cardiac hypertrophy); human NPPA mutations (p.I137T, frameshift, p.Arg150Gln) cause atrial fibrillation and atrial dilated cardiomyopathy; T2238C polymorphism modifies antihypertensive response (ALLHAT)

## Key new patterns (6)

### 1. Secreted peptide hormone — the therapeutic antibody targets the *receptor*, not the peptide

ANP is a 28-aa peptide (~3 kDa) with a plasma half-life of ~2–5 min — too small
and too short-lived to be a practical antibody target for chronic therapy. All
published anti-ANP antibodies are immunoassay/diagnostic reagents (RIA, ELISA,
chemiluminescent) or a nanocarrier-targeting ligand (PMID 34575433). No
therapeutic neutralizing anti-ANP antibody exists.

The therapeutic antibody approach targets the *receptor* (GC-A/NPR-A/NPR1):
a type I transmembrane guanylyl cyclase with a large extracellular domain.
The 2026 Nature Communications paper (PMID 41942428) reported two monoclonal
antibodies (XX16, REGN5308) that are positive allosteric modulators (PAMs)
of GC-A — with cryo-EM structures and in vivo antihypertensive efficacy in
obese-hypertension mice. This is the first disclosed therapeutic antibody
approach to the ANP axis, and it targets the receptor, not the peptide.

**Rule**: When the target is a small secreted peptide (<5 kDa, short
half-life), explicitly state in field 1 whether the antibody approach targets
the peptide or the receptor. Default to the receptor if the peptide is too
small/short-lived for chronic antibody therapy. In field 4, list receptor-
targeted antibodies separately from peptide-targeted (immunoassay) antibodies.

**Generalizes to**: All small peptide hormones — ANP, BNP, CNP, endothelin,
adrenomedullin, relaxin, ghrelin, GIP, GLP-1, somatostatin, apelin, CGRP.
The receptor is the antibody-accessible therapeutic target, not the peptide.

### 2. Positive allosteric modulator (PAM) antibodies — a new mechanism class

The ANP/GC-A axis is the first profiled target where the antibody mechanism
is **positive allosteric modulation** — the antibody enhances endogenous
ligand signaling rather than blocking or independently activating.

Two sub-types:
- **XX16** = ligand-independent agonist PAM. Stabilizes GC-A in an active
  conformation even without ANP. Stronger stabilizing influence on ATP and
  GTP binding. Cryo-EM structure determined.
- **REGN5308** = ligand-dependent PAM. Requires ANP to fully promote receptor
  activation. Increases ANP binding affinity to GC-A. Cryo-EM structure
  determined.

This is a **fourth mechanism class**, distinct from:
1. Neutralizing (block primary function)
2. Agonist (activate independently — e.g., TrkB 29D7)
3. Function-selective (block one function, spare another — e.g., tPA Glunomab)
4. **PAM** (enhance endogenous ligand signaling — XX16/REGN5308)

The ligand-dependent PAM (REGN5308) has a unique safety advantage: it
preserves physiological feedback (endogenous ANP release tracks atrial
stretch), reducing the risk of sustained overactivation when atrial
pressure is low.

**Rule**: For field 4, add a "mechanism class" descriptor: ligand-independent
agonist / ligand-dependent PAM / neutralizing / function-selective. For
field 5, PAM antibody epitopes are *conformational* (receptor dimerization
interface / allosteric site), not linear — cryo-EM structure is essential
for epitope mapping. For field 11, the ligand-dependent vs ligand-independent
choice is a safety-driven format differentiation.

### 3. Long-acting agonist antibody — non-titratable hypotension as a format liability

A monthly (long-acting) agonist antibody against a vasodilatory pathway
(ANP/GC-A → cGMP → vasodilation) risks sustained, non-titratable
hypotension. Unlike oral drugs (stoppable) or short-acting peptide infusions
(titratable, stoppable), a long-acting antibody cannot be rapidly
discontinued if symptomatic hypotension occurs.

This is the *agonist* analog of the ACE-neutralizing-antibody format
liability (ace.md: antagonist with non-titratable RAAS toxicity). Both
share: long half-life + non-titratable kinetics + a pathway where the
on-target effect is dose-limiting.

Hypotension is the leading AE of sacubitril/valsartan (PMID 39284545) and
the dose-limiting toxicity of all ANP-axis agonists (carperitide, MANP,
cenderitide). Cenderitide was engineered to achieve renal/anti-fibrotic
effects "without clinically significant hypotension" (PMID 29226471).

**Mitigation strategies** (for field 11):
- Ligand-dependent PAM design (REGN5308 — preserves physiological feedback)
- Partial agonism (lower maximal efficacy, analogous to TAM-163 partial
  TrkB agonism for chronic CNS dosing)
- Conservative dosing with hypotension monitoring
- Patient selection (avoid hypovolemic/low-BP patients)

**Rule**: For any agonist antibody against a vasodilatory/natriuretic
pathway, field 8 must flag non-titratable hypotension as the primary safety
liability and field 6 must list it as the dominant failure-mode class.

**Generalizes to**: Agonist antibodies against vasodilatory or BP-lowering
pathways — ANP/GC-A, BNP/GC-A, adrenomedullin/ADM-R, relaxin/RXFP1,
CGRP/RAMP1.

### 4. Approved peptide agonist with no mortality benefit (carperitide) — target valid, format matters

Carperitide (recombinant human ANP / α-hANP) is approved in Japan for
acute heart failure (since 1995) but clinical outcomes are controversial:
- Propensity-matched study: carperitide associated with *increased*
  in-hospital mortality (OR 2.13, P=0.013), with greater harm in elderly
  (OR 2.93) (PMID 25999241)
- LASCAR-AHF RCT (247 patients): no significant difference in composite
  death/HF hospitalization; greater eGFR decline (PMID 39656827)
- 2025 meta-analysis (6 studies): no significant mortality or
  hospitalization benefit (RR 1.02), "challenging its widespread use"
  (PMID 40922889)

Meanwhile, sacubitril/valsartan (ARNI — neprilysin inhibition augments
endogenous ANP/BNP + ARB) is approved for HFrEF (PARADIGM-HF, PMID
25176015) and beneficial in HFpEF (PARAGON-HF, PMID 31475794) — proving
the *target* is valid.

The failure is *peptide-format-specific* (short half-life ~2–5 min requiring
continuous IV infusion, hypotension, renal function decline), not *target-
specific*. A long-acting antibody PAM (months, not minutes) is the
differentiated opportunity.

**Rule**: For field 3, separate "evidence for the target" (strong — ARNI
success + knockout genetics) from "evidence for the direct peptide format"
(weak — carperitide failure). For field 6, the failure is format-specific
(short half-life, infusion delivery), not target-specific.

**Generalizes to**: Any short-lived peptide hormone where direct
replacement failed but indirect augmentation succeeded.

### 5. PubMed search for receptor-targeted antibodies — include receptor name, not just peptide name

Generic `"ANP antibody"[tiab]` and `"atrial natriuretic peptide
antibody"[tiab]` queries returned immunoassay antibodies (anti-peptide
RIA/ELISA) and old mechanistic papers — NOT the therapeutic anti-receptor
(GC-A) antibodies.

The landmark anti-GC-A PAM antibody paper (PMID 41942428, 2026) was found
via `"natriuretic peptide receptor" antibody[tiab]`, `"GC-A antibody"[tiab]`,
and `REGN5308[tiab]` queries, not via peptide-name queries.

**Rule**: For secreted peptide hormones where the antibody targets the
receptor, run receptor-name queries alongside peptide-name queries:
- `"<receptor name> antibody"[tiab]`
- `"<receptor gene symbol> antibody"[tiab]`
- `"<receptor alias> antibody"[tiab]`

The clinical/therapeutic antibody evidence is published under the receptor
name, not the peptide name.

**Generalizes to**: All peptide-hormone targets where the antibody
approaches the receptor (ANP/GC-A, GLP-1/GLP-1R, ghrelin/GHS-R, CGRP/RAMP1,
somatostatin/SSTR, endothelin/ET receptor).

### 6. NPPA loss-of-function causes disease — therapeutic direction is agonism, not antagonism

NPPA mutations cause disease via *loss of function*:
- p.Ile138Thr (I137T): reduces ANP–NPR-A interaction, cGMP, activates
  inflammation/fibrosis → atrial fibrillation (PMID 31034774)
- Frameshift NPPA: ion channel remodeling → familial AF (PMID 31077706)
- p.Arg150Gln (homozygous): atrial dilated cardiomyopathy with atrial
  standstill (PMID 40838933)
- NPPA knockout mice: hypertension, cardiac hypertrophy, salt-sensitivity
  (PMID 23981445)

ANP *deficiency* is pathogenic. A neutralizing (antagonist) anti-ANP or
anti-GC-A antibody would worsen hypertension and AF — the *wrong*
therapeutic direction. The therapeutic direction is *agonism* (GC-A PAM).

A neutralizing antibody would only be relevant for rare ANP-excess states
(ANP-producing tumors, vasodilatory shock) — a narrow blue ocean.

**Rule**: When the target's loss-of-function causes the disease of
interest, the neutralizing-antibody direction is a failure mode, not a
strategy. For field 6, flag the wrong direction explicitly. For field 11,
state the therapeutic direction (agonism vs antagonism) and flag the
wrong direction as a known risk.

This is the cardiovascular analog of the clusterin "double-edged sword"
pattern (neuroscience: enhancement, not inhibition, for AD).

## PubMed search queries used (11)

Specified (3):
1. `"atrial natriuretic peptide antibody"[tiab]` → 3 results
2. `"ANP antibody"[tiab]` → 14 results
3. `"NPPA antibody therapeutic"[tiab]` → 0 results

Supplementary (8):
4. `"atrial natriuretic peptide"[tiab] AND ("monoclonal antibody"[tiab] OR "therapeutic"[tiab] OR "neutralizing antibody"[tiab])` → 30
5. `"natriuretic peptide"[tiab] AND "antibody"[tiab] AND ("heart failure"[tiab] OR "hypertension"[tiab] OR "myocardial"[tiab])` → 30
6. `"NPPA"[tiab] AND ("heart failure"[tiab] OR "genetic"[tiab] OR "polymorphism"[tiab])` → 30
7. `cenderitide[tiab] OR "carperitide"[tiab] OR "anaritide"[tiab] OR "nesiritide"[tiab]` → 30
8. `"natriuretic peptide receptor"[tiab] AND "antibody"[tiab]` → 30
9. `"atrial natriuretic peptide"[tiab] AND ("knockout"[tiab] OR "deficient"[tiab] OR "transgenic"[tiab])` → 30
10. `"NPPA"[tiab] AND ("genetic variant"[tiab] OR "polymorphism"[tiab] OR "mutation"[tiab]) AND ("heart failure"[tiab] OR "hypertension"[tiab] OR "atrial fibrillation"[tiab])` → 20
11. `MANP[tiab] AND ("first-in-human"[tiab] OR "clinical trial"[tiab] OR "hypertension"[tiab])` → 13

Two HTTP 429 errors during batch querying; recovered with 20-60s backoff.

## Retrieval statistics

- Papers reviewed: 25+ (abstracts fetched via efetch XML)
- Full text retrieved: 0 (abstract-only ingestion; delegated subagent,
  lightweight pipeline)
- Key papers: PMID 41942428 (GC-A PAM antibodies, Nat Commun 2026), PMID
  34657445 + 38362338 (MANP first-in-human + metabolic syndrome), PMID
  31034774 + 31077706 (NPPA mutations → AF), PMID 23981445 (ANP KO), PMID
  25999241 + 39656827 + 40922889 (carperitide failure), PMID 29226471 +
  29941213 (cenderitide), PMID 21498657 (GC-A/NPR-C receptor antibody
  tracking), PMID 35998113 (ANP/autophagy), PMID 18212314 (NPPA T2238C
  pharmacogenetics, ALLHAT)
- Unique PMIDs cited: 49
- Profile size: ~61K chars
