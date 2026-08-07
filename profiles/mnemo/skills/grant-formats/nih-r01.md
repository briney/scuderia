# NIH R01 — Research Project Grant (no clinical trials)

The R01 is NIH's standard research grant: a defined, hypothesis-driven project
led by an investigator with the preliminary data and track record to carry it.
Bryan's usual route is the parent announcement **PA-25-301** (Research Project
Grant, Clinical Trial Not Allowed), reissued every few cycles under a new PA
number. Confirm the live number and read its Section IV — the NOFO overrides
this file (`README.md`).

## Award parameters

- **Budget** — not capped; it must reflect the actual needs of the work. (The
  former $500K-direct-costs prior-approval threshold was rescinded by
  NOT-OD-26-019, after PA-25-301 issued — a reminder that NIH notices override
  a standing NOFO, per `README.md`.)
- **Project period** — up to 5 years.

## The application package

A grant is one `grant` page (`grant-ingest` and the grant-writing cluster share
the kind). The science sections that the cluster drafts, with their limits:

| Section | Limit | Notes |
|---|---|---|
| Project Summary / Abstract | 30 lines of text | Standalone; readable by a non-specialist. |
| Project Narrative | 3 sentences | Public-health relevance, plain language. |
| Specific Aims | 1 page | The anchor — draft and lock this first. |
| Research Strategy | 12 pages | Significance, Innovation, Approach (below). |
| Bibliography & References Cited | no limit | Every Research Strategy citation, formatted. |
| Introduction to Application | 1 page | Resubmissions (A1) only — see below. |

Page limits are from the NIH Table of Page Limits, not the NOFO body
(`README.md`). Biosketch, budget, budget justification, facilities, and
data-management plan are package documents but not cluster-drafted science
prose.

## Research Strategy structure

Twelve pages, organized under three headers:

- **Significance** — the problem, the gap, why solving it matters. What the
  field gains.
- **Innovation** — what is new: concept, approach, methodology, or
  instrumentation. Innovation is not novelty for its own sake (`SOUL.md` §3).
- **Approach** — the experimental plan, aim by aim. Each aim states its
  rationale, design, expected outcomes, potential pitfalls and alternatives,
  and a rigor/feasibility argument. Preliminary data lives here, tied to the
  aim it supports.

## Review framework (2025 simplified framework)

Reviewers score a 1–9 Overall Impact and assess three factors:

1. **Importance of the Research** — Significance and Innovation. Scored.
2. **Rigor and Feasibility** — Approach. Scored.
3. **Expertise and Resources** — investigators and environment. Assessed as
   sufficient or not, not separately scored.

`grant-coherence` checks that the draft gives each scored factor what it needs
to land — Significance and Innovation legible, Approach rigorous and feasible.

## Preliminary data

Expected. The R01 is for an established line of work, and reviewers read
preliminary data as the feasibility evidence for the Approach. A claim of
feasibility with no data behind it is a `grant-coherence` flag. (This is the
sharpest contrast with the R21 — see `nih-r21.md`.)

## Citations

NIH mandates no single citation style — it requires a consistent, complete one.
Include a PMCID for any cited publication that arose from NIH funding.
Cite-or-flag is non-negotiable (`SOUL.md` §2): `grant-citations` resolves every
needs-citation flag before submission.

## Resubmission (A1)

A resubmission adds a 1-page **Introduction to Application** responding to the
prior summary statement. NIH will not accept an A1 before the A0's summary
statement has issued. `grant-plan` detects a resubmission, loads the prior
`grant` page's `[!critique]` annotations (placed there by `grant-ingest`), and
plans the Introduction; `grant-section` drafts it as a normal section.
