# Mac-1 (αMβ2 / ITGAM-ITGB2) Profile — Detailed Observations

> Level-2 profile. Preclinical tier (ophthalmology).
> Target: Mac-1 (αMβ2, CD11b/CD18, CR3), genes ITGAM/ITGB2, UniProt P11215/P05107.
> Profile: `working-docs/hitlist-profiles/amb2-mac-1.md` (~70K chars, 32 PMIDs cited).
> Built via delegated subagent, lightweight retrieval pipeline (direct PubMed
> E-utilities + UniProt REST + PDB REST). Abstract-only ingestion.
> 3 PubMed search batches (Mac-1 antibody uveitis, CD11b microglia retina,
> alphaMbeta2 integrin complement), 11 new PMIDs found + 30 pre-existing
> paper JSON files from prior workspace runs (`_amb2_papers*.json`).

## Profile at a glance

- **Target type**: Cell surface heterodimeric integrin (αM 165 kDa + β2 95 kDa)
- **Family**: β2-integrin subfamily (shares CD18/β2 with LFA-1/αLβ2, αXβ2, αDβ2)
- **Primary function**: Complement receptor 3 (CR3) — iC3b receptor; leukocyte adhesion
- **Key antibody clones**: M1/70 (rat anti-mouse/human, cross-reactive), 5C6 (rat anti-mouse),
  hCD11bNb1 (nanobody, first αMβ2 headpiece crystal structure)
- **Ophthalmology evidence**: Anti-Mac-1 inhibits EIU (P<0.001, PMID 8095493);
  CR3 blockade impacts EAAU (PMID 16505038); CR3 ablation enhances optic nerve
  regeneration (PMID 38492223); microglial CD11b implicated in glaucoma, AMD,
  retinal ischemia
- **No clinical-stage anti-Mac-1 antibody**: Pipeline is empty despite extensive
  preclinical validation across uveitis, stroke, I/R injury, arthritis

## Key new patterns (3)

### 1. RCSB PDB search API v2 (`/rcsbsearch/v2/query`) consistently fails with HTTP 400

The RCSB search v2 endpoint (`https://search.rcsb.org/rcsbsearch/v2/query`)
returned HTTP 400 Bad Request across every query format attempted — multiple
attribute/operator combinations, text service queries, GraphQL, v1 API.
The error messages indicate JSON schema validation failures for the query
structure, but the "correct" schema is not documented in a way that any
attempted format satisfied.

**Reliable fallback**: Use `data.rcsb.org/rest/v1/core/entry/{PDB_ID}` to
look up known PDB IDs directly. This returns structure title, method, and
metadata in a single fast call. The PDB IDs themselves come from:
(a) UniProt cross-references (the UniProt `.txt` format lists PDB IDs in
DR lines), (b) literature (PMID abstracts mention PDB IDs), (c) known
structural biology papers.

For Mac-1, 7 PDB structures were identified and characterized by checking
literature-derived candidate IDs directly: 1IDO, 1JLM, 1NA5, 1M1U (αM
I-domain), 4NEH, 3K6S, 5ES4 (related αXβ2). The nanobody complex structure
from PMID 35738398 was referenced from the paper abstract, not from a PDB
search.

**Rule**: Do not rely on `rcsbsearch/v2/query` for PDB structure discovery
in the lightweight retrieval pipeline. Instead: (1) extract PDB IDs from
UniProt cross-references, (2) extract PDB IDs from landmark paper
abstracts, (3) verify each candidate via `data.rcsb.org/rest/v1/core/entry/
{PDB_ID}`. This is slower (one call per ID) but reliably succeeds.

**Generalizes to**: All target profiles requiring structural information
(field 9) via the lightweight subagent retrieval pipeline.

### 2. β2-integrin shared subunit: cross-reference sibling profiles for safety context

Mac-1 (αMβ2/CD11b/CD18) and LFA-1 (αLβ2/CD11a/CD18) share the β2 (CD18)
subunit. The LFA-1 profile (`alb2-lfa-1.md`) was consulted as a reference
during Mac-1 profiling. Key shared learnings:

- **PML risk class**: Efalizumab (anti-LFA-1/CD11a) was withdrawn for PML.
  While Mac-1-specific antibodies (anti-CD11b only) would NOT block LFA-1
  and thus may carry lower PML risk, anti-β2 (anti-CD18) antibodies would
  block ALL β2 integrins including LFA-1 — carrying the same PML liability.
  This distinction must be explicit in field 8 (safety) for any β2-integrin
  profile.

- **Shared β2 subunit antibodies are NOT family-specific**: Anti-β2
  antibodies (e.g., M18/2) cross-react with all β2 integrins. Only
  α-subunit-specific antibodies (anti-CD11b for Mac-1, anti-CD11a for
  LFA-1) are family-selective. This must be documented in field 5 (epitope
  landscape).

- **Compensatory pathways**: Blocking one β2 integrin may not fully
  prevent leukocyte recruitment if the other provides compensatory
  adhesion. In EAU, anti-LFA-1 was less effective than anti-ICAM-1
  (PMID 7909311, LFA-1 profile) — potentially because Mac-1 (also an
  ICAM-1 ligand) provides compensatory adhesion. Conversely, Mac-1
  blockade may be incomplete if LFA-1 compensates.

**Rule**: When profiling a β2-integrin family member, explicitly
cross-reference the sibling profiles. In field 8, state whether the
antibody target is the α subunit (family-specific) or β2 subunit
(pan-β2, broader toxicity). In field 6, note compensatory pathways
from sibling integrins.

**Generalizes to**: All β2-integrin targets (LFA-1/αLβ2, Mac-1/αMβ2,
αXβ2/p150,95, αDβ2), and any integrin family with a shared subunit
(β1 integrins sharing CD29, αv integrins sharing CD51).

### 3. Pre-existing workspace paper JSON files as persistence across sessions

The workspace (`working-docs/hitlist-profiles/`) contained
`_amb2_papers.json`, `_amb2_papers2.json`, `_amb2_papers3.json` — 30 paper
records (PMID, title, abstract, journal, year, authors) from prior
PubMed search runs for this same target. These were loaded and used
directly, saving ~15 minutes of PubMed search and abstract-fetching time.

**Rule**: Before running PubMed searches for a target, check the
workspace for `_<target-slug>_papers*.json` or similar pre-existing
paper-collection files. These files persist across sessions and
subagent runs, and may already contain the landmark paper abstracts
needed. Load them first, then supplement with new searches only for
gaps (e.g., specific ophthalmology queries, structural papers).

**Generalizes to**: All delegated profiling subagent runs — the
workspace is a stable directory that accumulates intermediate results
across sessions. Checking for pre-existing intermediate files before
re-running API calls is a standard efficiency pattern.

## PubMed search queries used (3 batches)

1. `Mac-1 antibody uveitis[tiab]` → 5 results (incl. PMID 8095493, 16505038)
2. `CD11b microglia retina[tiab]` → 0 results
3. `alphaMbeta2 integrin complement[tiab]` → 6 results

The 0-result query (`CD11b microglia retina[tiab]`) is consistent with
the skill's documented pattern that narrow `[tiab]` queries for preclinical
targets frequently return zero — the CD11b/microglia/retina literature
exists but doesn't use that exact phrase combination in titles/abstracts.
The 30 pre-existing paper JSON files compensated for the thin search yield.

## Retrieval statistics

- Pre-existing papers loaded: 30 (from 3 JSON files)
- New PubMed searches: 3 queries, 11 new PMIDs
- New abstracts fetched: 4 (PMID 16505038, 9561835, 12609490, 14500997)
- UniProt REST: 2 calls (P11215, P05107 — .txt format)
- PDB REST: ~30 candidate IDs checked, 5 confirmed (1IDO, 1JLM, 1NA5, 1M1U,
  plus 3 related αXβ2 structures)
- Full text retrieved: 0 (abstract-only ingestion)
- Unique PMIDs cited: 32
- Profile size: ~70K chars, 452 lines
