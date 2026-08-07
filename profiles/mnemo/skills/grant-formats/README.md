# Grant formats — structural reference for the grant-writing cluster

This directory holds **format references**, one file per grant mechanism. They
are not skills — they have no trigger. The grant-writing skills consult them:
`grant-plan` to build an application's outline and `grant-coherence` to check
page-limit and structure compliance.

A format file is *structure* — required sections, page limits, section order,
review framework, citation rules. It is not sentence-level *style*: how the
prose reads is `STYLE.md`, and `STYLE.md` §1 is explicit that document
structure belongs to the skill side, not the character. These files are that
structure. One companion here goes one level deeper than structure:
`section-style.md` carries the argument-level criteria for how a section's
case is built — the sentence still belongs to `STYLE.md`.

There are three files of guidance in this directory:

- **Mechanism files** (`nih-r01.md`, `nih-r21.md`) — package-level structure:
  required sections, page limits, section order, review framework. One file
  per grant mechanism.
- **`section-structure.md`** — within-section structure: Bryan's
  paragraph-level conventions for individual sections (how the Specific Aims
  page is organized, what each paragraph does). Mechanism-independent where
  the section envelope is fixed (Specific Aims is 1 page regardless of
  mechanism); mechanism-specific structure lives in the mechanism file.
- **`section-style.md`** — within-section argument criteria: how the
  significance case on an Aims page must be built, how Aims integrate without
  becoming interdependent, page economy, calibrated impact. The companion to
  `section-structure.md` — structure says what each paragraph does, style
  says how the argument inside it is constructed. Session-derived (the
  2026-08-03 CARDS toxin Aims review); to be tested and refined on
  subsequent pages.

## The load-bearing rule: the NOFO wins

A format file is a **generic scaffold**. The specific funding announcement
Bryan is applying to — the NOFO / FOA / RFP, with its own number — is
**authoritative and overrides this file** wherever they differ. NIH reissues a
parent announcement every few years under a new PA number, foundation calls
vary year to year, and a NOFO can impose its own page limits in its Section IV.

So `grant-plan` always reads the actual announcement Bryan provides, extracts
its requirements, and archives the NOFO to R2 as a `source:` on the grant page
(`conventions/raw-source-archive.md`). The format file is the fallback when no
NOFO is in hand yet, and the checklist of things to confirm against the one
that is.

## Coverage

| File | What it covers |
|---|---|
| `section-structure.md` | Within-section conventions (Bryan's paragraph-level structure for Specific Aims, and future sections) |
| `section-style.md` | Argument-level criteria for sections (significance architecture, Aim integration, page economy, calibrated impact) |
| `nih-r01.md` | NIH R01 — Research Project Grant, no clinical trials (PA-25-301) |
| `nih-r21.md` | NIH R21 — Exploratory/Developmental, no clinical trials (PA-25-304) |

R01 and R21 are the mechanisms Bryan writes most. Other mechanisms get a file
when one is first needed — not pre-built.

## Page limits are NIH-wide and dated

The page limits in `nih-r01.md` / `nih-r21.md` come from the NIH **Table of
Page Limits**, not the individual NOFO — the NOFOs point at that table rather
than reproducing it. The table is current as of the 2025 application cycle.
`grant-plan` should confirm against the live table when an application opens:
<https://grants.nih.gov/grants/how-to-apply-application-guide/format-and-write/page-limits.htm>

## Sample applications — structure, never voice

NIAID publishes high-scoring sample applications with their summary statements:
<https://www.niaid.nih.gov/grants-contracts/sample-applications>

These are **structural exemplars** — what a funded Aims page or Approach
section looks like — and useful test material for `grant-coherence`. They are
**not** voice corpus. `STYLE.md` §2 is strict: Bryan's voice is learned only
from Bryan's own writing. `grant-section` learns voice from the `## Verbatim`
sections of ingested `grant` pages — never from another PI's application.
