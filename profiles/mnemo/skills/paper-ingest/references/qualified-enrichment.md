# Qualified figure/table enrichment

Runtime paths and installation: `runtime.md`. Every trusted method, enrichment, integration and adapter root below is the same resolved skill `scripts/` directory.

Use this after the retained-source workflow and verified source-only v4 handoff for each new production ingest retaining PDFs. This is an agent-operated route through the deployed qualified-enrichment capability (Hermes binding: `paper_enrichment`). Discover its native schema in the operating session before proceeding. Resolve the canonical skill runtime and PDF interpreter from the active instance deployment (`runtime.md`); do not install another profile or substitute a generated shell executor when a capability is unavailable. An unavailable deployment is a hold, not permission to skip enrichment silently.

Historical reads and strict execution bindings follow the compatibility table in
`source-package-integration.md`. A saved code hash is producer provenance, not
permission to resume a job with a changed implementation.

## Acceptance and boundaries

New ingestion and refresh share the portable enrichment executor. Ordinary page content is the ingesting model's best estimate, not certified ground truth. Record only evidence-supported substantive deviations from that baseline: a material native/VLM disagreement, an unreadable table region, or a failed figure description. Do not hunt for limitations, invent minor caveats, or label missing exhaustive review coverage as a defect. Empty findings and qualifications are valid.

Page readiness is separate from request success. An attributed assessment must identify usable retained evidence and explicitly account for any never-attempted requests. Failed or uncertain visual requests remain failed or uncertain, but usable manuscript text may support a page. Integrity/route/model/count holds, fixture provenance and unaccounted pending source work still prevent production completion. Never call unavailable visual content successfully enriched.

The capability selects all eligible source figures and tables, retaining its existing data-file-to-table mapping. Unknown/skipped/incomplete elements remain in its disposition register. Algorithms/code are not selected by default. Existing algorithm records may be reviewed for discovery; mathematical-specification use always requires source inspection. Production enablement does not authorize historical re-ingestion or another evaluation campaign.

## Operations

Use absolute paths and a new external `attempt_dir` for every call; missing parents are created safely. Keep inputs in a separate directory from attempt/output roots. Keep all receipts, including refusals, while the job is active; final products replace them after verified finalization. `qualified-enrichment-schema.md` owns the full operation and submission schema; the native tool supplies argument names. No phase authorizes another automatically.

1. `prepare`: provide the verified v1 `source_handoff`, a new job `output`, and the accepted `processor_cache`. Code enumerates all eligible figures/tables, counts the actual payloads and writes the seal and unapproved template. Never curate only favorable elements or use a test-root flag on production sources.
2. Review the saved payload/count/overflow, model route and budget. A responsible parent/operator separately authors approval against the seal using the portable approval contract at `enrichment/approval.template.json`. Counting never grants approval.
3. `execute`: provide `job`, the separate `approval`, and explicit `authorize_posts: true`, only after authorization. Local transport/response failures allow independent siblings to continue. Explicit continuation may send only never-reserved siblings with the byte-identical executed approval and original budget; consumed/uncertain requests are never retried. Global integrity, authorization, route, model or count faults stop posting. Do not set offline mode for actual execution.
4. `report`: provide `job` and a new external `output`. Check process status and saved evidence separately from semantic success. A zero-eligible preparation reports `review-create`; skip count/seal/execute and retain its explicit disposition.

To resume interrupted offline bookkeeping, use `seal` with `job`, `processor_cache`, and a new attempt directory. It revalidates evidence and skips completed counting/sealing. Partial counts remain holds; consumed requests are never restarted. Preparation without a cache and the separate `count` command remain supported for staged inspection. Never rerun preparation into an existing job. All output and attempt directories must stay outside immutable retained sources; misplaced writes are rejected before directory creation.

Use explicit `offline: true` for non-execution operations. Original PDFs, native text, crops, raw responses and extraction outcomes remain unchanged. Corrections are separately attributed findings/proposals. New review decisions require a new export; do not overwrite or repin historical exports.

## Review and downstream use

Compare the actual generated claim, not merely strings somewhere in its source. Count physical row/column positions rather than treating the largest printed item number as a row count. A correct account of source coordinates does not validate a contradictory generated count. Review coverage on a prose field is an attributed check, not proof that every clause was tested; narrow the target where possible, and record only evidence-supported substantive problems.

Every observed substantive unresolved ambiguity or disagreement affecting an included claim belongs in a scoped finding with its reason and evidence. Do not store it only in a coverage explanation or let a broad inherited limitation substitute for it. An empty findings list can coexist with errors the operator missed. Ordinary values and summaries do not require exhaustive certification. Specialized uses may impose stronger checks.

Review table values with their headings, units, notation and source association. Units printed once in a header need not recur in every value. Native equality does not establish superscripts, indentation or grouping. Distinguish extraction omissions from information present in the answering input but omitted in its answer. Figures permit empty observation lists; do not require subjective biological interpretation or precise estimates from unlabelled plot coordinates.

Use the dedicated pinned source-inspection capability (Hermes: `paper_vision_inspect`) when visual evidence is needed. Attribute its findings to the returned inspection model, not to a text-only operator's personal vision or independent human truth. Preserve disagreement rather than deciding by model vote.

`consume` takes `export_path`, `element`, exact JSON-Pointer `target`, `purpose`, and new `output`. Use `summary` for ordinary page material; retain applicable substantive findings and qualification alongside the claim. Discovery retains audit context. Exact use exposes all review aspects and refuses unresolved/unreviewed content without a real `source_inspection` attestation or explicit `qualification`. Qualification permits qualified use; it does not correct the original or make an unsupported number factual. `algorithm-specification` always requires owning-source inspection and cannot be cleared by qualification alone.

Retain the entire relevant consumer context: `findings` including attributed resolutions, `unresolved_findings`, `unreviewed_aspects`, `unapplied_correction_findings`, qualification and unchanged-original status. Do not copy only `content`. For a cell's exact value, also inspect its parent cell/record for notation, header association and units; a raw-value JSON Pointer alone is not the complete scientific quantity. Resolved proposals never silently replace originals. Conflicting proposals stay unresolved, and a native literal match cannot clear structural uncertainty.

Keep any applicable substantive qualification beside the scientific claim. Unsupported exact claims must be inspected, omitted or stated as unresolved; a detached generic caveat is insufficient. This procedure does not promise automatic detection of every discrepancy.

## Final v5 handoff and completion

Build a new handoff with the source arguments plus the verified annotated export and its actual export receipt:

    <pdf-python> -B <scripts>/source_package.py handoff --retention <retention.json> --package <source-package> --launcher-result <source-summary-attempt/result.json> --method <scripts> --enrichment-handoff <export/handoff.json> --enrichment-launcher-result <export-attempt/result.json> --integration <scripts> --enrichment-root <scripts> --output <new-v5-handoff>
    <pdf-python> -B <scripts>/source_package.py verify --handoff <v5/handoff.json> --method <scripts> --integration <scripts> --enrichment-root <scripts> --require-enriched

Finalize the verified v5 result into permanent scientific products before writing the paper's durable source pointer:

    <pdf-python> -B <scripts>/final_products.py ingest --handoff <v5/handoff.json> --output <new-final-package> --method <scripts> --integration <scripts> --enrichment-root <scripts>

Keep the v5 `qualifications.txt` text exactly (an empty file is valid) in the paper. Add the unformatted Ingest log pointer, relative to that paper:

    Source package: <relative-final-package/manifest.json>

The final package's `products_key` identifies its descriptions, structured values and substantive qualifications. It also retains originals, native text, crops and source mappings. Do not point the completed paper at temporary review packets, raw requests or annotated runtime exports.

Before the final page check, render manuscript figures from the compact package:

    <pdf-python> -B <scripts>/figure_embeds.py render --manifest <final-package/manifest.json> --page <paper.md> --output <new-candidate.md>

Review and apply the candidate under the original-page guard, before recording any page completion hash. The renderer embeds retained figure-body crops with standard Markdown relative links and extracted source captions as text. It does not copy images, embed caption screenshots, or rerun extraction/model requests. New figures default to a Figures section before the Ingest log; whole figure blocks can be moved beside the discussion. Keep panel fragments in source order. Preserve source-caption/crop qualifications beside the affected figure; distinguish model interpretations from source captions. A failed model description alone is not a reason to hide an intact image.

Supplementary figures are opt-in: add `--supplement 'ELEMENT_ID=why this figure is essential to the page'` only when needed for context. The reason remains with the figure. No automatic supplementary gallery. Missing figure bodies are stated explicitly rather than fabricated. Unknown source roles require source-metadata reconciliation, not guessing from the figure number.

Generated blocks have ownership markers. Prose outside them is preserved. If a block was manually edited, regeneration holds for reconciliation instead of overwriting it; retain that edited content while reconciling a new candidate. Do not bypass the guard by silently removing markers. Full blocks can be repositioned without changing their contents. Initial finalized packages require figure verification; old completion formats keep their original contract.

Images remain in the local final package, outside Git and replicated through the existing source-package sync/archive process. Restore packages to their linked vault-relative locations. Before removing an older package, update every affected embed and verify the actual page links. A Markdown-only Git clone does not contain the images.

Complete Phase 10 with:

    <pdf-python> -B <scripts>/verify_ingest.py <slug> --instance <instance> --require-filled --final-products <final-package/manifest.json> --require-enriched-source

Add `--page-only` for the existing PAGE_READY contract, not to bypass source/enrichment checks. The finalizer first reconstructs the current source/enrichment handoff, then durable verification checks retained product hashes, article identity and substantive qualifications without the original job directories. Legacy handoff options remain for historical records. Identity, bibliography, author wiring, graph integration and scientific review remain required.

After final products and the paper pass verification, follow `portable-articles.md` for verified cleanup of completed temporary jobs. Active request reservations and incomplete enrichment are not cleanup candidates.
