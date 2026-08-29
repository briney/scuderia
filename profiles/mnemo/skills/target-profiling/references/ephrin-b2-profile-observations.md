# Ephrin-B2 (EFNB2) — profile observations

Profile: working-docs/hitlist-profiles/ephrin-b2.md
Date: 2026-08-17
Tier: preclinical (neuroscience)
UniProt: P52799 (human), P52800 (mouse), A6IWT6 (rat)
Papers: 5 ingested (3 full-text via PMC XML, 2 abstract-only — front-matter-only PMC XML)
Size: ~38K chars, 11 PMID citations

## Key new patterns

### 1. Species cross-reactivity computation — naive alignment gives wildly wrong identity

When computing human/mouse sequence identity for field 2 (species
cross-reactivity), a naive position-by-position comparison of the raw
UniProt `SQ` sequence blocks gave **9.9% identity** — obviously wrong for
a highly conserved mammalian protein. The cause: the mouse sequence
(P52800, 336 aa) has a **3-residue N-terminal extension** relative to
the human (P52799, 333 aa). Without accounting for this offset, every
position is misaligned and the identity calculation is meaningless.

**Fix — sliding-offset alignment.** Before computing pairwise identity,
find the best alignment offset by sliding one sequence against the other
over a small range (±10 residues) and scoring matches at each offset:

```python
best = (0, 0, 0)  # (matches, length, offset)
for off in range(-10, 11):
    h2, m2 = human_seq, mouse_seq
    if off > 0:  m2 = mouse_seq[off:]
    elif off < 0: h2 = human_seq[-off:]
    n = min(len(h2), len(m2))
    same = sum(1 for a, b in zip(h2[:n], m2[:n]) if a == b)
    if same > best[0]:
        best = (same, n, off)
print(f"Best: {100*best[0]/best[1]:.1f}% at offset {best[2]}")
```

With the offset applied, human/mouse EFNB2 showed **96.1% identity**
overall and **97.4% in the mature extracellular region** (after signal
peptide cleavage) — the correct, expected conservation level.

**Generalizable rule:** Always compute species cross-reactivity with an
offset search, not a naive zip. N-terminal signal-peptide length
differences and minor isoform variations are common across orthologs
and will corrupt a position-by-position comparison. Report the
offset-adjusted identity, not the naive one. This applies to any
target where you fetch ortholog sequences from UniProt for field 2.

### 2. Indication-context-dominated PubMed searches — pivot to indication-specific queries

For targets whose name is dominated by a *different therapeutic context*
than the one being profiled, the initial `"<target> antibody[tiab]"`
query returns mostly irrelevant papers from the dominant context.

Ephrin-B2 is a transmembrane ligand involved in neuroscience (axon
guidance, synaptic plasticity, CNS injury), but it is ALSO the cell-entry
receptor for henipaviruses (Nipah/Hendra). The initial PubMed searches
for "ephrin-B2 antibody[tiab]" and "EFNB2 antibody[tiab]" returned 55
and 8 papers respectively — but the top results were dominated by
henipavirus virology (viral G-protein antibodies, neutralization
assays, vaccine candidates), not neuroscience therapeutic antibody work.

**Fix — indication-specific query terms.** After the initial generic
queries return context-dominated results, pivot to queries that combine
the target name with indication-specific biology terms:

- `"ephrin-B2 spinal cord"[tiab]` → 32 results, all CNS injury
- `"ephrin-B2 axon guidance"[tiab]` → 42 results, all developmental neuroscience
- `"ephrin-B2 neurodegeneration"[tiab]` → 6 results, highly relevant
- `"ephrin-B2 synaptic plasticity"[tiab]` → 21 results, all synaptic biology

These indication-specific queries surfaced the landmark neuroscience
papers (ALS, anti-NMDAR encephalitis, spinal cord injury, neuropathic
pain, stroke) that the generic "antibody" queries completely missed.

**Generalizable rule:** When the target name is shared with a dominant
non-target context (viral receptor, oncology antigen, developmental
marker), run indication-specific PubMed queries combining the target
name with disease/biology terms from the profiling context. Do not rely
on `"<target> antibody[tiab]"` alone. This is distinct from the
"topic-divided search" pattern (CD44 — multiple roles of the SAME
target) — here the issue is that an unrelated field dominates the
search results, drowning out the indication of interest.

### 3. Bidirectional-signaling target — agonism vs antagonism by disease context

Ephrin-B2 is a transmembrane ligand with bidirectional signaling
(forward into Eph-receptor-expressing cells, reverse into
ephrin-B2-expressing cells). The therapeutic direction REVERSES
depending on disease:

- **Blockade** (siRNA/shRNA knockdown, conditional KO, receptor-body
  decoys) is therapeutic in ALS (astrocyte ephrin-B2 is pathogenic),
  spinal cord injury (glial scar), and neuropathic pain (nociceptor
  ephrin-B2 drives central sensitization).
- **Activation/agonism** (clustered ephrin-B2-Fc, recombinant ephrin-B2)
  is therapeutic in anti-NMDAR encephalitis (stabilizes EphB2-NMDAR
  interaction disrupted by patient antibodies) and ischemic stroke
  (promotes angiogenesis and reduces secondary neurodegeneration).

This extends the dual-directional targeting pattern (FasL, IL-15,
TrkB, BDKRB2) to a transmembrane ligand. For field 11, the key
differentiation insight is that no therapeutic antibody has been
engineered for EITHER direction despite strong preclinical mechanism
— the agonist antibody for encephalitis/stroke recovery is the
highest-priority unexplored space. For field 6, the critical failure
mode is mismatching direction to disease: a blocking antibody would
be harmful in encephalitis/stroke; an agonist would be harmful in
ALS/pain.

### 4. UniProt mutagenesis data as epitope leads

The UniProt `.txt` flat-text format includes `FT   MUTAGEN` entries
that identify functionally critical residues — high-value starting
points for epitope design in field 5. For EFNB2, the entry
`MUTAGEN 121..122 /note="LW->YM: Complete loss of Nipah protein G binding"`
identified the LW motif as a functionally critical surface whose
mutation abolishes viral/receptor binding. This region is a candidate
functional epitope for an antibody that could block ephrin-B2's
pathogenic interactions while potentially sparing physiological
EphB2-stabilizing interactions.

**Generalizable rule:** When parsing UniProt `.txt` for field 1/9, also
scan `FT   MUTAGEN` entries for residues whose mutation abolishes a
relevant interaction (receptor binding, viral entry, ligand binding).
These are natural epitope leads for field 5 — an antibody targeting a
known functional "hot spot" is more likely to be functionally
neutralizing than one targeting an arbitrary surface.
