# Section structure — index of section guides

This file is a **compatibility index**: it routes a drafting or checking
request to the guide for the requested section, and nothing else. Load the
one section guide named below, not all of them — a request to revise an
Aims page should not load unrelated section guidance or the historical corpus
analysis. Read other application passages when the revision actually depends
on them; whole-application coherence still reads the entire application.

| Section | Guide | What it holds |
|---|---|---|
| Specific Aims | `specific-aims.md` | NIH requirement, aim-paragraph structure, what stays out of the page |
| Significance (Research Strategy) | `significance.md` | NIH requirement, where rigor content lives, topic-survey structure |
| Innovation (Research Strategy) | `innovation.md` | NIH requirement, innovation-paragraph structure, method-vs-combination claims |
| Approach (Research Strategy) | `approach.md` | NIH requirement, per-aim subsections, preliminary data, pitfalls |
| Project Summary / Abstract | `project-summary.md` | 30-line limit, standalone structure, non-specialist bar |
| Project Narrative | `project-narrative.md` | At-most-three-sentence rule, problem→approach→payoff arc |

Resubmission Introduction has no separate guide: it is drafted from the
prior application's critiques as a normal section by `grant-section`.

## Division of labor

- **Mechanism files** (`nih-r01.md`, `nih-r21.md`) — package-level
  structure: required sections, page limits, review framework, preliminary
  data expectation. The Research Strategy page budget lives there, not in
  the section guides.
- **Section guides** (this index's targets) — within-section structure:
  what the NIH instructions for that section actually require, plus generic
  drafting defaults.
- **`section-style.md`** — argument-level criteria (specific to the Aims
  page): how the significance case is built, aim integration, page economy.
  Load it when drafting or reviewing a Specific Aims page, not for every
  section.
- **`STYLE.md`** — the sentence itself: voice, rhythm, the machine-writing
  tells.

The load-bearing rule is unchanged: **the NOFO wins** wherever it differs
(`README.md`).

## Instance calibration

Section guides carry generic defaults. If the instance's `AGENTS.md`
declares a grant-writing calibration index, each section guide names where
its calibration note is found — the instance's own structural preferences
and reviewer context. With no calibration bound, the generic defaults apply
without pretending they are any particular author's voice.
