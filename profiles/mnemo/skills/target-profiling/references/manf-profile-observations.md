# MANF profile observations (2026-08-17)

Fiftieth level-2 profile (preclinical tier, neuroscience — PD/AD/stroke/diabetes).
MANF (Mesencephalic Astrocyte-Derived Neurotrophic Factor, gene MANF) is a
secreted, ER-resident neurotrophic factor that promotes dopaminergic neuron
survival via ER stress / UPR modulation. 8 landmark papers identified via
PubMed esearch (5 queries), 2/8 retrieved as full text via PMC XML
(PMID 37048105 — Front Neurol, 32K chars; PMID 37555005 — Int J Mol Sci,
81K chars), 6/8 abstract-only (paywalled, no PMCID). 15 total abstracts
retrieved via efetch for supplementary content. UniProt P55145 (human MANF,
182 aa, 20.7 kDa). PDB: 2KVD (NMR solution structure). CDNF Phase I/II
clinical trials confirmed (NCT03295786, NCT03775538). ~52.7K chars profile,
14 unique PMIDs cited, working-docs/hitlist-profiles/manf.md.

## Key new patterns

### 1. Augmentation-only target — no antibody blockade paradigm

MANF is the **first profiled target where the therapeutic paradigm is
exclusively augmentation (recombinant protein delivery or gene therapy),
with zero anti-MANF antibodies in development**. This is distinct from:
- TrkB (dual-directional: agonist antibodies for neurodegeneration,
  antagonist antibodies for cancer/pain)
- Clusterin (opposite direction across disease areas: enhancement for
  AD, inhibition for cancer)

MANF has only ONE direction across ALL disease areas — augmentation.
The antibody landscape (field 4) consists entirely of research/diagnostic
reagents; the "antibody landscape" entries are recombinant protein (rMANF)
and AAV gene therapy, not antibodies. The epitope landscape (field 5) has
no mapped epitopes, no antibody binning, no neutralizing vs non-neutralizing
classification — because no therapeutic antibody campaign has been run.

**Implication for profiling:** When the target is augmentation-only:
- Field 4 should list the therapeutic protein/gene therapy approaches as
  entries, clearly noting "not an antibody" in the format field.
- Field 5 should describe the functional interaction surfaces (receptor-
  binding, chaperone-interaction) that WOULD be relevant for antibody
  design, even though no antibodies exist yet.
- Field 11 should explore whether an agonist antibody (mimicking the
  protein's activity) or a receptor-targeted antibody (targeting the
  downstream receptor) could replace recombinant protein delivery —
  solving the CNS delivery challenge that plagues protein therapeutics.
- The "gaps" in field 10 should note the absence of antibody approaches
  as an opportunity, not just an empty field.

Generalizes to any neurotrophic factor / ER chaperone / growth factor
target where the therapeutic paradigm is protein replacement, not
antibody blockade (GDNF, neurturin, CDNF, MANF, FGF21, IGF-1).

### 2. UniProt ID verification — task-specified IDs can be wrong

The task specified UniProt ID P56528, but P56528 is mouse CD38 (ADP-
ribosyl cyclase), not human MANF. The correct human MANF UniProt entry
is P55145. This was caught by fetching the UniProt record and checking
the protein name + gene symbol against the target.

**Rule:** Always verify the UniProt ID by fetching the record and
confirming the protein name and gene symbol match the target. Do not
trust task-specified UniProt IDs blindly — they may be wrong (wrong
species, wrong paralog, or a completely unrelated protein). When a
mismatch is found, use the correct ID and note the discrepancy in the
profile's field 1.

### 3. Paralog clinical precedent as translational evidence

MANF has not entered clinical trials, but its paralog CDNF (~50% sequence
similarity, same protein family, same mechanism: ER stress / UPR
modulation, dopaminergic neuroprotection) completed Phase I/II clinical
trials in PD (NCT03295786, NCT03775538) via intracerebral brain infusion
— shown to be safe and well-tolerated in 17 PD patients.

This "paralog clinical precedent" is a distinct evidence type that
strengthens the target's translatability argument without being direct
clinical evidence for the target itself. It should be listed in field 3
(disease evidence) as a separate entry with evidence type "clinical
success (paralog)" and a clear explanation of the relationship.

**Generalizable pattern:** When a target has a close paralog (same
family, same mechanism) that has reached clinical trials or approval,
document the paralog's clinical status as translational evidence. This
de-risks the target's clinical translatability. The paralog must share
the core mechanism, not just structural homology. Key elements to
capture: paralog name, sequence similarity, shared mechanism, clinical
trial NCT IDs, outcome, and what the paralog's clinical experience
implies for the target (delivery approach, safety profile, dosing).

### 4. Paradoxical disease-context dual role — augmentation target edition

MANF shows a paradoxical role across neurodegenerative diseases:
- **PD (protective):** MANF augmentation protects dopaminergic neurons
  across multiple PD models (6-OHDA, MPTP, rotenone, α-synuclein).
  MANF deficiency increases neuronal vulnerability. Therapeutic direction:
  augmentation.
- **AD (pathogenic):** MANF overexpression CAUSES synapse loss and
  learning/memory deficits in AD mouse models (PMID 39425207). Both
  increasing and decreasing MANF in AD hippocampus exacerbated or
  ameliorated pathology respectively. Therapeutic direction: REDUCTION
  (the opposite of PD).

This extends the Clusterin "double-edged sword" pattern to augmentation
targets: a target that should be augmented in one disease may need to
be inhibited in another. The critical difference from Clusterin (where
the oncology vs. neuroscience directions are opposite) is that here
both diseases are in the SAME therapeutic area (neuroscience) — PD vs.
AD, both neurodegenerative. The paradox is more subtle and dangerous
because a MANF-based therapeutic developed for PD could be harmful if
given to an AD patient (or a patient with mixed PD/AD pathology, which
is common in elderly populations).

**Implication for field 6 (failure modes):** For targets with disease-
context-dependent dual roles WITHIN the same therapeutic area, the
headline failure mode is "wrong disease context" — the same drug given
to the wrong neurodegenerative disease population. This is more
dangerous than cross-area dual roles (oncology vs. neuroscience) because
the patient populations overlap (elderly patients with mixed pathology).

**Implication for field 11 (differentiation):** A disease-context-
specific approach (MANF augmentation for PD, anti-MANF blockade for AD)
with biomarker-based patient stratification is the key differentiation.
An anti-MANF blocking antibody for AD would be a completely novel
approach — the first antibody-mediated MANF intervention — but carries
pancreatic β-cell toxicity risk (MANF KO → diabetes).

### 5. Full-text retrieval rate for neuroscience reviews

2/8 papers (25%) retrieved as full text via PMC XML — both were open-
access reviews (Front Neurol, Int J Mol Sci). The 6 paywalled papers
were from Dev Neurobiol, Neurobiol Dis, Ageing Res Rev, Front Biosci,
Exp Neurol, Cell Rep — all subscription journals with no PMC access.

This is consistent with the BDNF profile (0/5 full text, all
paywalled neuroscience journals) and contrasts with the Nav1.8 profile
(100% via EPMC fullTextXML for recent pain/neuroscience OA papers).
Neuroscience review papers in subscription journals (Dev Neurobiol,
Neurobiol Dis, Ageing Res Rev) are consistently paywalled; the OA
reviews (Front Neurol, Int J Mol Sci, Mol Neurodegener, Cells) provided
sufficient full-text content (32K + 81K chars) for comprehensive profiling.

**Rule:** For neuroscience targets, prioritize OA review papers
(Front Neurol, Int J Mol Sci, Mol Neurodegener, Cells) for full-text
retrieval — they provide comprehensive mechanistic content. Two
good OA reviews (50K+ chars combined) are sufficient for a high-quality
profile even if all primary research papers are paywalled.

### 6. ClinicalTrials.gov search for paralog trials

ClinicalTrials.gov API v2 search for "MANF" returned 0 relevant
results (the term "MANF" matched unrelated studies — "PEA" protein,
neuromediators, ER stress in periodontal disease). Searching for
"CDNF cerebral dopamine neurotrophic factor" found the CDNF Phase I/II
trials (NCT03295786, NCT03775538).

**Rule:** When searching ClinicalTrials.gov for a target with no
clinical trials, also search for the paralog(s) — the paralog's
clinical trials provide translational evidence and delivery approach
validation. Use the full protein name, not just the gene symbol,
for clinical trial searches.
