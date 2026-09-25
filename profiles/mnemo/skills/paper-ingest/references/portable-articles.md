# Portable article archives and full/selective re-enrichment

Runtime paths and installation: `runtime.md`. Every trusted method, enrichment, integration and adapter root below is the same resolved skill `scripts/` directory.

Load for an explicit article-package archive/restore or existing-paper re-enrichment request. This is one shared Python library/CLI (`scripts/portable_articles.py`, `scripts/reenrich.py`), not a second acquisition pipeline or an unattended campaign. New ingestion and refresh share `article_enrichment`; source acquisition/extraction gates remain unchanged. The operator supplies retrieval, scientific review and page reconciliation through explicit contracts; pending operator work is not completion.

Historical reads and strict execution bindings follow the compatibility table in
`source-package-integration.md`. A saved code hash is producer provenance, not
permission to resume a job with a changed implementation.

## Prerequisites and ownership

Use the instance's accepted PDF Python interpreter, rclone remote/bucket/prefix and trusted code roots. Set `PDF_ENRICHMENT_METHOD`, `REENRICH_ENRICHMENT_ROOT` and `REENRICH_INTEGRATION_ROOT` to the same resolved skill `scripts/` directory (`runtime.md`). Never execute code or choose credentials from paths embedded in an archive. Set `PYTHONDONTWRITEBYTECODE=1`; use an explicit nonsymlink scratch directory only for disposable tests/caches. Production inputs, work directories and receipts require durable storage. No installation, scheduled run, paid call, archive write or page mutation is authorized merely by loading this reference.

The primary owns source identity, budget, review, durable receipts and final verification. A delegated worker returns its owned paths and pending operations; it cannot silently broaden a selected roster or start a corpus campaign. Resolve source acquisition through Phase 4 and `source-package-integration.md`; preserve actual response evidence and supplementary-source dispositions. Unknown source retrieval is explicit operator work, not an executable shell hook.

## Archive layout and source identity

New manifests use `portable-article-manifest-v3`:

    <prefix>/articles/<article-key>/objects/<sha256>
    <prefix>/articles/<article-key>/revisions/<revision-id>/manifests/<manifest-sha256>.json

The manifest maps logical files, documents/source hashes, element IDs, ordered crop fragments, native context, dependencies, provenance and limitations to individually accessible objects. No compressed archive is required. The article key hashes slug/DOI/PMID; keep that identity stable, and treat identity corrections or slug changes as an explicit migration, not a silent new revision. Element labels must resolve unambiguously against source-bound IDs.

Unchanged bytes share article-scoped object keys across revisions. Both reused and newly uploaded objects are read back and SHA256-verified; the immutable manifest is published last. There is no mutable latest pointer. This is byte verification, not scientific acceptance or protection against an actor who replaces every trusted input. Saved v2 manifests retain their old revision-scoped object-key interpretation. Legacy `papers/<hash>.pdf` objects and frozen source receipts remain unchanged.

Use absolute, disjoint paths. Local materialization is described by a separate manifest-bound `local-map.json`; do not upload that map or rewrite original receipts to change workstation paths. Inputs/parents cannot be symlinks; source files cannot be hardlinks.

## Manifest, publication and restore

After accepted source preparation/extraction and a verified source handoff:

    <py> -B <scripts>/portable_articles.py manifest --retention <retention.json> --package <package> --handoff <source-handoff.json> --package-id <revision-id> --output <new-archive-dir>

Existing frozen qualified evidence uses `--job`, `--review` and `--export` together. Optional `--page` and repeated `--legacy-pdf` retain historical bytes. `--document-bindings` supplies exact document/acquisition associations when required. Never use `--fixture-root` on a production package.

Only with archive-write authorization:

    <py> -B <scripts>/portable_articles.py publish --manifest <archive/manifest.json> --remote <remote> --bucket <bucket> --prefix <prefix>

Save the actual returned publication receipt, especially `manifest_key`, `manifest_sha256` and `article_key`, in a trusted durable location. File existence or an upload exit alone is not proof of successful read-back. Restore with trusted transport and exact pins:

    <py> -B <scripts>/portable_articles.py restore --manifest-key <key> --manifest-sha256 <hash> --article-key <article-key> --remote <remote> --bucket <bucket> --prefix <prefix> --destination <new-restored-dir>

Add `--element <element-id>` for a selected dependency closure. Full restore is required before publishing a whole-article revision or verifying its completion, even after selected enrichment. Selected materialization supports enrichment/export but is not a full archive; automatic partial-map merging is not implemented. Do not delete an existing materialization to retry into it.

## One full/selected request path

The library uses `Request(article, elements=None, page=None)` and `plan`/`execute` plus explicit stage operations. The CLI uses `reenrich.py plan`: no `--element` means all eligible figures/tables; repeated `--element` selects exact IDs or unambiguous labels. An empty list is invalid. Algorithms/code remain deferred. Full scope includes the actual source inventory and acquisition dispositions. New source readiness metadata allows supported pages despite accounted-for missing supplements; it never claims those sources were retrieved. Legacy manifests retain their original completion rules.

    <py> -B <scripts>/reenrich.py plan --article <slug> --manifest <restored/manifest.json> --work-root <new-durable-work-dir>

Add `--element <selector>` for selected enrichment. Omit `--page` for archive-only work. For a paper refresh, add `--page <absolute-paper.md>`; selective page refresh also requires `--page-scope <json>` containing a list of `{heading, elements}` for real existing headings and exact element IDs. Planning binds current page, source, code and model hashes. A run planned with a page cannot later bypass page application by claiming archive-only completion.

Legacy plans omit `--manifest` and remain pending retrieval/source preparation. After the normal acquisition/extraction route and manifest construction, `adopt --work-root ... --manifest ... --approval ...` requires explicit identity approval with `plan_sha256`, `manifest_sha256`, `article`, original `requested_elements`, `approved_by`, and `identity_and_scope_reviewed: true`. It preserves the original plan. Full/legacy page refresh still requires full distillation/reconciliation review.

## Selected diagnostic validation

For explicitly selected saved elements in a current partial or multi-document source bundle, use the diagnostic-only adapter. It does not require or fabricate an acquisition manifest. It preserves the `pdf-source-package-v1` schema and recomputes the source reader's evidence, fixture origin, document identities, ordered fragments and type eligibility. It asserts no bibliographic article association. Only existing eligible logical figure/table IDs are accepted, never labels, unassociated candidates or caller-supplied type overrides.

    <py> -B <scripts>/portable_articles.py diagnostic-manifest --package <saved-package> --element <exact-element-id> --output <new-diagnostic-source-dir>
    <py> -B <scripts>/reenrich.py diagnostic-plan --manifest <diagnostic-source/manifest.json> --element <same-exact-element-id> --work-root <new-work-dir>

Repeat `--element` for each selected ID in the same order at both gates. An absent, empty, duplicate, unknown or expanded roster is refused. The local `selected-diagnostic-source-v1` representation has no article identity/key. It retains and revalidates the whole saved source inventory without modifying originals; model requests remain limited to the selected elements. This intentionally conservative local path requires the original package layout. Archive publish/restore is refused for this representation.

Use the same `prepare`, `count`, `seal`, separately authorized `approved-execute`, `review-create`, `review-import` and `export` continuations below. The default profile and exact count/usage checks are unchanged. Diagnostic scope is bound into preparation, approval, outcomes and export; the unapproved approval template does not authorize posting. `--fixture` is only for explicit offline tests; a fixture source or run cannot be promoted to live. A live diagnostic remains live, not an offline fixture.

The final local status is `diagnostic-export-ready`, never an article archive or page-refresh completion. Diagnostic status/export always have `production_complete: false` and `page_refresh_complete: false`. Source incompleteness, acquisition/association holds, recorded findings and unreviewed aspects remain visible. `candidate-import`, `apply`, `publish` and article completion verification are forbidden. Do not use this output as a complete article revision or a substitute for production acquisition/extraction gates.

## Continuations, model gates and review

Run the following with `--work-root <work>`; each stage reports evidence or the next pending operation:

    execute
    prepare
    count --cache <accepted-processor-cache>
    seal
    approved-execute --approval <separately-authored-approval.json> --authorize-posts
    review-create
    review-import --submission <contextual-review.json>
    export

`execute` validates status/resume; it does not authorize posting. Its enrichment receipt reports each request as pending, uncertain, failed or completed. `approved-execute` is idempotent for consumed requests and can explicitly resume never-sent siblings under the byte-identical executed approval and original budget. Local transport/response failures retain per-request evidence and allow independent siblings to continue; route/count/credential mismatches and source/code/approval integrity failures stop further posting. No consumed or possibly posted request is retried. A failed/uncertain request needs a separately authorized selected run for a new attempt. These rules also apply to new-ingest enrichment. Historical v7 execution is refused; historical readers remain available.

Review the generated unapproved template, complete wire counts and explicit token/post budget before separately approving an HTTP or HTTPS model endpoint and credential environment-variable name. The separately authored approval binds the exact operator-chosen endpoint; HTTP deployments are supported without TLS probing or endpoint discovery. Redirects and proxies are disabled; credentials are not forwarded across redirects. Endpoint userinfo, query/fragment, missing hosts, malformed ports and whitespace are rejected. Never store credential values in approval files.

The default model profile is frozen-compatible `qwen3.8-27b`. A custom `--profile` at plan time must use `operator-exact-count-receipt` counting: exact model and wire hashes/counts with retained provider/processor evidence via `count --count-receipt`. Temperature must be zero and response format JSON-object. Returned model and prompt-token usage must agree exactly; overflow is a hold, not automatic trimming. Configurable model support is offline-tested, not proof that any particular production provider works. A new provider/profile needs separately authorized bounded live validation before campaign use.

Review submissions use `contextual-review-v2`, packet hash, attributed reviewer, findings, coverage, resolutions and an optional assessment. Follow `qualified-enrichment-schema.md` for the source-bound usable-evidence assessment and explicit unattempted dispositions. Current exports use `portable-qualified-export-v4` with `policy: observed-limitations-v1`. All requested elements remain reviewable, including failed/uncertain visuals and zero-eligible text-only sources. Usable source evidence can make a page ready without all requests succeeding; `request_accounting` and `execution_complete` retain the actual result. Integrity holds cannot become page-ready. A review is an immutable snapshot; later sibling successes never broaden it. Diagnostics retain their separate no-apply/no-publication contract.

Archive and consumer retention are not model context. Raw originals, hashes and the broad review history remain unchanged and addressable. The shared production/diagnostic prompt projects selected-element and source-document findings using recorded document/hash/element and directory associations, not shared labels or page numbers. Actual unscoped warnings and attribution remain explicit; empty hash-only entries are not sent. Identical decoded projections are represented once without merging different targets, sources or attribution. Surrounding native page text and source limitations remain context, not verified element associations. New results do not resolve inherited findings automatically. There is no text cap or model-based pruning; an oversized relevant prompt still fails the official context gate.

## Optional page reconciliation

Archive-only plans skip this section. Page plans require `candidate-import --submission ...`, inspection of `page-candidate/page-candidate.md` and its diff, then separately authorized `apply --authorize-page-apply`. Inspect the generated qualification register and total page size as well as the scientific prose. New page registers use `portable-page-qualification-register-v3`: readable scoped qualifications and archive evidence pointers, with a compact machine binding. Full review history stays in the immutable export/archive. Historical v1/v2 registers and completion receipts retain their original rendering and verification contract; do not rewrite completed receipts.

The candidate schema is `reenrich-page-candidate-v3`: `binding`, `export_sha256`, attributed `reviewer`, `qualification` (may be empty), `full_distillation_reviewed`, and `replacements`. Each replacement binds an existing `heading`, `old_sha256`, `new_text`, `elements`, and `evidence`. Model evidence uses `kind: enrichment`, `element_id`, `source_sha256`, JSON-Pointer `target`, and `qualification`; ordinary page use checks substantive findings through `page_view`, not exhaustive coverage. Native fallback uses `kind: source`, manifest `key`/`sha256`, `pointer` (empty for text), exact nonempty `quote`, and `qualification`. PDF fallback uses `kind: inspection`, `key`/`sha256`, physical `page`, inspection `reason`, and `qualification`. Cover every requested element with supported prose or attributed reconciliation. Full/legacy page runs still require full distillation review. Qualifications are required for relevant observed substantive conflicts, not baseline model fallibility or missing coverage.

For an attributed no-change review, set `reconciliation_outcome: reviewed-no-scientific-text-change` and keep each reviewed body exactly unchanged. Do not invent scientific edits to pass the gate. The code installs a source/element/target-specific qualification register after unchanged frontmatter, with applicable source/element/target warnings, attributed correction proposals, export hashes and a publication-receipt locator. Recorded source/version/element and target relationships scope inherited warnings; genuinely unscoped warnings remain explicit. Identical qualifications are represented once. Previously cited targets and their qualifications survive subsequent selective refreshes. Before replacing an embedded register, the reader verifies its archived page snapshot, exports, source locators, review bindings and inherited evidence. Missing evidence or edits inside the old register hold replacement; restore the required archive objects before continuing. A missing publication receipt still means publication is pending. Generic caution alone cannot replace scoped findings. Source/graph links, human annotations and unrelated sections remain protected; a changed live page hash holds application. Pause noncooperating editors during application.

## Publication, durable receipts and completion

    <py> -B <scripts>/reenrich.py publish --work-root <work> --remote <remote> --bucket <bucket> --prefix <prefix>

This verifies all archive bytes, publishes the immutable manifest and writes `completion.json` (`portable-article-completion-v2` for current exports). Page/archive completion, `requests_accounted_for`, and `requests_successful` are separate; a completed partial refresh retains its failed/uncertain counts. For a page refresh it also writes an immutable sibling receipt named `<page-filename>.article-<binding-prefix>.json`. Keep that receipt with the page in Git-backed storage. For archive-only completion retain an exact copy in the instance's documented durable publication-receipt directory; the only copy must never live in disposable scratch. Neither the sibling receipt nor local operational maps are inputs to their own archive. Before successful publication, a missing receipt means pending publication.

Run the dedicated completion verifier with externally trusted publication pins and the full local archive, including the actual page for page-refresh plans:

    <py> -B <scripts>/reenrich.py verify-completion --receipt <durable-receipt.json> --manifest <full-archive/manifest.json> --manifest-key <key> --manifest-sha256 <hash> --article-key <article-key> --page <paper.md>

Omit `--page` only for archive-only plans. The verifier checks source/history/review bindings, complete inventory, export/register pointers and the exact applied page/companion receipt. It works after original run roots are gone. Publication verification is historical; for fresh remote availability, restore using trusted transport/pins and then verify. Subsequent manual page edits invalidate exact-snapshot completion and require a new reviewed revision, not overwriting an old receipt.

Keep `selected-refresh-complete`, `full-refresh-complete`, `selected-archive-complete` and `full-archive-complete` distinct. Fixture labels start with `offline-` and have `production_complete: false`. Archive-only is never page-refresh completion. Missing prerequisites, interrupted writes or unconfirmed requests remain holds.

This is a separate completion contract from the new-ingest v5 handoff. Never feed a portable refresh export to `source_package.py`/`verify_ingest.py` as if it were their frozen export schema. For an existing-page refresh, run ordinary page/identity/graph checks and frontmatter lint in addition to `reenrich.py verify-completion`; retain all applicable prior ingest/source pointers. Do not weaken new-ingest verification or infer bibliography/author integration from a package receipt. Close the verified owned changes with `git-ops`; campaign scheduling and figure embedding are separate work.
