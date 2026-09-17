# Worked example: durable reference data versus graph pages

Load when a compendium or structured corpus appears to need a new page kind.
The reusable decision is to distinguish durable data from a research concept;
private migration history and corpus counts are not execution instructions.

## Apply the identity and graph tests

A large corpus can be durable without every row needing a graph node. A record
with measurements, identifiers and source provenance belongs in a non-graph
reference corpus when it lacks a separate research argument or independent
linking role. Do not bulk-promote records merely because `working-docs/` is
transitory, and do not add a `resource` kind just to accommodate file volume.

`reference-corpus` owns the `references/<name>/` convention: registry/README,
record identity, source provenance, templates and optional changelog. Reference
records are not brain pages; use the owner's non-graph link and metadata rules
rather than adding brain frontmatter or wikilinks by default.

A target that becomes an independently useful research concept can receive a
concept page through its approved authoring workflow. That page points back to
the canonical reference data; it does not replace or duplicate the whole corpus.
A master index can likewise remain data unless it has a distinct graph role.
Status and relationship differences normally use existing fields, not new kinds.

## Preserve sources and assign migration ownership

Keep structured source bodies, identifiers and provenance intact during an
approved relocation. Templates, run prompts, raw-source directories and
sidecars are supporting material, not candidate graph pages by default.

Route corpus setup to `reference-corpus` and use the active deployment's
existing bulk-edit procedure for an approved migration, discovered through the
resolver/capability binding. Check format variants, collisions and inbound
references in a reviewed pilot; do not copy a parallel slug/stub-generation
recipe into this schema example. Paper identity and stubs retain their existing
`paper-ingest` and `paper-stubs.md` owners. No bulk move or promotion is implied
by reading this example.
