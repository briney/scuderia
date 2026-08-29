# CCHFV GP profile observations (2026-08-17)

Session-specific detail from profiling Crimean-Congo hemorrhagic fever virus
glycoprotein complex (CCHFV GP), a preclinical-tier infectious disease target.

Profile: `working-docs/hitlist-profiles/crimean-congo-gp.md` (~42K chars,
99 PMID citations across 17 distinct PMIDs).

## Retrieval pipeline used

- Direct PubMed E-utilities via `urllib.request` in `execute_code` (NOT curl
  via subprocess — `urllib.request` worked in this subagent's `execute_code`
  context without DNS errors, contrasting the caveat in SKILL.md delegation
  section). The DNS-error caveat may be environment-specific; if
  `urllib.request` works on the first call, continue using it (simpler than
  curl+subprocess).
- 8 PubMed esearch queries (broad, non-`[tiab]`-restricted): 69 unique PMIDs.
- esummary batch (25 IDs/call) for title/journal/date triage of all 69.
- Selective efetch (abstract) for ~20 landmark papers.
- UniProt REST API (Q8JSZ3) for polyprotein domain/glycosylation/MW.
- No PDB REST call (structures cited from paper abstracts, not independently
  surveyed — acceptable for a target where structural data is recent and sparse).

## Multi-glycoprotein viral target from a single polyprotein

CCHFV's M RNA segment encodes a single ~186 kDa polyprotein (UniProt Q8JSZ3)
that host proteases (SKI-1/S1P, furin) cleave into multiple functional
glycoproteins:
- GP38 (~38 kDa, secreted + surface-associated, "viral toxin" — induces
  vascular leak)
- Gn (~37 kDa, structural, locks Gn-Gc in prefusion state)
- Gc (~75 kDa, class II fusion protein, binds LDLR receptor, mediates
  membrane fusion)
- NSm (~15 kDa, non-structural)
- Mucin-like variable region (heavily glycosylated, removed during processing)

This is fundamentally different from single-GP viruses (EBOV, SUDV, LASV)
where one glycoprotein complex is the target. For CCHFV, there are TWO
major antibody target glycoproteins (Gc and GP38) with DIFFERENT mechanisms:
- Anti-Gc antibodies: neutralize virus entry (block LDLR binding / fusion)
- Anti-GP38 antibodies: non-neutralizing but protective (block vascular leak,
  mediate complement)

### Field organization impact

- **Field 1 (target identity)**: Must describe the polyprotein architecture
  and all cleavage products, not just one "GP." UniProt provides the domain
  map (topological domains, glycosylation sites, cleavage evidence). Note
  that Gn and GP38 share distant homology (gene duplication, PMID 31996434).
- **Field 4 (antibody landscape)**: Group antibodies by target glycoprotein
  (Gc-targeting vs GP38-targeting), not by company or phase. The mechanism
  differs by glycoprotein, so the grouping must reflect that.
- **Field 5 (epitope landscape)**: Two separate epitope maps (Gc: 6 antigenic
  sites; GP38: 5 sites / 11 overlapping regions) with different functional
  implications (neutralizing vs protective).
- **Field 6 (failure/success)**: The neutralization-protection dissociation
  is the central organizing principle (see below).

## Neutralization-protection dissociation (field 6 organizing principle)

### The pattern

For CCHFV, neutralizing antibodies (anti-Gc) frequently FAIL to protect,
while non-neutralizing antibodies (anti-GP38) DO protect:

1. Gn/Gc subunit vaccines induced high neutralizing Ab titers but did NOT
   protect STAT1-KO mice from lethal challenge (PMID 26684523).
2. Gc-specific neutralizing antibodies from a human survivor neutralized
   only weakly and did NOT protect against heterologous challenge, while
   non-neutralizing GP38 antibodies DID protect (PMID 41915428).
3. Most individual Gc-neutralizing mAbs protect only prophylactically; only
   the bispecific DVD-121-801 (dual Gc epitope) achieved therapeutic protection
   (PMID 34077751).
4. GP38 antibodies protect via non-neutralizing mechanisms: blocking GP38-
   mediated endothelial barrier dysfunction / vascular leak (PMID 39970234)
   and complement-mediated effector function (PMID 41915428).

### Why this is distinct from the "graveyard" pattern

The graveyard pattern (field 6 as taught in the skill) is about
antibody-specific failures (wrong epitope, wrong format, wrong dosing)
where the target is validated. The CCHFV pattern is different: the STANDARD
EFFICACY PROXY (neutralization) does not predict the clinical endpoint
(protection). The failure is not in the antibody — it's in the assay
paradigm. A neutralizing antibody can be a "success" in vitro and a
"failure" in vivo, while a non-neutralizing antibody is a "failure" in
vitro and a "success" in vivo.

### Generalization

For viral targets where the pathogenesis mechanism extends beyond viral
entry (e.g., viral toxins, immune-mediated damage, vascular leak), field 6
must document:
1. Whether neutralization predicts protection (cite the evidence for AND
   against).
2. The protective mechanism of non-neutralizing antibodies (e.g., toxin
   neutralization, Fc effector function, vascular leak blockade).
3. Which antibody format/epitope achieved therapeutic (post-exposure)
   protection vs only prophylactic.

This applies to CCHFV (GP38 vascular toxin), and potentially to other
viral hemorrhagic fevers where non-structural or secreted glycoproteins
drive pathogenesis independently of entry.

## esummary-first triage for rate-limit mitigation

When surveying 50+ PMIDs from multiple esearch queries:

1. **esearch** (multiple queries, 3-5s sleep between) → collect all unique
   PMIDs (deduped).
2. **esummary** (batch 25 PMIDs per call) → get title, journal, date, first
   author for ALL PMIDs in 2-3 calls. This is the triage step — read the
   title table to identify the 15-20 landmark papers worth full-abstract
   retrieval.
3. **efetch** (selective, 1 PMID per call or small batches) → fetch full
   abstracts only for the landmark papers identified in step 2.

The esummary step costs 2-3 API calls for 50-70 PMIDs. Without it, fetching
all 50-70 abstracts via efetch would cost 50-70 calls (or 2-3 batched calls
of 25, but then you're reading 70 abstracts you don't need). The esummary
triage saves context-window space (title table is compact) and reduces
the number of full-abstract reads.

Rate-limit note: HTTP 429 occurred after ~5 rapid efetch calls even with
3-5s sleeps. After 429, wait 10+s and retry. The esummary-first pattern
reduces total efetch calls from ~70 to ~20, cutting 429 exposure
proportionally.

## Key PMIDs for CCHFV GP

| PMID | Year | Key finding |
|------|------|-------------|
| 34077751 | 2021 | Human neutralizing Abs, 6 Gc sites, DVD-121-801 bispecific (Cell) |
| 39970234 | 2025 | GP38 vascular leak mechanism, GP38 Abs limit leak (Science TM) |
| 39701101 | 2025 | First Gn structure, GP38-Gn-Gc heterotrimer (Cell) |
| 39002130 | 2024 | 188 GP38-specific human Abs, 5 sites/11 regions (Cell Reports) |
| 36435827 | 2022 | 13G8/CC5-17 GP38 protective Ab structures (Nat Commun) |
| 31996434 | 2020 | GP38 crystal structure, novel fold (J Virol) |
| 38300972 | 2024 | Gc fusion-loop neutralizing mAbs Gc8/Gc13 (PLoS Pathog) |
| 28842265 | 2017 | Broadly neutralizing Gc mAbs 8A1/11E7/30F7 (Antiviral Res) |
| 40237506 | 2025 | Optimized bispecific DVD-121-801GS (mBio) |
| 41915428 | 2026 | Human GP38 mAb protects heterologous challenge (JCI) |
| 38182887 | 2024 | LDLR as entry receptor for CCHFV (Cell Research) |
| 35234630 | 2022 | Gc cryo-EM postfusion structure, class II fusion (Virol Sin) |
| 17898072 | 2007 | SKI-1/S1P processing essential for infectivity (J Virol) |
| 15858000 | 2005 | Gn/Gc cellular localization, Golgi targeting (J Virol) |
| 26684523 | 2015 | Neutralizing Abs without protection (Vector Borne Zoonotic Dis) |
| 41352535 | 2025 | VHH-Fc neutralizing Abs targeting Gc fusion loop (Virol Sin) |
| 38815869 | 2024 | Convalescent plasma partial protection in A129 mice (Virus Res) |
