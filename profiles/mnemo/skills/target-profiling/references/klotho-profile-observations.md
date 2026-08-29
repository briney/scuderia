# Klotho (KL) profile observations — 2026-08-17

Fifty-third level-2 profile (preclinical tier, cardiovascular — cardiac
aging/HFpEF/CKD-CVD/vascular calcification). Klotho (α-Klotho, KL,
UniProt Q9UEF7) is a type I transmembrane anti-aging protein that exists
in two functional forms: (a) membrane-bound Klotho, the obligate FGF23
co-receptor (phosphate/vitamin D homeostasis), and (b) soluble Klotho
(sKlotho, shed ectodomain), a pleiotropic endocrine factor with
FGF23-independent cardioprotective effects (SIRT1, anti-TGF-β, anti-Wnt,
anti-NF-κB, eNOS). Built via delegated subagent using the lightweight
retrieval pipeline (direct PubMed E-utilities via urllib, no paper-ingest
scripts). 15+ PubMed queries across antibody, cardiovascular, FGF23,
aging, soluble Klotho, β-Klotho, structure, and clinical-trial terms.
55 unique abstracts fetched. Abstract-only ingestion. ~42.5K chars,
55 unique PMIDs cited.

Key new patterns:

## 1. Dual-form target — membrane co-receptor + soluble pleiotropic factor — antibody must mimic soluble form without blocking membrane form

Klotho is the first profiled target with two distinct functional forms
where the antibody must replicate the *soluble* form's beneficial effects
without disrupting the *membrane* form's co-receptor function. Membrane
Klotho is the FGF23 co-receptor (disrupting it → hyperphosphatemia,
vascular calcification, the kl/kl aging phenotype). Soluble Klotho is the
cardioprotective factor (supplementation → reduced fibrosis, improved
diastolic function, anti-senescence). A blocking/neutralizing antibody
would be harmful; an agonist antibody must replicate soluble-Klotho
signaling without over-activating or blocking the FGF23 co-receptor axis.
For field 6, the wrong modality (blocking vs agonist) is the central
failure mode. For field 11, the antibody must be agonist/function-
mimicking, not antagonistic. Generalizes to any target with a
membrane-bound co-receptor form and a shed soluble form with independent
signaling (ACE2 has a similar dual-form structure but the antibody
challenge there was viral-entry vs enzymatic, not co-receptor vs
pleiotropic).

## 2. Cross-target family antibody precedent — closest antibody is against a homologous family member

No therapeutic anti-α-Klotho antibody exists (zero disclosed — true blue
ocean). The closest antibody precedent is an **agonistic anti-β-Klotho
antibody** (PMID 30068552, Genentech) that mimics FGF21 metabolic
functions, plus an FGFR1c/β-Klotho-activating antibody (PMID 28988823).
β-Klotho is a separate gene product (KLB, ~41% identity to α-Klotho)
serving as co-receptor for FGF19/FGF21. The β-Klotho agonistic antibody
demonstrates that a Klotho-family agonist antibody is *feasible* — it
activates the FGFR1c/β-Klotho complex to mimic FGF21. For field 4,
when zero antibodies exist against the target itself, search for
antibodies against homologous family members and cite them as the
closest mechanistic precedent. For field 11, the cross-target family
precedent de-risks the antibody format (agonistic Klotho-family antibody
is feasible) while leaving the target-specific mechanism (α-Klotho
cardioprotective signaling) unvalidated. Generalizes to any target
family where one member has antibody data and another does not
(α-Klotho/β-Klotho, TrkA/TrkB/TrkC, IL-4Rα/IL-13Rα1, etc.).

## 3. Target not expressed in the disease-relevant tissue — constrains antibody mechanism

Membrane-bound Klotho is NOT expressed endogenously in healthy or
uraemic human vascular tissue (arteries/veins) (PMID 26116633). The
cardiovascular protective effects are mediated entirely by soluble
Klotho from the kidney acting on the heart/vasculature in an
endocrine/paracrine manner. This constrains the antibody mechanism: an
antibody targeting membrane Klotho on vascular cells would have no
local target. The antibody must either (a) be an agonist that mimics
circulating soluble Klotho (requires a defined receptor, currently
unknown), or (b) target membrane Klotho on kidney/brain to promote
shedding/release of endogenous soluble Klotho. For field 1, when the
target is not expressed in the disease-relevant tissue, explicitly state
this and its implication for the antibody mechanism. For field 11, the
mechanism is constrained to soluble-Klotho mimetic or shedding-enhancer,
not local membrane-targeting. Generalizes to any endocrine/paracrine
target whose disease-relevant effects are mediated by a shed/soluble
form acting at a distance from the expressing tissue.

## 4. FGF23 axis as a dosing ceiling — pathway constraint creates a narrow therapeutic index

Activating the FGF23–Klotho co-receptor axis too strongly causes
hypophosphatemia, vitamin D deficiency, and metabolic bone disease
(FGF23-excess phenotype). This creates a dosing ceiling: the antibody
must replicate soluble-Klotho (FGF23-independent) cardioprotective
effects without over-activating the FGF23 co-receptor axis. This is a
variation of the U-shaped dose-response pattern (IGF-1, PMID
18793116) but specifically a *pathway-ceiling* constraint — the
beneficial pathway (soluble Klotho) shares a protein with the
constrained pathway (FGF23 co-receptor), so the antibody's epitope
determines which pathway is engaged. For field 8, the therapeutic index
is narrow and determined by epitope selectivity, not just dose. For
field 11, epitope differentiation (engaging soluble-Klotho pathways
without FGF23 co-receptor activation) is the primary differentiation
strategy. Generalizes to any target where a single protein drives both
a desired therapeutic pathway and a constrained homeostatic pathway
(ACE2: viral entry vs RAAS; Klotho: cardioprotection vs phosphate).

## 5. PubMed search strategy: broad mechanism/disease queries outperform narrow "antibody" queries for zero-antibody targets

For a target with zero disclosed therapeutic antibodies, narrow
`"Klotho antibody"[tiab]` queries returned only 6 results (mostly
research/imaging antibodies and one β-Klotho paper). The highest-yield
queries combined the target name with disease/mechanism terms:
`Klotho[tiab] AND cardiovascular[tiab]` (10 results), `Klotho[tiab] AND
FGF23[tiab]` (10), `Klotho[tiab] AND (antibody[tiab] OR
therapeutic[tiab])` (10), `beta-Klotho[tiab] AND antibody[tiab]` (9).
The β-Klotho antibody query was essential for finding the cross-target
family precedent (PMID 30068552). For targets with no antibody pipeline,
search broadly across mechanism, disease, and homologous family
members — the antibody evidence is in the biology/disease literature,
not in an "antibody" keyword search. Generalizes to all blue ocean
targets where the antibody evidence is indirect (biology validation +
family precedent, not direct antibody papers).

## 6. Klotho-derived peptides confirm tractability but are PK-limited — antibody half-life is the differentiation

Klotho-derived peptides (KP6 targeting Wnt/β-catenin, PMID 35644285; a
TGF-β-targeting peptide, PMID 35064106) confirm that Klotho's
cardioprotective signaling can be replicated by a biologic smaller than
the full protein. However, peptides have short half-lives and poor
biodistribution. An antibody (2-3 week half-life via FcRn) offers a
fundamental PK advantage over both recombinant soluble Klotho protein
(short plasma half-life) and peptides. For field 10, list the peptide
approaches as competitive landscape (they validate the biology) and
identify the PK gap the antibody fills. For field 11, the half-life
advantage is a concrete format differentiation. Generalizes to any
target where protein/peptide supplementation is proven preclinically but
PK-limited — the antibody is the long-acting alternative.

(Klotho/KL profile, ~42.5K chars, 55 papers (abstract-only), 55 unique
PMIDs cited, working-docs/hitlist-profiles/klotho.md.)
