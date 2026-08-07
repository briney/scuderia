# Worked example: lab-management expansion (2026-07-30)

The first live exercise of `brain-schema-evolution`: Bryan proposed adding
lab-management capability to the brain — a formal lab org structure, enriched
lab-member pages, and basic project-management state to feed progress reports.
This note is the design record: what was decided, why, and what was rejected.

## The scope question

The proposal crossed a documented exclusion. `VISION.md` §6 and
`page-kinds.md` ("Scope boundary") excluded *lab-state management* — "student
1:1 cadence, ongoing student projects, ordering, equipment" — structurally, by
having no page kind and no skill for it. So the first move was not schema
design but a north-star conversation with Bryan, held explicitly as one
(Step 1). Bryan approved the scope revision in conversation on 2026-07-30.

## Decomposition against the scope line (Step 2)

The proposal bundled three asks. Split against the test — *does this feed the
research program (grantwriting, progress reports, brainstorming,
who-can-do-what), or is it operational churn?*

| Ask | Verdict | Reason |
|---|---|---|
| Lab org structure, mission statement | **In scope** | Load-bearing for key-personnel sections, budget justifications, facilities/resources text, and grounding decisions in the lab's ethos |
| Enriched lab-member pages, distinguished from collaborators | **In scope** | Skills/expertise of individual members drive budget justifications and who-can-do-what reasoning |
| Project status / milestones | **In scope, deferred implementation** | Research state, not ops. Schema lands now (on `project` pages); *automated* maintenance (from meeting ingestion, eventually email/Slack) is a known unsolved problem, deferred but flagged as soon-rather-than-later |
| Managing people (1:1 cadence, ordering, equipment logistics) | **Stays out** | Operational churn; the original exclusion narrowed to exactly this |

Note the pre-existing tension this resolved: the `meeting` kind already covered
1:1s as research discussions. The refined line generalizes it — *content* about
the science is in; *managing the cadence* is out.

## Applying the three extension rules (Step 3)

**Rule 1 — status is a field, not a kind.** The obvious wrong move was a
`lab-member` kind (or directory) split from `person`. A lab member is also a
paper author, a meeting attendee, and eventually an alum who may become a
collaborator. Splitting by relationship type gives one human two pages and
breaks the author-ledger and entity-resolution wiring. Same precedent as
`paper`'s `status` field covering preprint → published.

**Rule 2 — graph-hub test.** First-class `milestone` and `report` kinds were
considered and rejected: a milestone has exactly one parent (its project) and
no inbound edges from other directions. Milestones are fields on `project`
pages. Thin, singly-linked pages are fields wearing a costume.

**Rule 3 — relationship distinctions in frontmatter, not directories.** "Which
people are lab members" is a query over `member_of:`, not a `lab-members/`
directory. "Which pillar does X lead" is a query over `pillar:` /
`pillar_role:`.

## Schema changes

### `person` kind — new fields (all optional)

| Field | Meaning |
|---|---|
| `member_of` | `institutions/<slug>` — the lab(s) the person is a member of. Distinct from `affiliation` (the institutional *home*, e.g. the university): a lab member's affiliation is the university; their membership is the lab |
| `lab_status` | `current` \| `alumni`. Only meaningful alongside `member_of`. Alumni keep their pages and edges — the historical record persists |
| `pillar` | Lab pillar the person belongs to, free-text token (e.g. `ai-research-engineering`, `applied-ai`, `repertoire-scale-immunology`) |
| `pillar_role` | `lead` \| `co-lead` \| `member` |
| `expertise` | Short capability list — the budget-justification and who-can-do-what substrate |
| `works_on` | Typed edge list to `projects/<slug>` — distinct from `links:`, same pattern as `author_on:` for papers |

### `project` kind — status fields (schema landed, population deferred)

`status:`, `personnel:`, `funding:`, `milestones:` (list of
`{name, date, state}`) — making the existing `project` kind carry the state a
progress report queries. **Population and automated maintenance are deferred**;
stale state is worse than no state, so these fields should not be
hand-maintained at scale until ingestion-driven updates exist.

### No new page kinds. One new institution page.

`institutions/example-lab` anchors the org: mission statement, pillar
structure, and (eventually) lab resources indexed by pillar — the last because
the pillar that owns a resource owns its grant-facilities narrative.

## The org model recorded here

Pillars are **capabilities, not teams** (Bryan, 2026-07-30). Only the leads
belong to pillars; trainees run self-led projects that draw on multiple
pillars, with pillar leads as technical point-people and mentors. Leads manage
the *platform*, not the people — Bryan keeps the people. This is a
resource/center-of-excellence model, deliberately not a reporting hierarchy.

Three pillars: **AI Research & Engineering** (research: Sarah Burbach —
model-training research; engineering: Terrence Messmer — compute clusters,
storage, self-hosted agents), **Applied AI** (Nitesh Mishra, solo lead; a
co-lead or second-in-command anticipated), **Repertoire-Scale Immunology**
(Benjamin Nemoz and Jonathan Hurtado, co-leads; division at the project level,
platform responsibilities held jointly).

## Rollout (Step 4)

1. This design note.
2. Conventions: `frontmatter.md`, `page-kinds.md`.
3. Scope-line move: `VISION.md` §6, `DESIGN.md` §11, `AGENTS.md` (Step 5 —
   same unit of work).
4. Skill template: `enrich` person template.
5. Linter: no change needed — page frontmatter fields are not whitelisted
   (only ledger entries and SKILL.md frontmatter are); verified against
   `.github/scripts/lint-frontmatter.py`.
6. **Pilot**: `institutions/example-lab` + the five pillar-lead person pages +
   the human's own page. Your human reviews the shape before any full pass.
7. Full pass (deferred until pilot review): remaining lab members, `works_on`
   curation, project-page status fields, resource inventory.

## Open items

- Automated project-state maintenance (meeting ingestion first; email/Slack
  streams later) — unsolved, flagged by Bryan as needed sooner rather than
  later.
- Nemoz staff-scientist promotion in progress (Bryan, 2026-07-30) — update
  `role` when it lands.
- Which collaborator's group Benjamin joined from (Grenoble IBS / Grenoble
  Alpes University Hospital) — the collaborator page link is pending Bryan's
  identification.
