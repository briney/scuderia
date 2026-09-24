# Portable article archives and full/selective re-enrichment

Load for an explicit article-package archive/restore or existing-paper re-enrichment request. This is one shared Python library/CLI (`scripts/portable_articles.py`, `scripts/reenrich.py`), not a second acquisition pipeline or an unattended campaign. The existing new-ingest source-package/v7 route remains unchanged. The operator supplies retrieval, scientific review and page reconciliation through explicit contracts; pending operator work is not completion.

## Prerequisites and ownership

Use the instance's accepted PDF Python interpreter, rclone remote/bucket/prefix and trusted code roots. Set `PDF_ENRICHMENT_METHOD`, `REENRICH_ENRICHMENT_ROOT` and `REENRICH_INTEGRATION_ROOT` to the accepted source method, frozen enrichment package and qualified-enrichment integration respectively. Never execute code or choose credentials from paths embedded in an archive. Set `PYTHONDONTWRITEBYTECODE=1`; use an explicit nonsymlink scratch directory only for disposable tests/caches. Production inputs, work directories and receipts require durable storage. No installation, scheduled run, paid call, archive write or page mutation is authorized merely by loading this reference.

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

The library uses `Request(article, elements=None, page=None)` and `plan`/`execute` plus explicit stage operations. The CLI uses `reenrich.py plan`: no `--element` means all eligible figures/tables; repeated `--element` selects exact IDs or unambiguous labels. An empty list is invalid. Algorithms/code remain deferred. Full scope includes source limitations and missing-supplement holds; it is not permission to infer completeness from a manuscript alone.

    <py> -B <scripts>/reenrich.py plan --article <slug> --manifest <restored/manifest.json> --work-root <new-durable-work-dir>

Add `--element <selector>` for selected enrichment. Omit `--page` for archive-only work. For a paper refresh, add `--page <absolute-paper.md>`; selective page refresh also requires `--page-scope <json>` containing a list of `{heading, elements}` for real existing headings and exact element IDs. Planning binds current page, source, code and model hashes. A run planned with a page cannot later bypass page application by claiming archive-only completion.

Legacy plans omit `--manifest` and remain pending retrieval/source preparation. After the normal acquisition/extraction route and manifest construction, `adopt --work-root ... --manifest ... --approval ...` requires explicit identity approval with `plan_sha256`, `manifest_sha256`, `article`, original `requested_elements`, `approved_by`, and `identity_and_scope_reviewed: true`. It preserves the original plan. Full/legacy page refresh still requires full distillation/reconciliation review.

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

`execute` validates status/resume; it does not authorize posting. Never automatically retry a consumed or possibly posted request. Review the generated unapproved template, complete wire counts and explicit token/post budget before separately approving an HTTPS model endpoint and credential environment-variable name. Never store credential values in approval files.

The default model profile is frozen-compatible `qwen3.8-27b`. A custom `--profile` at plan time must use `operator-exact-count-receipt` counting: exact model and wire hashes/counts with retained provider/processor evidence via `count --count-receipt`. Temperature must be zero and response format JSON-object. Returned model and prompt-token usage must agree exactly; overflow is a hold, not automatic trimming. Configurable model support is offline-tested, not proof that any particular production provider works. A new provider/profile needs separately authorized bounded live validation before campaign use.

Review submissions use `contextual-review-v1`, packet hash, attributed reviewer, findings, coverage and resolutions. Apply the scientific and exact-use rules in `qualified-enrichment.md`; unreviewed content remains unreviewed. The new export schema is `portable-qualified-export-v3`. It retains raw history through logical key/hash references and deterministic warning projections rather than recursively embedding prior wire bodies or images. New results do not resolve inherited findings automatically. Unscoped historical warnings remain explicit; context overflow requires operator action rather than truncation.

## Optional page reconciliation

Archive-only plans skip this section. Page plans require `candidate-import --submission ...`, inspection of `page-candidate/page-candidate.md` and its diff, then separately authorized `apply --authorize-page-apply`.

The candidate schema is `reenrich-page-candidate-v2`: `binding`, `export_sha256`, attributed `reviewer`, nonempty `qualification`, `full_distillation_reviewed`, and `replacements`. Each replacement binds an existing `heading`, `old_sha256`, `new_text`, `elements`, and `evidence`; each evidence entry supplies `element_id`, `source_sha256`, JSON-Pointer `target` and `qualification`. Cover every requested element. Full/legacy page runs require full distillation review, not merely passing mechanical extraction.

For an attributed no-change review, set `reconciliation_outcome: reviewed-no-scientific-text-change` and keep each reviewed body exactly unchanged. Do not invent scientific edits to pass the gate. The code installs a source/element/target-specific qualification register after unchanged frontmatter, with warnings, coverage, unresolved history, export hashes and a publication-receipt locator. Generic caution alone cannot replace scoped findings. Source/graph links, human annotations and unrelated sections remain protected; a changed live page hash holds application. Pause noncooperating editors during application.

## Publication, durable receipts and completion

    <py> -B <scripts>/reenrich.py publish --work-root <work> --remote <remote> --bucket <bucket> --prefix <prefix>

This verifies all archive bytes, publishes the immutable manifest and writes `completion.json`. For a page refresh it also writes an immutable sibling receipt named `<page-filename>.article-<binding-prefix>.json`. Keep that receipt with the page in Git-backed storage. For archive-only completion retain an exact copy in the instance's documented durable publication-receipt directory; the only copy must never live in disposable scratch. Neither the sibling receipt nor local operational maps are inputs to their own archive. Before successful publication, a missing receipt means pending publication.

Run the dedicated completion verifier with externally trusted publication pins and the full local archive, including the actual page for page-refresh plans:

    <py> -B <scripts>/reenrich.py verify-completion --receipt <durable-receipt.json> --manifest <full-archive/manifest.json> --manifest-key <key> --manifest-sha256 <hash> --article-key <article-key> --page <paper.md>

Omit `--page` only for archive-only plans. The verifier checks source/history/review bindings, complete inventory, export/register pointers and the exact applied page/companion receipt. It works after original run roots are gone. Publication verification is historical; for fresh remote availability, restore using trusted transport/pins and then verify. Subsequent manual page edits invalidate exact-snapshot completion and require a new reviewed revision, not overwriting an old receipt.

Keep `selected-refresh-complete`, `full-refresh-complete`, `selected-archive-complete` and `full-archive-complete` distinct. Fixture labels start with `offline-` and have `production_complete: false`. Archive-only is never page-refresh completion. Missing prerequisites, interrupted writes or unconfirmed requests remain holds.

This is a separate completion contract from the existing new-ingest v2 handoff. Never feed `portable-qualified-export-v3` to `source_package.py`/`verify_ingest.py` as if it were their frozen export schema. For an existing-page refresh, run ordinary page/identity/graph checks and frontmatter lint in addition to `reenrich.py verify-completion`; retain all applicable prior ingest/source pointers. Do not weaken new-ingest verification or infer bibliography/author integration from a package receipt. Close the verified owned changes with `git-ops`; campaign scheduling and figure embedding are separate work.
