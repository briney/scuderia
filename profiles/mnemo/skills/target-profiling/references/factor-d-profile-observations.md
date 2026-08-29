# Factor D (CFD/adipsin) profile observations — 2026-08-16

Thirty-fourth level-2 profile (clinical-trial tier, immunology — complement
alternative pathway; also ophthalmology/geographic atrophy). Factor D is the
**rate-limiting serine protease of the alternative complement pathway** — a
24 kDa non-glycosylated soluble plasma protein produced primarily by
adipocytes (hence "adipsin"). 5 papers ingested, 2/5 PMC XML OA (Front Immunol
×2), 1/5 EPMC PDF (IOVS — inPMC:Y, OA:N), 2/5 abstract-only (Bentham Curr Med
Chem, Elsevier Lancet Haematol). 60% full-text retrieval. ~36K chars, 5 unique
PMIDs, 42 authors.

## Key new patterns

### 1. Small-molecule-approved, antibody-failed — the open-antibody-space pattern with a known failure mode

Danicopan (ACH-4471/ALXN2040, Voydeya) is a first-in-class **oral small-
molecule** factor D inhibitor approved by FDA (January 2025) as add-on to C5
inhibitors for PNH with clinically significant EVH. The ALPHA Phase 3 trial
(NCT04469465) showed +2.44 g/dL hemoglobin vs placebo (p<0.0001) at 12 weeks.
Meanwhile, lampalizumab (FCFD4514S, Genentech/Roche) — the only anti-factor D
**antibody** to reach clinical trials — showed promising Phase II results for
geographic atrophy (GA) but **FAILED in two Phase III trials**.

This is a distinct pattern from:
- C5aR1 (avacopan approved, no antibody tried) — antibody space open, no
  failure precedent
- GHR (pegvisomant approved, no antibody tried) — antibody space open, no
  failure precedent
- Factor D: antibody space open BUT with a known failure mode (lampalizumab
  Phase III)

For field 4 (antibody landscape), when a small molecule is approved and an
antibody has failed, the profile must document: (a) the small molecule
validates the target, (b) the antibody failure is a specific failure mode
not a target invalidation, (c) the antibody space is open but requires
differentiation from the failed approach. For field 6 (failure modes),
analyze WHY the antibody failed (format, route, indication, incomplete
blockade) vs why the small molecule succeeded (systemic oral delivery,
add-on design, biomarker-selected population). For field 11
(differentiation), the differentiation must be explicit: different epitope,
different format (full IgG vs Fab), different route (systemic vs
intravitreal), different indication, or biomarker-selected population.

### 2. Self-inhibitory loop as conformational targeting challenge

Factor D has a unique structural feature: a **self-inhibitory loop** that
locks the catalytic triad in an inactive resting state. Factor D only
becomes catalytically active upon binding to the C3bB complex, which
triggers a conformational change. After cleaving factor B, factor D returns
to the inactive state. This creates a conformational targeting challenge
for antibodies:

- Antibodies targeting the catalytic site face access limitations (site is
  sequestered in the resting state by the self-inhibitory loop)
- Antibodies that lock factor D in its self-inhibited conformation
  (preventing the activation conformational change) are an unexplored
  approach
- Antibodies targeting the factor D–C3bB interface (blocking substrate
  recruitment) rather than the enzyme active site represent another
  unexplored approach

For field 5 (epitope landscape) and field 9 (structural information), the
conformational states of the target are not just structural details — they
directly determine which epitopes are functionally relevant. A target with
a conformational switch (active vs inactive) requires epitope mapping in
both states. This generalizes to any serine protease with zymogen-to-active
conformational transitions.

### 3. EPMC PDF as reliable fallback for inPMC:Y, OA:N papers

PMID 22003108 (Stanton 2011, IOVS) had `inPMC: Y, isOpenAccess: N`. The PMC
XML had no `<body>` element (metadata-only PMC record). The EPMC PDF render
endpoint (`https://europepmc.org/api/getPdf?pmcid=PMC3230905`) returned a
full 342K PDF, which pymupdf extracted to 40K chars of usable text. This
extends the known EPMC PDF success cases: it works not just for embargoed
OA papers but also for non-OA papers that have a PMC metadata record with
no XML body. The EPMC PDF endpoint is a higher-yield fallback than jina or
Wayback for this specific paper state (inPMC:Y, OA:N, no PMC XML body).

### 4. Phase II success → Phase III failure (lampalizumab) — a distinct antibody failure trajectory

Lampalizumab showed promising Phase II results (reduced GA lesion growth
via intravitreal injection) but FAILED in two Phase III trials. This is the
first profile in the set with this specific failure trajectory. Prior
failed-antibody profiles had earlier failures (Phase II or preclinical).
The Phase II→III failure suggests:

- The antibody's mechanism was biologically active (Phase II signal was real)
- The Phase III failure may reflect: (a) insufficient degree of AP blockade
  (even low factor D levels sustain AP activity), (b) intravitreal route
  limitation (local only, doesn't address systemic adipose-derived factor D),
  (c) AP not the sole driver (classical/lectin pathways contribute to GA),
  (d) bypass mechanisms (kallikrein can cleave C3 independently of factor D),
  (e) Fab format limitations (shorter half-life than full IgG, potentially
  requiring more frequent dosing)

For field 6, this is a richer failure analysis than a simple "didn't work"
— the Phase II success provides evidence that the target was engaged, and
the Phase III failure points to specific remediable factors. For field 11,
each potential failure reason suggests a specific differentiation strategy.

### 5. Delegation with search instructions — complement target validation

The subagent received search query templates (not pre-identified PMIDs) and
topic coverage requirements: danicopan/ACH-4471, anti-factor D antibodies,
factor D biology. The subagent ran 4 esearch queries, used esummary to
screen 65 unique PMIDs, and selected 5 papers covering all topics:
- Danicopan discovery (Wiles 2020, Curr Med Chem)
- Factor D as strategic target (Barratt 2021, Front Immunol) — the most
  comprehensive review, with full text
- Danicopan PNH Phase 3 trial (Lee 2023, Lancet Haematol) — the pivotal
  clinical evidence
- Factor D in cardiovascular/metabolic disease (Kong 2024, Front Immunol)
  — adipsin biology
- Factor D in AMD (Stanton 2011, IOVS) — GA genetic/plasma evidence

This validates the IL-17A delegation pattern for a complement target in a
different therapeutic area. The subagent autonomously implemented the full
paper-ingest pipeline (PubMed XML, Europe PMC, full-text ladder, paper page
writing) using urllib.request directly, without invoking the
fetch_fulltext.py script. The subagent's implementation followed the same
ladder pattern (PMC XML → EPMC PDF → jina → Wayback → abstract-only).

### 6. Bentham Science (Curr Med Chem) publisher block confirmed

PMID 31573880 (Wiles 2020, Curr Med Chem) was published by Bentham Science
(eurekaselect.com). The DOI resolved to a Cloudflare-protected page;
jina reader returned a CAPTCHA page (496 chars). Wayback had no snapshot.
This confirms Bentham Science as a hard-block publisher for full-text
retrieval — add to the known-blocks table alongside ASH/Blood,
ScienceDirect, Wiley, Karger. The abstract (1,432 chars) was sufficient
for the danicopan discovery context.

(Factor D profile, ~36K chars, 5 papers, 42 authors, 5 unique PMIDs cited,
working-docs/hitlist-profiles/factor-d.md.)
