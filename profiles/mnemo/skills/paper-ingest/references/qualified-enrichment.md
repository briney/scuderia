# Qualified figure/table enrichment

Runtime paths and installation: `runtime.md`. Every trusted method, enrichment, integration and adapter root below is the same resolved skill `scripts/` directory.

Use this after the retained-source workflow and verified source-only v1 handoff for each new production ingest retaining PDFs. This is an agent-operated route through the deployed qualified-enrichment capability (Hermes binding: `paper_enrichment`). Discover its native schema in the operating session before proceeding. Resolve the canonical skill runtime and PDF interpreter from the active instance deployment (`runtime.md`); do not install another profile or substitute a generated shell executor when a capability is unavailable. An unavailable deployment is a hold, not permission to skip enrichment silently.

Historical reads and strict execution bindings follow the compatibility table in
`source-package-integration.md`. A saved code hash is producer provenance, not
permission to resume a job with a changed implementation.

## Acceptance and boundaries

The route permits imperfect figure/table content with explicit findings, review scope and qualifications. It does not establish factual fidelity from schema validity, successful execution, an empty findings list or a reviewer's coverage declaration. Source acquisition/extraction holds, integrity or serving mismatches, pending/possibly-posted requests, fixture provenance and caption-only controls remain disqualifying. Verified failed/partial enrichment records are visible content limitations, not accepted structured content. The frozen executor's completed, schema-failed run may also classify untouched siblings as `skipped-after-failure`; the qualified runtime's verified eligibility and execution-hold list determine whether that is a retained limitation. Do not confuse this disposition with a pending or possibly-posted request, and never describe skipped elements as successfully enriched. Read the qualified runtime/export, not only the older execution report, before deciding completion. Keep usable supported material; do not make perfect extraction a prerequisite for the whole paper.

The capability selects all eligible source figures and tables, retaining its existing data-file-to-table mapping. Unknown/skipped/incomplete elements remain in its disposition register. Algorithms/code are not selected by default. Existing algorithm records may be reviewed for discovery; mathematical-specification use always requires source inspection. Production enablement does not authorize historical re-ingestion or another evaluation campaign.

## Operations

Use absolute paths and a new external `attempt_dir` with an existing parent for every call. Keep inputs in a separate directory from attempt/output roots. Retain all receipts, including refusals. `qualified-enrichment-schema.md` owns the full operation and submission schema; the native tool supplies argument names. No phase authorizes another automatically.

1. `prepare`: `source_handoff` is the verified v1 handoff; `output` is a new qualified job. Code enumerates the full roster. Never curate only favorable elements or use a test-root flag on production sources.
2. `count`: provide `job` and the accepted `processor_cache`. Review actual payload/count/overflow, model route and budget; preserve frozen extraction settings.
3. `seal`: provide `job`. A responsible parent/operator separately authors approval against the resulting seal using the unchanged frozen approval contract. The generated template remains unapproved.
4. `execute`: provide `job`, the separate `approval`, and explicit `authorize_posts: true`, only after authorization. No retry, fallback, budget reuse or automatic repair of consumed/uncertain requests. Do not set offline mode for actual execution.
5. `report`: provide `job` and a new external `output`. Check process status and saved evidence separately from semantic success. For a zero-eligible job, skip count/seal/execute and retain the explicit zero-eligible disposition.
6. `review-create`: provide the qualified `run` and new `output`. Production uses qualified jobs; `kind: v7-run` creates review-only dossiers for historical records and never retroactively promotes them.
7. `review-packet`: provide `review_root`, exact `elements` and a new packet `output`. Bound review to actual targets and supplied source evidence. Use multiple small packets rather than truncated inventories. Optional `max_bytes` may be increased within the documented bound.
8. `review-import`: provide `review_root`, `packet`, and a separately authored contextual-review submission. Record checks actually performed; unreviewed fields stay unreviewed. No review is fabricated merely to clear an exact-use gate.
9. `export`: provide `review_root` and a new `output`. Preserve its actual successful attempt `result.json` for v2 construction. `verify-export` revalidates its `export_path`; a structural pass does not waive execution holds.

Use explicit `offline: true` for non-execution operations. Original PDFs, native text, crops, raw responses and extraction outcomes remain unchanged. Corrections are separately attributed findings/proposals. New review decisions require a new export; do not overwrite or repin historical exports.

## Review and downstream use

Compare the actual generated claim, not merely strings somewhere in its source. Count physical row/column positions rather than treating the largest printed item number as a row count. A correct account of source coordinates does not validate a contradictory generated count. Review coverage on a prose field is an attributed check, not proof that every clause was tested; narrow the target where possible, or explicitly state unreviewed clauses and add findings for suspected errors.

Every observed unresolved ambiguity or disagreement affecting an included claim belongs in a scoped finding with its reason and evidence. Do not store it only in a coverage explanation or let a broad inherited limitation substitute for it. An empty findings list can coexist with errors the operator missed. Model-operated review is not an autonomous correctness certificate; task-critical exact claims still require targeted source inspection, stronger/human review, or explicit qualification/omission.

Review table values with their headings, units, notation and source association. Units printed once in a header need not recur in every value. Native equality does not establish superscripts, indentation or grouping. Distinguish extraction omissions from information present in the answering input but omitted in its answer. Figures permit empty observation lists; do not require subjective biological interpretation or precise estimates from unlabelled plot coordinates.

Use the dedicated pinned source-inspection capability (Hermes: `paper_vision_inspect`) when visual evidence is needed. Attribute its findings to the returned inspection model, not to a text-only operator's personal vision or independent human truth. Preserve disagreement rather than deciding by model vote.

`consume` takes `export_path`, `element`, exact JSON-Pointer `target`, `purpose`, and new `output`. Discovery/summary retain warnings and review scope. Exact use exposes all review aspects and refuses unresolved/unreviewed content without a real `source_inspection` attestation or explicit `qualification`. Qualification permits qualified use; it does not correct the original or make an unsupported number factual. `algorithm-specification` always requires owning-source inspection and cannot be cleared by qualification alone.

Retain the entire relevant consumer context: `findings` including attributed resolutions, `unresolved_findings`, `unreviewed_aspects`, `unapplied_correction_findings`, qualification and unchanged-original status. Do not copy only `content`. For a cell's exact value, also inspect its parent cell/record for notation, header association and units; a raw-value JSON Pointer alone is not the complete scientific quantity. Resolved proposals never silently replace originals. Conflicting proposals stay unresolved, and a native literal match cannot clear structural uncertainty.

Keep the applicable qualification beside the scientific claim. Unsupported exact claims must be inspected, omitted or stated as unresolved; a detached generic caveat is insufficient. This procedure does not promise automatic detection of every discrepancy.

## Final v2 handoff and completion

Build a new handoff with the source arguments plus the verified annotated export and its actual export receipt:

    <pdf-python> -B <scripts>/source_package.py handoff --retention <retention.json> --package <source-package> --launcher-result <source-summary-attempt/result.json> --method <scripts> --enrichment-handoff <export/handoff.json> --enrichment-launcher-result <export-attempt/result.json> --integration <scripts> --enrichment-root <scripts> --output <new-v2-handoff>
    <pdf-python> -B <scripts>/source_package.py verify --handoff <v2/handoff.json> --method <scripts> --integration <scripts> --enrichment-root <scripts> --require-enriched

Keep the v2 `qualifications.txt` text exactly in the paper and add both unformatted Ingest log pointers, relative to that paper:

    Source package: <relative-v2-handoff.json>
    Annotated enrichment: <relative-export/annotated.html>

Complete Phase 10 with:

    <pdf-python> -B <scripts>/verify_ingest.py <slug> --instance <instance> --require-filled --source-package-handoff <v2/handoff.json> --source-package-method <scripts> --require-enriched-source --enrichment-integration <scripts> --enrichment-root <scripts>

Add `--page-only` for the existing PAGE_READY contract, not to bypass source/enrichment checks. Legacy v1 verification remains for history; new production ingests use v2. The canonical qualification register and annotated pointer must survive unchanged; field-level prose must also preserve the relevant scientific limitation. Source/enrichment mechanical completion does not replace identity, bibliography, author wiring, graph integration or scientific review.
