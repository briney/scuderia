# fv-antigen.md — style for Fv-on-ghost-antigen renders (tier 3)

> Type file for renders of antibody Fv(s) bound to an antigen shown as a
> ghost surface. Parent chain: `STYLE/STYLE.md` →
> `STYLE/structures/structures.md` → this file. Everything in the parent
> files applies unless overridden here for a stated reason.
>
> **Crystallized 2026-08-26** from a demonstrated run in the founding
> instance (PD1–Fab complexes 5ggs/5wt9, iterated v1–v10 with user
> correction). Split out of `structures.md` 2026-08-28.

## 1. Composition

- **Default view is Fv-only cartoon, ghost antigen surface.** Show the
  antibody Fv (VH + VL), not the full Fab — the constant domains clutter
  and pull the eye from the interface. User correction, locked.
- **Fv boundaries come from sequence, not round numbers.** Cut VH at the
  CH1 junction (`…VTVSS|ASTKGPS`) and VL at the Cκ junction (`…EIK|RTVAAPS`);
  in the founding run's PD1 templates that was HC 2–120 / LC 1–111 (5ggs)
  and 1–120 / 1–111 (5wt9). Verify per antibody. (AF predictions are
  often already Fv-only — check the termini before trimming.)
- **Ghost surface: antigen surface at 60% transparency with the antigen
  cartoon visible through it** (surface lighter, cartoon darker). Strongly
  preferred over opaque. Locked after v5a/v5b comparison. Remember:
  recoloring a surface resets its alpha — re-apply transparency after
  every recolor (`structures.md` §3).

## 2. Multiple antibodies on a shared antigen

- Superpose by the antigen (`matchmaker /Ag2 to /Ag1` — chain-only
  specs), cartoon-hide the duplicate antigen chains.
- Each antibody gets its own palette slot, assigned once per project and
  identical to the slot used in accompanying figures (`STYLE/STYLE.md`
  §6). Watch the confusable pairs flagged in `structures.md` §1 when
  assigning adjacent antibodies.
