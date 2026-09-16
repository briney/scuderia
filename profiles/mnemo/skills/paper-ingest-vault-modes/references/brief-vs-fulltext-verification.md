# Brief-vs-fulltext verification — case studies

Companion to the paper-ingest Phase 5 rule "Verify the task brief against
the full text before writing Findings." Case files of briefs whose
framing diverged from the paper's actual text, the check that caught each,
and how each was recorded. The pattern: **identifiers can all be right
while the brief's *narrative* is still wrong** — the identity gate
(Phase 1) never sees it; only full-text grep does.

## Case 1 — Thai 2023 (Cell Rep, PMID 38007690, PMC10720262; ingested 2026-09-04)

Example: a paper-ingest brief targeting `<satellite-vault>`.
Brief asked for: "VH3-33 germline gene usage determinants, structural
basis of cross-reactivity and potency across junctional and epsilon
epitope mAbs, CDR features, the public clonotype concept for CSP
antibodies", venue "Molecular Cell".

Three independent divergences, each caught by a different check:

1. **Venue wrong** ("Molecular Cell" → actually Cell Reports).
   Check: compare brief venue against PubMed `<Journal/Title>` during
   the Phase 1 gate. Identifiers all matched, so this was NOT a
   wrong-paper signal — PubMed authoritative for `venue:`, correction
   logged. Fix is now in the Phase 1 gate table ("Wrong venue in the
   task").

2. **Brief terminology absent from the paper.** Full-text search
   (`grep -ci`) returned **zero hits** for "epsilon", "public",
   "clonotype". The paper's actual framing: cross-reactivity across
   junctional (NPDP/KQPA), minor (NVDP), and major (NANP) repeat
   motifs, plus convergent antibody features across clonally distinct
   lineages. Follow-up established that "epsilon epitope" is not a PfCSP
   concept at all in the literature (EPMC full-text search: "epsilon
   epitope" hits are adenovirus hexon papers; "epsilon" AND
   "circumsporozoite" hits are unrelated fields). The dive's own
   working doc had inherited the bad term
   ("VH3-33 public germline for junctional/epsilon epitope mAbs (Thai
   2023)").

   Handling: distill the paper's real claims; flag the discrepancy
   prominently in Limitations with the zero-hit evidence; do NOT
   silently overwrite the brief's framing or write it into Findings as
   the paper's claim; name the correction the parent should make to the
   working doc.

3. **Phantom citation in a sibling vault page.** The vault's
   kisalu-2018 page cited "Plymler et al. 2023 (PMC10720262)" as a
   secondary source for CIS43's germline genes — but PMC10720262 is the
   Thai 2023 paper being ingested, and PubMed has no author named
   Plymler at all (`esearch Plymler[Author]` → count 0; EPMC → 0 hits).
   Some prior ingest mis-attributed a citation to a nonexistent paper
   while holding the right PMCID.

   Handling: record the phantom in the new page's Ingest log as an
   `entity-resolution`/`citation-fixer` flag naming both pages and the
   correct attribution, so the parent can repair the sibling. General
   rule: when a task names sibling vault pages as context, grep them
   for THIS paper's identifiers — mismatches are cheap to find and
   otherwise persist silently.

## Case 2 — terminology-provenance check (general recipe)

When a brief uses a term the paper doesn't contain, before calling it
wrong, establish whether the term is:

1. **Real in the field** — EPMC full-text search
   (`"exact phrase" AND <domain keyword>`). If the phrase exists in
   sibling papers, the brief is probably conflating two papers in the
   dive; name the likely true source paper.
2. **Real but renamed** — the paper may use different vocabulary for
   the same concept (e.g. brief "public clonotype" vs paper "convergent
   features across clonally distinct lineages"). Distill the concept
   under the paper's own name; note the synonym in the Ingest log.
3. **Not real anywhere in the domain** — treat as a bad seed term,
   flag for the parent's working-doc correction.

Cost is three curl calls; the alternative is a distillation that
attributes to a paper claims it never made.

## Cell Press / PMC XML extraction quirks (same ingest)

When distilling from PMC JATS XML for Cell Press papers:

- **Figure legends are inline with body paragraphs**, not in a
  `<fig>`-caption block the plain-section walker reaches — they appear
  as text runs like `Figure 1High-affinity cross-reactive...` directly
  after the paragraph they illustrate. Pattern to recover them:
  `re.finditer(r'Figure\s(\d)(?=[A-Z])', text)` — the digit followed
  immediately by a capital letter (no space) distinguishes a legend
  start from an in-text citation (`Figure 1A`). Legends can also be
  **truncated mid-sentence** at the end of a long paragraph block;
  re-wrap paragraphs (e.g. `textwrap.wrap(..., width=110)`) before
  grepping for the tail.
- **PDB IDs in the STAR★Methods key-resources table run together with
  the next sentence** — `PDB: 8F9ECrystal structure of...`. The naive
  `PDB: ([0-9A-Z]+)` swallows the following capital letters. Extract
  with a fixed-length pattern: `PDB:\s*([0-9][A-Za-z0-9]{3})` (PDB IDs
  are exactly 4 chars, first a digit).
- Deposited surnames can carry typos shared by PubMed AND the publisher
  XML ("de Bruijni") — see the SKILL.md pitfall.
