# Paper-ingest helper commands

Load when invoking a helper. Resolve `<scripts>` to this skill's `scripts/`
directory and `<brain>` to the assigned vault; use Python >=3.10, with PyYAML
for YAML helpers and pymupdf for PDF extraction. These are existing programs,
not guarantees that every source/identity condition is checked automatically.

| Helper | Invocation / output contract |
|---|---|
| `fetch_fulltext.py` | `--out <prefix>` required; optional `--pmid`, `--doi`, `--pmcid`, `--publisher-url`, `--skip-publisher`, `--figures`. JSON gives `provenance`, `text_file`, `chars`, `figures_dir`, `notes`. Read `text_file`: `.txt` is appended even if the prefix already ends in `.txt`. Exit 0 includes `provenance: none`; validate the candidate body independently. |
| `dedup_check.py` | `--doi`, `--pmid`, `--title` (at least one), `--instance <brain>`, optional `--json`. Exit 0=no match; 1=matches with STUB/FULL state; 2=invocation error. Similar-title matches require review. |
| `validate_identifiers.py` | `--batch <json-file> --recover`; single input uses `--title`, `--author`, `--year`, optional `--pmid`, `--doi`, `--pmcid`. Batch entries use those same field names. Read validated/recovered/HOLD results and the `dispatch` list; surface retraction flags. |
| `slugify_name.py` | `--pubmed-xml <file>` for a batch; `--family`/`--given` for one author; `--filter-surname` with `--ledger-file` for token-match queries; `--crossref-family`/`--crossref-given` supply a name cross-check. Handles diacritics and documented compound-name misparses; confirmed existing identity takes precedence over a proposed slug. |
| `check_authors.py` | `--ledger <brain>/people/_ledger.yaml`, optional `--people-dir`, names as arguments or stdin. Prints EXISTING/NEW and surname candidates; always exits 0. It compares ledger name tokens, not person-page identities, and displays only eight near candidates. Phase 8's reference owns the additional identity checks. |
| `ledger-append.py` | Template, not a CLI updater. Copy to unique scratch FIRST, then set `LEDGER`, `PAPER`, and `NEW_BLOCKS` in that copy. Never edit the canonical helper for an ingest. New entries only; existing-entry updates and promotion follow `author-ledger-mutation.md`. |
| `pmc_xml_body_parser.py` | `<xml_file>`, optional `--range START END` or `--full`; default is only the first 15,000 characters. There is no `--refs`. Imports `fetch_fulltext.pmc_xml_to_text`; parse failure/no body prints a message, not a failing exit. No XML repair, reference-list or table-cell extraction; load `pmc-xml-tools` for those needs. |
| `verify_ingest.py` | `<bare-slug>` (with/without `.md`) `--instance <brain> --require-filled`; add `--page-only` for queued PAGE_READY validation. `--ledgerless` is only for an explicitly declared ledgerless satellite and refuses an existing ledger. `--offline` skips canonical network identity, not a workaround for a failed check. |
| `embargo_recheck.py` | Scheduled enrichment-candidate reporter, not a normal ingest step. It has no argument parser and derives `VAULT` from its resolved script path; `--help` is not a safe probe. Verify the actual wrapper/target before running, and do not treat silence as proof that the intended vault was checked. Do not copy a deployment's schedule/model/delivery into the procedure. |

The fetch helper implements EPMC→PMC XML→EPMC PDF→bioRxiv/Jina→publisher
Jina→Wayback, not paperclip, browser retrieval, or final closure. Its special
bioRxiv branch recognizes only `10.1101/`; it may default to v1 after version
lookup fails. Resolve the desired version separately. It can accept long
preview/reference-only pages; validate returned content, not its byte threshold.

Identifier validation uses title similarity, surname, and year checks. Older
titles, hyphenated surnames, and punctuation can yield false HOLDs; verify the
full identity against a primary record, using a PubMed summary batch when
applicable. Never repair malformed identifier strings merely to fit a format.
Confirm a bare-number PMCID candidate against the article record first.

The final verifier checks local graph/ledger structure and DOI/PMID identity;
arXiv resolution tries DataCite before other indexes. Its author-count match
is not proof of correct individual identities or every required author edge.
The primary still checks source evidence, bibliography, wiring, and propagation.

## Host and transport failures

Use named temporary files for downloaded payloads and scripts; do not depend
on truncated terminal stdout. URL-encode raw query parameters once; quote
shell arguments, especially DOI parentheses/brackets. JSON APIs need their
actual JSON responses, not Jina's text wrapper.

Respect tool protection. If a shell form fails due to syntax/tool limitations,
use a supported file-intermediary or script form; an authorization refusal is
not permission to repeat the operation through another tool. Never use heredocs
or whole-file YAML dumps for shared-ledger mutation.

Batch PubMed IDs and pace requests; the recorded workflow used 3–5 seconds
between sequential calls, with longer backoff after repeated 429s. Honor
Retry-After and stop repeated failures. Check real process FD limits before
large dispatches: macOS EMFILE was observed with a 256 soft limit. Raising a
terminal shell's limit does not retroactively change the agent process.

Historical arXiv API timeouts/host restrictions and Jina domain-level 403s
(2026-09-05) did not imply arXiv source closure: direct abs/HTML/PDF routes
remained alternatives. Inspect the current response; do not preserve a
permanent host-wide ban or assume a proxy's failure belongs to the source.
