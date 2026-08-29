# TLR2 (Toll-like receptor 2) infection profile — session observations

**Profile**: `working-docs/hitlist-profiles/tlr2-infection.md` (~39K chars, 220 lines)
**Date**: 2026-08-17
**Tier**: Preclinical (infection context)
**Therapeutic area**: Infectious disease / innate immunity / gram-positive sepsis
**Rigor level**: Level 2 (key paper ingestion — 6 papers, 3 with full text via PMC XML, 1 via EPMC PDF, 1 via jina, 1 abstract-only)
**PMIDs ingested**: 15146245, 26147469, 20026776, 23880971, 38358825, 28011917

## Key new patterns

### (1) PRR (pattern recognition receptor) as antibody target — a new target class

TLR2 is the first profiled target that is a host pattern recognition receptor
(PRR) — not a pathogen protein (toxin, viral glycoprotein, bacterial
structural protein) and not a traditional host signaling protein (cytokine,
receptor, enzyme). TLR2 is an innate immune sensor expressed on
circulating leukocytes (monocytes, macrophages, neutrophils, DCs) that
recognizes Gram-positive bacterial PAMPs (lipopeptides, LTA, PGN).

The antibody does NOT neutralize a pathogen factor or block a
pathology-driving host signaling pathway directly. Instead, it blocks
the host's own sensor for microbial products — preventing the innate
immune system from over-activating in response to infection. The
mechanism is immunomodulatory, not anti-pathogen: blocking TLR2 prevents
neutrophil CXCR2 loss, restoring neutrophil migration to the infection
site (PMID 26147469). The antibody "re-programs" the innate immune
response rather than killing the pathogen or neutralizing a toxin.

For field 2, explicitly describe the PRR function (what PAMPs are
recognized, which TLR heterodimer is formed, which signaling pathway is
activated). For field 6, the failure/success modes are fundamentally
different from anti-pathogen antibodies: the risk is immunosuppression
(too much blockade → host can't fight infection), not just on-target
toxicity. For field 8, the safety concern is infection susceptibility
(blocking a PRR impairs pathogen sensing), not target-mediated organ
toxicity. Generalizes to any PRR target (TLR4, TLR7, TLR9, NOD2, RIG-I,
MDA5, cGAS).

### (2) Single-PRR blockade is protective; combined PRR blockade is harmful

The CLP sepsis model (PMID 26147469) revealed a counterintuitive pattern:
blocking TLR2 ALONE improved survival (75% preventive, ~50% therapeutic),
blocking TLR4 ALONE also improved survival (65% preventive, ~50%
therapeutic), but blocking BOTH TLR2 AND TLR4 simultaneously was NOT
protective — it was worse than either alone. Mechanism: dual TLR blockade
mimics MyD88 deficiency (MyD88 is the shared adaptor for most TLRs),
causing excessive immunosuppression → failure of neutrophil migration
→ uncontrolled bacterial growth → death.

However, when antibiotics were added, the combined blockade BECAME
protective (~75% survival), because antibiotics control bacterial
spread while TLR blockade controls inflammation.

For field 6, this is a distinct failure mode: "combined pathway
blockade exceeding the immunosuppression threshold." It is NOT simply
"wrong population" or "insufficient efficacy" — it is active harm from
over-blocking the innate immune system. For field 11, the differentiation
opportunity is to avoid combined PRR blockade unless paired with
antibiotics, or to develop a PRR-selective approach that blocks only the
pathology-driving PRR while leaving others functional.

Generalizes to any multi-PRR system where blocking individual receptors
is protective but combined blockade mimics global pathway deficiency
(e.g., combined TLR7+TLR9 blockade in SLE, combined complement C3+TLR
blockade in sepsis).

### (3) EPMC PDF fallback succeeds when PMC XML is front-matter only (stale PMCID)

PMID 15146245 (Meng 2004, J Clin Invest) is the landmark T2.5 paper.
Both PMCIDs available — PubMed XML had PMC359108, EPMC had PMC406529 —
returned front-matter-only XML (2.4 KB and 9.7 KB respectively, no
`<body>` element). The EPMC PDF render endpoint
(`https://europepmc.org/api/getPdf?pmcid=PMC406529`) delivered the
full 766 KB publisher PDF, from which 53,643 chars of text were
extracted via pymupdf.

This extends the paper-ingest observation about EPMC PDF Branch 1b:
when `inPMC: Y` but PMC XML returns front-matter only (stale/restricted
PMCID), the EPMC PDF endpoint can still deliver the full publisher PDF
even when `isOpenAccess: N`. The `hasPDF` flag is unreliable — always
try the EPMC PDF endpoint when `inPMC: Y` regardless of `hasPDF`.
This is now confirmed for JCI (Journal of Clinical Investigation) in
addition to the previously confirmed OUP/ATS and ASM journals.

### (4) PubMed XML DOI cross-reference error — completely wrong journal

PMID 26147469 (Lima 2015, PLoS One) had DOI `10.1056/NEJMoa1202290` in
PubMed XML — this is a New England Journal of Medicine DOI, not a PLoS
One DOI. The correct DOI (`10.1371/journal.pone.0132336`) was in the
Europe PMC core record. This is a more severe variant of the
paper-ingest "PubMed XML can carry an erroneous DOI" pitfall: not just
a different paper's DOI in the same journal family, but a DOI from a
completely different journal. This could silently route full-text
retrieval to the wrong paper if the PubMed DOI is trusted without
verification.

**Rule:** Always cross-check the PubMed XML DOI against the Europe PMC
DOI during identity resolution. When they disagree, use the Europe PMC
DOI. Also verify the DOI prefix matches the expected journal
(10.1371 = PLoS, 10.1056 = NEJM, 10.1172 = JCI, 10.1038 = Nature, etc.).
A mismatch between the DOI prefix and the expected journal is a
red flag.

### (5) TLR2/TLR13 dual PRR sensing — the human TLR8 equivalent

The pneumococcal meningitis study (PMID 38358825) identified TLR2 + TLR13
(mouse) as the major PRR pair for cerebral pneumococcal sensing — not
TLR2 + TLR4 as previously assumed. TLR13 is absent in humans (mutational
deletion); its functional equivalent is TLR8, which senses bacterial
23S rRNA. The dual TLR2+TLR8 blockade reduced S. pneumoniae-induced
IL-6 in human PBMCs by 90.2% median (10 donors).

For target profiling, when a mouse model identifies a PRR pair and one
member lacks a direct human ortholog, always identify the functional
human equivalent. The antibody target (anti-TLR2) is the same in both
species, but the combination partner changes (TLR13 → TLR8). For field
2, document both the mouse model PRR pair and the human equivalent.
For field 11, a bispecific anti-TLR2/anti-TLR8 antibody could replace
the T2.5 + chloroquine cocktail used in the mouse study.

### (6) Compartmentalized vs systemic infection — anti-PRR efficacy varies by infection site

The T2.5 + chloroquine dual TLR blockade was highly effective in the
intracisternal (CNS) pneumococcal meningitis model but showed NO effect
in an intravenous (systemic) pneumococcal challenge model (PMID
38358825). This suggests anti-TLR2 therapy may be most effective in
compartmentalized infections (CNS, peritoneal) where the antibody can
achieve high local concentrations and the PAMP release is contained,
rather than in systemic bloodstream infection where PAMPs are diluted
and degraded by serum RNases/proteases.

For field 6, this is a population/indication differentiation: the same
antibody may work in meningitis but not in sepsis. For field 11,
recommend targeting compartmentalized infections first (CNS, peritoneal,
pleural) where the therapeutic window and local concentration are more
favorable. Generalizes to any anti-PRR antibody where efficacy depends
on infection compartmentalization.

### (7) OPN-305 Phase 1 — the only clinical anti-PRR antibody data

OPN-305 (humanized IgG4 anti-TLR2, Opsona Therapeutics) is the only
anti-TLR2 antibody to reach clinical trials (Phase 1, PMID 23880971).
The Phase 1 data (41 healthy subjects, 0.5-10 mg/kg IV) provides the
only human PK/PD benchmark for an anti-PRR antibody:
- Full receptor occupancy on CD14+ monocytes at ALL doses (14-90+ days)
- Dose-dependent IL-6 inhibition: >50% at 14 days (0.5 mg/kg), 84% at 90 days (10 mg/kg)
- t1/2: 84-489h (dose-dependent, target-mediated drug disposition)
- Low immunogenicity: 1/29 subjects, non-neutralizing
- No cytokine elevation, no infusion reactions, no QTc effects

For field 4, this is the benchmark clinical antibody. For field 8,
the safety data (well-tolerated, no dose-limiting toxicity) is the only
clinical safety data for any anti-PRR antibody. For any future anti-PRR
antibody development, the OPN-305 PK/PD/safety profile is the reference
point.

### (8) Search strategy for PRR targets — antibody code names are key

Searching PubMed for "TLR2 antibody" returned 940 hits — too broad.
"anti-TLR2 monoclonal antibody sepsis" returned only 6 — too narrow but
highly relevant. The most effective strategy was:
1. Broad search: `"TLR2" AND antibody AND infection` (940 hits)
2. Narrow search: `"anti-TLR2" AND "monoclonal antibody" AND sepsis` (6 hits)
3. Antibody code name search: `"T2.5" AND TLR2 AND antibody` (10 hits — surfaced the T2.5-specific literature)
4. Clinical trial search: `OPN-305 AND TLR2 AND antibody` (5 hits — surfaced the Phase 1 trial)

For PRR targets, the antibody code name search (T2.5, OPN-305, OPN-301)
is critical because these clone/code names are used in the literature
independently of the generic "anti-TLR2" term. The clone name T2.5 is
particularly important because it's used across multiple disease
contexts (sepsis, meningitis, stroke, I/R injury) and links the
research-grade antibody to the clinical candidate lineage.
