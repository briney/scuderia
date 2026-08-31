# STYLE.md — ergon archetype template

> This is the **template** for an ergon instance's visual-artifact standard.
> At scaffold time (`scuderia init`) the whole `STYLE/` tree is copied into
> the new instance. The copy is instance-owned: divergence from this
> template is expected and correct, because style is crystallized from the
> instance's own corrected runs (§5 of the spine). When a run earns generic
> craft worth sharing, back-port it here with the `style-promote` skill.
>
> The template is opinionated by design (the mnemo precedent): the
> palettes, tracks, and locked mechanics below are the founding instance's
> demonstrated defaults, kept generic — dates and "demonstrated run"
> language; the instance's run log is the full provenance record. An
> instance that wants different values swaps them freely; the *mechanisms* —
> one canonical palette, assets enforce, provenance on artifacts,
> crystallization over speculation — are load-bearing and worth keeping.
>
> Everything below the line is the template body.
>
> ---

# STYLE.md — {{INSTANCE_NAME}}'s style spine (tier 1)

> {{INSTANCE_NAME}}'s standard for the *appearance* of produced artifacts —
> figures, structure renders, tables, decks. Its companions are `SOUL.md` §5
> (conversational voice) and this file's modality and type descendants,
> which carry the detail. This file is the spine: it is short enough to be
> read on every commission that produces a visual artifact, and it routes
> to the file that governs the artifact at hand.
>
> This directory is instance-owned: it was scaffolded from the ergon
> profile's STYLE template and may diverge from it freely — divergence is
> expected (§5). Generic improvements earned here are back-ported upstream
> with the `style-promote` skill; the profile template carries the generic
> form.
>
> Four commitments govern everything below: the **ethos** of Tufte and
> Cleveland orients every aesthetic judgment (§2); style is **enforced by
> assets, not by prose alone** (§3); every artifact records **which style
> version made it** (§4); and style content is **crystallized from
> demonstrated runs, never written speculatively** (§5).

## 1. Scope and tiers

Style governs how a produced artifact *looks*: color, typography, layout,
rendering mechanics, figure structure. Two things sit outside it. What an
artifact *contains* — which analysis, which residues, which comparison —
is the commission, not style. And how {{INSTANCE_NAME}} *talks* — in
conversation or in prose documents — is `SOUL.md` §5, not this directory.

Style content lives at three tiers:

1. **Universal** (this file + `assets/palettes.yaml`) — holds for every
   visual artifact, any modality.
2. **Modality** (`plotting/plotting.md`, `structures/structures.md`) —
   holds for every artifact of one modality.
3. **Type** (`plotting/heatmaps.md`, `structures/fv-antigen.md`, …) —
   holds for one figure or render type.

Load only what the commission needs: the spine always, the modality file
when producing that modality, the type file only when producing that
type. Each descendant file names its parent chain in its header. When
tiers disagree, **the most specific tier wins**, and the artifact
manifest records the override (§6).

## 2. Ethos (Tufte / Cleveland)

Two questions govern every visual artifact. Tufte's: *what can be
removed, integrated, or made more information-bearing?* Cleveland's:
*what judgment must the viewer make, and does the encoding support it
accurately?*

- **Show the evidence; quiet the scaffolding.** The subject — data,
  interface, structure — carries the visual weight; axes, grids,
  surfaces, and frames stay subordinate. When subject and scaffolding
  compete, scaffolding loses. (The ghost antigen is already this
  principle, rendered.)
- **Every mark earns its place.** If erasing an element loses no
  information, erase it — then ask again of what remains. Erasure stops
  where it starts destroying orientation or honesty: minimalism is a
  means; emptiness is not the goal.
- **The visual never overstates the evidence.** Emphasis proportional to
  effect; no drama the data did not earn. A render that makes a weak
  contact look intimate lies the same way a truncated axis does.
- **Density through arrangement, never through simplification.** Rich,
  layered artifacts that read at a glance *and* survive close
  inspection. To clarify, add detail — arranged.
- **Beauty is a byproduct.** Clear, truthful, dense, well-proportioned
  artifacts are beautiful; decorated ones are not.

This ethos is direction, not procedure: §3's assets enforce mechanics;
this section governs judgment — the part of style that cannot be
enforced, only practiced. Adopted by human direction 2026-08-28,
distilled from Tufte and Cleveland. Modality files translate it; they do
not repeat it.

## 3. Assets enforce; prose explains

A style guideline that exists only as prose drifts. Every enforceable rule
in this directory has a machine-readable asset under `STYLE/assets/` that
carries it out — a palette definition, a matplotlib style sheet, a
ChimeraX preset script. The modality and type files explain the rationale,
the edge cases, and when deviation is warranted; the asset is what
actually executes. When the two disagree, the asset is wrong until a
human says otherwise — prose is the record of intent.

One canonical palette lives in `assets/palettes.yaml`. Every tier
references it. A chain that is one color in a structure render is the same
color in the accompanying plot, because both read the same file. Never
define a color twice.

## 4. Provenance

Every visual artifact's `manifest.json` records which style governed it:
the asset paths with hashes, and the style *files* loaded (path + git
state) at each tier. An artifact that cannot say which palette, which
preset, and which rules produced it is unfinished — this is `SOUL.md` §2
applied to appearance. When a style asset or file changes, old artifacts
keep pointing at the version that made them.

## 5. Crystallization, not speculation

Style content is earned the same way skills are: a file gains a rule when
a real run demonstrates it — typically when the human corrects a
rendering or figure choice, and the correction is written down. Do not
fill these files with plausible-sounding defaults in anticipation of need.
An empty section is an honest section; an invented rule is a future error.
New modality and type files are created the same way: when a demonstrated
run needs one, not before. (The single exception is §2: ethos is adopted
by human direction, not earned per-run.)

## 6. Universal principles

Defaults that hold across every modality and type unless a more specific
file overrides them for a stated reason:

- **Colorblind-safe by default.** Categorical palettes must survive
  deuteranopia. If a scheme cannot, the overriding file must say why and
  what the accommodation is.
- **Consistency within a commission.** All artifacts produced for one
  commission share palette, typography, and conventions — enforced by
  §3's shared assets, not by memory.
- **Semantic entities get fixed palette slots, assigned once per
  project.** STYLE defines the slots (`assets/palettes.yaml`); a project
  assigns its entities (mAbs, epitope bins, antigens) to slots once and
  records the assignment in the project (e.g.
  `projects/<slug>/palette.yaml`). The assignment is identical across
  modalities — an antibody that is sky in the binding curves is sky in
  the render — because both read the same assignment. The assignment is
  project state; this rule is style.
- **Deviation is allowed, undocumented deviation is not.** Any tier may
  be overridden for a specific artifact; the manifest records the
  override and the reason.

## 7. Routing

Load the modality file for the artifact you are producing, then the type
file it routes to. The spine alone is never enough to render or plot
with.

| Producing a... | Load |
|---|---|
| Figure, plot, or chart | [`plotting/plotting.md`](./plotting/plotting.md) |
| Structure render or session (ChimeraX, PyMOL) | [`structures/structures.md`](./structures/structures.md) |

New modalities and types are added the same way content is: when a
demonstrated run needs one.
