# CCL2/MCP-1 Profile Observations (2026-08-16)

Thirty-sixth level-2 profile (failed-clinical tier, oncology). CCL2/MCP-1
is a soluble CC chemokine that recruits monocytes/macrophages (TAMs) to
the tumor microenvironment. Carlumab (anti-CCL2, CNTO 888) failed in
prostate cancer (Phase 2), advanced solid tumors (Phase 1b), AND IPF
(Phase 2). 7 papers ingested (1 full text via Wayback, 2 structured
abstracts via jina reader, 4 abstract-only). ~35.5K chars, 7 PMIDs cited.

## Paper retrieval summary

| PMID | Journal | Publisher | Full text? | Source |
|------|---------|-----------|------------|--------|
| 17909051 | Cancer Research | AACR | Yes | Wayback (direct urllib.request) |
| 22907596 | Investigational New Drugs | Springer | Abstract | jina reader (structured abstract) |
| 24928772 | Targeted Oncology | Springer | Abstract | jina reader (structured abstract) |
| 23385782 | Cancer Chemother Pharmacol | Springer | Abstract-only | jina returned reference list only |
| 23878055 | J Clinical Pharmacology | Wiley | Abstract-only | CAPTCHA block (506 bytes) |
| 26493793 | European Respiratory Journal | ERS | Abstract-only | No PMCID, no access |
| 34286437 | Adv Exp Med Biol | Springer (book) | Abstract-only | jina returned reference list only (117K chars) |

Retrieval rate: 1/7 full text (14%), 3/7 structured abstract (43%),
3/7 abstract-only (43%). Total usable content: 7/7 (all had at least
PubMed abstracts).

## Key new observations

### 1. Three-part failure framework for soluble ligand antibody targets

CCL2/MCP-1 is the first profile where the clinical failure can be
decomposed into three distinct mechanistic causes with different
fixability:

1. **Insufficient in vivo binding affinity (antibody-specific, fixable)**:
   Carlumab's in vivo KD (2.4 nM) was substantially weaker than in vitro
   predictions. PK/PD modeling (PMID 23878055) identified this as "the
   major factor hindering suppression of free CCL2 at clinically viable
   doses." A higher-affinity antibody could fix this. This is an
   antibody-specific problem, NOT a target problem.

2. **Compensatory ligand upregulation (target-intrinsic, partially
   fixable)**: Free CCL2 rebounded above baseline after antibody dosing
   — the body increases CCL2 production in response to sequestration.
   In the IPF trial (PMID 26493793), free CCL2 was chronically elevated
   above baseline at 24 and 52 weeks. Total CCL2 increased >1,000-fold
   (PMID 23385782). This is a property of CCL2 biology (multiple
   producing cell types, feedback loops). Higher affinity + more
   frequent dosing can partially manage this.

3. **Chemokine redundancy (target-intrinsic, not fixable for
   ligand-targeting)**: CCR2 has multiple ligands (CCL2, CCL7, CCL8,
   CCL13). Blocking CCL2 alone leaves redundant signaling active.
   The preclinical authors explicitly warned about this (PMID
   17909051). An anti-CCR2 receptor antibody would block all ligands
   simultaneously, but no anti-CCR2 antibody has reached late-stage
   clinical development.

**Generalization**: This three-part framework (antibody affinity,
compensatory production, pathway redundancy) applies to any soluble
ligand target with multiple producing cell types and receptor-level
ligand redundancy. For chemokine/cytokine targets, always check: (a)
is the receptor shared by multiple ligands? (b) is the ligand produced
by multiple cell types? (c) is there evidence of feedback regulation of
ligand production? If all three are yes, the ligand-targeting strategy
faces the same three challenges. (CCL2 profile, 2026-08-16.)

### 2. PK/PD modeling paper as highest-value paper for graveyard profiles

For the CCL2 profile, the PK/PD modeling paper (PMID 23878055,
Fetterly 2013) was the single most valuable paper for the failure
analysis (field 6). It provided the quantitative mechanism of failure
(in vivo KD = 2.4 nM vs in vitro predictions, "major factor hindering
suppression of free CCL2"). For graveyard profiles where the antibody
failed clinically, PK/PD modeling papers (when they exist) are the
equivalent of structural biology papers for approved-antibody profiles
— they explain WHY the antibody failed at a mechanistic level.

**Recommendation**: For graveyard/failed-clinical profiles, include
PK/PD modeling papers in the landmark paper selection if available.
Search terms: `<antibody name> PK PD` or `<antibody name>
pharmacokinetics pharmacodynamics`. (CCL2 profile, 2026-08-16.)

### 3. Multi-indication failure strengthens the failure analysis

Carlumab failed in THREE separate clinical trials across TWO different
disease areas (oncology: mCRPC Phase 2, solid tumors Phase 1b; fibrosis:
IPF Phase 2). The IPF trial independently confirmed the compensatory CCL2
upregulation problem (free CCL2 elevated above baseline at 24 and 52
weeks) in a non-cancer indication. This cross-disease confirmation
strengthens the conclusion that the failure is target-intrinsic
(compensation) rather than disease-specific. For graveyard profiles,
always check if the antibody failed in multiple indications —
multi-indication failures strengthen the failure analysis and help
distinguish target-intrinsic from indication-specific problems. (CCL2
profile, 2026-08-16.)

### 4. Springer subscription journals: two distinct jina patterns

The existing Springer/Drugs known-blocks entry documents the
reference-list masquerade pattern. This session confirmed two distinct
jina reader behaviors for subscription Springer journals:

- **Structured abstract returned** (PMID 22907596, Investigational New
  Drugs, 24.5 KB; PMID 24928772, Targeted Oncology, 33 KB): jina returns
  the full structured abstract (Background/Methods/Results/Conclusion)
  plus the "Access this article" paywall page. The abstract is complete
  and usable for profile grounding. Tag `fulltext_source: jina-reader`
  at abstract level.

- **Reference list only** (PMID 23385782, Cancer Chemother Pharmacol,
  34 KB; PMID 34286437, Springer book chapter, 117 KB): jina returns
  the reference list with zero body paragraphs — the documented
  masquerade pattern. Validate body text presence before tagging.

The difference appears to be journal-specific (some Springer journals
render the abstract in the HTML head, others only render references).
The existing Springer/Drugs known-blocks entry's guidance ("validate
body text presence before tagging") covers both cases. No new entry
needed — this observation confirms the existing entry covers the full
range of Springer subscription journal behaviors. (CCL2 profile,
2026-08-16.)

### 5. ERS Journal (European Respiratory Journal) — new publisher block

PMID 26493793 (Raghu 2015, European Respiratory Journal, DOI
10.1183/13993003.01558-2014) had no PMCID (`inPMC: N`, `isOpenAccess:
N`). Not attempted via jina (no jina call made for this paper;
abstract was sufficient). The ERS journal is not in the paper-ingest
known-blocks table. Based on the DOI prefix (10.1183) and the
`ersjournals.org` domain, it likely follows the standard subscription
journal pattern (jina may return abstract or may be CAPTCHA-blocked).
If encountered in future sessions, add to the known-blocks table.

### 6. Wayback CDX + direct urllib.request confirmed for AACR papers

PMID 17909051 (Loberg 2007, Cancer Research, DOI
10.1158/0008-5472.can-07-1286) was successfully retrieved via the
documented AACR Wayback CDX pattern: CDX search on
`cancerres.aacrjournals.org/content/67/19/9417` found a 200-status
snapshot (2017), and direct `urllib.request` (NOT jina-on-Wayback,
which returned a 403 AbuseAlleviationError) fetched 350 KB HTML →
56.6K chars extracted text containing full Abstract, Introduction,
Materials and Methods, Results, and Discussion sections. This
confirms the AACR known-blocks entry: use Wayback CDX +
`.content/<vol>/<issue>/<page>` URL pattern, and use
`urllib.request` (not jina-on-Wayback) to fetch the snapshot. (CCL2
profile, 2026-08-16.)

Note: The jina-on-Wayback 403 AbuseAlleviationError is a new failure
mode not previously documented. Jina's reader proxy appears to be
blocked by the Wayback Machine's abuse detection system (returned
JSON: `{"code":403,"name":"AbuseAlleviationError"}`). Direct
`urllib.request` with a `User-Agent` header bypasses this. For
Wayback retrieval, prefer `urllib.request` over jina-on-Wayback when
jina returns the AbuseAlleviationError. (CCL2 profile, 2026-08-16.)
