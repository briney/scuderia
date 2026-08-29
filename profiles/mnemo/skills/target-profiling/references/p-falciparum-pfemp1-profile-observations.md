# P. falciparum PfEMP1 — profile observations

**Profile:** `working-docs/hitlist-profiles/p-falciparum-pfemp1.md`
**Date:** 2026-08-17
**Tier:** preclinical (infectious disease)
**Retrieval:** lightweight pipeline — direct PubMed E-utilities via `urllib.request`. 5 PubMed query variants (3 exact-phrase `[tiab]` queries all returned 0 hits — broadened to unfielded queries without `[tiab]` restriction, which returned 33–536 hits each). 67 unique PMIDs collected, 5 landmark + 10 supporting abstracts fetched via efetch XML + ElementTree parsing. One HTTP 429 on efetch — waited 18 s and retried successfully. Abstract-only ingestion. No single UniProt ID (multi-gene family). ~51K chars, 28 unique PMIDs cited.

## Key new patterns

### 1. Antigenic-variation target class — the central challenge is polymorphism, not accessibility

PfEMP1 is the first target profiled where the primary obstacle to antibody therapy is **antigenic variation via a multi-gene family**, not target accessibility, Fc effector function, or epitope identification. Each P. falciparum genome encodes ~60 `var` genes; only one is expressed at a time (allelic exclusion, PMID 16382237). As antibodies against the expressed variant develop, parasites switch to a different variant — evading the immune response. This is fundamentally different from all prior infectious disease targets:

- **Secreted toxins** (PEA, anthrax EF): challenge is neutralization potency; one serotype, one target.
- **Viral glycoproteins** (EBOV GP, SUDV GP, YFV E, EBV gp350): challenge is strain/serotype coverage; quasi-species variation but typically one dominant variant per infection.
- **Bacterial surface proteins** (SrtA, SpA): challenge is accessibility (cell-wall barrier) or immune evasion (Fc binding); limited antigenic variation.
- **Parasite antigens with antigenic variation** (PfEMP1): challenge is within-host, within-infection polymorphism — the parasite actively switches the target protein to escape immunity. The antibody must either (a) be broadly cross-reactive across many variants, or (b) target a conserved functional epitope that cannot be mutated without losing receptor binding.

**Rule (generalizes to any antigenic-variation parasite target — PfEMP1, trypanosome VSG, Giardia variant-specific surface proteins):** For field 2 (biological mechanism), document the antigenic variation mechanism explicitly (gene family size, switching rate, allelic exclusion). For field 6 (failure modes), "antigenic variation evading variant-specific antibodies" is THE central failure mode — more important than epitope, format, or dosing. For field 11 (differentiation), the key question is whether the antibody targets conserved receptor-binding-site residues (broadly inhibitory) or variant-specific epitopes (narrowly protective). The profile should classify known antibodies by breadth: variant-specific, group-specific, or broadly cross-reactive.

### 2. Conserved receptor-binding-site epitopes overcome antigenic variation

The 2024 Nature paper (PMID 39567685) is the landmark demonstrating that broadly inhibitory antibodies CAN be generated against PfEMP1 by targeting conserved residues within the receptor-binding site. Two human mAbs from different individuals both targeted three conserved EPCR-binding-site residues in CIDRα1, inhibiting 5 of 6 CIDRα1 subclasses and blocking sequestration in 3D brain microvessels. Similarly, mAb02 (PMID 41053123) targets a conserved epitope in the DBLβmotif ICAM-1-binding site, conserved across cerebral malaria-associated variants.

**Rule (the receptor-binding-site conservation principle):** For antigenic-variation targets, the receptor-binding site is functionally constrained — the parasite cannot mutate these residues without losing receptor binding and thus losing its virulence mechanism. This makes the receptor-binding site the sweet spot for broadly inhibitory antibodies, even when the rest of the protein is hyperpolymorphic. For field 5 (epitope landscape), prioritize mapping conserved residues within receptor-binding interfaces. For field 11 (differentiation), "targeting the conserved receptor-binding-site epitope" is the primary differentiation strategy for antigenic-variation targets — analogous to targeting the CD4 binding site on HIV gp120 or the fusion peptide on influenza HA. This principle generalizes to any antigenic-variation pathogen target where receptor binding is functionally constrained.

### 3. Multi-gene family targets have no single UniProt ID

PfEMP1 is a polymorphic multi-gene family with ~60 members per genome and thousands of variants across isolates. There is no single UniProt entry for "PfEMP1." Field 1 (target identity) handled this by: (a) noting the gene family (`var` genes), (b) providing a representative UniProt ID for a well-characterized member (VAR2CSA, Q8IHW5 for 3D7 strain), and (c) classifying by domain architecture (DBL/CIDR domain classes) rather than a single canonical sequence. This is distinct from all prior targets which had a single canonical UniProt entry.

**Rule (generalizes to any multi-gene family target — PfEMP1/var, trypanosome VSG, IgSF variable-domain families, TCR/BCR variable regions):** When a target is a multi-gene family rather than a single gene, field 1 should: (a) state explicitly that no single UniProt ID exists, (b) provide a representative/well-characterized member's UniProt ID as a reference point, (c) classify by domain architecture or sequence class rather than a single sequence, and (d) note the family size (genes per genome) and diversity level. The "gene symbol" field becomes a gene family name, not a single gene. Do NOT force a single UniProt ID — this misrepresents the target's biology.

### 4. Unfielded queries as the fallback when both quoted AND unquoted [tiab] fail

The existing pitfall (lines 414–429 of SKILL.md) documents that quoted `[tiab]` queries return 0 for multi-word terms while unquoted AND-joined `[tiab]` queries succeed. This session revealed a third tier: for "PfEMP1 antibody", even unquoted AND-joined `[tiab]` returned 0. The fix was to drop the `[tiab]` field restriction entirely and use unfielded queries (e.g., `PfEMP1 antibody` without any field tag), which returned 340 hits. The progression is:

1. `"PfEMP1 antibody"[tiab]` (quoted, field-restricted) → 0 hits (exact phrase never appears)
2. `PfEMP1 antibody[tiab]` (unquoted, field-restricted) → 0 hits (both terms in title/abstract — but PubMed's AND-joined `[tiab]` syntax can still fail for certain term combinations)
3. `PfEMP1 antibody` (unfielded) → 340 hits (both terms anywhere in the record)

**Rule (extends the existing [tiab] pitfall to a three-tier fallback):** When `[tiab]` queries return 0, do not conclude "no literature." The fallback sequence is: (1) quoted `[tiab]` → (2) unquoted AND-joined `[tiab]` → (3) completely unfielded (no field tag) → (4) unfielded with additional synonymous terms (`Plasmodium falciparum erythrocyte membrane protein 1 antibody` → 536 hits). The unfielded query searches all PubMed fields (title, abstract, MeSH terms, keywords) and has the highest recall. For target profiling, recall is more important than precision — you will manually screen the results for relevance. Always have unfielded query variants pre-written.

### 5. Fc glycoengineering (afucosylation) as a correlate of protection for parasite antigens

Afucosylated anti-VAR2CSA IgG correlated with protection from placental malaria in pregnant Malawian women (PMID 42446379). Afucosylation enhanced FcγRIIIa/b engagement, neutrophil phagocytosis, and NK cell degranulation. This extends the Fc-engineering pattern from the M. tb LAM profile (where Fc-effector function was a binary requirement) to a new mechanism: for parasite surface antigens displayed on infected host cells (IEs), Fc-mediated opsonization/phagocytosis of the entire infected cell is a protective mechanism alongside direct receptor-binding blockade.

**Rule (extends the Fc-effector function pattern to parasite antigens on host cells):** For targets displayed on infected host cells (PfEMP1 on IEs, viral antigens on infected cells), the antibody has two independent protective mechanisms: (a) Fab-mediated receptor-binding blockade (preventing cytoadherence/sequestration) and (b) Fc-mediated opsonization/phagocytosis of the infected cell (clearing the parasite). For field 6 (success factors), note that Fc glycoengineering (afucosylation) enhances mechanism (b). For field 11 (differentiation), an afucosylated anti-PfEMP1 mAb would combine both mechanisms — dual blockade + enhanced clearance. This is unexplored for severe malaria mAbs (demonstrated only for VAR2CSA). Generalizes to any antibody targeting a pathogen antigen displayed on the surface of infected host cells.

### 6. No robust animal model for human-only pathogens

P. falciparum infects humans (and limited primate species). No robust small-animal model exists for blood-stage P. falciparum infection. Humanized SCID mouse models with human skin grafts have been used (PMID 12393525), and Aotus monkeys support limited infection (PMID 37932470), but neither is standardized for mAb efficacy testing. This creates regulatory uncertainty — the FDA Animal Rule pathway may apply but requires robust animal data.

**Rule (generalizes to any human-only pathogen target — P. falciparum, P. vivax, HIV, HBV, HCV):** When no robust animal model exists for the target pathogen, field 7 (assay systems) must document the available surrogate models and their limitations explicitly. For field 11 (differentiation, known risks), "no validated animal model for efficacy" is a critical regulatory risk that affects development strategy. The FDA Animal Rule pathway may apply but requires robust, well-characterized animal models — if none exist, the development timeline and regulatory pathway are fundamentally uncertain. Bioengineered 3D tissue models (e.g., 3D human brain microvessels, PMID 39567685) may serve as novel preclinical efficacy readouts but are not yet regulatory-accepted.

## Profile statistics

- 11/11 fields present, all verified
- 28 unique PMIDs cited (range of evidence types: foundational domain mapping, comprehensive review, in vivo anti-adhesive therapy, structural biology, phagocytosis-inducing mAbs, complement-PfEMP1 interaction, broadly inhibitory human mAbs, cerebral malaria mAb, VAR2CSA vaccine Phase 1, antibody dynamics in infants, CHMI predictive profiles, Fc glycoengineering, structure-guided immunogen design)
- 15 abstracts fetched and distilled (5 landmark + 10 supporting)
- 0 anti-PfEMP1 therapeutic mAbs in clinical development (field 4 — all preclinical)
- 1 vaccine (PAMVAC) in Phase 1 (field 4 — active immunization, not mAb)
- No single UniProt ID (multi-gene family — representative: VAR2CSA Q8IHW5)
- Field 11 differentiation: conserved receptor-binding-site epitopes (CIDRα1 EPCR-binding site, DBLβmotif ICAM-1-binding site) as the primary strategy; bispecific anti-CIDRα1 + anti-DBLβmotif; Fc glycoengineering (afucosylation); combination with artemisinin therapy; AAV-delivered mAbs for prophylaxis
