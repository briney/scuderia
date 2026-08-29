# HMGB1 (HMGB1) profile observations — 2026-08-17

Preclinical-tier neuroscience target. HMGB1 (High Mobility Group Box 1,
UniProt P09429) — a nuclear non-histone chromatin protein that acts as a
prototypical DAMP/alarmin when released extracellularly. 5 papers ingested
(3/5 full text: PMID 14695889 + 23514872 via PMC NCBI HTML, PMID 28446773
via Europe PMC fullTextXML; 2/5 abstract-only: PMID 10398600 Science 1999
paywalled, PMID 30391757 World Neurosurg 2019 no PMC). ~30K chars profile,
9 unique PMIDs cited, working-docs/hitlist-profiles/hmgb1.md.

## Key new patterns

### 1. DAMP/alarmin target — intracellular protein with extracellular cytokine function

HMGB1 is the first profiled target that is fundamentally an intracellular
nuclear protein (chromatin-associated DNA chaperone) whose therapeutic
relevance comes from its EXTRACELLULAR function as a DAMP. This dual
compartment identity has specific implications for antibody targeting:

- The antibody only needs to engage the extracellular, released form.
  Intracellular HMGB1 (nuclear, cytoplasmic) is not antibody-accessible
  and is not the therapeutic target — antibodies do not replicate the
  neonatal lethality of HMGB1 knockout because they cannot enter intact
  cells.
- The target is secreted/released (not surface-displayed), so all
  surfaces of the soluble protein are antibody-accessible. This is
  structurally simpler than membrane targets where only the
  extracellular face is accessible.
- HMGB1 is redox-state-dependent: three conformations (fully reduced
  → CXCL12 complex/CXCR4 signaling; disulfide → TLR4 signaling; fully
  oxidized → inactive). A neutralizing antibody's efficacy may vary with
  the redox environment at the disease site. For field 5 (epitope
  landscape) and field 9 (structural information), document the redox
  states and note which form the neutralizing antibodies target.

This pattern generalizes to other DAMP/alarmin targets (S100 proteins,
HSPs, ATP, IL-1α) where the therapeutic target is the released form of
an intracellular protein.

### 2. PubMed search without "antibody" returns the landmark discovery papers

The standard search templates (e.g., "HMGB1 antibody[tiab]") returned
relevant papers but the MOST important landmark paper — Wang et al. 1999
Science (PMID 10398600) — was NOT in the top results for "HMGB1
antibody[tiab]" because the 1999 paper uses "HMG-1" (not "HMGB1") and
describes "antibodies to HMG-1" rather than "anti-HMGB1 antibody." It
was only found by searching "Wang H[au] HMG-1 late mediator endotoxemia"
(author + historical name + function).

**Lesson:** For targets with historical name changes (HMG-1 → HMGB1),
search by the historical name and by author + function, not just the
current gene symbol. The landmark discovery paper may predate the name
standardization. Also search by the key researcher's name (e.g.,
"Nishibori anti-HMGB1" found the comprehensive CNS review, PMID
31105025, and the humanized mAb paper, PMID 36230933).

### 3. Clone-dependent failure — same target, different antibody, opposite outcome

HMGB1 is the first profiled target where two different neutralizing mAb
clones gave OPPOSITE outcomes in different disease models:

- Clone 3B1 (IgG2a, 100 μg i.v.): POSITIVE in EAE (ameliorated clinical
  disease, blocked T cell infiltration) (PMID 23514872)
- Clone 2G7 (IgG2b, 50 μg i.p. ×10 weeks): NEGATIVE in lupus nephritis
  (no effect on albuminuria, anti-dsDNA, complement, cytokines) (PMID
  26837069)
- Nishibori rat mAb (1 mg/kg i.v.): POSITIVE across epilepsy, TBI, ICH,
  stroke (PMID 28446773, 30391757, 28393932)

The negative result could be: (a) disease-specific (lupus nephritis is
not HMGB1-driven), (b) epitope-specific (2G7 binds a non-functional
epitope), (c) dose/schedule-specific (50 μg vs 100–600 μg used
elsewhere), or (d) isotype-specific (IgG2b vs IgG2a). No epitope mapping
exists for ANY anti-HMGB1 mAb, so the cause cannot be determined.

For field 6 (failure modes), this is a new failure class — "clone-
dependent efficacy with unknown epitope basis." For field 5 (epitope
landscape), the absence of epitope mapping is the critical gap. For
field 11 (differentiation), systematic epitope binning of all available
anti-HMGB1 mAbs would resolve whether the lupus failure was epitope-
driven or disease-driven.

This pattern generalizes to any target where multiple mAb clones have
been tested in different disease models with discordant results and
no epitope mapping exists to explain the differences.

### 4. Extracellular DAMP as universal therapeutic — disease context determines efficacy

HMGB1 is the most broadly implicated target profiled to date —
therapeutic anti-HMGB1 antibody has shown preclinical efficacy in:
sepsis, EAE/MS, epilepsy, TBI, ICH, stroke, Parkinson's, Alzheimer's,
hemorrhage, periodontitis, obesity/metabolic disease. This breadth is
inherent to DAMPs — HMGB1 is released in virtually all forms of tissue
injury.

However, the lupus nephritis failure demonstrates that "HMGB1 is
elevated" does NOT mean "HMGB1 is a driver." In lupus, HMGB1 is a
biomarker (elevated in plasma/urine), but neutralizing it does not
ameliorate disease. For field 3 (disease evidence), distinguish
between:
- Diseases where HMGB1 neutralization CHANGED outcomes (sepsis, EAE,
  epilepsy, TBI, ICH — strong preclinical evidence)
- Diseases where HMGB1 is elevated but neutralization FAILED (lupus
  nephritis — biomarker, not driver)

For field 11, the differentiation opportunity is biomarker-stratified
clinical trials — select patients with elevated plasma/CSF HMGB1 and
active HMGB1-driven inflammation, not just any patient with the
disease.

### 5. Europe PMC fullTextXML works for some PMC papers where NCBI PMC HTML is needed for others

For PMID 28446773 (Sci Rep, PMC5430706), Europe PMC fullTextXML
(`europepmc.org/webservices/rest/<PMCID>/fullTextXML`) returned 112K
chars of well-structured XML — the best format for programmatic
extraction. For PMID 14695889 (PNAS, PMC314179) and 23514872 (J
Autoimmun, PMC3672339), Europe PMC fullTextXML returned 404 — but
the NCBI PMC HTML pages (`pmc.ncbi.nlm.nih.gov/articles/<PMCID>/`)
returned 197–219K chars of HTML, extractable via an HTML parser.

**Lesson:** Europe PMC fullTextXML and NCBI PMC HTML are complementary
sources — when one returns 404, try the other. Europe PMC XML is
preferable for parsing (clean structure), NCBI PMC HTML is the fallback
(messier but available). The 404 from Europe PMC is not a reliable
"full text unavailable" signal — it may mean the specific PMC record
hasn't been indexed by EPMC yet. Always try both sources for papers
with known PMCIDs.

This complements the Nav1.8 observation (2026-08-17) that EPMC
fullTextXML is the highest-yield source for recent OA papers — it
extends to: EPMC XML is best when available, but NCBI PMC HTML is a
viable second source that should not be skipped.

### 6. Humanized mAb in non-human primate — translational pipeline visible

HMGB1 is the first preclinical target where a humanized antibody
(OKY001) has been tested in a non-human primate (common marmoset) ICH
model (PMID 36230933). This represents a more advanced translational
stage than most preclinical targets. For field 4 (antibody landscape),
document the humanization and NHP testing as a distinct pipeline entry
— it signals that clinical translation is actively being pursued. For
field 10 (competitive landscape), this means the target is closer to
clinical trials than the "preclinical" tier suggests.

The marmoset study showed: inhibited HMGB1 release from brain to
plasma, reduced 4-HNE accumulation, reduced cerebral iron deposition,
reduced brain injury volume at 12 days, improved behavioral
performance. No adverse effects reported — important for field 8
(safety profile).

### 7. UniProt REST API as primary source for structural fields (1, 5, 9)

UniProt JSON API (`rest.uniprot.org/uniprotkb/P09429.json`) provided:
- Domain architecture: HMG box A (aa 9–79), HMG box B (aa 95–163),
  disordered linker (76–95), acidic tail (161–215)
- Functional regions: LPS-binding (3–15, 80–96), cytokine-stimulating
  (89–108), RAGE-binding (150–183)
- PTMs: acetylation (multiple Lys), phosphorylation (Ser35, Ser100),
  ADP-ribosylation (Ser181), redox (Cys23, Cys45, Cys106)
- PDB structures: 13 entries listed
- Subcellular locations: nucleus, cytoplasm, secreted, cell membrane
- Tissue specificity: ubiquitous

This is the same pattern noted in the BDKRB2 profile (2026-08-17) —
UniProt REST API as the primary source for fields 1 and 9. For HMGB1,
the API also provided the functional regions that directly inform
field 5 (epitope landscape) — the cytokine-stimulating and RAGE-binding
regions are the logical neutralizing epitope targets, and no published
epitope mapping exists to confirm whether the known mAbs target these
regions.

## Profile statistics

- ~30K chars, 212 lines
- 9 unique PMIDs cited (10398600, 14695889, 23514872, 26837069,
  28393932, 28446773, 30391757, 31105025, 36230933)
- 5 papers ingested (3/5 full text, 2/5 abstract-only)
- 60% full-text retrieval rate (3/5)
- Full-text sources: Europe PMC XML (1), NCBI PMC HTML (2)
- 6 disease entries in field 3 (sepsis, EAE/MS, epilepsy, TBI, ICH,
  lupus nephritis)
- 5 antibody entries in field 4 (polyclonal rabbit IgG, 3B1, 2G7,
  Nishibori rat mAb, OKY001 humanized, A-box fragment)
- 11 differentiation opportunities in field 11
