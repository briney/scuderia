# NIH R21 — Exploratory/Developmental Research Grant (no clinical trials)

The R21 funds early-stage, exploratory, or developmental work — a novel idea or
a new model system that would not yet survive R01 review. your human's usual route
is the parent announcement **PA-25-304** (Exploratory/Developmental Research
Grant, Clinical Trial Not Allowed), reissued periodically under a new PA
number. Confirm the live number and read its Section IV — the NOFO overrides
this file (`README.md`).

## Award parameters

- **Budget** — combined direct costs may not exceed **$275,000** over the
  two-year period, and **no single year may exceed $200,000**.
- **Project period** — up to 2 years.

These are hard caps. `grant-plan` scopes the aims to fit them; an R21 proposing
R01-sized work is the most common way the mechanism is misused.

## The application package

Same `grant` page kind as the R01. The cluster-drafted science sections:

| Section | Limit | Notes |
|---|---|---|
| Project Summary / Abstract | 30 lines of text | Standalone; readable by a non-specialist. |
| Project Narrative | 3 sentences | Public-health relevance, plain language. |
| Specific Aims | 1 page | The anchor — draft and lock this first. |
| Research Strategy | **6 pages** | Half the R01 — the defining structural difference. |
| Bibliography & References Cited | no limit | Every Research Strategy citation, formatted. |
| Introduction to Application | 1 page | Resubmissions (A1) only — see below. |

The 6-page Research Strategy is organized under the same Significance /
Innovation / Approach headers as the R01 (`nih-r01.md`), compressed.

## What makes it an R21, not a small R01

The R21 is for ideas that **break new ground**. Reviewers weigh the conceptual
framework, the level of innovation, and the potential of the idea — not a thick
evidence base. `grant-plan` and `grant-coherence` hold the draft to that bar:
an R21 whose pitch is incremental, or which reads as a scaled-down R01, is
miscast and should be flagged early — ideally in the planning phase, where
shelving it is cheap (`status: shelved`).

## Preliminary data

**Not required.** Preliminary data may be included if available and can
strengthen feasibility, but their absence is not a weakness — the mechanism
exists precisely for ideas that do not yet have them. `grant-coherence` does
**not** flag a missing-preliminary-data gap on an R21 the way it does on an R01
(`nih-r01.md`). It still flags an unsupported *factual* claim — cite-or-flag is
spine and mechanism-independent (`SOUL.md` §2).

## Citations

As for the R01: no mandated style, but a consistent and complete one, with
PMCIDs for NIH-funded publications. `grant-citations` resolves every
needs-citation flag before submission.

## Resubmission (A1)

A resubmission adds a 1-page **Introduction to Application** responding to the
prior summary statement; an A1 cannot be submitted before the A0's summary
statement issues. `grant-plan` loads the prior `grant` page's `[!critique]`
annotations and plans the Introduction; `grant-section` drafts it.
