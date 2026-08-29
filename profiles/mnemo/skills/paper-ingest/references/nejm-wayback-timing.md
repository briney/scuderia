# NEJM Wayback Snapshot Timing vs Paywall Window

## The key variable

NEJM full-text availability in Wayback snapshots depends on **whether the snapshot was captured after the 6-month embargo window**, not just the publication year.

- NEJM articles are paywalled for approximately 6 months after publication, then become freely available on nejm.org.
- Wayback snapshots captured during the paywall window (first ~6 months) archive the paywall preview page — abstract + author block + reg wall, ~107–109 KB HTML, ~13K chars of extractable text from `<article>` tag, zero body sections.
- Snapshots captured after the embargo window archive the free full-text page — 189–544 KB HTML, 38–50K chars of body text from `<article>` tag.

## Observed cases

| PMID | Year | Snapshot date | Post-embargo? | Result |
|------|------|---------------|---------------|--------|
| 33720637 (Mintun 2021) | 2021 | Mar 2021 (pub month) | No | Abstract-only (13,379 chars) |
| 27690741 (Simpson 2016 SOLO) | 2016 | ~2019 | Yes | Full text (~50K chars) |
| 29782217 (Castro 2018 QUEST) | 2018 | ~2020 | Yes | Full text (~50K chars) |
| 26422722 (Lebwohl 2015 AMAGINE-2/3) | 2015 | 2015–2016 | Mixed | Abstract-only (~2.3K chars, old page template) |
| 39282907 (Groarke 2024) | 2024 | 2024–2025 | No (too recent) | Abstract-only (11–12K chars) |

## Implication for retrieval

When CDX returns multiple 200-status snapshots for an NEJM paper:
1. Check the snapshot **timestamps** — prefer snapshots ≥6 months after the publication (Epub) date.
2. The `largest length` heuristic still helps — but only among post-embargo snapshots. Pre-embargo snapshots are all ~107–109 KB regardless of content.
3. For papers published within the last 6 months: don't expect full text from any Wayback snapshot. Try the S2 `openAccessPdf` institutional-repository path first; if blocked, go straight to abstract-only with `needs-enrichment: true`.
4. For papers published 6–24 months ago: try the latest snapshots first (most likely to be post-embargo); older snapshots may be pre-embargo.

## Fallback

When no post-embargo snapshot exists: three-source closure (EPMC all-N + S2 CLOSED/BRONZE + Unpaywall bronze), tag `fulltext_source: abstract`, `needs-enrichment: true`. The structured PubMed/NEJM abstract for clinical trials is usually rich enough for a meaningful distillation (all endpoints, population, safety headline).
