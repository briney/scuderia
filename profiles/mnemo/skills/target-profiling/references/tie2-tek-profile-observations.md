# Tie2/TEK Profile Observations (2026-08-17)

Tie2 (TEK, gene TEK, UniProt Q02763) is a receptor tyrosine kinase expressed
predominantly on vascular endothelial cells — the central regulator of
vascular quiescence in the angiopoietin/Tie signaling axis. Ophthalmology
target, preclinical tier (per hit list). Built via delegated subagent using
the lightweight retrieval pipeline (direct PubMed E-utilities + urllib, no
paper-ingest scripts). 5 PubMed queries (antibody + ophthalmology + DR/AMD),
31 unique PMIDs identified, 7 landmark abstracts fetched. Abstract-only
ingestion (no full-text retrieval). One paper already in the brain
(PMID 38847896, faricimab review, full-text) was leveraged for rich Ang/Tie2
biology and clinical trial data. ~32K chars, 7 unique PMIDs cited.

Output: `working-docs/hitlist-profiles/tie2-tek.md`

## Key new patterns

### (1) Indirect vs direct Tie2 modulation — the "approved drug that doesn't bind the target" pattern

Faricimab (Vabysm, Roche/Genentech) is **FDA-approved** for nAMD and DME and
is universally described as a "Tie2 pathway" therapy. But faricimab does NOT
bind or activate Tie2 directly — it is a bispecific antibody that neutralizes
**Ang-2** (the Tie2 antagonist ligand) and **VEGF-A**. Tie2 activation is
indirect: by removing Ang-2, endogenous Ang-1 can activate Tie2 unopposed.
Similarly, AKB-9778 (VE-PTP inhibitor) activates Tie2 by inhibiting the
phosphatase that dephosphorylates it, not by binding Tie2. Nesvacumab
(anti-Ang-2, discontinued Phase 2) also works indirectly.

This means the "Tie2 antibody landscape" (field 4) is dominated by
**indirect modulators** — antibodies against the ligand (Ang-2) or the
phosphatase (VE-PTP), not the receptor itself. The only direct anti-Tie2
antibody is a preclinical agonist (PMID 36828931, academic). For field 4,
when the target is a receptor with a validated pathway but the approved/
clinical antibodies target upstream regulators (ligands, phosphatases),
**separate "direct receptor antibodies" from "indirect pathway modulators"**
explicitly. The competitive gap (field 10) is the direct approach: no
direct Tie2 agonist antibody is in clinical development despite a validated
pathway and an approved indirect drug. This generalizes to any receptor
target where the approved drug targets the ligand (e.g., anti-VEGF for
VEGFR, anti-Ang-2 for Tie2) — the receptor itself is open territory for
direct antibody approaches.

### (2) Agonist antibody for vascular stabilization — the "therapeutic direction is activation, not blockade" pattern in ophthalmology

Tie2 is the first profiled ophthalmology target where the therapeutic
direction is **receptor agonism (activation)** for vascular stabilization —
the opposite of the standard anti-angiogenic blockade paradigm (anti-VEGF).
In DR/DME/AMD, hypoxia drives Ang-2 upregulation and VE-PTP activation,
which **inactivate** Tie2, destabilizing retinal vessels. The therapeutic
goal is to **reactivate** Tie2, restoring vascular quiescence. This is the
ophthalmology analog of the ANP/GC-A pattern (cardiovascular: agonism for
vasodilation) and the CFI pattern (complement: augmentation of a regulator).

For field 2, document "effect of blockade" AND "effect of activation" as
therapeutically **opposite** — blockade destabilizes vessels (detrimental
in ophthalmology, potentially useful in oncology); activation stabilizes
vessels (therapeutic in ophthalmology). For field 11, the therapeutic
direction (agonism) must be stated explicitly, and a neutralizing antibody
flagged as a known risk, not a strategy. Generalizes to any vascular
stability receptor where the disease is driven by receptor inactivation:
Tie2, potentially VEGFR2 (vessel normalization), EphB4, and integrin
receptors on endothelial cells.

### (3) Ligand-independent agonistic antibody with cross-pathway mechanism

The agonistic anti-Tie2 antibody (PMID 36828931) is notable for two reasons:
(a) it activates Tie2 **without requiring Ang-1** — bypassing the problem of
Ang-2 competition and hypoxia-driven VE-PTP upregulation that limits
ligand-dependent strategies; (b) it triggers a **novel cross-pathway
mechanism**: Tie2 activation induces VE-PTP-mediated VEGFR2
dephosphorylation, meaning the agonist achieves anti-VEGF-like benefit
through an entirely different mechanism. This is the first profiled target
where a receptor agonist antibody has a cross-pathway inhibitory effect on a
parallel RTK.

For field 6 (failure/success modes), when a direct receptor agonist has a
cross-pathway mechanism, note it — this may explain efficacy in patients
resistant to conventional pathway blockade. For field 11, a bispecific
that directly activates Tie2 (agonistic Fab) while neutralizing VEGF-A
(antagonistic Fab) would combine the additive mechanisms proven in the
AKB-9778 + ranibizumab trial (PMID 27236272) into a single molecule. The
cross-pathway mechanism (Tie2 activation → VEGFR2 dephosphorylation) suggests
a direct Tie2 agonist may have intrinsic anti-VEGF activity, reducing the
need for a separate anti-VEGF arm.

### (4) Human genetic validation from candidate-gene SNP association — sex-specific effects

TIE2 SNPs (rs625767, rs652010, rs669441) are associated with DR
susceptibility in a Chinese cohort (n=285 DR, 433 controls), with
**sex-specific effects in females** (rs625767 OR=0.62, P=0.005 in females;
not significant in males; PMID 38750959). This is the first profiled target
with **sex-stratified genetic association** data. For field 3 (disease
evidence), when genetic association studies report sex-specific effects,
record them — they define a precision medicine subpopulation for field 11.
A Tie2 agonist could be positioned for genetically stratified female DR
patients carrying risk alleles, where Tie2 function may be inherently
impaired. For field 11, note whether the genetic evidence supports a
biomarker-defined subset. Generalizes to any target with sex-specific or
population-specific genetic associations.

### (5) PubMed search strategy for receptor targets with approved indirect drugs — search for the drug name, not just the receptor

The highest-yield queries for Tie2 were NOT `"Tie2 antibody"[tiab]` (which
returned 10 results, mostly irrelevant — stem cells, erectile dysfunction,
nucleus pulposus) but the **ophthalmology indication queries**: `"Tie2"[tiab]
AND ("diabetic retinopathy"[tiab] OR "age-related macular degeneration"[tiab])`
(104 results) and `"Tie2"[tiab] AND ("retinopathy"[tiab] OR "AMD"[tiab] OR
"retina"[tiab])` (152 results). The key clinical trial paper (AKB-9778,
PMID 27236272) was found via a separate `"AKB-9778"[tiab]` search, and the
faricimab paper via the already-ingested brain page.

**Rule:** For receptor targets where the approved/clinical drugs target
upstream regulators (ligands, phosphatases), search for: (1) the receptor
name + indication, (2) the drug/antibody code names (AKB-9778, faricimab,
nesvacumab), (3) the ligand name + antibody (Ang-2 antibody), in addition
to the standard `"receptor name antibody"[tiab]` query. The therapeutic
evidence is published under the drug name and the indication, not under
the receptor name + "antibody." This is the receptor analog of the ANP
pattern (search for receptor name, not peptide name).

### (6) Already-ingested brain papers as a first-check before PubMed search

Before running PubMed searches, check whether papers relevant to the
target are already in the brain (`papers/` directory). For Tie2, the
faricimab review (PMID 38847896) was already fully ingested and provided
richer content (full-text: Ang/Tie2 biology, preclinical models, Phase 2/3
trial data, CrossMAb technology, Fc engineering) than any PubMed abstract.
A simple `grep -rl 'Tie2\|TEK\|faricimab\|AKB-9778' papers/` surfaced this
paper immediately. This extends the "cross-reference existing brain pages"
pattern: for any target in a pathway already profiled (Ang-1, VEGF-A/Ang-2),
check for already-ingested papers before searching PubMed — they may provide
full-text content that paywalled PubMed papers cannot.

## Summary stats

- 5 PubMed queries, 31 unique PMIDs
- 7 landmark abstracts fetched (all abstract-only — no full-text retrieval
  attempted; paywalled journals: J Clin Invest, Ophthalmology, Curr Diabetes
  Rep, J Transl Med was OA but not retrieved as full-text)
- 1 already-ingested brain paper leveraged (PMID 38847896, faricimab, full-text)
- 7 unique PMIDs cited in profile
- ~32K chars profile
- PubMed HTTP 429 rate limiting: hit once on query 2, resolved with 15s pause
- Tier confirmed as preclinical (no direct anti-Tie2 antibody in clinical
  development; faricimab is approved but targets Ang-2, not Tie2 directly)
