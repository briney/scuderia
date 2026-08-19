---
name: antibody-sequence-search
description: Enrich a therapeutic-antibodies corpus entry with VH/VL sequences — resolve the molecule against the local Thera-SAbDab mirror, classify coverage honestly, and rewrite the entry's machine-owned Sequences block. Use when an entry needs sequences or a sequence refresh.
triggers:
  - "get sequences for <antibody>"
  - "enrich sequences"
  - "sequence-search this entry"
  - "refresh the sequence block"
eval_contract:
  goal: |
    Every enriched entry carries a Sequences block that is complete, honestly
    sourced, and per-arm correct — so an in silico discovery pipeline can
    trust corpus sequences as ground truth without re-verification.
  dimensions:
    - "RESOLUTION — did the skill exhaust the resolution ladder (exact → suffix-strip → cocktail-split → parent fallback) before declaring not-found?"
    - "HONESTY — are status, source, and maturity labeled per chain; are provenance conflicts stated rather than silently resolved?"
    - "SCHEMA — does the block match the entry-template Sequences spec exactly (per-arm groups, raw AA, no IMGT numbering)?"
    - "BLOCK DISCIPLINE — was only the Sequences block rewritten, with curated blocks untouched?"
  hard_fails:
    - a sequence written into an entry that does not come from the mirror or another cited source
    - declaring not-found while a parent-antibody or cocktail-component lookup would have hit
    - hand-editing any non-Sequences block in the entry
---

# antibody-sequence-search — corpus sequence enrichment

Fills the machine-owned `## Sequences` block of a
`references/therapeutic-antibodies/entries/<slug>.md` record. Sequences are the
foundation layer for the in silico discovery pipeline, so honesty beats
coverage: a correct `not-found` is a good outcome, an invented sequence is a
hard fail. Distinct from `therapeutic-antibody-registry` (which builds and
maintains the corpus's curated fields) — this skill owns exactly one
machine-generated block.

> **Conventions:** `references/therapeutic-antibodies/templates/entry-template.md`
> (the block schema), `references/therapeutic-antibodies/raw/mirrors/_mirror-manifest.md`
> (mirror provenance + gotchas), `skills/conventions/raw-source-archive.md`
> (what may live in-repo). Paths under `references/` resolve from the brain
> root; `skills/…` resolves per `skills/RESOLVER.md` §Path resolution.

## What this guarantees

- Every sequence in the block traces to the Thera-SAbDab mirror or an
  explicitly cited fallback source — never model memory.
- Multispecifics get one arm group per binding specificity; cocktails get one
  per component; ADCs inherit the parent mAb's arms, labeled as parent-derived.
- `sequence_status` reflects reality: `complete` | `partial` | `not-found` |
  `not-public` | `not-applicable` (Fc-fusions have no Fv).
- Only the `## Sequences` block is written; the rest of the entry is untouched.

## Phases

1. **Mirror check.** The mirror lives at
   `references/therapeutic-antibodies/raw/mirrors/TheraSAbDab_SeqStruc_OnlineDownload.csv`
   and must exist and be fresh enough for the job (bulk runs: refresh at run
   start):
   ```bash
   curl -sL --max-time 120 \
     "https://opig.stats.ox.ac.uk/webapps/sabdab-sabpred/static/downloads/TheraSAbDab_SeqStruc_OnlineDownload.csv" \
     -o <mirror>.new
   ```
   Validate before replacing: first line must start with `Therapeutic,` and row
   count must exceed 1000. A failed fetch (404 HTML, truncation) must never
   overwrite a good mirror. Log the refresh in `_mirror-manifest.md`.

2. **Resolve identity.** Read the entry's Identity + Relations blocks. Modality
   gate first: `fc-fusion` → `not-applicable` (no Fv); `car-t`/`car-nk` →
   expect `not-public` (verify in mirror anyway). Then run the lookup script in
   this skill's `scripts/` directory:
   ```bash
   python3 skills/antibody-sequence-search/scripts/therasabdab_lookup.py <INN-or-slug>
   ```
   (profile-root-relative path — on Hermes, under
   `~/.hermes/profiles/<instance>/skills/atticus/antibody-sequence-search/`.)
   The script implements the ladder: exact → suffix-strip → cocktail-split.
   For ADCs (`modality: adc`/`immunoconjugate`), look up the curated
   `Parent antibody` and label arms `parent-derived: <parent slug>`.
   For cocktails, look up each component INN separately.

3. **Fallback ladder (only if the mirror misses).** (a) PLAbDab keyword
   search — `python3 skills/patent-search/scripts/plabdab_lookup.py --keyword
   <target-or-code-name>` against the paired mirror; a sequence found here is
   cited `PLAbDab:<ID>` (patent-sourced, literature-annotated). (b) IMGT/mAb-DB
   via web — cite `IMGT/mAb-DB` as source. (c) if a structure exists in the
   PDB, the sequence can be read off the coordinates — hand a note to
   `structure-search` and cite `pdb:<id>`. (d) otherwise mark `not-found` and
   leave a one-line handoff note for `patent-search` (sequence listings are
   its job — never duplicate that machinery here).

4. **Compose the block.** Follow the template spec exactly. Per chain:
   `- **VH** (<len> aa, Thera-SAbDab, mature (variable domain)): \`<seq>\``.
   Arm-target assignment from Thera-SAbDab column order is a heuristic —
   cross-check against the entry's curated Architecture / Target assignments
   and say so if they disagree. Fc engineering: mirror the entry's curated
   Isotype/Fc value if present, else `None reported by source`. Provenance
   conflicts (e.g. mirror vs. curated knowledge) go in the conflict field with
   both variants — never silently pick one.

5. **Write wholesale.** Replace an existing `## Sequences` block entirely
   (it is machine-owned); append at end of file if absent. Set
   `Last refreshed`. Do not touch any other block.

6. **Report.** One line per entry: status, arms found, match_kind, conflicts.
   For bulk runs, end with a coverage summary (complete / partial / not-found /
   not-public / not-applicable counts).

## Output

- The entry file with a rewritten/appended `## Sequences` block per the
  template spec.
- Console report per phase 6.

## Anti-patterns

- Writing a sequence from memory or from an uncited source.
- Overwriting a good mirror with a failed download (validate first — the
  `INNwithnoSeq` companion file 404s while linked; downloads can lie).
- Treating Thera-SAbDab sequences as full chains — they are variable domains
  only; the block must say so.
- Looking up an ADC by its conjugate name and declaring not-found without the
  parent fallback (Thera-SAbDab keys ADCs by parent mAb only).
- Silently choosing one variant when sources disagree.
- Patching anything outside the `## Sequences` block.
