# Galectin-3 Profile Observations (2026-08-16)

**Target**: Galectin-3 (LGALS3)
**Tier**: Clinical-trial
**Therapeutic area**: Cardiovascular (heart failure, fibrosis)
**Profile path**: `working-docs/hitlist-profiles/galectin-3.md`
**Size**: ~35K chars, 312 lines, 7 unique PMIDs cited (6 ingested + 1 cross-referenced)
**Papers ingested**: 6 (PMID 20425490, 29344292, 39482190, 38641066, 37391294, 35972987)

## Retrieval summary

| PMID | Journal | Source | Chars |
|------|---------|--------|------|
| 20425490 | Curr Heart Fail Rep | PMC XML (PMC2831188) | 35,219 |
| 29344292 | Theranostics | PMC XML (PMC5771079) | 91,526 |
| 39482190 | Cytokine Growth Factor Rev | Abstract-only (Elsevier paywall) | 1,152 |
| 38641066 | J Biol Chem | PMC XML (PMC11134550) | 75,011 |
| 37391294 | Trends Pharmacol Sci | Abstract-only (Elsevier paywall) | 879 |
| 35972987 | Am J Respir Crit Care Med | PMC XML (PMC9893334) | 51,580 |

**Retrieval rate**: 4/6 (67%) — 4/6 via PMC XML OA, 2/6 abstract-only (Elsevier
paywall). Both Elsevier papers hit the Cloudflare CAPTCHA block on ScienceDirect
(jina returned "Just a moment..." CAPTCHA page, ~113K chars of junk). Europe PMC
confirmed OA:N, inPMC:N for both — no fallback path available. Confirms the
paper-ingest Elsevier known-block extends to Cytokine & Growth Factor Reviews
and Trends in Pharmacological Sciences.

## Key new patterns

### 1. Non-antibody therapeutic landscape — first profile with zero clinical-stage antibodies

Galectin-3 is the **first target profiled where ALL clinical-stage therapeutics
are small molecules or carbohydrates, NOT antibodies**. The entire inhibitor
landscape: GB0139/TD139 (thiodigalactoside, inhaled, Phase 2b IPF), GR-MD-02
(polysaccharide, Phase 2 NASH), GM-CT-01/Davanat (galactomannan, Phase 1/2
cancer), MCP/GCS-100/PectaSol-C (modified citrus pectin, Phase 1 cancer), and
GB1107/GB1211/GB0149 (next-gen small molecules, preclinical). No anti-galectin-3
antibody has entered clinical development.

This creates a fundamentally different profile shape:
- **Field 4** becomes "Therapeutic landscape" — entries are small molecules and
  carbohydrates with N/A for format/isotype/epitope fields
- **Field 5** becomes "binding site landscape" — CRD S-face (subsites C/D) vs
  F-face (subsites A/B/E), not antibody epitopes
- **Field 10** notes "No antibody therapeutics" as a key finding
- **Field 11** is richest — first-in-class antibody could offer superior
  selectivity (TD139 also binds galectin-1), longer half-life, N-terminal
  domain targeting (block oligomerization without blocking CRD), and
  conformation-selective approaches (pentamer-only binding)

Generalizable: for targets where the clinical pipeline is dominated by
non-antibody therapeutics, reframe fields 4-5 as "therapeutic/binding site
landscape" and use field 11 to identify the antibody-specific opportunity.

### 2. Soluble secreted lectin — not a transmembrane receptor

Galectin-3 is a soluble, secreted protein (non-classical secretion, no signal
sequence). Present in plasma/serum at low nanomolar concentrations. An antibody
would target the soluble/secreted form, not a cell-surface protein. Key
implications:
- **Target-mediated drug disposition risk**: high-affinity antibodies needed
  for effective neutralization; antibody-on-antigen sink may require high doses
- **No membrane-proximal regions**: field 9 does not need membrane-proximal
  analysis. However, extracellular galectin-3 forms lattices on cell surfaces
  by cross-linking glycosylated membrane proteins (integrins, receptors),
  creating membrane-proximal complexes that are the functional signaling units
- Note in field 1 that the target is NOT transmembrane; flag soluble-target
  PK challenge in field 11

### 3. Dual-role target with timing-dependent safety — "window of opportunity"

Galectin-3 has a **protective role in early wound healing** and a **pathogenic
role when sustained**. Galectin-3 KO mice post-MI showed **increased mortality
due to ventricular rupture** — blocking galectin-3 during acute injury is
dangerous (on-target toxicity from loss of protective function). The "window
of opportunity" concept (Suthahar 2019): inhibit only during the chronic
fibrotic phase, not during acute injury/repair.

- **Field 6**: timing risk is both a failure mode (wrong time → tissue damage)
  and a success factor (chronic-phase restriction → safety manageable)
- **Field 8**: safety is timing-dependent, not dose-dependent — no dose
  reduction makes acute-phase inhibition safe
- **Field 11**: propose biomarker-stratified or phase-restricted trial design

Generalizable: for dual protective/pathogenic targets, document timing risk
in fields 6 and 8, and propose phase-restricted trial design in field 11.

### 4. Biomarker-validated target with Class II guideline recommendation

Galectin-3 has a **Class II recommendation in HF management** (ACCF/AHA 2013
guidelines) as a prognostic biomarker — the first profiled target with a
guideline-level biomarker recommendation. Plasma galectin-3 ELISA is a cleared
diagnostic test (cutoff ~6.88 ng/mL). Biomarker-stratified trial design is
immediately feasible: select patients with elevated galectin-3 for therapy.

- **Field 7**: companion diagnostic already exists (rare among profiled targets)
- **Field 11**: biomarker-defined population differentiation is clinically
  validated, not theoretical

Generalizable: when the target is also a clinically validated biomarker with
a guideline recommendation, document the assay, cutoff values, and guideline
status in fields 3, 7, and 11.

### 5. Broad multi-organ fibrosis — not disease-specific

Galectin-3 drives fibrosis across heart, lung, liver, kidney, vasculature.
Pipeline spans IPF, NASH, COVID-19, cardiac fibrosis — all via the same
TGF-β1 activation mechanism. Field 3 lists 6 diseases; field 10 notes the
unexplored heart failure indication as a key gap (strong preclinical evidence
and biomarker validation, but no HF clinical trial).

Generalizable: for multi-organ fibrosis targets, cover all relevant disease
areas in field 3, and note which indications are clinically pursued vs
unexplored in field 10.

### 6. PubMed search strategy — author-name and drug-code queries

9 esearch queries across 5 topic areas. The key author search ("de Boer RA
galectin-3 heart failure") and drug code name search ("GB0139 galectin-3")
were critical — they found the foundational mechanism paper (PMID 20425490)
and the clinical trial paper (PMID 35972987) that were NOT in the initial
5 queries.

Generalizable: for targets with a dominant key author or known drug code
names, add author-name and drug-code esearch queries to the standard 5-query
search template. This ensures landmark papers and clinical trial reports are
captured even when they don't appear in keyword searches.

### 7. Elsevier ScienceDirect Cloudflare CAPTCHA confirmed for two additional journals

Both Elsevier papers hit the Cloudflare CAPTCHA block. Jina reader returned
the "Just a moment... Are you a robot?" CAPTCHA page (~113K chars of junk).
Europe PMC confirmed OA:N, inPMC:N, hasPDF:N for both. Wayback CDX timed out
for one and returned only 302 redirects for the other. Abstract-only was the
only viable path. Confirms the paper-ingest Elsevier known-block extends to:
Cytokine & Growth Factor Reviews, Trends in Pharmacological Sciences.

### 8. Full-text extraction from PMC XML via execute_code + urllib

The entire pipeline ran via `execute_code` + Python `urllib.request` — no
terminal, no browser. PMC XML fetched and parsed in-process using
`root.itertext()` (extracts ALL text from XML tree in one call, 35K-92K
chars per paper). Paper pages written via `write_file`. This confirms
`execute_code` as the standard execution path for delegated profiling
subagents — the full pipeline (esearch → esummary → efetch PubMed XML →
efetch PMC XML → text extraction → paper page write) runs end-to-end with
no terminal or browser needed.
