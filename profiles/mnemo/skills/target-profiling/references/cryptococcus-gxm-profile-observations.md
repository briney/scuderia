# Cryptococcus GXM profile observations (2026-08-17)

Preclinical-tier infectious disease target. Glucuronoxylomannan (GXM) —
the major capsular polysaccharide of *Cryptococcus neoformans*. Not a
protein: a high-molecular-weight (~1.7 MDa) polysaccharide of mannose,
xylose, and glucuronic acid with O-acetylation. Secreted/extracellular;
forms a capsule around the yeast cell AND accumulates in serum (CrAg)
and tissues during infection. 5 key papers ingested (3/5 full text via
Europe PMC PDF render — PMC549259, PMC105619, PMC98299; 2/5 abstract-only
— J Immunol paywalled, not in PMC). ~49K chars, 5 unique PMIDs cited.
Key new patterns:

## 1. Fungal polysaccharide capsule — first fungal target, extends the
non-protein target pattern

GXM is the first profiled target from a fungal pathogen and the first
capsular polysaccharide target. Like M. tb LAM (glycolipid), GXM is NOT
a protein — no UniProt entry, no HGNC gene symbol, no single-chain
sequence. Field 1 (Target identity) adapts the same way as LAM: gene
symbol → biosynthetic enzyme genes (CAP10, CAP59, CAP60, CAP64, CAS1);
UniProt ID → N/A; key domains → glycan structural motifs (O-acetylation
sites, xylose side chains, glucuronic acid residues, mannose backbone).

But GXM differs from LAM in a critical way: GXM is BOTH a surface
capsule component AND a shed circulating antigen. LAM is a cell wall
glycolipid (surface only). GXM accumulates in serum (cryptococcal
antigenemia, CrAg) where it mediates systemic immunosuppression —
inhibiting leukocyte migration, inducing T-suppressor cells, enhancing
HIV replication, promoting cerebral edema, causing antibody
unresponsiveness. This dual location (capsule + serum) means the
antibody target exists in two compartments: surface-bound (opsonization)
and soluble circulating antigen (neutralization + clearance). For field
2, describe both compartments and the immunosuppressive effects of
circulating GXM. For field 6, the antibody must address both: opsonize
the yeast (Fab + Fc) AND clear circulating antigen (immune complex
formation → reticuloendothelial clearance).

Generalizes to any capsular polysaccharide target (pneumococcal,
meningococcal, *C. gattii* GXM) where the capsule is both a surface
virulence factor and a circulating antigen.

## 2. Single clinical candidate with completed Phase 1 and NO follow-on —
a unique pipeline shape

mAb 18B7 (murine IgG1) is the ONLY anti-cryptococcal mAb to reach
clinical trials — a Phase 1 dose-escalation study in HIV-infected
patients with treated cryptococcal meningitis (PMID 15728888, 2005).
The trial was the first application of mAb therapy for ANY fungal
disease in humans. The MTD was 1.0 mg/kg; 2.0 mg/kg exceeded MTD.
No Phase 2/3 trial has ever been conducted. No subsequent anti-GXM
mAb has entered clinical development in the 21 years since.

This creates a unique pipeline shape for field 4 (antibody landscape)
and field 10 (competitive landscape): exactly one clinical candidate,
Phase 1 completed, no follow-on, entirely academic (Albert Einstein
College of Medicine / NIAID Mycoses Study Group). No pharmaceutical
company has an active anti-GXM mAb program. For field 10, this is
neither "saturated" (many antibodies) nor "blue ocean" (no one has
heard of the target) — it is "validated clinically (Phase 1 safety),
stalled development." The target is clinically de-risked for safety
but commercially undeveloped.

For field 6, the failure modes from the Phase 1 trial are highly
informative even though the trial succeeded: (a) mAb undetectable in
CSF (BBB penetration failure), (b) 53h half-life (vs ~21 days for
typical IgG — antigen-antibody complex rapid clearance), (c) HAMA in
~10%, (d) HIV load increase in 35%, (e) transient CrAg decline (2-3
fold, returned to baseline by week 12). These are the lessons for the
next antibody, not reasons to abandon the target.

## 3. Protective vs nonprotective from the SAME V-region genes —
epitope-dependent protection where immunodominance is the problem

The most distinctive feature of GXM as a target: the immunodominant
antibody response generates BOTH protective and nonprotective
specificities from the SAME V-region genes (VH7183, JH2, Vk5.1, Jk1).
Class II MAbs (18B7, 2H1, 12A1, 2D10, 3E5) and nonprotective MAbs
(13F1, 21D2) share the same V-region gene families but differ by
somatic mutations. Two VH residues — F33 (CDR1) and N57 (CDR2) —
determine the annular (protective) vs punctate (nonprotective) binding
pattern. Site-directed mutagenesis converting F33→Y33 and N57→S57
switched MAb 12A1 from protective to nonprotective (PMID 11292763).

This is fundamentally different from AMA1 antigenic polymorphism
(where the TARGET varies across strains) — here the target is
constant, but the antibody RESPONSE generates both outcomes. The
problem is immunodominance: the immunodominant epitope elicits both
protective and nonprotective antibodies. A rationally designed
therapeutic mAb bypasses this by selecting only the protective
specificity.

For field 5, the annular vs punctate classification is the key epitope
taxonomy. For field 6, "immunodominance generating nonprotective
specificities" is a distinct failure category for vaccine design (but
NOT for therapeutic mAb design, where the specificity is chosen). For
field 11, the differentiation opportunity is selecting antibodies with
the F33/N57 motif and using the anti-idiotypic MAb 7B8 (which
recognizes protective but not nonprotective MAbs) as a screening
reagent.

Generalizes to any polysaccharide or glycan target where the
immunodominant response includes both protective and nonprotective
specificities (pneumococcal capsule, GXM of *C. gattii*).

## 4. Isotype-dependent fine specificity — constant region allostery
affects epitope binding pattern

McLean 2002 (PMID 12133962, J Immunol) demonstrated that expressing
the 18B7 V regions with different human constant regions changed the
binding pattern: IgG1, IgG2, IgG4, IgA → annular (protective); IgM,
IgG3 → punctate (nonprotective) — despite IDENTICAL V-region sequences.
This is a concrete demonstration of antibody allostery: the constant
region affects the variable region's conformation and binding
specificity, not just its effector function.

For field 4 (antibody landscape), always note the isotype AND its
effect on the binding pattern — not just the effector function. For
field 6, "wrong isotype" is a failure mode that changes SPECIFICITY,
not just effector function — an IgM or IgG3 version of an otherwise
protective antibody would be nonprotective. For field 11, isotype
selection (IgG1 preferred) is a design constraint, not just a
preference.

This connects to the broader antibody allostery concept (Casadevall &
Janda 2012, PMID 22826242) and generalizes to any polysaccharide-
binding antibody where the constant region can influence the paratope
conformation.

## 5. BBB penetration failure — a CNS-specific PK failure mode for
brain infection targets

mAb 18B7 was UNDETECTABLE in the CSF of all 20 patients in the Phase 1
trial (PMID 15728888). The antibody does not cross the blood-brain
barrier at therapeutic concentrations. This is a critical limitation
for cryptococcal meningitis, where the primary site of infection is
the CNS. The serum half-life was only ~53 hours (vs ~21 days for
typical human IgG1), likely due to rapid antigen-antibody complex
formation and clearance by the reticuloendothelial system.

For field 6, BBB non-penetration is a distinct failure mode from
"wrong epitope" or "wrong isotype" — it is a PK/distribution failure
that no amount of epitope or format optimization can fix without
actively engineering CNS penetration. For field 8 (safety), the
absence of CNS antibody may actually be a safety feature (no
neuroinflammation from immune complex deposition in brain tissue).
For field 11, differentiation opportunities include: (a) intrathecal
delivery, (b) receptor-mediated transcytosis engineering (anti-TfR),
(c) focused ultrasound BBB disruption, (d) treating antigenemia
pre-CNS involvement (prevention rather than treatment of meningitis).

Generalizes to any CNS infection target (bacterial meningitis
capsular polysaccharides, viral encephalitis glycoproteins) where BBB
penetration is a prerequisite for efficacy.

## 6. PubMed E-utilities rate limiting — batch efetch can hit limits

During this session, a batch efetch call for 5 PMIDs returned
`{"error":"API rate limit exceeded","api-key":"192.26.252.1","count":"4","limit":"3"}`
after 4 esearch calls + 1 esummary call in quick succession. The rate
limit is ~3 requests per second per IP. Recovery: sleep 15s and retry
the efetch call — the retry succeeded. The rate limit is recoverable,
not a hard block.

Mitigation: (a) sleep 3-5s between E-utilities calls (already
documented in the skill), (b) when hitting the rate limit, sleep 15s
(not 3-5s) before retrying the failed call, (c) prefer esummary (lighter)
over efetch (heavier) for initial paper screening — only efetch the
final selected landmark papers, (d) batch efetch calls are more
efficient but count as one request per PMID in the batch, so a 5-PMID
efetch is effectively 5 requests.

This is a transient operational note, not a target-class observation.
Already partially documented in the skill's "sleep 3-5s between
E-utilities calls" guidance; the addition is the 15s backoff for rate-
limit recovery and the preference for esummary over efetch for
screening.

(Cryptococcus GXM profile, ~49K chars, 5 papers ingested (3 full text,
2 abstract-only), 5 unique PMIDs cited,
working-docs/hitlist-profiles/cryptococcus-gxm.md.)
