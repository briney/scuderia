---
name: grant-coherence
description: Review a grant in progress as a whole application — catch cross-section contradiction and framing drift, check page-limit and structure compliance, confirm cite-or-flag completeness, and read it as a study-section reviewer would. Diagnoses and routes; does not rewrite.
triggers:
  - "check the grant"
  - "review the whole application"
  - "does this hang together"
  - "is the framing consistent"
  - the pre-submission coherence gate
---

# Grant coherence — hold the whole application in view

Grant writing is multi-section, and the failure mode is local: each section
reads fine, but Aim 3 contradicts the Significance section, the innovation
framing drifted between drafts, a claim never got its citation. This skill is
the one that holds the *whole* application in view (`VISION.md` §2.2). It
**diagnoses and routes** — it does not rewrite. Fixes go back to `grant-section`
(prose, contradiction) and `grant-citations` (citations).

> **Conventions:** `STYLE.md` §3 (the one reader — the smart near-expert),
> §4 (the machine-writing tells), `SOUL.md` §2 (cite-or-flag — and §3, never
> suppress a substantive flaw to preserve rapport), `skills/conventions/quality.md`
> (citation discipline), `skills/conventions/capabilities.md` (the harness contract),
> `skills/grant-formats/` (page limits, required sections, mechanism fit),
> `skills/grant-formats/section-style.md` (argument-level criteria for
> sections). Routes fixes to `skills/grant-section/SKILL.md` and
> `skills/grant-citations/SKILL.md`.

## Capabilities

`brain-read` (diagnoses; does not write to the grant page itself, only
the diagnosis log).

## What this guarantees

- The application is reviewed as a whole, never section by section in
  isolation — the cross-section view is the entire point.
- Cross-section contradiction and framing drift are caught: a claim, number, or
  central hypothesis stated inconsistently across sections.
- Page-limit and structure compliance is checked against the **NOFO first**,
  `grant-formats/` as fallback — including mechanism fit.
- Every substantive claim is confirmed cited or `[needs-citation]`-flagged;
  unresolved flags are collected, not resolved here.
- The output is a prioritized, section-tagged issue list, each item routed to
  the skill that fixes it.

## Phases

1. **Read the whole application.** The grant page's `## Draft`, its
   `## Section plan`, and the NOFO (or `grant-formats/` file). Hold all of it
   in view at once.

2. **Cross-section coherence pass.** Contradiction and drift: an aim that cuts
   against the Significance claim, a number or result stated two ways, the
   central hypothesis framed differently in the Aims, the Abstract, and the
   Approach. The innovation framing should be one framing, not three drafts'
   worth.

3. **Compliance pass.** Per-section page budgets, required sections present,
   section structure — against the NOFO first. Mechanism fit: an R21 that
   reads as a scaled-down R01 is miscast (`grant-formats/nih-r21.md`); an R01
   Approach should carry the feasibility evidence its review factor needs
   (`nih-r01.md`).

4. **Cite-or-flag pass.** Every substantive claim is cited or carries a
   `[needs-citation]` flag (`SOUL.md` §2). Collect the unresolved flags for
   `grant-citations` — this skill confirms completeness; it does not resolve.

5. **The reviewer read.** Step back and read the application as the smart
   near-expert (`STYLE.md` §3) and as a study-section reviewer: where the
   argument is muddy, where significance is asserted instead of shown
   (`STYLE.md` §4) or carried by statistics instead of logic
   (`grant-formats/section-style.md`), where a reviewer will find a gap and
   punish it. Consult the
   `[!critique]` annotations on prior `grant` pages — what study sections
   punished Bryan's earlier applications for is direct evidence here.

6. **Report and route.** A prioritized issue list, each item tagged with its
   section and routed: prose, contradiction, and framing → `grant-section`;
   citations → `grant-citations`. Then the revision loop runs until the
   application clears the gate. Surface every substantive problem — never
   soften a real flaw to make the draft look closer to done (`SOUL.md` §3).

## Output

A prioritized, section-tagged issue list. Each item: what is wrong, which
section(s), and which skill fixes it. No rewritten prose — diagnosis and
routing only. When the list is empty, the application has cleared the
pre-submission coherence gate.

## Anti-patterns

- Rewriting prose in place — that is `grant-section`; this skill diagnoses and
  routes.
- Flagging missing preliminary data on an R21 — the mechanism does not require
  it (`grant-formats/nih-r21.md`). An unsupported *factual* claim is still a
  flag; a thin evidence base on an exploratory grant is not.
- Checking only mechanics — page limits and section structure — and skipping
  the reviewer read, which is where the application is actually won or lost.
- Treating a `grant-formats/` file as authoritative when a NOFO is in hand —
  the NOFO wins (`grant-formats/README.md`).
- Reviewing one section in isolation — the cross-section contradiction is the
  failure this skill exists to catch.
- Softening a real flaw so the draft looks closer to finished (`SOUL.md` §3).
