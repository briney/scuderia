# P2X7 receptor profile observations (2026-08-17)

P2X7 (P2RX7, UniProt Q99572) is the **first ligand-gated ion channel** target
profiled at level 2 (key paper ingestion). Preclinical tier, neuroscience area
with cross-indication relevance in immunology/oncology. 7 landmark papers
ingested (4/7 via PMC XML full text, 1/7 via jina reader on `linkinghub.elsevier.com`
redirect for an Immunity review, 2/7 abstract-only — older Elsevier papers
without PMCID). ~37K chars profile, 7 unique PMIDs cited (132 total citations).
Full-text retrieval rate: 71% (5/7).

## Ion channel target profiling considerations

P2X7 is a trimeric ATP-gated ion channel — structurally and functionally
distinct from GPCRs (7-TM, orthosteric pocket in TM core), soluble cytokines
(neutralization mechanism), and cell-surface receptors with canonical
extracellular ligand-binding domains. Key profiling differences:

- **The functionally critical binding site is at the subunit interface, not
  on a single extracellular domain.** The ATP-binding pocket sits between
  adjacent monomers (dorsal fin of one subunit, head/left flipper of the
  adjacent). Antibodies targeting a single subunit's extracellular domain
  may not block the interface binding site. An antibody that bridges or
  locks the trimer interface (preventing conformational change) could be
  functionally superior to one that merely decorates the extracellular
  domain. In field 5 (epitope landscape), the subunit interface is the
  highest-value epitope target, but it may be partially occluded by the
  adjacent subunit — an accessibility challenge unique to trimeric ion
  channels. (PMID 28723547, PMID 42498814.)

- **Conformational states (channel vs dilated pore) may present different
  epitopes.** P2X7 transitions from closed (apo) → open (ATP-bound, cation
  channel) → dilated pore (permeable to ~900 Da molecules). The L4 mAb
  binds both the canonical P2X7A and the truncated P2X7B isoform, but NOT
  the non-functional conformational variant nfP2X7. In field 5, note which
  conformational states the antibody can bind — an antibody selective for
  the open/dilated state could functionally trap the receptor, while one
  selective for the closed state would be a pure antagonist. (PMID
  42498814.)

- **The long C-terminal tail (239 aa) is intracellular and not antibody-
  accessible, but is functionally critical.** The C-terminal tail is
  required for large pore formation, contains death-domain homology, and
  mediates protein-protein interactions. This is the domain that small
  molecules cannot target but intrabodies or PROTACs could. In field 9
  (structural information), explicitly note which domains are
  extracellular/antibody-accessible vs intracellular. (PMID 28723547.)

## Species-specific mAb enables donor-vs-host dissection

The L4 mAb (clone L4, mouse IgG2b) binds human but NOT mouse P2X7. In a
humanised NSG mouse GVHD model, this species-specificity allowed the first
demonstration that **donor (human) P2X7 directly contributes to GVHD
progression** — a question that non-selective small molecule antagonists
(BBG, AZ10606120) could not resolve because they block both human and mouse
P2X7. AZ10606120 failed to alter GVHD in the same model, possibly due to
insufficient in vivo dosing, while BBG succeeded but may have off-target
effects (pannexin-1 blockade). (PMID 37765233.)

**Generalizable insight:** For targets where both donor and host cells
express the receptor, a species-specific antibody in a humanised mouse
model is the cleanest way to attribute mechanism to donor vs host
contributions. This is a unique advantage of antibody over small molecule
approaches. In field 6 (failure/success modes), note whether the
preclinical model used species-specific or pan-species blockade, and
how this affects interpretation. For field 7 (in vivo models), the
humanised NSG mouse + species-specific mAb is a high-value model for
any target with donor/host ambiguity.

## Dual-mechanism antibody: blockade + CDC

The L4 mAb has two distinct therapeutic mechanisms:
1. **Channel blockade** — blocks ATP-induced Ca2+ flux, pore formation,
   and downstream IL-1β release (IC50 0.21-0.48 µg/mL depending on assay).
2. **Complement-dependent cytotoxicity (CDC)** — depletes P2X7-high-
   expressing cells (monocytes, DCs, iNKT cells, Th17 cells, MDSCs) while
   sparing P2X7-low cells (most T cells, B cells).

The CDC effect is proportional to cell-surface P2X7 density — cells with
the highest P2X7 expression are most sensitive to complement lysis. This
is the first demonstration of CDC by an anti-P2X7 biologic. (PMID
39853757.)

**Generalizable insight:** For surface-expressed ion channels with
heterogeneous expression across cell types, a complement-fixing antibody
(IgG2b, IgG1) can simultaneously block channel function AND selectively
deplete the highest-expressing (most pathogenic) cell populations. This
dual mechanism is NOT available to small molecule antagonists and is a
differentiation dimension for antibody therapy. In field 4 (antibody
landscape), note the isotype AND whether CDC/ADCC is a feature. In field
6, the dual-mechanism (blockade + depletion) may explain efficacy that
pure blockade cannot. In field 11, an engineered Fc for enhanced CDC/ADCC
could amplify the depleting mechanism.

## Small molecule clinical failure may be modality-specific

Over 30 clinical trials of small molecule P2X7 antagonists in RA, OA, COPD,
and Crohn's disease yielded disappointing results. Key insight from the Di
Virgilio review: many tested compounds are **negative allosteric
modulators** that bind at a site distinct from the ATP-binding pocket. This
allosteric site **narrows when ATP is bound**, restricting drug access. At
inflammatory sites where extracellular ATP can reach hundreds of
micromolar (4-5 orders of magnitude above healthy tissue), allosteric
modulators may be unable to compete. (PMID 28723547.)

**Generalizable insight:** When a target has failed clinically with small
molecules, assess whether the failure was **modality-specific** (wrong
binding site, wrong mechanism — e.g., allosteric vs competitive) before
declaring the target invalid. A competitive antibody at the ATP-binding
site, or a nanobody with 20-50x greater potency (Dano1), may succeed where
allosteric small molecules failed. In field 6 (failure modes), distinguish
between "target is not clinically valid" (biology doesn't support it) and
"modality was wrong" (right target, wrong drug class). In field 10
(competitive landscape), the small molecule failures do NOT preclude
antibody success — they define the efficacy bar and safety benchmark the
antibody must differentiate against.

## Non-functional conformational variant (nfP2X7) creates distinct epitope space

nfP2X7 is a non-functional conformation of P2X7 that is structurally
distinct from the canonical form and is expressed on the surface of tumor
cells. The L4 mAb does NOT bind nfP2X7. A polyclonal anti-nfP2X7 antibody
(BIL010t, Biosceptre) showed positive phase 1 results in basal cell
carcinoma (topical, 65% lesion reduction). nfP2X7-targeting CAR-T cells
have also been proposed. (PMID 28723547, PMID 42498814, PMID 39853757.)

**Generalizable insight:** The same gene product can have disease-specific
conformational states that are differentially antibody-targetable. An
antibody against the canonical conformation may miss the disease-specific
conformation, and vice versa. In field 5 (epitope landscape), note whether
the target has known conformational variants (e.g., nfP2X7, P2X7A vs P2X7B)
and whether characterized antibodies discriminate between them. In field
11 (differentiation), an antibody selective for the disease-specific
conformation could have a better therapeutic index than one targeting the
canonical form.

## P2RX7 genetic heterogeneity affects antibody binding and drug response

Over 150 non-synonymous SNPs in P2RX7 generate complex haplotypes with
gain- or loss-of-function. Key examples:
- **E496A** (rs3751143): common LOF SNP (~30% in some populations), reduced
  receptor activity but normal surface expression on T/B cells; reduced
  surface expression on monocytes/macrophages.
- **R307Q** (rs28360457): rare LOF SNP in the ATP-binding pocket; severely
  decreases agonist affinity AND abolishes L4 mAb binding — meaning patients
  with this SNP would be non-responders to L4-based therapy.
- **I568N** (rs1653624): rare LOF SNP, impairs receptor trafficking to
  plasma membrane.
- **T357S** (rs2230911): common LOF SNP, reduced activity without altered
  surface expression.

The L4 mAb epitope involves Arg307 — R307Q abolishes binding. The P2X7L
isoform (exons 7-8 skipped, deleting part of the extracellular domain)
also cannot bind L4. (PMID 42498814, PMID 28723547.)

**Generalizable insight:** For highly polymorphic targets, patient
genotype can affect antibody binding (epitope-disrupting SNPs), drug
response (LOF/GOF variants), and surface expression levels. In field 6
(failure modes), include genetic heterogeneity as a potential failure
mode — unstratified clinical trials may dilute efficacy if a substantial
fraction of patients carry epitope-disrupting or LOF variants. In field
11 (differentiation), genotype-stratified trials are an unexplored
opportunity for polymorphic targets.

## Full-text retrieval notes

- **PMC XML retrieval was highly effective for newer OA papers**: 4/7 papers
  retrieved via PMC XML (Elhage 2023 Pharmaceutics PMC10536354 — 40K chars;
  Elhage 2025 EJI PMC11760643 — 41K chars; Sluyter 2026 Purinergic Signal
  PMC13400550 — 37K chars; Rifat 2024 J Neuroinflammation PMC10895799 — 57K
  chars). All were open-access with full XML body text.
- **Jina reader succeeded on Immunity (Cell Press) review via linkinghub
  redirect**: PMID 28723547 (Di Virgilio 2017, Immunity) — no PMCID, DOI
  resolved to `linkinghub.elsevier.com/retrieve/pii/S1074761317302807`,
  jina returned 110K chars of full review text including body, figures
  captions, and references. This confirms the existing Cell Press/Elsevier
  known-blocks table entry: jina reader on the `linkinghub.elsevier.com`
  redirect URL works for Cell Press research journals (not just
  `cell.com` direct URLs).
- **2/7 abstract-only**: PMID 9808543 (Buell 1998, Blood — no DOI, no PMCID,
  pre-PMC era) and PMID 35850190 (Hu 2022, Brain Res Bull — Elsevier,
  no PMCID, jina blocked, Wayback no snapshot). Both had structured PubMed
  abstracts (961 and 1129 chars) sufficient for profile grounding.

(P2X7 profile, ~37K chars, 7 papers ingested, 7 unique PMIDs cited,
working-docs/hitlist-profiles/p2x7.md.)
