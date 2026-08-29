# CCL13/MCP-4 Profile Observations (2026-08-16)

Forty-fifth level-2 profile (preclinical tier, immunology). CCL13/MCP-4
is a secreted CC chemokine that binds CCR2 and CCR3 (plus CCR1, CCR5,
CCR11), recruiting monocytes, eosinophils, basophils, and immature
dendritic cells. 3 landmark papers ingested (2/3 full text: PMID 9062350
via EPMC PDF 66K chars, PMID 37153575 via PMC XML 44K chars; 1/3
abstract-only: PMID 8955214, J Immunol 1996, paywalled, no PMCID).
~37K chars profile, 111 PMID citations, 3 paper pages created.

## Paper retrieval summary

| PMID | Journal | Year | Full text? | Source |
|------|---------|------|------------|--------|
| 8955214 | J Immunol | 1996 | Abstract-only | Paywalled, no PMCID, not in PMC |
| 9062350 | J Clin Invest | 1997 | Yes (66K chars) | EPMC PDF |
| 37153575 | Front Immunol | 2023 | Yes (44K chars) | PMC XML |

Retrieval rate: 2/3 full text (67%), 1/3 abstract-only (33%).

## Key new observations

### 1. Absence of a mouse ortholog as a preclinical development barrier

CCL13 is absent in mice — the mouse MCP family includes CCL2/MCP-1,
CCL7/MCP-3, CCL8/MCP-2, and CCL12/MCP-5, but no CCL13 equivalent. This
is the first profiled target where the absence of a mouse ortholog
completely blocks standard preclinical antibody evaluation (PK, efficacy,
toxicity in mouse disease models). This is a distinct challenge from
species cross-reactivity (where the ortholog exists but differs) — here
there is no ortholog at all.

**Implications for profiling:**
- Field 2 (species cross-reactivity): explicitly state "no mouse
  ortholog exists" rather than "no data on mouse cross-reactivity" —
  these are fundamentally different statements with different
  implications for preclinical development.
- Field 7 (assay systems): note that standard mouse disease models
  cannot be used; humanized mouse models, CCL13 overexpression models,
  or non-human primate studies are required.
- Field 6 (failure modes): the lack of mouse models is a preclinical
  development risk that increases cost and complexity — include it as
  a distinct failure mode category for targets without mouse orthologs.
- Field 11 (differentiation): if a mouse surrogate model has been
  developed (e.g., using a related chemokine like CCL2 or CCL7 in
  mice), note it as a workaround.

**Generalization:** This applies to any human-specific protein without
a mouse ortholog (e.g., some human-specific cytokines, complement
components, or immune molecules). When filling field 2, always check
for the existence of a mouse ortholog via UniProt or Ensembl — its
absence is a major preclinical development finding, not a minor note.
(CCL13 profile, 2026-08-16.)

### 2. DOI recovery from Europe PMC when PubMed XML returns None

PMID 8955214 (Garcia-Zepeda 1996, J Immunol) had no DOI in PubMed XML
(`<ELocationID EIdType="doi">` absent, `<ArticleId IdType="doi">`
absent). Europe PMC core record carried the DOI: `10.4049/jimmunol.
157.12.5613`. This is a known paper-ingest pattern (EPMC as metadata
fallback) but has a profiling-specific implication: when constructing
the paper page frontmatter for older papers (pre-2000), always check
EPMC for the DOI even when PubMed XML returns None — the DOI is needed
for the profile's citation trail and for any future full-text retrieval
attempt via jina on the DOI URL.

**Pattern:** PubMed XML DOI = None → EPMC core record `doi` field →
use EPMC DOI in paper page frontmatter. The EPMC gate (Branch 0 of
fetch_fulltext.py) always fetches the EPMC core record first for
PubMed papers, so the DOI is available for free. (CCL13 profile,
2026-08-16, PMID 8955214.)

### 3. Proteomic-transcriptomic discrepancy as a target confidence pitfall

The comprehensive CCL13 review (PMID 37153575) explicitly notes that
CCL13 mRNA expression is upregulated in various diseases, but
protein-level expression has rarely been validated, and studies show
inconsistency between proteomics and transcriptomics. This is the
first profiled target where this discrepancy is called out as a
systematic issue affecting target confidence across ALL disease
evidence.

**Implications for profiling:**
- Field 3 (disease evidence): when disease associations are based on
  mRNA data (RT-PCR, microarray, RNA-seq), note whether protein-level
  validation (ELISA, IHC, Western blot, proteomics) has been performed.
  If only mRNA data exists, the disease evidence is weaker than it
  appears — the target protein may not be elevated in disease tissue
  even if the mRNA is.
- Field 6 (failure modes): proteomic-transcriptomic discrepancy is a
  distinct failure mode for antibody targets — an antibody targets
  the PROTEIN, so if the disease association is only at the mRNA level,
  the antibody may not show efficacy because the protein is not
  elevated.
- Field 7 (assay systems): recommend protein-level biomarker assays
  (ELISA) rather than mRNA-based assays for patient stratification.

**Generalization:** This applies to any target where disease evidence
is primarily transcriptomic. The CCL13 review's explicit warning
("research based on mRNA of CCL13 should be supported by protein
analysis to establish convincing conclusions") is a generalizable
principle: mRNA-based disease associations require protein-level
validation before an antibody development program can confidently
target the protein. (CCL13 profile, 2026-08-16, PMID 37153575.)

### 4. Chemokine-derived peptide as proof of concept for ligand blockade

CDIP-2 (chemokine-derived inhibitory peptide 2), a synthetic peptide
derived from CCL13, ameliorates allergic airway inflammation by acting
as a competitive antagonist at CCR1, CCR2, and CCR3 (PMID 37153575).
This is the first profiled target where a derivative of the target
protein itself (rather than an exogenous antibody or small molecule)
demonstrates therapeutic efficacy by blocking the target's receptor
interactions. This provides direct proof of concept that blocking
CCL13's receptor-binding surface is a viable therapeutic strategy.

**Implications for profiling:**
- Field 4 (antibody landscape): include target-derived peptides as a
  distinct modality class alongside antibodies, small molecules, and
  receptor-Fc fusions. The peptide validates the receptor-binding
  surface as a druggable epitope.
- Field 11 (differentiation): a neutralizing antibody targeting the
  same receptor-binding region that CDIP-2 mimics would have a
  validated mechanism — the peptide de-risks the epitope selection.
- The peptide's mechanism (competitive antagonism at CCR1/CCR2/CCR3)
  also confirms that a single CCL13-neutralizing antibody can block
  signaling through ALL three of CCL13's primary receptors
  simultaneously, which is a potential advantage over receptor-
  selective approaches.

**Generalization:** For any soluble ligand target where a derived
peptide has shown therapeutic efficacy, the peptide defines the
functionally critical epitope and de-risks antibody epitope selection.
(CCL13 profile, 2026-08-16.)

### 5. 1990s J Immunol papers: DOI absent from PubMed XML, no PMC copy

PMID 8955214 (J Immunol 1996) is representative of a class of older
papers (pre-2000, J Immunol, JBC, and similar subscription journals)
that: (a) have no DOI in PubMed XML (the DOI was assigned later by
the publisher or indexed by EPMC but not propagated to PubMed); (b)
have no PMCID (not deposited in PMC — these papers predate the NIH
Public Access Policy); (c) are paywalled with no OA copy. For these
papers, abstract-only is the expected and correct outcome — there is
no retrieval path that will yield full text. The EPMC core record
provides the DOI for the citation, and the PubMed abstract provides
sufficient content for profile fields 2 and 3.

**Pattern for 1990s landmark papers:** PubMed XML (no DOI, no PMCID)
→ EPMC core record (recovers DOI, confirms no PMC copy) → abstract-only
ingest with `needs-enrichment: true`. Do not attempt jina on the
publisher URL — J Immunol (highwire.org) will return a paywall page.
(CCL13 profile, 2026-08-16, PMID 8955214.)
