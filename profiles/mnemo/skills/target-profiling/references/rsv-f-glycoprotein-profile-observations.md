# RSV F glycoprotein profile observations (2026-08-16)

Thirty-first level-2 profile (approved tier, infectious disease — RSV lower
respiratory tract infection in infants). RSV F is the **first viral surface
glycoprotein target profile** (Ebola GP, anthrax PA, botulinum toxin, and C.
difficile toxin B are also infectious disease targets, but RSV F is the first
**viral fusion protein** — a class I fusion glycoprotein with conformational
states that fundamentally define the antibody landscape). It is also the
**first infectious disease target with TWO approved antibodies from different
generations** (palivizumab 1998, nirsevimab 2023) plus a failed antibody
(motavizumab — not approved due to safety) and a no-efficacy antibody
(suptavumab), making it one of the richest antibody landscapes in the
infectious disease profile set. 5 papers ingested: 3/5 PMC XML full text
(McLellan 2013 Science ×2 — both have PMCIDs despite being AAAS/Science
papers; Sun 2023 JAMA Netw Open — OA), 2/5 abstract-only (both NEJM
nirsevimab trials — Hammitt 2022 MELODY, Griffin 2020 Phase 2b — paywalled,
jina blocked by Cloudflare, Wayback 429). 60% full-text retrieval. ~39K
chars (profile), 83 authors across 5 papers, 5 unique PMIDs. New
observations:

## 1. Prefusion vs postfusion conformational states define the epitope hierarchy

RSV F exists in two conformational states: prefusion (pre-F, metastable) and
postfusion (post-F, stable). The prefusion conformation contains antigenic
site Ø — a quaternary epitope at the membrane-distal apex that is the target
of the most potent neutralizing antibodies (D25, AM22, 5C4, nirsevimab).
Site Ø is DESTROYED in the postfusion state (α4-helix pivots ~180°). The
postfusion form retains antigenic sites I, II, and IV — targeted by
palivizumab and motavizumab (site II).

The key insight: **absorption of human sera with postfusion F fails to remove
the majority of F-specific neutralizing activity** — the most important
neutralizing epitopes are prefusion-specific (PMID 23618766). Site Ø
antibodies are 10-100-fold more potent than site II antibodies (palivizumab).
This conformational duality is the central organizing principle for fields 5
(epitope landscape), 6 (success/failure modes), and 11 (differentiation).

For field 5, explicitly document both conformational states and which
epitopes are present/absent in each. For field 6, the epitope choice
(prefusion-specific vs conformation-independent) is THE primary success
factor — nirsevimab (site Ø) is dramatically more potent than palivizumab
(site II). For field 11, the conformational states create differentiation
opportunities: a postfusion-stable epitope might offer broader cross-reactivity
at the cost of potency, while a prefusion-specific epitope offers maximum
potency but requires the metastable conformation.

This pattern generalizes to other class I viral fusion proteins with
prefusion/postfusion states (HIV Env, influenza HA, SARS-CoV-2 spike, Ebola
GP). For any viral fusion protein target, determine: (a) which
conformational state is the target of the most potent neutralizing
antibodies, (b) which epitopes are conformation-specific vs
conformation-independent, (c) whether the prefusion state can be stabilized
for vaccine/antibody design. (PMID 23618766, PMID 24179220.)

## 2. DS-Cav1: structure-based antigen engineering directly enabled vaccines

The McLellan 2013 Science paper (PMID 24179220) engineered prefusion-stabilized
RSV F (DS-Cav1: S155C-S290C disulfide lock + S190F-V207L cavity-filling) that
elicited 10-fold higher neutralizing titers than postfusion F in mice and
macaques. This DS-Cav1 antigen is the **direct predecessor of two approved
RSV vaccines** (Arexvy/GSK, Abrysvo/Pfizer). The "neutralization-sensitive
site" strategy — identify the most potently neutralized site, determine its
structure, engineer stable presentation, elicit high-titer responses — became
a paradigm for structure-based vaccine design.

For field 9 (structural information) and field 11 (differentiation), when a
target has conformational states and the metastable state is the primary
antibody target, document whether a stabilized form has been engineered and
whether it has been used in vaccine development. The antibody and vaccine
landscapes are connected: the same prefusion-stabilized antigen can serve as
both a vaccine immunogen and a screening reagent for discovering
prefusion-specific antibodies. (PMID 24179220.)

## 3. Fc half-life engineering as a clinical differentiator

Nirsevimab's key innovation over palivizumab is not just epitope selection
(site Ø vs site II) but **Fc engineering for extended half-life** (YTE
modifications: M252Y/S254Y/T256E, extending half-life from ~20 days to ~70
days). This enables single-dose season-long protection vs palivizumab's 5
monthly injections. The clinical impact: nirsevimab is approved for ALL
infants (not just high-risk), with a single dose covering an entire RSV
season (150 days).

For field 4 (antibody landscape), document Fc engineering modifications
explicitly (YTE, M252Y/S254Y/T256E, pH-dependent recycling, etc.) alongside
epitope and format. For field 6 (success factors), half-life engineering can
be THE differentiator that enables a broader population and simpler regimen
— even when the epitope is the same or similar. For field 11, a
next-generation antibody could combine a different epitope with further Fc
engineering (e.g., pH-dependent recycling for even longer half-life, or
effector-function-enhanced Fc for infected-cell killing). (PMID 35235726,
PMID 32726528.)

## 4. Motavizumab: efficacy without approval — the safety gate

Motavizumab (affinity-matured variant of palivizumab, same epitope site II)
showed numerically superior efficacy to palivizumab in the network
meta-analysis (significantly larger reduction in RSV infection: OR 0.52
vs palivizumab; larger ICU admission reduction: OR 0.47 vs palivizumab).
Yet it was NOT approved by the FDA due to **hypersensitivity/skin reactions**
and lack of sufficiently greater clinical efficacy to justify the safety
risk (PMID 36800182).

This is a distinct failure mode from suptavumab (no efficacy — epitope/mechanism
failure). Motavizumab had the right epitope and superior efficacy but failed
on **safety** — the antibody itself (likely immunogenicity from affinity
maturation) caused unacceptable reactions. For field 6, document both types
of failure: (a) epitope/mechanism failure (suptavumab — targeting F is not
sufficient; the epitope must be functionally relevant), and (b) safety
failure (motavizumab — efficacy is necessary but not sufficient; safety
gates approval). For field 8 (safety profile), when comparing antibodies
targeting the same epitope/domain, note whether the affinity-matured variant
introduced new safety signals absent in the parent antibody.

This is the clearest "safety gate" example in the infectious disease profile
set: a more potent antibody against the same target was rejected because the
incremental efficacy did not justify the safety risk. (PMID 36800182.)

## 5. Science (AAAS) papers with PMCIDs retrieve full text normally

Both McLellan 2013 Science papers (PMID 23618766, PMID 24179220) have PMCIDs
(PMC4459498, PMC4461862) despite being published in Science — a publisher
that typically blocks jina with Cloudflare CAPTCHA. The paper-ingest skill
already documents that "some Science papers DO have a PMCID" and PMC XML
efetch works normally. This session confirms the pattern for landmark RSV F
structural papers: the two most important structural/vaccine design papers
were fully accessible via PMC XML, providing 10.9K and 23.7K chars of body
text respectively. For orchestrators: when selecting landmark papers for
viral structural biology targets, Science papers with PMCIDs are
high-value, fully accessible sources — prefer them over paywalled NEJM
clinical trial papers. (PMID 23618766, PMID 24179220.)

## 6. NEJM nirsevimab trials: abstract-only but abstracts are self-sufficient

Both nirsevimab clinical trial papers (Hammitt 2022 MELODY, Griffin 2020
Phase 2b) were published in NEJM with no PMCID. Jina was blocked by
Cloudflare (~460-474 bytes CAPTCHA page), and the Wayback availability API
returned 429. The paper-ingest skill documents the Wayback CDX API as a
fallback for NEJM, but in this session the CDX API was not attempted (the
abstract was sufficient). The NEJM structured abstracts (2087 and 2282
chars) contained complete trial design (randomization ratio, population,
dose, primary endpoint), full efficacy results (percent reduction, CI,
P-value, event counts), and safety data (AE rates, SAE rates, no
hypersensitivity). For field 3 (disease evidence) and field 4 (antibody
landscape), the NEJM structured abstract was self-sufficient — the profile
did not need full text for these clinical trial papers. The full-text
content came from the structural/biology papers (PMC XML) and the
meta-analysis (PMC XML OA), which grounded fields 2, 5, and 6. This
validates the pattern: for clinical trial papers, the structured abstract
is often sufficient; for structural/biology papers, full text is essential.
(PMID 35235726, PMID 32726528.)

## 7. PubMed search strategy for viral targets with multiple antibody names

The initial search `RSV F AND (palivizumab OR nirsevimab) AND review[pt]`
returned 0 results because the pre-encoded `%5B` brackets in the search term
were double-encoded by the URL construction. The fix (already documented in
paper-ingest) is to use `urllib.parse.quote()` on raw terms with natural
brackets. After fixing: `palivizumab AND review[pt]` returned 374 results,
`nirsevimab AND review[pt]` returned 117. Broader queries without the
`[pt]` filter but with `[tiab]` for "review" in title/abstract returned 270
results. The highest-value structural papers (McLellan 2013) were found via
a separate search for prefusion/structure/epitope terms, not via the
palivizumab/nirsevimab review searches.

For viral targets with multiple approved antibody names, search each
antibody name separately (they may not co-occur in the same paper), then
search the target biology separately (prefusion, structure, epitope,
neutralizing). The structural biology papers are often NOT tagged as
reviews and will be missed by review-filtered searches. Always include
non-review queries for structural/biology papers. (Search session,
2026-08-16.)

(RSV F glycoprotein profile, ~39K chars, 5 papers, 83 authors, 5 unique
PMIDs cited, working-docs/hitlist-profiles/rsv-f-glycoprotein.md.)
