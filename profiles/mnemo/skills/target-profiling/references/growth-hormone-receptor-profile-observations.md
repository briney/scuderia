# Growth Hormone Receptor (GHR) profile observations (2026-08-16)

Thirty-third level-2 profile (approved tier, cardiovascular/metabolic —
endocrine/acromegaly). GHR is the **first target where the approved biologic
is a PEGylated protein antagonist, not a conventional antibody** —
pegvisomant (Somavert) is a modified GH molecule (G120R substitution) that
blocks receptor dimerization, PEGylated for half-life extension. This is
also the **first cytokine receptor target profiled** (class I cytokine
receptor family) and the **first target where the approved drug is a
modified version of the natural ligand** (hormone variant turned antagonist).
5 key papers ingested: 1/5 PMC XML OA (Frontiers in Endocrinology —
Dehkhoda 2018, PMID 29487568, 59K chars full text), 4/5 abstract-only
(Endocrine Reviews, Elsevier Growth Horm & IGF Res ×2, Nature Reviews
Dis Primers — all subscription, jina/Wayback blocked). 20% full-text
retrieval rate. ~40K chars (profile), 5 unique PMIDs cited. 16 authors.

## 1. Non-antibody biologic as the approved drug — PEGylated protein antagonist

Pegvisomant is the only approved GHR-targeting drug. It is NOT an antibody,
Fc-fusion, or nanobody — it is a recombinant human GH molecule with specific
amino acid substitutions (key: G120R at binding site 2) that convert it from
agonist to antagonist, plus PEGylation for half-life extension. This creates
a distinct competitive landscape pattern:

- **Field 4 (antibody landscape)** must accommodate a non-immunoglobulin
  biologic. The format column should describe the molecule accurately
  ("PEGylated recombinant protein antagonist — modified GH with G120R
  substitution") rather than forcing it into antibody categories (naked IgG,
  Fab, ADC, bispecific, Fc-fusion, nanobody). Add a note: "Not a conventional
  antibody — PEGylated protein antagonist functioning as a receptor-targeting
  biologic."

- **Field 6 (success factors)** — the key success factor is **rational
  structure-based design**: the crystal structure of GH-GHR complex revealed
  the two-site binding mechanism (site 1 high affinity, site 2 lower
  affinity), enabling design of a site 2 mutant that blocks dimerization while
  maintaining site 1 binding. This is a model for structure-based biologic
  design when the natural ligand's binding mechanism is understood at atomic
  resolution. The second success factor is **PEGylation for half-life
  extension** — native GH has a ~20-30 min half-life; PEGylation enabled
  daily (eventually weekly) SC dosing.

- **Field 11 (differentiation opportunities)** — the primary format
  differentiation is a **conventional anti-GHR antibody** (which does not
  exist). An antibody would offer: (1) longer half-life via FcRn recycling
  vs PEGylation; (2) potential for monthly/quarterly dosing; (3) different
  immunogenicity profile; (4) established antibody manufacturing. The key
  risk is **agonist activity** (see below).

This pattern generalizes to any target where the approved biologic is a
modified ligand rather than an antibody (e.g., etanercept is a TNFR-Fc
fusion, not an anti-TNF antibody; anakinra is a recombinant IL-1 receptor
antagonist, not an anti-IL-1 antibody). For such targets, the antibody
competitive space is completely open — the approved drug validates the
target but leaves the antibody modality unexplored.

## 2. Preformed dimer + conformational activation = agonist risk for antibody approaches

GHR exists as a **preformed homodimer** on the cell surface (dimers form in
the ER). Activation does NOT involve de novo dimerization — it involves a
conformational change within the preformed dimer: GH binding causes the
transmembrane domains to transition from parallel to a left-handed crossover
orientation, separating the lower transmembrane helices and the ICDs, which
dissociates JAK2 trans-inhibition and enables kinase activation.

This creates a **critical pitfall for anti-GHR antibody design**: bivalent
antibodies (IgG) can cross-link GHR dimers, potentially inducing the
conformational change and activating the receptor (agonist activity) rather
than blocking it. Early studies confirmed this risk: bivalent monoclonal
antibodies to the GHR ECD activated a GHR/G-CSFR hybrid receptor, while
monovalent fragments did not. However, of eight agonist antibodies on the
hybrid receptor, only one showed weak agonist activity on full-length GHR —
suggesting that simple dimerization is NOT sufficient for GHR activation,
and the correct conformational change is required. (PMID 29487568.)

For field 6 (failure modes) and field 11 (differentiation), an anti-GHR
antibody must be designed to:
1. Block the conformational change (stabilize the inactive parallel
   transmembrane state) rather than simply bind the ECD
2. Avoid cross-linking two GHR dimers (which could induce activation)
3. Be functionally screened as an antagonist (not just a binder)
4. Consider monovalent formats (Fab, VHH) if bivalent cross-linking is
   shown to activate the receptor

This is distinct from the Treg-depletion agonist risk (CCR8, where ADCC-
deficient formats fail because depletion IS the mechanism) — here, the
agonist risk is from the antibody's bivalency inducing the conformational
change that activates signaling, which is the opposite of the desired
antagonist effect.

This pattern generalizes to any **preformed-dimer cytokine receptor**
where activation requires a conformational change (not de novo
dimerization): the prolactin receptor (PRLR), erythropoietin receptor
(EPOR), thrombopoietin receptor (TPOR) — all class I cytokine receptors
that form preformed dimers. For these targets, antibody design must
account for the conformational activation mechanism, not just ligand
competition.

## 3. GHR-deficient individuals show no cancer deaths — genetic validation for oncology

GHR-deficient individuals (Laron syndrome / primary GH insensitivity) have
severe short stature but show a **lack of deaths from cancer**. This is
strong genetic evidence that GHR signaling promotes cancer development
and that GHR blockade may be protective against cancer. Additionally, an
SNP in GHR (P495T in the ICD) that impairs SOCS2-mediated GHR degradation
extends GHR signaling and correlates with increased lung cancer risk.
(PMID 29487568.)

For field 3 (disease evidence), this provides a **human genetics
validation pathway** for a target whose approved indication (acromegaly)
is different from the emerging indication (cancer). The genetic evidence
(GHR-deficient = no cancer) is stronger than epidemiological evidence
alone (acromegaly patients have increased cancer risk) because it
isolates GHR as the causal variable. For field 11 (differentiation
opportunities), cancer is an unexplored indication for GHR-targeting
biologics — pegvisomant is approved only for acromegaly, but the genetic
data suggest GHR blockade could have anti-cancer activity.

This pattern generalizes to any target where **loss-of-function humans**
are protected from a disease different from the approved indication:
the LOF phenotype reveals the target's role in the protected-against
disease, providing genetic validation for a new indication. Always
check whether LOF individuals show altered disease incidence for
indications beyond the approved one.

## 4. Full-text retrieval rate: 20% — subscription endocrine journal mix

Only 1/5 papers (20%) had accessible full text — the Frontiers in
Endocrinology OA paper (PMID 29487568, PMC5816795, 59K chars via PMC
XML). The other 4 were:
- Endocrine Reviews (Oxford Academic) — jina returned CAPTCHA/bot
  verification page, Wayback unavailable
- Growth Hormone & IGF Research (Elsevier) × 2 — DOI redirect 404,
  ScienceDirect CAPTCHA via jina
- Nature Reviews Disease Primers — jina retrieved 131K chars but it
  was entirely the reference list (177 references), not the article body

This confirms the documented pattern: subscription endocrine/metabolic
journals (Endocrine Reviews, Elsevier GH&IGF Res, Nature Reviews) are
consistently paywalled with no PMC copy. The one OA paper (Frontiers)
provided 59K chars of full text — more than sufficient for grounding
fields 2, 3, and 6 at the level-2 rigor standard. The abstracts of the
paywalled papers (Endocrine Reviews and Nature Reviews Dis Primers
abstracts are particularly rich — 1,000-2,500 chars) compensated
adequately for the missing full text.

Notable: the Nature Reviews Dis Primers jina retrieval returned 131K
chars that appeared to be the reference list only (no body text). This
is a new jina failure mode — jina successfully bypassed the paywall for
the references section but not the article body, producing a large
character count that initially appeared to be full text. Always verify
jina output by checking for article body markers (abstract text,
section headers, discussion) before classifying as "publisher-jina"
full text.

## 5. PubMed search strategy for endocrine/metabolic targets

Four search queries were used:
1. `growth hormone receptor AND pegvisomant AND review` — 15 results
2. `GHR AND antibody AND acromegaly AND review` — 1 result (very narrow)
3. `growth hormone receptor antagonist AND acromegaly` — 15 results
4. `growth hormone receptor AND JAK2 AND STAT5 AND review` — 15 results

The combined 41 unique PMIDs were batched through esummary (20 at a
time, 4s sleep between batches) to select 5 landmark papers covering:
(a) pegvisomant discovery/development (Kopchick 2002, Endocr Rev),
(b) GHR receptor biology (Waters 2016, GH&IGF Res),
(c) acromegaly disease review (Colao 2019, Nat Rev Dis Primers),
(d) pegvisomant clinical concept (Parkinson 2000, GH&IGF Res),
(e) GHR mechanism/signaling (Dehkhoda 2018, Front Endocrinol — the
only OA paper).

The second query (`GHR AND antibody AND acromegaly AND review`)
returned only 1 result, confirming that for this target, "antibody" is
not the right search term — the approved drug is a protein antagonist,
not an antibody. For targets where the approved biologic is not a
conventional antibody, search queries should include "antagonist" and
"PEGylated" alongside "antibody" to capture the full landscape. The
broader query 3 (`growth hormone receptor antagonist AND acromegaly`)
was more productive (15 results) because it captures the actual drug
modality.

(GHR profile, ~40K chars, 5 papers, 16 authors, 5 unique PMIDs cited,
working-docs/hitlist-profiles/growth-hormone-receptor.md.)
