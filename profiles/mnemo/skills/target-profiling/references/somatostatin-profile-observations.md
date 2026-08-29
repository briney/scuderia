# Somatostatin (SST) — key-paper-ingestion profile observations

**Date**: 2026-08-16
**Target**: Somatostatin (SST) / SSTR2A
**Tier**: clinical-trial
**Area**: cardiovascular / metabolic
**Profile**: `working-docs/hitlist-profiles/somatostatin.md`
**Papers**: 5 ingested (3/5 full text via PMC XML, 2/5 via publisher-jina with explicit --publisher-url)
**Size**: ~51K chars, 151 PMID citations, 11 unique PMIDs

## Papers ingested

| PMID | Author/Year | Label | Full-text source | Chars |
|------|------------|-------|-----------------|-------|
| 22251942 | Körner 2012 | SSTR2A mAb IHC (UMB-1) | PMC XML (PMC3261429) | 30,166 |
| 32684623 | Si 2021 | Anti-SSTR2 ADC for NET | PMC XML (PMC7854894) | 36,030 |
| 36697135 | Tawakol 2023 | SSTR2 PET in vasculitis | PMC XML (PMC9889111) | 8,032 |
| 7909409 | Martín 1994 | Anti-SST Ab → gastrin | publisher-jina (APS) + PubMed abstract | 44,289 |
| 19704057 | Rinke 2009 | PROMID: octreotide LAR RCT | publisher-jina (ASCO) + PubMed abstract | 49,780 |

## Key new patterns

### (1) Peptide-ligand + GPCR-receptor dual-target profiling

Somatostatin is a small secreted peptide (~1.6 kDa, 14 aa) with a half-life
of <3 min. The peptide itself is antibody-accessible in circulation, but
its extreme brevity makes direct antibody targeting impractical. The
therapeutically druggable target is the somatostatin receptor subtype 2A
(SSTR2A), a 7-TM GPCR highly expressed on NET cells and activated
macrophages. This creates a **dual-target profile**: the ligand (SST) is
the biological context, but the receptor (SSTR2A) is the antibody target.

For field 1 (target identity), document BOTH the peptide ligand AND the
receptor — gene symbols (SST for the peptide, SSTR2 for the receptor),
UniProt IDs (P61278 for SST, P30874 for SSTR2A), molecular weights, and
domain structures. The profile should clarify which entity the antibody
targets.

For field 2 (biological mechanism), the "effect of blockade" section
must distinguish: (a) blocking the ligand (immunoneutralization —
anti-somatostatin antibody releases G-cells from inhibitory control,
PMID 7909409); (b) blocking the receptor (anti-SSTR2 antibody for ADC
delivery, not functional blockade — the antibody binds for payload
delivery via receptor-mediated endocytosis, PMID 32684623). These are
fundamentally different therapeutic strategies against the same axis.

Generalizable to any peptide-GPCR axis where the ligand is too small/
short-lived for practical antibody targeting but the receptor is
surface-expressed and overexpressed in disease: SST/SSTR2, GLP-1/GLP-1R
(cf. glp-1-profile-observations.md — same pattern, AMG 133 targets GIPR
not GLP-1R), GIP/GIPR, glucagon/GCGR.

### (2) fetch_fulltext.py DOI auto-resolution can fail silently

When the EPMC gate returns `inPMC: N, isOpenAccess: N, hasPDF: N,
pmcid: None`, the fetch_fulltext.py script falls through to branch 2
(publisher page via jina). Branch 2 calls `resolve_doi()` which does a
HEAD request to doi.org to follow the redirect. This can fail silently
(no exception, but returns None), causing the script to skip the jina
step entirely and return `provenance: none` almost instantly.

**Fix**: Provide `--publisher-url` explicitly when calling
fetch_fulltext.py for papers without PMCIDs. The publisher URL bypasses
the doi.org resolution step entirely. For ASCO/JCO papers:
`--publisher-url https://ascopubs.org/doi/<DOI>`. For APS journals:
`--publisher-url https://journals.physiology.org/doi/<DOI>`.

This is a general technique for any paywalled paper where the EPMC gate
returns nothing — always supply the publisher URL explicitly rather than
relying on automatic DOI resolution.

### (3) GPCR-targeted ADC — internalization as the mechanism

SSTR2A is a 7-TM GPCR. The anti-SSTR2 ADC (Si et al., PMID 32684623)
exploits receptor-mediated endocytosis: the antibody binds ECD1+ECD2 on
the cell surface, then the antibody-receptor complex is internalized via
clathrin-coated pits (detected within 40 min by confocal microscopy),
and the cytotoxic payload (MMAE) is released in the lysosome. This is a
distinct mechanism from: (a) naked mAb blocking GPCR signaling (e.g.,
erenumab anti-CGRP-R); (b) small-molecule GPCR antagonists (e.g.,
avacopan anti-C5aR1); (c) PRRT (radiolabeled peptide analog internalization).

For field 4 (antibody landscape), GPCR-targeted ADCs are a distinct
format category — the antibody is a delivery vehicle, not a signaling
blocker. For field 5 (epitope landscape), the critical property is
internalization kinetics, not neutralization potency. For field 6
(success factors), the ~20-fold overexpression of SSTR2 on NET cells
vs normal cells creates a wide therapeutic window — the ADC can kill
tumor cells while sparing normal tissues with low surface SSTR2.

Generalizable to any GPCR target that undergoes agonist-induced
internalization and is overexpressed in disease: SSTR2 (NET), CXCR4
(cancer), GRPR (prostate cancer), GPCRs with known internalization
pathways.

### (4) Companion diagnostic antibody as a field 4 entry

UMB-1 (anti-SSTR2A mAb, PMID 22251942) is not a therapeutic antibody —
it is a companion diagnostic used for IHC-based patient selection for
SSTR2-targeted therapy. It has a validated cut-off (>10% positive tumor
cells = targetable, 95.4% PPV, 96% NPV) equivalent to the HercepTest
paradigm. This is a distinct antibody category that belongs in field 4
(antibody landscape) alongside therapeutic antibodies.

For field 4, include diagnostic/companion-diagnostic antibodies as
separate entries with: format (IHC reagent, not therapeutic), phase
(diagnostic, not clinical trial), outcome (validated companion
diagnostic with sensitivity/specificity data), and epitope info (the
staining pattern and validation method). The companion diagnostic is
part of the target's antibody ecosystem — without it, patient selection
for therapeutic antibodies fails.

Generalizable to any target with a validated companion diagnostic
antibody: HER2/HercepTest, SSTR2A/UMB-1, PD-L1/22C3, EGFR/Dako
pharmDx.

### (5) mRNA vs surface protein discrepancy — safety-relevant

The Human Atlas Project reports high SSTR2 mRNA expression in brain,
but IHC with the anti-SSTR2 mAb showed minimal/undetectable surface
SSTR2 protein in brain and 33 other normal organs (PMID 32684623).
This discrepancy is safety-critical for ADC approaches: if one relied
on mRNA data alone, one might conclude brain SSTR2 expression makes
SSTR2 ADCs unsafe. In reality, the lack of surface protein means brain
toxicity is not a concern — confirmed by the in vivo study (no brain
histopathology at 20 mg/kg).

For field 8 (safety), always verify surface protein expression (IHC,
flow cytometry), not just mRNA, when assessing on-target toxicity risk
for ADC targets. mRNA expression without surface protein does not
equate to targetable expression. For field 9 (structural information),
note the mRNA-protein discrepancy as a factor in epitope accessibility
assessment.

Generalizable to any ADC target where mRNA and protein expression
disagree — this is a common pattern for GPCRs and other
tightly-regulated surface proteins where mRNA may be present but
protein is intracellular or rapidly turned over.

### (6) PubMed abstract supplementation for paywalled papers

For the two paywalled papers (Martín 1994, APS; Rinke 2009, ASCO/JCO),
the publisher-jina retrieval returned page chrome/navigation rather
than article text (APS) or only the abstract (ASCO). The PubMed efetch
abstract API (`efetch.fcgi?db=pubmed&id=<PMID>&rettype=abstract&retmode=text`)
provided clean, complete abstracts that supplemented the jina output
for grounding fields 2, 3, and 6.

This is a complementary technique to the jina reader: when jina returns
page chrome instead of article text, fall back to PubMed efetch abstract
to get the structured abstract. The abstract alone was sufficient for
the PROMID trial data (TTP 14.3 vs 6 months, HR 0.34) and the
anti-somatostatin antibody functional data (gastrin >2-fold increase).
