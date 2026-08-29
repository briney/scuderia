# IGF-1 profile observations (2026-08-17)

Forty-seventh level-2 profile (preclinical tier, cardiovascular — secreted
growth factor). IGF-1 (Insulin-like Growth Factor 1, IGF1) is a 7.6-kDa
secreted peptide growth factor — the first cardiovascular-tier profile where
the **entire clinical antibody pipeline is dual-ligand (IGF-1/IGF-2) and was
developed for oncology, not cardiology**. This session also produced the
first use of the **UniProt flat-text `.txt` format as a structured-data
source** beyond identity verification.

Built via delegated subagent using the lightweight retrieval pipeline
(direct PubMed E-utilities via `execute_code` + terminal curl). 8 PubMed
search queries, 12 key paper abstracts fetched via efetch, UniProt P05019
flat-text parsed for structural/domain data. Abstract-only ingestion (no
full-text retrieval attempted — subagent context). ~59K-char profile, 25
unique PMIDs cited across 197 PMID mentions.

## Papers retrieved (abstracts via efetch)

1. **PMID 21245093** — Gao et al. 2011, Cancer Res: MEDI-573 dual IGF-I/II
   neutralizing antibody preclinical
2. **PMID 25024259** — Haluska et al. 2014, Clin Cancer Res: MEDI-573 Phase I
3. **PMID 32054790** — Weyer-Czernilofsky et al. 2020, Mol Cancer Ther:
   Xentuzumab + enzalutamide in prostate cancer
4. **PMID 33451345** — Schmid et al. 2021, Breast Cancer Res: Xentuzumab
   Phase Ib/II breast cancer (negative)
5. **PMID 37308971** — Schmid et al. 2023, Breast Cancer Res: XENERA-1
   Phase II xentuzumab (negative)
6. **PMID 34870878** — Doi et al. 2022, Cancer Sci: Xentuzumab Phase 1 Japan
7. **PMID 9455703** — Su et al. 1997, Hybridoma: 35I17 IGF-1-specific
   neutralizing mAb with cross-species reactivity
8. **PMID 18793116** — Abbas et al. 2008, Expert Rev Cardiovasc Ther:
   IGF-1 in glucose regulation and cardiovascular disease
9. **PMID 34363749** — Zaman et al. 2021, Immunity: Resident macrophage-
   derived IGF-1 required for adaptive cardiac growth
10. **PMID 25924852** — Zhao et al. 2015, Int J Cancer: m708.5 dual
    IGF-1/IGF-2 antibody in neuroblastoma
11. **PMID 22491965** — Higashi et al. 2012, J Gerontol: Aging,
    atherosclerosis, and IGF-1 review
12. **PMID 12021121** — Maruyama et al. 2002, Ann NY Acad Sci: Anti-IGF-1
    autoantibodies in type 1 diabetes (not detected)

## Key new patterns

### 1. UniProt flat-text `.txt` as a structured-data source

The UniProt `.txt` flat-text format (retrieved via
`curl -sL 'https://www.uniprot.org/uniprot/P05019.txt'`) provides a rich
structured-data source beyond simple identity verification. The format
contains:

- **`FT SIGNAL`, `FT PROPEP`, `FT CHAIN`**: Signal peptide, propeptide, and
  mature chain boundaries (residues 1–21, 22–48, 49–118 for IGF-1). These
  define the mature protein boundaries for MW calculation and domain
  annotation without manual lookup.
- **`FT REGION`**: Functional domain annotations with notes (e.g.,
  `/note="B"`, `/note="C"`, `/note="A"`, `/note="D"` for IGF-1's B-C-A-D
  domain architecture). These are the authoritative domain boundaries,
  more reliable than textbook descriptions.
- **`DR PDB`**: All PDB cross-references with method, resolution, and
  chain mapping (e.g., `DR   PDB; 1GZR; X-ray; 2.00 A; B=49-118`). A single
  grep extracts all structures with their resolution and the specific
  residue range covered — faster than searching the PDB website.
- **`CC -!- FUNCTION`**: Full functional description with PubMed citations
  inline. Provides the authoritative mechanism summary for field 2.
- **`CC -!- SUBCELLULAR LOCATION`**: Localization annotation with evidence
  codes.
- **`CC -!- DISEASE`**: Disease associations with MIM numbers and PubMed
  citations. Direct source for field 3 disease evidence.
- **`CC -!- SUBUNIT`**: Complex/partner information (e.g., IGF-1 forms a
  ternary complex with IGF-1R and integrins, with IGFBP3 and ALS).
- **`SQ SEQUENCE`**: Full sequence with MW and CRC — authoritative MW for
  field 1.

**Extraction technique**: Use `grep -E` to pull specific line types, then
`awk` for multi-line CC blocks:
```bash
# All PDB structures
grep 'DR   PDB' uniprot.txt
# Domain regions
grep -E 'FT   (CHAIN|REGION|DOMAIN|SITE|MOD_RES)' uniprot.txt
# Function block (multi-line)
awk '/CC   -!- FUNCTION/{flag=1} flag{print; if(/CC   -!- / && !/FUNCTION/) flag=0}' uniprot.txt
```

**Generalizable**: For every target profile, fetch the UniProt `.txt` early
and use it as the primary structured-data source for fields 1 (identity,
domains, MW), 9 (PDB structures, conformational states), and 2 (function,
subcellular location). It is faster and more reliable than manual literature
lookup for these structured annotations.

### 2. U-shaped dose-response as a partial-neutralization rationale

IGF-1 is the first cardiovascular-tier profile where the target has a
**U-shaped relationship with disease risk**: both low IGF-1 (associated with
aging, cardiovascular mortality) and high IGF-1 (acromegaly, cardiac
hypertrophy, cardiovascular mortality) increase cardiovascular mortality
(PMID 18793116, PMID 22491965). This creates a therapeutic strategy of
**partial neutralization** — reducing IGF-1 from supraphysiological to
physiological levels, not eliminating it.

This extends the partial-neutralization pattern from leptin (where partial
20–80% reduction is therapeutic but complete elimination causes obesity,
PMID 31495688) to the cardiovascular domain. The generalizable rule for
field 6 (failure modes) and field 11 (differentiation): when the target has
a U-shaped disease relationship, complete neutralization is a failure mode
(causing deficiency pathology), and a partial-neutralization antibody
(maintaining 50–80% of circulating levels) is the differentiation strategy.
The dosing/PK requirement is fundamentally different from targets where
complete neutralization is the goal (most cytokine neutralizers).

For field 8 (safety), the U-shaped relationship means the therapeutic index
is inherently narrow — the antibody must titrate precisely to avoid crossing
from the therapeutic zone into the deficiency zone. This is a distinct
safety profile from targets where more inhibition = more efficacy.

### 3. Integrin co-receptor binding site as a function-selective antibody epitope

IGF-1 directly binds integrins (αvβ3, α6β4) at Arg-84/Arg-85 (C-domain),
forming a ternary complex with IGF-1R that is essential for full IGF-1
signaling (PMID 19578119). An antibody targeting the integrin-binding
site would block integrin-dependent IGF-1 signaling (relevant in vascular
smooth muscle proliferation, restenosis, atherosclerosis) while preserving
IGF-1R-mediated cardioprotective and metabolic signaling.

This is a **function-selective antibody** approach analogous to the tPA
Glunomab pattern (block harmful function, preserve beneficial function,
documented in tPA profile observations). For field 5 (epitope landscape),
the integrin-binding motif represents a distinct epitope bin that separates
from the receptor-binding interface. For field 11 (differentiation), this
is the most compelling unexplored epitope — it creates a mechanistically
novel antibody class that has never been explored (all existing antibodies
target the IGF-1R-binding surface).

**Generalizable**: For any growth factor/cytokine that binds both a
signaling receptor AND a co-receptor/adhesion molecule (e.g., IGF-1/integrin,
FGF/HSPG, VEGF/αvβ3, CXCL12/ACKR3), the co-receptor binding site is a
function-selective epitope that could block one signaling arm while
preserving the other. Include this in field 5 and field 11 for targets
with known co-receptor interactions.

### 4. INN name search in PubMed for clinical-trial antibody discovery

Searching PubMed by the antibody's INN (international nonproprietary name)
was essential for finding clinical trial papers that generic "[tiab]"
queries missed. PubMed's thesaurus auto-translates INNs to supplementary
concept terms:

- `xentuzumab` → returns all xentuzumab clinical and preclinical papers
  (16 results)
- `MEDI-573` → auto-translated to `dusigitumab` supplementary concept,
  returning 10 results including the Phase I trial

The generic queries (`"IGF-1 antibody"[tiab]`, `"anti-IGF-1"[tiab]`)
returned mostly preclinical and mechanistic papers but missed the
clinical trial reports. Adding INN-specific queries captured the
clinical evidence anchor papers (Phase I, Phase Ib/II, Phase II XENERA-1).

**Extraction technique**: When profiling a target with known antibody drug
candidates, always run a separate PubMed search for each known INN and
company code name. The PubMed thesaurus handles the INN → supplementary
concept translation automatically. Check the `translationset` in the
esearch JSON response to confirm the INN was recognized:
```json
{"from":"MEDI-573","to":"\"dusigitumab\"[Supplementary Concept] OR ..."}
```

**Generalizable**: For any target where antibody drug candidates are known
(from the hit list, literature, or ClinicalTrials.gov), always include
INN/code-name searches alongside generic target-name queries. This applies
to all tiers but is most critical for clinical-trial and saturated targets
where the clinical evidence is published under the INN, not the target name.

## Profile stats

- IGF-1 profile: ~59K chars, 11 fields, no frontmatter
- 25 unique PMIDs cited across 197 PMID mentions
- Abstract-only ingestion (no full-text retrieval — subagent context)
- Tier: preclinical | Area: cardiovascular
- working-docs/hitlist-profiles/igf-1.md
