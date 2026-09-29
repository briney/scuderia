# Article archive retention

Source files and retained text belong in the configured external cache and R2
article package. The brain retains scientific Markdown with a compact remote
`Article archive:` locator only. Full publication/completion receipts, object
hashes and verification records belong in R2, not JSON sidecars in the brain.
Do not embed figures, registers or local source directories.

Modern packages use manuscript-article-package-v1. They record original source
hashes, readable manuscript locations, draft/review, optional inspection outcomes,
prior archive qualifications and the exact page snapshot. This is focused
manuscript review, not a claim of exhaustive figure/table extraction.

`publish` uploads immutable content-addressed objects and the full publication
receipt, verifying remote bytes before applying the page. The receipt locator is
assigned before snapshotting to avoid a circular page/manifest hash dependency:
`Article archive: r2://<bucket>/<prefix>/receipts/<job-id>-<revision>.json`.
The returned local `receipt` path is external working storage for verification,
not a file to copy into the vault or commit. Never manufacture archive locators,
hashes or publication pins. Existing local receipts are read-only compatibility
inputs; migrate them only after upload/readback, replace their page pointers with
content-addressed remote receipt locators, and preserve all scientific prose.
Refresh downloads receipts and sources into external storage using the configured
trusted archive destination. Old packages and their snapshots remain unchanged.
A failed upload can resume independently of drafting or inference. Publication and
required graph/author/bibliography integration have separate pending states.

Ordinary refresh restores verified originals through `sources`, preserving previous
scientific products, corrections and receipt references. Historical archive formats
have separate read-only validators outside the bound skill; their execution
procedures are not instructions for a new job. A source/version mismatch holds
for explicit reconciliation. Never silently substitute a preprint/published twin.

A receipt-only relocation leaves historical page snapshots immutable. Legacy
completion validators still describe those original snapshots and local-pointer
layout; use them on preserved external historical artifacts, not as acceptance
gates for a relocated live page. Ordinary source restoration supports both receipt
formats. The modern page verifier accepts an exact hash-pinned receipt-pointer
relocation while still rejecting any other change to the archived page bytes.

For historical reuse, the runtime validates manifest identity before restoring
selected originals and retained manuscript text. Old extraction/enrichment
products remain in their immutable archive, referenced by provenance; they are
not downloaded to inspect metadata. Cached originals are verified by hash and
size. A derived body document is not a supplementary original. Identifier
representation (numeric/string PMID) and version spacing/case may normalize;
a different manuscript version or unproven version equivalence still holds.

For newly found attachments, `sources` accepts `supplement_inputs` only after a
manuscript is bound. This appends originals without reading or extracting them
and without resetting manuscript coverage. Restage to include them in a new
archive revision; use the published-page amendment procedure when applicable.
