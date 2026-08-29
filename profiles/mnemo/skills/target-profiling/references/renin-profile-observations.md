# Renin (REN) profile observations — 2026-08-16

Forty-third level-2 profile (clinical-trial tier, cardiovascular — RAAS
enzyme). Renin is the rate-limiting enzyme of the renin-angiotensin-
aldosterone system (RAAS) and the first secreted aspartic protease
profiled. The clinical context is dominated by small-molecule renin
inhibitors (remikiren, aliskiren) — no therapeutic antibody against
renin has ever been developed. 7 papers ingested (1/7 full text via
PMC XML; 6/7 abstract-only — all paywalled). ~27K chars profile, 83
PMID citations. Key new patterns:

## (1) Small-molecule-dominant target with no antibody pipeline

Renin is the first profiled target where the entire clinical landscape
is small-molecule (aliskiren approved, remikiren discontinued), and
the only antibodies ever raised against it are research tools (Simon
1981, PMID 6788795; Zuo 1992, PMID 1548051). The profile's field 4
(antibody landscape) lists research mAbs alongside small-molecule
inhibitors, each clearly tagged "not an antibody." For field 10
(competitive landscape), the "pipeline depth" entry must explicitly
state "no therapeutic antibodies in development" — the antibody space
is completely open. For field 11 (differentiation), the opportunity
framing is inverted: instead of "what epitope/format differentiates
from existing antibodies," it's "why would an antibody be better than
the approved small molecule." The answer is longer half-life, complete
(>99%) active-site blockade, and (P)RR co-targeting via bispecific
format.

## (2) Reactive renin secretion as a fundamental biological limitation

Renin inhibition triggers compensatory reactive renin secretion via
the feedback loop. Aliskiren causes greater reactive rises in plasma
renin concentration than any other antihypertensive class. Because
aliskiren only blocks 90–95% of plasma renin activity, the expanded
renin pool can offset BP-lowering at higher doses (600 mg = 300 mg
plateau) (PMID 17485026). This is a target-inherent limitation, not a
drug-specific one — any pharmacological renin inhibitor (small
molecule or antibody) faces the same feedback loop. For field 6
(failure modes), this is a "mechanism-of-action ceiling" failure
distinct from epitope, population, or format failures. For field 11,
the differentiation opportunity is an antibody achieving >99% blockade
(to overcome the 90–95% ceiling) or a depleting antibody (clearing
circulating renin to reduce the reactive pool).

## (3) ALTITUDE trial — dual RAAS blockade toxicity as a class effect

The ALTITUDE trial (PMID 23121378) stopped early because adding
aliskiren to ACEi/ARB in diabetic patients with CKD/CVD caused excess
hyperkalemia (11.2% vs 7.2%), hypotension (12.1% vs 8.3%), and possibly
nonfatal stroke (2.6% vs 2.0%). This is a dual-RAAS-blockade toxicity
class effect, not specific to aliskiren — ONTARGET (ramipril +
telmisartan) showed the same pattern. For field 6, the lesson is that
the failure was the trial design (add-on to existing RAAS blockade)
and the population (diabetic with renal impairment), not the target
itself. Monotherapy was safe and effective. For field 8, dual RAAS
blockade contraindications are a safety constraint that applies to any
new renin-targeting agent, including an antibody.

## (4) Surrogate endpoint misdirection (AVOID → ALTITUDE)

The AVOID trial showed a 20% reduction in albumin/creatinine ratio
(surrogate) with aliskiren added to losartan, but ALTITUDE showed no
benefit on hard cardio-renal endpoints and possible harm. This
confirms the pattern from ONTARGET: surrogate biomarkers
(microalbuminuria) did not predict hard outcomes. For field 6,
surrogate endpoint success is a misleading signal for dual RAAS
blockade. For field 7 (assay systems), this means hard endpoints
(cardiovascular death, ESRD, doubling of creatinine) must be used
for any future renin-targeting trial, not surrogate renal markers.

## (5) Secreted enzyme target — antibody accessibility profile

Renin is the first secreted enzyme target profiled (previous
secreted/soluble targets were cytokines and complement proteins). As
a secreted protein, all surface epitopes are accessible to circulating
antibodies — no membrane-proximal or transmembrane accessibility
constraints. However, the stoichiometry challenge is significant: an
antibody must neutralize circulating renin at sufficient concentration
in the plasma compartment, and the reactive renin feedback loop
continuously produces more. For field 1 (localization), "secreted"
with the note on antibody accessibility is the correct framing. For
field 11, the high volume of distribution and continuous production
rate are practical challenges for antibody dosing.

## (6) Species specificity requiring primate models

Renin has strong species specificity — the first anti-renin mAb
recognized human and monkey renin but not hog or mouse (PMID 6788795).
Renin inhibitors developed for humans have >100-fold lower potency
against rodent renin. This required primate hypertension models for
preclinical development (PMID 8498974). For field 2, species cross-
reactivity notes must flag that standard rodent models are not
usable — transgenic human-renin/human-angiotensinogen models or
primate models are required. For field 7, this limits preclinical
assay options and increases the translational gap.

## (7) 100% paywall rate for cardiovascular landmark papers

All 7 ingested papers were paywalled with no OA access — the journal
mix (J Clin Endocrinol Metab [OUP], Hypertension [AHA], Arzneimittel-
forschung [no DOI], Clin Pharmacol Ther [Wiley], Am J Hypertens [OUP],
NEJM, EXCLI J [OA]). Only the EXCLI Journal review (PMID 26417326)
was retrieved via PMC XML; the other 6 returned `provenance: none`
from fetch_fulltext.py and jina reader returned CAPTCHA pages. This
is the lowest full-text retrieval rate of any profile (1/7 = 14%),
even worse than C5 (1/5 = 20%). Cardiovascular papers from the 1980s-
2000s era are predominantly in journals that predate OA policies.
Abstract-only was sufficient to build a high-quality profile — the
structured abstracts (especially ALTITUDE and the remikiren PK study)
carried enough trial design, safety, and efficacy data to ground
fields 2, 3, and 6.

## (8) (Pro)renin receptor ((P)RR) as a dual-target opportunity

The (pro)renin receptor ((P)RR) activates prorenin non-proteolytically
(without prosegment cleavage), contributing to tissue RAAS activity
and end-organ damage independent of circulating angiotensin II (PMID
26417326). No small-molecule or antibody currently targets (P)RR
clinically. For field 11, a bispecific antibody targeting both renin
active site and (P)RR could achieve dual blockade of circulating and
tissue RAAS with a single molecule — potentially avoiding the dual
small-molecule RAAS blockade toxicity of ALTITUDE. This is a
blue-ocean differentiation opportunity specific to the renin/(P)RR
axis.

(Renin/REN profile, ~27K chars, 7 papers (1/7 full text via PMC XML,
6/7 abstract-only), 83 PMID citations,
working-docs/hitlist-profiles/renin.md.)
