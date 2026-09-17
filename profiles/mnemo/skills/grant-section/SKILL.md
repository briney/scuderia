---
name: grant-section
description: Draft or revise one section of a grant in progress — Specific Aims, Significance, Innovation, Approach, Abstract, Narrative, or a resubmission Introduction — in your human's voice, cite-or-flag throughout, against the section's page budget.
triggers:
  - "draft the Significance section"
  - "write the Specific Aims"
  - "revise the Approach"
  - "redo Innovation"
  - applying your human's edits or grant-coherence flags to a section
eval_contract:
  goal: |
    Draft or revise one section of an opened grant inside its page budget,
    in your human's voice, with every claim cited or flagged and the
    section's structural requirements honored.
  dimensions:
    - "VOICE — prose matches the human's measured voice, not invented mannerisms"
    - "COMPLIANCE — section meets the NIH/NOFO requirement and page budget for its section"
    - "CITE-OR-FLAG — every substantive claim cited or [needs-citation]-flagged"
    - "LOCALITY — only the owned Draft subsection and revision log change; gaps remain explicit"
  hard_fails:
    - Inventing a citation or silently dropping a claim that needs one.
    - Writing past the section's page budget and leaving overflow for others.
    - Altering Verbatim or unrelated sections, or concurrent whole-file rewrites by section workers.
---

# Grant section — draft one section in your human's voice

> **Git closeout:** Follow `skills/git-ops/SKILL.md`. Close one verified section revision and its supporting citation changes. Do not claim the entire unfinished application is complete. When called by a larger grant operation, return changed paths and validation to that owner.

The workhorse of the grant-writing cluster. It drafts or revises **one** section
of a grant already opened by `grant-plan`, writing into that grant's `## Draft`.
It is invoked many times across a multi-week application — once per section,
then again for every revision pass. It is where `STYLE.md` does its work: the
prose must read as your human, be pitched at the smart near-expert, and carry none of
the machine-writing tells.

> **Conventions:** `STYLE.md` (the scientific-writing standard — voice, reader,
> the tells), `SOUL.md` §2 (cite-or-flag — spine, non-negotiable),
> `skills/conventions/quality.md` (citations, no paraphrase of your human's prose),
> `skills/conventions/brain-first.md` (pull from the brain before going external),
> `skills/conventions/capabilities.md` (the harness contract),
> `skills/grant-formats/` (the section's page budget).
> The section's structure guide loads per section below. For a Specific Aims
> page, also `skills/grant-formats/section-style.md` (argument-level criteria).
> Chains to `skills/query/SKILL.md`, `skills/literature-research/SKILL.md`, and
> `skills/academic-verify/SKILL.md` for substrate and grounding.

## Capabilities

`brain-read`, `brain-write`, `user-model-query` (your human's voice priors are
loaded into the draft pass).

## What this guarantees

- One section is drafted or revised per invocation, written into the grant
  page's `## Draft` — never a blind overwrite of the whole page.
- The prose reads as your human: voice matched from the `## Verbatim` sections of
  ingested `grant` pages, with the universal `STYLE.md` standards carrying the
  cold start where that model is thin.
- Every substantive claim carries a verifiable citation or an explicit
  `[needs-citation]` flag — never a silent omission.
- The section respects its page budget from the NOFO or `grant-formats/`.
- The section's open gaps are surfaced for `grant-coherence` and
  `grant-citations`, not papered over.

## Phases

1. **Locate the section in the plan.** Read the grant page's `## Section plan`
   — which section, its page budget, the brain pages feeding it, the gaps
   already flagged. If the section is the Specific Aims and it is not yet
   locked, it is drafted first: nothing downstream is stable until it is.

2. **Gather the section's substrate.** Pull the `project`, `concept`, `method`,
   and `hypothesis` pages the plan names. Chain to `skills/query/SKILL.md` for
   anything thin, `skills/literature-research/SKILL.md` for current field state
   where the section needs it, `skills/academic-verify/SKILL.md` for a claim
   that must be grounded to source.

3. **Draft, or revise.** Load `STYLE.md`, the section's guide from
   `skills/grant-formats/` (`specific-aims.md`, `significance.md`,
   `innovation.md`, `approach.md`, `project-summary.md`,
   `project-narrative.md` — only the one in scope), and any instance
   calibration the section guide names. For a resubmission Introduction, use
   the NOFO/mechanism instructions and prior critiques; none of the six guides
   substitutes for that response. For a Specific Aims page, also load
   `skills/grant-formats/section-style.md`. Write as your human — match sentence
   rhythm, paragraph shape, and claim calibration from the `## Verbatim`
   sections of ingested `grant` pages; where that voice model is thin, lean on
   the universal standards (`STYLE.md` §3–§4), not a guessed mannerism. Delete
   the tells (§4). Stay inside the page budget. For a **revision**, the input
   is your human's edits or `grant-coherence` flags — your human's edits are
   the highest-value voice signal there is (`STYLE.md` §2): apply them and
   carry what they teach into the rest of the draft.

4. **Cite or flag, every claim.** Each substantive claim gets a verifiable
   citation or an explicit `[needs-citation]` flag (`SOUL.md` §2). A claim with
   no source is flagged, never quietly dropped and never given an invented
   citation. `grant-citations` resolves the flags later; this skill never
   leaves a claim silently unsupported.

5. **Write into `## Draft` and surface the gaps.** Update only this section's
   subsection of `## Draft`. Log the draft or revision in `## Drafting log`.
   Then list what the section still needs — unresolved `[needs-citation]`
   flags, cross-section dependencies, thin spots — for `grant-coherence` and
   `grant-citations`. Do not paper over a thin spot to look finished.

The Specific Aims are drafted and locked in series, first. Once they are
locked, the remaining sections are independent enough to be drafted in
parallel — `grant-plan`'s section plan says which. After a batch of sections,
chain to `grant-coherence`. A resubmission Introduction is drafted here like
any other section, working from the prior grant's `[!critique]` annotations.

## Personal calibration and write ownership

Read the author's declared writing judgments in `USER/<name>.md` and the
measured voice in `USER/VOICE.md` when available. Do not assume another
instance has the same principles, section numbering, or corpus history.
The optional calibration binding is declared in the instance's `AGENTS.md`;
load its index and only the current section's note. Without a binding, use
the generic guide and available author-owned prose without inventing a voice.

Distinct sections of one grant page are **not** safe simultaneous whole-file
rewrites. When sections are drafted in parallel, each worker returns its
section text or writes to its own scratch file; a single owner integrates the
`## Draft` updates serially.

## Output

The updated `## Draft` subsection on the grant page — finished prose for one
section, within budget, every claim cited or `[needs-citation]`-flagged, in
your human's voice. A `## Drafting log` entry. A short list of the section's open
gaps handed to `grant-coherence` and `grant-citations`.

## Anti-patterns

- Inventing a voice instead of matching your human's corpus — and, where the corpus
  model is thin, inventing a mannerism instead of leaning on the `STYLE.md`
  universal standards (`STYLE.md` §2).
- Paraphrasing prose lifted from an ingested grant's `## Verbatim` — that is
  your human's preserved voice, not a draft source (`skills/conventions/quality.md`).
- Reproducing the machine-writing tells of `STYLE.md` §4 — inflated
  significance, copula avoidance, forced triads, hedge stacks.
- Dropping a claim that needs a citation, or inventing one, instead of leaving
  a `[needs-citation]` flag.
- Writing past the section's page budget and leaving the overflow for someone
  else to cut.
- Promoting `## Draft` into `## Verbatim` — only submission does that.
- Blind-overwriting the grant page instead of updating the one section.
- Two workers rewriting different sections of the same grant page
  concurrently — section text is returned or scratch-written; the parent
  integrates serially.
