---
name: target-prioritization
description: "Rank viruses for mAb discovery. Use when picking targets."
triggers:
  - "rank viruses for mAb discovery"
  - "prioritize targets for antibody discovery"
  - "comprehensive virus target ranking"
  - "which viruses should we target"
  - "target prioritization"
---

# target-prioritization — rank virus targets for mAb discovery grants

A multi-phase campaign to identify the highest-priority human viruses for a
long-term antibody discovery program. Each target requires virus-specific
preliminary data (pilot-scale mAb discovery campaigns) before grant submission,
so stringent prioritization is essential given the resource investment per
target.

The output is a living reference document at
`docs/surveys/<topic>-priority-ranking.md` — a `docs/surveys/`
artifact, not a brain page-kind entity. It participates in the graph via
wikilinks but has no frontmatter edges, no importance score, and is not a
graph node. Individual viruses that graduate to active grant targets get their
own `project` pages, which do participate in the graph.

> **Conventions:** `conventions/brain-first.md` (check the brain for existing
> knowledge before going external), `conventions/quality.md` (cite or flag
> every substantive claim), `conventions/test-before-bulk.md` (pilot before
> scaling).

## Capabilities

`brain-search`, `brain-read`, `fetch-url` (PubMed E-utilities, CrossRef),
`spawn-subagent` (parallel family scoring), `terminal` (ICTV MSL download +
parsing).

## The scoring rubric

### Critical criteria (gates)

| # | Criterion | Rationale |
|---|----------|-----------|
| 1 | Human disease, especially US | Virus causes disease in US citizens; not necessarily high mortality |
| 2 | US seroprevalence | High enough to procure donor samples without extensive screening |
| 3 | Few/no known human mAbs + no active programs | Published-mAb count is the floor; active NIH-funded programs are the ceiling |
| 4a | Structure of surface antigen exists | Without a structure, solving one becomes a preliminary-data project |
| 4b | Target soluble without major engineering | No metastable trimer stabilization, no heroic protein engineering |
| 5 | BSL level / assay feasibility | BSL-2 screenable in-house; BSL-3+ needs collaboration or pseudovirus |
| 6 | Serotype diversity (bimodal) | Low (1-3): straightforward. Moderate (4-15): bnAb bonus. High (16-50): scope expands. Extreme (50+): impractical for initial project |
| 7 | Animal model availability | Every grant needs protection data; no model = a gap to fill |

### Moderate criteria (tiebreakers)

| # | Criterion | Rationale |
|---|----------|-----------|
| 8 | Active competition | No active programs = green; saturated = red |
| 9 | Funding landscape alignment | NIAID priority pathogen list, CEPI/BARDA targets |
| 10 | Antigenic stability | High drift undermines antibody-based strategies |
| 11 | Unmet medical need / existing countermeasures | Licensed vaccine or mAb weakens significance argument |

### Hold-back (deep-dive only)

| # | Criterion | Rationale |
|---|----------|-----------|
| 12 | Memory B cell frequency | Needs flow/ELISpot data that may not exist for most viruses |

### Tier system

| Tier | Definition |
|------|-----------|
| **Tier 1** (grant-ready) | BSL-2, single/moderate serotypes, structure exists, target soluble, high US seroprev, few/no human mAbs, no active programs, animal model exists |
| **Tier 2** (feasible with additional pre-data) | Missing 1-2 critical criteria; path to close is clear |
| **Tier 3** (major investment required) | Missing 3+ critical criteria, or any single criterion is a multi-year project to close |
| **Tier 4** (deprioritize) | Fails on seroprevalence or no identifiable neutralization target |

Scoring scale: **G** (green/clear) / **Y** (yellow/partial) / **R** (red/fails) / **U** (unknown/needs deep-dive)

## Phases

### 1. Build the universe

Compile a comprehensive list of all human-infecting viruses from domain
knowledge, organized by Baltimore class, family, and virus entries. Each entry
captures intrinsic virology properties: family, Baltimore class, genome type,
envelope status, BSL, serotype/genotype count, key disease.

Write the initial table to `docs/surveys/<topic>-priority-ranking.md`
with the methodology, criteria definitions, and tier system documented at the
top. The scoring columns are empty at this stage.

**Verify against authoritative sources before proceeding:**
- ICTV Master Species List (MSL41 or current) — download the xlsx from
  `https://ictv.global/msl/current`, parse with openpyxl, cross-reference all
  family names and species for taxonomy corrections
- NIAID Emerging Infectious Disease Research Areas of Interest list —
  navigate to `https://www.niaid.nih.gov/research/emerging-infectious-diseases-pathogens`,
  extract all virus entries, verify each is present in the inventory

Record all corrections in a verification log section at the bottom of the
document. See `references/taxonomy-verification.md` for the ICTV MSL parsing
workflow and known taxonomy changes.

**NIAID list extraction technique:**
The NIAID emerging pathogens page renders virus names as link text inside
nested list items. The browser snapshot may not expose the full text. Use
`browser_console` with a DOM-walk expression to extract the complete virus
list:
```js
const headings = Array.from(document.querySelectorAll('h3'));
const virusHeading = headings.find(h => h.textContent.trim() === 'Viruses');
let items = [];
let elem = virusHeading.nextElementSibling;
while (elem && elem.tagName !== 'H3') {
    items.push(elem.textContent.trim());
    elem = elem.nextElementSibling;
}
items.join('\n');
```
This returns the full concatenated list. Parse it to confirm whether a target
virus is on the NIAID priority list (criterion 9). Note: some entries are
grouped — e.g., "Variola major (smallpox) and other related poxviruses
(including Monkeypox)" covers all orthopoxviruses.

### 2. Pilot scoring (2-3 families)

Pick 2-3 representative families spanning the range of mAb-field maturity:
- One well-characterized (e.g., Orthoherpesviridae)
- One mid-landscape (e.g., Caliciviridae)
- One underexplored (e.g., Astroviridae)

Score all viruses in these families against the 11 criteria to validate the
rubric. Use subagents (one per family) to keep the orchestrator context clean.

**PubMed mAb landscape query strategy (criterion 3):**
Run TWO queries per virus via PubMed esearch (`execute_code` with urllib):
  1. Total mAb: `"virus name" AND "monoclonal antibody"`
  2. Human mAb: `"virus name" AND "human monoclonal antibody"`
The distinction matters: vaccinia has 207 total mAb but only 8 human — most are
mouse mAbs from smallpox surrogate work. Criterion 3 scores on the HUMAN mAb
landscape, not total. A virus with 200 total but 0 human mAbs is an open field.

**PubMed E-utilities rate-limiting pitfall:**
Batch esearch calls hit HTTP 429 (Too Many Requests) rapidly — within 4–5
queries at 0.5s spacing. Use `time.sleep(3.5–5)` between calls, add a
`User-Agent` header, and implement retry-with-backoff (10s on 429, 3 attempts).
Batch all queries in a single `execute_code` block rather than individual
browser navigations — the esearch JSON API is faster and lighter than the
browser stack. See `references/pubmed-query-patterns.md` for a reusable query
script template.

**Subagent delegation protocol (full scoring pass):**
- One subagent per family, dispatched via `delegate_task` in a batch
- Pass the virus list, the rubric, and any pre-existing brain knowledge as
  context
- The subagent searches PubMed for `[virus name] human monoclonal antibody`
  to assess criterion 3 (mAb landscape) and checks for active programs
- Return format: a markdown table with G/Y/R/U scores per criterion, per-virus
  tier assignments with justifications, and family-level observations
- **NIH RePORTER API pitfall:** the v2 API at
  `api.reporter.nih.gov/v2/projects/search` returns all 2.9M projects
  regardless of query criteria. Use the browser-based search at
  `reporter.nih.gov` instead, or skip RePORTER and rely on PubMed counts
  plus the NIAID priority pathogen list.
- **Subagent failure handling:** subagents may return empty content,
  especially under load. Retry with pre-fetched PubMed data from the failed
  attempt fed directly into the context so the retry does not re-search.

**Inline scoring (small batches):**
For focused requests (≤4 families, ≤20 viruses), scoring inline is more
efficient than subagent delegation. Use `execute_code` to batch all PubMed
esearch queries in one block (with rate-limit delays), then score from domain
knowledge + the returned counts. This avoids subagent overhead and keeps the
full scoring context visible for the user to review. Reserve subagent
delegation for the full 40+ family scoring pass.

**Rubric validation check:** After the pilot, verify the tier system
correctly separates known targets. Classic HAstV should score Tier 1 (proof
of concept). CMV/VZV should score Tier 3 (saturated mAb fields). If the rubric
does not produce this separation, adjust thresholds before scaling.

### 3. Full scoring pass

Scale to all remaining families, parallelized across subagents. Batch
families to stay within the concurrent delegation pool (3 by default).
Collect results and merge into the ranking document.

### 4. Calibration and ranking

Review preliminary scores. Identify top candidates, sanity-check against known
mAb landscapes. Flag viruses where criterion 3 needs deeper verification.

### 5. Deep-dive on top 10-20

Thorough literature investigation: verify seroprevalence with primary sources,
confirm mAb landscape exhaustively, assess target solubility from structural
data, evaluate memory B cell frequency where data exists. Create brain pages
for key literature on top candidates.

### 6. Grant-fit assessment

Cross-reference against USER.md, FUNDING-PROFILE.md, and reviewer critique
lessons. Top candidates get `project` pages in the brain.

## Where the artifact lives

`docs/surveys/<topic>-priority-ranking.md` — a living reference
document in the `docs/surveys/` directory. Not a brain page-kind entity. It
participates in the graph via wikilinks but has no frontmatter edges. The
rationale: a ranked virus list is a survey artifact, not a thing in the world
being modeled. Individual viruses graduate to `project` pages when they
become active grant targets.

## Anti-patterns

- **Building the universe from Wikipedia.** Wikipedia has no comprehensive
  human virus list. Build from domain knowledge, verify against ICTV MSL +
  NIAID list.
- **Trusting the NIH RePORTER API for project counts.** The v2 API does not
  filter by text query. Use the browser interface or skip it.
- **Scoring all families inline.** PubMed searches are context-heavy. Use
  subagents for the full 40+ family scoring pass. For small batches (≤4
  families, ≤20 viruses), inline scoring with `execute_code`-batched PubMed
  queries is more efficient.
- **Skipping the pilot.** The pilot validates the rubric before full-scale
  scoring.
- **Forcing the ranking into a brain page kind.** The survey document is the
  right home. Viruses graduate to `project` pages when they become active
  targets.
- **Adding serotype diversity as a linear penalty.** It is bimodal: low is
  straightforward, moderate (4-15) creates a bnAb narrative, extreme (50+)
  is impractical for an initial project.
- **Querying only total mAb counts.** A virus can have hundreds of mouse mAb
  publications but zero human mAbs. Always run both total and human-specific
  PubMed queries. Criterion 3 scores on the human mAb landscape.
- **Rate-limiting PubMed E-utilities.** HTTP 429 hits within 4–5 queries at
  0.5s spacing. Use 3.5–5s delays, a User-Agent header, and retry-with-backoff.
- **Extracting the NIAID list from the browser snapshot.** The accessibility
  tree may not expose the full virus list text. Use `browser_console` with a
  DOM-walk expression to extract the concatenated text from the Viruses
  heading section.
