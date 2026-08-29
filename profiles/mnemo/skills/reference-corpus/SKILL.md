---
name: reference-corpus
description: "Build a new references/ corpus — durable non-graph data."
triggers:
  - "build a reference for"
  - "new reference corpus"
  - "structured corpus of"
  - "compendium dataset"
  - "references/ directory"
  - "reference dataset"
---

# reference-corpus — build a durable reference corpus

The brain has a third content layer beyond graph pages (`concepts/`, `papers/`,
...) and ephemeral `working-docs/`: **`references/`** — durable, structured,
consulted-not-authored corpora that inform the research program but are NOT part
of the knowledge graph (no frontmatter, no wikilinks, no QMD indexing). Use
this skill whenever Bryan asks to *build* a new corpus: "a reference containing
every X", "a structured dataset of Y", "a compendium of Z".

Existing corpora (follow their anatomy as the proven pattern):
- `references/antibody-target-hitlist/` — per-target profiles (580).
- `references/therapeutic-antibodies/` — per-molecule mAb registry (321).
- `references/virus-families/` — per-family virology + per-virus clinical (two-tier).

The per-corpus skills (`therapeutic-antibody-registry`, `target-prioritization`)
own *one* corpus each; `antibody-target-hitlist` is now a reference corpus
without a skill (methodology lives in its `master.md`). This skill owns the *pattern* for
standing up a new one. Read `references/README.md` and
`docs/specs/2026-08-18-references-directory-design.md` before designing — they
are the authoritative contract (anatomy, registry table, changelog format,
promotion rule).

## The standard anatomy

Every corpus is a lowercase-hyphenated subdirectory of `references/`, mirroring:

```
references/<name>/
  README.md            # YAML metadata block + overview + scope decisions + structure + usage
  CHANGELOG.md         # reverse-chronological; each entry = What / Why / Downstream impact
  master.md            # the agent guide: scope, identity, tiers, vocab, citation rules, onboarding
  <records>/           # one record per entity, slug-named .md
  index/               # compiled views over records (by X, by Y) — NEVER a second source of truth
  templates/           # per-record field templates
  raw/                 # raw API/source extracts (small; binaries -> R2 per raw-source-archive)
```

Then register the corpus in `references/README.md` (add a row to the registry
table: name / purpose / status / last-updated).

## The governing decisions to lock with Bryan FIRST (fork-gate)

The anatomy is fixed, but a new corpus always has genuine schema forks that
change every file downstream. Surface them as 2–4 explicit options and get a
decision *before* writing templates — never silently pick (see `ask-user`).

The two forks that recur:
1. **Record granularity / tiering.** Is the record a single entity, or a
   two-tier split (trait-stable anchor + variant-variant detail)? The
   virus-families corpus split *family* (entry/replication/genome — constant)
   from *virus* (disease/geography/transmission — variant). The antibody
   registry split *drug product* from *target*. Find the trait axis along which
   fields are constant vs vary, and split records there — forcing one record to
   hold both cleanly is the classic failure.
2. **Coverage depth.** Two-tier (full depth for the reportable/major entities,
   a compact/honestly-sparse marker for the rare ones) beats uniform full depth.
   A thin record is thin *on purpose*, marked as such, never padded.

## Workflow: pilot-first, always

1. **Gather substrate.** What already exists in the brain? A survey
   (`docs/surveys/`), an existing corpus, or concept pages may already hold the
   roster or the facts — reuse them; don't re-derive. (The virus-families roster
   was seeded from `target-prioritization`'s 148-virus inventory; the
   astroviridae profile was distilled from `concepts/astrovirus-replication-lifecycle`.)
2. **Write the anchors** — README, master.md, templates. Review with Bryan.
3. **Pilot batch of ~3 records** spanning the maturity range (one well-trodden,
   one mid, one sparse/field-relevant). Bryan reviews the *shape* of the pilot
   pages before any scale.
4. **Full sweep**, delegated in batches (see `batch-drain` for the wave pattern),
   ICTV/registry names verified, indexes regenerated from canonical records,
   linter run, committed.

## Cite-or-flag applies here as everywhere

Every substantive claim carries an inline source `(PMID n)`, `(ICTV MSL41)`,
`(CDC)`, `(ViralZone)`, etc. A thin/unconfirmed field is written `Unknown` /
`No data` / `[needs source]`, never a bare assertion. This is the
consulted-data equivalent of the grant-writing liability: uncited reference
records poison grants built on them. Distinguish *fact* from *countermeasure
existence* — the mAb-countermeasure field points to
`references/therapeutic-antibodies/` (plain path); it does not duplicate the
molecule data.

## Pitfalls (from standing up virus-families)

- **`index/` dir must exist before you write into it.** `write_file` creates
  parent dirs, but `open()` in `execute_code` does NOT —
  `os.makedirs(..., exist_ok=True)` first, or FileNotFoundError.
- **Generate the roster from an existing source, never hand-transcribe.** Parsing
  a markdown table: skip separator rows with `set(cell) <= set("-")` (a
  `set(cell) == {"-"}` check misses dash-only cells padded with spaces); check
  `len(cells) >= N` before indexing fixed columns.
- **Tuple unpack arity when aggregating.** If you store
  `dict[key] -> [tuples]` and later `for a, b in ...` while the tuples have 7
  fields, you get "too many values to unpack". Unpack the same shape you stored.
- **Headline counts drift.** A survey saying "148 entries" may parse to 149 rows
  (aggregate rows like "Other lyssaviruses"). Don't force the number; log the
  discrepancy as a compiled-view note.
- **Use current taxonomy.** ICTV/MSL nomenclature changes (megataxonomy split
  *Herpesviridae*→*Orthoherpesviridae*, *Bunyaviridae*→4 families). Canonical
  name = current; superseded names go in an aliases field, never silently used.
- **Relationship fields, not duplication.** A "countermeasure" or "target" field
  points at the owning corpus by path; it never copies rows. Two references
  cross-link, never each hold a copy of the other's data.

## Relationship to other skills

- `brain-schema-evolution` — governs adding *page kinds* (graph). This skill is
  deliberately OUT of that blast radius: references are non-graph, so no linter,
  no QMD, no frontmatter. If a proposed corpus needs graph edges, it's a page
  kind, not a reference.
- `maintain` — the rem-cycle health pass; can flag a reference's stale/changed
  status.
- `bulk-corpus-editing` — bulk edit campaigns over existing large corpora;
  complementary to (not overlapping with) standing up a new one.
- Per-corpus skills — own one corpus each; this umbrella owns the standing-up
  pattern and the cross-corpus conventions.
