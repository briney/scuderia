---
name: structure-search
description: Enrich a therapeutic-antibodies corpus entry with PDB structures — resolve against the local SAbDab mirror by name AND by VH/VL sequence, then compute epitope contact residues from coordinates, and rewrite the entry's machine-owned Structures block. Use when an entry needs structures or a structure refresh.
triggers:
  - "get structures for <antibody>"
  - "enrich structures"
  - "structure-search this entry"
  - "compute the epitope contacts"
eval_contract:
  goal: |
    Every enriched entry carries a Structures block that finds what name search
    alone misses (structures deposited under code names), with epitope contacts
    that are honestly labeled as computed from coordinates — the ground truth
    layer for epitope-landscape work and the platform demo.
  dimensions:
    - "RECALL — was sequence search run (not just name search) before declaring none-found?"
    - "CORRECTNESS — are chain assignments taken from the SAbDab row, and do computed contacts match the named chains?"
    - "HONESTY — are contacts labeled computed-from-coordinates, and unliganded vs complex state reported per instance?"
    - "BLOCK DISCIPLINE — was only the Structures block rewritten?"
  hard_fails:
    - a PDB ID in the block that does not come from the mirror or the SAbDab API
    - declaring none-found after name search only
    - committing fetched mmCIF files to git
---

# structure-search — corpus structure enrichment

Fills the machine-owned `## Structures` block of a
`references/therapeutic-antibodies/entries/<slug>.md` record. SAbDab is the
primary source; RCSB supplies coordinates. Two retrieval modes are mandatory
in sequence: **name search** (mirror `compound` column) then **sequence
search** (SAbDab similarity API on the entry's VH/VL) — structures are
routinely deposited under code names (`4D5`, `mAb 3E8`) that name search can
never catch. Distinct from `antibody-sequence-search` (Sequences block) and
`therapeutic-antibody-registry` (curated fields).

> **Conventions:** `references/therapeutic-antibodies/templates/entry-template.md`
> (block schema), `references/therapeutic-antibodies/raw/mirrors/_mirror-manifest.md`
> (mirror provenance), `skills/conventions/raw-source-archive.md`.
> Paths under `references/` resolve from the brain root; `skills/…` per
> `skills/RESOLVER.md` §Path resolution.

## What this guarantees

- Every PDB in the block traces to the SAbDab mirror or its API — never memory.
- Chain assignments come from the SAbDab row, not from inspecting the file.
- Epitope contacts are computed from coordinates (4.5 Å all-atom cutoff,
  heterogens excluded) and labeled as computed.
- Only the `## Structures` block is written.

## Phases

1. **Mirror check.** Mirror at
   `references/therapeutic-antibodies/raw/mirrors/SAbDab_all_summary.tsv`:
   ```bash
   curl -sL --max-time 300 \
     "https://sabdab.opig.stats.ox.ac.uk/api/download/all-summary" \
     -o <mirror>.new
   ```
   Validate before replacing: header starts with `INSTANCE,` and row count
   exceeds 20,000. Canonical host is `sabdab.opig.stats.ox.ac.uk` — the
   `/webapps/newsabdab/api/...` path 301-redirects and downgrades POSTs to
   GETs; use the canonical host everywhere. Log refreshes in
   `_mirror-manifest.md`.

2. **Name search.** Run the lookup script in this skill's `scripts/`:
   ```bash
   python3 skills/structure-search/scripts/sabdab_lookup.py <INN> [<brand> <alias> ...]
   ```
   Substring match against `compound`; pass the entry's aliases/brand names
   too. Note the open problem: many therapeutic structures are deposited under
   code names and will NOT appear here — that is what phase 3 is for.

3. **Sequence search (mandatory).** Pull VH/VL from the entry's
   `## Sequences` block (chain it: run `antibody-sequence-search` first if
   absent) and run:
   ```bash
   python3 skills/structure-search/scripts/sabdab_lookup.py --vh <VH> --vl <VL> --threshold 95
   ```
   Defaults: full variable region when both chains given, VH-only/VL-only
   otherwise. Threshold 95 catches expression-construct variants; drop to 90
   for heavily engineered formats. If the Sequences block is `not-found` /
   `not-public`, say so and rely on name search alone — explicitly labeled
   lower recall.

4. **Dedupe and classify.** Merge name+sequence hits by `instance`; prefer
   the mirror row's metadata. The lookup script classifies each instance:
   `complex` (protein/peptide/nucleic-acid antigen — epitope-relevant),
   `complex-artifact` (protein A/G or MBP chaperone — real but not the
   therapeutic antigen; list it, never compute contacts on it),
   `additive-only` (hapten/ion/sugar crystallization additives — treat as
   unliganded), `complex-untyped` (older rows without antigen_type; inspect
   the antigen name and use judgment), `unliganded`. Multiple instances per
   PDB are separate rows (H/L chain pairs differ).

5. **Compute contacts (complex instances only).**
   ```bash
   python3 skills/structure-search/scripts/compute_contacts.py <pdb> \
     --h <H> --l <L> --antigen <comma-sep chains>
   ```
   mmCIFs land in `.sabdab-cif-cache/` (cwd-relative) — disposable; **never
   commit them** (RCSB is the immutable archive). If the PDB or chains are
   missing/renumbered, the script reports `_missing_chains` — record the
   instance as `contacts: not computed (chain mismatch)`, never hand-pick
   alternative chains without noting it.

6. **Compose + write wholesale.** Table per the template spec (PDB bare
   4-char, resolution, method, state, antigen, H/L chains, antigen chains),
   then per-complex contact lists keyed by PDB+instance, H-chain and L-chain
   contacts separately. Replace an existing `## Structures` block entirely;
   append at end of file otherwise. Set `Last refreshed`. Touch nothing else.

7. **Report.** Per entry: instances found (name-only / sequence-only / both),
   complexes vs unliganded, contacts computed. Bulk runs end with a coverage
   summary.

## Output

- The entry file with a rewritten/appended `## Structures` block per spec.
- Console report per phase 7.

## Anti-patterns

- Name search only — code-name deposits are the norm for therapeutics, and
  skipping sequence search silently halves recall.
- Treating computed contacts as database annotations, or database fields
  (SAbDab has no epitope annotation) as contacts.
- Committing `.sabdab-cif-cache/` or any mmCIF to git.
- Using the `/webapps/newsabdab/api/...` host for POSTs (301 → GET downgrade).
- Guessing chain assignments when the mirror row disagrees with the file.
- Patching anything outside the `## Structures` block.
