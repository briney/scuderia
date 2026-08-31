# heatmaps.md — style for heatmaps and similarity/competition matrices (tier 3)

> Type file for matrix figures: heatmaps, epitope-similarity matrices,
> competition matrices. Parent chain: `STYLE/STYLE.md` →
> `STYLE/plotting/plotting.md` → this file. Everything in the parent files
> applies unless overridden here for a stated reason.
>
> **Crystallized 2026-08-26** from a demonstrated run in the founding
> instance (heatmap iterations v1→v3 with user correction: binary blocks →
> graded clustermap). Split out of `plotting.md` 2026-08-28.

## 1. Cell encoding

- **Negative/empty cells are very light grey (`#F0F0F0`), never white** —
  white reads as "missing", light grey reads as "measured negative".
  White is reserved for gridlines. User correction; locked.
- **Grade intensity, don't binarize.** Default similarity metric is
  symmetric min-normalized overlap (shared / min(|A|, |B|)) —
  competition-style relations are symmetric, and min-normalization (not
  Jaccard) scores a small epitope nested in a large one as near-total
  overlap, which is the competition-relevant case.
- **Intensity ramps: data-stretch, then gamma 0.5.** Compute the observed
  distribution first (in the founding run the same-bin pairs sat at
  p∈[0.30, 0.97] — a 0–1 linear ramp wastes most of the range). Map
  p02→1.0 of the observed range onto the ramp, then apply t^0.5 to open
  the crowded top end. Locked after user compared linear / LC→HC /
  HSV-value variants. The ramp tops out at the palette color, not past it
  (`plotting.md` §2).

## 2. Axes and layout

- **Order matrix axes by average-linkage hierarchical clustering
  (distance = 1 − similarity). Do NOT draw dendrograms** — they clutter
  the plot area and add little perceptive value. User correction; locked.
- **White gridlines (~1.2 pt) between every cell** (pcolormesh
  `edgecolors="white"`), not just group boundaries; no frame (all spines
  off); no tick marks; x labels on top.
