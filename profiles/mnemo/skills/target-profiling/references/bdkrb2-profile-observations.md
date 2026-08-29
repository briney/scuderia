# BDKRB2 (Bradykinin B2 Receptor) Profile Observations

**Session:** 2026-08-17
**Target:** Bradykinin B2 receptor (BDKRB2), UniProt P30411
**Tier:** preclinical (neuroscience)
**Profile:** `working-docs/hitlist-profiles/bradykinin-b2.md` (~37K chars, 61 PMID citations)
**Papers:** 19 reviewed (2 full-text via PMC OA XML, 17 abstract-level)

## Key new techniques

### UniProt REST API for target identity and structural data

The UniProt REST API (`rest.uniprot.org/uniprotkb/<accession>.txt`) is a
fast, reliable source for filling **field 1 (target identity)** and **field 9
(structural information)** without literature retrieval. The plain-text
format (not JSON) is easy to parse with Python regex.

Fetch:
```
curl -sL 'https://rest.uniprot.org/uniprotkb/P30411.txt' -o /tmp/target_uniprot.txt
```

Extract (all present in the flat text format):
- **Protein name, gene symbol, synonyms** — `DE` / `GN` lines
- **Molecular weight** — `SQ   SEQUENCE   391 AA;  44461 MW;` line
- **Protein family** — `CC   -!- SIMILARITY:` lines
- **Subcellular location** — `CC   -!- SUBCELLULAR LOCATION:` lines
- **Tissue specificity** — `CC   -!- TISSUE SPECIFICITY:` lines
- **Function** — `CC   -!- FUNCTION:` lines (with PMID citations)
- **Topology domains** — `TOPO_DOM` entries (extracellular/cytoplasmic
  residue ranges)
- **Transmembrane helices** — `TRANSMEM` entries (numbered, with residue
  ranges)
- **Glycosylation** — `CARBOHYD` entries (N-linked sites)
- **Lipid modifications** — `LIPID` entries (S-palmitoylation, etc.)
- **Phosphorylation sites** — `MOD_RES` entries (with kinases)
- **Disulfide bonds** — `DISULFID` entries
- **Alternative splicing** — `ALTERNATIVE PRODUCTS:` section
- **PDB cross-references** — `DR   PDB;` lines (PDB ID, method, resolution,
  residue range)
- **Variants/polymorphisms** — `VARIANT` entries
- **Keywords** — `KW` line (glycoprotein, phosphoprotein, etc.)

This is particularly valuable for GPCR targets where the 7-TM topology,
extracellular loop boundaries, and PTM sites are needed for field 1 and
field 9 but are tedious to extract from papers.

### PDB REST API for structural data

The RCSB PDB REST API provides structure metadata including the associated
publication PMID — critical for finding the paper that describes a structure.

Fetch:
```
curl -sL 'https://data.rcsb.org/rest/v1/core/entry/<PDB_ID>' -o /tmp/pdb.json
```

Extract:
- **Title** — `struct.title`
- **Method** — `exptl[0].method` (X-RAY, ELECTRON MICROSCOPY, etc.)
- **Resolution** — `rcsb_entry_info.resolution_combined`
- **Associated PMID** — `rcsb_primary_citation.pdbx_database_id_pub_med`
  (may be absent — search PubMed by title to find the PMID)

For BDKRB2, the UniProt entry listed PDB 7F2O; the PDB API revealed it is a
cryo-EM structure (2.90 Å) of B2R bound to bradykinin and Gq protein. The
PMID was not in the PDB citation, but a PubMed title search
(`"Molecular basis for kinin selectivity and activation of the human
bradykinin receptors"`) found PMID 34518695 (Yin et al, Nat Struct Mol Biol
2021).

**Workflow:** UniProt `DR   PDB;` → PDB REST API → PubMed title search →
abstract retrieval. This 3-step chain reliably finds structure papers
that PubMed keyword searches may miss.

## Profile-specific observations

### GPCR with approved peptide antagonist, zero antibodies

B2R is a class A GPCR with an approved peptide antagonist (icatibant for
HAE) but **zero therapeutic antibodies** in development. PubMed searches
for `"bradykinin B2 antibody"[tiab]` and `"BDKRB2 antibody"[tiab]` both
returned 0 results — confirming the antibody space is completely
unexplored. The only antibody study (PMID 21756898) used an artificial
myc-tag epitope for receptor trafficking research, not a therapeutic
antibody.

This extends the C5aR1 GPCR pattern: the approved drug (peptide or small
molecule) clinically validates the target, but the antibody competitive
landscape is completely open. The distinction from C5aR1: icatibant is a
peptide (not a small molecule like avacopan), and B2R also has an agonist
approach (labradimil for BBB disruption) — a dual-modality axis (antagonist
for HAE, agonist for drug delivery) that C5aR1 does not have.

For field 10, explicitly state "No anti-B2R antibodies in clinical
development or approved." For field 11, the differentiation framing is
"why would an antibody be better than the peptide" — answer: longer
half-life (icatibant t1/2 ~1-2h), sustained receptor blockade, potential
for prophylactic/chronic use.

### PubMed search strategy for GPCR targets with no antibody pipeline

Productive search queries (yielding landmark papers):
- `"bradykinin B2 receptor antagonist"[tiab]` — 447 results
- `"bradykinin B2 receptor"[tiab] AND (antibody OR monoclonal)[tiab]` — 55
- `icatibant[tiab]` — 774
- `"bradykinin B2 receptor"[tiab] AND "blood-brain barrier"[tiab]` — 15
- `"bradykinin B2 receptor"[tiab] AND (brain OR neuroinflammation OR
  astrocyte OR microglia)[tiab]` — 0 (too specific)
- `bradykinin receptor GPCR structure signaling` — 12

Zero-result searches:
- `"bradykinin B2 antibody"[tiab]` — 0
- `"BDKRB2 antibody"[tiab]` — 0

**Lesson:** For GPCR targets where the therapeutic landscape is
peptide/small-molecule dominated, search by the drug name (icatibant),
by receptor function (antagonist, agonist), and by disease (HAE, BBB,
stroke) — not by "antibody." This parallels the Nav1.9 observation about
searching by function rather than "antibody" for ion channels.

### B2R agonism vs antagonism — dual-direction modulation

B2R is unique among profiled GPCRs in having BOTH an approved antagonist
(icatibant, for HAE) AND a clinical-stage agonist (labradimil, for BBB
disruption in glioma). This dual-direction modulation creates a
complex competitive landscape:
- An anti-B2R antibody (antagonist) competes with icatibant (differentiation:
  longer half-life, prophylactic use)
- An anti-B2R antibody (agonist) would compete with labradimil for BBB
  disruption (but agonist antibodies against GPCRs are technically
  challenging and carry constitutive activation risks)

For field 11, this means the differentiation case must specify which
direction (antagonist or agonist) the antibody takes, and address the
specific competitor in that modality.

### Neuroscience-specific: BBB disruption as both opportunity and risk

B2R modulates BBB permeability — agonism opens the BBB (drug delivery
opportunity), antagonism protects the BBB (stroke/TBI therapy). For
neuroscience target profiling, this dual role means:
- **Field 3 (disease evidence):** B2R appears in both stroke/TBI (antagonist
  approach) and glioma drug delivery (agonist approach) — list both
- **Field 8 (safety):** A B2R antibody's effect on BBB integrity is a
  safety concern regardless of direction — an antagonist antibody could
  protect the BBB but might also impair normal BBB function; an agonist
  antibody could cause uncontrolled BBB disruption
- **Field 11:** A BBB-shuttle bispecific (anti-B2R + anti-TfR) could enable
  CNS penetration — a format differentiation unique to neuroscience targets

### "Bradykinin storm" — disease evidence from a structure paper

The cryo-EM structure paper (PMID 34518695, Yin et al 2021) introduced the
"bradykinin storm" concept (hyperactivation of bradykinin receptors
associated with pulmonary edema in COVID-19). This is a disease evidence
entry that came from a structural paper, not a clinical paper — confirming
the existing observation that structural papers are high-value for
profiling. For field 3, include mechanistic disease hypotheses from
structure papers even when clinical evidence is preliminary.
