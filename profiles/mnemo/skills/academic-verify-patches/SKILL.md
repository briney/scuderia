---
name: academic-verify-patches
description: "Patch pending academic-verify: intermediary claims."
triggers:
  - "patch academic-verify skill"
---

# academic-verify — profile-side pending patches

The authoritative `academic-verify` SKILL.md lives in the vault at
`skills/academic-verify/SKILL.md`. `skill_manage` cannot patch
vault skills from a background context ("Skill not found in active
profile"). Patches are recorded here so a foreground or vault-edit
session can fold them in. Same pattern as the `paper-ingest` pointer.

## Patch 2026-08-03: claims cited through an intermediary

Add to Phase 3 ("Trace it externally"), after the confounds/replication
paragraph:

> **Claims cited through an intermediary.** When the claim arrives via
> paper B paraphrasing a figure from paper A ("approximately X% as
> reported in [A]"), do not stop at B's wording:
>
> - Pull B's reference list (full text if needed) and identify A's
>   PMID/DOI.
> - Fetch A itself and locate the figure in A's own text.
> - Paraphrase distortion is a documented failure mode: intermediaries
>   round, reframe, or silently drop the qualifying contrast. Observed
>   2026-08-03: Maselli 2018 paraphrased Wood 2013 as "approximately
>   50% of hospitalized children with acute exacerbation of asthma had
>   detectable CARDS toxin," but Wood's abstract reports 64% detection
>   in acute-asthma children *and 56% in healthy controls* — the
>   contrast the paraphrase implied does not survive the primary
>   source. The exact figure Maselli meant presumably sits in Wood's
>   body, unreachable from the abstract.
> - If the figure exists only in the primary source's body and full
>   text is inaccessible, the verdict is **unverifiable** as stated;
>   anchor the downstream claim to a different, verifiable primary
>   source and record the discrepancy on the intermediary's or
>   primary's brain page so the paraphrase is never quoted uncritically
>   again.

Session evidence: grounding an epidemiology sentence on a real R01
Specific Aims page. The clean anchor became Peters 2011 (Chest,
PMID 21622549 — 52% of refractory-asthma adults positive vs 2.9%
healthy controls, verified against PMC3148797 full text); Wood 2013
(PMID 23622002) was filed as a stub with an explicit caution flag
against quoting its pediatric figure without full-text verification.
