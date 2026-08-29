# B. anthracis edema factor (EF) — profile observations

**Profile:** `working-docs/hitlist-profiles/b-anthracis-edema-factor.md`
**Date:** 2026-08-17
**Tier:** preclinical (infectious disease / biodefense)
**Retrieval:** lightweight pipeline — direct PubMed E-utilities via `urllib.request` + UniProt REST. 4 PubMed queries (one hit a transient 429, retried after sleep), 41 candidate PMIDs, 10 landmark abstracts fetched via efetch XML. UniProt P40136 + 18 PDB cross-refs via single REST call. Abstract-only ingestion (no full-text retrieval needed — abstracts + UniProt grounded all 11 fields). ~37K chars, 22 unique PMIDs cited.

## Key new patterns

### 1. Read the already-profiled homolog first — toxin-component family reuse (extends the SUDV GP pattern)

B. anthracis EF is the third anthrax-toxin-component target profiled, after **anthrax PA** (`anthrax-pa.md`, approved tier). Loading `anthrax-pa.md` before writing provided: (a) the exact field-depth/format calibration (how field 4 lists approved antibodies, how field 5 bins epitopes by mechanism, how field 3 frames the FDA Animal Rule), and (b) the differentiation axis — every EF field contrasts against the already-characterized PA. The central unmet-need narrative ("anti-EF only blocks edema toxin, not lethal toxin; anti-PA blocks both via the shared delivery component") came directly from the PA profile's field 2 and field 6. The domain map (PA domain 4 = receptor binding = approved-antibody target) transferred and framed EF's three-mechanism epitope landscape.

**Rule (generalizes the SUDV→EBOV rule):** before profiling a target, grep `working-docs/hitlist-profiles/` for its family and load the closest profiled homolog; contrast throughout. For multi-component toxin systems (anthrax PA/EF/LF, botulinum neurotoxin serotypes, Shiga Stx1/Stx2, diphtheria toxin A/B), the homolog is the sibling component, and the differentiation axis is usually "which toxin arm / which delivery step" — not a separate viral species.

### 2. Preclinical-tier toxin-component target with an approved sibling → field 3 + field 10 organized by "approved vs preclinical" gap, not model tier

For SUDV GP (no approved therapy anywhere in the family), field 3 was organized by preclinical model tier (NHP → ferret → rodent → mechanistic). For EF, the *family* already has approved antibodies (anti-PA: raxibacumab, obiltoxaximab, AIGIV), but EF-specific antibodies are all preclinical. Field 3 therefore organized by the **approved-vs-preclinical gap**: (1) the approved anti-PA evidence (cross-referenced, not re-profiled), (2) the preclinical anti-EF disease evidence (mouse ET/spore models), (3) the human-immunogenicity evidence (AVP vaccine induces EF-neutralizing antibodies). Field 10 (competitive landscape) led with "0 approved, 0 clinical, ~5-8 preclinical" and explicitly contrasted pipeline depth against the mature anti-PA field.

**Rule:** when a target's sibling/family member has approved antibodies but the target itself is preclinical, frame field 3 and field 10 around the *gap* (why no anti-EF advanced despite anti-PA success) rather than purely by model tier. The family precedent is the reference standard the profile is measured against.

### 3. "Complementary, not complete, protection" as the central preclinical-toxin narrative — the single-arm-vs-shared-delivery distinction

Anti-EF antibodies only neutralize edema toxin (PA+EF); they do not touch lethal toxin (PA+LF), which is the dominant virulence factor. This is the defining limitation and it shapes fields 2 (effect of blockade), 3 (disease evidence), 6 (failure modes), and 11 (differentiation). The profile makes this contrast in every relevant field, citing the anti-PA profile as the "complete blockade" reference. The corollary — combination/bispecific anti-EF+anti-PA or anti-EF+anti-LF shows synergy in mice (PMID 20385755, PMID 21704379) — became the field-11 differentiation opportunity.

**Rule (generalizes to all multi-component toxin systems):** when profiling one enzymatic component of a multi-component toxin, the central question is whether neutralizing that arm alone is sufficient. If a shared delivery component (PA) or a dominant effector (LF) exists, the single-arm antibody is "complementary, not complete" — and the field-11 opportunity is almost always a bispecific/combination that neutralizes multiple arms. State this explicitly in field 2 (effect of blockade) and field 6 (failure modes), and make the bispecific the lead field-11 opportunity.

### 4. UniProt REST + PDB cross-references ground fields 1 and 9 for secreted bacterial toxin — the standalone-entry advantage

EF (UniProt P40136, 800 aa) has a standalone reviewed UniProt entry providing: domain architecture (ATLF-like 60-273, catalytic CA1/CB/CA2, calmodulin-interaction helical domain 623-800), active-site/binding-site residues, and **18 PDB cross-references** (1K8T, 1K90, 1PK0, 6UZB/6VRA cryo-EM) with method + resolution in a single REST call. This fully grounded field 1 (identity, MW, domains) and field 9 (structural information) without any full-text retrieval — the abstracts + UniProt were sufficient for a rigorous preclinical-tier profile. This matches the SUDV GP standalone-entry pattern and contrasts with polyprotein-encoded fragments (ZIKV NS1) that lack standalone entries.

**Rule:** for any bacterial or viral toxin protein, check for a standalone reviewed UniProt entry first; if one exists, a single `curl https://rest.uniprot.org/uniprotkb/<ID>.json` call grounds fields 1 and 9 (domain map, MW, PDB inventory). The `features` array gives Domain/Region/Active_site/Binding_site with residue positions; the `uniProtKBCrossReferences` array (database="PDB") gives every PDB ID with method + resolution. No full-text retrieval needed for these fields.

### 5. PubMed [tiab] quoted-phrase queries worked well for a distinctive toxin name

Unlike FABP4 (where `"FABP4 antibody"[tiab]` returned 0) and like PcrV (distinctive gene name), `"anthrax edema factor" antibody[tiab]` returned 4 hits and `"edema factor" toxin[tiab] anthrax` returned 15. The term "edema factor" is distinctive enough that [tiab] phrase queries had good recall. One query hit a transient HTTP 429 (rate limit) — retried after a 4s sleep and succeeded. This confirms the established pattern: distinctive target names → [tiab] works; common-name targets → broaden to boolean/unquoted.

## urllib.request worked in this subagent context (2026-08-17 correction)

This session ran as a delegated subagent and used `urllib.request.urlopen` for **all** PubMed E-utilities calls (esearch ×5, esummary batch, efetch XML ×3) plus UniProt REST — **8+ successful HTTP calls, zero DNS errors**. The task instructions explicitly said "via urllib." This directly contradicts the earlier SKILL.md claim that "urllib.request fails in subagent execute_code contexts with DNS errors." The DNS failure a prior session observed was environment-specific, not a universal property of subagent sandboxes. The SKILL.md subagent-environment caveat has been corrected (see SKILL.md lines 309-330): default to `urllib.request`, fall back to `curl` via `subprocess.run` only if a DNS/socket error actually occurs. Do not pre-emptively refuse urllib.

## Profile statistics

- 11/11 fields present, all verified
- 22 unique PMIDs cited (range of evidence types: mechanism, antibody discovery, structural, vaccine immunogenicity)
- 18 PDB structures inventoried (field 9)
- 5 preclinical antibodies profiled (field 4): EF13D, Leysath mAb panel (3F2/7F10), Winterroth IgM, bispecific H10, synthetic Fabs A4/B7
- 3 distinct neutralization mechanisms identified (field 5): PA-binding blockade (domain I), calmodulin-competition (domain III/IV), catalytic-site blockade (CB domain)
