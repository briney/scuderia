---
name: antibody-target-hitlist
description: "Enumerate antibody targets and build deep profiles."
triggers:
  - "antibody target hit list"
  - "hit list of targets"
  - "target profiling"
  - "build target profiles"
  - "comprehensive target enumeration"
  - "antibody discovery target"
---

# antibody-target-hitlist — comprehensive antibody target enumeration and profiling

A multi-phase campaign to build a comprehensive "hit list" of therapeutic
antibody targets across all of human medicine, then build deep, reusable
target profiles for each target worth pursuing. The hit list is a
breadth-first enumeration (not a literature dive); the profiles are
key-paper-ingestion-level syntheses grounded in full-text content.

## Key distinction from literature-dive

`literature-dive` is depth-first on ONE topic — review-anchored, tier-classified,
synthesized into a concept page. This skill is the OPPOSITE: breadth-first
enumeration across an entire disease area, with a binary inclusion bar (in or
out), no tiering, and no concept page synthesis. The profiles come later, as
a separate phase, and use a different methodology (key-paper-ingestion per
target, not a literature dive per topic).

## Key distinction from target-prioritization

`target-prioritization` ranks VIRUSES for mAb discovery using a virology-
specific rubric (BSL, serotype, seroprevalence, etc.). This skill enumerates
PROTEIN TARGETS for antibody therapeutics across all diseases, using a
binary evidence bar, then builds comprehensive profiles. The two skills
are complementary — target-prioritization is for the virus discovery
program; this skill is for the broader antibody therapeutic landscape.

## Phase 1: Hit list enumeration

### The binary bar

**IN**: There is sufficient evidence — compelling direct evidence OR very
strong circumstantial evidence — that antibodies against this target could
potentially show clinical benefit in a human disease.

**OUT**: The evidence does not meet this bar.

This is a binary gate. No ranking, no scoring, no prioritization at this
stage. Prioritization is a separate, later effort.

### Scope rules

- **All antibody modalities**: naked mAb, ADC, bispecific, CAR-T, fragments,
  Fc-fusions. The target is what matters, not the format.
- **Approved drugs**: IN. Pipeline saturation does not exclude.
- **Failed clinical trials**: IN. The drug may be the problem, not the target.
- **No antibody attempted**: IN if the target is antibody-accessible AND
  small-molecule or basic-science evidence shows the pathway matters.
- **No drug at all**: IN if mechanistic evidence (KO, genetics, disease
  association) suggests drugging could help AND the target is antibody-accessible.
- **Intracellular targets**: OUT unless a credible antibody-based strategy
  exists (surface expression, MHC presentation, intrabody, targeted degradation).

### Disease area subdivision

The enumeration is organized by disease area, each producing its own working
doc. The areas (and their working doc slugs):
1. Immunology & autoimmunity (`hitlist-immunology-inflammation.md`)
2. Oncology (`hitlist-oncology.md`)
3. Neuroscience (`hitlist-neuroscience.md`)
4. Infectious disease (`hitlist-infectious-disease.md`)
5. Cardiovascular & metabolic (`hitlist-cardiovascular-metabolic.md`)
6. Ophthalmology & rare diseases (`hitlist-ophthalmology-rare.md`)

A master guide (`hitlist-master.md`) ties the areas together and contains the
methodology, scope rules, and per-area learnings. The master guide is
self-contained — a future phase can launch in a fresh context window using
only this document.

### Discovery methodology (per area)

The methodology has 8 steps, 3 of which are gap-fill (standard, not optional):

1. **Enumeration from comprehensive reviews** — Search PubMed for the most
   comprehensive reviews that enumerate antibody targets in the disease area.
   Extract target lists, not full ingests.
2. **Database cross-reference** — Scrape the Antibody Society web tables
   (approved, late-stage, approved-with-indications) via urllib. These are
   the highest-yield, lowest-effort source.
3. **Systematic family coverage** — Go through protein families relevant to
   the disease area. For each family member: is there evidence that
   antibodies against this target could show clinical benefit?
4. **Mechanistic target identification** — Search for targets where no drug
   has been attempted but mechanistic evidence suggests therapeutic potential.
5. **Failed target recovery** — Search for targets where antibody clinical
   trials failed. These are still IN (the drug may be the problem).
6. **Coverage verification** — Cross-check for systematic gaps.
7. **Compile and write** — Write the per-area target list using the target
   record format. Group by evidence type.
8. **Gap-fill (STANDARD — not optional)**:
   - **Gap 1: Systematic family sweep** — Every member of key protein families
     searched individually in PubMed. Identify the area's largest
     under-covered family and sweep it exhaustively.
   - **Gap 2: ClinicalTrials.gov search** — REST API v2
     (`clinicaltrials.gov/api/v2/studies`). Query:
     `query.intr=monoclonal antibody` + `query.cond=<disease>` for each
     disease. Also search terminated/withdrawn trials
     (`filter.overallStatus=TERMINATED,WITHDRAWN,SUSPENDED`).
   - **Gap 3: Failed trial recovery** — From terminated/withdrawn trials,
     extract drug names not in the current list. Resolve targets via PubMed.
     Targets from failed trials are included.

### Target record format

```
### [Target name — gene symbol]
- **Disease(s)**: [indication(s)]
- **Evidence type**: approved | clinical-trial | preclinical | failed-clinical | mechanistic
- **Evidence**: [1-2 line summary]
- **Reference**: [DOI/PMID, FDA approval ID, or ClinicalTrials.gov NCT ID]
```

### Key data sources

- **Antibody Society tables**: `antibodysociety.org/antibody-therapeutics-product-data/`
  (approved, 229 entries), `antibodysociety.org/antibodies-in-late-stage-clinical-studies/`
  (late-stage, 178 entries), `antibodysociety.org/resources/approved-antibodies/`
  (approved with indications, 168 entries). Scrape via urllib with regex
  table extraction. These tables are the backbone — everything else is
  gap-filling. The database scrape is done ONCE and serves all areas.
- **"Antibodies to watch" series**: Annual mAbs papers (PMID list: 41560619
  for 2026, 39711140 for 2025, 38178784 for 2024, etc.). Open access via
  Europe PMC. Tables extracted from PMC XML.
- **YAbS database**: `db.antibodysociety.org` (2,900+ candidates). Paper:
  PMID 40013403.
- **PubMed E-utilities**: REST API via urllib (Entrez Direct CLI NOT installed).
  Rate limiting is AGGRESSIVE and unpredictable — 429s can hit on the very
  first call of a session (not just after repeated calls). Observed in
  profile-building: the first esearch often 429s; 3-5s between calls is
  insufficient under concurrent/parallel subagent load. Use **4-5s between
  individual calls within a batch, but 20-25s between batches** (esearch →
  esummary → efetch sequences). After ANY HTTP 429, wait 20-25s before
  retrying, not 15s. Fetch summaries (esummary) before abstracts (efetch)
  to triage — esummary is lighter and lets you pick the 3-5 best PMIDs
  before spending efetch calls.
- **ClinicalTrials.gov API v2**: `clinicaltrials.gov/api/v2/studies`. No
  authentication needed. Use `query.intr` for intervention, `query.cond` for
  condition, `filter.overallStatus` for trial status.

### Where hit lists live

`working-docs/hitlist-*.md` — working docs, NOT brain pages. No frontmatter,
no indexing, no wikilinks. The master guide is `working-docs/hitlist-master.md`.

## Phase 2: Target profiling

### Profile template (11 fields)

1. **Target identity** — name, gene, UniProt, family, localization, MW, oligomerization, domains
2. **Biological mechanism** — function, pathway, effect of blockade/activation, cell types, signaling
3. **Disease evidence** — per disease: type (genetics/clinical/preclinical/mechanistic), summary, PMIDs
4. **Antibody landscape** — per known antibody: INN, company, format, isotype, phase, outcome, epitope
5. **Epitope landscape** — mapped epitopes, structural data (PDB), neutralizing vs non-neutralizing, bins
6. **Known failure modes and success factors** — what succeeded/failed and WHY (epitope, format, dosing, population, safety)
7. **Assay systems** — functional assays, in vivo models, key readouts, biomarkers, cell lines
8. **Safety profile** — toxicities, mechanism, organ-specific, therapeutic index, black box warnings
9. **Structural information** — PDB structures, glycosylation, conformational states, epitope accessibility
10. **Competitive landscape** — pipeline depth, companies, patents, market, gaps
11. **Differentiation opportunities** — judgment (clearly marked): format, epitope, population, mechanism

Fields 1-10 are facts (cite PMIDs). Field 11 is judgment.

### Key-paper-ingestion level of rigor

Each profile is grounded in 3-5 landmark papers ingested via the `paper-ingest`
skill (full pipeline: PubMed identity resolution → full-text retrieval →
distillation into `papers/` → verification). Fields 2, 3, and 6 must be
grounded in full-text content, not just abstracts.

**Abstract-level vs key-paper-ingestion**: The pilot showed that abstract-level
synthesis (reading abstracts only) produces profiles with factual errors.
Full-text ingestion caught 3 errors in the 20-target pilot:
- CD147/begelomab misattribution (begelomab targets CD26/DPP4, not CD147)
- C5aR1/ADVOCATE Phase 3 trial retraction (retracted June 2026)
- Properdin UniProt ID error (P05155 is C1 inhibitor, not properdin)

Always use key-paper-ingestion level for profiles.

### Landmark-paper search strategy (for profiles)

The skill says "search PubMed → ingest 3-5 papers" but the *search strategy*
matters for finding the right landmark papers, not just any papers. Use
this multi-query approach via PubMed E-utilities (urllib):

1. **Multiple `[tiab]` query formulations** — run 2-3 different title/abstract
   formulations of the target (e.g., `"ESAT-6 antibody"[tiab]`, `"early
   secreted antigen 6"[tiab]`, full species+target). Union the PMID sets.
2. **Author+topic searches for known landmark authors** — if you know or
   discover a key author (from a review or the first hit's author list),
   search `AuthorName + target + structure/discovery/mechanism` to find the
   seminal paper (e.g., `Renshaw ESAT-6 structure` found the 2002 and 2005
   NMR structure papers).
3. **Mechanism/structure-specific queries** — search for `target +
   structure/crystal/PDB`, `target + complex`, `target + monoclonal +
   protection` to find structural data and any antibody functional studies.
4. **Triage with esummary BEFORE efetch** — fetch titles/journals/dates for
   all candidate PMIDs (batched, comma-separated IDs) first, then pick the
   3-5 most relevant before spending rate-limited efetch calls on full
   abstracts. This conserves API calls and focuses on landmark papers.
5. **Prioritize**: original discovery paper, key structure paper, key
   mechanism/pathogenesis paper, key antibody/therapeutic paper (if any),
   and a recent review. Cite PMIDs throughout the profile.

This multi-query approach consistently finds seminal papers that a single
keyword search misses (e.g., the 1995 Sørensen discovery and 2002/2005
Renshaw structure papers were only found via author+topic queries, not the
initial `[tiab]` target search).

### Target selection for profiling

- **Profile ALL**: approved, clinical-trial, failed-clinical targets
- **Profile SELECTIVELY**: preclinical targets with at least one of: known
  antibody in development, human genetic validation, >20 PubMed hits for
  antibody/therapeutic approaches, published structure, or active area of
  antibody research
- **EXCLUDE**: preclinical targets with no antibody development, no genetics,
  <10 PubMed hits, or only intracellular expression

### Subagent delegation pattern

Profiles are built by delegated subagents:
- Batch 3 targets per delegation (concurrent limit)
- Each subagent gets: target name, gene, tier, area, template path, key
  context (known antibodies, key PMIDs if available, key biological points)
- Subagent workflow: search PubMed → ingest 3-5 papers via paper-ingest →
  read full-text → write profile → return path + paper list
- Orchestrator: verify each batch (check files on disk), commit with
  descriptive message, note any tier recalibrations or factual corrections
- Raise FD limit: `ulimit -n 4096` before dispatching

### Where profiles live

`working-docs/hitlist-profiles/<target-slug>.md` — working docs, not brain
pages. The template is at `working-docs/hitlist-profiles/TEMPLATE.md`.
High-value profiles may eventually be promoted to brain concept pages.

### Ingest artifact convention

Each profile is accompanied by a `_<target-slug>_ingest/` directory
(also under `working-docs/hitlist-profiles/`) containing:
- `papers.json` — the full paper records (PMID, title, abstract, journal,
  pubdate, authors, DOI) fetched via PubMed E-utilities, saved as JSON.
- `INGEST-LOG.md` — a markdown table of all ingested papers (PMID, title,
  first author, year, journal, full-text? = No) plus the PubMed search
  queries used and any rate-limiting notes.

This convention was established with the M. tb LAM profile
(`_mtb_lam_ingest/`) and continued with the M. tb ESAT-6 profile
(`_mtb_esat6_ingest/`). It provides an auditable trail of which papers
were retrieved and how, without creating brain pages for each paper.
Subagents building profiles should always save these artifacts.

## Phase 3: Prioritization (future)

Profiles are durable and reusable. Different prioritization runs query the
same profiles with different weights:
- **Platform demonstration**: weight saturated targets (known epitope
  landscape, known success AND failure, existing assays)
- **Real discovery pipeline**: weight blue ocean and graveyard targets
  (novel, de-risked by failure, uncompetitive)
- **Grant targeting**: weight unmet need and biological validation

The profile is the record; the scoring is the query. Build the fact base
once, run many queries.

### The graveyard sweet spot

Failed-clinical targets ("the graveyard") are the highest-value profiles
for a discovery program. The failure is usually antibody-specific (epitope,
format, dosing), not target-specific. The failure analysis (field 6) tells
you what NOT to do — and by implication, what a better antibody should do.

The canonical example: anti-Aβ antibodies. Bapineuzumab, solanezumab,
gantenerumab, crenezumab, ponezumab all failed. Then aducanumab, lecanemab,
and donanemab succeeded. Same target. The difference was epitope specificity
and conformational selectivity. The graveyard wasn't dead — it was waiting
for a better antibody.

### Saturated targets for platform demonstration

For in silico pipeline validation, saturated targets are better than
graveyard targets because you know BOTH what succeeded AND what failed.
The ground truth (known epitopes, known functional consequences, known
structural basis) lets you test whether your pipeline would have found the
winners and avoided the losers. Graveyard targets only tell you what failed
— you'd need a full preclinical workup to know if a novel antibody works.

## Pitfalls

- **Starting from keyword search instead of databases.** The Antibody
  Society tables are the highest-yield source. Start there.
- **Treating the hit list as a literature dive.** No tier classification,
  no supplementary passes, no concept page. The goal is exhaustive
  enumeration with a binary bar.
- **Skipping the gap-fill.** The gap-fill adds 28% of the final list
  (observed in immunology pilot). It is NOT optional.
- **ClinicalTrials.gov drug name extraction is messy.** Many entries are
  dose variants, biosimilars, or non-antibody concomitant drugs. A large
  exclusion list is needed.
- **Abstract-level profiles have factual errors.** Always use
  key-paper-ingestion level. The pilot caught 3 errors in 20 profiles.
- **Paywall impact.** ~60-70% of papers are abstract-only (NEJM, Lancet,
  Elsevier, Wiley). PMC OA journals provide full text. This is expected
  and acceptable.
- **Tier calibration is approximate.** The abstract-level tiering
  (approved/clinical-trial/failed-clinical/preclinical) is a first pass.
  Deep profiles reveal the actual development stage — some "preclinical"
  targets have clinical proof of concept, some "clinical-trial" targets
  have Phase 3 failures.
- **The graveyard pattern.** Failed-clinical targets are the highest-value
  profiles. The failure is usually antibody-specific (epitope, format,
  dosing), not target-specific. The failure analysis (field 6) is the
  most informative part of the profile.
- **Forgetting to commit after each batch.** The auto-snapshotter can
  commit subagent-written pages under a generic message. Commit each
  batch yourself with a descriptive message.

## Environment

- PubMed E-utilities REST API via urllib (Entrez Direct CLI NOT installed)
- Rate limiting is aggressive: 4-5s between individual calls, 20-25s between
  batches; 429s can hit on the first call of a session — wait 20-25s after
  any 429, not 15s (see Key data sources above for full guidance)
- Triage with esummary before efetch to conserve rate-limited calls
- ClinicalTrials.gov API v2 (no authentication)
- `paper-ingest` skill scripts at `skills/atticus/paper-ingest/scripts/`
- `ulimit -n 4096` before parallel subagent dispatch
- Known publisher blocks: Elsevier, Wiley (paywalled; use PMC OA, EPMC PDF,
  jina, or Wayback as fallbacks)
- All output must be in English

## Relationship to the molecule-side registry

The hit-list is the **target-side** corpus. Its molecule-side complement is
`references/therapeutic-antibodies/` (managed by the
`therapeutic-antibody-registry` skill) — one record per drug product (INN),
across all modalities and stages. The two corpora cross-reference: each
molecule entry carries a `target_hitlist` pointer to the corresponding
profile here; each profile's "Antibody landscape" field lists molecules that
the registry is the authoritative source for.

Hit-list profile slugs use **common-name slugs** (`pd-1.md`, `her2.md`,
`tnf.md`), not gene symbols. The molecule-side registry resolves slugs
against the actual `profiles/` directory — it does not assume gene-symbol
filenames. See the `therapeutic-antibody-registry` skill's "Cross-referencing
to the hit-list" section for the resolution pattern.

## Anti-patterns

- **Profiling every target in the hit list.** Exclude thin preclinical
  targets. Profile approved, clinical-trial, failed-clinical, and selected
  preclinical only.
- **Building profiles before the hit list is complete.** The hit list must
  be done first — you need the target list to know what to profile.
- **Using abstract-level synthesis for profiles.** The pilot showed
  factual errors. Always ingest key papers.
- **Forcing profiles into brain pages.** Profiles start as working docs.
  Promote high-value ones to concept pages later.
- **Re-profiling already-profiled targets.** Check
  `working-docs/hitlist-profiles/` for existing profiles before starting.
