# IGF-2 profile observations (2026-08-16)

Forty-sixth level-2 profile (preclinical tier, oncology — secreted growth factor).
IGF-2 (Insulin-like growth factor 2, IGF2) is a 7.5-kDa secreted peptide
growth factor, the first profiled target where the **entire antibody pipeline
exists as a response to receptor-targeting antibody failures**.

3 landmark papers ingested via PubMed search queries "IGF-2 antibody",
"anti-IGF-2 cancer", "IGF2 growth factor tumor" — all 3 retrieved as full
text via PMC XML (100% retrieval rate). ~21K-char profile, 48 PMID citations
across 3 ingested papers.

## Papers ingested

1. **PMID 25924852** — Zhao et al. 2015, Int J Cancer: m708.5 dual
   IGF-1/IGF-2 antibody in neuroblastoma (PMC XML, 26K chars)
2. **PMID 32054790** — Weyer-Czernilofsky et al. 2020, Mol Cancer Ther:
   Xentuzumab (BI 836845) + enzalutamide in prostate cancer (PMC XML, 25K chars)
3. **PMID 31623387** — Kasprzak & Adamek 2019, Int J Mol Sci: IGF2 signaling
   in colorectal cancer review (PMC XML, 55K chars)

## Key new patterns

### 1. Ligand neutralization as the response to receptor-targeting failures

IGF-2 is the first profiled target where the antibody pipeline exists
**because** receptor-targeting antibodies failed. Over 30 anti-IGF-1R
antibodies entered clinical trials; ALL failed. Two failure mechanisms:
(a) IGF-2 mediates escape via IR-A (insulin receptor isoform A) — when
IGF-1R is blocked, IGF-2 activates IR-A as a compensatory survival pathway;
(b) hyperglycemia from disrupting IGF-1R/IR hybrid receptors that regulate
glucose homeostasis.

The ligand-neutralization strategy (xentuzumab, m708.5, MEDI-573) addresses
both failures: (a) sequestering IGF-1 AND IGF-2 simultaneously blocks both
IGF-1R and IR-A activation, aborting the escape mechanism; (b) by not
binding insulin or INSR-B, the antibodies preserve metabolic signaling,
avoiding hyperglycemia.

**Generalizable to any receptor-ligand system where:** (1) receptor-targeting
antibodies failed clinically, (2) the ligand activates multiple receptors
(creating escape pathways), (3) the ligand is a soluble secreted protein
(antibody-accessible). The strategy is to neutralize the shared ligand rather
than target individual receptors.

For field 6 (failure modes), the anti-IGF-1R failures are a distinct class:
"receptor-targeting escape via ligand-mediated alternative receptor
activation." For field 11 (differentiation), the ligand-neutralization
approach IS the differentiation — it's not a minor format variation but a
fundamentally different strategy.

### 2. Imprinted gene overexpression as disease mechanism + biomarker

IGF-2 is the first gene discovered to be parentally imprinted, and the first
profiled target where **epigenetic dysregulation (loss of imprinting, LOI)**
is the primary mechanism of disease overexpression. LOI occurs in 30-88% of
CRC tumors and 20-70% of adjacent normal mucosa. Other mechanisms: gene
amplification (7% of CRC), enhancer-hijacking (>250-fold upregulation),
reactivation of fetal promoters.

This creates a unique biomarker opportunity: IGF2 LOI is detectable by
methylation-specific PCR in blood and tissue. For field 3 (disease evidence),
"epigenetic overexpression via LOI" is a distinct evidence type alongside
human genetics, clinical success/failure, and preclinical data. For field 7
(assay systems), methylation-specific PCR for IGF2 LOI is a companion
diagnostic candidate. For field 11, patients with IGF2 LOI-positive tumors
are a biomarker-defined subset for anti-IGF-2 therapy.

**Generalizable to any imprinted gene target** (IGF2, H19, CDKN1C/p57KIP2,
DLK1, MEG3, PEG3) where loss of imprinting drives overexpression in cancer.

### 3. Mol Cancer Ther is PMC XML-retrievable (refines IL-35 observation)

The IL-35 profile observation states: "AACR journals (Mol Cancer Ther) are
Cloudflare-blocked for jina reader." PMID 37988561 returned a Cloudflare
CAPTCHA page via jina reader (Branch 2 of fetch_fulltext.py).

The IGF-2 profile retrieved PMID 32054790 (Weyer-Czernilofsky 2020, Mol
Cancer Ther) as full text via **PMC XML** (Branch 1) — 25K chars, provenance
`pmc-xml`, PMCID PMC10823795. The Europe PMC gate showed `inPMC=Y,
isOpenAccess=N, hasPDF=Y`.

**Refinement:** The Cloudflare block on AACR journals is **path-specific
(jina reader / publisher page), not journal-wide.** When `inPMC=Y`, the
PMC E-utilities XML path (Branch 1) retrieves the full text regardless of
publisher Cloudflare protection — it queries NCBI's PMC server, not the
publisher's website. The block only prevents Branch 2 (publisher-jina)
and potentially Branch 1b (EPMC PDF, which redirects through the publisher).

**Actionable rule:** For Mol Cancer Ther papers, always check the Europe PMC
gate first. If `inPMC=Y`, use PMC XML — the Cloudflare block is irrelevant.
Only if `inPMC=N` should you tag as abstract-only. This applies more broadly:
any journal with Cloudflare protection (AACR, potentially others) is
retrievable via PMC XML when a PMCID exists.

### 4. Dual-specific antibody pipeline with no monospecific antibody

Every disclosed IGF-2 antibody (xentuzumab, m708.5, MEDI-573) is dual
IGF-1/IGF-2 cross-reactive. There are ZERO monospecific anti-IGF-2
antibodies in the pipeline. This creates a clear differentiation gap:

- IGF-1 is GH-regulated with broad physiological roles (less tumor-specific)
- IGF-2 overexpression is a more cancer-specific event (LOI, amplification)
- A monospecific anti-IGF-2 antibody could avoid unnecessary IGF-1
  neutralization, potentially improving therapeutic index
- The IGF-2 C-domain differs from IGF-1 and mediates IR-A selectivity —
  targeting the C-domain could selectively block IGF-2/IR-A while sparing
  IGF-1/IGF-1R

For field 10 (competitive landscape), state "no monospecific anti-IGF-2
antibody in development" explicitly. For field 11 (differentiation), the
monospecific approach is the primary differentiation opportunity.

**Generalizable to any shared-ligand system** where a dual-specific antibody
dominates the pipeline: the monospecific alternative is always a
differentiation gap worth noting, especially when the two ligands have
different physiological roles and different disease-association profiles.

### 5. Soluble ligand epitope accessibility in circulation

IGF-2 circulates at 400-700 ng/mL (the predominant IGF in adults, 3.5×
higher than IGF-1), largely bound in 150-kDa ternary complexes with IGFBP3
and ALS. For field 5 (epitope landscape) and field 9 (structural
information), this creates a unique epitope accessibility challenge:

- Antibody must access IGF-2 within or displace from IGFBP3/ALS complexes
- Free (bioavailable) IGF-2 and tumor-microenvironment IGF-2 (autocrine/
  paracrine, less IGFBP-complexed) may be more accessible
- "Big IGF2" (partially processed, 10-18 kDa) is tumor-enriched and may
  present different epitope surfaces
- No PDB structures of IGF-2 bound to neutralizing antibodies exist

This is distinct from membrane-proximal epitope accessibility (relevant for
cell-surface receptors). For soluble ligand targets, the binding-protein
complex is the epitope-accessibility barrier, not the membrane environment.

**Generalizable to any secreted growth factor/cytokine that circulates
bound to carrier proteins** (IGF-1/IGFBP3/ALS, VEGF/α2-macroglobulin,
TGF-β/latent-TGF-β-binding protein). For field 9, document the circulating
complex and its implications for antibody access.

## Profile stats

- IGF-2 profile: ~21K chars, 11 fields, no frontmatter
- 3 papers (3/3 full text via PMC XML — 100% retrieval rate)
- 48 PMID citations (18 + 14 + 16 across the three PMIDs)
- Tier: preclinical | Area: oncology
- working-docs/hitlist-profiles/igf-2.md
