# MER/TK (MERTK) profile observations

**Date**: 2026-08-16
**Target**: MER/TK (MERTK) — MER proto-oncogene tyrosine kinase
**Tier**: Preclinical
**Therapeutic area**: Oncology
**Profile**: `working-docs/hitlist-profiles/mer-tk.md` (~39K chars)
**Papers ingested**: 3 (1/3 full text via PMC XML, 1/3 abstract-only [Elsevier paywalled], 1/3 already ingested)
**Unique PMIDs cited**: 8 ingested + 6 supplementary abstracts = 14 total

## Papers ingested

| PMID | Title | Journal | Fulltext source |
|------|-------|---------|----------------|
| 32049051 | Blockade of MerTK on TAMs Enhances STING Activation by Tumor-Derived cGAMP | Immunity 2020 | Abstract-only (Elsevier paywalled, not in PMC) |
| 36555321 | Bispecific MerTK-Engaging Antibodies for Cancer Immunotherapy | Front Immunol 2022 | Full text via PMC XML (PMC9779728, OA) |
| 31088471 | TAM Receptors: Implications for Macrophages in Tumor Microenvironment | Mol Cancer 2019 | Full text via PMC XML (already ingested) |

Supplementary abstracts batch-fetched for profile grounding: PMID 41661650 (RGX-019 ADC, Cancer Res 2026), 40294287 (CRISPR MerTK knockout, JACS 2025), 33239426 (AXL/MERTK cooperation, Cancer Res 2021), 25074939 (MERTK overexpression in epithelial cancer, JBC 2014), 28258690 (TAM as innate immune checkpoint, Immunol Rev 2017), 34074493 (TAM efferocytosis in TME, Int Rev Cell Mol Biol 2021).

## Key new patterns

### 1. Publisher-jina false positive — provenance tag misleading for 404 pages

**Observation**: `fetch_fulltext.py` returned `{"provenance": "publisher-jina", "chars": 24733}` for PMID 32049051 (Zhou et al, Immunity 2020, Elsevier). However, the actual content was the Cell Press website's 404/navigation page — journal menus, login forms, and navigation links — NOT the article text. The character count (24,733) was sufficient to pass a naive length check, but the content was useless.

**Root cause**: The Cell Press URL `https://www.cell.com/immunity/fulltext/S1074-7613(20)30036-X` returned a 404, and jina reader returned the 404 page's rendered HTML (which is large — journal navigation, menus, etc.).

**Fix**: After `fetch_fulltext.py` returns `publisher-jina`, always verify the output by checking the first ~500 chars for navigation/404 markers: `"Login to your account"`, `"404"`, `"Page not found"`, `"Skip to Main Content"`, journal navigation lists. If the content is a navigation page, treat it as `provenance: none` and fall back to abstract-only.

**Generalizable**: This applies to any Elsevier/Cell Press paper where the publisher URL returns a 404. The `fetch_fulltext.py` script does not currently validate that the jina reader output is actual article text — it trusts the character count. For target profiling, always read the first 10 lines of the fulltext file before using it for distillation.

### 2. EPMC REST API as reliable abstract fallback for paywalled papers

**Observation**: When `fetch_fulltext.py` returns `provenance: none` (no full text available), the Europe PMC REST API provides a reliable fallback for full structured abstracts:

```
https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:{pmid}&resultType=core&format=json
```

This returns the full `abstractText` field (often 1,000-2,500 chars for structured abstracts), plus `authorString`, `journalTitle`, `pubYear`, `inPMC`, `isOpenAccess`, `pmcid`, and `hasPDF` flags — all in a single JSON call.

**Application**: For the Zhou 2020 paper (PMID 32049051), the EPMC abstract (1,499 chars) contained all the mechanistic findings needed for key-paper-level distillation: STING dependence, P2X7R-cGAMP transport axis, synergy with anti-PD-1/PD-L1, Sting(gt/gt)/Cgas-/- knockout results. This was sufficient to fill fields 2, 3, 6, and 8 of the target profile.

**Generalizable**: This is already documented in the paper-ingest skill's EPMC gate, but for target profiling it's worth noting that the EPMC REST API is the single most reliable abstract source for paywalled Elsevier/Wiley/Cell Press papers. Add it to the profiling workflow as step 0.5: "If fulltext retrieval fails, always fetch the EPMC core record for the abstract."

### 3. TAM family cross-referencing — sibling profiles enrich each other

**Observation**: MERTK is the second TAM family member profiled (after AXL, `working-docs/hitlist-profiles/axl.md`). The AXL profile already contained extensive TAM family biology (shared ligands Gas6/Pros1, shared downstream pathways PI3K/Akt/NF-κB, TAM receptor dimerization, MERTK upregulation as AXL bypass). Reading the AXL profile before starting MERTK profiling provided:
- Shared family biology (no need to re-search TAM receptor structure, ligand interactions)
- The AXL→MERTK bypass mechanism (directly relevant to MERTK field 6 failure modes)
- Clinical trial landscape for TAM-targeted therapies (AVB-S6-500, bemcentinib, etc.)
- The Myers 2019 review (PMID 31088471) which was already ingested for the AXL profile

**Generalizable**: When profiling a member of a receptor family (TAM, EGFR family, IL-6 cytokine family, TNF superfamily), always read the sibling profiles first. The shared family biology is already distilled — the new profile only needs to add target-specific details (distinct ligand affinities, distinct cell-type expression, distinct disease associations, distinct antibody landscape).

### 4. Bispecific macrophage engager (BiME) — engage vs. block paradigm

**Observation**: The Carrara 2022 paper (PMID 36555321) describes the first MerTK-mediated macrophage engager — a bispecific antibody that engages MerTK on macrophages and EGFR on tumor cells to redirect phagocytosis. This is fundamentally different from the antagonist approach (Zhou 2020, PMID 32049051) which blocks MerTK-mediated efferocytosis. The bispecific "engages" MerTK as an anchoring receptor rather than blocking its function.

**Key distinction for field 4 (antibody landscape)**: For the first time in the profiling campaign, the same target has antibodies with diametrically opposed mechanisms:
- **Antagonist** (Zhou et al., RGX-019): blocks efferocytosis → STING activation → antitumor immunity
- **Agonist/engager** (MerK28 bivalent): activates MerTK signaling → pAKT → may promote immunosuppression (unwanted)
- **Bispecific engager** (KiH MerK28-7D9G): engages MerTK without activation → redirects phagocytosis to tumor cells

**For field 6 (failure/success modes)**: The bispecific engager approach avoids two key risks: (1) the retinal toxicity of antagonistic antibodies (engaging rather than blocking may spare RPE phagocytosis), and (2) the immunosuppressive signaling of agonistic antibodies (monovalent binding avoids MerTK activation).

**Generalizable**: For any macrophage-expressed target where the biological function is immunosuppressive (MerTK efferocytosis, SIRPα "don't eat me" signaling), the "engage vs. block" paradigm is a fundamental mechanistic choice that should be explicitly documented in field 4 and analyzed in field 6. The bispecific macrophage engager format is a third approach distinct from both agonism and antagonism.

### 5. On-target retinal toxicity with format-dependent safety

**Observation**: MERTK is essential for retinal pigment epithelium (RPE) phagocytosis — MERTK mutations cause retinitis pigmentosa in humans. An antagonistic anti-MerTK antibody caused retinal toxicity in cynomolgus monkeys (PMID 36555321, referencing Waterborg et al.). However, the RGX-019-MMAE ADC showed NO retinal toxicity in vivo (PMID 41661650).

**Key insight for field 8 (safety)**: Retinal toxicity is NOT an inevitable consequence of MERTK targeting — it is format/epitope/dose-dependent. The ADC data suggests that either (a) the ADC's epitope doesn't block RPE-relevant phagocytosis, (b) the ADC's dosing/tissue distribution differs from the naked antibody, or (c) the ADC mechanism (MMAE payload delivery) spares RPE cells. This is a critical nuance: on-target toxicity that appears to be a deal-breaker for one format may not apply to all formats.

**Generalizable**: For any target with a known on-target toxicity in a specific organ (MERTK/retina, CD47/RBC, Treg targets/tissue Tregs), always check whether different formats (naked antibody, ADC, bispecific, Fc-silent) have different toxicity profiles. The format-dependent safety profile should be documented explicitly in field 8, and the format that avoids the on-target toxicity should be highlighted in field 11 (differentiation).

### 6. Receptor recycling as a durability limitation for antibody blockade

**Observation**: PMID 40294287 (JACS 2025) showed that anti-MerTK antibody and anti-PtdSer antibody combination induced only transient efferocytosis prevention. Anti-MerTK antibodies are degraded intracellularly, and MerTK receptors recycle to the cell surface, restoring efferocytosis. CRISPR/Cas9 gene editing was required for permanent efferocytosis prevention.

**For field 6 (failure modes)**: Receptor recycling is a distinct failure class — the antibody works mechanistically but the effect is transient due to target biology (receptor turnover), not due to antibody quality. This is different from epitope failure, population failure, or format failure.

**Generalizable**: For any receptor target with rapid turnover/recycling, receptor recycling limits antibody durability. The mitigation strategies are: (1) more frequent dosing, (2) ADC format (depletes receptor-expressing cells rather than blocking them), (3) bispecific engager format (harnesses receptor expression rather than blocking it), (4) gene editing (non-antibody approach). Include receptor turnover rate in field 9 (structural information) when available.

### 7. ADAM17-mediated shedding as an antibody accessibility barrier on M2 macrophages

**Observation**: M2-differentiated THP-1 macrophages showed decreased surface MerTK, attributed to ADAM17 protease-mediated cleavage/shedding (PMID 36555321). This releases soluble MerTK ectodomain that can compete with surface-bound MerTK for antibody binding.

**For field 6 and field 9**: ADAM17 shedding is a target-specific accessibility barrier — the most immunosuppressive cell population (M2 TAMs) has the least surface target for antibody binding. This is the inverse of the usual problem (target overexpression on pathogenic cells = good for antibody targeting). Here, the pathogenic function (efferocytosis) is highest when the target is being shed.

**Generalizable**: For any target that undergoes proteolytic shedding (MerTK, AXL, EGFR, L-selectin/CD62L), check whether the shedding rate is cell-type-dependent and whether the most therapeutically relevant cell population has reduced surface expression due to shedding. Include shedding in field 9 (structural information) and its therapeutic implication in field 6.

### 8. Topic-divided PubMed search for landmark paper selection

**Technique**: Three separate PubMed ESearch queries targeting distinct topic areas were more effective than one broad query:
1. `MERTK antibody cancer immunotherapy` → 13 results
2. `anti-MERTK cancer immunotherapy` → 4 results  
3. `MERTK TAM receptor efferocytosis` → 68 results

EFetch with XML parsing (batch of 22 PMIDs in 3 calls with 4s sleep between) provided full metadata (title, authors, abstract, DOI, journal, year). This is the same pattern used in the IL-17A and CXCL10 profiles — delegation with search instructions works, and topic-divided queries yield better coverage than monolithic queries.

(MER/TK profile, ~39K chars, 3 papers ingested (1/3 full text, 1/3 abstract-only, 1/3 pre-existing), 14 PMID citations, `working-docs/hitlist-profiles/mer-tk.md`.)
