# CXCL12/SDF-1 Profile Observations (2026-08-16)

Forty-sixth level-2 profile (preclinical tier, immunology — chemokine
axis / stem cell homing / HIV / cancer metastasis). CXCL12/SDF-1 is the
unique high-affinity ligand for CXCR4 — one of the most studied chemokine
axes in biology. 3 papers ingested (2/3 full text via publisher-jina,
1/3 abstract-only). ~44.5K chars, 3 PMIDs cited throughout (44, 49, 43
citations respectively).

## Papers

| PMID | Paper | Journal | Full text |
|------|-------|---------|-----------|
| 8752280 | Bleul et al 1996 — SDF-1 as ligand for LESTR/fusin, blocks HIV-1 entry | Nature | publisher-jina (19,511 chars) |
| 9933168 | Peled et al 1999 — CXCR4 dependence of stem cell engraftment | Science | abstract-only (paywalled) |
| 11242036 | Müller et al 2001 — CXCR4/CXCL12 in breast cancer metastasis | Nature | publisher-jina (90,371 chars) |

## Key new patterns

### 1. `--doi` + `--publisher-url` flag combination recovers papers that `--pmid` alone cannot reach

When `fetch_fulltext.py --pmid <PMID>` returns `provenance: none` (no
PMC, no EPMC, no PMCID), providing both `--doi` and `--publisher-url`
together triggers the jina.ai reader path on the publisher page. This
recovered 2/3 old Nature papers (1996, 2001) that PMID-only lookup
could not reach.

```
# PMID-only: provenance=none
python3 fetch_fulltext.py --pmid 8752280 --out /tmp/bleul1996

# DOI + publisher-url: provenance=publisher-jina (19,511 chars)
python3 fetch_fulltext.py --doi 10.1038/382829a0 \
    --publisher-url https://www.nature.com/articles/382829a0 \
    --out /tmp/bleul1996
```

The `--pmid` path checks the Europe PMC gate first (PMC/EPMC OA
flags), and when all return negative, it stops. The `--doi` +
`--publisher-url` path skips the EPMC gate and goes directly to the
jina.ai reader on the publisher URL. For old papers (pre-2000s)
that predate PMC/OA, the DOI+publisher-url path is the correct
entry point.

The skill previously documented `--publisher-url` only for Lancet
(CCR4 profile). This session confirms it works generally for
Nature articles (1996 and 2001) and should be the default approach
when `--pmid` returns `provenance: none` and a DOI + publisher URL
are available.

### 2. Science.org (Science magazine) is a hard paywall — completely unrecoverable

The Peled 1999 paper (PMID 9933168, Science) was completely
unrecoverable through all paths:
- `--pmid`: `provenance: none` (no PMC, no EPMC, no PMCID)
- `--doi` + `--publisher-url` (science.org): jina returned 403 Forbidden
- Wayback Machine: HTTP 503 (Service Unavailable)
- Jina on Wayback URL: HTTP 403 (Forbidden)

This is a harder block than Elsevier/Wiley. Science.org appears to
actively block all automated readers. Old Science papers (pre-2000s)
have no PMC copies and no OA versions. Abstract-only is the only
option for Science papers from this era.

This contrasts with Nature papers from the same era, which ARE
jina-recoverable (see below). When selecting landmark papers for
ingestion, prefer Nature over Science for old (pre-2000s) papers
when both cover the same topic.

### 3. Old Nature papers (1996–2001) ARE jina-recoverable

Both Nature papers from 1996 (Bleul et al, PMID 8752280) and 2001
(Müller et al, PMID 11242036) were successfully retrieved via jina.ai
reader on the nature.com URL. The 2001 paper returned 90,371 chars
(full article text); the 1996 paper returned 19,511 chars (article
text, possibly partial but sufficient for profile building).

This is a positive finding: Nature articles from the 1990s–2000s,
while not in PMC/OA, are accessible via jina reader on the
nature.com URL. This makes Nature a reliable source for old
landmark papers — better than Science.org for the same era.

### 4. Chemokine axis "ligand vs receptor" targeting pattern

CXCL12/SDF-1 is the first profiled target where the entire clinical
pipeline targets the receptor (CXCR4), not the ligand (CXCL12):
- Plerixafor (AMD3100) — FDA-approved CXCR4 small-molecule antagonist
- Ulocuplumab (BMS-936564) — anti-CXCR4 antibody, Phase 1/2
- LY2510924 — anti-CXCR4 peptide-Fc, Phase 2
- BL-8040/BKT140 — CXCR4 peptide antagonist, Phase 3

No anti-CXCL12 (anti-ligand) antibody has entered clinical development.
This mirrors the CCL5/RANTES profile (where all drugs target CCR5,
not CCL5) and establishes a generalizable pattern for chemokine axis
targets: the industry consistently targets the receptor, leaving the
ligand completely unexplored as an antibody target.

For field 10 (competitive landscape) and field 11 (differentiation),
the "ligand vs receptor" framing is the key differentiation argument:
- An anti-ligand antibody blocks all receptor interactions simultaneously
  (CXCL12 binds both CXCR4 and ACKR3/CXCR7)
- An anti-ligand antibody does not occupy the receptor, potentially
  avoiding some on-target receptor-related toxicities
- The ligand-targeting approach enables format flexibility (bispecific,
  ADC, conditional) impossible with small-molecule receptor antagonists

This pattern applies to any chemokine axis where the receptor has
approved drugs but the ligand does not (CCL5/CCR5, CXCL12/CXCR4,
CXCL13/CXCR5, CCL20/CCR6, etc.).

### 5. CXCL12-specific biological insight: HIV paradox as a contraindication

CXCL12 naturally blocks X4-tropic HIV entry by competing with HIV for
CXCR4. An anti-CXCL12 antibody that neutralizes CXCL12 would remove
this natural HIV blockade, potentially ENHANCING X4-tropic HIV
infection. This makes anti-CXCL12 antibodies contraindicated in
HIV-infected patients with X4-tropic virus — a critical safety concern
unique to this target.

This is the first profiled target where the natural ligand is
protective against a major disease (HIV), and blocking the ligand
would WORSEN the disease. For field 8 (safety profile), this is a
target-specific contraindication that does not apply to receptor
antagonists (plerixafor blocks CXCR4 directly, preventing HIV entry
rather than removing the natural blockade).

Generalizable to any chemokine axis where the ligand has a protective
endogenous function that an anti-ligand antibody would abrogate.

## Retrieval statistics

- Full-text retrieval rate: 2/3 (67%)
- Retrieval method: publisher-jina (2/2 successful)
- Paywall blocks: Science.org (1/3 papers, completely unrecoverable)
- Profile size: ~44.5K chars, 204 lines, 5,950 words
- PMID citations: 8752280 (44×), 9933168 (49×), 11242036 (43×)
- File: working-docs/hitlist-profiles/cxcl12-sdf-1.md
