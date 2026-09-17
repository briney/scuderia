# Tier A table-to-entry recipe

Load for Tier A table generation or area assignment. Use the corpus contract
and relevant templates named in the umbrella; load `source-extraction.md` only
when acquiring/parsing inputs. Start a new bulk run with a representative
pilot; do not treat a historical roster as current source data.

## Map the captured inputs

1. Identify the actual source capture, URL, retrieval date, header labels,
   and parsed rows. The extraction reference returns separate `headers` and
   `rows`; do not discard the first data row. For other capture shapes,
   inspect whether a header is embedded. Measure rows, duplicates, existing
   records, unresolved candidates, and resulting products separately.
2. Preserve raw INNs, then collapse display whitespace (including embedded
   newlines) for matching. Resolve source names and existing slugs against
   the drug-product identity rules. Add verified missing products; update
   existing entries only within authorized curated fields. Preserve their
   enrichment blocks and unrelated curated edits.
3. Map target/format from the observed source column. A semicolon can delimit
   target from format but also occur within multi-target values; inspect the
   row rather than blindly discarding later segments. Map explicit ADC,
   multispecific, fragment, immunotoxin, or radioisotope descriptions to the
   template vocabulary. Do not default an unrecognized format to naked IgG.
   Record origin only when stated; distinguish humanized from human rather
   than matching the substring `human` in both.
4. Interpret regional approval/review columns with the source legend. Retain
   current approvals, filings, withdrawals, and reapprovals with their regions
   and dates. A current approval in one region is not erased by another
   region's withdrawal. Filed products belong to Tier A. A fully withdrawn
   product is evaluated under the corpus's Tier C definition, with its failure
   history retained; source-table membership alone does not assign Tier A.
5. Populate only supported fields and cite the source row. The table does not
   establish developer, regulatory IDs, biosimilars, ADC payload/linker/DAR,
   CAR construct details, or a mechanistic account. Use `Unknown` / `No data`
   until regulatory/official sources or the appropriate cited literature
   supply those details. Apply the relevant modality/failure appendices.

## Areas and indexes

Use the corpus's six area names and primary-first multi-tag convention.
Assign areas from source-backed indications, not the target alone. Keyword
matching can propose tags but needs review against the indication; use word
boundaries (`\b`) for short terms so `sma` does not match `melanoma` and
`als` does not match `false`. Preserve all supported area memberships.
Do not default unresolved products to oncology. Leave unsupported assignment
explicitly unknown and report it for review rather than inventing an index row.

Regenerate each area list and the master index from the canonical entries,
including INN, brand, target, modality, status, and entry path. Compare index
membership against each entry's `Therapeutic area(s)` and verify target
hit-list pointers against real filenames. Distinguish unique products from
multi-area memberships when reporting counts.

## Products not covered by the table

Check regulatory records and official disclosures for Fc-fusions, CAR cell
products, radioimmunoconjugates, regional approvals, and other omissions.
Verify each product's identity and fields; mark unsupported fields `Unknown`.
A historical candidate list is not source metadata or an exhaustive roster.
Keep that run's candidates, source evidence, gaps, and measured coverage in
the private corpus, not in this reusable recipe.
