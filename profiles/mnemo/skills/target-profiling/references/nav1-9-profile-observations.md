# Nav1.9 (SCN11A) profile observations — 2026-08-17

Preclinical-tier neuroscience target. Voltage-gated sodium channel Nav1.9
(encoded by SCN11A, UniProt Q9UI33) — a TTX-resistant channel preferentially
expressed in peripheral nociceptive neurons. 8 papers ingested (3/8 full
text: Huang 2017 JCI via EPMC PDF, Dib-Hajj 2015 Nat Rev Neurosci + Leipold
2013 Nat Genet via jina reader; 5/8 abstract-only: Wiley, Elsevier, JGP all
paywalled). ~27K chars profile, 57 PMID citations,
working-docs/hitlist-profiles/nav1-9.md.

## Key new patterns

### 1. Ion channel target — no antibody pipeline at all, small-molecule-dominated landscape

Nav1.9 is the first profiled target where the entire therapeutic landscape
is small-molecule channel blockers, with zero therapeutic antibodies in
development or clinical trials. The only antibodies raised against Nav1.9
are research tools (polyclonal peptide antibodies for immunolocalization,
PMID 10683857). This is distinct from the "no antibody attempted but
mechanism suggests potential" blue-ocean pattern — here the target is an
ion channel (transmembrane protein with extracellular loops), and the
therapeutic approach is fundamentally pharmacological (pore blockade,
VSD modulation) rather than immunological.

For field 4 (antibody landscape), the entry should list the research
antibody and explicitly state "No therapeutic antibodies in development."
For field 10 (competitive landscape), the pipeline depth is 0 for antibodies
but non-zero for small molecules (ANP-230, pan-Nav blocker, PMID 40633498;
suzetrigine/VX-548, Nav1.8 selective, FDA-approved for acute pain, PMID
40601424). For field 11 (differentiation), the framing is "why would an
antibody be better than small molecules" — answer: (1) inherent subtype
selectivity (antibodies can discriminate Nav1.9 from Nav1.8 based on
extracellular loop differences, whereas small molecules struggle with
pore conservation), (2) long half-life, (3) peripheral restriction by
design (antibodies don't cross BBB, eliminating CNS side effects).

This pattern generalizes to any ion channel target where the therapeutic
landscape is exclusively small-molecule. The VSD-targeting antibody
approach (validated for Nav1.7 by Lee et al. 2014, Cell, ref 63 in PMID
26243570) is the proof-of-concept that antibodies CAN functionally block
voltage-gated channels — but it has not been extended to Nav1.9 or any
other Nav channel in a therapeutic context.

### 2. Biphasic dose-response from human genetics — U-shaped excitability curve

Nav1.9 is the first profiled target where human genetics reveals a biphasic
relationship between target activity and disease phenotype. Gain-of-
function mutations cause BOTH pain (familial episodic pain, painful
neuropathy) AND insensitivity to pain (congenital insensitivity to pain),
depending on the magnitude of the functional effect. The mechanism is a
U-shaped relationship between resting membrane potential and current
threshold (PMID 28530638):

- Small depolarizations (~4-6 mV) → hyperexcitability → pain
- Large depolarizations (~8-12 mV) → inactivation of other NaV channels
  (including Nav1.8) → hypoexcitability → insensitivity to pain

For field 6 (failure/success modes), the biphasic curve is a distinct
failure class — "mechanism-of-action non-linearity." An antibody that
overshoots blockade could paradoxically cause insensitivity to pain
(a safety concern, though less severe than self-injury seen in complete
genetic loss). The therapeutic window is between "reduces pain" and
"eliminates pain sensation entirely."

For field 8 (safety), the on-target toxicity of excessive Nav1.9 blockade
is insensitivity to pain with risk of unrecognized injury. This is
manageable through dose titration but is a unique safety profile compared
to most antibody targets where more blockade = more efficacy.

For field 11 (differentiation), a state-dependent antibody targeting the
inactivated conformation could preferentially block hyperactive channels
(inflammatory/painful state) while sparing resting-state channels — a
functional selectivity mechanism impossible for state-independent small
molecules. This could widen the therapeutic index.

This pattern generalizes to any target where the dose-response is
non-monotonic — the "more is better" assumption breaks down.

### 3. Poor human-mouse ortholog conservation complicating preclinical translation

Human and mouse Nav1.9 share only ~73% amino acid identity, which is
notably lower than other mammalian sodium channel orthologs (typically
>90% for Nav1.1-1.8). This was explicitly noted in PMID 28530638, where
functional differences between human L811P and mouse L799P orthologous
mutations confounded direct comparisons (differences in inactivation
kinetics, current density, and voltage dependence).

For field 2 (species cross-reactivity notes), this is the first profiled
target where the cross-species sequence identity is explicitly called out
as a translation risk in the primary literature. For antibody development,
epitope conservation between human and rodent/cyno needs careful evaluation
— an epitope on the extracellular loops of human Nav1.9 may not be present
on mouse Nav1.9, complicating preclinical efficacy studies.

This pattern generalizes to any target with unusually low cross-species
conservation. For ion channels, the extracellular loops (the only
antibody-accessible regions) are the most variable domains — the
transmembrane segments and pore are more conserved. This means the
antibody-accessible epitopes are the LEAST conserved parts of the protein.

### 4. Nature Reviews articles via jina return references list, not body text

The Dib-Hajj 2015 Nature Reviews Neuroscience review (PMID 26243570,
DOI 10.1038/nrn3977) was fetched via jina reader (publisher-jina
provenance, 42K chars). However, the content was the references list
(numbered citations with links), NOT the review body text. The review
body is behind the Nature paywall. The jina reader successfully fetched
the page but returned the openly accessible references section, not
the paywalled body.

This extends the "Nature subscription articles return abstract + figures
via jina, not body text" observation from the IL-35 profile. For Nature
Reviews articles specifically, the jina output may be primarily the
reference list, which is still useful — it provides the bibliography
of key papers for the target, even without the synthesis text.

For target profiling, when a Nature Reviews review is fetched via jina
and the content is mostly numbered references, extract the reference
list as a bibliography guide (it identifies the landmark papers the
review authors considered most important) and rely on PubMed abstracts
for the actual content. The reference list from a high-quality review
is a valuable paper-discovery tool even without the body text.

### 5. PubMed DOI field errors — JCI paper with wrong DOI

PMID 28530638 (Huang 2017, J Clin Invest) had a PubMed esummary DOI field
showing "10.1038/nprot.2009.90" (a Nature Protocols DOI) instead of the
correct "10.1172/JCI92373". This is a PubMed metadata error, not a
retrieval error. The EPMC gate and full-text retrieval via PMID worked
correctly (EPMC PDF render returned 60K chars of full text via PMCID
PMC5490760).

For target profiling, always cross-check the DOI against the journal:
if the DOI prefix doesn't match the publisher (e.g., 10.1038 for a JCI
paper), the PubMed DOI field is wrong. Use the PMID for retrieval
(which is reliable) rather than the DOI when the DOI looks suspicious.
The EPMC gate uses PMID by default and is unaffected by DOI errors.

### 6. PubMed search strategy for ion channel targets — multiple synonym queries needed

Nav1.9 has multiple names in the literature: "Nav1.9", "NaN", "SCN11A",
"voltage-gated sodium channel type IX alpha". A single PubMed search
misses papers using alternate nomenclature. The effective search strategy
was 3 separate queries:

1. `Nav1.9 antibody[tiab]` — 3 results (papers using the modern nomenclature)
2. `SCN11A antibody[tiab]` — 3 results (papers using the gene symbol)
3. `sodium channel Nav1.9 pain[tiab]` — 15 results (broader functional query)

The broader functional query (#3) was the highest-yield, returning the
most clinically relevant papers. The narrow antibody-specific queries
(#1, #2) returned very few results (3 each) because no therapeutic
antibodies exist — the antibody-specific search terms mostly hit
research antibody characterization papers.

For ion channel targets with no antibody pipeline, search by function
("pain", "inflammatory", "channel blocker") rather than by "antibody" —
the literature is about the biology and small-molecule pharmacology, not
antibodies. Also search for the historical name (NaN for Nav1.9) if the
channel was renamed.

### 7. VSD-targeting antibody precedent for Nav channels

The Lee et al. 2014 Cell paper (ref 63 in PMID 26243570) describes a
monoclonal antibody targeting the Nav1.7 voltage sensor domain (VSD)
for pain and itch relief. This is the only published example of a
functional blocking antibody against a voltage-gated sodium channel.
It was cited in the Dib-Hajj 2015 Nav1.9 review as a proof-of-concept
for the antibody approach to Nav channels.

For Nav1.9 profiling, this precedent is critical for field 11
(differentiation opportunities): the VSD-targeting approach is
validated for Nav1.7 but unexplored for Nav1.9. The four VSDs (DI-DIV)
of Nav1.9 each offer distinct epitope opportunities, and the extracellular
loops of the VSDs (S1-S2, S3-S4) are subtype-variable and antibody-
accessible. A state-dependent anti-VSD antibody could achieve preferential
blockade of the activated or inactivated state.

This generalizes to the broader ion channel antibody space: VSD-targeting
is the validated approach for functional blockade of voltage-gated channels
by antibodies, analogous to how the pore-targeting approach works for
small molecules.
