---
name: grant-section
description: Draft or revise one section of a grant in progress — Specific Aims, Significance, Innovation, Approach, Abstract, Narrative, or a resubmission Introduction — in your human's voice, cite-or-flag throughout, against the section's page budget.
triggers:
  - "draft the Significance section"
  - "write the Specific Aims"
  - "revise the Approach"
  - "redo Innovation"
  - applying your human's edits or grant-coherence flags to a section
---

# Grant section — draft one section in your human's voice

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
> `skills/grant-formats/section-style.md` carries the argument-level criteria
> for the section being drafted. Chains to `skills/query/SKILL.md`,
> `skills/literature-research/SKILL.md`, and `skills/academic-verify/SKILL.md`
> for substrate and grounding.

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

3. **Draft, or revise.** Load `STYLE.md` and
   `skills/grant-formats/section-style.md`. Write as your human — match sentence
   rhythm, paragraph shape, and claim calibration from the `## Verbatim`
   sections of ingested `grant` pages; where that voice model is thin, lean on
   the universal standards (`STYLE.md` §3–§4), not a guessed mannerism. Delete
   the tells (§4). For a Specific Aims page, build the significance argument
   and Aim architecture against `section-style.md`. Stay inside the page
   budget. For a **revision**, the input is your human's edits or `grant-coherence`
   flags — your human's edits are the highest-value voice signal there is
   (`STYLE.md` §2): apply them and carry what they teach into the rest of the
   draft.

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

## Specific Aims page — construction principles

Six principles from your human's critique-and-rewrite decisions on a real
R01 Specific Aims page (2026-08-03). These are his decisions, not
suggestions.

1. **Significance is carried by logic; statistics are ballast.** The
   Aims-page significance argument must not be a statistics pile (he is
   on the record rejecting a statistics pile in favor of a logical
   argument). Working structure: disease burden → therapeutic bind
   framed as logic (e.g., resistance is monogenic — one mutation
   accounts for ≈97% of resistant isolates — so resistance arrives all
   at once; the therapeutic gap is widest exactly where burden is
   greatest) → target biology plus the clinically validated precedent →
   the motivating scientific puzzle → overall goal. The puzzle (e.g.,
   the reinfection paradox: universal exposure + strong seroconversion
   yet lifelong reinfection) is the best material on the page and goes
   up front, just before the goal — not buried behind the statistics.

2. **Promote the clinically validated precedent to the Aims page.** For
   anti-toxin / anti-virulence proposals, the bezlotoxumab (anti-C.
   difficile TcdB: ~40% reduction in recurrence, Phase 3, FDA-approved)
   vs suvatroxumab (anti-S. aureus α-hemolysin: missed Phase 2 endpoint)
   contrast converts the proposal from a bet into an instance of a
   validated formula — anti-toxin antibodies succeed where one dominant
   toxin drives disease and fail where virulence is distributed. This
   belongs on the Aims page, not only in Significance. Generalizes to
   the pertussis-toxin pilot and the whole antibacterial-antibody
   program.

3. **Feasibility fallbacks belong in the Approach, never the Aims
   page.** Including a design fallback at the Aim level "plants
   feasibility doubt in the reviewer's mind right from the start."
   Alternative approaches go in that Aim's Approach section.

4. **Build Aim independence in explicitly; no feeder language.** State
   which Aims/phases proceed without upstream outputs ("Aim 2's
   polyclonal mapping requires only donor sera"; "Phase 1 is fully
   independent of Aims 1 and 2 and runs in parallel"). Never write
   "hits that pass this gate will advance to Aim N" — it makes one Aim
   a feeder for another and invites the cascade-failure critique. Add
   one integration sentence before the closing paragraph making the
   integrated-but-parallel architecture explicit.

5. **Verify every statistic against the primary source before it
   appears on the page.** Do not conflate distinct statistics: a
   draft's "more than half of pediatric pneumonia hospitalizations
   during the 2024 resurgence... a six-fold increase" merged the
   July-2024 peak-month proportion (53.8%) with the annual incidence
   ratio (6×); the true annual figure for 2024 was 33%. Do not cite a
   range endpoint without a specific study behind it: "80% in some US
   outbreaks" was the unelaborated upper bound of a 3–80% review range;
   the honest framing is the trajectory + monogenic-resistance
   argument.

6. **Qualify associative evidence explicitly.** Human
   prevalence/association plus animal sufficiency is strong
   triangulation, not human causation. State both halves and their
   relation. Model sentence pattern: "CARDS-toxin-producing
   M. pneumoniae is detected in roughly half of adults with refractory
   asthma [association], and the toxin alone induces asthma-like
   pathology in primates [animal sufficiency]." Anchor such sentences
   on the primary study with the clean contrast (Peters 2011: 52% RA
   vs 2.9% healthy controls) rather than on a paraphrased pediatric
   figure whose healthy-control contrast is weak (Wood 2013: 64% vs
   56%). See `academic-verify` Phase 3 for the intermediary-paraphrase
   verification technique that surfaced this.

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
