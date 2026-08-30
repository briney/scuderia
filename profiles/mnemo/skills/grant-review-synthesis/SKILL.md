---
name: grant-review-synthesis
description: Use for grant summary statements and reviewer critiques.
triggers:
  - "ingest a summary statement"
  - "ingest reviewer critiques"
  - "grant review synthesis"
---

# Grant review synthesis

Post-submission review materials — a summary statement, reviewer critiques, a score notice — are a **delta on an existing grant page**, not a new grant package. This skill owns that delta: preserve the already-ingested application prose, add the review outcome, synthesize what study section punished, and propagate the funding state into the research graph.

Use `grant-ingest` instead when the operation includes a new application package or creates the grant page for the first time. Use this skill when the grant already exists and the new material is review/outcome material.

## Workflow

1. **Locate the grant brain-first.** Match by application number, title, PI, funder, and mechanism. Also grep the filesystem for the grant number; search indexes can lag freshly written pages. Never create a second page for the same application.

2. **Archive the review source.** Upload the PDF/DOCX with `role: summary-statement` or `role: reviewer-critique`, record `hash`, `r2_key`, `filename`, `ingested`, and `provenance`, and verify the object before treating it as archived. No binary enters git.

3. **Update review metadata.** Set `score:`, `decision_date:` from the summary-statement release date, `study_section:`, `council:`, `nofo:`, requested start, budget totals, and program/SRO contacts when present. Omit `percentile:` if the statement does not report one — never infer it.

4. **Use the lifecycle state honestly.** The grant schema currently has no `scored-pending-funding` state. If the application was reviewed but the funding decision remains open, use `status: under-review`, set the score fields, and state in `## Review` that the funding decision is pending. Do not mark it `scored-not-funded` or `funded` until there is an actual decision.

5. **Write `## Review`.** Include:
   - overall score, percentile if present, meeting/release dates, council, requested start, and outcome;
   - a component score table when projects/cores are scored separately;
   - SRO resume themes, separated into strengths and weaknesses;
   - a dedicated deep synthesis for the component your human names as theirs — score, reviewer strengths, reviewer weaknesses, and what is actionable;
   - actionable concerns for resubmission, JIT response, or funded-project launch;
   - administrative and budget notes (recommended modifications, missing sharing/authentication plans, hypertext warnings), because these become JIT obligations if the award is picked up.

6. **Annotate the existing verbatim, do not rewrite it.** Add short `> [!critique]` callouts against the exact aim/strategy passages they target. Preserve the application prose intact. If no verbatim science blocks were added or changed, the grant-ingest byte-check is not applicable; record that in the drafting log.

7. **Propagate the state.** Update `RESEARCH.md` funding context and the relevant project pages with the reviewed score and decision state. Create or update person/institution pages only when the review source clears the notability gate.

8. **Verify narrowly when the corpus has legacy lint debt.** Parse the frontmatter of every touched page and run `git diff --check`. If the whole-brain linter fails on pre-existing pages, search its output for the touched paths and report the legacy failure separately rather than blocking the ingest.

9. **Close with the queue truth.** Report how many paper stubs were created and how many existing pages were updated. If the review adds no key citations, say that no `ingest-pending-papers` handoff is needed; do not send your human to drain an empty queue.

## Pitfalls

- A score is not a funding decision. Keep “reviewed, pending funding” distinct from both `scored-not-funded` and `funded`.
- A component score can be strong even when the overall score is only moderate; synthesize both levels instead of flattening them into one verdict.
- Reviewer enthusiasm is not the deliverable — the actionable weakness map is. Prioritize concerns that change the resubmission, JIT response, or launch plan.
- Do not run paper-ingest for references mentioned only inside reviewer prose.
- Do not delete a `_drop/` original until the archive round-trip is verified. For direct attachments outside `_drop/`, leave the attachment in place.
- If `rclone hashsum` is unsupported by the object store, verify a small upload by streaming it back (`rclone cat ... | shasum -a 256`) and comparing against the local hash; record the verified hash in `sources:`.

## References

- `references/summary-statement-update-example.md` — worked example from a P01 summary-statement-only update, including status choice, propagation points, and R2 hash verification.
