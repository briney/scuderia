# Antibodies to Watch — Annual Series PMIDs

The "Antibodies to Watch" series (mAbs journal, The Antibody Society) provides
an annual census of the commercial antibody pipeline: first approvals,
regulatory review, and late-stage clinical development. All papers are open
access in mAbs.

## How to extract tables

1. Get the PMC ID from PubMed (esummary `articleids` -> `pmc` field)
2. Pull fullTextXML from Europe PMC:
   `europepmc.org/webservices/rest/PMC<ID>/fullTextXML`
3. Parse `<table-wrap>` elements with regex -- each contains a `<label>`,
   column headers in `<th>`, and data in `<td>` elements
4. Tables typically have: INN, Target(s), Format, Indication, Phase/Country

## PMID list (newest first)

| Year | PMID | Notes |
|------|------|-------|
| 2026 | 41560619 | PMC12826703. 19 first approvals in 2025, 26 in review, 209 late-stage |
| 2025 | 39711140 | |
| 2024 | 38178784 | |
| 2023 | 36472472 | |
| 2022 | 35030985 | |
| 2021 | 33459118 | |
| 2020 | 31847708 | |
| 2019 | 30516432 | |
| 2018 | 29300693 | |
| 2017 | 27960628 | |
| 2016 | 26651519 | |
| 2015 | 25484055 | |

## YAbS Database Paper

PMID 40013403 (mAbs 2025) -- "YAbS: The Antibody Society's antibody therapeutics
database." Describes the database at db.antibodysociety.org (2,900+ candidates).
Open access to data for approved + regulatory review + late-stage (450+
molecules). Updated bimonthly. Supports filtering by target, therapeutic area,
company, format, and date.
