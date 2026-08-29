# EGFR profile observations (2026-08-16)

Twenty-fourth level-2 profile (approved tier, oncology — colorectal,
head/neck, NSCLC). EGFR (epidermal growth factor receptor, ERBB1, HER1,
CD175) is a transmembrane receptor tyrosine kinase, the founding member
of the ErbB/HER receptor family. Three approved anti-EGFR antibodies:
cetuximab (Erbitux, chimeric IgG1, CRC + HNSCC), panitumumab (Vectibix,
fully human IgG2, CRC), necitumumab (Portrazza, fully human IgG1, squamous
NSCLC). 5 key papers ingested, 5 new paper pages written. ~31K chars
(profile), 5 PMIDs cited. Full-text retrieval: 1/5 PMC XML OA (20%),
1/5 jina-reader partial (abstract + references), 3/5 abstract-only.
New observations:

## 1. Fc effector function is NOT essential for anti-EGFR efficacy — the IgG1/IgG2 equivalence pattern

Cetuximab (chimeric IgG1, ADCC-capable via Fcγ receptors on NK cells and
macrophages) and panitumumab (fully human IgG2, minimal ADCC) are both
approved and effective for KRAS wild-type metastatic CRC. This is the
clearest example in the profile set where antibodies with fundamentally
different Fc effector functions (IgG1 with ADCC vs IgG2 without) achieve
comparable clinical efficacy against the same target in the same
indication. The conclusion: for EGFR in CRC, ligand blockade alone
(competitive inhibition of EGF/TGF-α binding and prevention of receptor
dimerization) is the primary therapeutic mechanism — Fc-mediated immune
effector function is not required.

This has important implications for field 6 (success factors) and field 11
(differentiation): when both ADCC-capable (IgG1) and ADCC-silent (IgG2)
antibodies are approved for the same target and indication, the target's
therapeutic mechanism is ligand/signaling blockade, not immune-mediated
killing. For such targets, Fc engineering (afucosylation for enhanced
ADCC) is NOT a differentiation opportunity — it adds complexity without
improving efficacy. The differentiation case must be built on epitope
(non-domain-III antibodies), format (bispecific, ADC, TCE), or population
(KRAS-mutant, HPV-positive HNSCC). (PMID 17171190, PMID 34663410.)

Note: cetuximab's ADCC IS clinically relevant in specific contexts — FcγR
genotype (FcγRIIa-131R, FcγIIIa-158F) correlates with shorter PFS, and
NK cell/CD137 combination strategies enhance cetuximab ADCC in preclinical
models. But the lack of ADCC in panitumumab did not prevent its approval
or efficacy — ADCC is a secondary mechanism, not the primary driver. This
nuance should be captured in field 6, not over-interpreted as "ADCC is
irrelevant for EGFR." (PMID 34663410.)

## 2. KRAS biomarker requirement — the canonical biomarker-driven therapy lesson

Anti-EGFR antibodies only work in KRAS wild-type tumors. KRAS mutations
activate downstream RAS-RAF-MEK-ERK signaling independent of upstream
EGFR, making receptor blockade futile. The CRYSTAL trial (cetuximab +
FOLFIRI) confirmed this: 15% risk reduction and 8.2-month OS benefit
specifically in KRAS WT mCRC. Clinical benefit in responders lasts only
8-10 months, with ~80% developing resistance.

For field 6 (success factors), this is the canonical example of
biomarker-selected population success: the target was correct, the
antibody was correct, but treating unselected patients (including
KRAS-mutant) diluted the effect. The fix was a companion biomarker
(KRAS testing), not a new antibody or epitope. This parallels the IL-5
observation (eosinophil count as companion diagnostic) but predates it
historically and is more widely cited as the founding example of
biomarker-driven oncology therapy.

For field 7 (biomarker assays), KRAS mutation testing is the companion
diagnostic for all anti-EGFR antibodies in CRC. Notably, no equivalent
genetic biomarker exists for necitumumab in squamous NSCLC — histology
itself (squamous vs non-squamous) is the current selection criterion, and
further biomarker research is needed. This gap between CRC (clear
biomarker) and NSCLC (histology only) is a field 11 differentiation
opportunity. (PMID 34663410, PMID 30501503.)

## 3. Epitope-specific ECD mutations as acquired resistance — the domain III resistance problem

EGFR extracellular domain mutations at the antibody-binding interface
(S468R, G465R, G465E, S492R in domain III) prevent cetuximab and
panitumumab binding and confer acquired resistance. The S468R mutation
is the most common cetuximab-resistant variant. This is epitope-specific
resistance — all three approved antibodies target domain III, so a
single mutation can escape all of them.

Strategies to overcome: (1) necitumumab can bind S468R (different binding
interface within domain III); (2) Sym004 (two non-overlapping anti-EGFR
antibodies) abrogates signaling of all individual EGFR mutants and
improved OS by 5.5 months in refractory mCRC; (3) MM-151 (oligoclonal
antibody binding multiple ECD regions) overcomes G465E; (4) GC1118
targets KRAS-mutant CRC with high-affinity ligand expression.

For field 5 (epitope landscape) and field 6 (failure modes), this is the
clearest example of epitope-specific acquired resistance in the profile
set — distinct from downstream pathway resistance (KRAS, BRAF, PI3K) or
compensatory signaling (MET, HER2, IGF-1R). For field 11
(differentiation), multi-epitope approaches (Sym004, MM-151) and
non-domain-III epitopes are validated strategies to overcome ECD
mutation resistance. An antibody targeting domain I, II, or IV would
access a different epitope bin entirely. (PMID 34663410.)

## 4. Histology-specific efficacy — squamous vs non-squamous NSCLC as a selection criterion

Necitumumab is approved ONLY for squamous NSCLC (SQUIRE trial: reduction
in risk-of-death with gemcitabine + cisplatin). The INSPIRE trial in
non-squamous NSCLC was stopped — necitumumab was not effective. This
demonstrates that EGFR dependency differs between squamous and
non-squamous NSCLC histology. The CRC development for necitumumab was
also discontinued, suggesting it did not differentiate from cetuximab/
panitumumab in that setting.

For field 6 (failure modes), histology-specific failure (non-squamous
NSCLC) is a distinct failure mode: the target is expressed and the
antibody is the same, but the tumor biology (squamous vs non-squamous)
determines response. This parallels the HPV-positive vs HPV-negative
HNSCC differential response to cetuximab — in both cases, the target
(EGFR) is overexpressed across histologies, but the biological
dependency on EGFR signaling varies. For field 11 (differentiation),
identifying the biomarker that explains histology-dependent EGFR
dependency (beyond histology itself) is an unmet need. (PMID 26729188,
PMID 30501503, PMID 40996745.)

## 5. JAMA Network CAPTCHA block confirmed for a second oncology profile

PMID 40996745 (Hwang 2025, JAMA Oncol — EGFR-targeted therapy in HNSCC)
was blocked by JAMA Network's CAPTCHA security verification. Jina reader
proxy returned 475 chars — the "Just a moment..." security page. No
PMCID, EPMC OA=N, inPMC=N, hasPDF=N. Wayback CDX returned only 302
redirects. This confirms the JAMA Network block pattern previously
documented (JAMA Dermatol, PMID 39602139) and extends it to JAMA
Oncology. For target profiling, JAMA Oncology papers are abstract-only
and the structured PubMed abstract must be used. The structured abstract
(1,430 chars with Importance/Observations/Conclusions) was sufficient
for distilling key HNSCC findings. (PMID 40996745.)

## 6. Portico (Drugs of Today) block — new publisher encounter

PMID 17171190 (Chua 2006, Drugs of Today — panitumumab review) was
blocked by Portico. The DOI (10.1358/dot.2006.42.11.1032061) resolved
to a Portico cookie preference page (4,175 chars) via jina reader —
not article content. No PMCID, EPMC OA=N, inPMC=N, hasPDF=N. Wayback
CDX returned 503 (service unavailable). This is a new publisher
encounter not previously documented in the skill. Drugs of Today
(journal code "dot") routes through Portico for archival access, and
Portico requires institutional authentication. The 1,649-char EPMC
structured abstract was sufficient for distilling panitumumab's
identity, phase III trial data, safety profile, and biomarker insights.
(PMID 17171190.)

## 7. Springer/Drugs via jina — abstract + references but not body

PMID 26729188 (Garnock-Jones 2016, Drugs — necitumumab first approval)
was retrieved via jina reader proxy on the Springer link.springer.com
URL — 13,567 chars containing the abstract and the complete reference
list (25 references) but NOT the article body text. The page is a
Springer paywall page with "Log in via an institution" and purchase
options. This is a partial retrieval: the reference list was valuable
(identifying the SQUIRE trial [Thatcher et al.], INSPIRE trial [Paz-Ares
et al.], phase I study [Kuenen et al.], and structural basis [Li et al.,
Structure 2008] — all key references for the profile), but the body text
containing development milestones, pharmacology, and detailed trial
results was not accessible. Tagged `fulltext_source: jina-reader` with
a note that content is abstract + references only.

This extends the DLL3 observation (Springer/Adis via publisher-jina
retrieved 23K chars full text) with a counterexample: Springer/Drugs
drug-approval reviews are sometimes retrievable in full (DLL3,
PMID 39023700) and sometimes only abstract + references (EGFR,
PMID 26729188). The difference may be journal-specific (Drugs vs
Adis Insight profiles) or article-age-dependent (2016 vs 2024).
When a Springer drug-approval review returns only abstract + references
via jina, the reference list itself is high-value — it identifies the
pivotal trial, phase I, and structural papers that should be sought
separately. (PMID 26729188.)

## 8. Taylor & Francis/Future Oncology paywall confirmed

PMID 30501503 (Díaz-Serrano 2019, Future Oncol — necitumumab in NSCLC)
was blocked by Taylor & Francis. Jina reader returned 21,419 chars —
the publisher page with abstract, keywords, competing interests
disclosure, and purchase options, but no article body. No PMCID, EPMC
OA=N, inPMC=N, hasPDF=N. The 850-char abstract plus the keyword list
(providing SQUIRE trial, INSPIRE trial, IMC-11F8, squamous cell
carcinoma keywords) were sufficient for distillation. The competing
interests disclosure (Paz-Ares advises Lilly, the maker of necitumumab)
is relevant context for interpreting the review's conclusions.
(PMID 30501503.)

## 9. OA review paper as the primary full-text source — the J Exp Clin Cancer Res pattern

PMID 34663410 (Zhou 2021, J Exp Clin Cancer Res — anti-EGFR resistance
in mCRC) was the ONLY paper with full PMC XML (278,200 bytes, 66,927
chars of body text). This open-access review in Journal of Experimental
& Clinical Cancer Research (Springer/BMC, open access) provided
comprehensive grounding for fields 2 (biological mechanism), 3 (disease
evidence), and 6 (failure modes and success factors) — covering EGFR
biology, KRAS resistance, ECD mutations, compensatory signaling, ADCC
mechanisms, microenvironment resistance, and clinical combination
strategies.

This confirms the pattern noted for CD79b (comprehensive biology review
as highest-value paper for ADC targets) and extends it: for oncology
targets where clinical trial papers are paywalled (JAMA, NEJM, Lancet),
a comprehensive open-access resistance/mechanism review in a BMC/Springer
OA journal can carry the entire full-text grounding burden for the
profile. When selecting 3-5 landmark papers, always include at least one
comprehensive OA review — it may be the only paper with accessible full
text, and review articles in OA journals (J Exp Clin Cancer Res, J
Hematol Oncol, Mol Cancer, Cancers) often provide 60-70K chars of body
text covering all required fields. (PMID 34663410.)

## 10. execute_code + urllib pipeline confirmed for second oncology profile

The entire pipeline ran via execute_code + urllib — PubMed esearch/
esummary/efetch, Europe PMC core records, PMC XML efetch, jina reader
proxy, Wayback CDX. No terminal, no browser. 1/5 full-text via PMC XML
(20% — consistent with the C5 profile's 20% rate, lower than CD79b's
80% because the EGFR paper set targeted high-impact journals [JAMA,
Drugs, Future Oncol] rather than OA-friendly hematology/oncology
journals). Paper pages written via write_file. This confirms the
execute_code + urllib pipeline as the standard for oncology target
profiling and extends the journal-mix observation: the full-text
retrieval rate is driven by journal selection, not by therapeutic area.

(EGFR profile, ~31K chars, 5 papers, 5 PMIDs, 14 unique authors,
working-docs/hitlist-profiles/egfr.md.)
