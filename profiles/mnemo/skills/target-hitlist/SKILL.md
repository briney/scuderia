---
name: target-hitlist
description: Use when enumerating antibody targets with a binary bar.
triggers:
  - "antibody target hit list"
  - "hit list of targets"
  - "enumerate antibody targets"
  - "comprehensive target list"
  - "target enumeration"
---

# target-hitlist — therapeutic antibody target enumeration

A hit list is **not** a literature dive. The `literature-dive` skill is
depth-first on one topic — review-anchored, tier-classified, synthesized into
a concept page. A hit list is the opposite: **breadth-first enumeration** across
an entire disease area, with a binary inclusion bar and no depth. It is the
step BEFORE prioritization.

The output is a working doc (`working-docs/hitlist-<area>.md`), NOT a brain
page. No frontmatter, no indexing, no wikilinks, no concept page synthesis.
The working doc feeds a later prioritization phase.

## The binary bar

**IN**: There is sufficient evidence — compelling direct evidence OR very strong
circumstantial evidence — that antibodies against this target could potentially
show clinical benefit in a human disease.

**OUT**: The evidence does not meet this bar.

This is a binary gate. No ranking, no scoring, no prioritization at this stage.
The list is deliberately over-inclusive — marginal hits are encouraged. The
prioritization phase will filter; the enumeration phase should not.

### Scope rules (what's IN)

1. **All antibody modalities.** Naked mAb, ADC, bispecific, CAR-T, antibody
   fragments, Fc-fusions. The target is what matters, not the drug format.
2. **Approved drugs.** If any drug targeting this protein is approved, the
   target is in. Pipeline saturation does not exclude.
3. **Failed clinical trials.** If an antibody targeting this protein was tried
   and failed, the target is still in. The drug may be the problem (wrong
   epitope, wrong population, wrong dosing), not the target.
4. **No antibody attempted.** If only small-molecule drugs exist and the target
   is antibody-accessible (extracellular, secreted, or surface-exposed), the
   target is in if the small-molecule evidence shows the pathway matters.
5. **No drug at all.** If no drug has been attempted, but basic science or
   mechanistic evidence (KO mice, human genetics, disease association) suggests
   drugging the target could have clinical benefit AND the target is
   antibody-accessible, the target is in.

### What's OUT

- Intracellular targets with no credible antibody-accessible strategy.
  Exception: if there is a credible antibody-based strategy (MHC-presented
  peptides, intrabodies, targeted protein degradation), note the strategy.
- Pure correlation with no mechanistic support.
- Evidence too speculative to clear the bar.

## Target record format

Each target is recorded as:

```
### [Target name — gene symbol]
- **Disease(s)**: [indication(s)]
- **Evidence type**: approved | clinical-trial | failed-clinical | preclinical | mechanistic
- **Evidence**: [1-2 line summary]
- **Reference**: [DOI/PMID, FDA approval ID, or ClinicalTrials.gov NCT ID]
```

Evidence types (in priority order):
- **approved** — An antibody or other drug targeting this protein is FDA/EMA-approved.
- **clinical-trial** — An antibody targeting this protein is in active clinical development.
- **failed-clinical** — An antibody targeting this protein was in clinical trials and failed.
- **preclinical** — Antibody or biological targeting in preclinical development or exploratory.
- **mechanistic** — No drug attempted; evidence is from basic science.

Group targets by evidence type in the working doc — this gives a natural
priority gradient without doing actual prioritization.

## The discovery workflow

### Step 1: Database extraction (reusable across phases)

Scrape the **Antibody Society** web tables — these are the single highest-yield,
lowest-effort source. Three tables, all scraped via urllib with regex table
extraction:

- Approved antibodies (product data): `antibodysociety.org/antibody-therapeutics-product-data/` (~229 rows)
- Late-stage clinical studies: `antibodysociety.org/antibodies-in-late-stage-clinical-studies/` (~178 rows)
- Approved antibodies with indications: `antibodysociety.org/resources/approved-antibodies/` (~168 rows)

Each table has columns: INN, Brand Name, Target, Format, Indication,
Therapeutic Area, approval years. Extract the Target column, normalize names,
and classify by disease area using keyword matching on indications + therapeutic
areas.

**Key efficiency**: the database scrape is done ONCE and serves ALL phases.
Save the scraped data to a JSON file and reuse across disease areas.

### Step 2: ATW pipeline census (reusable across phases)

Extract tables from the **"Antibodies to watch"** annual series (mAbs, open
access via Europe PMC). The latest is "Antibodies to watch in 2026" (PMID
41560619, PMC12826703). Pull the fullTextXML from Europe PMC
(`europepmc.org/webservices/rest/PMC<ID>/fullTextXML`) and parse `<table-wrap>`
elements with regex. Tables contain: INN, Target, Format, Indication, Phase.

See `references/atw-series.md` for the full PMID list (2014–2026).

### Step 3: Systematic family coverage

For each disease area, define the relevant protein families and search every
member individually in PubMed with antibody-development queries. This is the
**highest-value step** — it surfaces preclinical and mechanistic targets the
databases entirely miss.

Pattern:
```python
query = f'{target_name}[tiab] AND (antibody OR therapeutic) AND (disease_terms)[tiab]'
# Fetch count via PubMed esearch, sleep 2s between queries
```

Classify by hit count: >50 = HIGH, 11–50 = MEDIUM, 1–10 = LOW, 0 = ZERO.
HIGH and MEDIUM targets are generally IN. LOW targets need a closer look
(may still be in if the biology is strong but the field is young).

See `references/protein-families.md` for family lists by disease area.

### Step 4: Domain knowledge

Fill in targets with known antibody development not captured by databases or
PubMed searches. This is the least systematic source and the most
error-prone — flag for expert review. Domain knowledge plays a larger role
in oncology and infectious disease than in immunology because the target
landscape is broader.

### Step 5: Compile initial list

Merge all sources, normalize target names, deduplicate, assign evidence types.
Write the per-area working doc to `working-docs/hitlist-<area-slug>.md`.

### Step 6: Gap-fill (STANDARD — not optional)

After the initial enumeration (Steps 1–5), run three gap-fill searches. The
gap-fill is where the value compounds — the immunology pilot added 47 targets
(28% of the final list) from gap-fill alone, including 42 chemokine targets
that the database-centric approach entirely missed.

**Gap 1: Systematic family sweep.** Identify the area's largest under-covered
protein family and search every member individually in PubMed with
antibody-development queries. For immunology, the chemokine system was the
gap (55 receptors/ligands, 42 new targets). For oncology, RTK family members
and tumor antigens. For neuroscience, pain channels and neurotrophins.

**Gap 2: ClinicalTrials.gov search.** REST API v2
(`clinicaltrials.gov/api/v2/studies`):
- Active trials: `query.intr=monoclonal antibody&query.cond=<disease>` for
  each disease in the area's scope
- Failed trials: add `filter.overallStatus=TERMINATED,WITHDRAWN,SUSPENDED`
- Extract drug names from intervention fields; cross-reference against
  existing target list; resolve novel drug names to targets via PubMed
- A large exclusion list is needed to filter dose variants, biosimilars, and
  non-antibody concomitant drugs (see `references/clinicaltrials-gov-api.md`)

**Gap 3: Failed trial recovery.** From the terminated/withdrawn trial search,
extract drug names not in the current list. Resolve targets via PubMed
abstract search. Targets from failed trials are included (the drug may be the
problem, not the target). The value is in drugs you've never heard of —
already-approved antibodies that failed in a new indication confirm the target
but don't add new ones.

### Step 7: Write and commit

1. Write the per-area target list to `working-docs/hitlist-<area-slug>.md`
2. Update `working-docs/hitlist-master.md` (topic areas table status + count
   + phase learnings)
3. Commit with: `hitlist: <area> complete, N targets`

## Environment

- PubMed E-utilities REST API via urllib. Entrez Direct CLI (esearch/efetch)
  is NOT installed. Base URL: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`
  (NOT `/nih-annotator/eutils/` — that returns 404). Sleep 5s between
  sequential calls (2–3s is insufficient and triggers HTTP 429); after 3×
  HTTP 429, wait 15+s. Semantic Scholar is the fallback.
  See `references/api-templates.md` for esearch/esummary/efetch code patterns
  including ElementTree XML parsing for efetch (regex parsing fails — greedy
  matching returns the first article for all PMIDs).
- ClinicalTrials.gov REST API v2: `clinicaltrials.gov/api/v2/studies`. Use
  `query.intr` for intervention, `query.cond` for condition,
  `filter.overallStatus` for trial status. No authentication needed.
- Europe PMC for open-access full text: `europepmc.org/webservices/rest/PMC<ID>/fullTextXML`
- Raise FD limit before parallel work: `ulimit -n 4096`
- Working docs are NOT indexed by QMD and do not appear in search results.
- All output must be in English.

## Pitfalls

- **Synonym confusion.** Same protein under multiple names (TNFSF13B = BAFF =
  BLYS = CD257). Deduplicate by gene symbol or UniProt ID. Build a
  normalization map early and apply it consistently.
- **Target vs. drug.** Record the target, not the drug. Adalimumab is the drug;
  TNF is the target.
- **PubMed search noise.** Broad queries ("therapeutic targets" + disease
  terms) return thousands of irrelevant hits. Targeted queries with specific
  protein names + "antibody" + "clinical OR trial" are far more productive.
- **Immunotoxin-payload noise for toxin targets.** When searching for
  antibodies AGAINST a bacterial toxin (e.g., P. aeruginosa exotoxin A,
  diphtheria toxin), ~70% of PubMed hits will be papers using that toxin as
  a PAYLOAD in immunotoxin conjugates for cancer therapy, not papers
  developing antibodies to neutralize the toxin itself. Add filter terms
  like `AND (neutralizing OR "passive immunization" OR "anti-toxin" OR
  infection[tiab])` and exclude `AND NOT (immunotoxin OR fusion OR
  payload)[tiab]` to reduce payload noise. (PEA profile, 2026-08-17.)
- **ClinicalTrials.gov drug name extraction is messy.** Many entries are dose
  variants ("140 mg brodalumab"), biosimilars, or non-antibody concomitant
  drugs. A large exclusion list is needed. Unknown-target drugs require PubMed
  follow-up for target resolution.
- **Distinguishing disease areas.** Many targets (CD20, CD38, PD-1, CTLA-4,
  LAG-3) are approved for cancer but also have immunology relevance. Both the
  target's biology and its indication landscape determine the area. A target
  may appear in multiple area lists — this is correct.
- **The failed-trials search surfaces mostly known drugs.** Most
  terminated/withdrawn trials use already-approved antibodies that failed in a
  specific indication. These confirm the target but don't add new ones. The
  value is in the drugs you've never heard of.
- **The database under-represents infectious disease.** Most infectious
  disease antibodies are prophylactic, post-exposure, or government-funded
  biodefense products that don't fit the commercial therapeutic model. The
  family sweep and domain knowledge added 92% of the infectious disease list.
- **Domain knowledge is the least systematic source.** It fills gaps but is
  error-prone. Flag domain-knowledge targets for expert review.

## What this guarantees

- The list starts from expert curation (Antibody Society tables + ATW annual
  census), not a bare keyword search.
- The family sweep catches targets the databases miss — especially
  preclinical and mechanistic targets with strong biology but no drug
  development.
- ClinicalTrials.gov catches targets in active development and, critically,
  targets from failed trials that are still viable per the binary bar.
- The gap-fill is standard, not optional — it adds 20–30% to the final list.
- The working doc is the deliverable — grouped by evidence type, minimal
  target records, enough to feed prioritization without being a burden.

## Anti-patterns

- **Treating this as a literature dive.** No tier classification, no
  supplementary passes, no concept page. The goal is exhaustive enumeration,
  not depth on any single target.
- **Ranking or prioritizing during enumeration.** The binary bar is in or out.
  Prioritization is a separate, later effort.
- **Skipping the gap-fill.** The gap-fill adds 20–30% of the final list,
  including the most valuable targets (antibody-accessible proteins with
  biological rationale but no drug development yet).
- **Over-filtering marginal hits.** Marginal hits are encouraged at this
  stage. The prioritization phase will filter; the enumeration phase should
  not. Missing a real target is worse than including a marginal one.
- **Creating a brain page instead of a working doc.** The hit list is a
  working doc — no frontmatter, no indexing, no wikilinks. If a target's
  content becomes load-bearing, promote it to a brain page later.

## Relationship to other skills

- **`literature-dive`**: Depth-first on one topic. The hit list is
  breadth-first across a disease area. Different methodology, different
  output. The hit list is the step before prioritization; the literature dive
  is the step after a target is selected for deep investigation.
- **`target-prioritization`**: Ranks viruses for mAb discovery. The hit list
  enumerates all targets; prioritization ranks them. The hit list feeds
  prioritization.
- **`target-profiling`**: Builds comprehensive per-target profiles (11-field
  template) from the hit list. The hit list provides the target list and
  tier assignments; profiling builds the reusable fact base. Profiles are
  built at key-paper-ingestion level (3-5 landmark papers ingested per target).
- **`intersect`**: Single-item ranker across the brain. The hit list is
  multi-item enumeration across external databases + literature.

## Relationship to the molecule-side registry

The hit-list is the **target-side** corpus. Its molecule-side complement is
`references/therapeutic-antibodies/` (managed by the
`therapeutic-antibody-registry` skill) — one record per drug product (INN),
across all modalities and stages. The two cross-reference: each molecule
entry carries a `target_hitlist` pointer to the corresponding target profile
or hit-list entry; the hit-list's "Antibody landscape" field lists molecules
the registry authoritatively tracks.

## Changelog

- **2026-08-15 — initial creation.** Built during the first-pass hit list
  project across 6 disease areas (immunology, oncology, neuroscience,
  infectious disease, cardiovascular & metabolic, ophthalmology & rare
  diseases). Methodology validated: 920 total targets across all areas.
  Gap-fill added 28% of the immunology list, 50% of the oncology list, and
  92% of the infectious disease list.
- **2026-08-15 — profiling connection added.** Added `target-profiling`
  to the relationship section. The hit list feeds profiling, which builds
  durable per-target profiles at key-paper-ingestion level. The stratified
  random sampling pilot approach (20 targets from one area, spanning all
  tiers) is documented in the `target-profiling` skill.
