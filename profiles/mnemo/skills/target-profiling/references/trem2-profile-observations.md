# TREM2 profile observations (2026-08-16)

**Target**: TREM2 (Triggering receptor expressed on myeloid cells 2)
**Tier**: Clinical-trial
**Area**: Neuroscience (Alzheimer's disease)
**Papers ingested**: 5 (PMID 23150908, 28802038, 39444037, 41787076, 40806186)
**Full-text rate**: 3/5 (60%) — 2 EPMC XML OA, 1 jina reader; 2 abstract-only (NEJM, Nature Medicine)
**Profile**: ~34.5K chars, 272 lines, 8 unique PMIDs cited

## Retrieval observations

1. **PMC HTML endpoint now returns CAPTCHA interstitials, not XML.** The `pmc.ncbi.nlm.nih.gov/pmc/articles/{PMCID}/?report=xml` URL returns an HTML page with a reCAPTCHA challenge ("Checking your browser before accessing pmc.ncbi.nlm.nih.gov") rather than XML full text. This affected multiple papers. The reliable path is **Europe PMC full text XML** (`ebi.ac.uk/europepmc/webservices/rest/{PMCID}/fullTextXML`) for OA papers, which returned 48K–110K chars of valid full text. For future profiling sessions, skip the PMC HTML endpoint and go directly to EPMC full text XML. (PMID 39444037, 40806186, 29321225.)

2. **EPMC PMID search returns wrong papers — use EXT_ID instead.** Searching Europe PMC with `query=PMID:{pmid}` sometimes returned a completely different paper (e.g., searching for PMID 23150908 returned a paper about osteoclasts/microglia). Using `query=EXT_ID:{pmid}` reliably returned the correct paper with correct DOI, PMCID, and metadata. Always use `EXT_ID:` for EPMC PMID lookups during profiling.

3. **PubMed efetch PMCIDs can be stale/incorrect — always verify retrieved content.** The PubMed XML `<ArticleId IdType="pmc">` field sometimes carries a wrong PMCID. For PMID 39444037, efetch returned PMCID `PMC8219697`, but the correct PMCID (from EPMC) was `PMC11515656`. Using the wrong PMCID retrieved a completely different paper (a Scientific Reports sTREM2 biomarker paper). For PMID 41787076, efetch returned `PMC6433910`, but the correct PMCID was none (not in PMC). Always cross-check PMCID from EPMC metadata against PubMed efetch before fetching full text, and verify retrieved content contains target-specific terms (e.g., "TREM2", "AL002") before using it.

4. **Nature Medicine jina false positive — references only, no article body.** PMID 41787076 (AL002 Phase 2, Nature Medicine 2026) was retrieved via jina reader on the DOI URL — 46K chars. However, the content was entirely references, figure descriptions, and author information — no abstract, results, or discussion sections. The EPMC structured abstract (1,398 chars with full trial design, N=381, dosing, primary endpoint CDR-SB, LSM differences, CIs, and ARIA safety finding) was self-sufficient for profile grounding. For Nature Medicine clinical trial papers, EPMC abstract is the primary content source; jina may return reference-only false positives.

5. **NEJM papers remain abstract-only despite having PMCIDs.** PMID 23150908 (Jonsson 2013, NEJM) has PMCID PMC3677583 (from EPMC), but EPMC full text XML returned 0 chars. Jina reader on NEJM returned 474 chars (blocked). Wayback API returned HTTP 429 (rate limited even after 15s wait). The PubMed structured abstract (1,893 chars with full Background/Methods/Results/Conclusions) was sufficient for profile grounding. This confirms the pattern: NEJM papers are abstract-only at the profiling level; the structured PubMed abstract carries enough detail for fields 2, 3, and 6.

## Neuroscience-specific observations

6. **First neuroscience target profiled.** TREM2 is the first neuroscience target in the profile corpus (all prior profiles: immunology, oncology, infectious disease, cardiovascular/metabolic). Key differences from immunology/oncology targets:
   - **Target is a microglial receptor** (CNS-resident innate immune cell), not a peripheral immune cell cytokine/receptor. The biology centers on neuroinflammation, phagocytosis, and blood-brain barrier interactions rather than T cell/B cell trafficking or cytokine signaling.
   - **Species cross-reactivity is a critical barrier.** AL002 does NOT bind rodent TREM2 — preclinical studies required cynomolgus monkeys (toxicology/PK) and humanized TREM2 knock-in mice (hTREM2-5×FAD) for efficacy. Standard mouse/rat AD models cannot be used. For field 2 (species cross-reactivity) and field 7 (assay systems), this is a major constraint unique to neuroscience targets with species-specific epitopes.
   - **Therapeutic approach is agonist, not antagonist.** Unlike all prior profiles (blocking/depleting antibodies), TREM2 antibodies are agonists designed to ENHANCE microglial function. This inverts the antibody landscape: the goal is receptor activation, not blockade. For field 4, note the agonist mechanism explicitly. For field 6, success/failure factors are about receptor activation dynamics (internalization, desensitization) rather than target depletion or pathway blockade.
   - **ARIA as a novel safety signal.** The most frequent TEAE in INVOKE-2 was MRI changes resembling ARIA (amyloid-related imaging abnormalities) — a safety signal typically associated with anti-amyloid antibodies but observed with a microglial target. For field 8 (safety), CNS-specific adverse events like ARIA may be a class effect of microglial-targeting antibodies in the context of cerebral amyloid angiopathy.

7. **First negative Phase 2 trial profiled.** INVOKE-2 (PMID 41787076) is the first Phase 2 clinical failure in the profile corpus. Key field 6 observations:
   - **Target engagement ≠ efficacy.** AL002 demonstrated robust, sustained target engagement (CSF sTREM2 reduction, osteopontin increase) yet showed no clinical benefit on CDR-SB. This is a critical lesson: pharmacodynamic biomarkers confirm mechanism but do not predict therapeutic efficacy, especially for neuroprotective/neuroimmunomodulatory targets.
   - **Receptor internalization as self-limiting mechanism.** AL002's stalk-binding epitope induces receptor cross-linking → activation → internalization → degradation (ITAM-containing receptor property). This may limit sustained signaling efficacy — the agonist depletes the very receptor it activates. For field 6, document internalization kinetics as a potential failure mechanism for agonist antibodies.
   - **Treatment timing hypothesis.** The INVOKE-2 review (PMID 40353063) identifies treatment timing, dosage optimization, patient genetic variability, and combination therapy as critical determinants. Microglial dysfunction may be too advanced in early AD for TREM2 agonism to restore protective function — the therapeutic window may be earlier (preclinical/prodromal).

8. **UniProt and PDB data are readily available for structural fields.** UniProt REST API (`rest.uniprot.org/uniprotkb/search?query=gene:TREM2+AND+organism_id:9606`) returned the full entry with domains, topology, function, and subcellular location in one call. PDB RCSB search API v2 (`search.rcsb.org/rcsbsearch/v2/query` with JSON POST) returned 11 structures for TREM2 including 7 antibody-TREM2 complexes. For field 9 (structural information), UniProt + PDB API queries should be part of the initial data gathering for every target.

(TREM2 profile, ~34.5K chars, 5 papers, 8 unique PMIDs cited,
working-docs/hitlist-profiles/trem2.md.)
