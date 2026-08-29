# Alpha2-antiplasmin (SERPINF2) profile observations

**Date:** 2026-08-17
**Tier:** preclinical (hit list) → recalibrated to clinical-trial (Phase 2 ongoing)
**Area:** cardiovascular
**Profile:** `working-docs/hitlist-profiles/alpha2-antiplasmin.md`
**Size:** ~42.5K chars, 341 lines, ~20 PMIDs cited
**Rigor:** Abstract-level (delegated subagent, lightweight retrieval pipeline)

## Key new patterns

### (1) ClinicalTrials.gov API v2 as a primary source for clinical-stage antibody discovery

PubMed keyword searches for `"alpha2-antiplasmin" antibody[tiab]`, `"SERPINF2 antibody[tiab]`, and `"anti-plasmin" antibody[tiab]` returned academic preclinical antibody papers (RWR, JTPI-1, mAbs 49/70/77) but completely missed **TS23**, the sole clinical-stage anti-α2AP antibody (Phase 1 completed: NCT03001544; Phase 2 ongoing: NCT05408546 / NAIL-IT trial for pulmonary embolism, sponsor: Translational Sciences, Inc.).

TS23 was discovered by querying ClinicalTrials.gov API v2:
```
curl -sL 'https://clinicaltrials.gov/api/v2/studies?query.intr=alpha-2-antiplasmin+antibody&pageSize=10&format=json'
```

This returned 2 studies, including the NAIL-IT Phase 2 trial. The intervention description confirmed "Monoclonal antibody to a2-antiplasmin."

**Rule:** For any cardiovascular/thrombotic target, always query ClinicalTrials.gov API v2 with `query.intr` containing both the target name + "antibody" and just the target name. Clinical-stage antibodies may not be published in PubMed under the target name — they are indexed only in ClinicalTrials.gov under the intervention name. This extends the 5T4/TPBG observation (ClinicalTrials.gov for clinical-trial-tier targets) to ALL tiers: even "preclinical" targets may have undisclosed clinical programs.

### (2) PDB structure lookup via ortholog UniProt cross-references

The human UniProt entry (P08697) for alpha2-antiplasmin had **no PDB cross-references** — `uniProtKBCrossReferences` contained AlphaFoldDB, SMR, and many others but NOT PDB. The crystal structure paper (PMID 18063751, Law et al, 2008 Blood) was known from PubMed, but the PDB ID was not findable via PubMed, Europe PMC, or direct RCSB/PDBe search APIs (all returned 404 errors).

The PDB ID (**2R9Y**, 2.65 A, mouse alpha2AP) was found by:
1. Querying UniProt REST API for the *mouse* ortholog: `rest.uniprot.org/uniprotkb/search?query=SERPINF2+AND+organism_id:10090`
2. Getting the mouse UniProt accession (Q61247, A2AP_MOUSE)
3. Fetching Q61247's cross-references, which DID contain a PDB entry: `PDB: 2R9Y - X-ray, 2.65 A, Chains A=71-491`
4. Verifying via RCSB Data API: `data.rcsb.org/rest/v1/core/entry/2R9Y` confirmed "Structure of antiplasmin"

**Rule:** When the human UniProt entry lacks PDB cross-references but a crystal structure paper exists, query the UniProt REST API for orthologs (mouse: organism_id 10090, rat: 10116) and check their cross-references. Crystal structures are often solved using mouse/other species proteins but the PDB ID is only linked to the species-specific UniProt entry, not the human one. This is especially common for targets where the human protein is difficult to crystallize.

### (3) Tier recalibration via ClinicalTrials.gov — preclinical -> clinical-trial

The target was labeled "preclinical" in the hit list based on PubMed evidence of academic antibody work (RWR, JTPI-1 published 1989-1997, no clinical follow-up in PubMed). Deep profiling via ClinicalTrials.gov revealed that TS23 has been in clinical development since 2015 (Phase 1) and entered Phase 2 in 2023 (NAIL-IT, 64 subjects, completion 2026-11).

This is the most dramatic tier recalibration in the profile corpus: a target with only 1980s-1990s academic publications that was assumed preclinical actually has an active Phase 2 program. The gap exists because:
- TS23's development was done by a small biotech (Translational Sciences, Inc.) that does not publish in PubMed
- The Phase 1 trial (NCT03001544) results were never published in a journal
- The founder (Dr. Guy Reed) moved from academia to industry, shifting from publishable preclinical work to non-published clinical development

**Rule:** For any "preclinical" cardiovascular or thrombotic target, run a ClinicalTrials.gov query before assigning the tier. If a Phase 1+ trial exists for an antibody against the target, recalibrate to clinical-trial. The absence of PubMed publications does not mean absence of clinical development — small biotechs do not publish clinical results in PubMed. This is a systematic bias in PubMed-only tier assignment.

### (4) Unique thrombus-specificity safety profile — alpha2AP inactivation without bleeding

The alpha2AP profile documents the strongest preclinical safety advantage observed in the cardiovascular profile corpus: alpha2AP inactivation dissolves thrombi *without* fibrinogen degradation or bleeding, unlike all plasminogen activators (tPA, urokinase, streptokinase). In pulmonary embolism models, alpha2AP inactivation alone was comparable to 3 mg/kg r-tPA but caused *less* bleeding than clinical-dose r-tPA (P<0.001). This is a mechanistic consequence: alpha2AP inhibition allows plasmin to act on fibrin (clot-specific) without generating systemic plasmin that degrades circulating fibrinogen.

**Rule:** For fibrinolytic system targets (alpha2AP, PAI-1, TAFI), field 8 (safety) must explicitly compare the bleeding profile to plasminogen activators. The key differentiator for fibrinolysis inhibitors vs. plasminogen activators is *thrombus specificity* — does the intervention cause systemic fibrinogen degradation? This is the primary safety axis, not the traditional "on-target vs off-target" framing.

### (5) Context-specific on-target toxicity — pulmonary heart failure in AMI

Complete alpha2AP deficiency in mice with experimental AMI caused acute cor pulmonale (right ventricular overload) via VEGF overrelease and increased pulmonary vascular permeability, leading to markedly increased mortality (PMID 12239160). Anti-VEGF antibody rescued mortality. This is NOT a generic bleeding risk — it is a disease-context-specific on-target toxicity that would not be detected in standard toxicology studies (which do not include AMI models).

**Rule:** For fibrinolytic targets, field 8 must include disease-context-specific toxicities beyond standard bleeding risk. The alpha2AP-AMI interaction (unopposed plasmin -> VEGF cleavage -> pulmonary edema -> cor pulmonale) is a mechanism that requires the concurrent disease state (AMI) to manifest. The NAIL-IT trial explicitly excludes AMI patients. Always check for disease-context-specific safety signals in knockout/deficiency models, not just standard pharmacology studies.

### (6) PubMed search strategy for targets with multiple historical names

Alpha2-antiplasmin has at least 4 names used in the literature: "alpha2-antiplasmin", "alpha-2-antiplasmin", "alpha2-plasmin inhibitor", and "SERPINF2". PubMed searches needed all variants:
- `"alpha2-antiplasmin" antibody[tiab]` — 26 results
- `"alpha-2-antiplasmin" antibody[tiab]` — 112 results (highest yield, hyphenated form)
- `SERPINF2 antibody[tiab]` — 2 results (gene symbol rarely used in older papers)
- `"anti-plasmin" antibody[tiab]` — 7 results

The highest-yield query used the hyphenated form ("alpha-2-antiplasmin"), which captured the 1980s-1990s landmark papers. The modern form without hyphens ("alpha2-antiplasmin") captured recent papers. Both forms must be searched.

**Rule:** For targets with historical name variants (especially older targets discovered pre-2000), run PubMed searches with all known name variants including hyphenated and non-hyphenated forms, old synonyms, and gene symbols. Older papers use older nomenclature; newer papers use current nomenclature. Missing any variant can miss landmark papers.

## Technical notes

- PubMed 429 rate limits occurred after ~5-6 rapid esearch calls. Waiting 20-30s resolved the issue. The 3-5s sleep between calls was sometimes insufficient.
- Europe PMC search API (`ebi.ac.uk/europepmc/webservices/rest/search`) successfully provided `hasDbCrossReferences` flag indicating PDB cross-references exist, but did not expose the actual PDB IDs via the lite result format.
- UniProt REST API JSON format (`rest.uniprot.org/uniprotkb/<accession>.json`) provides `uniProtKBCrossReferences` array with database names and IDs — efficient for PDB lookup without parsing flat-text.
- RCSB search API (`search.rcsb.org/rcsb_search/v1/query`) consistently returned 404 errors across multiple URL formats and query structures. The RCSB Data API (`data.rcsb.org/rest/v1/core/entry/<PDB_ID>`) works reliably for individual PDB entry lookup once the ID is known.
