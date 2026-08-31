# structures.md — style for structure renders and sessions (tier 2)

> Modality file for molecular graphics: ChimeraX and PyMOL sessions,
> still renders, and animations. Governs appearance rules that hold for
> **every** render — what to render is the commission's business; rules
> for one render type live in a type file (see Routing below).
> Parent chain: `STYLE/STYLE.md` (spine) → this file → type files.
> Most-specific-wins: a type file may override this file for a stated
> reason; the artifact manifest records the override.
> Enforcing assets live under `STYLE/assets/`; the canonical palette is
> `STYLE/assets/palettes.yaml`.
>
> **Crystallized 2026-08-26** from a demonstrated run in the founding
> instance (PD1–Fab complexes 5ggs/5wt9, iterated v1–v10 with user
> correction). Tier split 2026-08-28: Fv-on-ghost-antigen rules moved to
> `fv-antigen.md`.
>
> Ethos mapping (spine §2): the rules below are the Tufte/Cleveland ethos
> applied to molecular graphics — the Fv and its interface are the
> "data"; the ghost antigen, neutral ligands, and restrained geometry are
> the quieted scaffolding; the locked tracks exist so emphasis stays
> proportional to what matters in the structure.

## 1. Coloring

**Two locked tracks, chosen per project** (per commission, not per
figure). Values and LC generation rule live in `STYLE/assets/palettes.yaml`;
ChimeraX presets in `STYLE/assets/chimera/` (`charcoal_ghost.cxc`,
`warm_paper_ghost.cxc`).

- **bright_on_charcoal** — high-key Fv colors on a dark neutral ghost
  (`#5C5C5C` surface / `#2B2B2B` cartoon). Modern, high-contrast.
- **muted_warm_on_paper** — muted warm Fv colors on a warm paper-grey
  ghost (`#B0A99F` surface / `#5A544C` cartoon). Printed-page, mature.

Rules that hold for both:

- **Antigen is always neutral; antibodies carry the color.** Antigen
  greys must be hue-free or deliberately warm — a blue-leaning "grey"
  (e.g. `#555B66`, `#9AA1AC`) reads purple under soft lighting. This was
  the first user correction of the run; do not reintroduce slate greys.
- **HC/LC pairs: same hue, LC generated not picked.** LC = HC hue, HSV
  saturation × 0.65, value unchanged. Locked at 65% after comparing
  50–70% on rendered structures; the target is "clearly distinguishable,
  but subtle." On the muted-warm track the 65% step is very small —
  acceptable default; lighten LC value +10% only when a specific render
  needs it, and record the deviation in the manifest.
- **Glycans and ligands stay white/neutral** so they don't add a
  competing color.
- **Confusable pair to watch (charcoal track):** sky vs. teal under
  deuteranopia — avoid on adjacent antibodies in one render.

## 2. Representation

- **Cartoon geometry is locked: `cartoon style width 1 thickness 1
  xsection oval divisions 2`.** User-locked 2026-08-26 after a composite
  rebuild — the low-poly oval ribbon reads cleaner and matches the
  EM-adjacent aesthetic of the density figures. Applies to every cartoon
  in every render/session (Fv, antigen-through-ghost, everything).

## 3. Rendering mechanics

- **Scene defaults:** white background, `graphics silhouettes true`,
  `lighting soft`. Export PNG 1800×1350, `supersample 3`.
- **`color ... target s` resets surface alpha to opaque.** Transparency
  must be (re-)applied AFTER every surface recolor. A "ghost" that
  renders opaque is this bug until proven otherwise.
- **Headless ChimeraX cannot rasterize** (no OpenGL in `--nogui`;
  `--offscreen` has no OSMesa). Renders require GUI mode.
- **Verification is part of the render.** Every render script dumps
  scene state to a text file: per-chain ribbon/atom display counts and
  the MolecularSurface RGBA. Ghost = alpha ≈102 (60%); Fabs = 0 atoms
  shown. Check the dump before shipping the PNG; pixel-hue histograms
  confirm the palette landed. (The founding run shipped an opaque "ghost"
  and a full-Fab "Fv" before this discipline was added.)

## 4. Sessions and scripts

- cxc command errors are **silent in GUI mode**: the script halts, the
  app stays open, no PNG, no error on stdout. Validate the full command
  sequence in `--nogui` mode first when iterating.
- Syntax traps hit in the founding run: `delete /G,H,L solvent` is
  invalid (spec and keyword don't mix — use `delete solvent`); open-ended
  ranges (`:121-`) are invalid (use explicit ends); `session.models[-1]`
  after `open` can be a submodel (`2.1`) — prefer chain-only specs, which
  are model-agnostic.
- Preset scripts live in `STYLE/assets/chimera/`; run scripts for a
  commission live in its run dir, not in STYLE.

## 5. Routing

Load the type file for the render you are producing, in addition to this
file. Type files carry type-specific rules only; everything above still
applies unless the type file overrides it.

| Producing a... | Load |
|---|---|
| Antibody Fv(s) on a ghost antigen surface | [`fv-antigen.md`](./fv-antigen.md) |

New type files are added the same way content is: when a demonstrated run
needs one (`STYLE/STYLE.md` §5).
