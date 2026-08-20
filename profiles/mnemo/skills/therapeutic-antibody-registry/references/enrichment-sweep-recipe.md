# Bulk enrichment sweep recipe

Proven pattern for enriching antibody entries with sequences, structures,
and IP blocks via delegated subagent batches. Validated on Tier A (2026-08-18)
and Tier B (2026-08-19). Covers fresh sweeps and interrupted-sweep resumption.

## Prerequisites

- Entries exist in `entries/` with curated blocks (Identity, Provenance, etc.)
- Three enrichment skills installed: `antibody-sequence-search`, `structure-search`, `patent-search`
- Three mirrors populated in `raw/mirrors/`: TheraSAbDab CSV, SAbDab summary TSV, PLAbDab paired sequences
- Entry template has the three machine-owned block specs (Sequences, Structures, IP & exclusivity)

## Block header reference

The three machine-owned block headers (use these EXACT strings in any scan):

| Block | Header | Owner skill |
|---|---|---|
| Sequences | `## Sequences` | `antibody-sequence-search` |
| Structures | `## Structures` | `structure-search` |
| IP & exclusivity | `## IP & exclusivity` | `patent-search` |

**Pitfall:** The IP block is `## IP & exclusivity`, NOT `## Patents`. Scanning
for `## Patents` will find zero matches and produce a false "no entries have IP"
conclusion. This cost a full diagnostic cycle in the 2026-08-19 resumption.

## Batch planning

1. **Scan all entries** for existing machine-owned blocks. Skip entries that already
   have all three. Flag Fc-fusions (modality: fc-fusion) — they get not-applicable
   blocks, not enrichment. Flag CAR-T (modality: car-t) — they get not-public blocks.
2. **Build batches of 4-5 entries** each. Group alphabetically; the pipeline is
   uniform per entry so grouping by area is not necessary.
3. **Count**: enrichable entries / 5 per batch = N batches. With
   max_concurrent_children=3, that's ~N/3 sequential waves.

## Delegation wave pattern — follow `batch-drain`

Load `skills/batch-drain/SKILL.md` and follow its dispatch/yield/verify loop
for the whole sweep; the per-entry pipeline below overrides only *what* each
subagent does, never the scheduling discipline. Specifically:

Each wave dispatches batches of 4-5 entries. Each subagent:
1. Reads its entry files + the template
2. Runs `therasabdab_lookup.py` for each entry's INN
3. Runs `verify_sequence.py` to confirm against PDB structures
4. Runs `sabdab_lookup.py` (name + sequence search) for each entry
5. Runs `compute_contacts.py` for each complex structure found
6. Runs `plabdab_lookup.py` (exact VH/VL match) for patent candidates
7. Runs `google_patents_lookup.py` (name search; 503 is transient — fall back to PLAbDab)
8. Optionally runs `blast_pat.py` (NCBI pataa BLAST for CoM — slowest step, queued)
9. Writes only the three machine-owned blocks into each entry file

**Yield and wait between waves.** Do not dispatch a new wave while the prior
one is in flight (see `batch-drain` — the core invariant). A wave's result has
*returned* only when its consolidated result re-enters the conversation, not
when its dispatch notice appears. This is the fix for the truncation loop and
the dropped-remainder failure seen in the 2026-08-19 Tier B run.

**Context passed to each subagent**: working directory, entry names, script paths,
mirror paths, modality-specific instructions (ADC parent lookup, bispecific per-arm,
cocktail per-component, CAR-T not-public), and the "if Google Patents 503, use
PLAbDab only" fallback.

## Post-sweep cleanup (mandatory)

After all waves complete:

1. **Check disk, not subagent reports.** Subagents can timeout (1800s) while
   having successfully written files. Count blocks on disk:
   ```python
   blocks = sum(["## Sequences" in text, "## Structures" in text, "## IP & exclusivity" in text])
   ```
   Any entry with <3 blocks needs re-dispatch or manual completion.

2. **Normalize status values.** Subagents produce inconsistent formats:
   - Backtick-wrapped: `` `complete` `` -> `complete`
   - Trailing periods: `complete.` -> `complete`
   - Parenthetical notes in status field: move to next line
   Run a normalization pass with string replacements across all entry files.

3. **Write not-applicable blocks for Fc-fusions** (8 entries in Tier A). These have no Fv
   domain — sequence_status = `not-applicable`, structure_status = `none-found`,
   ip_status = `not-searched`. Write directly, do not delegate.

4. **Write not-public blocks for CAR-T** (6 entries in Tier A). scFv sequences are
   proprietary. sequence_status = `not-public`, structure_status = `none-found`,
   ip_status = `not-searched` (or `candidates-found` if name-based patents exist).
   Write directly, do not delegate.

5. **Clean up temp files.** Subagents leave JSON dumps in the working directory
   (`blast_results.json`, `enrichment_cache/`, `.enrichment_tmp/`, etc.). Add
   these to `.gitignore` and `git rm --cached` them before committing.

6. **Regenerate index files** with enrichment coverage columns (Seq | Struct | IP
   status per molecule).

7. **Verify curated-block integrity.** A subagent may overwrite the entire file
   with only enrichment blocks, destroying the curated header (Identity,
   Provenance, Mechanism, Sources). This is not caught by step 1 (which only
   checks for machine-owned block presence). Run a check that every enriched
   entry still has `## Identity` — if any are missing, the subagent clobbered
   the header. Recovery: `git show <skeleton-commit>:<path>` retrieves the
   original content; split the current file at `## Sequences` to isolate the
   enrichment blocks, then reassemble as
   `original_header.rstrip() + "\n\n" + enrichment_blocks`. This happened to
   5 entries during the Tier A sweep and was only detected when the index
   regeneration showed "Unknown" modality for those entries.

## Resuming an interrupted sweep

When a sweep is interrupted (API flake, timeout, session end), resumption
follows a specific assessment-then-continue pattern:

1. **Inventory block coverage on disk.** Write a Python script (not a shell
   one-liner — complex grep/awk logic triggers the command-size blocker) that
   scans every entry file for the three machine-owned block headers. The
   exact headers are `## Sequences`, `## Structures`, and `## IP & exclusivity`.
   Categorize entries as: all-3-present, partial (some blocks missing), or
   none (bare skeleton). This triage is the only reliable way to know what the
   interrupted sweep actually completed — subagent reports and git status
   are not sufficient.

2. **Commit completed work first.** Interrupted sweeps leave enriched entries
   uncommitted in the working tree. Commit them with a descriptive message
   *before* starting new delegation — otherwise the auto-pusher may bury real
   intent under a generic snapshot message, and new subagent writes may
   interleave with old ones in the same diff.

3. **Pre-check Thera-SAbDab hits for all pending entries.** Before writing
   delegation context, run a single batch `therasabdab_lookup.py` call with all
   pending INNs. This flags:
   - Exact hits (most entries) — subagent can proceed directly
   - Cocktail splits (e.g., relatlimab-nivolumab, zeleciment-rostudirsen) —
     tell the subagent to look up each component separately
   - Not-founds (e.g., zebetuzumab) — subagent writes not-found block, skips
     to name-only patent search
   This pre-check takes seconds and dramatically improves delegation quality.

4. **Group remaining entries by what they need.** Partially-enriched entries
   (e.g., have Sequences + Structures but missing IP) need only the missing
   block, not the full 3-step pipeline. Dispatch them as a separate batch with
   instructions to only write the missing block.

5. **Delegate in parallel batches.** Same pattern as the original sweep:
   batches of 4-5 entries, 3+ concurrent subagents, each running the chained
   pipeline (sequences -> structures -> IP). For entries missing only IP,
   the subagent skips steps 1-2.

### Pitfall: Tier B entries are sparser than Tier A

Tier B skeletons from ClinicalTrials.gov carry `Target(s): Unknown` and
`source_quality: low` — they have INN and therapeutic area but little else.
The enrichment scripts work fine with this (Thera-SAbDab keys by INN, not
target), but do not expect the curated blocks to be populated. The
enrichment blocks are often the first substantive data in the entry.

## Coverage results — Tier A (2026-08-18)

- 182/182 entries with all 3 blocks
- Sequences: 162 complete (89%), 8 not-applicable, 6 not-public, 5 not-found, 1 partial
- Structures: 97 complex with computed epitope contacts (53%), 7 unliganded-only, 78 none-found
- IP: 162 candidates-found (89%), 12 not-searched, 8 none-found
- Google Patents 503 throughout — PLAbDab + BLAST fallback used exclusively
- 199 files changed, 16,739 insertions in the commit

## Coverage results — Tier B (2026-08-19, complete)

- 134/134 entries with all 3 blocks
- Sequences: 112 complete/partial (84%), 22 not-found, 1 not-applicable (Fc-fusion)
- Structures: 8 with complex structures + computed epitope contacts, 126 none-found
- IP: 108 candidates-found, 26 none-found/not-searched
- Google Patents 503 throughout both waves — PLAbDab + NCBI efetch used as fallback
- 5 entries from the Tier A sweep had clobbered curated headers — recovered
  from skeleton commit and merged with enrichment blocks (see step 7)
- Final corpus: 321 entries (182 Tier A + 139 Tier B), all enriched
- First wave: 117 files committed (74d869af), second wave: 40 files (4e73816c)

## Time budget

- Each subagent batch (4-5 entries): 400-1100s (BLAST patent search is the bottleneck)
- Full Tier A sweep (35 batches, 12 waves): ~30 minutes wall clock
- Post-sweep cleanup: ~5 minutes
- Total: ~35 minutes for 182 entries
