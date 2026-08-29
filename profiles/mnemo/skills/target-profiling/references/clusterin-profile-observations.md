# Clusterin (CLU) profile observations

**Target**: Clusterin (CLU, apolipoprotein J, UniProt P10909)
**Tier**: preclinical (neuroscience)
**Profile**: working-docs/hitlist-profiles/clusterin.md
**Date**: 2026-08-17
**Papers ingested**: 5 (3 PMC XML, 1 publisher-jina, 1 Wayback)
**Full-text retrieval rate**: 100% (5/5)
**Unique PMIDs cited**: 6 (5 ingested + 1 from initial PubMed search)

---

## Full-text retrieval

All 5 papers retrieved at 100% — an excellent retrieval rate for a mix
that included two Neuron papers (Elsevier, typically paywalled):

- PMID 39253532 (EXCLI J, 2024): PMC XML OA (PMC11382300). 54,818 chars.
  EXCLI Journal is open-access — reliable PMC XML.
- PMID 24378367 (JAMA Neurol, 2014): PMC XML (PMC4118752, inPMC=Y,
  isOpenAccess=N, hasPDF=Y). 18,972 chars. JAMA Network papers with
  inPMC=Y can deliver full body text via PMC XML even when not OA —
  the PMC deposit includes the full text for archival purposes.
- PMID 27477018 (Neuron, 2016): publisher-jina (inPMC=N, isOpenAccess=N,
  hasPDF=N). 87,912 chars. Elsevier/Neuron resolved via DOI redirect to
  linkinghub.elsevier.com; jina reader succeeded on the resolved URL.
  This is a high-yield path for Elsevier neuroscience journals.
- PMID 40311610 (Neuron, 2025): PMC XML (PMC12181066, inPMC=Y,
  isOpenAccess=N, hasPDF=Y). 80,740 chars. Recent Neuron paper with PMC
  deposit — full body text available despite not being OA.
- PMID 27781946 (Curr Med Chem, 2016): Wayback Machine snapshot
  (inPMC=N, isOpenAccess=N). 17,379 chars. Bentham Science/EurekaSelect
  paywalled; jina blocked; Wayback CDX returned a usable snapshot.
  Consistent with the CD11a profile's Bentham Science block observation.

**Key retrieval insight**: The two Neuron (Elsevier) papers were both
retrieved — one via PMC XML (PMC deposit existed) and one via publisher-jina.
For neuroscience profiling, the PMC deposit route works for many
high-impact Elsevier papers that are not OA but have inPMC=Y. Always
check the EPMC gate for inPMC status before falling back to jina.

## PubMed metadata pitfall: DOI mismatch

PMID 40311610 (Lish et al., Neuron 2025) had a **mismatched DOI** in
PubMed metadata — the DOI 10.1186/s12859-021-04344-9 returned by PubMed
efetch XML pointed to a *Bioinformatics* article, not the Neuron paper.
The `fetch_fulltext.py` script resolved the correct paper via PMID
(not DOI), so the retrieval succeeded. However, if the DOI alone had
been used for identity resolution or full-text retrieval, it would have
fetched the wrong paper.

**Rule**: When a task brief provides both PMID and DOI, always use PMID
as the primary identifier for retrieval. Validate that the DOI resolves
to a paper with the expected title before relying on it. This is a
PubMed metadata error, not a script bug — the DOI in PubMed's XML
can be wrong for recently indexed papers. If using `fetch_fulltext.py
--doi <DOI>`, verify the retrieved text title against the expected
paper title before distillation. The PMID-first approach (which the
script supports via `--pmid <PMID>`) avoids this trap entirely.

## Key new patterns

### 1. Opposite therapeutic direction across disease areas — the "double-edged sword" pattern

CLU is the **first profiled target where the therapeutic direction for
neuroscience is the OPPOSITE of the oncology direction**. This is a new
target-class pattern distinct from the FasL "block-vs-agonize
directionality" (where direction varies by disease within the same
target class) and the IL-15 "dual-directional" pattern (agonist for
cancer immunotherapy, antagonist for autoimmunity):

- **Cancer (inhibition)**: sCLU promotes tumor survival, therapy
  resistance, and anti-apoptosis (Ku70-Bax stabilization). CLU
  inhibition (antisense: custirsen/OGX-011; antibody: AB-16B5)
  enhances chemosensitivity. The AD risk allele (reduced CLU) is
  protective in cancer; the AD protective allele (increased CLU) may
  promote cancer.
- **Neuroscience/AD (enhancement)**: CLU is neuroprotective — it
  chaperones Aβ clearance, suppresses NF-κB/astrocyte reactivity, and
  limits complement C3/C1q-driven microglial synapse phagocytosis.
  CLU risk alleles (reduced CLU expression) drive neuroinflammation
  and synapse loss. The therapeutic direction is CLU enhancement
  (agonist, stabilizer, or replacement), not inhibition.

**This is NOT the same as dual-directional targeting** (FasL, IL-15,
TrkB), where the same antibody direction is chosen for different
diseases. Here, the same target has opposite biology in different
tissues: protective in brain, pathogenic in tumors. An antibody that
inhibits CLU (the cancer paradigm) would be predicted to be harmful
in AD — and vice versa.

**For field 6 (failure modes)**: The most significant failure mode for
a neuroscience anti-CLU antibody is using the wrong direction. If the
oncology CLU-inhibition paradigm is naively translated to neuroscience,
the antibody would remove the neuroprotective chaperone and
anti-inflammatory brake, worsening neurodegeneration. The profile
must explicitly state the therapeutic direction and why it differs
from the oncology approach.

**For field 11 (differentiation)**: A CLU-enhancing antibody (agonist,
stabilizer, or CLU-Fc fusion) is a blue ocean opportunity — no one is
developing CLU-enhancing antibodies for AD. The scientific rationale
(GWAS risk = low CLU; CLU loss causes neuroinflammation/synapse loss)
supports this direction. The risk is that chronically elevating CLU
could increase cancer risk (CLU is pro-tumorigenic in oncology context),
creating a safety concern for chronic neurodegenerative disease therapy.

**Generalizes to**: Any target with tissue-specific opposite biology
(apoptosis regulators, complement proteins, growth factors). The
profile must analyze the target's function in each disease context
separately and specify whether the antibody should inhibit or enhance
for each indication.

### 2. GWAS risk allele direction directly informs antibody therapeutic direction

CLU is the **first neuroscience target where GWAS risk allele direction
(low CLU = risk) directly determines the antibody therapeutic direction
(enhancement, not inhibition)**. This is a stronger genetic-to-therapeutic
link than in prior profiles:

- AD risk allele (rs11787077-C) → reduced CLU expression in astrocytes
  → worse cognition under amyloid burden, stronger tangle-cognition
  correlation (PMID 40311610).
- AD protective allele → increased CLU expression → preserved cognition
  under high neuropathological burden; no tangle-cognition correlation
  (PMID 40311610).
- CLU deficiency (CRISPR KO/HET in iPSC astrocytes) → NF-κB activation,
  C3/C1q upregulation, microglial synapse phagocytosis, tau
  phosphorylation (PMID 40311610).
- Clu−/− mice → reduced amyloid plaque deposition (PMID 27477018,
  DeMattos et al. 2004).

The genetic evidence (risk = loss of function) directly supports the
therapeutic strategy (enhancement/replacement). This is distinct from
the IL-7Rα pattern, where strong GWAS validation did NOT translate to
clinical success because the therapeutic window was too narrow — for
CLU, the genetics suggest the *direction* (enhance), but the feasibility
(agonist antibody engineering, BBB penetration, cancer risk) remains
untested.

**For field 3 (disease evidence)**: When GWAS risk allele direction is
known (increased vs. decreased expression), state the implied
therapeutic direction in the evidence summary. Risk = loss-of-function
→ enhancement strategy; risk = gain-of-function → inhibition strategy.
This is a direct, citable link from human genetics to antibody design
that should be made explicit in every profile where GWAS data exist.

### 3. Contradictory human biomarker evidence — the Desikan paradox

The Desikan et al. 2014 study (PMID 24378367) presents a **paradoxical
finding** that complicates the CLU enhancement hypothesis: elevated CSF
clusterin + high brain amyloid (low CSF Aβ1-42) was associated with
*increased* entorhinal cortex atrophy in nondemented older individuals.
This suggests clusterin may *accelerate* Aβ-associated neurodegeneration
rather than purely protect — the opposite of the Lish et al. 2025
finding (CLU loss is deleterious).

This is NOT a contradiction that invalidates the target — the two
studies measure different things:
- Desikan: elevated CSF CLU correlates with atrophy in the presence
  of high amyloid (observational, may be a response to pathology, not
  a cause).
- Lish: CLU deficiency causes neuroinflammation/synapse loss
  (mechanistic, genetic + iPSC + mouse).

**For field 6 (failure modes)**: When human biomarker evidence
(observational, elevated CLU = more atrophy) appears to contradict
mechanistic/genetic evidence (CLU loss = worse outcomes), the profile
must present both and explain the apparent paradox. The observational
study may measure CLU as a *marker* of disease stress (upregulated in
response to pathology), while the genetic/mechanistic studies establish
the *causal* role (CLU loss worsens disease). The profile should note
that observational confounding limits causal inference from biomarker
studies — a recurring issue for neuroscience targets.

### 4. Secreted chaperone as antibody target — no surface engagement needed

CLU is a **secreted glycoprotein**, not a cell-surface receptor. This
is the first neuroscience profile where the antibody target is entirely
in the extracellular space (plasma, CSF, brain interstitium). This has
several implications:

- **Antibody accessibility is maximal** — no BBB penetration for target
  engagement needed (the target is in the CSF/interstitium, not
  intracellular). However, the *antibody* must still cross the BBB to
  reach the target in the brain parenchyma.
- **No ADCC/CDC mechanism possible** (target is not cell-surface) —
  the antibody can only function as a modulator (inhibit, stabilize,
  or enhance CLU's chaperone activity), not as a depleting antibody.
- **Epitope landscape is conformation-dependent** — CLU exists in
  lipidated (HDL-associated, TREM2-binding) and lipid-free states with
  different epitope exposure. An antibody must be characterized in
  both states.
- **CLU-Fc fusion or recombinant CLU supplementation** is a viable
  alternative modality — since the target is secreted, simply
  delivering more functional CLU (rather than an antibody) is a
  therapeutic option. This is analogous to enzyme replacement therapy
  and is not available for cell-surface targets.

### 5. High full-text retrieval rate for neuroscience profiles continues

This is the third consecutive neuroscience profile (after BDKRB2 and
TrkB) with a high full-text retrieval rate (100% for CLU and TrkB;
partial for BDKRB2). The neuroscience journal mix (EXCLI J, JAMA
Neurology, Neuron, Current Medicinal Chemistry) has favorable PMC
deposit rates — JAMA Neurology and Neuron both had inPMC=Y despite
not being OA, and the PMC XML delivered full body text. This confirms
the BDKRB2/TrkB observation that neuroscience OA journals and
PMC-deposited subscription journals have very high full-text
retrieval rates for delegated profiling.

(Clusterin/CLU profile, ~28K chars, 5 papers ingested (5/5 full text),
6 PMIDs cited, working-docs/hitlist-profiles/clusterin.md.)
