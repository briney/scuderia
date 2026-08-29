# M. tuberculosis LAM profile observations (2026-08-17)

Preclinical-tier infectious disease target. Lipoarabinomannan (LAM /
ManLAM) — the major cell wall glycolipid of *Mycobacterium tuberculosis*.
Not a protein: a non-ribosomal lipoglycan assembled by multiple
glycosyltransferases. Surface-exposed, shed into urine (basis for urine
LAM diagnostic tests). Anti-LAM antibodies explored for passive TB
immunotherapy. Built via direct PubMed E-utilities using the two-step
curl form. 8+ PubMed queries (progressive broadening), 72 candidate
PMIDs screened, 14 landmark abstracts fetched via efetch XML parsing
(7 primary + 7 supplementary for structural/immunology context).
Abstract-only ingestion. No UniProt (glycolipid, not protein). 14 unique
PMIDs cited, ~40K chars,
working-docs/hitlist-profiles/m-tb-lam.md.

## Key new patterns

### 1. Glycolipid target class — UniProt does not apply, epitope is carbohydrate

LAM is the first profiled target that is NOT a protein. It is a
high-molecular-weight lipoglycan (~17–35 kDa) with a phosphatidyl-myo-
inositol lipid anchor, a mannan core, a branched arabinan domain, and
mannose caps. There is no UniProt entry, no gene symbol (HGNC), no
single-chain sequence. Field 1 (Target identity) must be adapted:
- **Gene symbol** → list the biosynthetic enzyme operon (*embCAB*)
  and key glycosyltransferases (*MT1671* for mannose capping)
- **UniProt ID** → N/A; optionally list UniProt entries for the
  biosynthetic enzymes (EmbC: P9WJA5) for reference
- **Key domains** → structural motifs of the glycan (PI anchor, mannan
  core, arabinan domain, mannose caps, tailoring modifications)
- **Molecular weight** → heterogeneous population (~17–35 kDa depending
  on arabinan chain length, capping, acylation)

Field 5 (Epitope landscape) describes **carbohydrate epitopes** —
oligosaccharide motifs, mannose caps, mannan core, MTX modifications —
not protein epitopes (linear vs conformational). Anti-carbohydrate
antibodies often have lower affinity than anti-protein antibodies (though
P1AM25 is high-affinity). No antibody–glycan co-crystal structures are
typically available in PDB; epitope data comes from glycan microarray
and functional competition assays.

Generalizes to any non-protein target: glycolipids (LAM, LPS, Gc
ganglioside), polysaccharide capsules (pneumococcal, meningococcal),
glycoconjugates. Adapt field 1 to list biosynthetic pathway rather than
a single gene; adapt field 5 to describe glycan motifs rather than
peptide epitopes.

### 2. Intracellular pathogen — antibody must access intracellular bacteria

M. tuberculosis is primarily an **intracellular** pathogen (survives
within macrophage phagosomes). This is fundamentally different from all
prior infectious disease targets profiled:
- **Secreted toxins** (cholera toxin, anthrax PA, PEA): antibody
  neutralizes free toxin in the extracellular space
- **Viral surface glycoproteins** (EBOV GP, SUDV GP, SARS-CoV-2 S):
  antibody neutralizes extracellular virions before cell entry
- **Bacterial surface structural proteins** (PcrV): antibody blocks
  contact-dependent apparatus at the bacterium-host interface
- **Intracellular bacteria** (M. tuberculosis): antibody must either
  (a) opsonize extracellular bacilli before uptake, redirecting them
  from the immunoevasive MR/DC-SIGN pathway to the bactericidal FcγR
  pathway, or (b) access the phagosome post-uptake

P1AM25's protective efficacy in vivo (PMID 37733444) demonstrates that
antibody-mediated protection IS achievable against an intracellular
pathogen — the mechanism is FcγR-dependent enhanced phagocytosis with
improved phagosome maturation and intracellular killing. The antibody
redirects mycobacterial uptake from MR/DC-SIGN (immunoevasive) to FcγR
(bactericidal). For field 2 (biological mechanism), explicitly describe
the intracellular access mechanism: the antibody doesn't need to
penetrate the host cell; it changes the uptake pathway at the cell
surface. For field 6 (failure modes), the fraction of extracellular vs.
intracellular bacilli during infection may limit antibody access —
this is a target-specific PK/PD consideration not present for secreted
toxin or viral targets. For field 11, the key risk is that antibody
efficacy may be greatest during the early (extracellular) phase of
infection and wane as bacilli become intracellular.

Generalizes to any intracellular bacterial target (Salmonella,
Listeria, Brucella, Legionella, Chlamydia). The antibody mechanism
is pathway-redirection at uptake, not direct neutralization.

### 3. Fc-effector function as a BINARY requirement — not just beneficial

P1AM25 as murine IgG2a (FcγR-binding) was protective in vivo, but
murine IgG1 (poor FcγR engagement) and a non-FcγR-binding IgG variant
were NOT protective — despite identical Fab specificity (PMID 37733444).
This is stronger than the PcrV observation (where Fab-only was a
liability and Fc engineering improved efficacy): for anti-LAM
antibodies, **Fc-effector function is non-negotiable** — the protective
mechanism is entirely FcγR-dependent (enhanced phagocytosis + intracellular
killing), not direct neutralization.

This has a critical implication for field 4 (antibody landscape):
always note the isotype and whether Fc effector function is required.
A high-affinity Fab that blocks LAM–MR binding but lacks FcγR engagement
may be non-protective. For field 6, "wrong Fc isotype" is a distinct
failure mode from "wrong epitope" — both are fatal, but they are
independent failure axes. For field 11, Fc optimization (e.g., afucosylation
for enhanced FcγRIIIa/ADCC, or FcγR-biased variants) is a clear
differentiation opportunity, building on the Grace 2025 finding that
restrictive Fc variants reorganize the innate immune response (PMID
40449485).

Generalizes to any antibody targeting an intracellular pathogen where
the mechanism is opsonophagocytosis rather than direct neutralization:
Fc-effector function is the mechanism, not an enhancement.

### 4. Glycan motif-level epitope specificity determines protection

P1AM25 (protective) and two other high-affinity human IgG1 anti-AM mAbs
(non-protective) all target the arabinomannan (AM) domain — the same
domain, different oligosaccharide (OS) motifs (PMID 37733444). Epitope
specificity at the **glycan motif level** is the single determinant of
protection. This is the glycolipid analog of the FGF19 N-terminal
selectivity pattern (where epitope selectivity separates mitogenic from
metabolic signaling): here, different glycan motifs on the same domain
separate protective from non-protective antibodies, even at equal
affinity.

For field 5 (epitope landscape), glycan epitope mapping requires
synthetic oligosaccharide libraries and glycan microarrays — not
peptide scanning or structural epitope determination. The epitope is
defined by the carbohydrate motif (e.g., specific arabinosyl linkages,
mannose cap structure, MTX modification), not by protein contacts. For
field 6, "high affinity to the wrong glycan motif" is a distinct
failure mode — binding a non-protective epitope with high affinity is
worse than binding the protective epitope with moderate affinity. For
field 11, systematic glycan-motif epitope mapping across the arabinan
domain (using synthetic arabinomannan oligosaccharides) could identify
additional protective epitopes beyond P1AM25's motif.

Generalizes to any glycan-targeting antibody (anti-LPS, anti-capsular
polysaccharide, anti-ganglioside): epitope specificity is at the
carbohydrate motif level, and functional outcome depends on which
motif is recognized, not just on affinity.

### 5. Diagnostic-to-therapeutic cross-validation for glycolipid targets

LAM is unique among profiled targets in having a **mature diagnostic
antibody pipeline** (Alere LF-LAM, Fujifilm SILVAMP TB-LAM) alongside
an early therapeutic antibody pipeline (P1AM25, Grace 2025 mAb). The
diagnostic antibodies (anti-MTX-LAM, 93% sensitivity) validate the
target's antibody-accessibility and clinical relevance — if anti-LAM
antibodies can detect LAM in urine with high sensitivity, the epitope
is accessible and the target is shed in vivo. But the diagnostic
antibody has NOT been evaluated for therapeutic function, and the
therapeutic antibody has not been used diagnostically.

For field 4 (antibody landscape), list diagnostic and therapeutic
antibodies separately — they have different optimization criteria
(diagnostic: sensitivity + specificity; therapeutic: Fc effector
function + protective epitope). For field 11, the MTX epitope
(diagnostic, species-specific) has not been evaluated as a therapeutic
target — an anti-MTX IgG1 with Fc-effector function could combine
species specificity with therapeutic activity, and serve as a
companion diagnostic-therapeutic pair. This is a target-specific
differentiation opportunity that leverages the existing diagnostic
pipeline.

Generalizes to any target with both diagnostic and therapeutic antibody
pipelines (CEA, PSA, HER2 — though these are proteins, not glycolipids).
For glycolipid targets specifically, the diagnostic antibody's success
is a strong prior for target accessibility, but therapeutic function
requires independent validation of epitope + Fc.

## Technical notes

- **Progressive query broadening strategy.** The initial exact-phrase
  query `"Mycobacterium tuberculosis lipoarabinomannan antibody"[tiab]`
  returned 0 results (the exact phrase never appears verbatim in any
  title/abstract — consistent with the FGF19 and PEA observations).
  The strategy that worked: run 8+ query variants with progressive
  broadening:
  1. Exact-phrase [tiab] (0 results — confirms the pattern)
  2. Shorter phrase [tiab] ("LAM antibody"[tiab] → 16 hits, "TB
     lipoarabinomannan"[tiab] → 24 hits)
  3. Boolean field-restricted (lipoarabinomannan antibody tuberculosis[tiab]
     → 233 hits, "lipoarabinomannan"[tiab] antibody → 291 hits)
  4. Functional-term queries ("lipoarabinomannan"[tiab] neutralizing → 8
     hits, "lipoarabinomannan"[tiab] immunotherapy → 18 hits)
  5. Specific modality (LAM monoclonal antibody Mycobacterium[tiab] →
     75 hits)
  6. Structural/context (lipoarabinomannan structure/CD1b/mannose caps/
     macrophage for supplementary papers)

  The "neutralizing" query (8 hits) was the highest-yield query per
  result — every paper was directly relevant to antibody-mediated
  function. The "immunotherapy" query surfaced the Reljic 2006 Lancet
  Infect Dis passive immunoprophylaxis review and the Correia-Neves 2019
  Front Immunol review. The broad boolean queries (233, 291 hits)
  surfaced the Liu 2023 P1AM25 paper and the Grace 2025 Immunity paper.
  **Rule: for targets where exact-phrase [tiab] returns 0, run both
  narrow functional-term queries (neutralizing, immunotherapy, passive)
  AND broad boolean queries — they return non-overlapping, complementary
  literatures.**

- **esummary title screening for landmark selection.** After aggregating
  72 unique PMIDs across all queries, esummary was fetched for ~27
  priority PMIDs (from the "neutralizing" set + older "LAM antibody"
  papers + diagnostic landmarks). Titles were screened for relevance
  (antibody therapy, protection, structure, diagnostic). 7 primary + 7
  supplementary papers selected. The two most important papers (PMID
  37733444 P1AM25, PMID 40449485 Grace 2025) were found via the broad
  boolean queries, not the narrow functional-term queries.

- **Two-round efetch.** Primary papers (7) fetched in one efetch XML
  batch; supplementary papers (7) fetched in a second batch. XML parsed
  with `xml.dom.minidom` (consistent with prior profiles; ElementTree
  also works per the PEA observation). Abstracts ranged 800–1800 chars,
  sufficient for level-2 grounding.

- **No UniProt query.** LAM is a glycolipid — no UniProt entry to query.
  Field 1 (target identity) was sourced entirely from literature (PMID
  29722821, PMID 16704981, PMID 22534567). Biosynthetic enzyme UniProt
  IDs (EmbC P9WJA5) were noted but not queried via REST — they describe
  the enzymes, not the target. This is the first profile where UniProt
  was not used at all.

- **Ingest log and supplementary papers.** Two JSON files (papers.json,
  supplementary.json) and an INGEST-LOG.md were written to
  `_mtb_lam_ingest/` alongside the profile, following the V. cholerae
  toxin pattern. The supplementary papers (structure/CD1b/mannose caps
  literature) enriched fields 2, 5, and 9 without being the primary
  basis for any single field.
