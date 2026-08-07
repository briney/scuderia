---
name: migrate
description: "Import an existing note collection — Obsidian, Notion, Logseq, Roam, plain markdown, CSV — into the vault. A setup-time onboarding job: map source pages onto the page kinds and the frontmatter schema, convert cross-references to wikilinks, test on a sample, verify."
triggers:
  - "migrate from"
  - "import from obsidian"
  - "import from notion"
  - "import an existing vault"
---

# Migrate — onboard an existing note collection

The vault starts empty. When Bryan already keeps notes somewhere — Obsidian,
Notion, Logseq, Roam, a markdown folder, a CSV — this skill brings that material
in: each source page mapped onto one of the page kinds, given proper
frontmatter, and wired into the graph. It is a one-time, setup-phase job.

> **Conventions:** `conventions/page-kinds.md` (the page kinds and
> directories), `conventions/frontmatter.md` (the schema each page must follow),
> `conventions/graph-and-links.md` (wikilinks and typed edges),
> `conventions/test-before-bulk.md` (sample before bulk), `_brain-filing-rules.md`
> (file by primary subject), `conventions/capabilities.md` (the harness
> contract).

## Capabilities

`brain-read`, `brain-write`, `read-file` (the source corpus). Universal.

## What this guarantees

- The source collection is never modified, moved, or deleted — migration is
  purely additive.
- Every imported page is filed under the kind its primary subject demands, with
  frontmatter matching the schema.
- Source cross-references — wikilinks, block refs, tags — are converted to
  `[[kind/slug]]` wikilinks and typed frontmatter edges.
- The approach is tested on a 5-10 file sample before any bulk run.
- After import, page counts, links, and search are verified.

## Source formats

| Source | Format | Notes |
|---|---|---|
| Obsidian | Markdown + `[[wikilinks]]` | The vault already *is* an Obsidian vault — frontmatter and `[[ ]]` links are native; the work is re-filing pages into the page kinds |
| Notion | Exported markdown / CSV | Nested directories with UUID-suffixed filenames — strip the UUIDs for clean slugs |
| Logseq | Markdown + `((block refs))` | Convert block refs to page-level wikilinks |
| Roam | JSON export | Convert the block tree to pages |
| Plain markdown | A `.md` directory | File each note by subject; add the frontmatter spine |
| CSV | Tabular | One row → one page; a designated column becomes the slug |

## Phases

1. **Assess the source.** What format, how many files, what structure? Read
   enough of it to know what kinds the content spans.
2. **Plan the mapping.** Decide how source pages map onto the page kinds — a
   research note → `note` or `concept`; a literature entry → `paper`; a person
   → `person`; a lab or funder → `institution`. Decide how
   source fields and tags map onto the frontmatter spine. Content with no home
   among the page kinds (personal-life material, lab-state logistics) is out
   of scope — do not invent a directory for it (`page-kinds.md`).
3. **Test on a sample.** Convert 5-10 representative files. File each under its
   kind directory, write proper frontmatter, convert its links. Hold the commit.
4. **Check the sample yourself.** Read the converted pages. Right kind? Spine
   fields present? `kind` matching the directory? Links forward-only and
   resolving? Fix the *approach* — then proceed (`conventions/test-before-bulk.md`).
5. **Bulk import.** Convert the rest, committing in batches so a bad run is easy
   to revert.
6. **Convert cross-references.** Turn every source link into a `[[kind/slug]]`
   wikilink or a typed frontmatter edge — forward only; backlinks are derived
   (`conventions/graph-and-links.md`).
7. **Verify.** Page count roughly matches the source (minus out-of-scope drops).
   Spot-check 5-10 pages. Search the brain for something you know was imported
   and confirm it comes back.

## Filing the imported pages

The source tool's folder structure does not survive the move — the page kinds
do. A page's kind is set by its **primary subject**, not the folder it sat in or
the format it arrived as (`_brain-filing-rules.md`). One dense source note may
split into several pages — a method and the hypothesis it supports — each filed
under its own kind and linked.

## Output

```
Migration — <source format> → vault
  Source:        <N> files
  Sample test:   <N>/<N> converted, links resolve
  Bulk import:   <N> pages, by kind: papers <N>, notes <N>, people <N>, ...
  Out of scope:  <N> source files skipped (no matching kind)
  Cross-refs:    <N> converted to wikilinks
  Verify:        page count ok; search test "<query>" → <N> hits
```

## Anti-patterns

- Bulk-importing before the 5-10 file sample is checked.
- Modifying, moving, or deleting the source files — migration is additive only.
- Dropping cross-references — an unlinked import loses the knowledge graph.
- Filing by the source folder structure instead of by subject and kind.
- Inventing a directory for content that has no home among the page kinds —
  that content is out of scope.
- Skipping verification — counts, spot-checks, and a search test.
