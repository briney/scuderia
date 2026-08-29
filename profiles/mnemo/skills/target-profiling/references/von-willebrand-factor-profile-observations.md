# Von Willebrand Factor (vWF) profile observations (2026-08-16)

Twenty-eighth level-2 profile (approved tier, cardiovascular/metabolic —
hemostasis/TTP). vWF is the **first nanobody therapeutic target profile**
— caplacizumab (Cablivi) is a bivalent VHH (single-domain antibody, ~15
kDa), not a conventional IgG. It is also the **first secreted soluble
protein target** in the profile series (all prior approved-tier targets
were cell-surface or membrane-associated). 5 key papers ingested: 1/5
PMC XML OA (J Clin Med, MDPI — 44.8K chars), 2/5 Wayback (both NEJM
trials — 48.5K and 41.7K chars), 2/5 abstract-only (Blood/ASH
Publications and JAMA — both confirmed publisher blocks). 60% full-text
retrieval rate. ~26K chars (profile), 5 unique PMIDs, 36 authors across 5
papers. New observations:

## 1. Nanobody format — the first non-IgG approved antibody therapeutic in the profile series

Caplacizumab is a bivalent, humanized single-variable-domain
immunoglobulin fragment (VHH, ~15 kDa) derived from llamas. This is
fundamentally different from every prior approved antibody in the
profile series (all conventional IgG1/IgG2/IgG4). The nanobody format
creates several profile-specific considerations:

- **Field 4 (antibody landscape)**: The "Format" field must describe the
  VHH architecture (bivalent, two linked single-domain fragments), not
  just "naked IgG." The "Isotype/subclass" field should note "VHH
  (single-domain antibody, camelid-derived)" — it is NOT an IgG
  subclass.
- **Field 6 (success factors)**: The nanobody's small size (~1/10 of
  IgG) provides rapid tissue penetration and fast onset — a format
  advantage specific to nanobodies. However, the short half-life
  (~1 hour after IV) requires daily SC dosing, which is a format
  disadvantage for convenience.
- **Field 8 (safety)**: The short half-life IS a safety feature — rapid
  reversibility by withholding the drug (vWF function recovers within
  hours) is a nanobody-specific advantage over longer-acting IgG
  antibodies. This is the first profile where rapid clearance is a
  designed safety mechanism, not a drawback.
- **Field 11 (differentiation)**: A longer-acting anti-vWF format
  (PEGylated VHH, Fc-fused VHH, or conventional IgG) could reduce dosing
  frequency but would sacrifice the rapid reversibility safety
  advantage. This is a format-efficacy-safety trilemma unique to
  nanobody-to-IgG format switching.

## 2. Secreted soluble protein — no membrane-proximal accessibility concerns

vWF is a large multimeric glycoprotein secreted by endothelial cells
and megakaryocytes, circulating in plasma. This is the **first target
in the profile series that is not membrane-bound**. Implications:

- **Field 1 (target identity)**: "Localization: secreted (circulating
  plasma protein)" — fully accessible to antibodies in circulation, no
  membrane-proximal regions to navigate.
- **Field 5 (epitope landscape)**: "Membrane-proximal regions: Not
  applicable — vWF is soluble, not membrane-anchored." This eliminates
  the membrane-accessibility concern that affects most cell-surface
  targets.
- **Field 9 (structural information)**: The A1 domain is accessible in
  both globular and extended vWF conformations — no membrane occlusion.
  The conformational state (shear-induced unfolding) is the relevant
  variable, not membrane proximity.
- For soluble targets, the antibody doesn't need to compete with
  membrane-bound target density — it interacts with the circulating
  protein directly. PK/PD considerations differ: the antibody's
  distribution volume and the target's plasma concentration matter
  more than receptor occupancy on cells.

## 3. Downstream-blockade strategy — blocking the consequence, not the cause

Caplacizumab blocks vWF–platelet GPIb interaction (downstream platelet
aggregation), NOT the upstream ADAMTS13 deficiency (the autoimmune
cause of iTTP). This is a mechanistic pattern distinct from prior
profiles:

- **Field 6 (failure modes)**: Relapse on discontinuation with
  persistent ADAMTS13 <10% is a mechanism-based failure — caplacizumab
  does not address the underlying autoimmunity. This was observed in
  the TITAN phase 2 trial (8 relapses, 7 with ADAMTS13 <10%) and
  mitigated in HERCULES by extending treatment until ADAMTS13 recovery.
  The lesson: for downstream-blockade antibodies, the treatment
  duration must be guided by the upstream cause's resolution
  biomarker (ADAMTS13 activity), not by the downstream effect's
  resolution (platelet count).
- **Field 6 (success factors)**: Biomarker-guided duration (treat
  until ADAMTS13 recovery) reduced relapses in HERCULES vs. fixed
  30-day dosing in TITAN. This is a trial-design success factor: for
  downstream-blockade antibodies, adaptive duration based on the
  upstream biomarker outperforms fixed-duration dosing.
- This pattern (downstream blockade + biomarker-guided duration) is
  generalizable to any target where the antibody blocks the
  pathological consequence but not the disease cause. For field 6,
  always ask: does the antibody address the cause or the consequence?
  If the consequence, what biomarker signals the cause has resolved?

## 4. On-target bleeding — the universal risk of anti-hemostatic antibodies

The most common caplacizumab adverse event is mucocutaneous bleeding
(54–65% vs. 38–48% placebo). This is an on-target, mechanism-intrinsic
toxicity — vWF is essential for primary hemostasis, and blocking it
impairs platelet adhesion. Observations:

- **Field 8 (safety)**: Bleeding is not a side effect — it IS the
  mechanism. The therapeutic index is the balance between preventing
  pathological thrombosis (TTP) and preserving physiological
  hemostasis. In TTP (life-threatening, >90% mortality untreated), the
  balance favors anti-thrombotic benefit. Outside TTP (e.g., chronic
  stroke prevention), the index would be much narrower.
- **Field 11 (differentiation)**: No format or epitope change can
  eliminate bleeding risk for an anti-vWF antibody — it is
  mechanism-intrinsic. The only mitigation is the narrow therapeutic
  window (TTP-specific) and rapid reversibility (nanobody short
  half-life). This is a "therapeutic ceiling" for the target class.

## 5. PubMed search via urllib — URL-encoding pitfall confirmed

The initial PubMed esearch attempt failed because `urllib.request.urlopen`
rejects URLs containing spaces (control character error). The fix
(documented in prior profiles, confirmed here):
`urllib.parse.quote(query_string, safe='')` URL-encodes spaces as `%20`
and all special characters, producing a valid URL. This is the
Python-urllib analogue of the bracket-encoding rule for curl. Always
URL-encode the entire query term before constructing the esearch URL.

## 6. Blood (ASH Publications) and JAMA Network — confirmed publisher blocks

Both PMID 28416507 (Blood, Joly 2017) and PMID 40388146 (JAMA, Pishko
2025) were abstract-only after three-source closure:
- **Blood**: inPMC=N, isOpenAccess=N, hasPDF=N. Jina reader proxy
  returns Cloudflare CAPTCHA (~518 bytes). No Wayback CDX snapshots.
  EPMC fullTextXML returns 404. Direct PDF URL returns 403. EPMC PDF
  render returns HTML, not PDF. Confirms the paper-ingest skill's
  ASH Publications entry.
- **JAMA**: inPMC=N, isOpenAccess=N, hasPDF=N. Jina reader proxy
  returns Cloudflare CAPTCHA (~504 bytes). No Wayback CDX snapshots
  (empty response for all URL variants). Confirms the paper-ingest
  skill's JAMA Network entry.

Both had comprehensive structured abstracts (1.9K and 3.1K chars
respectively) sufficient for profile grounding of fields 2, 3, and 6
at abstract level. The JAMA 2025 review abstract contained quantitative
efficacy and safety data (risk differences with 95% CIs) directly
usable in fields 6 and 8.

(vWF profile, ~26K chars, 5 papers, 36 authors, 5 unique PMIDs cited,
working-docs/hitlist-profiles/von-willebrand-factor.md.)
