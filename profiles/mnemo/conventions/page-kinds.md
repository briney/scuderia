# Convention: page kinds

The brain is one undifferentiated content space — a page is identified by its
`slug` alone. Every page has a **kind**, and the kind determines two things: the
directory the page lives in, and the frontmatter schema it follows
(see `frontmatter.md`).

Authoritative source: `DESIGN.md` §2.2. A mnemo brain is literature-native — papers,
methods, concepts, and hypotheses are first-class; people are real but
de-emphasised.

## The twelve kinds

| Kind | Directory | Holds |
|---|---|---|
| `paper` | `papers/` | A research article — peer-reviewed or a preprint |
| `method` | `methods/` | An experimental or computational technique |
| `concept` | `concepts/` | A persistent, cross-cutting research thesis or lens; never graduates |
| `hypothesis` | `hypotheses/` | A candidate crystallization in the proving-ground — from a concept intersection or a manual seed; promotes or is killed |
| `project` | `projects/` | A multi-paper research thread (a concrete `RESEARCH.md` domain) |
| `grant` | `grants/` | A funding application or active award |
| `interaction` | `interactions/` | A documented interaction event — a lab meeting, 1:1, conference talk, email thread, or call |
| `note` | `notes/` | First-person thinking — a reflection, a brainstorm capture |
| `task` | `tasks/` | A tracked to-do with a deadline |
| `person` | `people/` | A collaborator, student, postdoc, or paper author |
| `institution` | `institutions/` | A lab, university, consortium, or funder |
| `conversation` | `conversations/` | A captured discussion — science discussion, explainer, or fit-assessment — anchored on page(s) when relevant, or free-standing |

A page is one markdown file: `papers/<slug>.md`. The directory and the `kind`
frontmatter field must always agree.

## Peer-reviewed and preprint are one kind

A peer-reviewed article and a preprint are the same kind — `paper` — separated
by a `status` frontmatter field (`published`, `preprint`, or `unknown`), not
by directory. The reason is the lifecycle: a preprint that is later published
would otherwise have to move directories, which breaks every inbound
`[[papers/<slug>]]` wikilink. Keeping it one kind makes publication a one-line
`status` flip. Review status stays just as queryable — it is a field, in one
place. `unknown` is a transient ingest state; the `maintain` pass resolves
it (see `frontmatter.md`).

## The synthesis layer: concepts → hypotheses → crystallization

Three kinds form a maturation pipeline with different lifetimes (full design lives in the instance's private
`docs/specs/`, not shipped in the template):

- **`concept`** — persistent, cross-cutting, never graduates. The frontier where
  ideas evolve.
- **`hypothesis`** — transient proving-ground. When several concepts intersect
  into something that could **Beat / Unlock / Scale / Explain**, or when your human
  seeds a compelling-but-unready idea, a hypothesis is minted. It is worked, then
  **promoted** to a project/grant or **killed** (retained with a reason).
- **`project` / `grant`** — the crystallized, resourced output.

Edges are forward-only and child-declares-parent (`graph-and-links.md`).

## Slug conventions

A slug is lowercase, hyphen-separated, ASCII-only. The per-kind form:

- **`people/`** — `<surname-firstname>` (e.g. `people/setliff-ian`,
  `people/de-carvalho-renan`). Surname-first because the brain is keyed on the
  author tokens that appear in citations (`Setliff et al.`, `de Carvalho et
  al.`); putting surname in the slug head makes the back-link from a paper's
  `authors:` list deterministic. Multi-word surnames keep their particles
  attached to the surname token (`de-carvalho-renan`, not
  `carvalho-renan-de`). Collisions get a disambiguator on the *end*
  (`wilson-ian-oxford` vs. `wilson-ian-cambridge`), never on the head.

  **Deriving the slug — load-bearing; getting the order wrong is a recurring
  bug.** Build the slug from the source's *structured* name fields, never by
  guessing token order off a display string. CrossRef `family` / `given` and
  PubMed `LastName` / `ForeName` give the surname unambiguously → slug is
  `<family>-<given>`. When only a **flat** name string is available (arXiv's
  `<author><name>`, an HTML byline), it is in **"Given Family" order** — the
  **last** token is the surname (with its particles): `"Shane Crotty"` →
  `crotty-shane`, *never* `shane-crotty`; `"Galit Alter"` → `alter-galit`. The
  `name` field is stored in display order ("Given Family"), so a **self-check**
  is available: the slug's head token must equal the last word of `name`; if it
  does not, the slug is reversed — fix it before writing.
- **`papers/`** — `<first-author-surname>-<year>-<topical-tag>` (e.g.
  `setliff-2019-libra-seq`).
- **`institutions/`** — readable short form (e.g. `mit`,
  `washington-state-university`).
- **`grants/`** — mechanism + project number + short tag (e.g.
  `r01ai193616-data-driven-ab-models`).
- **`projects/`, `methods/`, `concepts/`, `hypotheses/`** — readable
  short-name slugs.
- **`conversations/`** — `<anchor-stem>-<mode>` when single-anchored (e.g.
  `esser-moller-2024-explainer`); otherwise a readable topical slug (e.g.
  `shower-idea-germline-affinity-gate`).

The `people/` convention is load-bearing: `paper-ingest`'s author back-link
phase and `grant-ingest`'s key-personnel resolution both depend on it being
the *only* slug shape in use. If you find an outlier, normalize it before
the next ingest — back-links to the wrong shape silently fail to wire.

## Scope boundary

There is **no page kind for personal-life content and none for lab operations
churn** (ordering, equipment logistics, managing the 1:1 cadence). The
boundary is kept structurally — by the absence of a kind — not by a runtime
filter.

Revised 2026-07-30 (design record:
`skills/brain-schema-evolution/references/lab-management-expansion-2026-07.md`,
approved by your human): **lab capability knowledge is in scope** — the lab's org
structure and mission, member expertise and pillar roles, and project status
are research-program knowledge, carried by the `person` lab-membership fields
(`frontmatter.md`), an `institutions/<lab>` anchor page, and status fields on
`project` pages. What remains out is *managing* the lab rather than *knowing*
it: content about the science is in, managing the cadence is out.

**Email as a source stream (added 2026-08-01 — design record:
`skills/brain-schema-evolution/references/email-modality-2026-08-01.md`).**
your human's work email is a raw source: archived to R2 under the `email/` prefix
(`raw-source-archive.md`), distilled into existing kinds, with notable threads
becoming `interaction` pages (`channel: email`) through the notability gate.
Personal mail is excluded upstream (account scoping at the CLI); the boundary
itself is unchanged — there is still no kind for personal-life content, and
non-research-program mail simply produces no pages.

`working-docs/` is a non-brain directory for transitory working documents —
feasibility assessments, scoring tables, subagent research outputs. It is
**not** a page kind, not indexed, not part of the knowledge graph. If content
there is load-bearing, promote it to a real page. See `working-docs/README.md`
and `DESIGN.md` §2.1.1.
