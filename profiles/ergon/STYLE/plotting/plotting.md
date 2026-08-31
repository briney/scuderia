# plotting.md — style for figures, plots, and charts (tier 2)

> Modality file for data graphics: matplotlib and anything else that
> produces a figure. Governs appearance and figure mechanics that hold for
> **every** plot type — what to plot is the commission's business; rules
> for one plot type live in a type file (see Routing below).
> Parent chain: `STYLE/STYLE.md` (spine) → this file → type files.
> Most-specific-wins: a type file may override this file for a stated
> reason; the artifact manifest records the override.
> Enforcing assets live under `STYLE/assets/`; the canonical palette is
> `STYLE/assets/palettes.yaml`.
>
> **Crystallized 2026-08-26** from a demonstrated run in the founding
> instance. Tier split 2026-08-28: heatmap-specific rules moved to
> `heatmaps.md`. §1 Principles adopted by human direction 2026-08-28 (the
> spine's §2 ethos translated to data graphics).

## 1. Principles

The spine's ethos (§2) applied to data graphics. These orient judgment;
they are defaults to start from, not bans — deviation is allowed with a
recorded reason (`STYLE/STYLE.md` §6). Locked rules elsewhere in this
file and its type files still bind.

- **Encode by perceptual accuracy (Cleveland).** Default order for
  quantitative judgment: position on a common scale → length → slope and
  angle → area → color intensity. Hue distinguishes categories; it is
  not a numerical ruler. Choose the highest-ranked encoding that fits
  the data and the question; break the order only for a stated domain
  reason.
- **Scales are chosen, not inherited.** Aspect ratio and axis limits are
  deliberate decisions, never the library default accepted unexamined.
  Zero baseline where length encodes magnitude; position encodings may
  use a justified non-zero baseline. Label transformations (log,
  normalization) when they could change interpretation.
- **Prefer direct labels over legends** when it doesn't create clutter;
  sort categories by an analytically useful variable rather than
  alphabetically; integrate words and numbers near the marks they
  explain.
- **Gray + one accent before any multi-hue scheme.** Start neutral; add
  color only where it carries meaning, and let semantic entity colors
  come from the palette slots (`STYLE/STYLE.md` §6), never ad hoc.
- **Density is welcome; crowding is not.** Small multiples and shared
  scales over overplotted spaghetti; the pattern should read at a glance
  and the values survive close inspection.

## 2. Color

- **Semantic entities that recur across figures get fixed colors, defined
  once in `assets/palettes.yaml`.** In a panel project each epitope bin
  gets a fixed hue (bright_on_charcoal antibody track), and the hue is
  identical across the heatmap and the structure render — a figure pair
  must never drift apart in its shared encoding. Entity→slot assignment
  is project state, recorded per project (`STYLE/STYLE.md` §6).
- **When a figure encodes intensity of a property that a structure render
  also shows, the ramp must top out at the palette color, not past it.**
  Ramps that darken or desaturate beyond the palette hue (e.g. value<1
  HSV ramps) visually disconnect the figure from the structure. User
  correction; locked.

## 3. Plot mechanics

- **Ship two variants of presentation figures**: full (title + legend)
  and bare (axis labels only). User preference from the founding
  instance's pilot.
- **Layout pitfall: `tight_layout()` squashes equal-aspect axes flat.**
  Use explicit `subplots_adjust` for equal-aspect figures with external
  legends. (v1 of the corrected heatmap shipped squashed; caught by
  aspect-ratio check.)

## 4. Typography

- **Type scale for a ~6×4 in (mpl-default-size) figure: axis labels
  14 pt, tick labels 12.5 pt.** User-locked 2026-08-26 on the bare
  binding-curves plot. Keep the hierarchy: axis labels ~1.5 pt above tick
  labels. Scale proportionally for larger figures.
- **Data curve weight is 1.75 pt** at that size (thin 1.0–1.2 weights read
  as anemic once fonts go up). Locked with the type scale.

## 5. Figure structure

- **Verification is part of the figure.** Pixel-match every expected
  palette color in the PNG (and the grey field / white gridlines where
  structural) before shipping; check the aspect ratio against intent.
  The agent cannot see figures — pixel checks are the eyes.

## 6. Routing

Load the type file for the figure you are producing, in addition to this
file. Type files carry type-specific rules only; everything above still
applies unless the type file overrides it.

| Producing a... | Load |
|---|---|
| Heatmap / similarity or competition matrix | [`heatmaps.md`](./heatmaps.md) |

New type files are added the same way content is: when a demonstrated run
needs one (`STYLE/STYLE.md` §5).
