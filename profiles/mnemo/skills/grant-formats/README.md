# Grant formats — structural reference for the grant-writing cluster

This directory holds **format references**, not skills — they have no
trigger. The grant-writing skills consult them: `grant-plan` to build an
application's outline and `grant-coherence` to check page-limit and
structure compliance.

A format file is *structure* — required sections, page limits, section
order, review framework, citation rules. It is not sentence-level *style*:
how the prose reads is `STYLE.md`, and `STYLE.md` §1 is explicit that
document structure belongs to the skill side, not the character. One
companion here goes one level deeper than structure: `section-style.md`
carries the argument-level criteria for the Specific Aims page.

## What is here

- **Mechanism files** (`nih-r01.md`, `nih-r21.md`) — package-level
  structure: required sections, page limits, section order, review
  framework. One file per grant mechanism; other mechanisms get a file
  when one is first needed, not pre-built.
- **Section guides** — within-section requirements and generic drafting
  defaults, one per section: `specific-aims.md`, `significance.md`,
  `innovation.md`, `approach.md`, `project-summary.md`,
  `project-narrative.md`. Load only the guide for the section in scope —
  never all of them for one section.
- **`section-structure.md`** — the compact index that routes a section
  request to its guide. Compatibility shim: existing callers point here.
- **`section-style.md`** — argument-level criteria for the Specific Aims
  page (significance architecture, Aim integration, page economy,
  calibrated impact). Load it for Aims drafting and Aims-level review,
  not indiscriminately for every section.

## The load-bearing rule: the NOFO wins

A format file is a **generic scaffold**. The specific funding announcement
being applied to — the NOFO / FOA / RFP, with its own number — is
**authoritative and overrides this file** wherever they differ. Related NIH
Guide notices supersede a standing NOFO and the application guide; the NOFO
supersedes the guide. NIH reissues a parent announcement every few years
under a new PA number, foundation calls vary year to year, and a NOFO can
impose its own page limits in its Section IV.

So `grant-plan` always reads the actual announcement provided, extracts
its requirements, and archives the NOFO to R2 as a `source:` on the grant
page (`skills/conventions/raw-source-archive.md`). The format file is the
fallback when no NOFO is in hand yet, and the checklist of things to
confirm against the one that is.

## Coverage

| File | What it covers |
|---|---|
| `section-structure.md` | Index routing each section to its guide |
| `specific-aims.md` | Specific Aims — requirement and drafting defaults |
| `significance.md` | Significance (Research Strategy) |
| `innovation.md` | Innovation (Research Strategy) |
| `approach.md` | Approach (Research Strategy) |
| `project-summary.md` | Project Summary / Abstract (30 lines) |
| `project-narrative.md` | Project Narrative (at most 3 sentences) |
| `section-style.md` | Argument criteria for the Specific Aims page |
| `nih-r01.md` | NIH R01 — Research Project Grant, no clinical trials (PA-25-301) |
| `nih-r21.md` | NIH R21 — Exploratory/Developmental, no clinical trials (PA-25-304) |

## Page limits are NIH-wide and dated

The page limits in `nih-r01.md` / `nih-r21.md` and the section guides come
from the NIH **Table of Page Limits**, not the individual NOFO — the NOFOs
point at that table rather than reproducing it. Confirm against the live
table when an application opens:
<https://grants.nih.gov/grants-process/write-application/how-to-apply-application-guide/page-limits>

Section-guide requirements are cited from the SF424 (R&R) Application Guide
Form I (G.220, G.400); the guide is current as of the 2026 cycle.

## Sample applications — structure, never voice

NIAID publishes high-scoring sample applications with their summary statements:
<https://www.niaid.nih.gov/grants-contracts/sample-applications>

These are **structural exemplars** — what a funded Aims page or Approach
section looks like — and useful test material for `grant-coherence`. They are
**not** voice corpus. `STYLE.md` §2 is strict: the human's voice is learned
only from their own writing. `grant-section` learns voice from the `##
Verbatim` sections of ingested `grant` pages — never from another PI's
application.
