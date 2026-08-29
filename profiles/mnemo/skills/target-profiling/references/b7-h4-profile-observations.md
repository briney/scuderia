# B7-H4 (VTCN1) Profile Observations

**Profile**: working-docs/hitlist-profiles/b7-h4.md
**Tier**: Preclinical
**Therapeutic area**: Oncology (immune checkpoint / ADC)
**Date**: 2026-08-16
**Papers ingested**: 4 (PMID 37294948, 29625896, 32938586, 37793853)
**Profile size**: ~32K chars, 4 ingested PMIDs + 8 ClinicalTrials.gov NCT IDs cited
**Full-text retrieval**: 3/4 PMC XML OA (Toader Mol Cancer Ther, Song Cancer Discov, Gray JITC), 1/4 publisher-jina (Li Immunity — Elsevier, no PMCID, 91K chars via jina)

## Key new patterns

### 1. ClinicalTrials.gov API v2 for antibody landscape enumeration

The session used the ClinicalTrials.gov REST API v2
(`clinicaltrials.gov/api/v2/studies`) to systematically enumerate the
full B7-H4 antibody pipeline — 8 clinical-stage antibodies across
ADC, bispecific, and naked antibody formats, including 2 in Phase 3
(AZD8205, HS-20089). This is the first target-profiling session to
systematically query ClinicalTrials.gov as a data source for fields 4
(antibody landscape) and 10 (competitive landscape).

**Two-step query pattern:**

1. Broad search: `query.intr=B7-H4&pageSize=20` — captures all
   B7-H4-intervention trials.
2. Drug-specific search: `query.intr=<drug_name>&pageSize=5` for each
   known drug name (XMT-1660, SGN-B7H4V, AZD8205, etc.) — captures
   all trials per drug, including terminated/withdrawn.

**Extract per trial:** NCT ID, brief title, overall status, phase,
intervention names. The status field is critical — multiple B7-H4
antibodies have been TERMINATED (SGN-B7H4V, FPA150, PF-07260437),
which is a key signal for field 6 (failure modes).

**Generalizable:** For any target with clinical-stage antibodies,
ClinicalTrials.gov API v2 provides the most current pipeline data
— more complete than PubMed (which won't list terminated trials) or
the Antibody Society tables (which lag behind). Add this as a
standard data source for field 4 and field 10 profiling. The
`target-hitlist` skill already documents the ClinicalTrials.gov API
for gap-fill; profiling should use it for antibody-specific
enumeration.

### 2. UniProt REST API for systematic structural data

The session queried the UniProt REST API
(`rest.uniprot.org/uniprotkb/<accession>.json`) to systematically
fill fields 1 (target identity) and 9 (structural information) for
B7-H4 (Q7Z7D3). This provided:

- Molecular weight (30,878 Da) and sequence length (282 aa)
- Domain topology: signal peptide [1-24], IgV1 [35-146], IgV2
  [153-241], transmembrane [260-280], cytoplasmic [281-282]
- Glycosylation: N-linked at Asn216 (within IgV2 domain)
- Disulfide bonds: C56-C130 (IgV1), C168-C225 (IgV2)
- Function text, tissue specificity, induction (IL-6/IL-10 up,
  GM-CSF/IL-4 down)
- 4 isoforms (alternative splicing)

**Generalizable:** UniProt REST API is the authoritative source for
fields 1 and 9 structural data. Query by UniProt accession (from
PubMed or manual lookup) — the JSON response carries all domain,
topology, glycosylation, and feature annotations in structured form.
This is faster and more complete than scraping UniProt web pages.
Add UniProt as a standard data source alongside PubMed for
target-profiling.

**Pitfall — Python string escaping in terminal heredocs.** Multi-line
Python scripts with f-strings containing newlines fail when embedded
in `terminal()` heredocs due to shell escaping of quotes and
backslashes. Write the script to a temp file first (`cat >
/tmp/script.py << 'PYEOF'`), then execute with `python3
/tmp/script.py`. The `'PYEOF'` (quoted) prevents variable expansion.

### 3. Immune checkpoint with unidentified receptor — ADC-dominant landscape

B7-H4 is the **first immune checkpoint target profiled where the
receptor on T cells remains unidentified** (as of 2024). This creates
a specific profiling pattern:

- **ADC-dominant landscape:** All 8 clinical-stage B7-H4 antibodies
  are ADCs (5), bispecifics (2), or terminated naked antibodies (1).
  The naked checkpoint-blocking approach (FPA150) was terminated. Without
  knowing the receptor, rational design of blocking antibodies that
  disrupt the B7-H4-receptor interaction is impossible — ADCs bypass
  this by delivering payload regardless of signaling.

- **Epitope landscape is a blank slate (field 5):** No published
  epitope mapping for any clinical-stage B7-H4 antibody. The field is
  too early for epitope binning. For field 5, note "Unknown" for all
  epitope subfields and frame the gap as a first-mover opportunity in
  field 11 (differentiation).

- **Non-overlapping expression with PD-L1 is the key differentiator:**
  B7-H4 and PD-L1 expression are minimally overlapping in tumors (PMID
  37294948, PMID 32938586). This is the single most important fact for
  fields 6 (success factors), 10 (competitive landscape gaps), and 11
  (population differentiation — B7-H4+/PD-L1- patients). Always check
  for non-overlapping expression with known checkpoint partners when
  profiling a B7 family member.

**Generalizable:** When profiling an immune checkpoint with an
unidentified receptor, expect: (1) ADC-dominant clinical landscape,
(2) empty epitope landscape, (3) combination with known checkpoints
(PD-1/PD-L1) as the clinical rationale. This pattern applies to B7-H4
and potentially to other checkpoints with unidentified receptors.

### 4. AACR journals (Mol Cancer Ther) CAN have PMC full text

The IL-35 profile observations noted that AACR journals (Mol Cancer
Ther) are Cloudflare-blocked for jina reader and are "abstract-only
by default." This session **corrects that observation**: PMID
37294948 (Toader et al., Mol Cancer Ther 2023) had PMCID PMC10477829
with `inPMC=Y, isOpenAccess=Y`, and `fetch_fulltext.py` retrieved
52,185 chars of full text via PMC XML. The paper was published as
open access (the authors or Mersana paid the OA fee).

**Correction:** AACR journal papers are NOT universally
abstract-only. AACR journals offer optional open access — when the
authors pay for OA, the paper gets a PMCID and full PMC XML access.
The Cloudflare block affects publisher-site jina retrieval, but
PMC XML bypasses it entirely. Always check for a PMCID before
assuming AACR papers are abstract-only. The IL-35 observation
should be refined: "AACR journals without OA author fees are
abstract-only; with OA, PMC XML is available."

### 5. Glycosylation-stabilized immune checkpoint — a druggable vulnerability

B7-H4 is the **first target profiled where N-linked glycosylation
stabilizes the checkpoint protein by preventing ubiquitination**
(PMID 32938586). Glycosylation at Asn216 (catalyzed by STT3A/UGGG1)
antagonizes AMFR-mediated ubiquitination, stabilizing B7-H4 on the
tumor cell surface. The OST inhibitor NGI-1 blocks glycosylation,
causing B7-H4 degradation and restoring immunogenic cell death.

**Generalizable:** For any membrane protein target where
glycosylation stabilizes surface expression (a pattern also seen in
PD-L1), the glycosylation site is a druggable vulnerability. In
field 2 (biological mechanism), document the glycosylation-ubiquitination
regulatory axis. In field 11 (differentiation), an antibody that binds
near the glycosylation site could potentially disrupt the stabilizing
glycan and promote degradation — a dual mechanism (blockade +
degradation). This is distinct from standard checkpoint blockade and
represents an underexplored antibody design strategy for
glycosylation-stabilized targets.

### 6. B7-H4 suppresses immunogenic cell death (ICD) — beyond T cell inhibition

B7-H4 is the **first immune checkpoint target profiled with a
non-immune function in suppressing immunogenic cell death** (PMID
32938586). B7-H4 inhibits eIF2α phosphorylation, blocking calreticulin
surface exposure — the "eat me" signal for dendritic cell phagocytosis.
This means B7-H4 has two immunosuppressive mechanisms: (1) T cell
inhibition (via unidentified receptor) and (2) ICD suppression (cell-
autonomous). A simple checkpoint-blocking antibody would only address
mechanism 1; an ADC that kills B7-H4+ cells addresses both by removing
the protein entirely.

**Generalizable:** When profiling a checkpoint molecule, check for
non-immune functions (ICD suppression, metabolic reprogramming, cell
adhesion). Document both immune and non-immune functions in field 2.
In field 11, note whether a blocking antibody vs an ADC would
differentially address each function — this can be a format
differentiation dimension for targets with dual mechanisms.

(B7-H4 profile, ~32K chars, 4 papers ingested (3/4 full text via PMC
XML, 1/4 full text via publisher-jina), 4 ingested PMIDs + 8 NCT IDs
cited, working-docs/hitlist-profiles/b7-h4.md.)
