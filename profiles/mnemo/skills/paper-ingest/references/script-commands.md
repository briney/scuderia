# Paper-ingest helper commands

Runtime: `runtime.md`. Resolve `<scripts>` to this skill’s scripts directory.
Use the configured Python 3.11+ environment. Identity/retrieval helpers supply
candidates; verify sources and retain originals outside the brain.

| Helper | Invocation / output contract |
|---|---|
| `fetch_source.py` | `--url <public-HTTP(S)-URL> --evidence-dir <NEW-absolute-dir> --filename <safe-basename>`; parent directory must already exist outside the brain. One retrieval with normal redirects, no automatic retry or parsing. Reuses the fulltext helper’s raw request/response evidence. Exit 0 returns JSON with `file`, `bytes`, `sha256`, `status`, `source_url`, `final_url`, and `evidence_dir`; read the returned file. Exit 2 means failure and never supplies an accepted source. Preserves bytes under `derived/<filename>`; use the correct extension and verify actual content. No authentication or caller-supplied headers; existing directories are refused. |
| `fetch_fulltext.py` | `--out <prefix>` required; optional `--pmid`, `--doi`, `--pmcid`, `--publisher-url`, `--skip-publisher`. Production source retention adds `--evidence-dir <NEW-absolute-dir>` and requires `--out <that-dir>/derived/<prefix>`; every HTTP attempt/retry/redirect retains raw bytes or explicit missing/partial/error evidence. No headers/credentials are saved. Without it legacy behavior is unchanged. JSON gives `provenance`, `text_file`, `chars`, `figures_dir`, `notes`. Read `text_file`: `.txt` is appended even if the prefix already ends in `.txt`. Exit 0 includes `provenance: none`; validate the candidate body independently. |
| `dedup_check.py` | `--doi`, `--pmid`, `--title` (at least one), `--instance <brain>`, optional `--json`. Exit 0=no match; 1=matches with STUB/FULL state; 2=invocation error. Similar-title matches require review. |
| `validate_identifiers.py` | `--batch <json-file> --recover`; single input uses `--title`, `--author`, `--year`, optional `--pmid`, `--doi`, `--pmcid`. Batch entries use those same field names. Read validated/recovered/HOLD results and the `dispatch` list; surface retraction flags. |
| `slugify_name.py` | `--pubmed-xml <file>` for a batch; `--family`/`--given` for one author; `--filter-surname` with `--ledger-file` for token-match queries; `--crossref-family`/`--crossref-given` supply a name cross-check. Handles diacritics and documented compound-name misparses; confirmed existing identity takes precedence over a proposed slug. |
| `check_authors.py` | `--ledger <brain>/people/_ledger.yaml`, optional `--people-dir`, names as arguments or stdin. Prints EXISTING/NEW and surname candidates; always exits 0. It compares ledger name tokens, not person-page identities, and displays only eight near candidates. Phase 8's reference owns the additional identity checks. |
| `ledger-append.py` | Template, not a CLI updater. Copy to unique scratch FIRST, then set `LEDGER`, `PAPER`, and `NEW_BLOCKS` in that copy. Never edit the canonical helper for an ingest. New entries only; existing-entry updates and promotion follow `author-ledger-mutation.md`. |
| `pmc_xml_body_parser.py` | `<xml_file>`, optional `--range START END` or `--full`; default is only the first 15,000 characters. There is no `--refs`. Imports `fetch_fulltext.pmc_xml_to_text`; parse failure/no body prints a message, not a failing exit. No XML repair, reference-list or table-cell extraction; load `pmc-xml-tools` for those needs. |
| `verify_ingest.py` | `<slug> --instance <brain> --require-filled --article-package <manifest> --publication-receipt <receipt>`. For an intermediate queued page add `--page-only`; it is not completion. Canonical identity uses network metadata. `--offline` skips identity and cannot establish production completion. |
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

## Direct metadata and document retrieval

Use the named helper for observed API/document URLs, including bioRxiv/medRxiv,
Crossref, DataCite, PubMed/EPMC, and versioned manuscript or supplement links.
Use the actual full DOI in bioRxiv/medRxiv details URLs, not just its suffix.
Resolve placeholders to quoted literal values and run each command separately:

```sh
"<python>" "<scripts>/fetch_source.py" --url "https://api.biorxiv.org/details/biorxiv/<full-doi>" --evidence-dir "<existing-external-parent>/metadata-attempt-1" --filename "details.json"
"<python>" "<scripts>/fetch_source.py" --url "<verified-versioned-pdf-url>" --evidence-dir "<existing-external-parent>/manuscript-attempt-1" --filename "manuscript.pdf"
```

The helper creates the new evidence directory. Use the file reader for returned
JSON/XML/HTML; preserve complete metadata and authors, paging through long records.
For PDF bytes, use the inspection commands below and then the manuscript runtime.
A filename or HTTP 200 does not establish format, identity or full text: reject
challenge pages and empty collections after reading the response. Retrieved
supplements are retained only. Retry only under the existing bounded retrieval
policy, using a new evidence directory; retain earlier failure evidence.

Keep routine retrieval out of `python -c`, interpreter heredocs and shell pipelines.
These canonical helpers are reviewed code, not permission exemptions: if a helper
is denied, report the denial and use only a separately authorized alternative.
Do not copy rejected payloads into temporary scripts or change security settings.

## Read-only PDF inspection

For page counts, attachment identity checks, page excerpts and keyword locations,
reuse installed `pdfinfo` and `pdftotext` before writing inline Python or a new
helper. Check availability with `command -v pdfinfo` and `command -v pdftotext`,
as separate commands. If absent, use the PDF skill's existing named reader with
its configured interpreter; do not install dependencies during ingestion.

Run each command separately with quoted, literal absolute paths. Use the terminal
workdir field if a working directory is actually needed; these commands need none.
Keep stderr visible and check each exit status. A scanner can reject a compound
`cd ... && python -c ...` command because it cannot resolve the nested executable
body, even when the inner inspection is read-only. Do not disable scanning, hide
rejected code inside a new script, or treat an actual authorization denial as a
syntax problem. Direct native commands are inspectable alternatives, not a promise
that every environment will approve them.

```sh
pdfinfo "<absolute-source.pdf>"
pdftotext -f 29 -l 36 -layout "<absolute-source.pdf>" -
pdftotext -tsv "<absolute-source.pdf>" "<new-scratch>/document-words.tsv"
rg -i 'term-one|term-two' "<new-scratch>/document-words.tsv"
```

The text command prints physical PDF pages **29–36 inclusive**; page numbers are
one-based, so Python indices 28–35 correspond to this range. The TSV's second
column, `page_num`, retains that physical page number for every word. Search the
TSV for keywords, then read candidate pages with `-f`/`-l`; word counts are not
page counts and multiword phrases may span rows. Verify the PDF conversion
succeeded before searching its new scratch file. `rg` exit 1 means no matching
text, while conversion errors or `rg` exit 2 are failures. Empty native text can
mean an image-only page; keyword hits do not establish article identity or prove
a supplement boundary. Inspect the actual title/header and source context.

These are acquisition/inspection aids only. Preserve the original PDF unchanged;
they do not replace full manuscript reading through the runtime, focused
scientific review, external archiving or final integration.

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

## Stage an existing annotated draft

Use the file-writing capability to create `<external-work>/draft.md`, then a
small `<external-work>/stage.json` containing:

```json
{"operation":"stage","job_id":"<existing-job-id>","markdown_path":"<external-work>/draft.md","review_note":"Central findings checked against the retained manuscript; no unresolved material issue."}
```

Run the configured runtime Python with `-m manuscript_ingest.cli --runtime-root
<runtime-root> --input <external-work>/stage.json`. Use the deployment's existing
PYTHONPATH. No inline interpreter or document embedded in a shell command is
needed. Keep citation locators in the draft file.
