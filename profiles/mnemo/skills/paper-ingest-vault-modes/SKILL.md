---
name: paper-ingest-vault-modes
description: "Use when ingest briefs name other vaults or errata reassign."
triggers:
  - a paper-ingest task brief names a vault path other than the main brain
    (satellite vault / ledgerless vault ingest)
  - an erratum (PubMed CommentsCorrectionsList, RefType=ErratumIn) reassigns
    data between named entities inside the paper being ingested
eval_contract:
  goal: |
    Run a paper-ingest variant correctly when the target vault is a satellite
    (no `people/_ledger.yaml`) or when an erratum re-attributes results inside
    the paper. Excellent output: the paper page lands in the vault the brief
    named, author alignment uses the person-page title scan where the ledger
    is absent, erratum-corrected attributions replace the printed ones, and
    nothing is silently "fixed".
  dimensions:
    - "TOPOLOGY_DISCIPLINE — did the run confirm which vault it is writing into (ledger presence + recent commits) instead of defaulting to the main brain?"
    - "LEDGERLESS_AUTHOR_ALIGNMENT — when the vault has no ledger, was the person-page title-scan substitute used with normalized matching and the cross-vault surname-conflation guard?"
    - "ERRATUM_FIDELITY — are re-attributed results carried in Findings with the erratum PMID recorded, and the correction flagged in Limitations/Analysis?"
    - "INTERNAL_CONSISTENCY — were fulltext self-disagreements recorded, not silently resolved or averaged?"
    - "SCOPE_LIMITS — does the run stay inside the base paper-ingest pipeline plus these two variants, leaving commit ownership with the parent?"
  hard_fails:
    - "Writing into the main brain when the brief named a satellite vault (or vice versa)."
    - "Reusing a same-surname person-page slug without reading that page's affiliation and body."
    - "Silently picking one of two conflicting in-paper numbers, averaging them, or 'correcting' the paper."
    - "Presenting secondary-source gene calls as the paper's own claim."
---

# paper-ingest-vault-modes — ingest topology and erratum handling

Two refinements to the `paper-ingest` pipeline that the base skill does
not yet carry. Load the base `paper-ingest` skill first for the main
pipeline; this sibling adds variant behavior for two situations.

## Trigger

- A paper-ingest task brief (usually from `literature-dive` or
  `ingest-pending-papers`) names a vault path other than the main brain
  (e.g. `<satellite-vault>` where the main brain is `<main-brain>`).
- A PubMed `CommentsCorrectionsList` entry with `RefType="ErratumIn"`
  resolves to a correction that reassigns data between named entities
  *inside* the paper.

## Topology: which brain am I writing into?

Two repos can sit side by side with near-identical layouts:

- **Main brain** — `papers/`, `people/` *with* `_ledger.yaml`, full graph
  machinery, the default target of every phase.
- **Satellite vault** — own git remote, own `papers/` and `people/`
  (person pages only, **no `_ledger.yaml`** by declared design). Fresh sources
  remain primary-owned; eligible queued page-only fills leave person-page
  creation to their parent.

A bare `ls` will not distinguish them. Check for `people/_ledger.yaml` and
read the recent commits — dive briefs name the vault explicitly, and the
task’s path always outranks the default brain. Confirm that ledger absence
is intentional from the task/vault contract; a missing ledger alone does not
establish a satellite topology or authorize skipping a damaged main ledger.

### What changes in the ledger-less vault

| Phase | Change |
|---|---|
| 2 (dedup) | Unchanged — run `dedup_check.py` from inside the vault; it scans that vault's `papers/`. |
| 4 (full text) | Unchanged. |
| 7 (bibliography walk) | Parent-owned in page-only mode; primary-owned for a full direct ingest. |
| 8 (author ledger) | `check_authors.py` crashes (`FileNotFoundError` on `--ledger`). Substitute the person-page title scan (below). |
| 10 (verify) | For explicitly declared ledgerless topology, use `--ledgerless --require-filled`; add `--page-only` for an eligible queued intermediate. Ledger absence is then labeled not applicable, not FAIL. Other failures remain failures. |

### Person-page title scan (check_authors substitute)

Vault person pages carry the display name in frontmatter `title:` (quoted),
not `name:` — a `^name:` grep matches nothing and every author looks NEW.
Normalize before comparing (punctuation alone turned an exact match into a
PARTIAL):

```python
def norm(s):
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r'[^a-z0-9 ]', ' ', s.lower())
    return re.sub(r'\s+', ' ', s).strip()
```

Match rules: normalized equality → EXISTING (use that slug verbatim, even
where it drops middle initials `slugify_name.py` would add — observed
`haynes-barton` and `saunders-kevin`); surname + given-name token overlap →
conflation-review candidate; otherwise NEW. Record ORCIDs (PubMed XML +
EPMC core record union) in saved source metadata, with an Ingest-log pointer.
The parent uses the source values, not a captured-count summary, to wire
person pages. Page-only results retain needs-ingest:true until parent
completion. Full verification without --page-only requires every author
reference to resolve to a person page; --ledgerless refuses an existing ledger
so it cannot be used to hide malformed data. Git ownership follows the base skill.

**Cross-vault surname conflation guard.** A glob of `people/*<surname>*`
can return a different person. For example, Neil P. King (protein design)
and Christopher L. King (malaria research) share a surname but are not the
same author. When a surname
matches, read the candidate page's frontmatter `affiliation:`/`title:` and
body BEFORE reusing its slug. An institution/domain mismatch requires
identity investigation, not an automatic split; after confirming distinct
people, mint a disambiguated new slug and note the pair in the Ingest log. Surname-only
hits in a multi-domain vault are the norm, not the exception — never wire
an author to a same-surname page without the affiliation check.

## Erratum re-attribution

When an erratum reassigns data between named entities inside the paper
(observed 2026-09-04, Kisalu 2018 Nat Med: every "CIS34" result was
actually CIS04 due to a labeling error — Author Correction PMID 30552419):

1. Resolve the erratum PMID and read what it corrects.
2. **Re-attribute each affected result in Findings** — the published body
   text is stale relative to the correction, so a faithful distillation
   must carry the corrected attribution, not the printed one.
3. Flag the correction prominently in Limitations (and in Analysis if it
   changes the paper's comparative claims).
4. Record the erratum PMID in the Ingest log.

## Fulltext-internal consistency (paper vs itself)

The brief-vs-fulltext check (base skill Phase 5) has a mirror the dive
also needs: **the paper disagreeing with itself.** The same quantity
restated across Abstract / Results / Discussion can drift — rounding, a
replicate restated as the headline, or a stale number carried into the
Discussion (observed 2026-09-04, Winnicki 2024 Nat Commun: humAb 826827's
transgenic blood-stage IC50 is 2.6 µg/mL in Results and 3.0 µg/mL in the
Discussion; the abstract's sporozoite range 0.3–3.7 µg/mL summarizes two
different hepatocyte assays whose replicate values elsewhere span
<0.07–1.8 µg/mL).

For each headline number destined for Findings, grep the full text for
every occurrence of that quantity and read each hit. When sections
disagree:

1. Report the value from the section that ran the experiment (Results),
   with the divergent restatement noted inline.
2. Add an "internal-consistency notes recorded, not corrected" line to
   the Ingest log carrying both numbers — the parent decides whether it
   matters.
3. Never silently pick one, average them, or "correct" the paper.

## Structural-statistics verification via RCSB

Crystallographic statistics tables sit in supplementary files the PMC
XML body does not carry — the body quotes only prose numbers. Before
writing resolution/method/deposition into Findings, verify against the
RCSB REST API:

```
curl -s "https://data.rcsb.org/rest/v1/core/entry/<PDB_ID>"
# struct.title, rcsb_entry_info.resolution_combined,
# rcsb_entry_info.experimental_method
```

Public-paper examples include Beutler 2022 (7RXP) and Winnicki 2024
(9DX6). Compare the returned resolution, method, and complex title against
the paper and its supplementary tables; the title check helps distinguish
structures when a paper cites several PDB entries.

## Pitfalls

- **`check_authors.py` --ledger is mandatory in the main brain** but a
  crash in a vault without `_ledger.yaml` means "use the title scan,"
  not "skip the alignment."
- **Do not infer person-page names from filename slugs** — read the
  frontmatter `title:` field; the two can differ in initial placement.
- **Supplementary PDFs behind the PMC bot-wall**: NCBI `/bin/` supplement
  URLs return an HTML bot-wall, jina returns 404, EPMC
  `supplementaryFiles` returns empty. When Supplementary Table 1 holds the
  antibody genetics and is unreachable, source the gene calls from citing
  literature (EPMC full-text search on the entity name + gene symbol) and
  flag them as secondary-source in Findings — never silently present
  secondary-source genetics as the paper's own claim.
- **`lint-frontmatter.py` path differs per vault** (observed 2026-09-04,
  Thai ingest in a satellite vault): the `<vault>/.github/scripts/` copy
  the base skill mentions may not exist in a satellite vault — fall back
  to the platform checkout (`core/tools/lint-frontmatter.py` in the
  scuderia repo) with `--instance <vault> --paths papers/<slug>.md`. Expected scoped-lint
  result for "paper page only" scope: exit 0 with orphan-link WARNINGS
  for every author `people/<slug>` the parent will create — warnings are
  not errors; only a nonzero exit blocks.
- **Deposited-name typos propagate through the chain** (observed
  2026-09-04: PubMed AND the publisher PMC deposit both list
  "de Bruijni MHC" — a stray 'i'). When a surname looks like a typo of a
  common Dutch/Scandinavian form, keep the deposited spelling in the
  page's `authors:` slug and Citation (it is the citable record), note the
  likely real spelling in the Ingest log, and let the parent decide at
  person-page wiring time.
- **Cross-checking the ingesting paper against its sibling vault pages
  surfaces phantom citations.** While ingesting Thai 2023
  (PMC10720262), the vault's kisalu-2018 page was found citing
  "Plymler et al. 2023 (PMC10720262)" — that PMCID belongs to the paper
  being ingested, and no Plymler author exists in PubMed at all. When a
  task names a vault page as context, grep it for citations to the
  current paper's identifiers; a mismatch (another paper's name attached
  to this PMCID/DOI) is an `entity-resolution`/`citation-fixer` flag for
  the parent — record it in the new page's Ingest log.

## See also

- `references/brief-vs-fulltext-verification.md` — case studies of task
  briefs whose framing (venue, terminology, "key findings") diverged
  from the paper's actual full text, and the verification moves that
  caught them.
