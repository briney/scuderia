# tPA (Tissue Plasminogen Activator, PLAT) profile observations (2026-08-17)

Forty-plus level-2 profile (preclinical tier, cardiovascular — thrombolysis/
stroke). tPA is the **first profiled target where the approved drug is a
recombinant form of the target protein itself** (alteplase = recombinant
tPA), and antibodies aim to *improve on* the approved protein, not replace
an absent therapy. It is also the **first target with two mechanistically
opposite antibody strategies** that both make therapeutic sense: (1)
antibody-*targeted* thrombolysis (conjugate/bispecific MAbs that
*potentiate* tPA by localizing it to the clot) and (2) antibody-*blockade*
of tPA's harmful non-thrombolytic signaling (anti-tPA/NMDAR, anti-LRP1).
5 key papers ingested: 2/5 full text (1 EPMC PDF render for a 1987 PNAS
paper, 1 PMC XML OA for a 2014 review), 3/5 abstract-only (NEJM, Circulation,
Wiley — all confirmed publisher blocks). 40% full-text retrieval rate, but
the 2014 review (PMC OA, 30K chars) provided comprehensive coverage of the
antibody-targeting approaches and the 1987 PNAS full text provided the
quantitative conjugate data. ~43K chars profile, 10 PMIDs cited across the
profile. New observations:

## 1. Function-selective antibody — block the side effect, preserve the therapeutic function

Glunomab (anti-tPA/NMDAR) is the first profiled antibody that selectively
blocks a target's *deleterious side-effect pathway* while preserving the
target's *desired therapeutic activity*. tPA has two functional axes: (a)
catalytic thrombolysis (the therapeutic effect — plasminogen → plasmin →
clot lysis) and (b) non-catalytic NMDAR/LRP1 signaling (the side effect —
BBB breakdown, neuroinflammation, hemorrhagic transformation). Glunomab
blocks (b) without blocking (a). This is a third antibody-mechanism class,
distinct from:
- **Neutralizing antibodies** (block the target's primary function)
- **Potentiating antibodies** (enhance/localize the target's function, e.g.,
  the 59D8-tPA conjugate, bispecific F36.23)
- **Function-selective antibodies** (block a secondary function while
  preserving the primary function — Glunomab)

For field 4 (antibody landscape) and field 5 (epitope landscape), a
function-selective antibody requires describing *which function is blocked
and which is preserved*, not just "neutralizing" or "non-neutralizing." The
epitope must map to the signaling interface (growth-factor domain for
NMDAR), not the catalytic site. For field 6, the success factor is
*dissociating* the dose-limiting toxicity from the efficacy — widening the
therapeutic index without changing the dose of the primary drug. For field
11, function-selective antibodies are a differentiated mechanism with a
clear value proposition over total neutralization (which would abolish the
therapeutic effect) or total potentiation (which does not address the
side-effect pathway). Generalizes to any target with separable beneficial
and harmful functions (e.g., growth factors with proliferative vs.
neuroprotective signaling; complement components with opsonization vs.
inflammation).

## 2. Dual-antibody-strategy target — two opposite directions, both valid

tPA is the first profiled target with two antibody strategies that move in
*opposite mechanistic directions* and *both are therapeutically rational*:
- **Strategy 1 (potentiation)**: conjugate/bispecific MAbs *increase* tPA
  activity at the clot (59D8, F36.23) — the goal is more thrombolysis with
  less systemic bleeding.
- **Strategy 2 (signaling blockade)**: anti-tPA/NMDAR or anti-LRP1 MAbs
  *decrease* tPA's neurovascular side effects — the goal is less BBB
  damage while retaining thrombolysis.

This is distinct from the clusterin "double-edged sword" pattern (same
target, opposite biology in different tissues, one direction per disease).
Here, *both* directions apply to the *same* disease (stroke) and could in
principle be combined (a bispecific that targets tPA to fibrin AND blocks
tPA–NMDAR). For field 6, the failure modes differ by strategy: strategy 1
fails on format (murine, chemical conjugation, short half-life —
translational, not biological), strategy 2 fails on being early
(preclinical, not yet in humans). For field 11, the combination of both
strategies in one molecule is an unexplored differentiation opportunity.
For field 10, the competitive landscape must describe both the
recombinant-protein competitors (alteplase, tenecteplase, reteplase) AND
the antibody competitors (all preclinical), which are in different
"modalities" — the antibody is not competing with another antibody, it is
competing with an approved recombinant protein and with mechanical
thrombectomy.

## 3. Approved recombinant protein as the benchmark — antibody improves on the drug, not the target

tPA is the first profiled target where the approved drug (alteplase) is a
recombinant version of the target protein itself. The antibody is not
filling a therapeutic gap (no approved antibody exists) — it is trying to
*improve on* an existing, effective, generic, cheap protein drug. This
shapes several fields:
- **Field 3 (disease evidence)**: the clinical-success evidence is for
  the recombinant protein (alteplase), not for an antibody. The antibody's
  clinical evidence is all preclinical. The profile must clearly separate
  "evidence for the target" (strong — approved drug) from "evidence for an
  antibody against the target" (weak — all preclinical).
- **Field 6 (failure modes)**: the dominant failure mode is *translation*,
  not biology. The preclinical proof-of-concept is 40 years old (1987) and
  no antibody has entered human trials. The barrier is that the approved
  recombinant protein + mechanical thrombectomy already address much of the
  need, raising the bar for an antibody's added value.
- **Field 8 (safety)**: the bleeding/ICH risk is mechanism-intrinsic to tPA
  *regardless of modality* (recombinant protein or antibody-potentiated).
  The function-selective antibody (Glunomab) is the only approach that can
  reduce the CNS-specific risk without reducing thrombolysis.
- **Field 10 (competitive landscape)**: the "pipeline depth" must include
  the recombinant-protein competitors (alteplase, tenecteplase, reteplase)
  alongside the antibody pipeline (all preclinical). The market-size
  discussion is framed by the existing thrombolytic market, not a
  hypothetical one.

Generalizes to any target where a recombinant protein (or other modality)
is already the approved drug and antibodies are the *second-generation*
improvement (e.g., recombinant cytokines → antibody-cytokine fusions;
recombinant enzymes → antibody-enzyme conjugates for targeting).

## 4. PubMed search with multiple query variants — the 4-query pattern

The standard esearch approach (4 query variants with different [tiab]
combinations) worked well for tPA. The queries:
1. `"tissue plasminogen activator" antibody[tiab]`
2. `"tPA antibody"[tiab] thrombolysis`
3. `"tPA" monoclonal antibody[tiab]`
4. `"tissue plasminogen activator" monoclonal antibody` (no field tag)

produced 20 unique PMIDs with good overlap on the key papers. The
abbreviated form ("tPA") and the full form ("tissue plasminogen activator")
returned *different* results — both are needed. Adding a clinical-trial
query (`"NINDS" rt-PA stroke trial`) and a mechanism query
(`"tissue plasminogen activator" neurotoxicity NMDA receptor`) was
necessary to capture the approved-drug evidence and the
signaling-blockade rationale that the antibody-focused queries missed.
Lesson: for a target with both an approved drug and an emerging antibody
strategy, run *both* drug-focused and antibody-focused queries; the
antibody queries alone will miss the clinical-evidence anchor.

## 5. Full-text retrieval for older papers — EPMC PDF render works for 1980s PNAS

PMID 3118374 (Runge 1987, PNAS) was retrieved via the EPMC PDF render
branch (provenance: epmc-pdf, 21.9K chars) despite inPMC=Y but
isOpenAccess=N. The PMC XML branch returned no <body> (metadata-only), but
the EPMC PDF render succeeded because the article is inPMC. This confirms
the fetch_fulltext.py ladder's branch 1b (EPMC PDF) is valuable for older
papers that are in-PMC but not open-access. The OCR quality of the 1987
scanned PDF was usable for profile grounding (some character recognition
errors in the methods, but the results and discussion were clean).

The 2014 review (PMID 25780787, Global Cardiology Science & Practice,
MDPI) was retrieved via PMC XML (OA, 30K chars) and provided comprehensive
coverage of antibody-targeting approaches (anti-fibrin conjugates,
bispecifics, ATTEMPTS, camouflaged-tPA, nano-delivery). For target
profiles, a good review paper with full text can substitute for multiple
primary papers when the primary papers are paywalled — the review cites
and summarizes them.

(tPA/PLAT profile, ~43K chars, 10 papers ingested (2/10 full text, 8/10
abstract-only), 10 unique PMIDs cited,
working-docs/hitlist-profiles/tpa.md.)
