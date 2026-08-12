# Convention: frontmatter schema

Every page opens with a YAML frontmatter block, then a markdown body. The
frontmatter is the page's structured data; the body is its prose.

The schema is a **convention enforced by skills and lint** — not a database
constraint. The files stay plain markdown that any tool (Obsidian, git, a
plain editor) can read. Authoritative source: `DESIGN.md` §2.3.

## The shared spine

Every page, regardless of kind, carries these fields:

| Field | Meaning |
|---|---|
| `kind` | One of the twelve page kinds (see `page-kinds.md`); must match the directory |
| `slug` | The page identity — unique across the whole brain |
| `title` | Human-readable title |
| `importance` | Research-salience score in `[0, 1]` (see `importance-scoring.md`) |
| `links` | Typed-link list to other pages (see `graph-and-links.md`) |
| `tags` | Free-form tags; some tags feed `importance` |

## Per-kind fields

Beyond the spine, each kind adds its own fields. Identifiers
(`doi`, `pmid`, `arxiv`, `biorxiv`) are **first-class** so a page resolves to a
real-world object. Example — a `paper`:

```yaml
---
kind: paper
slug: paired-antibody-lm-scaling
title: "Scaling paired antibody language models"
status: published        # published | preprint
doi: 10.1234/example.5678
pmid: 39876543
authors: [people/alice-example, people/a-collaborator]
venue: Nature Immunology
year: 2026
importance: 0.82
links: [methods/preferential-masking, concepts/repertoire-drift]
tags: [methods-paper, key-citation]
---
```

A `paper` carries `status` (`published`, `preprint`, or `unknown`) —
peer-reviewed and preprint are one kind separated by this field, not by
directory (`page-kinds.md`). `unknown` is the transient state for pages
whose publication status the ingester could not determine; the `maintain`
pass resolves them. Its identifiers are first-class: `doi` is the primary
key (every paper and every bioRxiv/arXiv preprint has one); `pmid`, `pmcid`,
`arxiv`, and `biorxiv` are carried where available.

A `paper` may also carry queue and provenance fields:

| Field | Meaning |
|---|---|
| `needs-ingest` | `true` if the page is a stub awaiting full ingestion; `false` (or absent) once `paper-ingest` has filled it in. Producers (`grant-ingest`, future `paper-ingest` redesign) set this; the consumer `ingest-pending-papers` drains the queue. |
| `cited_by` | List of `grants/<slug>` and `papers/<slug>` references that cite this paper. Append-only across ingests — paper-ingest preserves the existing list when filling a stub. The future paper-side threshold logic reads this. |
| `ingest_attempts` | Integer counter, bumped on each `paper-ingest` failure. |
| `last_ingest_attempt` | Date of the most recent attempt. |
| `needs-enrichment` | `true` if the distillation is partial — abstract-only, or from a preprint rather than the published version. Cleared when a full published full text is distilled. The embargo re-check sweep (`skills/paper-ingest/scripts/embargo_recheck.py`) re-tests these pages for newly available full text. |
| `fulltext_source` | Provenance tag recording where the distilled full text came from: `pmc-xml` \| `epmc-pdf` \| `biorxiv-jina` \| `biorxiv-browser` \| `publisher-jina` \| `nature-browser` \| `wayback` \| `paperclip-biorxiv` \| `paperclip-arxiv` \| `paperclip` \| `arxiv-html` \| `provided-pdf` \| `abstract-only`. Printed by `skills/paper-ingest/scripts/fetch_fulltext.py` on every retrieval; paper-ingest Phase 4 copies it into the page. Enables targeted enrichment queries ("every page whose text is `biorxiv-jina` or `abstract-only`") in one grep instead of parsing Ingest logs. Absent on pages ingested before 2026-08-05. The `paperclip-*` tags (local mirror full text) and `arxiv-html` (direct arxiv.org/html curl + regex extraction) were added 2026-08-12; a source-agnostic `paperclip-full` tag was proposed and rejected in favor of source-specific tags. |
| `tags: [stub]` | Marks a page that has only frontmatter + a placeholder body. Removed once filled. |

Stubs are valid `paper` pages — they resolve to a real-world object via their
citation entry even before DOI resolution — and they accumulate citation
edges in `cited_by` from any skill that touches them. The `## Ingest log`
section of a stub records per-attempt failure detail so successive runs of
`ingest-pending-papers` don't blindly retry the same broken DOI lookup.

Other kinds carry the fields their job needs — a `hypothesis` carries its
evidence edges, a `task` carries a due date. When adding a field, prefer an
existing name over a synonym, and record new per-kind fields here.

## The `person` kind

A `people/` page is a curated profile of an author or collaborator. The
shared spine applies; beyond it, a person page may carry:

| Field | Meaning |
|---|---|
| `role` | Free text — `PI`, `Staff Scientist`, `student`, `postdoc`, `collaborator`, etc. |
| `affiliation` | `institutions/<slug>` — primary institutional home (e.g. the university) |
| `orcid` | The author's ORCID, when known |
| `author_on` | List of `papers/<slug>` — the papers this person is an author on |

Lab-membership fields (optional; added 2026-07-30 — see
`skills/brain-schema-evolution/references/lab-management-expansion-2026-07.md`):

| Field | Meaning |
|---|---|
| `member_of` | `institutions/<slug>` — the lab(s) this person is a member of. Distinct from `affiliation`: a lab member's affiliation is the university, their membership is the lab |
| `lab_status` | `current` \| `alumni`. Only meaningful alongside `member_of`. Alumni keep their pages and edges — the historical record persists |
| `pillar` | Lab pillar, free-text token (e.g. `ai-research-engineering`, `applied-ai`, `repertoire-scale-immunology`) |
| `pillar_role` | `lead` \| `co-lead` \| `member` |
| `expertise` | Short capability list — the budget-justification and who-can-do-what substrate |
| `works_on` | Typed edge list to `projects/<slug>` — distinct from `links:`, same pattern as `author_on:` for papers |

Relationship distinctions live in these fields, never in directories: "which
people are lab members" is a query over `member_of:`, not a separate kind.

The `author_on:` field is the typed forward edge from the person page
back out to the papers they appear on. It is **distinct from `links:`**
(the generic graph-edge collection on the spine): `author_on:`
specifically carries the authorship graph, the way `cited_by:` on a
paper specifically carries the citation graph. The split keeps each
typed graph queryable on its own without scanning `links:` for which
edges happen to be authorship.

`paper-ingest` writes `author_on:` when a paper is ingested with this
person as an author and the page already exists (Branch 1 of Phase 8).
For authors **without** a page, the same Phase 8 instead writes to
`people/_ledger.yaml` — see `author-ledger.md` for the contract that
governs which authors get a page vs. a ledger entry.

## The `grant` kind

The `grant` page is shared by `grant-ingest` (ingesting a submitted or reviewed
grant) and the grant-writing cluster (`grant-plan` and downstream). Beyond the
spine it carries:

| Field | Meaning |
|---|---|
| `funder` | `institutions/<slug>` — the funding body |
| `mechanism` | Free text — `R01`, `R21`, or a foundation program; not an enum |
| `role` | `PI` \| `co-PI` \| `co-I` \| `consultant` |
| `status` | The lifecycle state — enum below |
| `deadline` | Next actionable deadline; the attention contract reads it |
| `score`, `percentile`, `submitted`, `decision_date` | Set once the grant is reviewed |
| `sources` | One entry per package document or NOFO (`raw-source-archive.md`) |

The `status` enum, in lifecycle order:

- `planned` — on the radar, not yet started.
- `drafting` — a grant-writing engagement is open; `grant-plan` created the
  page and the cluster is drafting it. Carries deadline pressure.
- `shelved` — started, then postponed or abandoned (the idea did not survive
  the `grant-plan` Aims filter, needs preliminary data that does not exist,
  etc.). Inert to the attention contract: **`deadline` is cleared when a grant
  is shelved**, so it stops nagging. The page stays queryable and revivable;
  the reason lives in its `## Drafting log`.
- `submitted` — sent to the funder.
- `under-review` — with the study section or funder.
- `scored-not-funded` — reviewed, not funded.
- `not-discussed` — submitted, but scored below the discussion threshold;
  the study section did not score it. Distinct from `scored-not-funded`
  for resubmission-planning purposes.
- `funded` → `active` → `closed` — awarded, running, completed.

## The `project` kind

A `project` is a multi-paper research thread. Beyond the spine it may carry
research-state fields (added 2026-07-30 — see
`skills/brain-schema-evolution/references/lab-management-expansion-2026-07.md`):

| Field | Meaning |
|---|---|
| `status` | Lifecycle state — e.g. `active`, `paused`, `complete` |
| `personnel` | List of `people/<slug>` currently pushing the project forward |
| `funding` | List of `grants/<slug>` supporting the work |
| `milestones` | List of `{name, date, state}` entries — attributes of the project, never first-class pages (the graph-hub test) |

These fields exist so a progress report can be answered from the graph.
Population and automated maintenance are **deferred** until ingestion-driven
updates exist; stale state is worse than no state.

## The `concept` kind

A `concept` is a **persistent, cross-cutting research thesis or lens** — one of
your human's living bets, drawn on by several projects and grants and never
graduating (it exports crystallized children but does not itself move). Concepts
are many-to-many with the applied layer and finer-grained than threads (expect
more concepts than projects). Beyond the spine:

| Field | Meaning |
|---|---|
| `status` | `active` (evolving) or `dormant` (not currently evolving). Optional; defaults to `active`. |
| `related_concepts` | Typed edge list to sibling `concepts/<slug>` — recorded intersections/relationships. Optional. |
| `thesis_updated` | `YYYY-MM-DD` — the date the Thesis/Frontier prose was last (re)synthesized. Set by `concept-synthesis` / `topic-synthesis` at authoring; refreshed when a Thesis rewrite lands. Drives `concept-refresh` (a concept with ≥3 shifts dated after `thesis_updated` is due a re-synthesis proposal). |

Body anatomy (Thesis / Frontier / Open questions / Shifts) is canonical in
`synthesis-layer-pages.md`.

## The `hypothesis` kind

A `hypothesis` is a **candidate crystallization in the proving-ground**: it enters
from an auto-detected concept intersection or a manual seed, is worked via
conversation, and exits by **promotion** to a project/grant or by being
**killed** (retained as a graveyard entry, never deleted). Beyond the spine:

| Field | Meaning |
|---|---|
| `status` | **Required.** `open` (in the proving-ground), `promoted`, or `killed`. |
| `origin` | `detected` (minted by the synthesis engine) or `seeded` (your human initialized it). Optional. |
| `promise` | List of the promise criteria it argues, each one of `Beat` / `Unlock` / `Scale` / `Explain`. Optional. |
| `draws_on` | Typed edge list to the `concepts/<slug>` whose intersection birthed it. |
| `killed_reason` | One-line cause of death. **Required when `status: killed`** (the graveyard). |

Its evidence graph is the existing `supports:` / `refutes:` edges (papers/concepts
point at it); the hypothesis sees them as derived backlinks. Body anatomy is
canonical in `synthesis-layer-pages.md`.

## The `conversation` kind

A `conversation` is a **captured discussion** — a science-driven back-and-forth,
an explainer of a dense paper, or a fit-assessment — distilled to a page on a
manual trigger (`conversation-capture`). It may be anchored on the page(s) it is
about, or free-standing. Beyond the spine:

| Field | Meaning |
|---|---|
| `mode` | **Required.** `discussion`, `explainer`, or `fit`. Sets the body shape and the forward-chaining. |
| `about` | Typed edge list to the central-subject page(s), `<kind-dir>/<slug>`. **Optional and often absent** — a free-standing discussion has none; an `explainer` almost always names one paper. |
| `status` | `open` (may be revisited) or `settled`. Optional; defaults to `open`. |
| `verdict` | `fit`, `no-fit`, or `undecided`. **Required when `mode: fit`** — the decision-log payload (mirrors the `hypothesis` `killed_reason` rule). Absent otherwise. |
| `channel` | Free provenance of where it happened (`tui`, `telegram`, …). Optional. |
| `date` | The conversation date. |

`about:` is the *central-subject* edge; the spine `links:` carries everything
else the conversation touches. The raw session transcript is archived to R2 and
recorded as a `sources:` pointer (`raw-source-archive.md`) — the page is a
distillation; your human's key phrasings are preserved verbatim in quote blocks
(`_output-rules.md`). A `no-fit` verdict is retained as a decision record, never
discarded. Full design lives in the instance's private `docs/specs/`.

## The `interaction` kind

An `interaction` is a **documented interaction event** — a lab meeting, 1:1,
conference talk, email thread, or call. (Kind renamed from `meeting`, and
`attendees:` renamed to `participants:`, 2026-08-01 — see
`skills/brain-schema-evolution/references/email-modality-2026-08-01.md`.)
Beyond the spine:

| Field | Meaning |
|---|---|
| `channel` | How the interaction happened — `in-person`, `video`, `phone`, `email`. Free text, not an enum (the `grant.mechanism` precedent). Optional; absent on pages predating the rename — historical channels are unrecorded and must not be fabricated |
| `participants` | List of `people/<slug>` who took part |
| `date` | The interaction date; for an email thread, the first message date |
| `granola_id` | Granola meeting ID, when sourced from Granola — the dedup key for `granola-meeting-sync` |
| `sources` | Pointer(s) to the archived raw source (transcript JSON, email messages) — `raw-source-archive.md` |

Most interaction pages are meetings ingested from Granola; email threads earn
pages only through the notability gate (`conventions/quality.md`) — bulk
email is a source stream, not a page population.

## Synthesis-layer edges on projects and grants

A `project` or `grant` may additionally carry two forward edges up into the
synthesis layer:

| Field | Meaning |
|---|---|
| `rests_on` | Typed edge list to the `concepts/<slug>` the page draws on. |
| `promoted_from` | Typed edge list to the `hypotheses/<slug>` it crystallized from, if any. |

These are added by the seeding/synthesis operations (a later spec), not
hand-maintained. A concept's crystallized children and a hypothesis's promotions
are the **derived backlinks** of these edges — never written by hand.

## Discipline

- The directory and `kind` must agree.
- `slug` is the identity — never reuse one, never derive meaning from the path
  beyond the kind directory.
- Skills *enforce* this schema; they do not duplicate the character (`SOUL.md`).
