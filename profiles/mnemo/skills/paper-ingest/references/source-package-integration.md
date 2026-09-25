# Retained-source integration

Runtime paths and installation: `runtime.md`. Every trusted method, enrichment, integration and adapter root below is the same resolved skill `scripts/` directory.

This is an agent-operated ingestion route. The adapter retains already acquired inputs and verifies handoffs; it does not retrieve, extract, approve, execute model requests, or write scientific prose. Identity, deduplication, integrity checks, bibliography, complete authors, graph propagation and archival remain paper-ingest obligations.

## Historical compatibility and execution bindings

Historical verification uses explicitly configured reader code. Producer code
hashes and launcher deployment paths remain provenance; readers do not import
code from paths named by an archive or require retired code directories to exist.
Existing evidence files, review chains, and receipts remain unchanged.

| Evidence | Supported reader contract | Checks retained |
|---|---|---|
| Source handoff v1/v2 | Existing source/package and fixed launcher-receipt formats | Recompute source state, facts, exact summary, source identity, holds, receipt grammar and artifact hashes; preserve recorded method/integration hashes |
| Enrichment v7 | `pdf-source-package-enrichment-v7`, prepare v7, prompts v7, response v7, pinned request settings | Source/request hashes, element accounting, count/approval/reservation bindings, response reconstruction and execution holds |
| Qualified selection/dossier/export v1 | `qualified-selection-v1`, `uncertainty-dossier-v1`, `qualified-enrichment-export-v1` | Reconstruct selection, snapshot, review chain, warnings and exact readable export |
| Portable plan v2 / review v2 / export v3 | Existing production and selected-diagnostic scope rules | Regenerate payloads, reconstruct outcomes/accounting, verify byte seals, review chains, qualifications and completion restrictions |

A known format is necessary, not sufficient: reconstruction must still match
its retained evidence. Unknown formats, changed payload semantics, mismatched
outcomes, missing source files, or removed warnings hold verification. A harmless
implementation edit does not invalidate a compatible saved result. This does
not promise compatibility with future semantic changes: retain supported readers
or add an explicit versioned reader when such a change is introduced.

Preparation/count/seal/execute and fixture-response import remain bound to the
prepared implementation. The qualified operation entry also checks its selection's
integration hashes before these mutations. Portable execution checks current code
at entry and before each request. Historical read success is never permission to
resume an old job under changed code; use its independently trusted original
deployment or an explicitly designed continuation. Never repin saved hashes or
replay an uncertain request to make a job pass. Legacy formats outside the table
require an independently trusted retained verifier, not execution of archived code.

Code relocation does not relocate source evidence. Saved package/run/receipt paths
still need their existing evidence; moving those artifacts is a separate migration.
New handoff creation remains bound to its current deployment. Reverification of an
existing handoff uses recorded producer locations only as historical metadata.

## Production routing: Phases 4, 5 and 10

Phase 4: use the existing retrieval references. Readable body, original manuscript PDF and advertised supplements are separate obligations. Invoke `fetch_fulltext.py` with `--evidence-dir` for this route. Preserve browser/other-route downloads and diagnostics in new attempt directories too. Record attachment discovery as not inspected, inspected with none listed, or advertised with each attachment retrieved/missing. Validate article identity and version as an operator before declaring any acquired file accepted. A helper exit, HTTP status, hash or parseable PDF is not scientific identity verification. Retain the original downloads, including non-PDF attachments; their extraction is deferred.

For every new production ingest retaining a PDF, run adapter `prepare`, then use the registered `paper_workflow` capability for actual phases. In Hermes its tool binding is `paper_workflow`; do not replace it with generated shell pipelines or a second executor. Scope defaults to every physical page and all five channels. Figure-only/selected-page diagnostics cannot satisfy this route. Acquisition and extraction failures remain holds; do not silently replace failed extraction with an unqualified body-only ingest.

Phase 5: produce a verified source-only v1 handoff as the input to qualified figure/table enrichment. Follow `qualified-enrichment.md` before treating the new production route as complete; the final paper points to the v2 handoff and annotated export, not the intermediate v1 handoff. Read the final handoff's exact `summary.txt`, `facts`, retained acquisition dispositions, qualifications and source material. `documents[].pages` identifies original physical page imagery and page directories (`native-text.txt`, `native-text.json`); `documents[].candidates[].regions` and `logical.elements[].ordered_source_fragments` retain crop fragment order. `documents[].requests` exposes classification/association files and call evidence; candidate classification observations remain model observations. Resolve these package-relative paths against `package`, not the paper page. Do not infer scientific findings from counts or mechanically generated labels.

When visual inspection is necessary, use the dedicated `paper_vision_inspect` binding, supplying original pages and ordered crop fragments with precise questions and a new inspection attempt. Its deployment pins the inspection model; text-only operators consume saved findings, not pixels. Same-model inspection is not independent verification. Supply its saved inspection directory to report/finalize/summary. Inspection input coverage is distinct from findings and human acceptance. There is no requirement for manual human crop approval on every future ingest; agent/human scientific review still applies. Historical acceptance never transfers to new output.

If acquisition or required PDF extraction is incomplete, keep `needs-ingest: true`, record the acquisition/extraction hold and any explicit decision to draft only source-limited material, and retain `needs-enrichment: true` when appropriate. Do not present that draft or a fixture handoff as completed ingestion. Missing/failed advertised acquisition, uninspected attachments, incomplete PDF extraction, uncertain requests and fixture/replay evidence remain holds. A retained non-PDF supplement is different: its extraction is deferred by this route, so deferred extraction alone is a visible limitation, not an automatic completion blocker. The retention manifest and handoff preserve that input and its deferred disposition; handoff limitations identify it explicitly. The operator must record an explicit source limitation in the paper for any scientific claim depending on unread non-PDF data. Mechanical completion does not establish that such data were read or that the claim is supported.

In the existing Ingest log, add an unformatted line, relative to the paper page:

    Source package: ../relative/source-run/handoff/handoff.json

Keep source version, URLs, acquisition limitations and scientific review decisions in that log. Add no frontmatter fields. Local retention is not external archival; existing source-archive requirements remain separate. Never invent R2 pointers.

Phase 10: for new retained-PDF production ingests, source and enrichment verifier options are mandatory, including queued PAGE_READY checks. Use the PDF interpreter with PyYAML available:

    <pdf-python> -B <scripts>/verify_ingest.py <bare-slug> --instance <absolute-instance> --require-filled --source-package-handoff <absolute-v2-handoff.json> --source-package-method <scripts> --require-enriched-source --enrichment-integration <scripts> --enrichment-root <scripts>

Keep the exact v2 `qualifications.txt` text in the paper and add `Annotated enrichment: <relative-annotated.html>` beside the source-package pointer in its Ingest log. See `qualified-enrichment.md` for scoped downstream use and the v2 construction command. Source-only v1 verification remains available for historical handoffs, not as a bypass for this new route.

The verifier revalidates the saved launcher/process receipt, current package, retention manifest, exact generated facts/summary, and paper identity fields. A prior `complete=true` field is insufficient. `--page-only` retains existing queue/wiring behavior but does not bypass source checks. `--offline` skips canonical network identity only; legacy callers without the new options keep their existing behavior. No successful mechanical check establishes scientific acceptance or exhaustive recall.

## Acquisition HTTP evidence

    <python> -B <scripts>/fetch_fulltext.py --doi <bare-doi> --evidence-dir /absolute/new-acquisition --out /absolute/new-acquisition/derived/paper

The evidence directory must not exist; its parent must exist. Output paths must be absolute and beneath its `derived/` directory. Files are created exclusively. Each retry has a new `attempt-NNNNNN` directory, containing `request.json` and `complete.json` or `error.json`. Every received HTTP response, including redirects, has `response-NNNN/response.json`, exact `body.bin`, and a body SHA-256 record. HTTP errors are recorded before fallback; a later success does not replace them. Status survives a failed body read; exposed partial bytes are explicitly marked partial. A hard interruption can leave only request/status evidence: that is unknown/incomplete, not success.

All HTTP paths in the helper go through this recorder in evidence mode: Europe PMC gate, PMC XML, EPMC PDF, bioRxiv version lookup, Jina, Wayback API/snapshot, PMC figure page/images, and the formerly direct DOI HEAD request. urllib redirects are captured individually. Without evidence mode the legacy retrieval ladder and output behavior remain available. A persistence failure is not swallowed as a quiet retrieval miss.

No authentication or cookie handlers are added; no request/response headers or exception message text are retained. Credential-bearing URLs are rejected, not silently rewritten; supply public source/discovery URLs. These are anonymous public retrieval routes. Do not use the helper for authenticated or signed-URL downloads. Caller-supplied browser diagnostics must be scrubbed of credentials/authentication headers before retention; record that limitation instead of claiming byte-exact raw responses. If a tool cannot expose response bytes, use `raw_response: unavailable` and describe the limitation. Do not infer missing historical times from filesystem metadata.

This recorder does not cover browser, paperclip, shell utilities or other tools. The operator must preserve their exact original downloads, unique-attempt diagnostics, status/exit evidence and exposed raw responses separately. Never overwrite a failed attempt. Do not claim a browser raw HTTP response exists when only a download or screenshot was available.

## Acquisition manifest v1

`source_package.py prepare` consumes a JSON object with exactly these root fields:

- `schema`: `acquired-sources-v1`.
- `article`: `slug`, exact page `title`, `doi` (bare identifier or null), `pmid` (same JSON scalar type/value as page frontmatter, or null), `version` (explicit string). These are operator-verified claims, not adapter scientific conclusions.
- `files`: accepted local originals/readable body files. Each has unique safe `id`, absolute `path`, expected `sha256`, original `filename` basename, `role` (`manuscript`, `supplement`, `body`), `format` (`pdf`, `other`), public `source_url`, public observed `discovery_url`, matching `article_slug`, and `identity_verification: {"status":"operator-verified","basis":"source-backed title/version/attachment association check"}`. PDFs may supply expected `page_count`. Manuscripts must be PDFs. Use manuscript/supplement roles for PDFs; a separate body file records the body-text obligation. Do not duplicate bytes as multiple files; record URL aliases in acquisition evidence. No `pages`/`channels` override is allowed.
- `attempts`: each has unique safe `id`, `route`, `outcome` (`retrieved`, `failed`, `unknown`), public `source_url`, `observed_at` (actual observed timestamp or `not-recorded`), `raw_response` (`available`, `unavailable`), `limitation` and `artifacts` (list of absolute `path` plus `sha256`). Enumerate every artifact from every helper/other-route attempt, including failed responses, status records and diagnostics, not just the final successful download. Empty artifacts require an explicit unavailable-response limitation. Original filenames/roles are preserved on `files`; numbered retained diagnostic filenames avoid collisions.
- `obligations`: exactly the `body` and `manuscript` dispositions. Retrieved: `{"status":"retrieved","file_ids":["main"]}` with all matching-role files. Missing: `{"status":"missing","attempt_ids":["attempt-id"],"disposition":"actual reason"}`. An unattempted missing source can use an empty attempt list, but remains a hold.
- `attachments`: `status` is `not-inspected`, `none-listed`, or `advertised`; `items` is always a list. Inspected states require the public `inspected_url`; advertised requires one item per observed attachment. Each item has safe `id`, observed public `observed_link`, advertised `filename`, and either `status: retrieved` plus `file_id`, or `status: missing` plus `attempt_ids` and explicit `disposition`. Every supplement file must occur exactly once. Retrieved/missing can coexist; no silent attachment loss.

Example acquired file (replace paths/hash/metadata with actual values):

```json
{"id":"main","path":"/absolute/acquisition/original.pdf","sha256":"<actual-sha256>","filename":"original.pdf","role":"manuscript","format":"pdf","source_url":"https://example.org/article.pdf","discovery_url":"https://example.org/article","article_slug":"paper-slug","identity_verification":{"status":"operator-verified","basis":"Title, version and article content checked against Phase 1"}}
```

Run:

    <pdf-python> -B <scripts>/source_package.py prepare --input /absolute/acquired.json --output /absolute/new-source-run --application-endpoint https://deployment.example/v1/chat/completions --max-application-posts <explicit-integer-budget>

The caller supplies endpoint and budget, not shared host constants. Output retains exact input JSON, all declared originals/diagnostics, hashes, non-PDF dispositions, `retention.json` and accepted-method `scope.json`. Hashes/page counts are checked before workflow preparation. No approval is generated. Use a dedicated retention directory such as `<article-run>/retained`; put workflow, handoff, enrichment and attempt directories beside it, never inside it. The entire retention output tree is hash-bound, so adding a workflow package beneath that directory invalidates retention even when all original bytes are unchanged. A source directory is append-never/reuse-never: even a partial failed preparation is preserved; use a new directory only after resolving the cause. The adapter refuses traversal, symlinks, hardlinked files, duplicate identities/bytes and output reuse. This is not a hostile-concurrent-filesystem security boundary.

## Explicit workflow gates

Replace placeholder paths with absolute values; each operation needs its own new attempt directory; missing parent directories are created safely. Attempts stay outside package, original inputs and report output. Deployment config supplies the trusted method/interpreter; the scope supplies endpoint/budget. Only the registered workflow tool runs phases in production.

Prepare, count and seal the initial phase in one offline call:

```json
{"operation":"prepare","scope_path":"/absolute/new-source-run/scope.json","output_dir":"/absolute/new-package","processor_cache":"/absolute/deployment/processor-cache","attempt_dir":"/absolute/attempts/prepare"}
```

The receipt reports the next step. Read the phase-local plan, count and seal evidence and review the exact bound inputs, overflow dispositions, deployment route and remaining budget. A responsible parent/operator separately authors approval against the seal. Never edit the unapproved template in place or set approval as a consequence of counting. Actual authorized execution is a distinct tool call, not an adapter operation:

```json
{"operation":"execute","package_dir":"/absolute/new-package","phase":"initial","approval_path":"/absolute/approvals/initial.json","authorize_posts":true,"timeout":14400,"attempt_dir":"/absolute/attempts/execute-initial"}
```

After reviewing initial outputs, call `prepare-stage` with `phase: classification` and the same processor cache. It counts and seals the phase; review its inputs and separately author classification approval before explicit execution. Do the same for association with its independent approval. Empty phases write sealed, zero-request completion evidence automatically, without a processor, approval, session or POST. This records an empty request roster, not proof that the source contains no content. Count remains the accepted full multimodal count; only measured overflow permits the method's existing reduction. Never trim or substitute unapproved input to avoid overflow.

```json
{"operation":"prepare-stage","package_dir":"/absolute/new-package","phase":"classification","processor_cache":"/absolute/deployment/processor-cache","attempt_dir":"/absolute/attempts/prepare-classification"}
{"operation":"prepare-stage","package_dir":"/absolute/new-package","phase":"association","processor_cache":"/absolute/deployment/processor-cache","attempt_dir":"/absolute/attempts/prepare-association"}
{"operation":"finalize","package_dir":"/absolute/new-package","inspection_dir":"/absolute/new-inspections","attempt_dir":"/absolute/attempts/finalize"}
```

If offline preparation stopped after writing its phase plan, resume with `seal`, the same `package_dir`, `phase`, `processor_cache`, and a new external attempt directory. It revalidates saved evidence, skips completed counting/sealing, and reports the next step. A partial count or incomplete preparation remains a hold; preserve it and resolve the cause before creating a new run. Never repeat `prepare` against an existing output. The separate `count` operation remains available for inspection before sealing. An optional `report` before execution describes incomplete work (normally exit 1); that is not spending authorization.

The two prepare-stage examples belong at their respective gates, not adjacent unconditional calls. Omit `inspection_dir` if none was supplied; do not supply a fictitious path. `timeout` is tool wall-clock time, independent of the accepted method's fixed 1,200-second request timeout and 65,536 completion allowance. Choose sufficient wall time for an explicitly authorized serial phase. Persistent overflow, unknown reservations, partial/failed phases, logging failures or hard-killed children remain holds. Inspect process/phase evidence; do not retry/resume consumed or possibly posted requests. New authorization for a genuinely new run is a parent decision.

For historical packages, only `summary` to new external output/attempt directories is permitted. Report/finalize mutate machine outputs and must not be pointed at old evidence. Summary success means successful export; `requested_work_complete: false` still means incomplete work.

## Verified distillation handoff

Save the actual code-owned attempt `result.json`, not an operator reconstruction or a copied model summary. After execution/finalization, obtain a fresh read-only `summary` in external output and attempt directories. A source-first HTML report may add display-only `review_overlay` fields to its state; use the canonical summary receipt for exact handoff revalidation. Do not strip fields, edit old receipts, relax validation or rerun extraction to remove that difference.

    paper_workflow: {"operation":"summary","package_dir":"/absolute/new-package","output_dir":"/absolute/source-summary","attempt_dir":"/absolute/attempts/source-summary"}

If inspection evidence was used, supply its actual directory to this summary too. A summary can describe incomplete work, which remains a hold. Build the intermediate source-only v1 handoff:

    <pdf-python> -B <scripts>/source_package.py handoff --retention /absolute/new-source-run/retention.json --package /absolute/new-package --launcher-result /absolute/attempts/source-summary/result.json --method /absolute/trusted-method --output /absolute/new-handoff
    <pdf-python> -B <scripts>/source_package.py verify --handoff /absolute/new-handoff/handoff.json --method /absolute/trusted-method

The adapter invokes the explicitly trusted accepted method's read-only `final_state` and `operation_evidence` validators. It reconstructs the reporting state, checks the saved process/receipt invocation and every bound artifact, compares the retained scope, and uses `facts.json` and the exact generated summary. It does not run a workflow phase, synthesize counts or trust narrative assertions. The handoff binds method code/assets, acquisition retention, launcher attempt, package inventory and any supplied inspection evidence. Revalidation detects subsequent additions/changes, not only missing files. Paths are explicit and must remain available; relocation requires fresh evidence at the new binding, not editing old receipts.

`handoff.json` includes the state documents, sources/dispositions and facts plus exact paths; sibling `summary.txt` is byte-equivalent UTF-8 text from the generated summary. Physical retention/inventory is separate from extraction coverage; input inspection coverage is separate from findings. Mechanical completion, crop/scientific review and human acceptance are separate decisions. Missing historical clocks remain `not-recorded`.

Offline tests may add `--test-only-root /absolute/new-test-root` to handoff. All retention/package/launcher inputs and handoff output must lie beneath it, and the package must carry the method's explicit fixture flag. The handoff is labelled `test-only`, reports holds, and always has `production_complete: false`. Even structurally complete replay is rejected by production `verify` and `verify_ingest.py`; this option is not a production fallback.

Exit 0 from adapter preparation means retained inputs/scope, not extraction. Exit 0 from test-only handoff means verified fixture plumbing, not completion. Exit 0 from production handoff/verify means all checked mechanical/source obligations hold; scientific review remains external. Exit 2 indicates setup/invariant/hold failure; failed output directories are never deleted or reused.
