# GPNMB Profile Observations (2026-08-16)

Clinical-trial tier, oncology (melanoma/breast cancer). 8 key papers
ingested (3/8 PMC XML OA full text: METRIC trial in NPJ Breast Cancer,
uveal melanoma in Cancers/MDPI, lung squamous in JTO Clin Res Rep; 5/8
abstract-only: Elsevier/Wiley/AACR/JCO — jina returned nav chrome or
minimal content for all). ~40K chars, 209 lines, 23 unique PMIDs cited.

## Key new patterns

### 1. ADC payload cross-resistance with prior taxane therapy

The METRIC trial (PMID 34016993) is the first profiled instance of
**payload cross-resistance** as a failure mode for an ADC. Glembatumumab
vedotin uses MMAE (monomethyl auristatin E), a microtubule inhibitor —
the same target pathway as taxanes (paclitaxel/docetaxel). All METRIC
patients had received prior taxane therapy. The post hoc analysis showed
that patients with only ONE prior taxane regimen had PFS 3.0 vs 1.9
months (HR 0.67), while the overall trial showed no benefit. This
suggests that taxane-resistant tumors are cross-resistant to MMAE.

This is a generalizable failure mode for ADCs with microtubule-inhibitor
payloads (MMAE/MMAF/maytansinoids) in tumors previously treated with
microtubule-targeting chemotherapy. For field 6 (failure modes), when
profiling an ADC target where patients have received prior taxane/vinca
therapy, explicitly analyze payload cross-resistance. The corollary:
ADCs with non-microtubule payloads (DXd/topoisomerase I, PBD/DNA
crosslinkers, immune agonists) may avoid this resistance mechanism.
Sacituzumab govitecan (SN-38 payload, anti-Trop-2) achieved 6.0 months
PFS in the same TNBC population — more than double GV's 2.9 months.

MDR1 (ABCB1/P-gp) is a known efflux pump for MMAE. This connects to the
B7-H3 observation that MMAE is a P-gp substrate (PMID 28399408) —
payload efflux is a second resistance mechanism beyond pathway
cross-resistance. Both mechanisms favor non-MMAE payloads for targets
in taxane-pretreated or P-gp-expressing tumors.

### 2. Biomarker-antibody mismatch as a trial failure mode

The METRIC trial used a goat polyclonal anti-gpNMB antibody (R&D Systems)
for IHC screening (≥25% of tumor cells positive), but the ADC used the
monoclonal antibody CR011. These may have different binding affinities
and specificities for GPNMB. The trial was designed to confirm that
gpNMB-overexpressing TNBC would benefit most — but gpNMB expression
levels showed NO association with response. Two additional biomarker-
driven studies (melanoma, osteosarcoma) showed the same lack of
association.

This is a generalizable pitfall: when the companion diagnostic antibody
differs from the therapeutic antibody, the biomarker may not predict
response because it recognizes a different epitope or has different
binding properties. For field 6, when profiling an ADC or antibody
trial, check whether the IHC/screening antibody is the same as the
therapeutic antibody. If not, note the mismatch as a potential failure
mode. For field 7 (assay systems), recommend that the companion
diagnostic use the therapeutic antibody itself (or a validated
surrogate with confirmed epitope equivalence).

### 3. CAR-T revival of a failed-ADC target

GPNMB is the first target profiled where the ADC approach failed
(glembatumumab vedotin, development suspended after METRIC) and a
different modality (CAR-T) is being revived against the same target.
Three independent CAR-T programs are in early development:
- GCAR1 (PMID 42387022): Phase 1 first-in-human in ASPS/translocation RCC
- Glioblastoma dual-compartment CAR-T (PMID 42386964): preclinical
- AI-discovered multi-cancer CAR-T (PMID 42349383): preclinical

This pattern — ADC fails, CAR-T revives — may generalize to other
failed-ADC targets where the failure was payload/delivery-specific
rather than target-specific. For field 10 (competitive landscape) and
field 11 (differentiation), when an ADC has failed, analyze whether
the failure was target-intrinsic (target invalid) or modality-specific
(wrong payload, wrong format, wrong biomarker). If modality-specific,
the target may be revivable with a different approach. GPNMB's failure
was likely modality-specific: the target is real (overexpressed,
internalizable), but the MMAE payload was cross-resistant with taxanes
and the biomarker strategy was flawed.

### 4. Dual-compartment targeting (tumor + myeloid) via CAR-T

The glioblastoma GPNMB CAR-T (PMID 42386964) is the second profiled
instance of dual-compartment targeting (after B7-H3's tumor + vasculature).
GPNMB is expressed on both glioblastoma tumor cells AND tumor-associated
macrophages (TAMs). The CAR-T achieved long-term disease control by
concomitant depletion of GPNMB+ tumor AND immunosuppressive myeloid
populations. This "collapsing tumor control and microenvironmental
reprogramming" is a distinct advantage over the ADC, which could only
kill tumor cells.

This extends the B7-H3 dual-compartment observation: the principle
generalizes beyond tumor + vasculature to tumor + immunosuppressive
myeloid cells. For any target expressed on both tumor cells and
immunosuppressive myeloid cells (TAMs, MDSCs), CAR-T or bispecific
approaches that deplete both compartments may be superior to ADCs
that target only tumor cells. Check GPNMB expression on TAMs/MDSCs
for any cancer type being profiled.

### 5. On-target normal tissue toxicity from skin and myeloid expression

GPNMB is expressed in normal skin (keratinocytes, hair follicle
melanocytes) and myeloid cells (macrophages, dendritic cells, neutrophil
precursors). The ADC produced rash (45%), alopecia (41%), and
neutropenia (28% grade 3-4) — all likely on-target. Four fatal sepsis
events (all GV arm) were preceded by neutropenia, demonstrating that
on-target myeloid toxicity can lead to fatal infectious complications.

This is a generalizable safety pattern for ADC targets with normal
tissue expression: on-target toxicity is determined by WHERE the
target is expressed in normal tissues, not just tumor selectivity.
For field 8 (safety profile), enumerate normal tissue expression
sites and predict the toxicity profile. Skin expression → rash/alopecia;
myeloid expression → neutropenia/infection risk; neural expression →
neuropathy. The therapeutic index is bounded by the tumor-to-normal
expression ratio in each tissue.

### 6. GPNMB-RYK receptor discovery — new ligand-receptor axis

PMID 41708863 (Nature 2026) identified RYK (related to receptor tyrosine
kinase) as the functional receptor for the soluble GPNMB ectodomain
(G-ECD). G-ECD binding to RYK activates ERK1/2 → PPARγ-CD36/SREBP1C
pathways. This is a newly discovered ligand-receptor pair with
therapeutic implications beyond oncology (MASH/metabolic liver disease).

For target profiling, this illustrates that a shed ectodomain can have
independent biological activity as a ligand — the target is not just a
cell-surface antigen but also a secreted signaling molecule. For
field 2 (biological mechanism), check whether the target has a
functionally active shed form. For field 11 (differentiation), a
neutralizing antibody against the shed form (blocking receptor
engagement) is a distinct mechanism from an internalizing ADC against
the membrane form.

### 7. Jina reader failure pattern for JCO and Wiley/Elsevier

Jina reader returned navigation chrome (45K chars of menu/header HTML)
for the JCO paper (PMID 25267761, DOI 10.1200/JCO.2013.52.5683) rather
than article body text. The same pattern occurred for the Wiley paper
(PMID 30690710, Cancer journal) and the Elsevier paper (PMID 28546082,
Pharmacology & Therapeutics) — jina returned <600 chars (redirect/block
page). AACR (PMID 20215530, Clin Cancer Res) returned 480 chars.

For the JCO paper, the abstract from PubMed E-utilities (efetch XML)
was self-sufficient for profile grounding — structured abstract with
Purpose/Methods/Results/Conclusion sections containing all key data
(dose, PFS, response rates). This confirms the existing observation
that rich PubMed abstracts can compensate for missing full text. The
Europe PMC esummary + efetch pipeline is the reliable first stop;
jina is a fallback, not a primary retrieval method, for these publishers.

### 8. Paradoxical target upregulation after ADC treatment

In the uveal melanoma trial (PMID 32823698), 38% of tumor samples showed
INCREASED GPNMB expression after one cycle of GV treatment. This suggests
inadequate target saturation at the 1.9 mg/kg dose — the ADC did not
fully engage or deplete the target. This is a previously unreported
pattern: the target can be upregulated in response to ADC pressure,
potentially as a compensatory mechanism.

For field 6 (failure modes) and field 7 (assay systems), when an ADC
trial includes pre/post-treatment biopsies, check for target expression
changes. If target increases after treatment, it suggests inadequate
dosing or target saturation. This has implications for dose optimization:
if the target is upregulated, higher or more frequent dosing may be
needed. The GV half-life was noted as "relatively short" (PMID 20373269),
which may have contributed to inadequate exposure.
