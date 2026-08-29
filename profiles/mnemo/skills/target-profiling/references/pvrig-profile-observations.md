# PVRIG (CD112R) Profile Observations

**Profile**: working-docs/hitlist-profiles/pvrig.md
**Tier**: Clinical-trial
**Therapeutic area**: Oncology (immune checkpoint)
**Date**: 2026-08-16
**Papers ingested**: 6 (PMID 26755705, 30659054, 34174928, 33903974, 38554184, 38626767)
**Profile size**: ~38K chars, 10 unique PMIDs cited
**Full-text retrieval**: 4/6 PMC XML OA (J Exp Med, Cancer Immunol Res, J Hematol Oncol, Cancer Immunol Immunother); 1/6 jina reader on Cell Press/Structure journal (94K chars); 1/6 abstract-only (Cancer Discovery news note, no PMCID)

## Paper retrieval details

| PMID | Journal | Full text? | Method |
|------|---------|-----------|--------|
| 26755705 | J Exp Med (2016) | Yes (36K chars) | PMC XML OA (PMC4749091) |
| 30659054 | Cancer Immunol Res (2019) | Yes (34K chars) | PMC XML OA (PMC7001734) |
| 34174928 | J Hematol Oncol (2021) | Yes (52K chars) | PMC XML OA (PMC8236157) |
| 33903974 | Cancer Immunol Immunother (2021) | Yes (58K chars) | EPMC PDF (PMC10992303) |
| 38554184 | — | — | — |
| 38626767 | Structure (2024) | Yes (94K chars) | jina reader on direct fulltext URL |

Note: A separate subagent session ingested 5 papers (26755705, 30659054, 34174928, 33903974, 39851063) with 4/5 full text. PMID 39851063 (Mol Cancer Ther 2025, bispecific TIGIT/PVRIG) was blocked by AACR/Cloudflare CAPTCHA — abstract-only is the expected outcome for AACR journals.

## Key new patterns

### 1. Nectin-family checkpoint profiling: nonredundancy is the key differentiator from TIGIT

PVRIG and TIGIT are in the same nectin/nectin-like receptor family but bind different ligands: PVRIG binds CD112 (PVRL2/nectin-2, Kd ~88 nM), TIGIT binds CD155 (PVR). They are **nonoverlapping, nonredundant inhibitory pathways** — dual blockade is additive/synergistic (PMID 30659054). For field 2 (biological mechanism) and field 11 (differentiation), explicitly state the nonredundancy: PVRIG is NOT "another TIGIT" — it governs a distinct ligand axis. The PVR:PVRL2 expression ratio varies by cancer type (breast/ovarian/prostate/endometrial enriched in PVRL2; melanoma/esophageal/colorectal enriched in PVR), providing a biomarker framework for patient selection (PMID 30659054). Generalizable to any multi-receptor checkpoint family where receptors share a costimulatory partner (CD226/DNAM-1) but bind different ligands.

### 2. NK cell as primary effector — distinct from T cell-focused checkpoints

Unlike PD-1 and TIGIT (primarily T cell checkpoints), PVRIG has a dominant NK cell effector mechanism. PVRIG+ tumor-infiltrating NK cells are exhausted (high CD96, TIGIT, Tim-3, PD-1, NKG2A); PVRIG blockade restores cytotoxicity and IFNγ production (PMID 34174928). NK cells are activated first (after 1st dose), with T cell activation following (after 2nd dose) via NK cell-derived cytokines (PMID 38554184). For field 2 (cell types expressing) and field 6 (success factors), identify the primary effector cell — NK vs T cell dominance has implications for Fc format selection, in vivo model choice, and biomarker strategy. Generalizable: for checkpoint receptors expressed on both T and NK cells, determine which effector dominates in vivo, not just which expresses the target.

### 3. Fc format debate (IgG4 vs IgG1) — same question as TIGIT, NK cell biology provides the answer

COM701 (Compugen, IgG4, weak Fc) is the most advanced clinical anti-PVRIG; IBI352g4a (Innovent, IgG1, full Fc) and SRF813 (Surface Oncology, IgG1) are alternatives. Preclinical data shows Fc-competent IgG1 is superior because it engages Fcγ receptors on myeloid cells, providing additional immune stimulation beyond ligand blockade — and NK cells (the primary effector) benefit from Fc-mediated myeloid activation (PMID 38554184). For field 4 (antibody landscape), always note the isotype AND the Fc format rationale. For field 6 (failure modes), the Fc format is unresolved — if COM701 (IgG4) fails, it may be format, not target. Generalizable: for NK cell-dominant checkpoint targets, the Fc-competent IgG1 format may be superior because NK cell activation benefits from myeloid FcγR engagement, unlike T cell-dominant checkpoints where Fc-active antibodies risk depleting exhausted T cells.

### 4. Structural uniqueness of the CC' loop as epitope differentiation target

The PVRIG/Nectin-2 crystal structure (PMID 38626767) revealed a unique CC' loop (residues N81, G82, A83) that adopts an upward conformation absent in TIGIT, CD96, and DNAM-1. This CC' loop provides high-affinity binding via a "double-lock-and-key" mode and determines ligand selectivity (Nectin-2 vs Necl-5/CD155). For field 5 (epitope landscape) and field 11 (differentiation), a target-specific structural feature like the CC' loop is a potential epitope differentiation target — an antibody specifically targeting the CC' loop could have a distinct mechanism. Generalizable: when a crystal structure reveals a target-specific structural feature absent in related family members, flag it as a potential epitope differentiation opportunity in field 11.

### 5. PVRIG low on Tregs — unlike TIGIT

TIGIT is highly expressed on Tregs, enabling Treg depletion with Fc-active antibodies. PVRIG is expressed at low levels on Tregs (PMID 38554184). This means anti-PVRIG cannot deplete Tregs via Fc-mediated mechanisms — the therapeutic effect is purely checkpoint blockade, not Treg modulation. For field 6 (failure modes) and field 11 (differentiation), note whether the target is expressed on Tregs and whether Treg depletion is a viable mechanism. This is a key difference between PVRIG and TIGIT that affects Fc format strategy.

### 6. Rapid internalization as a target accessibility limitation

PVRIG rapidly internalizes from the cell surface in the absence of TCR signaling (PMID 30659054) — a regulatory mechanism analogous to CTLA-4. For field 9 (structural information) and field 6 (failure modes), rapid internalization may limit antibody binding and efficacy in vivo, particularly for Fc-dependent mechanisms requiring sustained surface engagement. Generalizable: for checkpoint receptors with regulated surface expression (PVRIG, CTLA-4), note the internalization kinetics and consider whether an antibody that stabilizes surface expression would be differentiated.

### 7. Cell Press/Structure journal is jina-recoverable

The PVRIG/Nectin-2 crystal structure paper (PMID 38626767, Structure journal, Cell Press/Elsevier) was retrieved via jina reader proxy on the direct fulltext URL (`r.jina.ai/https://www.cell.com/structure/fulltext/<PII>`) — 94,284 chars of complete body text. The PII was obtained from PubMed `elink.fcgi?cmd=prlinks`. This contradicts the paper-ingest skill's previous "Cloudflare interstitial" entry for Cell Press — jina reader works on the direct fulltext URL. Updated the paper-ingest known-blocks table. For target profiling, this means Cell Press structural papers (Structure, Cell, Immunity, etc.) are retrievable via jina, making them high-value full-text sources for field 5 (epitope landscape) and field 9 (structural information).

### 8. AACR/Cloudflare CAPTCHA block on 2025 Mol Cancer Ther paper

PMID 39851063 (Mol Cancer Ther 2025, bispecific TIGIT/PVRIG antibody) was blocked by AACR/Cloudflare CAPTCHA — jina reader returned "Just a moment... Performing security verification" (480 chars). No PMC copy (inPMC=N, isOpenAccess=N). Abstract was retrieved from PubMed efetch XML and saved as the text file. This confirms the AACR hard publisher block already documented in the paper-ingest known-blocks table and the CCL2/MCP-1 profile observations. Abstract-only is the expected outcome for AACR journals.

### 9. UniProt REST API as standard initial data gathering for field 1

UniProt Q6DKI7 (PVRIG) provided via the REST API: 326 aa, 34,344 Da, cell membrane localization, single-pass type I transmembrane, IgV extracellular domain with PVR signature motifs, ITIM-like motif at Y233, disordered C-terminal region (296-326). Tissue specificity confirmed from UniProt: expressed on NK cells (both CD16+ and CD16−), CD8+ T cells (memory/effector), not on B cells, naive T cells, monocytes, neutrophils, or DCs. This confirms the UniProt API as the standard first call for field 1 (target identity) — provides protein name, gene, accession, mass, domains, features, tissue specificity, and function in a single JSON response.

## Nectin/nectin-like receptor checkpoint family context

The nectin checkpoint family is a multi-receptor system sharing ligands CD155 (PVR) and CD112 (PVRL2/nectin-2):

| Receptor | Type | Primary ligand | Affinity | Function |
|---------|------|---------------|---------|----------|
| CD226 (DNAM-1) | Costimulatory | CD155, CD112 | Low (µM) | Activates T and NK cells |
| TIGIT | Coinhibitory | CD155 (PVR) | High (nM) | Inhibits T and NK cells |
| PVRIG (CD112R) | Coinhibitory | CD112 (PVRL2) | High (88 nM) | Dominant receptor for CD112 |
| CD96 (TACTILE) | Coinhibitory (mouse) / Costimulatory (human NK) | CD155 (PVR) | Moderate | Inhibits mouse NK; costimulates human NK |

Key differences between PVRIG and TIGIT:
1. Ligand specificity (PVRIG→CD112, TIGIT→CD155)
2. Nonredundant signaling (dual blockade is synergistic)
3. Expression kinetics (TIGIT peaks day 3, PVRIG peaks day 11)
4. Internalization (PVRIG rapid >50% in 60-120 min, TIGIT surface-stable)
5. Exhaustion correlation (PVRIG correlates with Eomes+T-bet− exhausted phenotype)
6. Compensatory regulation (PVRIG blockade induces TIGIT, not vice versa)
7. NK cell prominence (PVRIG higher on NK cells than T cells)
