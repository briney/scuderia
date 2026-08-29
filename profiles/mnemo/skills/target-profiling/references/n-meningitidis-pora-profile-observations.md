# N. meningitidis PorA — profile observations

**Profile:** `working-docs/hitlist-profiles/n-meningitidis-pora.md`
**Date:** 2026-08-17
**Tier:** preclinical (infectious disease)
**Retrieval:** lightweight pipeline — direct PubMed E-utilities via `urllib.request` + UniProt REST. Task-brief `[tiab]` queries ("Neisseria meningitidis PorA antibody"[tiab], "porin A meningococcal"[tiab]) returned 0 hits; broadened to non-[tiab] boolean queries ("PorA meningococcal" → 25, "meningococcal PorA serosubtype" → 25). 43 unique PMIDs from 4 searches. esummary batch (20 PMIDs/batch) used to triage by title; 12 landmark abstracts fetched via efetch XML. Supplementary searches for Norwegian OMV trial, 4CMenB/Bexsero, crystal structures, and mAbs recovered 8 additional papers (20 total). UniProt P0DH58/P18194/P13415 fetched for MW and function. Abstract-only ingestion. ~45K chars, 25 unique PMIDs cited.

## Key new patterns

### 1. Vaccine-antigen target — a new target class: vaccine-validated, antibody-pipeline-empty

PorA is the first profiled target where the target is **primarily a vaccine antigen, not a therapeutic antibody target**. The entire clinical evidence base (Norwegian OMV efficacy trial, hexavalent PorA OMV Phase I/II, 4CMenB/Bexsero approval) is vaccine-derived. No anti-PorA therapeutic antibody has ever entered clinical development. This fundamentally changes the profile structure:

- **Field 3 (disease evidence)** is dominated by vaccine trials, not antibody trials. The evidence types are "vaccine efficacy" and "vaccine immunogenicity," not "antibody clinical trial."
- **Field 4 (antibody landscape)** lists research mAbs (MN12H2, MN14C11.6, MN5C11G, MN20F4.17) characterized for epitope mapping and passive protection in infant rats — none is a clinical-stage therapeutic.
- **Field 10 (competitive landscape)** is organized around vaccine products (Bexsero, hexavalent PorA OMV, Norwegian OMV, MeNZB), not antibody pipelines. The "pipeline depth" metric is vaccine depth, not antibody depth.
- **Field 11 (differentiation)** must argue why a therapeutic antibody would complement (not replace) the vaccine — a fundamentally different framing from targets where antibodies are the only modality.

**Rule (new target class — generalizes to any vaccine-validated antigen):** when the target's clinical validation comes entirely from vaccines and no therapeutic antibody exists, the profile must: (a) frame field 3 around vaccine evidence while noting the antibody gap; (b) list research/characterization mAbs in field 4 with explicit "preclinical — research reagent" phase labels; (c) organize field 10 by vaccine competitive landscape, noting "zero antibody therapeutics in clinical development"; (d) make field 11's lead differentiation opportunity the case for a therapeutic antibody where vaccines have gaps (outbreak response/passive immunotherapy, complement-deficient patients, serosubtype-independent coverage). This applies to any vaccine antigen target (PorA, PorB, fHbp, NadA, NHBA, pneumococcal PspA, etc.).

### 2. Antigenic variation as the defining target-selection challenge for bacterial surface porins

PorA's VR1 (loop 1) and VR2 (loop 4) are the immunodominant epitopes, but they are also the most variable regions. Single amino acid changes in VR2 completely abrogate mAb-mediated protection in vivo (PMID 11273739). Hundreds of VR sequence variants exist (PMID 15200858). This is a fundamentally different challenge from toxin targets (PEA, anthrax EF) where the neutralization epitopes are relatively conserved, and from viral glycoproteins (EBOV GP, RSV F) where variation exists but is slower.

The profile must capture: (a) the VR family nomenclature system and its scale (P1.10a–g, P1.16a–d); (b) the experimental evidence that single residue changes abrogate protection (isogenic mutant panel in infant rats); (c) the field 11 opportunity — an antibody targeting conserved non-VR loops (loops 2, 3, 5–8) would be serosubtype-independent, but these are non-immunodominant and may require active immunization or rationally designed antibodies rather than natural infection to elicit.

**Rule (generalizes to antigenically variable bacterial surface targets):** when the immunodominant epitopes are also the most variable, field 5 must explicitly map the variation landscape (VR families, variant nomenclature), field 6 must list "antigenic variation → immune escape" as the primary failure mode with specific evidence (variant-specific protection loss), and field 11 must identify conserved epitopes outside the variable regions as the key differentiation opportunity. This applies to PorA, PorB, Opa, OpcA, and other variable outer membrane proteins of Neisseria.

### 3. Phase variation / target loss as an escape mechanism distinct from antigenic variation

PorA-deficient meningococci caused an outbreak of 7 cases (5/7 PorA-negative) in the Netherlands (PMID 12599063). PorA expression is phase-variable via slipped-strand mispairing in a poly-G tract. This is a distinct escape mechanism from antigenic variation (point mutations in VRs): the target protein is entirely absent from the bacterial surface. A PorA-only vaccine or antibody provides zero protection against PorA-negative strains. This is relevant to field 6 (failure modes) and field 11 (a bispecific targeting PorA + a conserved OMP like PorB or fHbp would address this).

**Rule (generalizes to phase-variable bacterial surface targets):** when a bacterial surface target is phase-variable (poly-G/C tracts, slipped-strand mispairing), field 6 must list "target loss via phase variation" as a distinct failure mode from antigenic drift, with evidence of clinical transmission of target-negative strains. Field 11 should recommend bispecific/multicomponent approaches targeting non-phase-variable conserved antigens as the mitigation. This applies to PorA, Opa, OpcA, PilC, and other phase-variable Neisseria proteins.

### 4. Complement dependence as a target-specific vulnerability — the MAC-dependence distinction

Anti-PorA antibody protection in infant rats is impaired in C6-deficient rats (lacking MAC), while anti-capsular polysaccharide antibody protection is not (PMID 16622217). This means anti-PorA antibodies require the full complement cascade (MAC-mediated lysis) for protection, while anti-capsular antibodies can protect via opsonophagocytosis alone. This is clinically significant because complement-deficient individuals (C5–C9, properdin) are at 7,000–10,000-fold elevated risk of meningococcal disease — the exact population most in need of passive immunotherapy is the one where anti-PorA antibodies would be least effective.

**Rule (generalizes to complement-dependent antibody targets):** when passive protection data shows differential complement dependence (MAC-dependent vs MAC-independent), field 6 must document this as a target-specific vulnerability, field 8 must note the complement-dependence implications for high-risk populations, and field 11 must recommend Fc engineering for enhanced opsonophagocytosis (FcγR engagement) as a differentiation strategy to shift the mechanism from MAC-dependent lysis to complement-independent phagocytosis. This is relevant to any bacterial surface target where the antibody mechanism is complement-mediated lysis (PorA, PorB, fHbp, capsular polysaccharide).

### 5. UniProt for bacterial targets: multiple strain-level entries, not one canonical entry

PorA has multiple UniProt accessions: P0DH58 (strain MC58, serogroup B), P18194 (serogroup C), P13415 (serogroup C). Unlike human targets (one canonical entry per gene), bacterial targets often have multiple entries corresponding to different strains, serogroups, or serosubtypes. The most relevant entry depends on the strain context of the profile. For PorA, P0DH58 (MC58) is the most commonly referenced in structural studies, but the serosubtype-specific variation means no single entry represents all variants.

**Rule:** for bacterial targets, search UniProt by protein name + organism (not by a single accession). Expect multiple entries; note in field 1 that strain-level variation produces multiple UniProt accessions, and cite the most relevant one(s) for the profile's strain context. Do not assume a single canonical entry as with human targets.

### 6. Regex XML parsing worked but ElementTree remains the safer default

This session used `re.findall(r'<PubmedArticle>(.*?)</PubmedArticle>', xml, re.DOTALL)` to parse PubMed efetch XML, which correctly extracted all 12+8 articles with full abstracts. This worked because PubMed XML is well-formed and each `<PubmedArticle>` element is self-contained. However, the established pitfall (from the PEA profile) notes that greedy regex matching can cross article boundaries. The regex used here was non-greedy (`.*?`) which prevents cross-boundary matching. **ElementTree remains the recommended default** — but non-greedy regex with self-closing article delimiters is a viable fallback when ElementTree is not available or when the XML structure is simple and predictable.

## Profile statistics

- 11/11 fields present, all verified
- 25 unique PMIDs cited (identity/molecular, biophysical, structural, epitope mapping, vaccine trials, passive protection, outbreak investigation, vaccine quantification)
- 20 landmark abstracts fetched and distilled (12 primary + 8 supplementary)
- 4 research mAbs profiled (field 4): MN12H2 (anti-P1.16, crystal structure solved), MN14C11.6 (anti-P1.7), MN5C11G + 62D12-8 (anti-P1.16), MN20F4.17 (anti-P1.10, serosubtyping reagent)
- 2 vaccine-elicited antibody responses profiled (hexavalent PorA OMV, 4CMenB/Bexsero)
- 2 Fab–peptide crystal structures (field 9): P1.7 peptide at 1.95 Å (PMID 10512717), P1.16 peptide at 2.6 Å (PMID 9294871)
- Field 11 lead differentiation: bispecific anti-PorA + conserved OMP (addresses both antigenic variation and phase variation); Fc engineering for opsonophagocytosis (addresses complement dependence)
