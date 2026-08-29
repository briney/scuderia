# P. falciparum MSP-1 — profile observations

**Profile:** `working-docs/hitlist-profiles/p-falciparum-msp-1.md`
**Date:** 2026-08-17
**Tier:** preclinical (infectious disease)
**Retrieval:** lightweight pipeline — direct PubMed E-utilities via `urllib.request`. 3 initial esearch queries (two quoted `[tiab]` queries returned 0 hits — broadened to boolean AND-style; one succeeded). 3 supplementary queries (antibody+vaccine+clinical trial variants) surfaced 18 additional PMIDs. 40 unique PMIDs collected; 18 landmark abstracts fetched via efetch XML + ElementTree parsing. Abstract-only ingestion. ~43K chars, 18 unique PMIDs cited.

## Key new patterns

### 1. Inhibitory/blocking/neutral antibody paradigm — immune evasion via antigenic CONSERVATION

MSP-1 has a unique 3-class antibody system defined by functional effect on MSP-1(42) processing: **inhibitory** antibodies (block secondary processing and erythrocyte invasion, e.g., mAbs 12.8, 12.10), **blocking** antibodies (bind MSP-1 and prevent inhibitory antibodies from functioning, e.g., mAbs 1E1, 7.5), and **neutral** antibodies (neither). The critical insight: blocking antibodies target CONSERVED epitopes — this is immune evasion based on antigenic conservation, not diversity. The parasite tolerates antibodies against conserved blocking epitopes because they neutralize the protective response. This inverts the usual immune evasion logic (antigenic variation/diversity) and has direct vaccine design implications: a vaccine antigen must be engineered to present inhibitory but not blocking epitopes (PMID 10697894, 11292349, 19081386).

**Rule (generalizes to any vaccine antigen target with blocking-antibody phenomena):** when a target has a blocking-antibody mechanism, fields 5 (epitope), 6 (failure modes), and 11 (differentiation) must explicitly address it. Field 5 should classify epitopes as inhibitory vs blocking (not just neutralizing vs non-neutralizing). Field 6 must list "blocking antibody immune evasion" as a failure mode. Field 11 should note that a therapeutic (passively administered) antibody bypasses the blocking-antibody problem entirely — it can be engineered to bind only the inhibitory epitope, unlike active vaccination which elicits a polyclonal response. This is a key differentiation argument for therapeutic vs vaccine approaches against such targets.

### 2. Vaccine-only antibody landscape — decades of vaccine trials, zero therapeutic antibodies

MSP-1 has 7+ vaccine candidates that reached Phase I/IIa clinical trials (FMP1/AS02A, MSP1(42)-C1, FVO MSP1(42)/AS01, JAIVAC-1, PfCP-2.9, RTS,S+FMP1 combination) — yet NO therapeutic anti-MSP-1 monoclonal antibody has ever been developed. The entire antibody landscape is vaccine-focused. This is a distinct pattern from toxin targets (anthrax PA, PEA) where passive immunization (raxibacumab, obiltoxaximab) was developed alongside vaccines. The gap exists despite MSP-1 being surface-expressed, antibody-accessible, essential for egress/invasion, and parasite-specific with no human homolog.

**Rule (generalizes to any vaccine antigen target with no therapeutic antibody pipeline):** when a target has extensive vaccine history but no therapeutic antibody program, field 4 (antibody landscape) should explicitly document this asymmetry. Field 10 (competitive landscape) should list the gap as "no therapeutic antibody — the entire pipeline is vaccine-focused." Field 11 should position a therapeutic antibody as a fundamentally different approach that bypasses the vaccine-specific challenges (MHC restriction, adjuvant dependence, blocking antibody elicitation, polyclonal response variability).

### 3. Clinical trial paper search as a separate query strategy

Adding a separate esearch query for clinical trials (`MSP-1 vaccine clinical trial Plasmodium falciparum`) surfaced 7 additional Phase I/IIa clinical trial papers that the initial antibody/structure/mechanism searches missed entirely. These papers were critical for field 3 (disease evidence — clinical trial outcomes), field 4 (antibody landscape — vaccine-induced antibodies), and field 6 (failure modes — limited clinical efficacy). The initial 3 search queries (antibody, structure, mechanism) returned 40 PMIDs but included ZERO clinical trial papers.

**Rule (generalizes to all target profiling):** always run a dedicated clinical trial search query in addition to the antibody/mechanism/structure queries. The query template: `<target name> vaccine clinical trial <pathogen>`. This surfaces Phase I-III papers that are not tagged with `[tiab]` terms like "antibody" or "structure" and would be missed by mechanistic searches. Clinical trial papers are essential for fields 3, 4, 6, and 8. Add this as a standard 4th query in the search sequence.

### 4. E-utilities esummary is more aggressively rate-limited than esearch

In this session, esearch calls succeeded while the very next esummary call returned HTTP 429. This confirms the known rate-limit pattern but adds the observation that esummary (batch ID lookup) is more aggressively throttled than esearch (query). The fix: wait 15+ seconds after the last esearch before issuing the first esummary, and batch esummary in groups of ≤10 PMIDs per call with 8s sleeps between batches.

**Rule (refines the existing rate-limit guidance):** the rate-limit hierarchy is esearch < esummary < efetch. When running all three in sequence, insert progressively longer sleeps: 3–5s after esearch, 8–10s before esummary, 5–8s between esummary batches, 5–8s before efetch. If esummary returns 429, wait 15+s (not 5s) before retry — the shorter wait is insufficient for the esummary throttle window.

### 5. Parasite surface protein — conformational epitope dependence and narrow temporal window

MSP-1(19) epitopes are conformational (disulfide-bond-dependent EGF-like domains). Antibody recognition requires properly folded protein — linear peptides alone are insufficient for inhibitory antibody binding. Additionally, merozoites are extracellular for only minutes between egress and invasion, creating a narrow temporal window for antibody-mediated neutralization. This is distinct from: (a) secreted toxins (anthrax PA, PEA) where the target circulates and antibodies have extended exposure; (b) cell-wall-anchored bacterial enzymes (SrtA) where the target is behind the peptidoglycan barrier; (c) viral glycoproteins (EBOV GP) where the target is on the virion surface.

**Rule (generalizes to any parasite surface protein target with brief extracellular exposure):** for parasite surface proteins (merozoite antigens, sporozoite antigens), field 9 (structural) must document the conformational epitope requirement (disulfide-bond-dependent, EGF-like, etc.) and field 11 (known risks) must flag the narrow temporal window as a therapeutic challenge. The brief exposure window means a therapeutic antibody must be present at prophylactic levels — it cannot be administered reactively after infection is established. This shapes the deployment strategy (prophylaxis, not treatment) and the dosing requirement (sustained trough levels).

## Profile statistics

- 11/11 fields present, all verified
- 18 unique PMIDs cited (foundational mechanism, structural biology, epitope mapping, vaccine clinical trials, immune evasion, epidemiological protection)
- 18 landmark abstracts fetched and distilled (10 core + 8 clinical trial/supplementary)
- 0 therapeutic anti-MSP-1 antibodies profiled (field 4 — no therapeutic antibody pipeline exists)
- 4 characterized research mAbs documented (inhibitory: 12.8, 12.10; blocking: 1E1, 7.5)
- 7 vaccine candidates documented across Phase I/IIa trials
- Full-length MSP-1 cryo-EM structure (2021, PMID 34078606) grounded fields 1 and 9
- Field 11 differentiation: therapeutic antibody bypasses blocking-antibody problem; non-canonical epitopes (spectrin-binding site, dimerization interface) from 2021 structure are unexplored
