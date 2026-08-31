# assets/ — the enforcing layer

Machine-readable style assets. Prose rules in the modality and type
files (`../plotting/plotting.md`, `../structures/structures.md`, and the
type files beside them) point here; assets are what
actually execute. The spine (`../STYLE.md` §3) governs: assets enforce,
prose explains, colors are defined once in `palettes.yaml`.

Contents:

- `palettes.yaml` — the ONE canonical palette. Locked tracks:
  `bright_on_charcoal` and `muted_warm_on_paper`, plus the LC generation
  rule (hue = HC, HSV saturation × 0.65, value unchanged).
- `chimera/charcoal_ghost.cxc`, `chimera/warm_paper_ghost.cxc` — ChimeraX
  presets: named colors + scene defaults, generated from `palettes.yaml`.
  Edit the YAML, regenerate the presets — never the reverse.

Planned (created when first needed by a demonstrated run — `../STYLE.md` §5):

- `<instance>.mplstyle` — matplotlib style sheet encoding the plotting
  mechanics defaults.
- `pymol/` — PyMOL preset scripts.

Every artifact manifest that uses an asset records the asset path and
its hash (`../STYLE.md` §4).
