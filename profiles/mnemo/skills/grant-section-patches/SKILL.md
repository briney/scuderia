---
name: grant-section-patches
description: "Patch pending grant-section: Aims construction rules."
triggers:
  - "patch grant-section skill"
---

# grant-section — profile-side pending patches

The authoritative `grant-section` SKILL.md lives in the vault at
`skills/grant-section/SKILL.md`. `skill_manage` cannot patch
vault skills from a background context ("Skill not found in active
profile"). Patches are recorded here so a foreground or vault-edit
session can fold them in. Same pattern as the `paper-ingest` pointer.

## Patch 2026-08-03: Specific Aims page construction principles

Source: Bryan's critique-and-rewrite decisions on the M. pneumoniae
CARDS toxin R01 Aims page
(`grants/r01-mpneumoniae-cards-toxin-mab-discovery.md` `## Draft`),
2026-08-03. All six are user decisions, not suggestions. Add as a
"Specific Aims page — construction principles" section in the vault
SKILL.md.

1. **Significance is carried by logic; statistics are ballast.** The
   Aims-page significance argument must not be a statistics pile
   (Bryan: it "needs to be much more sophisticated than just vomiting
   up a bunch of statistics"). Working structure: disease burden →
   therapeutic bind framed as logic (e.g., resistance is monogenic —
   A2063G ≈97% of resistant isolates — so resistance arrives all at
   once; the therapeutic gap is widest exactly where burden is
   greatest) → target biology plus the clinically validated precedent
   → the motivating scientific puzzle → overall goal. The puzzle (e.g.,
   the reinfection paradox: universal exposure + strong seroconversion
   yet lifelong reinfection) is the best material on the page and goes
   up front, just before the goal — not buried behind the statistics.

2. **Promote the clinically validated precedent to the Aims page.**
   For anti-toxin / anti-virulence proposals, the bezlotoxumab
   (anti-C. difficile TcdB: ~40% reduction in recurrence, Phase 3,
   FDA-approved) vs suvatroxumab (anti-S. aureus α-hemolysin: missed
   Phase 2 endpoint) contrast converts the proposal from a bet into an
   instance of a validated formula — anti-toxin antibodies succeed
   where one dominant toxin drives disease and fail where virulence is
   distributed. This belongs on the Aims page, not only in
   Significance. Generalizes to the pertussis-toxin pilot and the
   whole antibacterial-antibody program.

3. **Feasibility fallbacks belong in the Approach, never the Aims
   page.** Bryan: including a design fallback at the Aim level "plants
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
   appears on the page.** Do not conflate distinct statistics: the
   draft's "more than half of pediatric pneumonia hospitalizations
   during the 2024 resurgence... a six-fold increase" merged the
   July-2024 peak-month proportion (53.8%) with the annual incidence
   ratio (6×); the true annual figure for 2024 was 33%. Do not cite a
   range endpoint without a specific study behind it: "80% in some US
   outbreaks" was the unelaborated upper bound of a 3–80% review
   range; the honest framing is the trajectory + monogenic-resistance
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
   56%). See the `academic-verify-patches` pointer for the
   intermediary-paraphrase verification technique that surfaced this.
