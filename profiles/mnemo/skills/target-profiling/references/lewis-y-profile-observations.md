# Lewis-Y (Le^y) Profile Observations

**Target**: Lewis-Y / Ley (Lewis Y blood group carbohydrate antigen)
**Tier**: clinical-trial
**Area**: oncology
**Profile**: `working-docs/hitlist-profiles/lewis-y.md`
**Date**: 2026-08-16
**Papers ingested**: 5 (5/5 full text — 1 PMC XML, 3 publisher-jina [Elsevier], 1 jina direct [ASCO/JCO])
**Size**: ~43.7K chars, 23 unique PMIDs cited, 200 PMID citations

## Full-text retrieval

All 5 landmark papers were retrieved as full text — an unusually high rate
(100%) for an oncology profile. The mix:

- **PMID 34644735** (Clinics, OUP) — PMC XML via PMC8478140. Open access.
- **PMID 17909358** (J Thorac Oncol, Elsevier) — publisher-jina via
  linkinghub.elsevier.com redirect. 30K chars.
- **PMID 26026738** (Gynecol Oncol, Elsevier) — publisher-jina via
  linkinghub.elsevier.com redirect. 47K chars.
- **PMID 33664128** (Int J Gynecol Cancer, Elsevier) — publisher-jina
  via linkinghub.elsevier.com redirect. 46K chars.
- **PMID 10829049** (JCO, ASCO) — jina reader directly on DOI URL
  (not resolved by fetch_fulltext.py because Europe PMC gate returned
  `inPMC: N`). Retrieved by manual `urllib.request` call to
  `r.jina.ai/https://doi.org/10.1200/JCO.2000.18.11.2282`. 26K chars.

**Key retrieval insight**: The `fetch_fulltext.py` ladder returned
`provenance: none` for PMID 10829049 (JCO/ASCO) because Europe PMC had
no record (`inPMC: N`, no PMCID). However, the jina reader CAN retrieve
older JCO articles directly via the DOI URL — the fetch_fulltext.py
Branch 2 (publisher-jina) should have caught this but the DOI
resolution step apparently failed for this 2000-era DOI. **Workaround:
when fetch_fulltext.py returns `none` for a paper with a known DOI, try
`r.jina.ai/https://doi.org/<DOI>` manually before accepting
abstract-only.** This recovered 26K chars of full text including the
complete Abstract, Results, and Conclusion sections.

## Carbohydrate antigen profiling — first observations

Lewis-Y is the **first carbohydrate (glycan) antigen** profiled at
key-paper-ingestion level. GloboH was profiled earlier but its
observations were not captured as a reference file. The Lewis-Y profile
reveals several patterns that apply to the broader class of
tumor-associated carbohydrate antigens (TACAs):

### 1. Template adaptation for non-protein targets

The 11-field template is protein-oriented (gene symbol, UniProt ID,
oligomerization, key domains). For carbohydrate antigens:
- **Gene symbol**: Replace with the biosynthetic enzyme(s) responsible
  for the glycan (e.g., FUT1/FUT2/FUT3 for Lewis-Y, B3GALT5 for GloboH).
- **UniProt ID**: Provide the enzyme's UniProt ID, clearly noting the
  target itself has no UniProt entry.
- **Oligomerization**: Replace with glycan display density/clustering
  on carrier molecules (glycoproteins, glycolipids).
- **Key domains**: Replace with glycan structure (monosaccharide
  sequence, linkage pattern) and biosynthetic pathway.
- Add a **"Cross-reactive family members"** subsection for structurally
  related glycans (Lewis-A/B/X/Y for Lewis family; SSEA-3/4 for GloboH
  family).

### 2. On-target off-tumor toxicity from normal tissue expression

The central failure mode for Lewis-Y is **on-target GI toxicity** —
the BR96-Doxorubicin ADC caused dose-limiting exudative gastritis by
binding Lewis-Y on normal gastric epithelium. This is NOT off-target
toxicity; the antigen IS expressed on normal tissue, but in a
restricted distribution (secretory borders of epithelial surfaces)
that is less accessible to naked antibodies but fully accessible to
ADC payloads delivered to the GI mucosa.

**Generalizable pattern for TACAs**: The differential expression
pattern — normal tissue antigen restricted to inaccessible secretory
borders vs. tumor cell surface broadly displaying the antigen —
creates a therapeutic window for naked IgG (limited normal tissue
binding) but NOT for armed formats (ADC, radioimmunotherapy) where
payload delivery to normal tissue is dose-limiting. The profile must
explicitly state:
- Where the antigen is expressed in normal tissue (which organs)
- Whether normal tissue expression is accessible to circulating
  antibodies (secretory borders = less accessible; gastric mucosa =
  accessible to ADC)
- Whether the therapeutic window is format-dependent (naked IgG safe
  but insufficient; ADC effective but toxic)

### 3. Naked IgG effector function insufficient against established tumors

hu3S193 (humanized IgG1) demonstrated excellent tumor targeting, potent
CDC (ED50 ~1 μg/mL) and ADCC, long half-life (~190 h), no HAHA — yet
showed NO objective responses across 3 Phase II trials (breast,
platinum-resistant ovarian, consolidation ovarian). Clinical benefit
rate was 19-23% (all stable disease, no partial/complete responses).

**Generalizable pattern**: For TACA targets, naked IgG-mediated
effector function (CDC/ADCC) alone is insufficient for clinical efficacy
against established solid tumors. This mirrors the CCR8 observation
that blockade alone has zero antitumor effect — only ADCC-mediated
depletion works. For carbohydrate antigens, the implication is that
**armed formats (ADC, bispecific, CAR-T) or combination with checkpoint
inhibitors are required** for therapeutic efficacy. The naked IgG
approach is a dead end for this target class.

### 4. Post-chemotherapy immune compromise as a timing failure mode

The consolidation ovarian trial hypothesized that patients' inability
to generate immune responses after chemotherapy may have compromised
hu3S193 efficacy, since the mechanism depends on CDC/ADCC. This is a
**timing/sequence failure mode** specific to immune-effector-dependent
antibodies:
- Administering an ADCC/CDC-dependent antibody after cytotoxic
  chemotherapy is counterproductive — chemotherapy depletes the very
  effector cells (NK cells, complement proteins) the antibody needs.
- The fix: administer immune-effector-dependent antibodies BEFORE
  chemotherapy (neoadjuvant), in minimal residual disease (post-surgery,
  pre-chemotherapy), or combine with immune-activating agents.

**Generalizable**: This applies to any naked IgG1 antibody whose
mechanism is CDC/ADCC, not just TACAs. Include in field 6 for any
antibody where the mechanism is effector-dependent and the trial
design places it after chemotherapy.

### 5. Biomarker selection too broad — quantitative expression matters

All Phase II trials required only IHC positivity (any staining) for
Lewis-Y. Post-hoc analysis of the breast trial showed that one patient
with elevated Lewis-Y expression had prolonged stable disease >2
years, suggesting that quantitative expression levels predict benefit.
This mirrors the GloboH vaccine trial finding that patients with
H-score ≥80 showed a trend toward better PFS.

**Generalizable for TACAs**: Carbohydrate antigen expression is
heterogeneous and quantitative. IHC any-positivity is insufficient for
patient selection. A quantitative threshold (e.g., 3+ or 4+ staining,
H-score cutoff) should be established and used for trial enrollment.
The profile should note in field 6 (failure modes) whether the
biomarker strategy was too permissive and in field 11
(differentiation) whether a stricter threshold could rescue the
target.

### 6. Protease-activated conditional antibodies as a format solution

A 2025 preclinical study (PMID 40246093) described a protease-activated
anti-Lewis-Y antibody designed to bind only in the tumor
microenvironment (where proteases are active), sparing normal gastric
tissue. This directly addresses the key failure mode (on-target GI
toxicity from ADC format) and represents the most promising format
differentiation for TACA targets where normal tissue expression limits
armed formats.

**Generalizable for TACAs**: For any TACA with normal tissue
expression that limits armed formats (ADC, bispecific),
protease-activated conditional antibodies are the most direct
engineering solution. Include in field 11 for any TACA where the
failure mode is on-target off-tumor toxicity.

### 7. Lewis-negative phenotype exclusion

Patients lacking functional FUT3 (Lewis-negative phenotype, ~5-10% of
populations) cannot synthesize Lewis-type antigens. This was not
explicitly addressed in trial designs. For any Lewis-type antigen
target, the profile should note that Lewis-negative individuals should
be excluded — their tumors will not express the target.

## Supporting PMIDs (not ingested as full text)

These PMIDs were identified during the PubMed search and cited in the
profile from their abstracts:

- PMID 17545534 — hu3S193 Phase I biodistribution (Scott 2007, Clin
  Cancer Res) — key for PK, safety, HAHA data
- PMID 10080588 — BR96-Dox Phase II randomized breast (Tolcher 1999,
  JCO) — key for ADC failure mode
- PMID 10866319 — hu3S193 construction/characterization (Scott 2000,
  Cancer Res) — key for epitope specificity, CDC/ADCC data
- PMID 19825951 — CMD-193 Phase I (Herbertson 2009, Clin Cancer Res) —
  immunoconjugate
- PMID 23408949 — mAb 692/29 dual Lewis-Y/Lewis-B (Noble 2013, PLoS
  ONE) — preclinical
- PMID 34440263 — anti-Lewis-Y/CD3 bispecific (Chen 2021, Biomedicines)
  — preclinical
- PMID 40246093 — protease-activated anti-Lewis-Y (Lee 2025, Int J Biol
  Macromol) — preclinical
- PMID 20003467, 21152298, 22312289, 26609483, 30066907 — Lewis-Y
  biology/mechanism in ovarian cancer (signal pathway papers)
- PMID 19242371, 20200563 — Lewis-Y CAR-T / gene-modified T cells
