# BACE1 profile observations (2026-08-16)

Thirty-first level-2 profile (failed-clinical/graveyard tier, neuroscience —
Alzheimer's disease). BACE1 (beta-site amyloid precursor protein cleaving
enzyme 1, β-secretase, memapsin 2) is a transmembrane aspartyl protease that
initiates Aβ production by cleaving APP. ALL BACE1 inhibitors in clinical
trials failed — verubecestat (Merck, 2× Phase 3), lanabecestat
(AstraZeneca/Lilly, 2× Phase 3), atabecestat (Shionogi/J&J, Phase 2/3),
elenbecestat (Eisai/Biogen, Phase 2/3), umibecestat/CNP520 (Novartis/Amgen,
Phase 2/3), LY3202626 (Lilly, Phase 2) — all discontinued for futility, liver
toxicity, or cognitive worsening. 8 key papers ingested (4/8 full text via
PMC HTML: 2 NEJM verubecestat trials, Hampel 2021 review in Biol Psychiatry,
Bhatt 2018 adult conditional KO in Sci Transl Med; 4/8 abstract-only: Atwal
2011 anti-BACE1 antibody in Sci Transl Med, Kennedy 2016 verubecestat
preclinical in Sci Transl Med, Moussa-Pacha 2020 review in Med Res Rev,
Ugbaja 2022 review in Curr Med Chem). ~50K chars (profile), 8 unique PMIDs
cited, 198 PMID citations across the profile.

Full-text retrieval: 4/8 (50%) via PMC HTML extraction. The PMC IDs from
PubMed efetch XML were MISMATCHED with the correct PMC IDs — the NCBI ID
converter API (`pmc/utils/idconv/v1.0/`) was required to resolve correct
PMCIDs. Full text was extracted from PMC HTML pages using a Python
HTMLParser-based text extractor (no `pmc_xml_body_parser.py` needed — these
were HTML pages, not XML). The Hampel 2021 review (PMC7533042) was the
richest source, covering all 6 failed BACE1 inhibitor programs, the >40
BACE1 substrates, and the three-point failure analysis framework.

New observations:

## 1. PMC ID mismatch between PubMed efetch XML and NCBI ID converter

The PMCID returned in PubMed efetch XML (`efetch.fcgi?rettype=abstract&retmode=xml`)
was WRONG for multiple papers. For example:
- PMID 30970186 (Egan 2019 NEJM): efetch XML returned PMC6070607, but the
  correct PMCID is PMC6776078 (per NCBI ID converter).
- PMID 29719179 (Egan 2018 NEJM): efetch XML returned PMC3622225, but the
  correct PMCID is PMC6776074.
- PMID 32223911 (Hampel 2021): efetch XML returned PMC7330928, but the
  correct PMCID is PMC7533042.
- PMID 30232227 (Bhatt 2018): efetch XML returned PMC4584174, but the
  correct PMCID is PMC11017370.

Using the wrong PMCIDs returned completely different papers (e.g., PMC6070607
was a Front Aging Neurosci paper about MK-8931 and dendritic spines, not the
Egan 2019 NEJM trial). The fix: ALWAYS use the NCBI ID converter API
(`https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids=PMID1,PMID2&format=json`)
to resolve correct PMCIDs before fetching full text. The ID converter is
fast (single call, no rate limits), handles batch PMID lookups, and returns
the authoritative PMCID mapping. This is now a required step for any profiling
workflow that uses efetch XML metadata for PMC full-text retrieval.

## 2. Mechanism-based cognitive worsening as a distinct graveyard pattern for enzymatic targets with multiple substrates

BACE1 is the canonical example of a graveyard target where the failure is
**predominantly target-specific (mechanism-based)**, not drug-specific — and
distinct from the NGF and Aβ graveyard patterns:

- **NGF graveyard (RPOA)**: on-target toxicity from blocking a single
  well-characterized pathway (NGF-TrkA nociception + joint homeostasis).
  Three different antibodies all caused the same RPOA. Target-specific but
  single-pathway.
- **Aβ graveyard (failed anti-amyloid antibodies)**: antibody-specific
  failures (wrong epitope, wrong species, wrong isotype, wrong dose). The
  target was validated by subsequent successes (lecanemab, donanemab).
  Drug-specific, not target-specific.
- **BACE1 graveyard (cognitive worsening)**: on-target toxicity from
  blocking an ENZYMATIC TARGET with >40 substrates beyond the intended
  target substrate (APP). BACE1 inhibition blocks processing of NRG1
  (myelination, synaptic plasticity), CHL1 (hippocampal axon guidance),
  SEZ6 (dendritic arborization), and other substrates essential for
  cognitive function. Six different small-molecule inhibitors from five
  companies all caused the same cognitive worsening or failed for futility.
  Target-specific, multi-substrate.

For field 6 (failure modes) of graveyard profiles where the target is an
ENZYME or PROTEASE with multiple physiological substrates: (1) the failure
analysis MUST enumerate the non-target substrates and their physiological
roles; (2) the cognitive/functional worsening is mechanism-based (on-target)
if it correlates with the known functions of non-target substrates; (3)
the failure cannot be rescued by changing the drug format or epitope — only
by achieving substrate selectivity (APP-selective BACE1 inhibition). This
is distinct from antibody-specific graveyard failures where epitope/isotype
changes can rescue the target. (PMID 32223911, PMID 30232227, PMID 30970186.)

## 3. Human genetics reveals the therapeutic window for mechanism-based toxicity

The APP A673T (Icelandic) variant reduces BACE1 cleavage of APP by 20-30%,
resulting in ~28% lower plasma Aβ40/Aβ42. Carriers are protected against AD
and age-related cognitive decline — human genetic proof that PARTIAL BACE1
inhibition is beneficial. However, clinical BACE1 inhibitors achieved >50-75%
CSF Aβ reduction — far exceeding the natural protective effect. The cognitive
worsening observed in clinical trials is consistent with excessive BACE1
inhibition blocking non-amyloid substrates beyond the therapeutic window.

For field 6 (failure modes) and field 11 (differentiation) of graveyard
profiles: when a human genetic variant reveals a NATURAL PARTIAL INHIBITION
that is protective, this defines the upper bound of the therapeutic window.
Clinical drug doses that exceed this natural inhibition level risk
mechanism-based toxicity from non-target substrate blockade. The A673T
variant is the BACE1 equivalent of the NGF R100W mutation (HSAN V) that
revealed the pain-sensitivity role of NGF — but with a critical difference:
A673T shows partial inhibition is BENEFICIAL (therapeutic window exists),
while R100W shows complete loss is pathological (toxicity is expected).
For orchestrators: when delegating a graveyard profile, instruct the
subagent to search for human genetic variants that naturally modulate the
target's activity — these define the therapeutic window. (PMID 32223911.)

## 4. Preclinical safety models did not predict clinical cognitive worsening

Verubecestat was tested in rats and monkeys at exposures >40-fold higher
than clinical doses. The preclinical toxicology assessment found NO evidence
of reduced nerve myelination, neurodegeneration, altered glucose homeostasis,
or hepatotoxicity (PMID 27807285). Yet the same drug caused cognitive
worsening in human clinical trials at therapeutic doses (PMID 30970186,
PMID 29719179). The adult conditional BACE1 KO mouse model (PMID 30232227)
retrospectively identified the hippocampal mossy fiber disorganization via
CHL1 — but this subtle axonal phenotype was not detected in standard
preclinical safety assessment.

For field 6 (failure modes) and field 8 (safety) of CNS-targeted enzyme
inhibitors: (1) standard preclinical toxicology (general behavior, motor
function, organ histology) does not detect subtle cognitive effects of
enzyme inhibition in the CNS; (2) the gap between preclinical safety and
clinical cognitive worsening is a systematic risk for CNS enzyme targets
with neurological substrates; (3) the adult conditional KO mouse model
identified the mechanism (CHL1 cleavage → hippocampal axon guidance)
retrospectively — this model should be part of preclinical safety assessment
for any CNS enzyme target with known substrates. For orchestrators:
CNS-targeted enzyme inhibitors require cognitive phenotyping beyond standard
tox, and the adult conditional KO model is the gold standard for detecting
on-target CNS effects. (PMID 27807285, PMID 30232227, PMID 30970186.)

## 5. Exosite vs active-site inhibition as a differentiation axis for enzymatic targets

The anti-BACE1 exosite antibody (Atwal 2011, PMID 21613622) binds
noncompetitively to an exosite on BACE1, NOT the catalytic active site. This
has two critical consequences: (1) the antibody does NOT inhibit BACE2 or
cathepsin D — highly selective, unlike all clinical small-molecule BACE1
inhibitors which also inhibited BACE2; (2) the exosite binding mode is
structurally distinct from active-site inhibition and may differentially
affect APP vs non-amyloid substrate cleavage.

All clinical BACE1 inhibitors (small molecules) targeted the active site and
co-inhibited BACE2, contributing to drug-class-specific side effects
(hair-color change from BACE2/melanocyte function). The exosite antibody
approach avoids BACE2 co-inhibition entirely. The review by Ugbaja 2022
(PMID 34102967) argues that non-active-site inhibition (exosite antibodies
and allosteric inhibitors) "might be the way forward" for BACE1 therapy.

For field 5 (epitope landscape), field 6 (failure modes), and field 11
(differentiation) of enzymatic targets: (1) the active-site vs exosite/allosteric
distinction is a critical differentiation axis — active-site inhibitors block
ALL substrates, while exosite/allosteric inhibitors may differentially
modulate substrate cleavage; (2) BACE2 co-inhibition is a drug-class liability
of active-site inhibitors, avoidable with exosite antibodies; (3) for any
enzyme target with multiple substrates, exosite/allosteric approaches should
be evaluated as a potential path to substrate selectivity. (PMID 21613622,
PMID 34102967, PMID 32223911.)

## 6. PubMed 429 rate-limiting with 9+ sequential queries

The profiling workflow ran 9+ esearch queries sequentially with 4-5s sleeps.
After 4-5 queries, PubMed returned HTTP 429 (Too Many Requests) on two
consecutive queries. Recovery required 15-20s waits. The esummary endpoint
also rate-limited at 16-PMID batch sizes. This is consistent with the
documented pattern: for profiling workflows that run 10+ E-utilities queries,
5s sleeps are the minimum and 429 recovery requires 15-20s. The NCBI ID
converter API (`pmc/utils/idconv/v1.0/`) did not rate-limit.

## 7. The entire pipeline ran via execute_code + urllib — no terminal, no browser

All PubMed searches (esearch, esummary, efetch), PMC HTML retrieval, NCBI ID
converter, and text extraction ran via Python `urllib.request` inside
`execute_code`. Paper metadata was saved to JSON files in `/tmp/` and passed
between calls. Full text was extracted from PMC HTML pages using a Python
`HTMLParser` subclass. No `terminal` or `browser_exec` calls were needed.
This confirms the established pattern: delegated profiling subagents run the
full pipeline (search → fetch → extract → profile write) through
`execute_code` + `write_file`.

(BACE1 profile, ~50K chars, 8 papers, 8 unique PMIDs cited, 198 PMID
citations, working-docs/hitlist-profiles/bace1.md.)
