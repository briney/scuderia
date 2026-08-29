# C. difficile toxin B (TcdB) profile observations (2026-08-16)

Twenty-ninth level-2 profile (approved tier, infectious disease — C. difficile
infection recurrence prevention). TcdB is the **second bacterial toxin target
profile** (after anthrax PA) and the **first bacterial toxin target with a
human-efficacy-validated antibody** (bezlotoxumab/Zinplava, FDA approved
2016 — anthrax PA antibodies were approved via the Animal Rule with zero human
efficacy data). It is also the **first profile where a combination antibody
strategy was tested and failed** (actoxumab + bezlotoxumab dual-toxin blockade
was not superior to bezlotoxumab alone in MODIFY II), and the **first profile
where endogenous antibody biomarker data independently validates the
therapeutic antibody target selection** (endogenous anti-TcdB antibodies
protect against recurrence; endogenous anti-TcdA do not). 5 papers ingested:
1/5 PMC XML OA (Pruitt 2012, Front Cell Infect Microbiol — 48K chars body
text), 4/5 abstract-only (3 OUP/Clin Infect Dis + 1 Wolters Kluwer/J Clin
Gastroenterol — all paywalled, no PMCID, jina Cloudflare-blocked, Wayback
CDX returned 0 snapshots). 20% full-text retrieval. ~33K chars (profile),
7 unique PMIDs cited. New observations:

## 1. Blocking one toxin was better than blocking both — the actoxumab failure

The MODIFY I/II trials tested bezlotoxumab (anti-TcdB) alone, actoxumab
(anti-TcdA) alone, and the combination. Actoxumab alone was discontinued
from MODIFY I after interim analysis (no benefit over placebo, more
deaths/SAEs). The combination (actoxumab + bezlotoxumab) was NOT superior
to bezlotoxumab alone in either trial (MODIFY I: 16% vs 17% recurrence;
MODIFY II: 15% vs 16%). This is the first profile in the set where a
dual-target combination was formally tested against monotherapy and the
monotherapy was equivalent or superior.

The biological explanation comes from the endogenous antibody analysis
(PMID 31628838, Kelly 2020): in the placebo arm (n=773), higher endogenous
anti-TcdB (eAb-B) titers correlated with lower recurrence (22% high eAb-B
vs 35% low/medium, P=.015), while endogenous anti-TcdA (eAb-A) titers
showed NO correlation with recurrence at any time point. The human immune
system's own protective mechanism is specifically anti-TcdB, not anti-TcdA
— directly concordant with the therapeutic antibody results.

For field 6 (failure/success modes), this is the headline insight:
targeting the dominant toxin (TcdB) is both necessary AND sufficient.
Adding anti-TcdA (actoxumab) provides no incremental benefit because (a)
TcdA is not essential for virulence (TcdA-negative strains are virulent
in animal models), (b) the human immune system does not use anti-TcdA to
prevent recurrence, and (c) TcdB is 100–10,000× more potent as a
cytotoxin than TcdA. For field 11 (differentiation), the lesson is that
dual-target combinations are not always superior to monotherapy — when
one target dominates the disease biology, adding a second target adds
complexity without benefit and may introduce safety signals (actoxumab
alone had more deaths/SAEs than placebo). (PMID 28121498, PMID 31628838.)

## 2. Endogenous antibody biomarker as independent target validation

The Kelly 2020 paper (PMID 31628838) is the single most important
mechanistic reference for this profile because it provides human-derived,
non-therapeutic evidence that anti-TcdB is the protective immune response.
By measuring endogenous anti-TcdA and anti-TcdB titers in the placebo arm
of MODIFY I/II and correlating them with recurrence, the study
demonstrates that the immune system's own protection mechanism is
specifically and exclusively anti-TcdB.

This is a new pattern not seen in prior profiles: **endogenous antibody
biomarker data as independent target validation**. The concordance
between endogenous immunity (eAb-B protects, eAb-A doesn't) and
therapeutic antibody efficacy (bezlotoxumab works, actoxumab doesn't)
provides a biological rationale for the paradoxical finding that blocking
one toxin is better than blocking both.

For field 3 (disease evidence) and field 7 (biomarker assays), the eAb-B
titer is both a target validation biomarker (confirms TcdB is the right
target) and a potential patient selection biomarker (patients with low
baseline eAb-B are at highest recurrence risk and would benefit most
from bezlotoxumab). This pattern may generalize to other anti-toxin
antibody targets where endogenous antibody levels can be measured and
correlated with disease outcomes. (PMID 31628838.)

## 3. OUP/Clinical Infectious Diseases is a hard block for target profiling

Three of the five key papers for this profile were published in Clinical
Infectious Diseases (Oxford University Press): PMID 32735653 (Johnson
2021), PMID 31883370 (Goldstein 2020), PMID 31628838 (Kelly 2020). All
three had no PMCID, EPMC isOpenAccess: N, inPMC: N, hasPDF: N. The jina
reader proxy was blocked by Cloudflare ("Just a moment... Performing
security verification") on both the advance-article URL and the DOI
redirect. Wayback CDX returned 0 snapshots for all three.

This confirms the paper-ingest skill's OUP/ATS entry (Cloudflare
interstitial). For target profiling, the impact is significant: the
MODIFY trial secondary analyses and biomarker studies — which carry the
most clinically actionable data for fields 3, 6, and 8 — are published in
Clin Infect Dis and are consistently abstract-only. The structured
abstracts (1,000–1,700 chars with BACKGROUND/METHODS/RESULTS/CONCLUSIONS)
were sufficient for profile grounding, but the full safety data, subgroup
forest plots, and detailed methods were not accessible.

For orchestrators: when selecting papers for C. difficile or infectious
disease profiles, expect Clin Infect Dis papers to be abstract-only and
prioritize them for the abstract's structured content. The 12-week
recurrence rates, NNT values, and P-values are all present in the
structured abstracts — sufficient for field 3 and field 6 without full
text. (PMID 32735653, PMID 31883370, PMID 31628838.)

## 4. Bacterial toxin target — same gene/UniProt adaptations as anthrax PA

Like anthrax PA, TcdB is a bacterial protein encoded by a bacterial gene
(tcdB), not a human gene. The UniProt ID (Q06144) is for the C. difficile
protein, not a human protein. Field 1 should note the organism
explicitly and flag that this is NOT a human gene. Field 2 "cell types
expressing" inverts: C. difficile produces the toxin, not host cells —
instead, describe which host cells the toxin targets (colonic epithelial
cells via FZD, submucosal/endothelial cells via CSPG4).

This confirms the anthrax PA observation: for bacterial toxin targets,
the template fields need the same organism/gene adaptation. The
existing skill already documents this pattern from the anthrax PA
profile — no new skill change needed, but the C. difficile profile
confirms it generalizes across infectious disease toxin targets.
(PMID 22919620, PMID 34862749.)

## 5. Existing paper pages as profile references — the brain's accumulated knowledge

A key workflow difference in this profile: the brain already contained
5 C. difficile paper pages (Wilcox 2017 MODIFY trial, Aktories 2017 toxin
biology, Chandrasekaran 2017 toxin role, Chen 2022 TcdB receptor binding,
Kroh 2025 TcdA/TcdB mouse mAbs, Pourliotopoulou 2024 toxin mechanisms).
These existing pages were used as additional references for the profile
without re-ingesting them — the profile cites PMIDs from both the 5 newly
ingested papers AND the pre-existing brain pages.

For orchestrators: before dispatching a target profiling subagent, check
the brain's `papers/` directory for existing paper pages relevant to the
target. The subagent should be told which papers already exist so it can
read them directly (via read_file) rather than re-ingesting them. This
saves time and avoids duplicate paper pages. The subagent should still
ingest 3-5 NEW papers not already in the brain to ensure the profile is
grounded in fresh full-text content. In this session, 4 of 5 papers were
new (PMID 22919620, 32735653, 31883370, 31628838) and 1 already existed
(PMID 34862749/Chen 2022) — the subagent correctly identified the
existing page and used it as a reference without re-ingesting.

## 6. Wolters Kluwer / J Clin Gastroenterol is a new publisher block

PMID 32053529 (Akiyama 2021, J Clin Gastroenterol) was published by
Wolters Kluwer/Lippincott. No PMCID, EPMC all flags N. Jina was not
attempted for this paper (the pipeline went directly to abstract-only
after EPMC gate). Wayback CDX was not attempted. The structured abstract
(1,627 chars) contained sufficient meta-analysis data (risk ratios, 95%
CIs, P-values) for profile grounding.

This is a new publisher encounter for the target profiling workflow.
Wolters Kluwer/Lippincott journals (J Clin Gastroenterol, others) should
be treated as likely abstract-only for target profiling — the structured
abstracts typically carry the key quantitative results. No addition to
the paper-ingest known-blocks table is needed (this is a profiling-level
observation, not a full-text retrieval workflow change). (PMID 32053529.)

## 7. 12-month observational follow-up data — durability evidence for field 6

The Goldstein 2020 paper (PMID 31883370) provides 12-month observational
follow-up from MODIFY II, showing zero late recurrences (0/69) in the
bezlotoxumab-alone group after sustained 12-week cure, vs 2/65 in the
combination group. This is a unique data type not seen in prior profiles:
**extended follow-up beyond the primary endpoint** demonstrating that
the antibody's effect is prevention, not delayed onset.

For field 6 (success factors), extended follow-up data strengthens the
"durability of protection" claim. For field 3 (disease evidence), it
addresses a key clinical question: does the antibody merely postpone
recurrence or truly prevent it? The 12-month data confirm prevention.
When selecting papers for target profiling, include at least one paper
with extended follow-up data if available — it provides the strongest
evidence for the durability of the antibody's therapeutic effect.
(PMID 31883370.)

## 8. PubMed search strategy for infectious disease toxin targets

The PubMed search strategy for this profile used a combination of
review-focused queries and drug-specific queries:
- `bezlotoxumab AND Clostridium difficile AND review[pt]` — 93 results
- `C. difficile toxin B AND antibody AND review[pt]` — 49 results
- `bezlotoxumab MODIFY trial` — 10 results (surfaced the pivotal secondary
  analyses)
- `actoxumab bezlotoxumab` — 10 results (surfaced the combination failure
  literature)
- `Clostridium difficile toxin B structure mechanism review[pt]` — 7
  results (surfaced the structural biology papers)

The review-focused queries returned the broadest results but missed the
key clinical papers (MODIFY secondary analyses, biomarker study). The
drug-specific queries were essential for finding the clinical evidence.
This confirms the anthrax PA observation: always add non-review queries
for infectious disease targets — the pivotal clinical trial secondary
analyses and biomarker studies are primary research papers, not reviews.

For the EPMC ORCID extraction, the `authorId` field for one author (Lacy
D Borden) was a dict `{'type': 'ORCID', 'value': '0000-0003-2273-8121'}`
rather than a string — confirming the paper-ingest skill's type-safety
pitfall. Always use `isinstance(author_id, str)` before string operations
on EPMC authorId fields. (PMID 22919620.)
