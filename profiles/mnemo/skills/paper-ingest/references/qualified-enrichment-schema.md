# Qualified enrichment operation and review schemas

See `runtime.md` for deployment and `qualified-enrichment.md` for the production sequence.

## Operation arguments

Pass these objects to `paper_enrichment`, or save one object for `operate.py`. All filesystem paths are absolute. Each invocation also needs `attempt_dir: <NEW_EXTERNAL_ATTEMPT>`. `offline: true` is required for test-root operations and recommended explicitly for all non-execute operations; non-execute operations install the offline guard regardless.

1. `operation: prepare`, `source_handoff: <VERIFIED_V1/handoff.json>`, `output: <NEW_JOB>`, optional `processor_cache: <ACCEPTED_OFFICIAL_CACHE>` to count and seal in the same offline call.
   The default is every eligible figure/table, not an operator-curated subset. Only an explicitly fixture-marked source handoff may use `test_root: <OWNED_TEST_ROOT>`; this is never production evidence.
2. `operation: count`, `job: <JOB>`, `processor_cache: <ACCEPTED_OFFICIAL_CACHE>`.
3. `operation: seal`, `job: <JOB>`, optional `processor_cache: <ACCEPTED_OFFICIAL_CACHE>` to count if needed. Saved complete counts/seals are verified and reused; interrupted counts and uncertain requests remain holds.
4. Parent reviews the source/payload/count/serving route and separately authors approval from `<JOB>/enrichment/approval.template.json`. The template is deliberately unapproved. Use the current portable approval contract. This module never writes approved booleans, credentials or a post budget for the operator.
5. After separate authorization, use operation `execute` with `job: <JOB>`, `approval: <SEPARATE_PARENT_APPROVAL.json>` and the explicit `authorize_posts` flag set to true. Do not pass `offline`, and never retry consumed requests; explicit continuation is only for never-reserved siblings under the identical approval and original budget. Existing offline environment markers cause refusal rather than being removed.
6. `operation: report`, `job: <JOB>`, `output: <NEW_EXTERNAL_REPORT>`. Report output must not be inside the run or source tree.
7. `operation: review-create`, `run: <JOB>`, `output: <NEW_REVIEW_ROOT>`. To review retained v7 records without production eligibility, use `run: <V7_RUN>`, `kind: v7-run` instead. This supports existing algorithm records without promoting algorithms by default.
8. `operation: review-packet`, `review_root: <REVIEW_ROOT>`, `elements: [<EXACT_ELEMENT_ID>]`, `output: <NEW_PACKET.json>`, optional `max_bytes` (default 1,000,000; maximum 8,000,000). Use `elements: []` for a zero-eligible current job. The packet contains native text, original records, crop/page locators, valid targets and inherited findings. Reduce the explicit roster if too large; nothing is silently truncated.
9. `operation: review-import`, `review_root: <REVIEW_ROOT>`, `packet: <PACKET.json>`, `submission: <OPERATOR_SUBMISSION.json>`.
10. `operation: export`, `review_root: <REVIEW_ROOT>`, `output: <NEW_EXPORT>`. Retain this operation's `result.json`; the enriched handoff checks its actual child exit and exported artifacts. `operation: verify-export`, `export_path: <EXPORT/handoff.json>` revalidates all warnings and evidence but does not waive a production hold.
11. `operation: consume`, `export_path: <EXPORT/handoff.json>`, `element: <ID>`, `target: <JSON_POINTER>`, `purpose: discovery|summary|exact|algorithm-specification`, `output: <NEW_CONSUMER.json>`. Optional `aspects` selects named review aspects for discovery/summary; exact and algorithm-specification use always exposes all six aspects, so requesting text alone cannot hide unchecked units or layout. Optional `qualification` is explicit explanatory text. `source_inspection` names a JSON file with reviewer, reason and evidence, using the same evidence contract as review import. Algorithm-specification inspection requires the owning crop, not native text alone. Consumers must preserve the returned warnings and unknown scope, not copy only `content`.

Historical v7 records remain readable under their original schemas. Current native jobs use `qualified-selection-v2` and the portable prepared/count/seal formats under `enrichment/`; the v7 execute entry refuses before reservation or network access. Fixture response injection is a test-only transport double, not a native operation. Zero-eligible jobs skip count/seal/execute and proceed to review/export.

## Operator review submission

The source packet's canonical SHA256 is `qualified_enrichment.records.digest(packet)` (sorted-key canonical JSON), distinct from its file-byte hash. The native packet operation returns it as `receipt.review_packet_sha256`. Submission shape:

    {
      "schema": "contextual-review-v2",
      "packet_sha256": "<CANONICAL_PACKET_HASH>",
      "reviewer": {
        "kind": "model-operator",
        "identity": "<OPERATOR_RUN_ID>",
        "model": "GLM-5.3",
        "provider": "<ACTUAL_PROVIDER>",
        "check": "<ACTUAL_CHECKED_SCOPE_AND_METHOD>",
        "timestamp": "<ACTUAL_TIME_OR_NOT_RECORDED>"
      },
      "findings": [],
      "coverage": [],
      "resolutions": []
    }

Current dossiers (`uncertainty-dossier-v2`, `portable-review-dossier-v3`) and exports (`qualified-enrichment-export-v2`, `portable-qualified-export-v4`) carry `policy: observed-limitations-v1`. Packets use `contextual-review-packet-v2`. Historical formats retain their original policy and rendering; unknown versions are rejected.

A final current submission adds `assessment` with `usable_evidence` (boolean), a specific `reason`, manifest-bound `source_refs` (`key`, `sha256`), and `unattempted` (exact pending request IDs mapped to specific reasons). Source refs must contain readable nonempty text; for inspected PDFs additionally provide physical `page` and nonempty `inspection`. Use actual source keys/hashes from the packet. Partial reviews may omit the assessment; page readiness requires it. No successful visual response is required. The export exposes `requests_accounted_for`, `requests_successful`, `page_ready` and holds independently; a ready page does not turn failures into successes. Frozen review snapshots never import later sibling results.

New source packages carry `source-readiness-v1`. Their packets expose
`source_readiness.pending`: include these exact namespaced keys (for example
`source:phase:association` or `source:request:<ID>`) in the same `unattempted`
map, along with pending enrichment request IDs. Give a specific deferral reason
for each. Local failed/uncertain source requests retain their original outcomes;
they are not retries or successful extractions. Integrity/fixture holds cannot
be waived by an assessment.

The assessment may also include `source_limitations`, a list of substantive
source limitations supported by the reviewed evidence. Use an empty list when
none is established. Do not hunt for limitations or list generic fallibility,
redundant missing formats, or hypothetical omissions. These statements are
preserved across later assessments, the initial handoff and refresh archive's qualification register;
keep relevant qualifications beside affected claims too. Acquisition and
extraction evidence remains available even when no source limitation is recorded.

Findings require source evidence. Coverage is audit metadata, not a mandatory certification checklist. Empty findings, coverage and page qualifications are valid when no substantive limitation is observed.

Human or orchestrator-imported judgments use `kind: human` or `kind: orchestrator-import` with `model: null` and `provider: null`. Do not relabel existing human findings as newly detected by GLM.

Finding fields: `element_id`, `source_sha256`, `target`, `category` (nonblank open vocabulary), `reason` (specific nonblank text), `stage` (`extraction` or `answer`), `evidence` (list). Optional `competing_readings` contains `{text, evidence}` entries; each needs source evidence.

Evidence entries: `pointer` into that element's packet evidence, `source_sha256`, and `kind`. Native text uses `kind: native-text`, literal `text`, and optional zero-based Unicode `start`/exclusive `end`. A crop uses `kind: crop` with the pointer to its fragment/caption object, without generated text. The importer derives owner, physical page and original crop references.

Coverage entries: `element_id`, exact `target`, `aspect`, `evidence`, `reason`. Aspects are `content`, `source-association`, `notation`, `layout`, `units`, `headers`. Layout/notation/header review requires crop evidence. This is attributed scoped review, not a machine correctness guarantee.

Resolution entries: `finding_id`, `reason`, `basis` (`literal-copy` or `source-inspection`), `evidence`, `agreement` (`unambiguous` or `disputed`), `proposed_value`, `aspect`. `proposed_value` denotes the complete value at the finding's target, not an implicit patch. A literal copy must equal its source selection and have the correct native association. Layout/typography cannot be resolved by native text alone. Crop inspection remains an attributed judgment. Competing readings/disagreement remain unresolved.

### Resolution semantics, revision two

Automatically projected `saved-uncertainty` findings can combine content and structural issues without an exhaustive aspect schema in the frozen record. The conservative rule is therefore crop-backed `source-inspection` for every one of the six existing aspects before that finding can become `resolved-with-attribution`. A native literal copy is rejected for these automatic findings, irrespective of the caller's chosen aspect. A partial set of crop-backed resolutions is retained but leaves the finding unresolved. This uses the deterministic finding's saved-state category/provenance, never keyword classification of its explanation. Coverage and supported content remain available; this is a scoped qualification requirement, not full-paper rejection. Manually imported answer-stage omissions and matching literal-copy resolutions remain representable under the existing evidence checks.

Each attributed proposal is retained. Agreement requires exact canonical JSON equality at overlapping targets, with type differences retained; there is no unit conversion, fuzzy text matching or scientific-equivalence inference. Different values at one target remain unresolved, including proposals under different finding IDs or aspect labels. For parent/child targets, the comparison selects the child's JSON Pointer from the proposed parent value; a missing or unrepresentable child is unresolved overlap, not agreement. Disjoint scopes are not conflicts. Comparisons are applied after collecting all decisions so a later/native/model proposal cannot override an earlier disagreement.

Every consumer view and adjacent readable annotation retains relevant resolution history, including a formerly summary-only ancestor that now has proposals. A proposed change never replaces the original. Even an attributed resolved proposal requires qualification or source inspection for exact reuse when its value differs from its original finding target; coverage cannot waive this condition. A proposal exactly equal to the original does not itself block scoped exact reuse, but its attributed history remains visible. A parent-level proposed change conservatively qualifies affected descendant views; consumers needing narrower resolution should review the narrower target explicitly. The generic adapter qualification register retains resolved findings and complete attributed proposals as well as unresolved findings. Consumers must retain this history, not only `unresolved_findings` or `content`.
