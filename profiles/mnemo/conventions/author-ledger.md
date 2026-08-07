# Convention: the author ledger

A `people/` page is a curated profile, not a graph artifact. Every author on
an ingested paper goes into the paper's `authors:` list as `people/<slug>` —
that contract is set by `paper-ingest` and unchanged here — but a *page*
under `people/` is reserved for authors who are load-bearing for the
research program. The **author ledger** is what tracks every other author:
the `people/<slug>` wikilinks pointing at no page, with the citations that
back them, so promotion to a real page is a counted decision rather than a
fuzzy one.

Authoritative source: `DESIGN.md` §2.4 (the graph layer) and `paper-ingest`
Phase 8 (the producer).

## Why the ledger exists

Paper ingest produces two distinct things for each author. The first is a
graph edge — `papers/<paper-slug>` lists `people/<surname-firstname>` in its
`authors:` field — which forward-only linking
(`graph-and-links.md`) allows even when the target page does not exist. The
second *would be*, in the old design, a stub `people/` page so the wikilink
resolves to a file. The ledger replaces the second thing.

The motivation is curation. A `people/` page implies the mind has something
to say about the person — collaborator, key figure, student, recurring
co-author. A paper with twelve authors typically has two or three that
matter to the brain and ten that are middle-author noise. Auto-creating ten
stub pages per paper clutters the directory and dilutes the implicit
contract that a `people/` page contains useful, hand-curated context.
Tracking those ten authors in a ledger preserves the graph (the count of
papers each name appears on) without paying the page-creation cost.

Decoupling these two concerns also makes promotion deterministic: when an
author's citation count crosses a threshold, the ledger entry is promoted to
a page. No per-author judgment call sitting on the hot ingest path.

## File location

`people/_ledger.yaml`. One file, lives next to the pages it complements.
YAML for human readability and to match the rest of the convention
(frontmatter, the lint script's parser). The leading underscore keeps it
out of the page-kind glob — `_ledger.yaml` is not a brain page.

## Schema

```yaml
# people/_ledger.yaml
# Non-paged authors tracked by `paper-ingest`. See
# skills/conventions/author-ledger.md for the contract.
entries:
  - slug: example-author
    name: "Example Author"
    orcid: "0000-0001-2345-6789"      # optional; captured when CrossRef returned one
    citations:
      - papers/some-paper-2024
      - papers/another-paper-2025
    affiliations:                       # optional; deduped, free-text
      - "Some University"
```

Per-entry fields:

| Field | Required | Meaning |
|---|---|---|
| `slug` | yes | The `<surname-firstname>` form (`page-kinds.md`), ASCII / lowercase / hyphen. Identical shape to a `people/` page slug. |
| `name` | yes | Full display name as it appeared in the source citation. |
| `orcid` | no | The author's ORCID if CrossRef (or another resolver) returned one. **Captured whenever available** — it is the real identity key for disambiguation. |
| `citations` | yes | List of `papers/<slug>` entries — the papers this author appears on. Append-only, deduped. |
| `affiliations` | no | Free-text affiliations seen across the cited papers. Deduped. Useful as a disambiguation hint when two same-slug authors are distinct people. |

No `count` field. The citation count is `len(citations)` — derive it,
don't store it. A stored count silently drifts from the list and corrupts
the promotion gate.

## The promotion rule

When `len(citations) >= 5`, the ledger entry is **promoted**: a
`people/<slug>.md` page is created via `enrich`, and the ledger entry is
removed in the same write. The threshold mirrors the paper-side
`needs-ingest` gate — same number, same one-way semantics, for the same
reason (citation density is a usable proxy for "this thing matters
enough to page").

Promotion is one-way. Once a page exists for the slug, the slug is owned
by the page; subsequent paper ingests update the page's `author_on:`
field directly (Branch 1 in `paper-ingest` Phase 8) and never touch the
ledger again for that slug.

### Inline promotion, no queue

When the threshold fires during a paper ingest, **create the page in the
same run**. People pages have no expensive resolution step — no DOI to
look up, no PDF to fetch, no R2 archive to write — so the cost is just
calling `enrich` with the slug and the seed data from the ledger entry.
There is no `ingest-pending-people` skill mirroring
`ingest-pending-papers`; the paper-side queue exists because paper fills
are expensive, and that justification does not apply here.

### The threshold is the default, not a hard rule

your human curates `people/`. The threshold is the **default automatic
trigger** for promotion — it fires when the system has no other signal —
but it is not the only path to a page. Two manual override paths:

- **Promote early.** your human writes a `people/<slug>.md` by hand (or asks
  the mind to). The next paper-ingest pass sees the page exist, takes
  Branch 1, and the ledger entry (if any) is removed at that point
  rather than at threshold.
- **Demote.** your human deletes a `people/<slug>.md`. The next paper-ingest
  pass sees no page and no ledger entry (since the slug was a paged
  author when the citation was first written), and Branch 3 fires: a
  fresh ledger entry is created with the paper as the seed citation.
  Subsequent ingests re-accumulate the count.

Neither override is automatic. Direct edits to `people/_ledger.yaml`
(adding entries, removing them, editing citations) are also legal — the
ledger is a plain file and your human owns it the way they own SOUL.md.

## ORCID disambiguation

Slug collisions are rare in a 169-page hand-curated set, but they become
inevitable as the ledger grows past a few hundred entries. Common
surname/firstname pairs (Chen-Jian, Wang-Lei) will collide on real,
distinct people. In a ledger, a collision is worse than a page collision
because the citation lists silently merge — no human reads the entries
the way they read a page, so the count climbs from two unrelated authors
and a promotion fires on a non-person.

The rule: **when CrossRef returns an ORCID for an author, store it on
the ledger entry**, even when there is no collision. The cost is one
field; the value is the real identity key being on record before the
collision happens.

On collision (a new ingest produces a slug that matches an existing
ledger entry **and** the ORCID differs from what is stored, or an
existing `people/<slug>.md` exists with a different ORCID in its
frontmatter), disambiguate by suffix:

- **ORCID-disambiguated form:** `<surname-firstname>-orcid-<orcid>`, e.g.
  `chen-jian-orcid-0000-0001-2345-6789`. Explicit and unambiguous; the
  trailing ORCID makes the page or entry self-identifying.
- **Institutional disambiguator:** when no ORCID is available for either
  side, use the affiliation in the slug tail
  (`wilson-ian-oxford` vs. `wilson-ian-cambridge`). Page-kinds.md already
  documents this form.

When a slug under either form is created, the existing entry's slug is
**also** rewritten to its disambiguated form. Two `wilson-ian` entries
become `wilson-ian-oxford` and `wilson-ian-cambridge` — never one
disambiguated and one bare.

## Lifecycle

A ledger entry passes through three states:

1. **Created** by `paper-ingest` Phase 8 Branch 3 — a new author appears
   on an ingested paper, no existing page or entry.
2. **Updated** by `paper-ingest` Phase 8 Branch 2 — subsequent papers
   cite the same author; the citation list grows, deduped.
3. **Promoted** (and removed) when `len(citations) >= 5` — the entry is
   converted to a `people/<slug>.md` page via `enrich`.

The ledger is **transient** by construction: every entry's terminal
state is either promotion (entry deleted, page exists) or stasis (entry
sits under threshold indefinitely). Promoted entries leave no trace in
the ledger — the durable record is the page, not the ledger history.

## The 5-citation threshold is a known tunable

The threshold is fine as a starting default but is not load-bearing on
principle. Authors have a fatter tail than papers — a senior PI's name
appears on many tangential papers in a field, and 5 may catch field
elders while missing a real collaborator who only co-authored 3 papers
that the brain actually cares about.

Tunables to revisit after a few weeks of operation:

- **Flat threshold value** — 5 may be too tight or too loose.
- **Weighting by paper importance** — a citation on a grant-anchored
  paper could count more than one on a tangential ingest.
- **Author position** — first / corresponding / senior position carries
  more signal than a middle-author cite.

Don't over-engineer on day one. Flat 5, all citations weighted equally,
no position handling. Revisit when there is real data to revisit
against.

## Anti-patterns

- **Writing a `people/` page directly during paper ingest** to bypass
  the ledger. Page creation goes through `enrich` after the threshold
  fires, or through a deliberate manual override by your human. Direct
  writes reintroduce the auto-stub clutter the ledger exists to
  prevent.
- **Populating a ledger entry from a paper that has not been
  ingested.** The citations list is the set of `papers/<slug>` whose
  full ingest produced this author entry. A ledger entry citing a
  not-yet-ingested paper has nothing to back it; the count is fictional
  and the threshold gate fires on phantoms.
- **Treating the ledger as durable history.** It is transient — a
  staging area for unpaged authors. Promoted entries are removed; the
  page is the record. A ledger entry that lingers below threshold for
  years is fine and expected; one that *replaces* the page after
  promotion is a bug.
- **Storing a `count` field on entries.** Derive from
  `len(citations)`. A stored count silently desyncs the moment any
  skill appends without updating it.
- **Skipping ORCID capture when CrossRef returned one.** The marginal
  cost is one field write; the value is real disambiguation when the
  collision arrives. Capturing ORCID retroactively requires re-walking
  the source papers' metadata.
- **Mixing ORCID-disambiguated slugs with bare slugs for the same
  collision pair.** Both members of the collision get disambiguated
  together; otherwise the bare slug looks ambiguous and the
  disambiguated one looks aliased.
- **Auto-promoting in bulk during the Stage 3 migration.** The
  migration populates the ledger from existing orphan refs; some
  authors will already exceed the threshold by virtue of cumulative
  history. Auto-creating their pages all at once defeats the curation
  discipline — surface a promote-ready report for review instead.

## See also

- `skills/paper-ingest/SKILL.md` Phase 8 — the producer side of the
  ledger; the three-branch logic that decides between page update,
  ledger append, and ledger create.
- `skills/enrich/SKILL.md` — the promotion consumer; called when a
  ledger entry crosses the threshold.
- `skills/conventions/frontmatter.md` — the `author_on:` field on the
  `person` kind, written by paper-ingest on existing pages (Branch 1).
- `skills/conventions/graph-and-links.md` — `author_on:` as a typed
  forward edge, owned by the person page but written by the paper-
  ingest skill that authors the paper page.
- `skills/conventions/page-kinds.md` — slug conventions for `people/`,
  including the existing surname-first form and the institutional
  disambiguator.
