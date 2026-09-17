# Convention: bioRxiv / medRxiv retrieval

Before fetching a bioRxiv/medRxiv preprint, load
`skills/paper-ingest/references/preprint-conference-retrieval.md`. That is the
canonical metadata, version, published-twin, and alternate-source procedure;
`paper-ingest` Phase 4 owns acceptance and source-closure requirements.

Resolve metadata separately from full text, using the full DOI and selected
version. Try the actual publisher/repository PDF links; historical Cloudflare
403s are route observations, not a permanent prohibition on direct retrieval.
EPMC PPR links, authorized browser access, and supplied PDFs are conditional
alternatives. Inspect actual API fields and content rather than assuming a
particular response means complete text. A published-version substitution or
justified abstract-only distillation retains `needs-enrichment: true`.

A worker brief points to this owner instead of repeating a competing ladder.
