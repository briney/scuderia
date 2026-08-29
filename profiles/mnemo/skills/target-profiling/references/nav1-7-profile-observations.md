# Nav1.7 / SCN9A Profile Observations (2026-08-17)

Forty-seventh level-2 profile (preclinical tier, neuroscience — voltage-gated
sodium channel). Nav1.7 is a TTX-sensitive sodium channel expressed in
peripheral nociceptive neurons; one of the strongest genetically-validated
pain targets (LOF → CIP, GOF → erythromelalgia/PEPD). 7 papers ingested at
86% full-text rate (6/7: 5 PMC XML + 1 publisher-jina for MDPI; 1/7 would
have been abstract-only but all papers had PMCIDs). ~50K chars, 91 PMID
citations. working-docs/hitlist-profiles/nav1-7.md.

## Key new patterns

### 1. Antibody reproducibility crisis for conformational VSD epitopes

The SVmab1/rSVmab1 discrepancy is a novel failure mode class: a
hybridoma-derived antibody (SVmab1, PMID 24856969) showed robust Nav1.7
binding and functional blockade, but the recombinant version (rSVmab1,
produced from the published VH/VL sequences in HEK293 cells, PMID 27990272)
completely failed to bind Nav1.7 peptide, VSD protein, or cells — and
showed no specific current block. A separate Duke group (Bang 2018,
PMID 29333591) confirmed: hybridoma SVmab worked, recombinant rSVmab
showed no/weak binding.

Possible explanations: (a) sequence differences between hybridoma and
recombinant sources; (b) Nav1.7 glycosylation or β subunit expression
differences between cell lines affecting epitope accessibility; (c) β
subunits partially mask VSD paddle epitopes (documented for NaV1.2 peptide
toxins); (d) post-translational modifications not captured in published
sequences.

**Implication for profiling:** When profiling ion channel targets where
the lead antibody targets a conformational VSD epitope, field 6 (failure
modes) must include a "reproducibility risk" entry. The conformational
nature of VSD paddle epitopes makes them inherently sensitive to
production method, cell line glycosylation, and β subunit co-expression.
This is distinct from soluble-protein antibody reproducibility (where
recombinant production is generally reliable). For field 4 (antibody
landscape), note whether the antibody was hybridoma-derived or
recombinant, and whether results have been independently replicated.

Generalizes to any conformational-epitope ion channel target (VSD
paddles, ECL loops with disulfide-stabilized structure).

### 2. Biparatopic crosslinking as an affinity-boosting strategy for low-density ion channels

Ion channels have limited extracellular epitopes AND low cell surface
density, which defeats the intermolecular avidity that conventional
bivalent IgGs rely on. Monospecific anti-Nav1.7 antibodies typically show
IC50 in the 75–138 nM range — too weak for robust efficacy. The
bi-epitopic crosslinking strategy (1080-PEG7-ACDTB, PMID 39461335)
overcomes this by introducing intramolecular avidity: both arms of the
molecule bind different VSDs (VSDII + VSDIV) on the SAME channel molecule.

Key design rules discovered:
- Linker length is critical: PEG7 (~40 Å) optimal; PEG3 too short (can't
  bridge); PEG15 too long (entropic penalty)
- Cross-arm avidity is essential: the ligand must be on the opposite arm
  from the antibody binding site
- Selectivity improves: steric hindrance from the antibody conjugate
  blocks off-target engagement (ACDTB hits Nav1.2/Nav1.6 as a free
  molecule, but 1080-PEG7-ACDTB does not)
- Result: IC50 0.06 nM (2,300-fold improvement over monospecific Ab-1080),
  >1,000-fold selectivity over other Nav subtypes

**Implication for profiling:** For ion channel targets with low surface
density and limited extracellular epitopes, field 11 (differentiation)
should include biparatopic/bi-epitopic crosslinking as a format
differentiation opportunity. The approach is generalizable to any
multi-domain transmembrane protein where two non-overlapping extracellular
epitopes can be identified and bridged. The linker-length optimization
requirement is a key engineering consideration — too short or too long
both fail.

Generalizes to any ion channel, transporter, or multi-domain transmembrane
receptor with low surface density and ≥2 accessible extracellular epitopes.

### 3. Blood-nerve barrier (BNB) gating as a natural therapeutic index

Shionogi's S-151128 (PMID 42357373) demonstrated a unique safety pattern:
robust analgesia in neuropathic pain (PSNL model, BNB disrupted) with NO
effect on physiological nociception (sham side, BNB intact) and NO motor
impairment (rotarod). The BNB restricts antibody access to nociceptor
terminals under normal conditions. In neuropathic pain states (PSNL, CCI,
diabetic neuropathy), the BNB is disrupted, allowing antibody penetration.

This creates a "built-in" therapeutic index: the antibody only reaches
Nav1.7 on nociceptor terminals where the BNB is compromised (pathological
tissue), while sparing normal nociception where the BNB is intact. This is
both a safety advantage (preserves protective pain) and a potential efficacy
limitation (requires BNB disruption for efficacy, restricting the
treatable population to those with active nerve pathology).

**Implication for profiling:** For peripheral nerve targets, field 8
(safety) should document whether the BNB is intact or disrupted in the
target indication. If BNB-gated access applies, field 11 (differentiation)
should frame it as a biomarker-defined population opportunity: patients
with confirmed nerve injury (nerve conduction studies, skin biopsy for
intra-epidermal nerve fiber density, BNB permeability markers) are the
optimal population. This is analogous to the BBB-gated access concept for
CNS antibodies but for the peripheral nervous system.

Generalizes to any antibody target on peripheral nociceptor terminals
where tissue access is BNB-limited.

### 4. Exceptionally high full-text retrieval rate for neuroscience ion channel papers

6/7 papers (86%) retrieved at full text — the highest rate for any profile
in this campaign. All 6 PMC-available papers had accessible XML via PMC
E-utilities (Lee 2014 Cell, Liu 2016 F1000Research, Nojima 2016 Yonsei Med
J, Zhang 2024 Cell Rep Med, Martina 2024 Adv Sci, Bang 2018 Neurosci Bull
via EPMC PDF). Only the Yoneda 2026 Pharmaceutics paper was not in PMC.

This contrasts sharply with immunology profiles where 60-80% of papers
are paywalled. Neuroscience ion channel papers, especially those in
Cell, F1000Research, Yonsei Med J, Cell Reports Medicine, and Advanced
Science, have high PMC deposition rates. MDPI journals (Pharmaceutics)
are open access but NOT deposited in PMC, requiring jina reader on the
publisher URL.

**Implication for profiling:** When profiling neuroscience ion channel
targets, expect high full-text retrieval rates. Prioritize PMC-available
papers for the key paper set. For MDPI-published papers, use jina reader
directly on the MDPI article URL (https://www.mdpi.com/journal/volume/issue/article)
— this works reliably and returns full article text. The fetch_fulltext.py
script does not try the publisher page for papers not in PMC by default
when the EPMC gate returns inPMC=N; for MDPI, manually invoke jina.

### 5. PubMed search strategy for ion channel antibody targets

Unlike the Nav1.9 profile (where "Nav1.9 antibody[tiab]" returned only 3
results and the recommendation was to search by function), Nav1.7 has a
rich antibody literature. Multiple search queries were productive:

- "Nav1.7 antibody[tiab]" → 4 results (landmark papers)
- "sodium channel Nav1.7 antibody pain[tiab]" → 15 results (broadest,
  most productive)
- "Nav1.7 monoclonal antibody[tiab]" → 7 results (key antibody papers)
- "SCN9A antibody therapeutic[tiab]" → 0 results (gene symbol too narrow)
- "Nav1.7 selective antibody[tiab]" → 0 results

**Key lesson:** For ion channel targets WITH an antibody pipeline, search
by channel name + "antibody" or "monoclonal antibody." For targets
WITHOUT an antibody pipeline (like Nav1.9), search by function. The gene
symbol (SCN9A) + "antibody" is too narrow — use the protein name. Always
run multiple queries and combine unique results.

### 6. Peptide-antibody conjugates as a modality

The 1080-PEG7-ACDTB molecule is a peptide-antibody conjugate (PAC) — a
small-molecule Nav1.7 inhibitor (ACDTB, aryl sulfonamide) conjugated to an
anti-Nav1.7 antibody (Ab-1080) via a PEG linker. This is distinct from
both ADCs (antibody-drug conjugates, where the payload is a cytotoxic)
and bispecific antibodies (two antibody arms). The PAC modality combines
the selectivity of an antibody (VSDII targeting) with the potency of a
small molecule (VSDIV targeting) and the PK of an antibody (74.93 h
half-life).

For field 4 (antibody landscape), PACs represent a novel format that
doesn't fit neatly into the "naked IgG / ADC / bispecific / Fc-fusion /
nanobody" classification. The profile should list them as "ligand-antibody
conjugate" and note the dual-mechanism (antibody-mediated binding +
small-molecule-mediated inhibition). This modality may become more
common for ion channel targets where monospecific antibodies lack
potency.

### 7. VHH/nanobody format for ion channel targets

VHH DI-D (PMID 39206821) demonstrates that single-domain antibodies can
target ion channel extracellular loops that are inaccessible to
conventional IgGs — the small size (~15 kDa) allows cavity penetration
and recognition of conformational epitopes in the DIE3 loop that
conventional antibodies cannot reach. However, VHHs have low affinity
(µM range from naïve libraries) and short half-life (3.3 h in rats),
requiring half-life extension strategies (Fc-fusion, albumin binding,
PEGylation) for therapeutic viability.

For field 4, VHHs should be listed as a distinct format. For field 11,
VHHs offer a complementary epitope space to conventional IgGs — they can
access concave/hidden epitopes that larger antibodies cannot. A
VHH-IgG biparatopic format (VHH targeting a hidden epitope + IgG
targeting an accessible epitope) is an unexplored format for Nav1.7.

### 8. Multiple distinct mechanisms of action for Nav1.7 antibodies

Three distinct antibody mechanisms were identified:
1. **State-dependent pore modulation** (SVmab1): stabilizes closed state,
   enhanced by channel cycling. IC50 improves 6-fold from 0.1 Hz to 10 Hz.
2. **Deactivation slowing** (VHH DI-D): slows the O→C and SI→C
   transitions, reducing channel availability for subsequent APs without
   blocking current amplitude.
3. **Fast/slow inactivation modulation** (1080-PEG7-ACDTB): rightward
   shift of fast inactivation V1/2, leftward shift of slow inactivation
   V1/2, delays recovery from slow inactivation.
4. **Partial current inhibition** (S-151128): 24% current block
   sufficient to reduce neuronal firing and produce analgesia — even
   modest channel blockade, sustained over time via long antibody
   half-life, can be clinically meaningful.

A fourth mechanism — antibody-induced receptor internalization
(demonstrated for P2X3 by the same Rinat/Pfizer group, PMID 27129281)
— has not yet been demonstrated for Nav1.7 but is a potential mechanism
that would provide sustained channel depletion with infrequent dosing.

**Implication for profiling:** For ion channel targets, field 2 (effect
of blockade) and field 5 (epitope landscape) should document the specific
biophysical mechanism, not just "inhibits the channel." Different
epitopes produce qualitatively different modulatory effects (closed-state
stabilization vs deactivation slowing vs inactivation modulation), which
has implications for efficacy, state-dependency, and therapeutic index.
