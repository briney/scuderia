# Tau (MAPT) profile observations — 2026-08-16

Thirty-ninth level-2 profile (clinical-trial tier, neuroscience — AD/PSP/FTD).
Tau is the **first intracellular aggregation target** profiled and the
**first neuroscience multi-antibody graveyard** — 6 N-terminal anti-tau
antibodies (semorinemab ×2, tilavonemab ×2, gosuranemab ×2) plus 1
conformational antibody (zagotenemab) all failed Phase 2, despite robust
target engagement. 10 papers ingested (5/10 Europe PMC OA XML for clinical
trial papers; 5/10 abstract-only for reviews/preclinical/Phase 1).
~37K chars, 14 unique PMIDs cited.

## Key new patterns

### 1. Epitope-dependent graveyard — all N-terminal antibodies failed, MTBR antibodies are promising

All three N-terminal anti-tau antibodies (semorinemab residues 6–23,
gosuranemab, tilavonemab) failed Phase 2 in both AD and PSP, despite
achieving 80–98% reduction in CSF free (unbound) tau — confirming robust
target engagement. The conformational antibody (zagotenemab, N-terminus +
MTBR) also failed. The problem is NOT insufficient dosing or target
engagement — it is the wrong epitope.

The N-terminal epitope is NOT on the aggregation-prone region. N-terminal
antibodies bind abundant full-length tau and soluble fragments but do
NOT detect truncated tau species lacking the N-terminus — and truncated
C-terminal fragments containing the MTBR are the most aggregation-prone
and seeding-active species. MTBR-tau fragments are rare in CSF (~1.8
ng/mL) vs N-terminal/midregion fragments (8.2–32.0 ng/mL). N-terminal
antibodies engage the most abundant but least pathogenic pool.

By contrast, etalanetug (E2814), which targets the MTBR (the
aggregation/seeding interface), showed the first pharmacodynamic effects
on BOTH hyperphosphorylated tau (57.9% reduction in CSF ptau217) AND
tangle pathology (71.6% reduction in MTBR-tau243) in dominantly
inherited AD. This is the first anti-tau antibody to show biomarker
effects on tau tangle pathology — a fundamental difference from the
N-terminal antibodies, which reduced CSF free tau but had NO effect on
tau PET pathology.

**Generalizable pattern:** When a target has multiple epitope bins and
antibodies targeting one epitope bin all fail despite target engagement,
the epitope — not the target — is the failure mode. This is distinct
from the dual-purpose target pattern (CD4: isotype/epitope determines
success vs failure across indications) because here all antibodies target
the same indication and the same format (IgG4), varying only the epitope.
The epitope-dependent graveyard analysis is the most important output of
field 6 for multi-antibody graveyard targets.

For field 5 (epitope landscape): explicitly map which epitope bins have
been tested and which have failed vs which are unexplored. The "competing
epitope bins" sub-field becomes a failure analysis tool, not just a
classification.

For field 6: structure the failure analysis as an epitope-by-epitope
comparison table (antibody × epitope × target engagement × clinical
outcome) — this is more informative than a flat list of failures.

### 2. The intracellular compartment problem — targeting the wrong pool

Tau is primarily an intracellular protein. Neurofibrillary tangles are
inside neurons. Anti-tau antibodies target extracellular tau (the
hypothesized spreading species), but extracellular tau is a minor
fraction of total brain tau. If intracellular tau is the primary driver
of neurodegeneration, extracellular-only targeting is fundamentally
insufficient.

This is the most fundamental mechanistic difference between the
anti-Aβ and anti-tau stories. Aβ plaques ARE extracellular — the
pathological species is directly accessible to antibodies in the brain
parenchyma. Tau tangles are intracellular — the pathological species is
NOT accessible to standard antibodies without neuronal entry.

**Generalizable pattern:** For any target where the pathological species
is primarily intracellular (tau, α-synuclein, TDP-43, huntingtin), the
antibody must either: (1) be engineered for enhanced neuronal uptake
(charge modification, as proposed in PMID 34896021); (2) target a
mechanism that indirectly clears intracellular aggregates (e.g.,
blocking extracellular spread to prevent seeding of new intracellular
aggregates); or (3) use a non-antibody modality (gene therapy, PROTACs,
small molecules, intrabodies). The "extracellular-only targeting is
insufficient" hypothesis is now supported by 7 clinical failures.

For field 2 (biological mechanism): explicitly state whether the
pathological species is intracellular, extracellular, or both, and what
fraction of total target is in each compartment. This determines whether
extracellular antibody targeting can work at all.

For field 9 (structural information): note whether the epitope is
accessible on the pathological aggregate (the MTBR is buried inside
PHFs, potentially limiting antibody access to the aggregate itself) or
only on released fragments.

### 3. The Aβ vs tau graveyard comparison — compartment determines success

The anti-Aβ and anti-tau antibody fields developed in parallel in AD,
with starkly different outcomes:
- **Anti-Aβ:** Multiple early failures (bapineuzumab, solanezumab,
  crenezumab, gantenerumab), but eventual success (lecanemab approved
  2023, donanemab approved 2024). The target IS extracellular (plaques,
  protofibrils) — antibodies can directly access the pathological species.
- **Anti-tau:** 7 clinical failures, no success. The target is primarily
  intracellular (tangles) — antibodies can only access the minor
  extracellular fraction.

The Aβ graveyard was "eventually solvable" because the target was in the
right compartment. The tau graveyard may be "fundamentally harder"
because the target is in the wrong compartment. However, the epitope
hypothesis (N-terminal = wrong, MTBR = untested in Phase 3) and the
timing hypothesis (symptomatic patients too advanced) remain open. The
MTBR-targeting antibodies (etalanetug) and mid-domain antibodies
(bepranemab) may yet succeed where N-terminal antibodies failed.

**Generalizable pattern:** When profiling an antibody graveyard, compare
to a parallel field that eventually succeeded (or is further along).
Identify the structural/biological difference that explains the divergent
outcomes — this is the highest-value analysis in field 6. The comparison
should be explicit and structured, not implicit.

For field 6: include a comparison table of the graveyard target vs the
parallel successful field, with columns for: target compartment
(intracellular vs extracellular), epitope bins tested, clinical outcomes,
and the mechanistic explanation for divergence.

### 4. Preclinical-to-clinical translational failure — P301L mouse models don't predict human outcomes

All N-terminal antibodies and zagotenemab showed efficacy in tau
transgenic mouse models (P301L/P301S) — reducing tau pathology and
improving behavioral measures. None of this translated to human clinical
benefit. Root cause: P301L/P301S models express human mutant tau with
FTD mutations under exogenous promoters, producing 4R tau pathology that
does not model the mixed 3R/4R tau pathology of AD. The brain-derived
tau seeds used in spreading models are mainly from intracellular
aggregates, which may not represent the extracellular species accessible
to antibodies in humans.

**Generalizable pattern:** For neuroscience antibody targets, the
preclinical-to-clinical translational gap is larger than for any other
therapeutic area. Mouse models of neurodegeneration (transgenic
overexpression of mutant human proteins) may not predict human efficacy
because: (1) the mutations are FTD-specific, not AD-specific; (2) the
tau isoform ratio differs (4R-only vs mixed 3R/4R); (3) the promoter
drives expression in regions not typically affected in AD; (4) the
spreading model uses intracellular-derived seeds, not extracellular
species. For field 7 (assay systems), note the translational limitations
of each model. For field 6, the preclinical-to-clinical gap is a
systematic failure mode, not a per-antibody one.

### 5. Disease stage paradox — possible benefit at later stage (Lauriet)

Semorinemab failed in prodromal-to-mild AD (Tauriel, no effect on any
endpoint) but showed a partial cognitive signal in mild-to-MODERATE AD
(Lauriet: 42.2% reduction in ADAS-Cog11 decline, P=0.0008) — though not
on functional or global outcomes. This is paradoxical: if the mechanism
is preventing tau spread, earlier intervention should be better, not
later. The possible explanation: in later-stage AD, there may be more
extracellular tau release from degenerating neurons, making the
extracellular pool larger and more targetable. Or the cognitive signal
is a chance finding. This pattern differs from the Aβ story (earlier is
better) and complicates the disease-stage hypothesis.

**Generalizable pattern:** For antibody graveyard targets, check
whether any dose, endpoint, or disease stage showed a partial signal —
even in an overall negative trial. A partial signal in one subpopulation
or endpoint can define the conditions under which the target might work,
informing field 11 (differentiation) and future trial design.

### 6. PMC ID converter API is more reliable than elink for PMC ID resolution

The NCBI elink API (`elink.fcgi?dbfrom=pubmed&db=pmc`) returned
incorrect results — hundreds of PMC IDs per PMID, when each paper has
only one. The NCBI ID Converter API (`/pmc/utils/idconv/v1.0/`) correctly
resolved PMIDs to PMCIDs and DOIs. This is a tool-usage pattern relevant
to the paper-ingest pipeline.

### 7. Europe PMC fullTextXML API is a reliable full-text source

The Europe PMC RESTful API (`/webservices/rest/{PMCID}/fullTextXML`)
retrieved full text XML for 4/5 PMC-available papers (80% success rate).
This is a more reliable source than the NCBI PMC OA service for papers
with PMC IDs but not in the PMC OA subset. The returned XML parsed
cleanly with ElementTree (no entity issues, no DOCTYPE problems).

(Tau profile, ~37K chars, 10 papers ingested, 14 unique PMIDs cited,
working-docs/hitlist-profiles/tau.md.)
