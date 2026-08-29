---
name: target-profiling
description: Target profiles for antibody discovery prioritization.
triggers:
  - "target profile"
  - "profile targets"
  - "build target profiles"
  - "comprehensive target profile"
  - "antibody target profiling"
---

# target-profiling — comprehensive target profiles for antibody discovery

After the hit list (`target-hitlist`) enumerates targets with a binary bar,
profiling builds a **durable, reusable record** per target. The profile is
fact-heavy and judgment-free — scoring is applied separately, querying the
profiles with different weights for different use cases (platform
demonstration, real discovery pipeline, grant targeting).

The output is a working doc at `working-docs/hitlist-profiles/<target-slug>.md`
— NOT a brain page. No frontmatter, no indexing, no wikilinks. Profiles are
the draft; high-value targets may later be promoted to brain pages (concept
or project).

## The profile template (11 fields)

See `templates/profile-template.md` for the full template. The fields:

1. **Target identity** — name, gene symbol, UniProt ID, family, localization,
   MW, oligomerization, key domains
2. **Biological mechanism** — function, pathway, effect of blockade/activation,
   cell types, downstream signaling, physiological role, species cross-reactivity
3. **Disease evidence** — per disease: evidence type, summary, PMIDs
4. **Antibody landscape** — per antibody: INN, company, format, isotype,
   phase, indication, outcome, epitope info, reference
5. **Epitope landscape** — mapped epitopes, structural data (PDB IDs),
   neutralizing vs non-neutralizing, conformational states, immunodominant
   regions, competing epitope bins
6. **Known failure modes and success factors** — what made winners succeed,
   what made losers fail (epitope, population, safety, format, dosing, trial
   design), with references
7. **Assay systems** — functional assays, in vivo models, key readouts,
   biomarker assays, available cell lines
8. **Safety profile** — toxicities, mechanism, organ-specific, managed vs
   unmanaged, therapeutic index, black box warnings, clinical safety data
9. **Structural information** — PDB structures, glycosylation, conformational
   states, epitope accessibility, membrane-proximal regions, oligomerization
10. **Competitive landscape** — pipeline depth, companies, patents, market
    size, gaps
11. **Differentiation opportunities** — JUDGMENT FIELD (clearly marked):
    format, epitope, population, mechanism differentiation + known risks

Fields 1-10 are facts (cite PMIDs). Field 11 is judgment — the only opinion
field. Different prioritization runs weight the facts differently.

## The workflow

### Phase 0: Lightweight triage (optional but recommended)

Before profiling all ~900 targets, cut to the ones worth a deep profile.
A 30-second gate: "Is there at least one strong line of biological evidence
AND is the target antibody-accessible?" Use the hit list evidence type +
PubMed hit count. This cuts 900 to ~400-500 for first-pass profiling.
Marginal targets are sequenced later, not removed.

### Phase 1: Pilot (5-10 profiles, done directly)

**Always start with a pilot.** Build 5 profiles directly — one per tier
(approved, clinical-trial, failed-clinical, preclinical, and one more for
diversity). This validates the template across the full information density
range before scaling.

The pilot serves three purposes simultaneously (design it for all three):
1. **Template test** — which fields are empty, where, how often? Does the
   template break for blue ocean targets?
2. **Workflow test** — how long does each profile take? Is delegation feasible?
3. **Tier calibration** — do the profiles confirm or challenge the tier
   assignments from the hit list?

Do NOT pre-register pass/fail criteria for the pilot. Observe what happens
and adjust from observation.

### Phase 2: Scale (delegated batches)

Once the template is validated, delegate remaining profiles to subagents
following `skills/batch-drain/SKILL.md` (dispatch → yield → verify-on-disk →
commit → next batch). Batch 3-5 targets; the remainder is a single-task call,
never dropped. **Yield and wait between batches** — do not dispatch the next
batch while the prior is in flight. Each subagent gets:
- The target name
- The profile template
- Instructions to search PubMed for key literature and fill all 11 fields
- The convention: "Unknown" or "No data" for empty fields (do not speculate)

The orchestrator verifies each batch on return — read the profiles back, check
for completeness, fill gaps the subagent missed — using the filesystem, not the
subagent's self-report. This is the paper-ingest queue-drain pattern applied to
target profiling, governed by the `batch-drain` loop.

### Phase 3: Pilot assessment

After the pilot (or after each batch), review:
- Which fields were consistently empty? For which tiers?
- Did the template handle the full range (saturated to blue ocean)?
- Did the tiering hold up, or did profiles reveal misassignment?
- How long did each profile take? Is the delegation batch size right?

## Empirical observations from the pilot (2026-08-15)

From 5 profiles across immunology/inflammation (TNF, TL1A, CD147, IL-11,
Siglec-8):

- **Fields 1-3 are always full.** Target identity, biological mechanism,
  and disease evidence can be filled from literature for any target that
  clears the binary bar.
- **Fields 4-6 (antibody landscape, epitope, failure modes) show the most
  tier-dependent variation.** Saturated targets have rich data; blue ocean
  targets have almost none. The template handles this — "Unknown" is valid.
- **Field 5 (epitope landscape) is almost always empty for non-saturated
  targets.** Only approved targets with multiple antibodies had published
  epitope mapping. This is the gap an in silico discovery pipeline fills.
  **Exception — single-dominant-antibody approved targets** (e.g.,
  dupilumab/IL-4Rα, >$10B blockbuster): even with one approved antibody
  and no competitors, the epitope landscape is completely unexplored in
  the public domain — no published antibody-target crystal structure,
  no epitope binning, no competing antibodies. The competitive pressure
  that drives epitope publication comes from *multiple companies racing*,
  not from approval status or sales volume. A single-antibody monopoly
  has no incentive to publish epitope data. (IL-4Rα profile, 2026-08-15.)
- **Field 6 (failure/success modes) is the most valuable field for platform
  demonstration.** For saturated targets, it captures ground truth (known
  winners and losers). For graveyard targets, it captures the specific
  failure analysis. For blue ocean, it captures theoretical risks.
- **Field 8 (safety) is the most variable.** Approved targets have decades
  of data; blue ocean targets have zero clinical exposure.
- **Blue ocean profiles don't break the template.** Fields 4-6 are thin but
  mechanistic biology (fields 2-3) carries the weight. This was predicted
  and confirmed.
- **Tier calibration is approximate.** Siglec-8 (clinical-trial) has a
  Phase 3 failure — closer to graveyard than expected. CD147
  (failed-clinical) has an approved product in China — partially validated.
  The tiers are starting points, not absolutes.

## Empirical observations from key-paper-ingestion profiles (2026-08-15)

From the Complement C5 profile (saturated/approved tier, immunology):

- **Full-text retrieval is the main bottleneck at level 2.** Of 5 landmark
  papers, only 1 (20%) had accessible full text via PMC XML — a Sci Rep OA
  article. The other 4 (2× NEJM, 1× J Immunol, 1× Blood) were paywalled with
  no PMC copy or publisher-restricted XML. Abstract-only distillation was
  the outcome for 80% of papers, making `needs-enrichment: true` the norm
  rather than the exception for level-2 profiles in this therapeutic area.
- **Rich EPMC abstracts compensate for missing full text.** Europe PMC
  core records carry structured abstracts (Background/Methods/Results/
  Conclusions) that are 1,000–2,500 characters — sufficient for distilling
  key findings, trial design, and safety data. The abstract alone yielded
  enough to fill fields 2, 3, 6, and 8 at a level adequate for
  prioritization decisions.
- **Epitope bins emerge from structural papers.** The C5–eculizumab crystal
  structure (PMID 27194791) and the SKY59/crovalimab crystal structure (PMID
  28439081) together revealed two distinct epitope bins (MG7 vs MG1 domains)
  — the single most important fact for field 5 (epitope landscape) and field
  6 (resistance mechanism). Structural papers are the highest-value papers
  to prioritize for full-text retrieval when only 3-5 can be ingested.
- **Cross-referencing between paper pages strengthens the profile.** Linking
  paper pages to each other (eculizumab structural paper → crovalimab
  preclinical paper → eculizumab PNH trial) creates a citation trail that
  makes the profile's claims auditable. Always link the ingested papers to
  each other in the `links:` frontmatter, not just to the profile.
- **Publisher blocks hit level-2 profiling hard.** The ASH Publications
  (Blood) block — `inPMC: Y` but publisher restricts XML body download, EPMC
  PDF render returns "No PDF file found", jina blocked by Cloudflare — is
  particularly painful because the PMC ID exists (suggesting full text should
  be available) but all retrieval paths fail. Added to the paper-ingest
  known-blocks table. **Correction (2026-08-16):** EPMC PDF Branch 1b CAN
  succeed for some Blood papers even when `hasPDF=N`. The CXCL7 profile
  retrieved PMID 23550035 (Ghasemzadeh 2013, Blood) via EPMC PDF — 58K chars
  extracted despite `inPMC=Y, isOpenAccess=N, hasPDF=N`. The `hasPDF` flag
  in the EPMC gate is unreliable; always try Branch 1b when `inPMC=Y`
  regardless of `hasPDF`. The Blood block is not universal — it is
  paper-specific, not journal-specific.
- **Full-text retrieval rate varies dramatically by journal mix.** The C5
  profile hit 20% (1/5 papers accessible); the IL-17A profile (same tier,
  same therapeutic area) hit 100% (5/5). The difference: IL-17A's landmark
  papers were in OA-friendly journals (Front Immunol, Nat Rev Immunol,
  Immunity — all PMC OA) plus 2 NEJM papers recovered via the Wayback
  direct-HTML technique documented in paper-ingest. When pre-identifying
  landmark papers for delegation, prefer papers from OA journals or NEJM
  (Wayback-recoverable) over publishers with hard blocks (ASH/Blood,
  ScienceDirect, Wiley, Karger). (IL-17A profile, 2026-08-15.)
- **The preclinical antibody characterization paper is the highest-value
  single paper.** In the IL-17A profile, the bimekizumab preclinical paper
  (PMID 32973785, Front Immunol) provided antibody structure/epitope data
  (crystal structure-guided affinity maturation, KD values, cross-reactivity
  profile, format/isotype) that filled fields 4, 5, and 6 most richly —
  confirming the C5 observation that "structural papers are the highest-value
  papers to prioritize for full-text retrieval." For antibody-target profiles,
  the preclinical characterization paper of the lead antibody is the
  equivalent of the structural paper for complement targets. (IL-17A profile,
  2026-08-15.)
- **Cross-validation of safety signals across evidence types strengthens
  field 8.** The IL-17A Candida infection signal appeared in: (a) Phase 3
  psoriasis trial data (PMID 25007392: 2.3–4.7% incidence), (b) Phase 3 AS
  trial data (PMID 26699169: 0.9/100 patient-years), (c) human genetics
  reviews (PMID 25145755, 30995505: IL17RA/IL17RC/ACT1/IL17F deficiency →
  CMC). Citing the same safety signal with multiple PMIDs across different
  evidence types (clinical trial + human genetics + review) makes field 8
  entries more authoritative and is the natural output of key-paper
  ingestion when the paper set spans reviews + trials + preclinical.
  (IL-17A profile, 2026-08-15.)
- **Delegation with search instructions (not pre-identified PMIDs) works.**
  The IL-17A task provided PubMed search query templates and topic areas
  rather than specific PMIDs. The subagent ran 10+ esearch queries, batched
  esummary calls, and selected 5 landmark papers spanning all required
  topics (biology review, antibody structure/epitope, clinical psoriasis,
  clinical AS, safety/genetics). This validates a lighter delegation
  pattern: the orchestrator provides search instructions and topic coverage
  requirements; the subagent identifies and selects the specific papers.
  This is more scalable than pre-identifying PMIDs for every target.
  (IL-17A profile, 2026-08-15.)

## Empirical observations from infectious disease toxin-target profiling (2026-08-17)

From the P. aeruginosa exotoxin A (PEA) profile (preclinical tier,
infectious disease):

- **Toxin targets generate massive immunotoxin-payload search noise.**
  When searching PubMed for antibodies AGAINST a bacterial toxin as a
  therapeutic target, ~70% of hits are papers using that toxin as a PAYLOAD
  in immunotoxin conjugates for cancer (e.g., moxetumomab pasudotox,
  IL13-PE, cintredekin besudotox — all use PEA as the cytotoxic moiety,
  not as the neutralization target). This is the single biggest PubMed
  noise source for bacterial toxin targets. Mitigation: add filter terms
  (`AND (neutralizing OR "passive immunization" OR "anti-toxin" OR
  infection[tiab])`) and exclude payload terms (`AND NOT (immunotoxin OR
  fusion OR payload)[tiab]`). Also search for `AND "passive immunization"[tiab]`
  and `AND vaccine[tiab]` separately — these queries surface the
  anti-infective antibody literature that the broad `AND antibody[tiab]`
  query drowns out. (PEA profile, 2026-08-17.)
- **UniProt REST API and RCSB PDB REST API are high-value for fields 1
  and 9.** UniProt (`rest.uniprot.org/uniprotkb/{id}.json`) provides
  canonical name, gene symbol, MW, sequence length, domain annotations
  (with exact residue ranges), active-site residues, catalytic activity
  description, and subcellular localization — filling most of field 1 and
  part of field 2 in a single API call. RCSB PDB
  (`data.rcsb.org/rest/v1/core/entry/{id}`) provides structure title,
  method, and resolution for field 9. For the PEA profile, UniProt P11439
  gave domain boundaries (Ia: 26–277, II: 278–389, Ib: 390–429, III:
  430–638), the catalytic residue (His-440), and the catalytic mechanism
  (NAD-dependent ADP-ribosylation of eEF-2 diphthamide) — more precise
  than any single paper. Always fetch UniProt early; it anchors the
  target identity field with authoritative annotations. (PEA profile,
  2026-08-17.)
- **Exact-phrase [tiab] queries return 0 results for multi-word target
  names.** `"Pseudomonas aeruginosa exotoxin A antibody"[tiab]` returns
  0 — the exact phrase never appears verbatim in any title/abstract.
  Breaking into AND-style queries (`Pseudomonas aeruginosa exotoxin A[tiab]
  AND antibody[tiab]`) returns 78+ hits. Always use AND-style queries for
  multi-word target names. (PEA profile, 2026-08-17.)
- **efetch XML must be parsed with ElementTree, not regex.** Greedy
  regex matching across `<PubmedArticle>` boundaries returns the first
  article's data for ALL PMIDs in a batch. `xml.etree.ElementTree` correctly
  parses each article. See `target-hitlist/references/api-templates.md`
  for the full code pattern. (PEA profile, 2026-08-17.)
- **Secreted toxins have no membrane-proximal or glycan-shielding
  complexity.** Fields 9 (structural) and 5 (epitope) are simpler for
  secreted bacterial toxins than for viral glycoproteins: no glycosylation,
  no conformational states from membrane anchoring, fully solvent-exposed
  epitopes. The PEA profile's field 9 was straightforward — the 1IKQ
  crystal structure and domain annotations from UniProt sufficed.
  However, NO antibody–toxin complex structures were in the PDB, so
  field 5 epitope data came entirely from functional mapping (peptide
  scanning, domain-targeted mAb characterization) rather than
  structural epitope determination. This is typical for preclinical
  infectious disease toxin targets. (PEA profile, 2026-08-17.)
- **Multi-mechanism neutralization is a feature of toxin targets.** PEA
  can be neutralized at three distinct steps (receptor binding, translocation,
  enzymatic activity), each corresponding to a different domain and a
  different epitope bin. This is richer than most host-protein targets
  where blockade is the only mechanism. For toxin target profiles,
  field 5 (epitope landscape) should explicitly classify epitopes by
  neutralization mechanism (receptor-blocking vs translocation-blocking
  vs enzyme-blocking), not just by domain location. (PEA profile,
  2026-08-17.)

## Platform demonstration: saturated targets first

When the purpose is demonstrating an in silico antibody discovery pipeline:
- **Saturated targets are the right starting point.** Ground truth exists —
  known antibodies that succeeded AND failed. The pipeline can be tested
  retrospectively: "would our platform have unearthed things that would have
  been winners if they'd been first across the finish line?" This is the
  scenario you'd be in when you later pivot to graveyard or blue ocean targets.
- **The graveyard is NOT ideal for platform demo.** Failed antibodies
  provide benchmarks, but a novel antibody that addresses the failure mode
  cannot be validated without a full preclinical workup — entirely unfeasible
  for a pipeline demonstration. The graveyard is the next step AFTER the
  pipeline is proven on saturated targets, where you know what succeeds AND
  what fails.
- **Blue ocean targets are the end goal, not the starting point.** No
  ground truth to validate against. Move here after the pipeline is proven
  on saturated targets.

## Sequencing for the full profiling campaign

Profile in tiers of decreasing information density:
1. **Graveyard (failed-clinical)** — highest information density (known
   antibodies, known failures, mapped epitopes). Fastest to profile.
2. **Saturated (approved, 5+ antibodies)** — for platform demonstration.
   Well-characterized epitope landscapes, known benchmarks.
3. **Clinical-trial (1-4 antibodies)** — moderate information. Real
   discovery pipeline candidates.
4. **Blue ocean (preclinical)** — deepest work. Mechanistic biology is
   the only evidence; the profile builds the case from scratch. Most
   valuable because these profiles don't exist anywhere else.

## Profile rigor levels

Profiles can be built at three levels of rigor. The level determines how
much literature is ingested and how deeply the mechanistic biology is grounded:

1. **Abstract-level synthesis** — PubMed abstract searches + domain knowledge.
   Fast (~15 min per target) but mechanistic detail is shallow. Fields cite
   PMIDs but content is from abstracts, not full text. Suitable for initial
   pilot template testing only.

2. **Key paper ingestion** — Ingest 3-5 landmark papers per target (the
   review plus 2-3 primary papers) into the brain as paper pages via
   `paper-ingest`, then build the profile from the full-text content. Slower
   (~45-60 min per target) but mechanistic biology in fields 2, 3, and 6 is
   grounded in full-text reading. This is the **recommended minimum rigor**
   for profiles that will be used for prioritization decisions.

3. **Full literature dive** — The `literature-dive` methodology applied to
   each target. Very slow (~2-4 hours per target) but comprehensive. Use
   for the final shortlist of targets under active investigation.

**The level-2 correction (2026-08-15):** The initial 5 pilot profiles were
built at level 1 (abstract-level). Bryan identified that the mechanistic
biology was not grounded in full-text reading — the profiles cited PMIDs
but the content came from abstracts. Level 2 (key paper ingestion) was
established as the minimum rigor for usable profiles. The 5 pilot profiles
were reprocessed at level 2, with 3-5 landmark papers ingested per target
and the profiles rewritten grounding fields 2, 3, and 6 in the full-text
content.

## Stratified random sampling for the pilot

When piloting the profile template, use a **stratified random sample** from
one therapeutic area (not the whole corpus) to test all tiers simultaneously:

- Select one therapeutic area (e.g., immunology/inflammation, the area with
  the most targets and diversity)
- Sample across all four tiers: 5 approved, 5 clinical-trial, all
  failed-clinical (there may be only 4), 6 preclinical = ~20 targets
- Draw across target types (cytokines, receptors, complement, chemokines,
  surface markers) for diversity
- The pilot tests the template, the workflow, and the tiering in one
  controlled experiment
- After the pilot, observe which fields were empty, where, and how often;
  whether the template handled the full range; and whether the tiering
  held up — then adjust from observation, not pre-registered criteria

This approach also allows reassessment of the hit list tiers after deep
profiling — profiles may reveal that a blue ocean target has stronger
biology than a saturated target, challenging the tier assignments.

## Delegation for profiling at key-paper-ingestion level

When delegating profile building at level 2 (key paper ingestion):
- Each subagent receives: the target name, gene symbol, tier, profile
  template path, and 3-5 landmark PMIDs (pre-identified by the orchestrator)
- The subagent: (1) ingests the papers via `paper-ingest`, (2) reads the
  full-text content, (3) writes the profile grounding fields 2, 3, and 6
  in the ingested content, (4) returns the profile path and paper list
- **Subagent environment caveat (2026-08-17, updated 2026-08-17; urllib
  correction 2026-08-17):** Delegated subagents running in a separate
  workspace context may NOT have access to
  `skills/atticus/paper-ingest/scripts/` — the directory may not exist in
  their workspace. Subagents should use the lightweight retrieval pipeline
  (see `references/lightweight-subagent-retrieval.md`) with direct PubMed
  E-utilities calls via `execute_code`. **Default to `urllib.request` for
  the HTTP call** — it is simpler (one call, no subprocess) and works in
  the majority of subagent `execute_code` contexts. A 2026-08-17 session
  (B. anthracis EF profile) used `urllib.request.urlopen` for 8+ PubMed
  E-utilities + UniProt REST calls with zero DNS errors, confirming the
  earlier "urllib always fails in subagents" claim was environment-specific,
  not universal. **Only fall back to `curl` via `subprocess.run` if
  `urllib.request` raises a DNS/socket error** (`nodename nor servname
  provided`, `gaierror`, `URLError`) in your specific sandbox — then use
  the two-step form: build the URL string with `urllib.parse.urlencode`
  (use only its encoder, not its opener), then
  `subprocess.run(["curl", "-sS", "--max-time", "30", url],
  capture_output=True, text=True)` and `json.loads(out.stdout)`. Do not
  assume the paper-ingest scripts are available. The subagent prompt need
  not force curl-only; say "use direct PubMed E-utilities API via
  urllib (or curl via subprocess if urllib hits a DNS error)."
- **Search-query recall for biology-first / preclinical targets
  (2026-08-17):** Narrow title-field-restricted queries like
  `"FABP4 antibody"[tiab]` or `"FABP4 therapeutic"[tiab]` frequently return
  ZERO hits for targets whose therapeutic antibody literature is thin or
  academic — the antibody papers exist but do not put those exact
  phrases in the title/abstract. Do not conclude "no literature" from an
  empty `[tiab]` result. Broaden the query set to maximize recall:
  (1) pioneer/author names (e.g., `Furuhashi FABP4`, `Hotamisligil aP2`,
  `Makowski aP2 atherosclerosis`), (2) tool-compound / inhibitor names
  (e.g., `BMS309403`, `andrographolide FABP4`), (3) gene + disease
  combos without `[tiab]` restriction (`"FABP4" biomarker cardiovascular`,
  `"FABP4" atherosclerosis`, `"FABP4" diabetes`), (4) alternate names
  the target goes by (`aP2`, `A-FABP`, `adipocyte fatty acid binding
  protein`). Run 8-12+ distinct queries; dedupe PMIDs; sleep 3-5s
  between E-utilities calls to respect the ~3 req/min rate limit (a
  rate-limit `{"error":"API rate limit exceeded"}` response is
  recoverable — back off 4-5s and continue). The landmark biology and
  antibody papers for preclinical targets almost always surface with
  this broader net even when the literal `"GENE antibody"[tiab]` is empty.
- **PubMed `[tiab]` quoted-phrase vs AND-joined syntax (2026-08-17):**
  When appending `[tiab]` to a multi-word term, quoting the phrase
  changes the semantics. `"Zika envelope protein antibody"[tiab]`
  (quoted) is an **exact phrase** search in title/abstract — returns
  0 unless that literal string appears. `Zika envelope protein
  antibody[tiab]` (unquoted) is treated as **AND-joined** terms
  restricted to `[tiab]` — returns all papers where each word appears
  in title/abstract. For Zika E protein: the quoted form returned 0
  for all three initial query variants; the unquoted AND-joined form
  returned 2–214 results depending on the term combination. **Default
  to unquoted AND-joined terms with `[tiab]`** for recall. Reserve
  quoted phrases for when you need an exact string match (rare).
  This is a syntax subtlety on top of the recall pitfall above —
  even broadening from a quoted phrase to an unquoted AND-joined
  query with the same words can be the difference between 0 and 200+
  results.
- The orchestrator: verifies papers were actually ingested (filesystem
  check), reads the profile back, and checks that PMIDs cited in the
  profile correspond to ingested paper pages
- Batch size: 3 subagents (concurrent limit). Follow `batch-drain`: yield and
  wait for each batch to return (its consolidated result re-enters the
  conversation) before dispatching the next; never dispatch "when a slot frees"
  while a batch is still in flight — that overeager re-dispatch is what causes
  the truncation/dropped-shard failure.
- For the first 5 profiles (pilot), the orchestrator does them directly
  to feel where the template breaks before delegating
- **Paywalled paper timeout rule (hard cutoff after three-source closure)**:
  The hard trigger is **three-source closure**, NOT the first failed
  fetch attempt. Once you have confirmed: (1) Europe PMC `inPMC: N`,
  `isOpenAccess: N` (no PMCID), AND (2) Unpaywall `is_oa: false`,
  `oa_status: closed`, AND (3) Semantic Scholar `isOpenAccess: false`,
  `status: CLOSED` — STOP. Do not attempt Wayback CDX, do not try jina
  reader on publisher URLs, do not try direct PDF download. Tag
  `fulltext_source: abstract-only`, `needs-enrichment: true`, and move
  to the next paper. The PubMed abstract (often 1,000–2,000 chars for
  structured abstracts) is sufficient content for profile grounding at
  the key-paper-ingestion level.
  
  **Do not cascade into manual retry branches.** After three-source
  closure, the following are ALL wasted effort and MUST NOT be attempted:
  jina reader on publisher/DOI URLs (returns <600 chars or 404 for
  J Immunol/AAI, Elsevier/JID, Wiley/NYAS), Wayback CDX API (503
  Service Unavailable is persistent, not transient — retrying after
  10-15s sleeps burns 3+ minutes for zero gain), direct urllib PDF
  download (403 for AAI, 404 for core.ac.uk). A single round of these
  is acceptable to confirm the closure, but sequential retries across
  all three are the failure mode.
  
  **The 2-minute budget.** From the first full-text attempt to the
  decision to tag abstract-only should take ≤2 minutes per paper. If
  you have spent >2 minutes on a single paper's full-text retrieval,
  stop immediately, tag abstract-only, and proceed. Spending 5+
  minutes retrying a single paywalled paper wastes the entire profiling
  budget and frustrates your human. 3 ingested papers (even all
  abstract-only) is sufficient for a high-quality profile. The
  orchestrator may intervene to halt retries if a subagent is stuck
  on a paywalled paper.

## GPCR target profiling considerations

C5aR1 is a class A GPCR (7-transmembrane). GPCR targets have structural
characteristics that fundamentally shape the antibody landscape and
require special handling in the profile:

- **The orthosteric binding pocket is within the transmembrane core.**
  Small molecules can access this pocket; antibodies cannot — they are
  too large to enter the transmembrane helix bundle. Antibodies must
  block ligand binding from the extracellular face (N-terminus +
  extracellular loops ECL1-3). When filling field 5 (epitope landscape),
  the antibody-accessible regions are exclusively extracellular — the
  orthosteric pocket (where small molecules bind) is NOT an antibody
  epitope target.
- **The approved drug is often a small molecule, not an antibody.**
  When a small molecule is approved for the target's indication (e.g.,
  avacopan for C5aR1 in AAV), the antibody competitive landscape (field
  10) is fundamentally different: the target is clinically validated,
  but the antibody space is completely open. The profile should note
  this explicitly — the small molecule sets an efficacy bar and a safety
  benchmark that an antibody must differentiate against (dosing
  frequency, safety profile, route of administration, small-molecule-
  failure population).
- **Biased signaling is a GPCR-specific differentiation dimension.**
  GPCRs can signal through multiple pathways (G-protein vs β-arrestin),
  and different ligands can preferentially activate one pathway over
  the other (biased agonism/antagonism). A biased antibody (blocking
  G-protein signaling while sparing β-arrestin, or vice versa) is a
  differentiation opportunity that does not exist for non-GPCR targets.
  Include biased signaling in field 11 (differentiation) for GPCR
  targets. The structural basis for biased signaling is often available
  from crystal/cryo-EM structures (e.g., M265 on TM6 for C5aR1,
  PMID 39153560).
- **Species cross-reactivity is a bigger issue for GPCR antibodies.**
  GPCR extracellular domains are less conserved across species than
  soluble protein domains. Human/mouse C5aR1 shares only ~65% amino
  acid identity. This means human-specific antibodies often do not
  cross-react with mouse C5aR1, necessitating human-receptor knock-in
  mice for preclinical testing. Note this in field 2 (species
  cross-reactivity) and field 7 (in vivo models).

(C5aR1 profile, 2026-08-15.)

### C5a observations (soluble complement fragment + dual-modality target)

C5a (complement C5a anaphylatoxin) is the **first soluble complement fragment**
target profiled — distinct from membrane-bound complement receptors (C5aR1)
or intact complement proteins (C5, properdin). C5a is a ~11 kDa cleavage
product of C5, fully soluble in plasma, not membrane-anchored. 5 key papers
ingested (4/5 full text: 3 PMC XML OA + 1 EPMC PDF render; 1/5 abstract-only
— NEJM, retracted). ~34.5K chars, 7 unique PMIDs cited. New observations:

- **Soluble-target profiling has a distinct isotype and epitope pattern.**
  For soluble targets (cytokines, complement fragments, growth factors),
  the antibody's mechanism is neutralization — blocking the ligand from
  binding its receptor — not cell depletion. The correct isotype is IgG4
  (minimal ADCC/CDC) to avoid Fc-mediated depletion of cells that might
  be coated with the target or target-containing immune complexes. This
  contrasts with cell-surface targets where IgG1 (ADCC/CDC) may be the
  therapeutic mechanism (CD20, CCR8 Treg depletion). In field 4 (antibody
  landscape), always note the isotype AND explain *why* — for soluble
  targets, IgG4 is a functional requirement, not a preference. For field 5
  (epitope landscape), the epitope must overlap with or sterically block
  the receptor-binding interface — for C5a, this is the C-terminal tail
  (residues 69–74, the receptor-activating sequence). Antibodies targeting
  the stable core domain may not neutralize the flexible C-terminal tail's
  receptor-activating function. For field 9 (structural information), there
  are no membrane-proximal regions, no oligomerization interfaces, and no
  conformational accessibility barriers — the entire soluble protein surface
  is antibody-accessible. This simplifies epitope design but means epitope
  differentiation must come from *functional* differences (neutralizing vs
  non-neutralizing, receptor-selective vs pan-blockade), not from
  structural accessibility.

- **Selective C5a blockade vs upstream C5 inhibition is a key mechanistic
  differentiation dimension for complement targets.** Vilobelimab (anti-C5a)
  neutralizes C5a while preserving C5b-9 (MAC) formation; eculizumab (anti-C5)
  blocks both C5a generation AND MAC assembly. This distinction is the
  single most important safety differentiator for complement-targeting
  antibodies: preserving MAC maintains bactericidal function against
  encapsulated organisms, avoiding the meningococcal infection risk that
  requires vaccination with upstream C5 inhibitors. In field 6 (failure/
  success modes), this is the headline success factor for vilobelimab.
  In field 11 (differentiation), it defines the competitive positioning
  vs upstream inhibitors. This pattern generalizes to any complement
  target where selective downstream blockade (C5a, C3a, Bb) can preserve
  upstream or terminal pathway functions that upstream inhibition would
  compromise.

- **Dual-modality targets (antibody + small molecule approved for the same
  axis) require cross-modality competitive analysis.** C5a is targeted by
  vilobelimab (anti-C5a antibody, approved for COVID ARDS) and avacopan
  (C5aR1 small molecule, approved for AAV). These are different modalities
  targeting the same C5a–C5aR1 axis at different points (ligand vs
  receptor). The profile must cross-reference both: the small molecule
  validates the axis clinically; the antibody validates the ligand-
  neutralization approach. In field 10 (competitive landscape), the
  pipeline includes both modalities, and a new antibody must differentiate
  against *both* the existing antibody (different epitope, format, PK)
  AND the small molecule (route, frequency, safety, small-molecule-failure
  population). In field 11, the differentiation case must address: (1) what
  the antibody does that the small molecule cannot (e.g., more complete
  C5a neutralization, different tissue distribution), and (2) what the
  antibody does that the existing antibody does not (e.g., different
  epitope, chronic dosing format, bispecific dual blockade).

- **NEJM retracted-paper retrieval remains blocked.** The ADVOCATE trial
  (PMID 33596356, NEJM) was already documented as retracted in the C5aR1
  profile. In this session, the Wayback Machine availability API returned
  HTTP 429 even after a 15s backoff, and jina reader proxy was blocked by
  CAPTCHA. This confirms the paper-ingest skill's NEJM entry: for retracted
  NEJM papers, abstract-only with `needs-enrichment: true` is the expected
  outcome, not a retrieval failure. The retraction was correctly detected
  via `<PublicationTypeList>` ("Retracted Publication") and
  `<CommentsCorrectionsList>` (`RefType="RetractionIn"` PMID 42377355)
  during Phase 1 identity resolution — confirming the retraction-detection
  pitfall is working as documented.

(C5a profile, ~34.5K chars, 5 papers ingested, 7 unique PMIDs cited,
working-docs/hitlist-profiles/c5a.md.)

### CCR8 observations (GPCR + Treg-depletion + blue ocean)

CCR8 is a class A GPCR (chemokine receptor) — the **second GPCR target
profiled** (after C5aR1) and the **first blue ocean/preclinical target**
profiled at level 2. 3/5 papers (60%) had PMC full text; 2 were
abstract-only (Cell Press Trends Immunol — 404 via jina; ACS Biochemistry
— CAPTCHA via jina). New observations:

- **ECL-binding anti-GPCR antibody structures are now available.**
  The mAb1–CCR8 cryo-EM structure (PMID 38040762, Nat Commun 2023)
  is the first published structure of an antibody bound to a GPCR's
  extracellular loops (ECL1 + ECL2 conformational epitope, long CDRH3
  forming a β-strand interaction with ECL2). This enriches the GPCR
  profiling considerations above: when filling field 5 for a GPCR target,
  check whether an ECL-binding antibody structure has been published —
  it provides direct epitope mapping data that the N-terminus-only
  approved antibodies (mogamulizumab, erenumab) do not. The structural
  motif (long CDRH3 / convex paratope engaging ECL2) is an emerging
  theme for anti-GPCR antibody discovery and should inform in silico
  library design.

- **Treg-depletion targets require a depletion-vs-blockade analysis
  in field 6.** For CCR8, CCR8 blockade alone (ADCC-deficient Nb-Fc)
  has **zero antitumor effect** — only ADCC-mediated depletion of
  CCR8+ Tregs achieves tumor control. This is the single most
  critical success factor and should be the headline finding of
  field 6 for any Treg-depletion target. The profile must explicitly
  state whether the therapeutic mechanism is depletion (requires Fc
  engineering for ADCC) or blockade (requires receptor antagonism),
  because the antibody engineering requirements are fundamentally
  different. For depletion targets, the Fc effector function IS the
  therapeutic mechanism — afucosylated Fc (enhanced FcγRIIIa) is the
  baseline requirement, not an optimization.

- **FcγRIIB is a checkpoint for Treg-depleting antibodies.** Tumor
  Tregs express high levels of FcγRIIB, which limits ADCC-mediated
  depletion. This is why ipilimumab and tremelimumab (anti-CTLA-4,
  IgG1) fail to deplete Tregs in humans despite preclinical efficacy.
  Any Treg-depleting antibody (anti-CCR8, anti-CTLA-4, anti-CD25,
  anti-TNFR2) must be Fc-engineered to minimize FcγRIIB engagement.
  This is a generalizable insight for the Treg-depletion target class
  — include it in field 6 (failure modes) and field 11
  (differentiation) for any target whose mechanism is Treg depletion.
  (PMID 38147316.)

- **Treg-depletion targets have tissue-Treg on-target risks.**
  CCR8+ Tregs are not confined to tumors — they play homeostatic
  roles in cardiac protection (PMID 41685444), bone fracture healing
  (PMID 39509336), and maternal-fetal tolerance (PMID 40249828).
  The on-target safety risk for Treg-depleting antibodies is from
  tissue-resident Tregs, not from the target receptor's signaling
  function. This is a distinct safety pattern from non-Treg targets
  where on-target toxicity comes from blocking the target's
  physiological signaling. For field 8 (safety), enumerate tissue-Treg
  populations that express the target and their physiological
  functions — these define the safety ceiling.

- **Bispecific antibody landscape is unusually active for a blue
  ocean target.** CCR8/CTLA-4, CCR8/TNFR2, and CCR8/4-1BB bispecifics
  are all in preclinical development because CCR8+ Tregs co-express
  multiple co-inhibitory receptors. For Treg-depletion targets where
  the target cell population is well-defined (CCR8+ Tregs), bispecific
  approaches that deplete Tregs via one arm and co-stimulate effectors
  via the other are a natural format. Include the bispecific landscape
  in field 4 and field 10 even for blue ocean targets — the activity
  level signals the field's trajectory.

- **CCL18 is NOT a human CCR8 ligand (contrary to older literature).**
  Despite early reports, CCL18 does not activate human CCR8 in
  functional assays (PMID 38040762). CCL1 is the sole confirmed
  endogenous agonist. For field 2 (biological mechanism), verify
  ligand assignments against recent functional data, not just
  database annotations — older literature can carry forward
  unvalidated ligand-receptor assignments that structural/biochemical
  studies later disprove.

(CCR8 profile, ~35K chars, 5 papers ingested, 12+ PMIDs cited,
working-docs/hitlist-profiles/ccr8.md.)

### CXCL10 observations (soluble chemokine ligand + ligand-redundancy target)

CXCL10 (IP-10) is a **secreted ELR-negative CXC chemokine** — the first
soluble chemokine ligand (not a receptor) profiled at level 2, and the first
target where **ligand redundancy among shared-receptor ligands** is the
central biological challenge. CXCL10 is one of three CXCR3 ligands (CXCL9/
MIG, CXCL10/IP-10, CXCL11/I-TAC). 5 key papers ingested (1/5 full text via
PMC XML: Kim 2014 myositis model, PMC4095607, 27.7K chars; 4/5 abstract-only:
Wiley/Elsevier/ADA publisher blocks, no PMCID). ~34.5K chars profile, 5
unique PMIDs cited. New observations:

- **Ligand redundancy among shared-receptor ligands is the central challenge
  for soluble chemokine targets.** CXCL10, CXCL9, and CXCL11 all bind CXCR3.
  Blocking a single ligand may be insufficient when the other two can
  compensate — this is the biological analog of the dual-receptor selectivity
  problem (LIGHT/HVEM+LTβR), but in reverse: one ligand, three redundant
  alternatives sharing one receptor. The clinical evidence confirms this:
  MDX-1100 (anti-CXCL10) achieved ACR20 (54% vs 17%, P = 0.0024) but NOT
  ACR50/ACR70 in the RA Phase II trial — consistent with partial efficacy
  from single-ligand blockade. However, **disease-specific ligand dominance
  determines whether monotherapy suffices**: in myositis, CXCL10 is the
  predominant CXCR3 ligand in muscle (CXCL9/CXCL11 weakly stained), while
  in lupus nephritis, CXCL9 is dominant. In some disease models (dengue,
  LCMV-induced diabetes), CXCL10 deficiency cannot be compensated by
  CXCL9/CXCL11. The profile must: (1) identify which CXCR3 ligand is
  dominant in the target indication (tissue IHC or serum levels); (2) note
  whether single-ligand or pan-ligand blockade is required; (3) include
  disease-specific ligand dominance as a field 11 differentiation dimension
  — a biomarker-selected anti-CXCL10 trial in CXCL10-dominant disease may
  succeed where an unselected trial failed. This pattern generalizes to any
  soluble ligand target where the receptor is shared by multiple ligands
  (CXCL9/10/11→CXCR3, CCL19/21→CCR7, IL-12/23 p40 shared by IL-12 and IL-23).
  (PMID 22147649, 24939012.)

- **The IFN-γ–CXCL10–CXCR3 positive feedback loop is the mechanistic basis
  for early intervention.** CXCL10 recruits CXCR3+ T cells that produce
  IFN-γ, which induces more CXCL10 — a self-amplifying inflammatory cycle.
  Blocking CXCL10 breaks this loop at its initiation. This has two
  implications for profiling: (1) in field 2 (biological mechanism), the
  amplification loop should be explicitly documented as it defines the
  therapeutic rationale — the target is not just a chemokine but a node in
  a self-reinforcing inflammatory network; (2) in field 6 (failure/success
  modes), the loop predicts that anti-CXCL10 monotherapy will work best in
  early disease (before the loop is fully established) and may fail in
  established disease where already-infiltrated T cells persist
  independently of new recruitment. This is confirmed by the T1D model:
  anti-CXCL10 alone was insufficient to reverse established diabetes but
  was effective at preventing re-infiltration after T cell depletion
  (combination with anti-CD3). For chemokine targets with amplification
  loops, always include the loop mechanism in field 2 and the therapeutic
  window implication in field 6. (PMID 24939012, 26293506.)

- **Pipeline attrition despite clinical validation is a distinct failure
  mode.** MDX-1100 (anti-CXCL10) showed clinical proof-of-concept in RA
  (Phase II positive, ACR20 54% vs 17%, no serious AEs) — the first
  chemokine inhibitor to demonstrate clinical efficacy in RA — yet has not
  advanced to Phase III in 14+ years (as of 2026). This is distinct from
  "target invalid" (the biology worked), "wrong antibody" (the antibody was
  safe and efficacious), and "mechanism-trial-design mismatch" (the trial
  was correctly designed and met its primary endpoint). The likely causes
  are commercial/competitive: the RA market is saturated with anti-TNF,
  JAK inhibitors, and anti-IL-6, and the modest absolute efficacy (ACR20
  only, not ACR50/70) may not justify a Phase III investment against
  entrenched competitors. For field 6 (failure modes), pipeline attrition
  despite clinical validation is a failure of the development program, not
  the target — a new antibody with a differentiated format (bispecific
  anti-CXCL10/CXCL9, biomarker-selected population, or a CXCL10-dominant
  indication like myositis) could reopen the target. This pattern applies
  to any clinical-trial-tier target where Phase II was positive but Phase
  III was never initiated. (PMID 22147649.)

- **The serum biomarker paradox complicates pharmacodynamic monitoring.**
  In the CIM myositis model, anti-CXCL10 treatment reduced muscle
  inflammation but did NOT reduce serum CXCL10 levels (370.5 vs 381.1
  pg/mL, P = 0.843). This is analogous to anti-TNF antibodies increasing
  serum TNF-α (increased half-life or assay interference by the antibody).
  For field 7 (assay systems) and field 8 (safety), when the target is a
  secreted protein, the serum level of the target may paradoxically
  increase or remain unchanged during effective antibody therapy —
  complicating the use of serum target levels as a pharmacodynamic
  biomarker. Alternative PD biomarkers (tissue infiltration scores,
  downstream T cell activation markers, or the target's functional
  readout like chemotactic index) should be identified. This pattern
  applies to any anti-cytokine/anti-chemokine antibody where serum levels
  of the target are used as a disease biomarker. (PMID 24939012.)

- **Combination therapy with T cell-depleting agents defines the optimal
  therapeutic window for chemokine blockers.** Anti-CD3/anti-CXCL10
  combination was superior to either monotherapy in T1D (two mouse models:
  RIP-LCMV and NOD). The paradigm: first inactivate existing autoreactive
  T cells (anti-CD3), then block re-infiltration (anti-CXCL10). This
  temporal two-hit strategy defines the optimal use of anti-chemokine
  antibodies: they are not monotherapy for established disease but
  relapse-prevention after T cell depletion. For field 11
  (differentiation), a bispecific anti-CD3/anti-CXCL10 could translate
  this paradigm into a single molecule. This combination strategy
  generalizes to any chemokine target where the pathological effector is
  a T cell population that can be depleted (anti-CD3, anti-CD4, anti-CD8)
  and then prevented from re-entering the tissue (anti-chemokine).
  (PMID 26293506.)

(CXCL10 profile, ~34.5K chars, 5 papers ingested, 5 unique PMIDs cited,
working-docs/hitlist-profiles/cxcl10-ip-10.md.)

### C3aR observations (dual-ligand GPCR + biased agonism + pharmacological confound)

C3aR (C3AR1) is a class A GPCR for the complement anaphylatoxin C3a —
the **third complement GPCR** profiled (after C5aR1 and CCR8) and the
**first dual-ligand GPCR** where two endogenous ligands with distinct
signaling bias create a therapeutic index opportunity. Preclinical tier
(immunology). 3 landmark papers ingested at 100% full-text retrieval rate
(2/3 EPMC PDF, 1/3 PMC XML — all had PMCIDs with accessible full text).
~34K chars profile, 3 paper pages created, 3 unique PMIDs cited. Key new
patterns:

- **Dual-ligand GPCR with ligand-mediated biased agonism is a
  therapeutic-index differentiation dimension.** C3aR has two endogenous
  ligands: C3a (complement anaphylatoxin, inflammatory, balanced agonist
  — both G protein and β-arrestin) and TLQP-21 (VGF-derived neuropeptide,
  metabolic, G protein-biased — minimal β-arrestin recruitment). A biased
  antagonist antibody that blocks C3a binding (inflammatory) while
  preserving TLQP-21 binding (metabolic) would have a fundamentally better
  therapeutic index than a pan-blocker. This extends the existing GPCR
  biased-signaling consideration: when a GPCR has multiple endogenous
  ligands with different signaling bias profiles, the antibody epitope
  can determine which ligand's signaling is blocked — this is an
  **epitope-dependent biased antagonism** opportunity that is unique to
  dual-ligand GPCRs. Include ligand bias profiles in field 2 (biological
  mechanism), field 5 (epitope landscape), and field 11 (differentiation).
  (PMID 38072064, full text; C3aR profile, 2026-08-16.)

- **The standard "antagonist" research tool may actually be an agonist
  — reinterpret all prior literature.** SB290157, the widely used C3aR
  antagonist, is a potent pan-agonist at all C3aR1 transducer pathways
  (Gi/o/z, β-arrestin, cAMP inhibition). Its apparent calcium-flux
  antagonism is caused by potent β-arrestin-mediated receptor
  internalization, not competitive antagonism. Blocking internalization
  (barbadin, Pitstop-2) unmasks SB290157 agonism. This means every prior
  study using SB290157 as a "C3aR antagonist" may have actually observed
  receptor activation + desensitization, not blockade. JR14a (an
  SB290157 derivative) has the same mechanism. For field 4 (antibody
  landscape), list small-molecule "antagonists" with a caveat about their
  true pharmacology when definitive profiling data exists. For field 6
  (failure modes), this is a distinct failure class: the preclinical
  evidence base for C3aR blockade is confounded by the research tool being
  an agonist — a true competitive antagonist (or antibody) must be
  validated against this confound. Generalizable to any target where the
  standard pharmacological tool has been recharacterized as having
  paradoxical pharmacology. Always check whether the reference antagonist
  has been definitively profiled at the transducer level, not just
  assumed to be an antagonist from functional assays. (PMID 38072064,
  full text.)

- **Biased agonism as a mast cell degranulation selectivity filter.**
  C3a (balanced agonist) potently induces mast cell degranulation
  (β-hexosaminidase release) while TLQP-21 (G protein-biased) and
  SB290157 (internalization-dependent) do not. A balanced agonist is
  required for full mast cell activation — this suggests that a biased
  C3aR antagonist could block inflammatory C3a signaling while
  inherently avoiding mast cell degranulation (anaphylaxis), a safety
  advantage. For field 8 (safety), biased ligands that avoid mast cell
  degranulation have an intrinsic safety advantage for chronic dosing.
  Generalizable to any GPCR target expressed on mast cells where
  degranulation is an on-target toxicity concern. (PMID 38072064, full
  text.)

- **Endothelial-specific conditional knockout validates cell-autonomous
  C3aR function.** Endothelial-specific C3ar1 deletion (C3ar1fl/fl ×
  Tie2-Cre, T2KO) replicated the global knockout phenotype (reduced
  VCAM1, rescued BBB permeability, reduced microglial reactivity),
  demonstrating cell-autonomous endothelial C3aR signaling. For field 7
  (assay systems) and field 3 (disease evidence), conditional
  cell-type-specific knockouts are the gold standard for validating
  which cell population's C3aR drives disease — and they demonstrate
  that an antibody (which targets the extracellular domain) can achieve
  the same cell-type-selective effect by targeting C3aR on the
  pathogenic cell population. Generalizable to any GPCR expressed on
  multiple cell types where the pathogenic signaling is cell-type-
  specific. (PMID 32990682, full text.)

- **C3aR blockade creates a complement feedback loop.** In Heymann
  nephritis rats, C3aR blockade reduced not only downstream podocyte
  injury but also upstream complement deposition (C1q, factor B, C5b-9)
  and specific IgG deposition in glomeruli. This suggests C3a/C3aR
  signaling feeds back to amplify the complement cascade — blocking
  C3aR dampens the entire inflammatory loop. For field 2 (biological
  mechanism), document feedback loops where target blockade reduces
  upstream complement activation, as this means the therapeutic effect
  is broader than simple receptor antagonism. Generalizable to any
  complement receptor where C3a/C5a signaling amplifies the cascade.
  (PMID 35777783, full text.)

(C3aR profile, ~34K chars, 3 papers ingested (3/3 full text), 3 unique
PMIDs cited, working-docs/hitlist-profiles/c3ar.md.)

### CCL1 observations (soluble chemokine ligand + context-dependent dual role + dual-receptor system)

CCL1 (I-309/TCA3) is a **soluble CC chemokine** — the second soluble
chemokine ligand profiled at level 2 (after CXCL10), and the first
target where a **context-dependent dual role** (protective in one
disease, pathological in another) is the central profiling challenge.
Preclinical tier (immunology). 3 landmark papers ingested (1/3 full
text via PMC XML: Tiffany 1997, J Exp Med, 17.3K chars; 2/3
abstract-only: Elsevier ScienceDirect CAPTCHA + J Immunol 403, both
paywalled with no PMC). ~27K chars profile, 12 unique PMIDs cited.
New observations:

- **Context-dependent dual role is the central challenge for
  Treg-recruiting chemokine targets.** CCL1-CCR8 has a **protective**
  role in atherosclerosis — it recruits anti-inflammatory Tregs to the
  vascular wall, where they produce IL-10 and suppress inflammation;
  CCL1 knockout or anti-CCR8 blockade *accelerates* atherosclerosis
  (PMID 31121182). But the same axis has a **pathological** role in
  cancer and fibrosis — CCR8+ Tregs suppress anti-tumor immunity
  (PMID 35428909), and CCL1 drives fibroblast-to-myofibroblast
  differentiation in pulmonary fibrosis (PMID 34407391). This is
  distinct from the CCR8 profile's depletion-vs-blockade analysis:
  the dual role is a property of the **biology**, not the antibody
  format. For field 6 (failure modes), the headline failure mode is
  "wrong disease context" — an anti-CCL1 antibody used in a patient
  with subclinical atherosclerosis could accelerate cardiovascular
  disease. For field 11 (differentiation), the key opportunity is
  **biomarker-selected populations**: patients with high CCL1 in
  BAL fluid (fibrosis) or high CCR8+ Treg infiltration in tumors
  (cancer), while excluding patients with active cardiovascular
  disease. This pattern generalizes to any Treg-recruiting chemokine
  target where Treg function is context-dependent (protective in
  autoimmunity/atherosclerosis, pathological in cancer/fibrosis).
  (CCL1 profile, 2026-08-16.)

- **Dual-receptor systems create an epitope selectivity opportunity
  that single-receptor targets do not have.** CCL1 signals through
  both CCR8 (on leukocytes/Tregs, Gi-coupled GPCR) and AMFR (on
  fibroblasts, identified by mass spectrometry of CCL1 complexes,
  PMID 34407391). These are structurally unrelated receptors with
  distinct cell-type-specific functions. An anti-CCL1 antibody whose
  epitope blocks the CCR8-binding interface but spares the AMFR-binding
  interface would selectively block leukocyte recruitment while
  preserving (or vice versa) fibroblast activation — a selectivity
  dimension that does not exist for single-receptor targets. This is
  the inverse of the C3aR dual-ligand pattern (one receptor, two
  ligands with different bias): here it is one ligand, two receptors
  with different cell targets. For field 5 (epitope landscape) and
  field 11 (differentiation), a dual-receptor target offers
  **epitope-dependent receptor selectivity** — map both receptor-
  binding interfaces and note whether a single epitope can block
  one while sparing the other. This generalizes to any soluble
  ligand with multiple receptors (CCL1/CCR8+AMFR, RANKL/RANK+OPG,
  BAFF/BAFF-R+TACI+BCMA). (PMID 34407391.)

- **Ligand-neutralization vs receptor-depletion is a class-level
  mechanistic choice for Treg-trafficking targets.** Anti-CCL1
  (neutralize the soluble ligand → IgG4, minimal Fc effector function,
  blocks the chemotactic gradient without killing any cells) vs
  anti-CCR8 (deplete the receptor-expressing cells → IgG1 with ADCC,
  eliminates CCR8+ Tregs including homeostatic tissue-resident
  populations). The CCR8 profile established that depletion (not
  blockade) is required for antitumor efficacy; the CCL1 profile
  extends this to the ligand side: neutralizing CCL1 blocks
  **recruitment** of new Tregs but does not remove Tregs already
  present in the tumor. For field 4 (antibody landscape) and field
  11 (differentiation), when both ligand and receptor are viable
  antibody targets, explicitly compare: (1) neutralization (ligand,
  IgG4) — blocks recruitment, spares existing cells, potentially
  safer for tissue-Treg on-target risks; (2) depletion (receptor,
  IgG1 afucosylated) — removes existing cells, more complete in
  established disease, higher on-target risk for tissue-resident
  Tregs. The choice depends on disease stage: early disease
  (recruitment-driven) favors neutralization; established disease
  (infiltrated Tregs) favors depletion. (PMID 17404314, PMID
  31121182, CCR8 profile PMID 38147316.)

(CCL1 profile, ~27K chars, 3 papers ingested (1/3 full text, 2/3
abstract-only — paywalled), 12 unique PMIDs cited,
working-docs/hitlist-profiles/ccl1.md.)

### CXCR6 observations (GPCR chemokine receptor + tissue-resident T cell marker + ICI myocarditis)

CXCR6 is a class A GPCR (chemokine receptor) — the **first tissue-resident
T cell marker** target profiled, where the receptor's primary therapeutic
relevance is as a marker and functional regulator of pathogenic
tissue-resident T cells (not just a chemokine signaling receptor). CXCR6
binds CXCL16 (sole ligand). Preclinical tier (immunology). 3 landmark
papers ingested (1/3 full text via PMC XML: Munir 2026 Circulation,
37,891 chars; 2/3 abstract-only: Jiang 2005 J Immunol [paywalled, no
PMCID], Dudek 2021 Nature [subscription, jina returned only references]).
~48K chars profile, 12 unique PMIDs cited. Key new patterns:

- **Tissue-resident T cell marker targets: CXCR6 as a new target class.**
  CXCR6 is not just a chemokine receptor — it is the hallmark marker of
  pathogenic tissue-resident T cells across multiple disease contexts:
  ICI myocarditis (clonal CXCR6+ cardiac T cells, PMID 41498147), NASH
  (auto-aggressive CXCR6+ CD8 T cells, PMID 33762736), and transplant
  tolerance (regulatory NKT cells, PMID 16081769). This distinguishes
  CXCR6 from other chemokine receptor targets profiled (CXCR3, CXCR5,
  CCR8) where the target's role is primarily in cell recruitment, not
  tissue residency. For field 2 (biological mechanism), the key concept
  is that CXCR6 marks a tissue-resident T cell population whose
  pathogenicity is context-dependent (pathogenic in myocarditis/NASH,
  regulatory in allograft tolerance). For field 6 (failure modes), the
  headline failure mode is tolerance disruption — blocking CXCR6 can
  break allograft tolerance by disrupting regulatory NKT cell trafficking
  (PMID 16081769), the same axis that is therapeutic in ICI myocarditis.
  Generalizable to any chemokine receptor that marks tissue-resident
  T cell populations with context-dependent pathogenicity. (CXCR6
  profile, 2026-08-16.)

- **Depleting vs blocking: depletion is superior for ICI myocarditis.**
  The Munir 2026 study (PMID 41498147) used a depleting anti-CXCR6
  antibody (decreases total T-cells and CXCR6+ T-cells by flow
  cytometry) that achieved 100% survival in Lag3-/-, Pdcd1-/- mice.
  Anti-CXCR3 (also tested) rescued lethality but with residual
  arrhythmias (4/8 vs 1/8 for anti-CXCR6). CXCR6, not CXCR3, marked
  hyperexpanded clonal T cells — suggesting depleting the clonally
  expanded pathogenic population is more effective than blocking
  recruitment alone. For field 6 (failure/success modes) and field 11
  (differentiation), when a chemokine receptor marks a pathogenic
  tissue-resident T cell population, a depleting IgG1 (afucosylated
  for enhanced ADCC) is likely superior to a blocking antibody —
  the pathogenic cells are already in the tissue, so blocking
  recruitment alone may be insufficient. This extends the CCR8
  Treg-depletion pattern to non-Treg pathogenic T cells.

- **ICI myocarditis as an emerging indication for chemokine receptor
  antibodies.** CXCR6 is the second chemokine receptor validated for
  ICI myocarditis (after CXCR3, PMID 39931812, CXCR3 profile). Both
  anti-CXCR6 and anti-CXCR3 rescue lethality in genetic mouse models.
  The CXCL16-CXCR6 axis is complementary to the CXCL9/10-CXCR3 axis:
  CXCL16 is produced by cardiac macrophages (not IFN-γ-inducible like
  CXCL9/10), and CXCR6 marks clonally expanded T cells (CXCR3 does
  not). For field 3 (disease evidence), ICI myocarditis is an
  emerging indication with no targeted therapies — the growing use
  of combination ICI (especially anti-LAG-3/PD-1, OR=4.0 for
  myocarditis risk) creates a growing market. For field 10
  (competitive landscape), the ICI myocarditis space is entirely
  preclinical for chemokine receptor antibodies — first-in-class
  opportunity.

- **Auto-aggressive T cell biology as a novel mechanism.** The Dudek
  2021 Nature paper (PMID 33762736) describes "auto-aggressive"
  CXCR6+ CD8 T cells that kill hepatocytes in an MHC-class-I-
  independent manner via P2X7 purinergic receptors — fundamentally
  distinct from antigen-specific cytotoxicity. This is triggered by
  IL-15-induced FOXO1 downregulation and CXCR6 upregulation, which
  renders T cells susceptible to metabolic stimuli (acetate,
  extracellular ATP). For field 2 (biological mechanism), this is a
  novel mechanism class: CXCR6 marks T cells that have undergone a
  metabolic switch to auto-aggressive killing. For field 6, the
  therapeutic implication is that depleting CXCR6+ T cells removes
  the auto-aggressive population, while blocking CXCR6 signaling
  alone may not prevent the metabolic trigger. Generalizable to any
  target where the receptor marks a metabolically reprogrammed T cell
  population (the IL-15/FOXO1/CXCR6/P2X7 axis may extend beyond NASH).

- **Nature subscription research articles return only references via
  jina reader proxy.** The Dudek 2021 Nature paper (PMID 33762736, no
  PMCID, subscription) returned 75K chars via jina reader proxy, but
  the content was entirely references, extended data figure legends,
  and metadata — no article body text (no Abstract, Introduction,
  Results, or Discussion sections). This is the same pattern as
  Nature Reviews subscription journals (documented in paper-ingest
  known-blocks). Nature *research* articles that are NOT open access
  (no PMCID) are subscription-gated and jina returns only the
  publicly accessible portions (references, data availability,
  extended data legends). The paper-ingest skill's note that
  "Nature research-article pages render reliably" applies only to
  *open access* Nature research articles (those with a PMCID).
  Subscription Nature research articles behave like Nature Reviews
  for jina retrieval purposes. For target profiling, when a key
  paper is a subscription Nature article with no PMCID, abstract-only
  is the expected outcome. (CXCR6 profile, 2026-08-16.)

(CXCR6 profile, ~48K chars, 3 papers ingested (1/3 full text, 2/3
abstract-only — paywalled), 12 unique PMIDs cited,
working-docs/hitlist-profiles/cxcr6.md.)

## Pitfalls

- **Skipping the pilot.** The pilot validates the template, the workflow,
  and the tiering. Scaling without it risks discovering the template is
  wrong after 50 profiles.
- **Pre-registering pilot pass/fail criteria.** The pilot is an empirical
  observation, not a test. Observe what happens and adjust.
- **Speculating in empty fields.** "Unknown" or "No data" is the correct
  entry for fields where no information exists. Do not fill with guesses.
- **Baking scoring into the profile.** Profiles are facts. Scoring is
  applied separately with different weights for different use cases.
  Field 11 (differentiation) is the only judgment field.
- **Creating brain pages instead of working docs.** Profiles are working
  docs — no frontmatter, no indexing. Promote to brain pages only when
  a target is selected for active investigation.
- **Profiling all 900 targets before starting.** Sequence by tier. The
  graveyard and saturated tiers are fastest and most valuable for
  platform demonstration. Blue ocean is the deepest work and the
  highest-value long-term investment.
- **Abstract-level errors that full-text ingestion catches.** The CD147
  profile at level 1 (abstract) incorrectly identified begelomab as an
  anti-CD147 antibody. Full-text ingestion at level 2 revealed begelomab
  targets CD26/DPP4, not CD147 — the confusion arose because both ABX-CBL
  (anti-CD147) and begelomab (anti-CD26) were tested in GVHD. This is the
  canonical example of why level 2 (key paper ingestion) is the minimum
  rigor for usable profiles: abstracts can misattribute drug-target
  relationships when drugs with similar indications have different
  targets. Always verify drug-target assignments against full text, not
  abstract summaries or database tags.
- **Retracted pivotal trial papers.** During identity resolution (Phase 1
  of paper-ingest), always check `<PublicationTypeList>` for
  "Retracted Publication" and `<CommentsCorrectionsList>` for
  `RefType="RetractionIn"`. A retracted pivotal trial paper (e.g., the
  ADVOCATE trial for avacopan, PMID 33596356, retracted 2026-06-29 per
  PMID 42377355) does NOT necessarily invalidate the underlying clinical
  data or regulatory approval, but it casts uncertainty on the published
  evidence base. When a retraction is discovered: (1) flag it prominently
  in field 3 (disease evidence) and field 6 (failure/success modes);
  (2) note the retraction PMID alongside the original; (3) acknowledge
  that the clinical data in regulatory records may still be valid — the
  retraction pertains to the published article, not necessarily the
  trial itself; (4) any new antibody program against this target should
  independently verify the target validation rather than relying on the
  retracted publication. This is a general issue — retractions of
  pivotal papers are uncommon but high-impact when they occur, and they
  are easily missed if identity resolution skips the PublicationType
  check.
- **Small-molecule-approved, antibody-open competitive landscape.**
  When the approved drug for a target's indication is a small molecule
  (not an antibody), the competitive landscape (field 10) and
  differentiation opportunities (field 11) require a distinct framing.
  The target IS clinically validated (the small molecule proves the
  biology), but the antibody space is completely open — no antibody has
  been approved, and antibody-specific epitope data is entirely absent.
  The profile should explicitly note: (1) the approved drug is a small
  molecule, not an antibody; (2) the antibody competitive landscape is
  open; (3) an antibody must differentiate against the small molecule's
  advantages (oral bioavailability, established safety, cost) — the
  antibody's differentiation case must be based on dosing frequency,
  safety profile, efficacy in small-molecule failures, or novel
  indications. This pattern applies to any target where a small molecule
  has been approved but no antibody has reached the market (e.g., C5aR1/
  avacopan, and potentially other GPCR targets where small-molecule
  modulators dominate).
- **Dual-purpose targets: isotype/epitope, not target biology, determines
  success vs failure.** When the same target has an approved antibody in
  one indication and failed antibodies in another (e.g., CD4: ibalizumab
  approved for HIV, multiple anti-CD4 antibodies failed in RA), the
  failure analysis (field 6) must explicitly compare the isotype and
  epitope of the winner vs the losers to isolate format/epitope failure
  from target failure. Ibalizumab (IgG4 non-depleting, D2 epitope
  preserving immune function) vs zanolimumab/4162W94/keliximab (IgG1
  depleting, D1 epitope blocking MHC II) — the target was not the
  problem; the isotype/epitope combination was. This pattern generalizes
  to any target where depleting and non-depleting approaches have been
  tried in different indications: the isotype determines the safety
  profile (depleting = immunosuppression risk; non-depleting = avoids
  depletion but requires a blocking mechanism), and the epitope
  determines the functional consequence (function-preserving vs
  function-blocking). For graveyard profiles, always check whether a
  successful antibody exists in a different indication before declaring
  the target invalid — a dual-purpose target may be a graveyard in one
  indication but validated in another. (CD4 profile, 2026-08-15.)
- **On-target, mechanism-based toxicity is a distinct graveyard pattern for immune-trafficking targets.** CD11a/LFA-1 is the canonical example: efalizumab (anti-CD11a, approved for psoriasis 2002, withdrawn 2009) failed not because of lack of efficacy — it worked for psoriasis — but because blocking LFA-1–mediated T cell trafficking impaired CNS immune surveillance against JC virus, leading to progressive multifocal leukoencephalopathy (PML). The PML risk is **target-specific, not antibody-specific**: any systemic LFA-1 blocker will impair CNS T cell trafficking. The same PML mechanism affects natalizumab (anti-α4 integrin), confirming that disrupting leukocyte trafficking into the CNS is a class effect across different targets. For field 6 (failure modes), the critical analysis is: (1) was the failure target-specific or antibody-specific? (2) is the toxicity an on-target consequence of the therapeutic mechanism (efficacy and toxicity share the same mechanism)? (3) does the risk-benefit ratio make sense for the indication (PML is unacceptable for psoriasis but may be tolerable for a life-threatening disease)? For field 11 (differentiation), the key question is whether a different format (tissue-specific delivery, conditional activation, partial blockade) could decouple efficacy from the on-target toxicity — but for mechanism-based toxicity, no format change addresses the root cause. (CD11a profile, 2026-08-15, PMID 20298966, PMID 19687432.)

- **IRIS upon drug removal creates a therapeutic dilemma for trafficking-blocker graveyard targets.** When efalizumab-associated PML was treated with plasma exchange to remove the drug, the rapid restoration of lymphocyte trafficking into the brain triggered immune reconstitution inflammatory syndrome (IRIS) — two efalizumab PML cases treated this way had fatal outcomes (PMID 20298966). This creates a double bind: the drug causes PML by blocking immune surveillance, but removing the drug to restore surveillance triggers inflammatory brain destruction. For field 6, IRIS upon drug removal is a distinct failure mode for any antibody whose mechanism involves blocking immune cell trafficking — the reversibility of the blockade itself becomes a safety risk. For field 8 (safety profile), note whether the antibody's mechanism is reversible (can be cleared to restore function) or irreversible (depleting), and whether reversibility itself carries risks. (CD11a profile, 2026-08-15.)

- **Cross-class PML risk for T cell trafficking blockers is a shared safety ceiling.** PML from impaired CNS immune surveillance is not specific to LFA-1 — it affects natalizumab (anti-α4 integrin/ VLA-4), efalizumab (anti-CD11a/LFA-1), and rituximab (anti-CD20, B cell depletion). The shared mechanism is disruption of T cell–mediated immune surveillance of JC virus in the CNS, achieved through different primary mechanisms (block trafficking, block adhesion, deplete B cells). For field 8 (safety) and field 11 (differentiation), any new antibody targeting leukocyte trafficking, adhesion, or T cell function should assess PML risk as a class-level concern, not a target-specific one. JCV serostatus (anti-JCV antibody index) is a validated risk stratification biomarker for natalizumab and should be considered for any trafficking-blocker program. (CD11a profile, 2026-08-15, PMID 20298966.)

- **Paywalled clinical trial papers limit full-text grounding.** NEJM,
  Lancet, Blood, and JAMA papers — the most important clinical trial
  publications — are consistently paywalled with no PMC copy. Of 5 C5
  landmark papers, 4 were abstract-only. Europe PMC structured abstracts
  (1,000–2,500 chars with Background/Methods/Results/Conclusions) often
  compensate sufficiently for fields 2, 3, 6, and 8, but structural papers
  (which carry epitope data for field 5) are the highest-value to
  prioritize for full-text retrieval. When selecting which 3-5 papers to
  ingest per target, prioritize: (1) structural/epitope papers (open
  access in Sci Rep, Nature Comms, mAbs, Front Immunol), (2) review
  papers (often OA), (3) clinical trial papers (likely paywalled, use
  abstract).
- **Proactive paper substitution beats abstract-only fallback.** When
  initially selected landmark papers turn out to be paywalled (Elsevier,
  Wiley — no PMC copy, jina returns nothing), do NOT immediately fall
  back to abstract-only. Instead, run additional PubMed searches with
  topic-specific queries to find open-access replacements covering the
  same topic area (e.g., search for "PAI-1 review pathophysiology" or
  "PAI-1 crystal structure" to find OA review/structural papers). This
  typically recovers 2-3 full-text papers that cover the same content as
  the paywalled originals. The pattern: (1) check Europe PMC gate for
  all 5 initial papers; (2) for any that are `inPMC: N, isOpenAccess: N`,
  immediately search PubMed for alternative OA papers on the same topic;
  (3) run `fetch_fulltext.py` on the replacements; (4) only use
  abstract-only for papers that have no OA equivalent. This approach
  yielded 5/5 full-text papers for the PAI-1 profile (vs 2/5 if we had
  kept the paywalled originals). The 2-minute paywall timeout rule
  applies to RETRYING a paywalled paper, not to finding a replacement.
  (PAI-1/SERPINE1 profile, 2026-08-16.)
- **Batch-fetch abstracts for paywalled citation papers.** Papers that
  cannot be ingested as full text but need to be cited (for disease
  evidence, antibody landscape, failure modes) can have their abstracts
  batch-fetched via `efetch` (XML, parse `<AbstractText>`). Collect
  10-15 paywalled paper abstracts in a single batch with 4s spacing
  between PubMed calls. Store as JSON for reference during profile
  writing. This extends the "abstract-only is acceptable" pattern:
  abstracts ground citations even when full text is unavailable.
  (PAI-1/SERPINE1 profile, 2026-08-16 — 14 abstracts batch-fetched
  for citation grounding.)
- **Task brief UniProt IDs can be wrong — always verify against the gene
  symbol. Make this a hard pre-flight gate, not a passive check.**
  This is a **recurring systematic error in delegation/orchestration
  metadata**, not a one-off — three independent recurrences across
  different profiles and different orchestrators:
  - Properdin/CFP: brief listed P05155 (C1 inhibitor/SERPING1); correct is
    P27918. (Properdin profile, 2026-08-15.)
  - 5T4/TPBG: brief listed Q13440 (demerged/inactive); correct active entry
    is Q13641. (5T4/TPBG profile, 2026-08-16 — see the "demerged/inactive
    entries" pitfall below.)
  - Endothelin receptor A/EDNRA: brief listed **P25105 (PTAFR —
    platelet-activating factor receptor, an unrelated class-A GPCR)**;
    correct is **P25101**. (EDNRA profile, 2026-08-17 — note P25105 and
    P25101 are adjacent accessions, making a copy/transposition error a
    plausible upstream cause.)
  - GDF11: brief listed **Q9GKX7 (HSP90-alpha / HSP90AA1 — a completely
    unrelated cytosolic chaperone)**; correct is **O95390**. (GDF11
    profile, 2026-08-17 — the error was caught immediately when UniProt
    returned the wrong protein name, before any profile content was
    written. This is the 4th recurrence across different orchestrators.)
  Always verify the UniProt ID from the task brief by: (1) querying UniProt
  by gene symbol + organism
  (`rest.uniprot.org/uniprotkb/search?query=gene:{SYMBOL}+AND+organism_id:9606&format=json`),
  (2) confirming the returned protein name matches the target, (3) **also
  fetching the brief's accession directly**
  (`rest.uniprot.org/uniprotkb/{ACCESSION}.txt`) and reading its
  `DE RecName`/`GN Name` lines — a mismatch here is the fastest detection
  path and takes one call, (4) flagging the discrepancy in the profile if
  the brief's ID was wrong (do not silently overwrite — note the correction
  explicitly in field 1, as the EDNRA profile did). This is the UniProt
  analogue of the paper-ingest seed-identifier gate: identifiers from
  upstream sources are suggestions, not facts. The UniProt API is fast
  (single call, no rate limits) and should be part of the initial identity
  verification for every profile. **Treat the brief-provided UniProt ID as
  untrusted until the gene-symbol lookup confirms it.**
- **Generic-name targets require gene-symbol-first PubMed searches.**
  Targets whose common name is a generic English word (LIGHT, APRIL,
  TWEAK, TRANCE, RANK) collide with hundreds of thousands of irrelevant
  PubMed results. "LIGHT" alone matches 340K papers (illumination,
  light chains, etc.). Always use the gene symbol (TNFSF14, TNFSF13,
  TNFSF12, TNFSF11) as the primary `[tiab]` search term and combine
  with receptor names (HVEM, TNFRSF14, LTβR) for specificity. Do NOT
  search by common name alone — the result set is almost entirely
  noise. (LIGHT/TNFSF14 profile, 2026-08-15.)
- **Dual-receptor targets with opposing downstream effects require
  pathway-selective blockade analysis.** When a ligand binds two
  receptors with opposing functions (LIGHT→HVEM is pro-inflammatory;
  LIGHT→LTβR is pro-resolving), global blockade risks harming the
  protective pathway. The profile must: (1) identify which receptor
  axis is pathogenic vs protective in the target indication; (2) note
  whether structural data (PDB structures of ligand-receptor
  complexes) enable pathway-selective inhibitor design — distinct
  binding interfaces make selective blockade structurally feasible;
  (3) include pathway-selective blockade as a field 11 differentiation
  opportunity. This pattern applies to any dual-receptor target
  (LIGHT/HVEM+LTβR, RANKL/RANK+OPG, BAFF/BAFF-R+TACI). (LIGHT/TNFSF14
  profile, 2026-08-15.)
- **PDB name collisions — always verify PDB structures via UniProt
  cross-references, not PDB title search.** A PDB title search for
  "CCR4" returns 17 hits — all are the CCR4-NOT mRNA deadenylase
  complex, a completely unrelated protein. The CCR4 chemokine
  receptor (UniProt P51679) has zero PDB structures, but a naive
  PDB title search would report 17 false positives. This is a
  generalizable pitfall for any target with a short or generic gene
  name: the abbreviation may match an unrelated protein complex
  in the PDB. Always verify PDB structure availability via the
  UniProt REST API cross-references (`uniProtKBCrossReferences`
  field, entries with `database: "PDB"`) rather than searching the
  PDB by gene name or protein name. The UniProt cross-reference is
  the authoritative source because it is manually curated to the
  correct UniProt entry; PDB title search is a keyword search over
  all deposited structures. (CCR4 profile, 2026-08-15 — 17 false
  PDB hits for "CCR4" were all CCR4-NOT complex; UniProt P51679
  correctly shows 0 PDB cross-references.)
- **UniProt JSON `molWeight` field, not `mass`.** The UniProt REST
  API JSON response stores the molecular weight in
  `sequence.molWeight` (in Daltons), not a `mass` field. Always read
  `data["sequence"]["molWeight"]` for the molecular weight value
  for field 1. (CCR4 profile, 2026-08-15 — `mass` returned N/A;
  `molWeight` returned 41403 Da.)
- **UniProt demerged/inactive entries — search by gene symbol, not
  accession.** Some UniProt accessions (e.g., Q13440 for TPBG/5T4)
  are inactive due to demerging into multiple new entries. Querying
  the inactive accession returns `"entryType": "Inactive"` with a
  `mergeDemergeTo` list but no useful data. Always verify by
  searching UniProt by gene symbol + organism:
  `rest.uniprot.org/uniprotkb/search?query=gene:{SYMBOL}+AND+organism_id:9606&format=json`
  This returns the current active entry (e.g., Q13641 for TPBG).
  (5T4/TPBG profile, 2026-08-16 — Q13440 was demerged; Q13641 is
  the correct active entry.)
- **PubMed efetch XML silently truncates abstracts with embedded HTML
  markup.** When a `<AbstractText>` element contains inline HTML
  tags (`<i>`, `<b>`, `<sup>`, `<h4>`), Python's
  `xml.etree.ElementTree` parsing silently returns only the text
  before the first nested tag — a truncated abstract (sometimes just
  the first sentence). The XML is well-formed; the issue is that
  `.text` only captures the leading text node, not the interleaved
  `<i>`/`<b>` child elements. **Fix:** use Europe PMC's REST API
  (`ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:{PMID}&resultType=core&format=json`)
  as a fallback — the `abstractText` field returns the complete
  abstract with HTML tags as raw strings. Always cross-check efetch
  abstract length against Europe PMC for papers from journals that
  use rich formatting in abstracts (JCO, JAMA Oncol, Mol Cancer
  Ther, PLoS One). (5T4/TPBG profile, 2026-08-16 — PMID 28522587
  efetch returned ~1100 chars; Europe PMC returned the full 2000+
  char abstract.)
- **ClinicalTrials.gov API v2 for structured trial data in fields 4
  and 6.** The ClinicalTrials.gov API v2
  (`clinicaltrials.gov/api/v2/studies?query.intr={TERM}&query.cond={COND}&pageSize=20&format=json`)
  returns structured data (NCT IDs, phases, statuses, interventions,
  conditions) essential for populating field 4 (antibody landscape)
  and field 6 (failure modes/success factors). Search by both
  intervention name (e.g., "TroVax", "naptumomab", "5T4") and
  target name to catch all trials. Note: `pageToken` for pagination
  uses a numeric offset string (e.g., "20"), not a cursor. For
  clinical-trial-tier targets, querying ClinicalTrials.gov is a
  required step — PubMed alone misses terminated/withdrawn trials
  and does not provide NCT IDs systematically. (5T4/TPBG profile,
  2026-08-16 — 20+ trials identified across TroVax, naptumomab,
  GEN1044, XB010, JK06, ALG.APV-527, CBA-1535, CAR-NK.)

- **Ligand absence in mice blocks preclinical development for
  costimulatory receptor targets.** When a target's primary human
  ligand is entirely absent in mice (not just sequence-divergent),
  standard mouse models are invalid — the entire receptor-ligand axis
  does not exist. CD2's primary ligand LFA-3 (CD58) is absent in mice,
  which express CD48 instead (lower affinity, also binds CD244). This
  meant alefacept (LFA-3-Ig fusion) had no cognate target in mice, and
  only human CD2 transgenic mice or non-human primates were valid
  models. For field 2 (species cross-reactivity) and field 7 (in vivo
  models), when the ligand is absent in mice, note this prominently
  and identify alternative models (transgenic, primate, or in vitro
  only). This is more severe than sequence divergence limiting
  antibody cross-reactivity — the entire biology is species-specific.
  (CD2 profile, 2026-08-15, PMID 32582179.)
- **NK cell fratricide is an on-target safety risk for IgG1
  antibodies targeting NK-expressed receptors.** When the target
  receptor is expressed on NK cells AND the antibody is IgG1 (ADCC-
  competent), the antibody coats NK cells (making them ADCC targets)
  while engaging CD16a on other NK cells (triggering killing) —
  "fratricide." Siplizumab (anti-CD2 IgG1) induces NK cell fratricide
  because NK cells express both CD2 and CD16 (PMID 33643309). For
  field 8 (safety) and field 6 (failure modes), any IgG1 antibody
  targeting a receptor on NK cells (CD2, CD16, NKp46, NKG2D, KIR)
  should be assessed for fratricide. An IgG4 (non-depleting) format
  avoids this. This generalizes to any target where the target cell
  IS the effector cell — IgG1 creates a self-depletion loop. (CD2
  profile, 2026-08-15, PMID 33643309.)
- **PubMed keyword searches for antibody approaches miss foundational
  antibody papers — trace references in comprehensive reviews to find
  them.** For targets where the dominant therapeutic modality is NOT an
  antibody (e.g., ASO, siRNA, small molecule), the key antibody
  proof-of-concept paper is often a preclinical study that does NOT
  appear in the top PubMed results for "<target> antibody" searches.
  In the ApoC-III profile, searching "ApoC-III antibody" (162 PubMed
  results) did not surface the foundational anti-apoC-III antibody
  paper (Khetarpal et al., Nat Med 2017, PMID 28825717) in the top 10
  — it was only found by reading the comprehensive review's full text
  (PMID 38039351) and tracing reference 155, then searching PubMed by
  author name ("Khetarpal APOC3 monoclonal antibody clearance") to
  retrieve the PMID. **Workflow:** (1) ingest the comprehensive review
  first and read its full text; (2) scan its reference list for
  antibody-related entries (look for "monoclonal antibody," "mAb,"
  "antibody targeting," company names); (3) for each candidate
  reference, search PubMed by first-author surname + key terms to
  resolve the PMID; (4) ingest the antibody paper as one of your 3-5
  key papers. This is especially important for secreted protein
  targets (apolipoproteins, cytokines, hormones) where oligonucleotide
  approaches dominate the literature and antibody papers are rare and
  buried. (ApoC-III profile, 2026-08-16, PMID 38039351, PMID 28825717.)
- **UniProt search by entry name can return a fragment, not the
  canonical isoform.** Searching UniProt by entry name
  (`CD44_HUMAN`) returned Q99900 (a 177-aa fragment), not P16070 (the
  742-aa canonical CD44 antigen). Always search by gene symbol +
  organism_id:
  `rest.uniprot.org/uniprotkb/search?query=gene:CD44+AND+organism_id:9606&format=json`
  and pick the entry with the correct full-length sequence length and
  the `_<GENE>_HUMAN` entry name. Multiple isoform entries may appear —
  the canonical isoform is typically the one with the longest sequence
  and the `_<GENE>_HUMAN` (not `H0Yxxx_HUMAN`) entry name. (CD44
  profile, 2026-08-16 — Q99900 is a 177-aa fragment; P16070 is the
  742-aa canonical entry.)
- **PDB search API requires POST, not GET, for JSON queries.** The RCSB
  search API (`search.rcsb.org/rcsbsearch/v2/query`) rejects GET
  requests with URL-encoded JSON — Python raises "URL can't contain
  control characters." Use a POST request with
  `Content-Type: application/json` and the JSON body as `data`:
  `urllib.request.Request(url, data=json.dumps(query).encode("utf-8"),
  headers={"Content-Type": "application/json"})`. The full-text search
  (`"type": "terminal", "service": "full_text", "parameters":
  {"value": "<query>"}`) is the simplest query form and returns PDB
  IDs; fetch titles via `data.rcsb.org/rest/v1/core/entry/<PDB_ID>`.
  (CD44 profile, 2026-08-16 — 67 PDB structures found for "CD44
  hyaluronan" via POST; GET failed with control-character error.)
- **Topic-divided PubMed search for landmark paper selection.** When
  a target spans multiple biological roles (e.g., CD44 in T cell
  activation, cancer metastasis, and cancer stem cells), search
  PubMed with separate targeted queries per topic area rather than one
  broad query. For CD44, 4 queries ("CD44 antibody", "anti-CD44
  metastasis", "CD44 hyaluronan T cell", "CD44 cancer stem cell")
  each returned 5-8 top results, from which 3 papers covering all
  topic areas were selected. This is more efficient than a single
  broad query returning hundreds of results, and ensures coverage of
  all the target's biological roles. Batch the esearch + esummary calls
  with 3-5s spacing. (CD44 profile, 2026-08-16.)
- **100% paywall rate is survivable — PubMed abstracts + UniProt + PDB
  suffice for a complete 11-field profile.** When all 3 ingested papers
  are paywalled (Elsevier/Wiley, no PMC copies, jina and Wayback both
  fail), structured PubMed abstracts (1-3K chars) combined with
  UniProt functional/domain data and PDB structural data provide enough
  grounding for all 11 fields. The CD44 profile (~42K chars, 59 PMID
  citations) was built entirely from abstracts + metadata — fields 5
  (epitope landscape) and 9 (structural information) were grounded in
  PDB structures (1POZ, 1UUH, 2I83, 32NZ, 4PZ3), and field 4 (antibody
  landscape) was grounded in clinical trial abstracts (RG7356 Phase I,
  bivatuzumab Phase I, A3D8 preclinical). This extends the
  "abstract-only is acceptable" pattern: when 100% of papers are
  paywalled, supplement abstracts with database queries (UniProt for
  function/domains/glycosylation, PDB for structures, ClinicalTrials.gov
  for trial data) rather than settling for thin fields. (CD44 profile,
  2026-08-16 — 3/3 papers abstract-only, 42K-char profile, 59 PMID
  citations across 3 ingested + 6 supplementary abstracts.)
- **High-abundance plasma targets need conformational-selective (surface-
  vs-soluble) epitope targeting to avoid the plasma sink and systemic
  toxicity.** For secreted/circulating proteins present at high plasma
  concentration (CFH ~2 µM; also complement C3, IgG, albumin-bound
  targets), a naive antibody that binds the soluble form is sequestered
  by the plasma sink (wasting dose, complicating PK) AND risks systemic
  on-target toxicity (CFH blockade → aHUS-like thrombotic
  microangiopathy). The validated design solution (GT103, anti-CFH,
  Phase 1b) is a conformational-selective antibody that recognizes a
  conformation present only on the surface-bound/disease-associated form
  (tumor-cell-associated CFH, tumor-derived exosomes) and does NOT bind
  native soluble CFH or normal tissues. For field 5 (epitope landscape)
  and field 11 (differentiation), when the target is a high-abundance
  circulating protein that deposits on cell surfaces, document: (a) the
  plasma concentration (sink magnitude); (b) whether a surface-specific
  conformational epitope has been identified; (c) whether conformational
  selectivity is the strategy to avoid systemic on-target toxicity.
  Generalizes to circulating regulators/effector proteins that change
  conformation upon surface binding (CFH, CFI, vitronectin, clusterin,
  apolipoproteins on lipoprotein particles). (CFH profile, 2026-08-17,
  PMID 36995981, PMID 39747856.)
- **Pathogenic autoantibody disease IS the pre-existing human toxicity
  profile for a blocking therapeutic antibody.** When autoantibodies
  against the target cause a recognized clinical disease, that disease
  defines the on-target toxicity ceiling of any therapeutic blocking
  antibody — the autoantibody literature is human "toxicity data" that
  exists before dosing any drug. Anti-CFH autoantibodies cause aHUS
  (thrombotic microangiopathy, AKI, ESRD); the GT103 Phase 1b saw a
  grade 3 AKI DLT at the lowest dose, matching this mechanism. For field
  6 (failure modes) and field 8 (safety), when a pathogenic autoantibody
  disease exists for the target, mine it for: the organ systems at
  risk, the clinical syndrome, the monitoring required, and the
  dose-response (autoantibody titer correlates with disease activity).
  Generalizes to CFH/aHUS, AChR/myasthenia gravis, TSHR/Graves',
  desmoglein/pemphigus, ADAMTS13/TTP. This is distinct from small-
  molecule toxicity (FGF19/bile acid) and non-autoantibody on-target
  toxicity (CD11a/PML). (CFH profile, 2026-08-17, PMID 33384694,
  PMID 39747856.)
- **Supplementary PubMed searches for the antibody landscape.** When
  the 3-5 ingested papers don't cover the clinical antibody landscape
  (common for targets where the key biological papers are reviews, not
  clinical trial reports), run additional PubMed searches for known
  antibody names (e.g., "RG7356", "bivatuzumab", "A3D8") and batch-fetch
  their abstracts. These supplementary abstracts ground field 4
  (antibody landscape) and field 6 (failure modes) with clinical trial
  data (response rates, DLTs, MTDs, discontinuation reasons) that the
  primary papers don't contain. This is distinct from the
  "batch-fetch abstracts for paywalled citation papers" pattern —
  these are papers you wouldn't have ingested anyway, but their
  clinical data is essential for the profile. (CD44 profile, 2026-08-16
  — 6 supplementary abstracts fetched for RG7356, bivatuzumab, A3D8,
  providing Phase I trial data for field 4 and fatal skin toxicity
  data for field 6/8.)
- **Ion-channel antibody targets: the "neutralizing" definition and
  paralog-redundancy efficacy ceiling.** For multi-pass transmembrane
  ion channels (Nav1.7/1.8/1.9, other VGSCs, TRP channels), an
  antibody is "neutralizing" if it **blocks ion conductance or locks
  the channel in a non-conducting conformation** (e.g., closed-state
  stabilization), NOT if it depletes cells or blocks ligand binding.
  The most attractive antibody epitopes are the **extracellular VSD
  loops** (S3–S4), which are subtype-specific and can be allosterically
  neutralizing without occluding the pore. Additionally, ion-channel
  targets with co-expressed paralogs (Nav1.7 + Nav1.8 in nociceptors)
  have an **intrinsic efficacy ceiling**: even >96% blockade of one
  paralog leaves residual firing via the sibling channel — a
  bispecific (dual-paralog) antibody may be required for complete
  blockade. Finally, rodent pain models **overestimate** ion-channel-
  target efficacy because rodent nociceptors depend more heavily on the
  target channel than human nociceptors do; use primary human DRG
  neuron electrophysiology (37°C) as the primary preclinical readout,
  not rodent behavioral models. See the Nav1.8/SCN10A and Nav1.9/SCN11A
  observation entries for the full detail. (Nav1.8 profile, 2026-08-17,
  PMID 40424150; Nav1.9 profile, 2026-08-17.)

- **2026-08-17 — Yellow fever virus E key-paper-ingestion profile
  observations.** Preclinical-tier infectious disease target. YFV E
  protein — the class II fusion glycoprotein of the prototype
  *Orthoflavivirus*, viscerotropic (hepatitis) with 5–10% CFR and
  ~200,000 cases/year. The 17D vaccine is highly effective but faces
  supply/distribution gaps; one antibody (TY014) reached Phase 1 (NEJM
  2020). Built via direct PubMed E-utilities using `urllib.request`
  (pure Python, no `curl`/`subprocess` needed). 8+ queries, 59 unique
  PMIDs, 20 key abstracts fetched via efetch XML. Abstract-only
  ingestion. UniProt P03314 (polyprotein) grounded field 1 via one
  REST call (E chain boundaries 286–778, fusion loop 383–396,
  transmembrane helices, receptor binding LRP1/LRP4/VLDLR). The WNV E
  profile (`west-nile-virus-e.md`) was loaded as the closest profiled
  homolog for format calibration and cross-flavivirus contrast. ~72.6K
  chars, 25 unique PMIDs cited. See
  `references/yellow-fever-virus-e-profile-observations.md` for full
  observations. Key new patterns:

  (1) **The cross-flavivirus DIII paradox — in vitro neutralization ≠
  in vivo protection.** The 864-cIgG antibody (DIII-specific) neutralized
  YFV 17D-204 in vitro but had zero protective capacity in the AG129
  mouse model (PMID 27126613). This directly contrasts with WNV, where
  DIII-lr antibodies (E16) are the MOST protective in vivo (hamster
  5-day post-infection therapy). Same domain, opposite in vivo outcome
  across flaviviruses. Rule: for each flavivirus E profile, explicitly
  state whether DIII antibodies are protective in vivo (not just
  neutralizing in vitro), and list DIII in vivo failure as a distinct
  field 6 failure mode with its PMID. Do not transfer DIII expectations
  from one flavivirus to another.

  (2) **The "double-lock" mechanism defines a new epitope class.** The
  5A antibody (PMID 30625326) and YD6/YD73 (PMID 36199277) bind YFV E
  in BOTH pre-fusion (dimer) and post-fusion (trimer) conformations,
  preventing both attachment AND fusion. Crystal structures solved in
  both states. This is mechanistically distinct from WNV E16
  (post-attachment fusion block only) and WNV-86 (mature-virion-
  preferential binding). For field 5, the "double-lock" class should be
  a distinct epitope classification category. For field 11, it is a
  first-in-class differentiation opportunity untested clinically for any
  flavivirus.

  (3) **Subdominant-but-vulnerable supersite — the prM-binding site.
  Antibodies targeting the prM-binding supersite (YD6, YD73) were
  "present in minute traces in YFV-infected individuals but contributed
  significantly to neutralization" (PMID 36199277) — subdominant in
  natural infection but ultra-potent therapeutically (complete
  protection as prophylactic + therapeutic). This is the inverse of the
  immunodominant fusion loop (abundant, ADE-prone). Profiling pattern
  for field 5: note immunodominance rank (dominant vs subdominant) AND
  protective value for each epitope. Subdominant-but-vulnerable sites
  are prime epitope-based vaccine design targets.

  (4) **Genotype-specific vaccine escape — structural basis for
  surveillance reevaluation.** South American YFV strains carry DII/
  DI-DII hinge mutations reducing susceptibility to 17D-vaccine-induced
  antibodies (PMID 34998466). R380 in 17D E stabilizes the virion and
  reduces fusion loop exposure; virulent strains have different
  morphology (PMID 41006244 — first high-res YFV cryo-EM). For field 3,
  genotype escape is a distinct disease-evidence block. For field 6,
  it is a structural failure mode with a defined molecular basis.
  Generalizes to all flavivirus profiles: if vaccine strain and
  circulating strains are from different genotypes, flag the genotype
  gap in fields 3, 6, and 10.

  (5) **`urllib.request` works directly — no curl subprocess needed.
  All PubMed E-utilities and UniProt REST calls used
  `urllib.request.urlopen()` from `execute_code` with no `subprocess`/
  `curl` dependency. Simpler than the two-step curl form. HTTP 429 rate
  limiting is the main risk — 3–5s sleeps between calls are required;
  10s wait + retry resolves 429s.

  (Yellow fever virus E profile, ~72.6K chars, 20 landmark abstracts
  fetched, 25 unique PMIDs cited,
  working-docs/hitlist-profiles/yellow-fever-virus-e.md.)

## Relationship to other skills

- **`target-hitlist`**: The step BEFORE profiling. Enumerates targets with
  a binary bar. The hit list feeds profiling.
- **`target-prioritization`**: Ranks viruses for mAb discovery (a different
  task). Target profiling builds the reusable fact base that multiple
  prioritization runs query with different weights.
- **`literature-dive`**: Depth-first on one topic, ingests papers,
  synthesizes into a concept page. Target profiling is broader — 11
  fields per target, no paper ingestion, working doc output. The
  literature-dive methodology (PubMed search, delegation, verification)
  is reused for the per-target literature search within profiling.

## Changelog

- **2026-08-15 — initial creation.** Built during the hit list profiling
  pilot. 5 profiles across immunology/inflammation (TNF, TL1A, CD147,
  IL-11, Siglec-8) validated the 11-field template across all tiers.
  Platform demonstration strategy (saturated first, graveyard not ideal
  for demo, blue ocean as end goal) established during the session.
- **2026-08-15 — level-2 correction + stratified sampling + delegation.**
  Bryan identified that the initial 5 profiles were built at abstract level
  (level 1) — mechanistic biology was not grounded in full-text reading.
  Level 2 (key paper ingestion: 3-5 landmark papers ingested per target)
  established as minimum rigor. Added profile rigor levels section,
  stratified random sampling pilot approach, and delegation protocol for
  key-paper-ingestion level. Platform demo section corrected: saturated
  targets validate retrospectively ("would our platform have unearthed
  winners?"), graveyard requires full preclinical workup to validate
  (unfeasible for demo). 5 pilot profiles reprocessed at level 2 with
  3 subagents dispatched for the remaining 15 targets.
- **2026-08-15 — IL-17A key-paper-ingestion profile observations.** Second
  level-2 profile (after Complement C5). 5/5 papers retrieved at 100%
  full-text rate (3 PMC OA + 2 NEJM via Wayback), vs C5's 20%. Added 5 new
  empirical observations to the key-paper-ingestion section: (1) journal mix
  drives retrieval rate — prefer OA journals and NEJM (Wayback-recoverable)
  over hard-block publishers; (2) the preclinical antibody characterization
  paper is the highest-value single paper for antibody-target profiles,
  equivalent to the structural paper for complement targets; (3) safety
  signal cross-validation across evidence types (clinical + genetics +
  review) strengthens field 8; (4) delegation with search instructions
  rather than pre-identified PMIDs is a validated, more scalable pattern;
  (5) brodalumab suicidality signal (receptor-level vs ligand-level
  blockade) is a key differentiation insight for fields 6 and 11.
  (IL-17A profile, 5,112 words, working-docs/hitlist-profiles/il-17a.md.)
- **2026-08-15 — IL-33 key-paper-ingestion profile observations.** Third
  level-2 profile (after Complement C5 and IL-17A). Clinical-trial tier,
  immunology/inflammation (COPD, asthma). 5 key papers selected, 2/5 (40%)
  full-text via PMC OA, 3/5 abstract-only (paywalled: Immunol Rev, NEJM,
  Allergy). 3 additional supporting references at abstract level (Phase 1,
  anti-ST2 Phase 2, comparative mechanism). New observations: (1) **Targets
  with multiple conformational states need special antibody-selection
  strategies.** IL-33 exists as IL-33red (ST2-binding) and IL-33ox
  (RAGE/EGFR-binding) — distinct receptor specificities from the same
  protein. Tozorakimab was selected using an oxidation-resistant IL-33C>S
  construct (cysteine→serine) to stabilize conformational epitopes; the only
  fully neutralizing antibody came from the IL-33C>S campaign, NOT from
  wild-type IL-33red. This is a generalizable lesson for targets with
  redox-sensitive or protease-sensitive conformational switches: use a
  stabilized antigen for antibody selection to preserve functionally
  relevant epitopes. (2) **The natural decoy receptor sets the affinity
  bar.** sST2 (soluble ST2) binds IL-33red at KD ~0.09 pM with ka ~1.5 × 10⁸
  M⁻¹ s⁻¹ — one of the highest-affinity interactions measured. An effective
  therapeutic antibody must exceed this affinity AND match the association
  rate. In silico modeling showed the association rate (not just KD) is the
  key driver of IL-33 suppression during acute release spikes. For any target
  with a high-affinity endogenous decoy/soluble receptor, the antibody
  engineering bar is set by the natural receptor, not by typical drug-antibody
  affinity targets. (3) **Dual-pathway antibodies create unique differentiation.
  ** Tozorakimab is the first anti-IL-33 antibody that blocks both the ST2
  and RAGE/EGFR pathways — this dual mechanism (inflammation + epithelial
  remodeling) is a structural differentiator that receptor-targeting
  antibodies (astegolimab, anti-ST2) cannot replicate. For targets with
  multiple signaling pathways (e.g., ligand-dependent + conformational
  switch), an antibody that blocks both is fundamentally differentiated from
  one that blocks a single receptor. This belongs in field 11
  (differentiation) as a mechanism differentiation insight. (4) **Combination
  therapy failure signals pathway redundancy.** Itepekimab (anti-IL-33) +
  dupilumab (anti-IL-4Rα) showed NO additive benefit — the combination did
  not significantly improve over either monotherapy. This signals that the
  IL-33 (upstream alarmin) and IL-4Rα (downstream effector) pathways are
  partially redundant. For competitive landscape (field 10) and
  differentiation (field 11), pathway redundancy between your target and
  existing approved antibodies is a key risk: if the pathway overlaps with
  an approved drug, your antibody may not add value in combination. (5)
  **Clinical-trial-tier targets benefit from including Phase 1 and
  comparator-antibody papers.** Beyond the standard 5 landmark papers (review
  + biology + lead antibody preclinical + lead antibody clinical + biology
  review), the IL-33 profile was enriched by 3 additional papers: the
  Phase 1 PK/safety paper (provided half-life, ADA, PK data for field 4), the
  anti-ST2 receptor-blocker Phase 2 (provided competitive context and
  eosinophil-low population data for field 10), and a 2025 comparative
  mechanism paper (provided pathway redundancy insight for field 6). When
  the target has multiple clinical-stage antibodies (anti-ligand AND
  anti-receptor), include both in the paper set — they reveal different
  aspects of the same pathway. (IL-33 profile, ~10,000 words,
  working-docs/hitlist-profiles/il-33.md.)
- **2026-08-15 — C5aR1 key-paper-ingestion profile observations.** Fourth
  level-2 profile (clinical-trial tier, immunology/inflammation). C5aR1
  is a class A GPCR — the first GPCR target profiled. 7 key papers
  reviewed (2 full-text via EPMC PDF render, 5 abstract-only). New
  observations: (1) GPCR targets require special epitope landscape
  handling — the orthosteric pocket is intramembrane and
  antibody-inaccessible; antibodies can only target the extracellular
  N-terminus and ECLs. Added a new GPCR target profiling considerations
  section. (2) Retracted pivotal trial papers — the ADVOCATE Phase 3
  trial (PMID 33596356) was retracted 2026-06-29 (PMID 42377355),
  discovered during identity resolution. Added a pitfall for checking
  PublicationTypeList during paper-ingest identity resolution and
  flagging retractions prominently in fields 3 and 6. (3)
  Small-molecule-approved, antibody-open competitive landscape —
  avacopan (small molecule) is the approved drug; no anti-C5aR1
  antibody is approved. This creates a distinct competitive landscape
  pattern where the target is validated but the antibody space is fully
  open. Added as a pitfall with guidance for framing fields 10 and 11.
  (4) Avdoralimab (anti-C5aR1 mAb) clinical failures — failed in
  COVID-19 (FORCE trial, negative) and inconclusive in bullous
  pemphigoid, providing antibody-specific failure mode data for field 6.
  (5) EPMC PDF render rescued 2/7 papers — JASN papers with PMCID but
  front-matter-only PMC XML were recovered via EPMC PDF render (pymupdf
  extraction), confirming the Branch 1b path documented in paper-ingest.
  (C5aR1 profile, ~30K chars, 16 PMIDs cited,
  working-docs/hitlist-profiles/c5ar1.md.)
- **2026-08-15 — CD20 key-paper-ingestion profile observations.**
  Sixth level-2 profile (saturated/approved tier, immunology + oncology).
  CD20 is the most epitope-characterized surface marker in antibody
  therapy — the Type I vs Type II distinction is the key story. 6 key
  papers selected (Cragg 2003 lipid rafts, Teeling 2006 epitope
  mapping, Beers 2010 Type I/II review, Niederfellner 2011 GA101
  crystal structure, Alduaij 2011 Type II lysosomal death, Hauser 2017
  ocrelizumab MS Phase 3). Full-text retrieval: 1/6 (17%) — only the
  Alduaij 2011 paper was retrievable (via EPMC PDF render, PMC3099571,
  63K chars). The other 5 were abstract-only (Blood, J Immunol, Semin
  Hematol, NEJM — all paywalled, no PMC, Cloudflare-blocked). New
  observations: (1) **The Type I/II framework is the most
  well-characterized epitope classification in all of antibody
  therapy.** Five distinct criteria define the classification: lipid
  raft redistribution (Type I = raft+, Type II = raft−), CDC activity
  (Type I = potent, Type II = weak), direct PCD (Type I = weak, Type II
  = potent, actin-dependent, lysosomal, nonapoptotic, BCL-2-independent),
  binding orientation/elbow angle (Type II GA101 is ~30° wider than Type
  I), and CD20 complex geometry (different oligomeric associations via
  protein tomography). No other target has this depth of epitope-mechanism
  characterization. (2) **Overlapping epitopes can produce qualitatively
  different biology.** GA101 and rituximab recognize overlapping residues
  on the CD20 large extracellular loop, yet GA101 binds in a completely
  different orientation with a wider elbow angle, creating different CD20
  oligomeric complex geometries that explain raft vs non-raft
  localization and downstream effector mechanisms. This is the structural
  proof that epitope *orientation* (not just epitope *location*) is a
  determinant of antibody function. (3) **The EPMC PDF render path
  (Branch 1b) rescued the only full-text paper.** The Alduaij 2011
  paper had `inPMC: Y` but PMC XML was front-matter only (8.9 KB);
  `europepmc.org/api/getPdf?pmcid=PMC3099571` delivered the full
  571 KB PDF (63K chars text). This confirms the Branch 1b path as
  the reliable next step after metadata-only PMC XML for papers with
  `inPMC: Y`. (4) **Abstract-only rate (83%) for this paper set is the
  worst yet** — C5 was 80%, IL-17A was 0%, IL-33 was 60%, C5aR1 was
  71%. The Blood/ASH Publications block (Cloudflare, no Wayback
  snapshot, jina blocked) is the dominant obstacle for CD20's key
  papers — 3/6 were Blood articles. (5) **Subagent delegation with
  search instructions (not pre-identified PMIDs) confirmed as
  scalable.** The CD20 task provided search query templates and topic
  coverage requirements. The subagent ran 10+ esearch queries, selected
  6 landmark papers spanning all required topics (biology/structure,
  epitope mapping, antibody mechanisms, clinical trials, crystal
  structure), and built the profile grounding fields 2, 3, 5, and 6 in
  the abstract content. (CD20 profile, ~35K chars, 294 lines, 12 PMIDs
 cited, working-docs/hitlist-profiles/cd20.md.)
- **2026-08-15 — CD4 key-paper-ingestion profile observations.** Seventh
  level-2 profile (failed-clinical/graveyard tier, immunology + infectious
  disease). CD4 is a **dual-purpose target** — the same molecule succeeded
  in one indication (HIV, ibalizumab approved) and failed in another (RA,
  multiple anti-CD4 antibodies abandoned). 17 PMIDs cited across structure,
  HIV therapy, RA failure, CTCL, and CD4 biology. New observations:
  (1) **Isotype + epitope together determine the entire therapeutic
  profile.** Ibalizumab succeeded with IgG4 (non-depleting) + D2 epitope
  (preserves CD4 immune function, blocks HIV post-attachment).
  Zanolimumab/4162W94/keliximab failed with IgG1 (depleting) + D1 epitope
  (blocks MHC II co-receptor, suppresses all T-helper responses). The
  same target, opposite outcomes — the difference is isotype and
  epitope, not target biology. For graveyard targets with a dual-
  indication track record (approved in one, failed in another), field 6
  failure analysis must explicitly compare the isotype/epitope of the
  winner vs loser to isolate format/epitope failure from target failure.
  This is the CD4 analogue of the CD20 Type I/II epitope lesson: the
  epitope determines the biology, and the isotype determines the safety.
  (2) **Depleting vs blocking is a binary safety fork for T-cell surface
  targets.** Depleting anti-CD4 antibodies (IgG1/ADCC) cause CD4
  lymphopenia, skin toxicity (4162W94: rash in 62% incl. vasculitis),
  and infection risk — an unacceptable safety profile for a chronic
  autoimmune disease. Non-depleting antibodies (IgG4/silent Fc) avoid
  these but must then rely on a blocking mechanism, which for D1
  antibodies means suppressing ALL T-helper function (mechanistic
  overkill vs anti-TNFα). The therapeutic window between "enough CD4
  depletion to suppress autoimmunity" and "so much that the patient is
  immunocompromised" is too narrow for depleting antibodies. This
  generalizes to any T-cell surface marker where the target cell is
  essential for normal immunity (CD4, CD8, CD3, CD28) — depleting
  approaches face an inherently narrow therapeutic index. (3) **Poor
  tissue penetration limits depleting antibodies in autoimmune
  disease.** Anti-CD4 antibodies cleared blood CD4+ T cells
  effectively but poorly penetrated synovial tissue — the actual
  disease site in RA. The doses needed for synovial depletion caused
  dangerous systemic immunosuppression. This is a PK/tissue-distribution
  failure specific to depleting mechanisms in solid-tissue autoimmune
  disease (RA, psoriasis, IBD) and may not apply to blood-borne
  diseases (CTCL, HIV) where the target cells are accessible. (4)
  **PubMed esummary rate-limits more aggressively than efetch.** When
  batching ~20 PMIDs through esummary.fcgi, the endpoint returned an
  85-byte JSON rate-limit body (`{"error":"API rate limit exceeded"}`)
  while efetch.fcgi (abstract text, same PMIDs in smaller batches of
  6-8) succeeded. For PubMed metadata retrieval during profiling,
  prefer efetch (rettype=abstract&retmode=text) over esummary — it
  returns structured abstracts suitable for distillation and is less
  rate-limited. Batch efetch in groups of 6-8 PMIDs with 4-5s sleeps.
  **efetch retmode pitfall (2026-08-17, influenza NA profile):**
  `retmode=json` on a multi-PMID efetch batch returned malformed JSON
  (`Extra data: line 2 column 1 (char 9)` — json.loads fails). Use
  `retmode=xml` and regex-parse the `<PubmedArticle>` blocks
  (`<AbstractText[^>]*>(.*?)</AbstractText>` after stripping inner tags)
  for reliable batch abstract retrieval. The XML path is what line 1097
  already recommends; the JSON path is a trap — do not use
  `retmode=json` for efetch multi-record batches.
  (5) **Subagent delegation with search query templates (no pre-
  identified PMIDs) confirmed as the scalable pattern.** The CD4 task
  provided the query string and topic coverage requirements (CD4
  biology, ibalizumab/HIV, zanolimumab/RA, CD4 structure, CD4 as
  therapeutic target). The subagent ran 15+ esearch queries across
  multiple topic areas, fetched abstracts in 12 batches, and selected
  17 landmark papers covering all required topics. This further
  validates the IL-17A observation: search-instruction delegation is
  more scalable than pre-identifying PMIDs for every target.
  (CD4 profile, ~40K chars, 245 lines, 17 PMIDs cited,
  working-docs/hitlist-profiles/cd4.md.)
 - **2026-08-15 — HERV-W env key-paper-ingestion profile observations.**
 Fifth level-2 profile (failed-clinical/graveyard tier, neuroscience/MS).
 HERV-W Env is a **human endogenous retroviral envelope protein** —
 a retroviral protein encoded in the human genome, not a classical
 human gene product. The only antibody (temelimab/GNbAC1, GeNeuro)
 reached Phase 2b and failed. 7 key papers reviewed (3 full-text: 1
 EPMC PDF render, 2 PMC XML; 4 abstract-only: Mult Scler, J Neuroimmunol,
 Drug Saf paywalled). New observations: (1) **Mechanism-trial-design
 mismatch is a distinct graveyard failure mode.** Temelimab's Phase 2b
 (CHANGE-MS, n=270, RRMS) failed its primary endpoint (Gd+ T1 lesion
 reduction at week 24 — an acute inflammation measure). But the drug's
 mechanism is anti-neurodegenerative: it neutralizes HERV-W Env's TLR4
 activation, which blocks OPC differentiation (remyelination failure)
 and drives chronic axonal damage — not acute lesion formation.
 Secondary neurodegenerative endpoints showed trends at 48-96 weeks
 (T1-hypointense lesions p=0.014, brain atrophy, MTR), suggesting the
 trial's 24-week anti-inflammatory endpoint was the wrong test for a
 drug whose effect requires months to manifest as structural
 neuroprotection. This is distinct from all failure modes previously
 documented (wrong epitope, wrong population, safety, format, dosing,
 retracted trials, wrong drug-target attribution) because the failure
 is in the *endpoint selection and trial duration*, not the target or
 drug. For graveyard profiles, the field 6 failure analysis must
 distinguish "target is invalid" from "trial design was wrong" — they
 have fundamentally different implications for field 11
 (differentiation). The authors themselves concluded temelimab might
 work in progressive MS (where neurodegeneration dominates), but this
 was never tested. (2) **Non-classical target classes have zero
 structural infrastructure.** HERV-W Env has no PDB structures, no
 epitope mapping, no natural animal model (human-specific endogenous
 retrovirus — the target is not expressed in animals). Fields 5
 (epitope), 7 (assay systems), and 9 (structural info) are nearly empty,
 but the cause is fundamentally different from the IL-4Rα pattern
 (competitive secrecy around a blockbuster) or the blue-ocean pattern
 (no antibody has been made yet). Here, a Phase 2b antibody exists but
 the entire structural biology of the target class is unexplored — no
 one has solved a retroviral envelope protein structure in the MS
 context. For non-classical targets (endogenous retroviral proteins,
 prion proteins, non-coding RNA-derived peptides, etc.), the absence
 of structural data is a feature of the target class, not a retrieval
 failure. (3) **Endogenous retroviral targets have a unique
 cross-reactivity liability.** Syncytin-1 (ERVWE1 locus) shares 81%
 amino acid identity with MSRV-Env and is essential for placental
 syncytiotrophoblast fusion. Temelimab's tissue cross-reactivity study
 showed placental staining at supratherapeutic concentrations — the
 basis for a pregnancy contraindication. Any anti-HERV-W Env antibody
 targeting the SU domain will face this liability because Syncytin-1
 is the only homologous human protein and it carries an essential
 physiological function. For endogenous retroviral targets broadly,
 the domesticated physiological copy (Syncytin-1, Syncytin-2, etc.)
 defines the cross-reactivity safety ceiling. (4) **Multiple
 transcribed loci complicate target validation.** NGS analysis of
 HERVW loci in CIS patients (PMID 34187540) found that MS-associated
 copies do NOT encode full-length Env protein — they are truncated,
 lack ATG codons, and/or carry frameshifts. This raises the question
 of whether the pathogenic moiety is full-length MSRV-Env (which
 temelimab was designed against) or a fragment/partial product. For
 multi-locus endogenous retroviral targets, target validation must
 address which protein species is actually expressed and pathogenic
 in disease tissue. (HERV-W env profile, ~4,200 words, 11 PMIDs
 cited, working-docs/hitlist-profiles/herv-w-env.md.)
- **2026-08-15 — IL-7Rα key-paper-ingestion profile observations.**
 Seventh level-2 profile (failed-clinical/graveyard tier,
 immunology/inflammation, T1D + oncology). IL-7Rα is the receptor for
 IL-7, the master T cell survival/proliferation cytokine. The defining
 clinical antibody (PF-06342674/RN168, Pfizer, humanized IgG1)
 completed Phase Ib in T1D but the program was discontinued — no Phase
 II conducted. A second-generation antibody (lusvertikimab/OSE-127,
 IgG4) is now in Phase 2 for UC and Sjögren's. 5 key papers ingested
 (3 PMC XML full text, 1 EPMC PDF render, 1 abstract-only — Nature
 Immunology paywalled). New observations: (1) **Non-monotonic
 dose-response is a distinct graveyard failure mode for
 immunomodulatory antibodies.** RN168's Treg:TEM ratio — the proposed
 PD biomarker — peaked at ~3 mg/kg Q2W and *declined* at higher doses
 because Tregs (which express low but non-zero IL-7Rα) were also
 depleted. The maximal effective dose coincided with maximal receptor
 occupancy — there was no pharmacological headroom. This is distinct
 from "wrong dose" (subtherapeutic) or "narrow therapeutic index"
(toxicity-limited): the dose-response curve *inverts* for the desired
 PD effect. For immunomodulatory antibodies targeting receptors
 expressed on both effector and regulatory T cells, the dose-response
 for the regulatory:effector ratio is inherently non-monotonic, and
 the peak may coincide with receptor saturation — leaving no room to
 overcome immunogenicity or inter-individual variability. Always
 model the full dose-response curve for the *ratio* biomarker, not
 just the absolute cell counts. (2) **Human genetic validation does
 not guarantee clinical success — target validity ≠ therapeutic
 feasibility.** IL7R is one of the strongest non-HLA GWAS loci for MS
 (rs6897932, functional mechanism via splicing → sIL7R → enhanced
 IL-7 bioavailability, epistasis with DDX39B), and is also associated
 with T1D. Yet the clinically validated target with an excellent
 preclinical package (NOD mouse reversal) and strong human genetics
 still failed because the *therapeutic window was too narrow* — not
 because the target was wrong. For graveyard profiles, field 6 must
 distinguish "target is biologically invalid" (the biology was wrong)
 from "target is valid but therapeutically infeasible" (the biology
 was right but the drug/target interaction couldn't be dosed safely).
 The latter has a fundamentally different implication for field 11:
 a new antibody with a different format or epitope may reopen the
 target — the genetics provide the validation, the format provides
 the feasibility. (3) **IgG1 → IgG4 format switch addresses effector-
 function-mediated toxicity, not the core pharmacology.** Lusvertikimab
 (IgG4, no ADCC/CDC) showed dramatically cleaner Phase 1 safety (63
 volunteers, no lymphopenia, no T cell subset changes) vs RN168 (IgG1,
 memory T cell depletion, EBV/CMV reactivation at high doses). The IgG4
 format eliminates the effector-function-driven Treg depletion that
 narrowed RN168's window. But the core pharmacology (IL-7Rα blockade
 → memory T cell depletion) is format-independent — the question is
 whether the IgG4 format widens the window enough for clinical efficacy
 in autoimmunity, or whether the non-monotonic dose-response is an
 intrinsic property of IL-7Rα blockade. For graveyard profiles where
 the failure is format-related (IgG1 effector function), the IgG4
 format switch is the key differentiation opportunity (field 11), but
 the profile should note that format alone may not rescue a target
 whose core pharmacology has a narrow window. (4) **Two epitope bins
 with distinct mechanisms.** RN168 blocks IL-7 binding (competes with
 cytokine); lusvertikimab blocks IL-7Rα/γc heterodimerization (binds
 site-1/site-2b, prevents receptor assembly). The heterodimerization
 blocker also spares TSLP receptor signaling (selectivity over the
 TSLPR complex) — a specificity advantage the cytokine-blocking
 antibody cannot claim. For targets that are shared subunits of
 multiple receptor complexes (IL-7Rα is in both IL-7R and TSLPR),
 epitope selection can determine pathway selectivity, not just binding
 affinity. When filling field 5 (epitope landscape) for shared
 receptor subunits, map each epitope bin to which receptor complexes
 it blocks vs spares — this is a higher-value epitope distinction
 than neutralizing vs non-neutralizing alone. (IL-7Rα profile,
 ~31K chars, 5 papers, 5 PMIDs cited,
 working-docs/hitlist-profiles/il-7ra.md.)
 - **2026-08-15 — Properdin key-paper-ingestion profile observations.**
 Eighth level-2 profile (preclinical/blue ocean tier,
 immunology/inflammation, complement alternative pathway). Properdin
 (CFP) is the only known positive regulator of the complement system —
 all other regulators are negative (Factor H, Factor I, CD55, CD46,
 CD59). 5 key papers ingested (4 full text: 3 PMC XML, 1 EPMC PDF render;
 1 abstract-only — the 1988 Lancet deficiency paper with no abstract or
 PMCID at all). New observations: (1) **Task brief UniProt IDs can be
 wrong.** The brief listed P05155 (C1 inhibitor/SERPING1) instead of
 P27918 (properdin/CFP) — two different complement proteins. Caught by
 querying the UniProt REST API by gene symbol. Added as a pitfall: always
 verify UniProt IDs from upstream sources against the gene symbol before
 populating field 1. This is the UniProt analogue of the paper-ingest
 seed-identifier gate. (2) **Blue ocean profiles are carried by
 mechanistic biology, not antibody data.** Fields 4 (antibody landscape)
 and 5 (epitope landscape) for properdin contain only preclinical tool
 antibodies (mAb 14E1, anti-TSR5–6 pAbs) and non-antibody inhibitors
 (CirpA1 tick protein, polysialic acid) — no approved or clinical-stage
 antibodies exist. But fields 2 (biological mechanism), 3 (disease
 evidence), and 11 (differentiation) are rich: properdin is the sole AP
 positive regulator, its inhibition selectively blocks AP amplification
 while preserving classical/lectin pathways (unique mechanism no other
 complement inhibitor offers), and its low plasma concentration (4–25
 μg/mL vs C5 at 75 μg/mL) is a dosing advantage. The blue ocean value
 proposition IS the mechanistic differentiation. (3) **The EPMC PDF
 render path (Branch 1b) rescued an EMBO J paper with front-matter-only
 PMC XML.** PMID 28264884 (EMBO J 2017, structural paper) had `inPMC: Y`
 but PMC XML was front-matter only (15.7 KB, no body). The EPMC PDF
 render (`europepmc.org/api/getPdf?pmcid=PMC5391138`) delivered the full
 4.7 MB PDF, extracted to 30K chars of full text containing the complete
 structural data (E244K deficiency, FPc convertase complex, SAXS
 structures). This is the same Branch 1b path confirmed in the C5aR1 and
 CD20 profiles — it is now 3/3 for EMBO J and JASN papers. (4) **Very
 old papers (pre-1990) may have no abstract and no PMCID.** PMID 2891989
 (Lancet 1988, properdin deficiency) has no abstract text, no PMCID, no
 DOI — the PubMed abstract text endpoint returns only the citation
 header. Such papers are still citable for landmark findings (this is
 the original properdin deficiency report) but cannot be ingested as
 paper pages. Cite them as key references in the profile without
 attempting full-text ingestion. (5) **UniProt REST API provides domain
 architecture and glycosylation data for field 9.** The UniProt JSON API
 (`rest.uniprot.org/uniprotkb/P27918?format=json`) returns structured
 feature data: 7 TSR domain boundaries (TSR0–TSR6 with residue ranges),
 glycosylation sites (14 C-mannosylation sites, N-glycosylation), and
 disulfide bond patterns. This is a free, fast single-call source for
 field 1 (key domains) and field 9 (structural information) that should
 be part of every profile's initial data gathering. (Properdin profile,
 ~45K chars, 5 papers + 6 additional references, 16 PMIDs cited,
 working-docs/hitlist-profiles/properdin.md.)
 - **2026-08-15 — LIGHT/TNFSF14 key-paper-ingestion profile observations.**
 Ninth level-2 profile (preclinical/blue ocean tier,
 immunology/inflammation). LIGHT is a TNF superfamily member with
 dual-receptor signaling (HVEM and LTβR). 5 key papers reviewed (3
 PMC XML full text, 2 abstract-only). 17 PMIDs cited total. New
 observations: (1) **"LIGHT" as a PubMed search term matches 340K
 papers (illumination, light chains, etc.) — always use the gene
 symbol TNFSF14 as the primary search term and combine with HVEM or
 TNFRSF14 for receptor-specific queries.** A title/abstract search
 for "LIGHT" returns almost entirely irrelevant results; `[tiab]`
 field-tagged TNFSF14 queries produce clean, specific result sets.
 This is the most extreme generic-name collision observed across all
 targets profiled. For any target whose common name is a generic
 English word (LIGHT, APRIL, TWEAK, TRANCE, RANK), always search by
 gene symbol as the primary term. (2) **Dual-receptor targets with
 opposing downstream effects create a "pathway-selective blockade"
 differentiation opportunity.** LIGHT-HVEM drives costimulation and
 pro-inflammatory signaling (pathogenic in IBD, dermatitis), while
 LIGHT-LTβR drives tissue repair, lymphoid organization, and
 inflammation resolution (protective). Global LIGHT blockade risks
 disrupting protective LTβR functions AND enhancing BTLA-HVEM
 inhibitory signals that suppress anti-tumor surveillance. The key
 field 11 differentiation insight: a pathway-selective antibody
 (blocking LIGHT-HVEM while sparing LIGHT-LTβR) is structurally
 enabled because LIGHT binds HVEM at CRD2/CRD3 and LTβR at a distinct
 interface — PDB 4RSU provides the structural basis for selective
 inhibitor design. This pattern generalizes to any dual-receptor
 target where one receptor axis is pathogenic and the other is
 protective. (3) **A single Phase 2 clinical trial can put a blue
 ocean target on the map.** LIGHT was a pure preclinical target
 until CERC-002 (Avalo Therapeutics) showed a positive Phase 2
 signal in COVID-19 ARDS (83.9% vs 64.5% alive/respiratory
 failure-free, P=0.044, PMID 34871182). This shifted the target from
 "no clinical data" to "clinical proof of concept in one
 indication" while the primary intended indication (Crohn's) had
 only a terminated Phase 1b. For blue ocean profiles, even a single
 positive trial in an adjacent indication can anchor the antibody
 landscape (field 4) and safety profile (field 8) — always search
 for clinical trial evidence in indications beyond the target's
 primary therapeutic area. CERC-002 was discovered via an
 `anti-LIGHT[tiab] AND (antibody OR antagonist OR inhibitor)[tiab]`
 query, not the primary TNFSF14 biology query. (4) **Soluble
 recombinant LIGHT requires a foldon trimerization domain for
 bioactivity — Fc-fusion alone produces inactive protein.** This
 is the only TNF superfamily member observed where the standard
 Fc-fusion approach fails. For any agonist approach to LIGHT
 (oncology immunotherapy), the foldon domain is mandatory, and this
 complicates antibody-based agonist strategies. Record
 trimerization requirements in field 9 (structural information)
 for any TNF superfamily target. (5) **EPMC rate-limiting (429)
 during multi-query PubMed searches can require 15s backoff.**
 Running 5+ sequential esearch queries in rapid succession triggered
 a 429 that cleared only after a 15s wait. The paper-ingest skill
 documents 3-5s sleeps between sequential E-utilities calls; for
 profiling workflows that run 10+ queries to identify landmark
 papers across multiple topic areas, 5s sleeps are the minimum and
 429 recovery requires 15s. Batch esummary calls (20 PMIDs per call)
 to minimize sequential request count. (LIGHT profile, ~25K chars,
 237 lines, 17 PMIDs cited,
 working-docs/hitlist-profiles/light.md.)
- **2026-08-15 — BCMA/TNFRSF17 key-paper-ingestion profile observations.**
  Eleventh level-2 profile (saturated/approved tier, immunology/oncology).
  BCMA is the **first multi-modality approved target** profiled — 4 approved
  therapies spanning 3 distinct modalities: belantamab mafodotin (ADC),
  idecabtagene vicleucel (CAR-T), ciltacabtagene autoleucel (CAR-T),
  teclistamab (bispecific). 5 key papers ingested (2/5 full text via PMC
  XML: a J Hematol Oncol review + a NEJM trial with inPMC:Y; 3/5
  abstract-only: Lancet Oncol, NEJM, Lancet — all paywalled, no PMCID).
  ~42K chars, 357 lines, 20+ PMIDs cited. New observations:
  
  (1) **Multi-modality targets require a modality comparison matrix in
  field 4 and field 6.** When 3+ distinct therapeutic modalities (ADC,
  CAR-T, bispecific) are all approved for the same target, the profile
  must compare them head-to-head on: ORR (belantamab 31% vs ide-cel 73%
  vs cilta-cel 97% vs teclistamab 63%), logistical access (ADC/bispecific
  = off-the-shelf vs CAR-T = apheresis + manufacturing wait), safety
  profile (ADC keratopathy vs CAR-T/bispecific CRS/neurotoxicity), and
  durability (CAR-T longer DOR vs bispecific/ADC shorter PFS). The
  modality comparison is the single most valuable content for field 6
  (failure/success modes) and field 11 (differentiation) — each modality
  has distinct strengths and weaknesses that a new antibody must
  differentiate against. For field 6, the belantamab US withdrawal
  (DREAMM-3 failed vs evolving SOC) is a trial-design failure mode
  distinct from target failure — the drug was withdrawn not because
  BCMA was wrong, but because the single-agent comparator trial design
  couldn't keep pace with the rapidly evolving standard of care.
  Subsequent combination Phase 3 trials (DREAMM-7, DREAMM-8) showed
  positive OS, confirming the target remained valid. This is the
  multi-modality analogue of the HERV-W "mechanism-trial-design
  mismatch" pattern: the failure is in trial design, not the target.
  
  (2) **Soluble target antigen (sBCMA) interference is a unique
  target-level challenge.** BCMA is cleaved by gamma-secretase to
  produce soluble BCMA (sBCMA), which can sequester anti-BCMA antibodies
  and reduce cell-surface target density — directly inhibiting therapy
  efficacy. This is the first target profiled where the target's own
  shedding product creates a pharmacodynamic escape mechanism. For
  field 6 (failure modes) and field 11 (differentiation), this creates
  a unique opportunity: (a) gamma-secretase inhibitors (GSI) can
  increase surface BCMA and reduce sBCMA, enhancing all BCMA therapies
  — a GSI+antibody combination is a differentiated approach; (b) an
  antibody epitope that discriminates between membrane BCMA and sBCMA
  could avoid sequestration — a "protective" antibody mechanism
  analogous to the FasL Nok2 pattern. For any target with a soluble
  shed form (sBCMA, sIL-6R, sVEGFR, etc.), the shed antigen's
  interference with therapy should be analyzed in field 6 and a
  GSI-combination or epitope-selective approach considered in field 11.
  
  (3) **Bi-epitope vs single-epitope CAR-T design correlates with
  efficacy.** Cilta-cel (two BCMA-targeting single-domain antibodies,
  bi-epitope design) achieved ORR 97% vs ide-cel (single murine scFv)
  ORR 73%. While cross-trial comparisons are confounded by patient
  population differences, the bi-epitope design may contribute through
  higher avidity or broader epitope coverage. This is the first CAR-T
  epitope-structure-efficiency relationship observed in target
  profiling — for field 5 (epitope landscape), when multiple CAR-T
  products target the same antigen, compare their scFv/single-domain
  antibody architecture and correlate with clinical outcomes. This
  insight also applies to bispecific antibody design (bivalent vs
  monovalent target-binding arm).
  
  (4) **The entire pipeline ran via `execute_code` + urllib — no
  terminal, no browser.** PubMed esearch/esummary/efetch, Europe PMC
  core records, PMC XML efetch, jina reader proxy, UniProt REST API —
  all fetched via Python `urllib.request` inside `execute_code`. Paper
  pages written via `write_file`. PMC XML parsed via
  `subprocess.run` calling the skill's `pmc_xml_body_parser.py`. This
  confirms the paper-ingest skill's documentation of `execute_code` as
  the primary terminal-curl fallback: the full paper-ingest pipeline
  (identity -> full-text -> distillation -> page write) runs end-to-end
  through `execute_code`. For delegated profiling subagents, this is
  the standard execution path — no terminal or browser needed.
  
  (5) **UniProt REST API confirmed as standard initial data gathering.**
  UniProt Q02223 provided: 184 aa, 20.2 kDa, type III transmembrane
  topology (extracellular aa 1-54, TM aa 55-77, cytoplasmic aa 78-184),
  three disulfide bonds (C8-C21, C24-C37, C28-C41), FUNCTION and TISSUE
  SPECIFICITY comments, and 11 PDB cross-references (1OQD, 1XU2, 2KN1,
  4ZFO, 6J7W, 8HXQ, 8HXR, 8QY9, 8QYA, 8QYB, 9MQO). This is now 3/3
  profiles (Properdin, FasL, BCMA) confirming the UniProt API as a
  reliable single-call source for fields 1 and 9 — it should be a
  mandatory step in every profile's initial data gathering.
  
  (BCMA profile, ~42K chars, 357 lines, 5 papers, 20+ PMIDs cited,
  working-docs/hitlist-profiles/bcma.md.)

- **2026-08-15 — CD11a/ITGAL key-paper-ingestion profile observations.**
  Twelfth level-2 profile (approved/withdrawn — GRAVEYARD tier,
  immunology/inflammation, psoriasis). CD11a is the alpha subunit of
  LFA-1 (leukocyte function-associated antigen-1, αLβ2 integrin),
  mediating T cell adhesion and trafficking via ICAM-1/2/3. Efalizumab
  (Raptiva, anti-CD11a, humanized IgG1) was approved for psoriasis in
  2002 and withdrawn in April 2009 after 3 confirmed PML cases. 5 key
  papers ingested (1/5 full text via PMC XML — the Tan & Koralnik 2010
  Lancet Neurol PML review, PMC2880524, 38K chars, 30 sections; 4/5
  abstract-only — Elsevier, Wiley, JAMA, Bentham Science all blocked).
  ~27.5K chars, 43 PMID citations. New observations:
  
  (1) **On-target, mechanism-based toxicity is a distinct graveyard
  pattern for immune-trafficking targets.** The PML risk is
  target-specific, not antibody-specific: blocking LFA-1–mediated T
  cell trafficking impairs CNS immune surveillance against JC virus —
  any systemic LFA-1 blocker will cause this. The same mechanism affects
  natalizumab (anti-α4 integrin), confirming it's a class effect of
  disrupting leukocyte trafficking, not specific to the efalizumab
  antibody. For field 6, the critical analysis is whether the failure is
  target-specific or antibody-specific, and whether the toxicity is an
  on-target consequence of the therapeutic mechanism (efficacy and
  toxicity share the same mechanism). For field 11, no format change
  addresses mechanism-based toxicity — the root cause is the target
  biology, not the antibody format.
  
  (2) **IRIS upon drug removal creates a therapeutic dilemma.** Two
  efalizumab PML cases treated with plasma exchange developed IRIS and
  died — removing the drug to restore immune surveillance triggered
  inflammatory brain destruction. This is a distinct failure mode for
  trafficking-blocker antibodies: the reversibility of the blockade
  itself becomes a safety risk. For field 8, note whether the antibody's
  mechanism is reversible and whether reversibility carries risks.
  
  (3) **Cross-class PML risk for T cell trafficking blockers is a
  shared safety ceiling.** PML affects natalizumab (anti-α4),
  efalizumab (anti-CD11a), and rituximab (anti-CD20) through different
  primary mechanisms but the shared downstream effect of disrupting
  CNS immune surveillance. JCV serostatus is a validated risk
  stratification biomarker (proven for natalizumab) and should be
  considered for any trafficking-blocker program.
  
  (4) **Two new publisher blocks documented.** JAMA Network
  (jamanetwork.com) — Cloudflare CAPTCHA on all URL variants, no
  Wayback snapshots, genuinely unreachable. Bentham Science
  (eurekaselect.com/ingentaconnect.com) — Cloudflare CAPTCHA on jina,
  and Wayback CDX returned a 200-status snapshot whose content was a
  *completely different article* (Alzheimer's paper instead of LFA-1
  review). This is a new Wayback failure mode: always validate CDX-
  fetched content against the paper title before distillation. Both
  added to the paper-ingest known-blocks table.
  
  (CD11a profile, ~27.5K chars, 5 papers, 43 PMID citations,
  working-docs/hitlist-profiles/cd11a.md.)

- **2026-08-15 — FasL/CD95L key-paper-ingestion profile observations.**
  Tenth level-2 profile (preclinical/blue ocean tier,
  immunology/inflammation + oncology). FasL (FASLG, TNFSF6) is the
 canonical death-inducing ligand of the TNF superfamily — binds Fas
 (CD95/TNFRSF6) to trigger apoptosis via FADD→caspase-8. 14 key
 papers reviewed across 6 topic areas (biology, non-apoptotic
 signaling, GVHD, transplantation, glioblastoma clinical, ALPS
 genetics, reverse signaling, immune privilege, cancer immunotherapy).
 4/14 papers (29%) retrieved full text (3 PMC XML OA + 1 PMC XML
 older JEM paper); 10/14 abstract-only. 20 unique PMIDs cited. New
 observations: (1) **Block-vs-agonize directionality is a new
 target-class pattern for death receptor ligands.** FasL is unique
 among profiled TNF superfamily targets because the therapeutic
 direction (block vs. agonize) depends on the disease: blockade for
 GVHD (APG101 prevents GVHD while preserving GVT, PMID 23203823),
 blockade for glioblastoma invasion (asunercept Phase II, PMID
 25338498), agonism for cancer (anti-Fas agonistic antibodies kill
 Fas+ tumor cells, but lethal hepatotoxicity prevents systemic
 use), and a novel "protective" mechanism for CAR-T enhancement
 (anti-FasL antibodies that protect FasL from plasmin cleavage,
 preserving bystander killing, PMID 40593750). No single antibody can
 serve all directions — the profile must explicitly state which
 direction(s) apply and why. For field 6 (failure modes) and field
 11 (differentiation), the directionality question IS the central
 analysis: blocking antibodies risk pharmacological ALPS
 (lymphoproliferation from failed AICD), agonistic antibodies risk
 lethal hepatotoxicity (Fas on hepatocytes), and protective
 antibodies are a novel, unvalidated mechanism. This pattern will
 recur for any death receptor ligand (FasL, TRAIL, TWEAK) where the
 ligand's function is beneficial in one context (tumor killing,
 immune regulation) and harmful in another (tissue destruction,
 autoimmunity). (2) **"Protective" antibodies are a novel mechanism
 class beyond neutralizing, agonistic, and depleting.** The Nok2/
 Nok2h anti-FasL antibodies (PMID 40593750) do NOT neutralize FasL
 — they bind a conformational epitope that blocks plasmin cleavage
 at the human-specific 144RK145 site, preserving FasL's
 cell-killing function on CAR-T cells. This is fundamentally
 different from all antibody mechanisms previously documented in
 target profiles: neutralizing (block ligand-receptor interaction),
 agonistic (stimulate receptor), depleting (kill target cell via
 ADCC/CDC), reverse-signaling-modulating (trigger intracellular
 signal in ligand-expressing cell). "Protective" antibodies
 stabilize/protect the target from degradation while preserving
 its function. For field 11 (differentiation), this opens a
 mechanism dimension not previously considered: the antibody's
 relationship to the target's function can be protective
 (preserve/enhance), not just inhibitory or stimulatory. This may
 apply to other targets with protease-sensitive active forms
 (TNF, RANKL, VEGF — all have protease cleavage that modulates
 activity). (3) **Human-specific evolutionary substitutions can
 invalidate mouse preclinical models for certain mechanisms.**
 Human FasL has Ser153 (evolved from the primate Pro153), which
 creates a plasmin cleavage site (144RK145) absent in all nonhuman
 primates and mice. This means mouse FasL is NOT cleaved by plasmin,
 and mouse models do not recapitulate the human FasL regulatory
 dynamics that underlie the "protective" antibody mechanism. For
 field 2 (species cross-reactivity) and field 7 (in vivo models),
 note when a human-specific post-translational modification or
 cleavage site creates a species-dependent regulatory mechanism —
 human knock-in mice (human FasL expressing) are required, not
 wild-type mice. This generalizes to any target where a
 human-specific sequence variant creates a protease-sensitive
 regulatory site (check UniProt for human-specific substitutions
 vs. nonhuman primates). (4) **UniProt JSON cross-references are
 the reliable PDB structure discovery path when the RCSB search API
 fails.** The RCSB search API (search.rcsb.org/rcsbsearch/v2/query)
 returned HTTP 400 for both POST and GET requests with various
 query formats. The UniProt REST API
 (`rest.uniprot.org/uniprotkb/<accession>.json`) carries PDB
 cross-references in the `uniProtKBCrossReferences` field — each
 entry has `database: "PDB"`, the PDB ID, method (X-ray, cryo-EM),
 resolution, and chain mappings. This is a free, fast, reliable
 single-call source for field 9 (structural information) that
 should be part of every profile's initial data gathering, alongside
 the domain/glycosylation data already documented in the Properdin
 observations. Three FasL PDB structures (4MSV, 5L19, 5L36) were
 discovered this way. (5) **PubMed esearch via urllib requires
 URL-encoding the entire query string with `urllib.parse.quote(q,
 safe='')`.** Unlike curl (where double-quotes protect the URL),
 Python's `urllib.request.urlopen` rejects URLs containing spaces
 ("URL can't contain control characters"). The fix:
 `urllib.parse.quote(query_string, safe='')` URL-encodes spaces,
 brackets, and all special characters in the PubMed search term
 before constructing the esearch URL. This is the Python equivalent
 of the paper-ingest skill's bracket-encoding rule for curl URLs.
 (FasL profile, ~53K chars, 308 lines, 20 PMIDs cited,
 working-docs/hitlist-profiles/fasl.md.)
 - **2026-08-15 — BAFF/BLyS key-paper-ingestion profile observations.**
 Eleventh level-2 profile (approved tier, immunology/inflammation,
 SLE + lupus nephritis). BAFF (TNFSF13B) is a TNF superfamily ligand
 with three receptors (BAFF-R, TACI, BCMA) — the first approved-target
 profile where the ligand itself (not a receptor) is the drug target.
 5 key papers ingested (2 PMC OA, 1 jina reader via Lancet direct URL,
 1 Wayback via CDX API fallback, 1 abstract-only — 80% full-text
 rate). 12 PDB structures identified via UniProt API (highest
 resolution: 1KXG at 2.0 Å). New observations: (1) **Pharmacodynamic
 activity without clinical efficacy is a distinct failure mode for
 BAFF-targeting antibodies.** Tabalumab (IgG4, Eli Lilly) failed two
 Phase 3 SLE trials (ILLUMINATE-1/2) despite clear biological activity
 — reductions in anti-dsDNA, increases in C3/C4, reductions in B cells
 and immunoglobulins — all consistent with BAFF pathway engagement.
 The SRI-5 endpoint was not met (31.8% Q2W and 35.2% Q4W vs 29.3%
 placebo, no significant difference). This is distinct from "wrong
 target" (belimumab succeeded with the same target) and "wrong
 mechanism" (both antibodies neutralize BAFF). The failure suggests
 that either the endpoint was too stringent, the population was not
 optimally selected, or binding membrane BAFF (which tabalumab does
 but belimumab does not) provides no additional therapeutic benefit
 and may paradoxically interfere with normal immune function. For
 field 6 (failure modes), PD-activity-without-clinical-efficacy is a
 unique failure pattern: the drug hit the target, the target was
 validated (by belimumab's success), and yet the clinical outcome was
 negative — the explanation lies in endpoint design, population
 selection, or the soluble-vs-membrane targeting distinction, not in
 target validity. (2) **Soluble-only vs. soluble+membrane targeting
 is an unexplored differentiating axis for anti-ligand antibodies.**
 Belimumab (approved) binds only soluble BAFF; tabalumab (failed)
 binds both soluble and membrane BAFF. This is the only profiled
 target where two anti-ligand antibodies with different binding
 selectivity (soluble-only vs. soluble+membrane) have reached Phase 3
 with opposite outcomes. Whether this distinction is causally related
 to the differential clinical outcomes is not established — but it is
 the most prominent unexplained difference between the winner and the
 loser, and no published study has resolved it mechanistically. For
 field 5 (epitope landscape), the soluble-only vs. soluble+membrane
 distinction maps to epitope accessibility: the stalk region (which
 is present in membrane BAFF but absent from soluble BAFF after
 furin cleavage) is the structural basis for the difference. An
 antibody targeting the THD alone would bind both forms; an antibody
 requiring the stalk for binding would be soluble-specific. No
 published co-crystal structures exist for either belimumab or
 tabalumab — a significant gap. (3) **Fc-fusion decoy receptors
 represent a parallel competitive landscape alongside antibodies.**
 Atacicept (TACI-Fc), telitacicept (TACI-Fc, approved in China), and
 povetacicept (engineered TACI-Fc) are not antibodies but compete in
 the same target space — they sequester BAFF (and APRIL) by acting
 as soluble receptor decoys. For field 4 (antibody landscape) and
 field 10 (competitive landscape), include Fc-fusion decoys alongside
 antibodies: they are the same therapeutic class (protein
 biologics targeting the same ligand), even though they are not
 monoclonal antibodies. Povetacicept's engineered TACI domain with
 enhanced binding to both BAFF and APRIL represents a "next-
 generation" dual inhibitor that outperforms wild-type TACI-Fc
 preclinically — the class is evolving beyond antibody and first-
 generation decoy formats. (4) **UniProt API provides domain,
 glycosylation, transmembrane, and PDB cross-reference data in a
 single call for field 1 and field 9.** The UniProt REST API
 (`rest.uniprot.org/uniprotkb/<accession>.json`) returns structured
 features (topological domains, transmembrane regions, glycosylation
 sites, domain boundaries) and PDB cross-references (with method and
 resolution) in one JSON response. This is the fastest path to
 populate field 1 (key domains, MW, localization) and field 9
 (structural information, PDB IDs, glycosylation). Confirmed across
 multiple profiles (Properdin, FasL, BAFF) — this should be a
 standard step in every profile's initial data gathering. (5)
 **Targets with multiple conformational/oligomeric states may offer
 unique epitope differentiation opportunities.** BAFF forms trimers
 (the active form) that can further assemble into virus-like 20-mers
 (60-mers), which may enhance receptor crosslinking and signaling.
 An antibody targeting the 20-mer assembly interface (PDB 4V46)
 could differentially modulate BAFF signaling strength — an
 unexplored epitope space not addressed by any current antibody.
 This generalizes to any target with higher-order oligomeric states
 (TNF superfamily members, complement proteins): the oligomeric
 assembly interface is a structurally distinct epitope that
 monomer-targeting antibodies miss. (BAFF/BLyS profile, ~34K chars,
 4.7K words, 5 papers + 6 supporting references, 15+ PMIDs cited,
 working-docs/hitlist-profiles/baff-blys.md.)
- **2026-08-15 — CCR4 key-paper-ingestion profile observations.**
  Twelfth level-2 profile (saturated/approved tier,
  immunology/oncology). CCR4 is the **first approved-tier GPCR +
  Treg-depletion target** profiled — combining the GPCR structural
  challenges (from C5aR1) with the Treg-depletion biology (from CCR8)
  in a single approved antibody (mogamulizumab/KW-0761, Kyowa Kirin).
  5 key papers ingested (3/5 PMC XML full text — Solari 2015, Jones
  2026, Fujikawa 2023; 1/5 jina reader — Kim 2018 MAVORIC Lancet
  Oncol; 1/5 abstract-only — Ishii 2010 Clin Cancer Res, AACR
  CAPTCHA block). ~34K chars, 229 lines, 5 unique PMIDs cited. New
  observations: (1) **PDB name collisions — a naive PDB title search
  for "CCR4" returns 17 hits, all the CCR4-NOT mRNA deadenylase
  complex (unrelated protein); the CCR4 chemokine receptor has zero
  PDB structures. Always verify via UniProt cross-references.**
  Added as a pitfall. (2) **Afucosylation (POTELLIGENT technology) IS
  the therapeutic mechanism, not an optimization.** Mogamulizumab's
  defucosylated Fc (~7% fucose) enhances FcγRIIIa binding, making
  ADCC the primary killing mechanism. ADCC potency was determined by
  NK cell effector numbers, not CCR4 target density (PMID 20160057).
  This is the approved-tier confirmation of the CCR8 Treg-depletion
  observation: for depletion targets, Fc effector function IS the
  therapeutic mechanism — afucosylated Fc is the baseline requirement,
  not an optimization. (3) **CCR4 gain-of-function mutations are a
  predictive biomarker that increases target density.** ~25% of ATLL
  patients harbor CCR4 mutations that impair internalization, trapping
  CCR4 on the cell surface. Mutated patients had 5-year OS 72.2% vs
  26.2% (non-mutated) with mogamulizumab (PMID 42305457). This is the
  first target profiled where a gain-of-function mutation directly
  increases the antibody's target antigen density — a
  target-density-increasing biomarker, distinct from
  expression-level biomarkers. (4) **Concurrent CD8+ T cell depletion
  limits Treg-depletion efficacy in solid tumors.** In the
  Fujikawa Phase Ia/Ib trial (PMID 37729184), KW-0761 depleted both
  eTregs AND central memory CD8+ T cells (which also express CCR4).
  At low doses (0.1 mg/kg), CD8+ T cells were less affected than
  eTregs; at high doses (1.0 mg/kg), both were equally impaired. This
  is a target-expression-specificity problem: CCR4 is not exclusively
  expressed on Tregs. Dose optimization (lower doses) or
  Fc-engineering for high-CCR4-density targets (eTregs express very
  high CCR4) could improve selectivity. This extends the CCR8
  Treg-depletion observations to the approved-tier setting: the
  dual-depletion problem is not unique to CCR8. (5) **Lancet Oncol
  jina reader proxy succeeds on the direct publisher URL.** The
  MAVORIC trial (PMID 30100375) was retrieved via jina on the direct
  thelancet.com URL (89K chars), despite Lancet DOIs containing
  parentheses. This confirms the paper-ingest skill's Lancet entry:
  use `fetch_fulltext.py --publisher-url <thelancet.com URL>` or
  jina on the direct publisher URL, not the DOI URL. (CCR4 profile,
  ~34K chars, 229 lines, 5 papers, 5 unique PMIDs cited,
  working-docs/hitlist-profiles/ccr4.md.)
- **2026-08-15 — CD2 key-paper-ingestion profile observations.**
  Thirteenth level-2 profile (approved tier, immunology/inflammation,
  psoriasis + transplant/GVHD). CD2 is a T cell/NK cell costimulatory
  receptor whose ligand is LFA-3 (CD58). 5 key papers ingested (4/5
  full text: 2 PMC XML OA, 1 EPMC PDF render, 1 jina reader; 1/5
  abstract-only — JAAD/Elsevier with old Mosby DOI returning 404).
  ~35K chars, 5 papers, 8 unique PMIDs cited. New observations:

  (1) **Fusion-protein-approved, antibody-failed is a distinct
  competitive landscape pattern.** Alefacept (LFA-3-Ig fusion protein,
  not a monoclonal antibody) was the approved drug for CD2; siplizumab
  (anti-CD2 IgG1 antibody) failed Phase II and was discontinued for
  psoriasis. This inverts the usual pattern (antibody succeeds,
  fusion protein is the also-ran): here the fusion protein is the
  winner and the antibody is the graveyard entry. For field 4
  (antibody landscape) and field 10 (competitive landscape), when the
  approved drug is a fusion protein and the antibody failed, the
  profile must analyze WHY the fusion protein succeeded where the
  antibody did not — the answer is usually mechanistic (epitope
  location, isotype, selectivity), not just "the antibody was
  underdosed." For field 11 (differentiation), the key question is
  whether a different antibody (different epitope, isotype, dose)
  could replicate the fusion protein's success — the fusion protein
  validates the target, and the antibody's failure may be
  format-specific rather than target-specific. This is the
  converse of the C5aR1 "small-molecule-approved, antibody-open"
  pattern: here the fusion protein is the approved modality and the
  antibody is the failed modality.

  (2) **Epitope location determines memory selectivity and tissue
  penetration — the third confirmed example.** Alefacept binds
  T11.1/T11.2 (LFA-3-binding region, membrane-distal domain) and
  achieves: (a) direct LFA-3-competitive blockade, (b) selective
  memory-effector T cell depletion (CD45RO+), and (c) tissue-level
  T cell depletion in psoriatic skin (73% lymphocyte reduction).
  Siplizumab binds T11.2/T11.3 (non-LFA-3-competitive,
  membrane-proximal domain) and achieves: (a) no direct LFA-3
  blockade, (b) no memory/naïve selectivity (both depleted), and
  (c) NO tissue-level T cell depletion despite blood depletion.
  The epitope distinction maps directly to three clinically
  consequential differences: mechanism (blockade + depletion vs
  depletion-only), selectivity (memory-selective vs
  non-selective), and tissue penetration (skin T cell depletion vs
  blood-only). This is the third confirmed example after CD20
  Type I/II (epitope → raft localization → CDC/PCD mechanism) and
  CD4 D1/D2 (epitope → MHC II blockade vs HIV post-attachment →
  depleting vs non-depleting). For any target with multiple
  antibodies targeting different epitopes, field 5 (epitope
  landscape) must map each epitope bin to its functional
  consequences (mechanism, selectivity, tissue penetration) — the
  epitope is not just a binding site, it is a determinant of the
  entire therapeutic profile.

  (3) **Blood depletion without tissue depletion is a PK failure
  mode for skin-homing T cell targets.** Siplizumab significantly
  reduced circulating CD2+ cells (CD3+, CD8+, CD16+/56+) but did
  NOT reduce skin-infiltrating CD3+ T cells, epidermal thickness,
  or K16/ICAM expression (PMID 19471949). In contrast, alefacept
  achieved 73% lesional lymphocyte reduction and 79% CD8+ reduction
  in psoriatic skin (PMID 15671179). This blood-tissue disconnect
  is a distinct PK failure mode: the antibody reaches therapeutic
  concentrations in blood but not in skin. For field 6 (failure
  modes), when a depleting antibody shows blood activity without
  clinical response, the analysis must check whether tissue-level
  target cell depletion was achieved — blood depletion is necessary
  but not sufficient for efficacy in solid-tissue autoimmune
  diseases. Low trough concentrations (subtherapeutic dosing) and
  insufficient tissue penetration are the likely causes; higher
  doses or different formats (higher affinity, tissue-homing
  bispecifics) may address this. This pattern may not apply to
  blood-borne diseases (CTCL, leukemia) where blood depletion IS
  the therapeutic goal. (CD2 profile, 2026-08-15, PMID 19471949
  vs PMID 15671179.)

  (4) **NK cell fratricide is an on-target effect unique to IgG1
  anti-CD2 antibodies.** NK cells express both CD2 (the antibody
  target) and CD16/FcγRIIIA (the ADCC effector receptor). When an
  IgG1 anti-CD2 antibody (siplizumab) binds CD2 on NK cells, those
  NK cells become ADCC targets for other NK cells that engage the
  antibody's Fc via CD16 — "fratricide" (PMID 33643309). This is a
  novel on-target mechanism: the effector and target cell
  populations are the same cell type. For field 6 (failure modes)
  and field 8 (safety), any IgG1 antibody targeting a receptor
  expressed on NK cells should be assessed for fratricide — it
  depletes NK cells as an unintended (or intended, in NK
  malignancies) consequence. An IgG4 (non-depleting) format would
  avoid fratricide. This generalizes to any target co-expressed on
  NK cells and any effector cell: when the target cell IS the
  effector cell, IgG1 antibodies create a self-depletion loop.
  (CD2 profile, 2026-08-15, PMID 33643309.)

  (5) **Ligand divergence across species can block preclinical
  development entirely.** Mice lack LFA-3 (CD58, the primary human
  CD2 ligand) entirely — they express CD48, which binds CD2 with
  lower affinity and also binds CD244. This means: (a) alefacept
  (LFA-3-Ig fusion) has no cognate target in mice; (b) mouse models
  do not recapitulate the human CD2-LFA-3 interaction; (c) only
  human CD2 transgenic mice or non-human primates are valid
  preclinical models. This made CD2 therapeutic development
  resource-intensive and most CD2 biology was conducted in vitro
  (PMID 32582179). For field 2 (species cross-reactivity) and
  field 7 (in vivo models), when a target's primary ligand is
  absent in mice, the standard mouse model is invalid — note this
  prominently and identify the alternative model (transgenic,
  primate, or in vitro only). This is more severe than the usual
  "human/mouse sequence divergence limits antibody cross-reactivity"
  pattern: here the entire ligand-receptor axis is absent, not
  just sequence-divergent. (CD2 profile, 2026-08-15,
  PMID 32582179.)\n

- **2026-08-15 — CD22/SIGLEC-2 key-paper-ingestion profile observations.**
  Fourteenth level-2 profile (approved tier, immunology/oncology, B-ALL +
  HCL). CD22 is a B-cell-restricted Siglec family member whose rapid
  internalization upon antibody binding makes it an ideal ADC and
  immunotoxin target. 5 key papers ingested at 100% full-text rate (3
  PMC XML OA, 1 Wayback CDX for NEJM, 1 jina reader for Annual Reviews).
  ~33K chars, 239 lines, 5 unique PMIDs cited. New observations:

  (1) **Rapid internalization as the defining biological enabler for
  ADC/immunotoxin target selection.** CD22's endocytosis — mediated by
  ITIM-clathrin adaptor AP50 interactions and a membrane-proximal motif
  (R737/Q739) — is the fundamental property that makes it an excellent
  target for payload-delivery therapies (ADC, immunotoxin). This is
  distinct from CD20 (poor internalization, works via ADCC/CDC) and CD19
  (moderate internalization). For any surface-marker target being
  profiled, the internalization rate should be assessed in field 2
  (biological mechanism) as it directly determines suitability for
  ADC/immunotoxin approaches. A target that internalizes slowly may
  still work for naked antibody (ADCC/CDC) or CAR-T approaches, but not
  for payload delivery. (PMID 31986070, PMID 37821931.)

  (2) **Payload-specific vs target-specific toxicity is a critical
  distinction for ADC/immunotoxin target profiles.** Both approved CD22
  drugs have severe but completely different toxicities: inotuzumab
  (calicheamicin) causes VOD/SOS (hepatic sinusoidal injury, 11%), while
  moxetumomab (Pseudomonas exotoxin A) causes HUS/CLS (endothelial
  damage, 5%/3%). Neither toxicity is CD22-mediated — they are entirely
  determined by the payload. For field 6 (failure modes) and field 8
  (safety), when a target has multiple approved therapies with different
  payloads, explicitly separate target-specific toxicity (B-cell
  depletion, expected and manageable) from payload-specific toxicity
  (VOD/SOS, HUS/CLS, neuropathy). This has direct implications for
  field 11 (differentiation): a new CD22 ADC with a different payload
  class (tubulin inhibitor, topoisomerase inhibitor) could have a
  completely different safety profile — the payload, not the target,
  defines the therapeutic index. This pattern applies to any ADC
  target where multiple payloads have been tested (CD22, CD33, CD30,
  CD19, HER2, TROP-2).

  (3) **Commercial withdrawal for non-safety reasons is a distinct
  outcome that opens competitive space.** Moxetumomab pasudotox was
  withdrawn from the US market in 2023 for commercial reasons (low
  clinical uptake, complexity of administration), NOT for safety
  concerns. For field 4 (antibody landscape), a withdrawn-for-commercial
  drug is different from a withdrawn-for-safety drug: the target remains
  validated, the efficacy data remain valid, and the withdrawal creates
  an open competitive space for a simpler format (e.g., a standard IgG
  ADC rather than a recombinant immunotoxin with complex administration).
  For field 10 (competitive landscape) and field 11 (differentiation),
  explicitly note whether a withdrawal was commercial or safety-driven
  — a commercial withdrawal is a market opportunity, not a red flag.

  (4) **CD22 density (not just presence) as a predictive biomarker.**
  Clinical data showed that CD22 density on the tumor cell surface
  correlated with clinical outcomes for inotuzumab — higher CD22
  density → more ADC internalization → better response. This is the
  second target profiled where target density (not just expression)
  is a predictive biomarker (after CCR4, where gain-of-function
  mutations increase target density). For field 7 (biomarker assays)
  and field 6 (success factors), when a target's therapeutic mechanism
  depends on internalization (ADC, immunotoxin), surface density
  quantification (flow cytometry MFI) is a more predictive biomarker
  than binary expression (positive/negative). The resistance mechanism
  is partial downregulation (not complete loss as with CD19), making
  density-based patient selection feasible.

  (5) **UniProt REST API search endpoint returns HTTP 400 with the
  `fields=` parameter; use the direct accession URL as fallback.** The
  search endpoint
  (`rest.uniprot.org/uniprotkb/search?query=gene:CD22+AND+organism_id:9606&format=json&fields=...`)
  returns HTTP 400 Bad Request. The direct accession URL
  (`rest.uniprot.org/uniprotkb/P20273.json`) succeeds and returns the
  complete entry including all features (domains, glycosylation,
  transmembrane, PDB cross-references, function comments, tissue
  specificity). The direct accession URL is more reliable than the
  search endpoint when the UniProt accession is known (from the task
  brief or a prior search). When the accession is unknown, use the
  search endpoint WITHOUT the `fields=` parameter (just
  `query=gene:<symbol>+AND+organism_id:9606&format=json`) to discover
  the accession, then fetch the full entry via the direct URL.

  (CD22 profile, ~33K chars, 239 lines, 5 papers, 5 unique PMIDs cited,
  working-docs/hitlist-profiles/cd22.md.)

- **2026-08-15 — CD30 key-paper-ingestion profile observations.**
  Fifteenth level-2 profile (approved tier, immunology/oncology,
  Hodgkin lymphoma + ALCL + CTCL). CD30 (TNFRSF8) is the canonical
  TNFR superfamily ADC target — brentuximab vedotin (SGN-35/Adcetris)
  is the sole approved anti-CD30 antibody, and the first approved ADC
  for a hematologic malignancy. 5 key papers ingested (80% full-text
  rate: 1 EPMC PDF render, 2 PMC XML OA, 1 jina reader; 1/5
  abstract-only — AACR Clin Cancer Res blocked). ~22K chars, 88 PMID
  citations, 5 unique PMIDs. New observations:

  (1) **Naked antibody failed, ADC succeeded — the canonical
  format-failure pattern for ADC targets.** The naked anti-CD30
  antibody SGN-30 (same cAC10 antibody scaffold) showed limited
  single-agent efficacy. Conjugation to MMAE via a protease-cleavable
  citrulline-valine linker transformed it into brentuximab vedotin
  (SGN-35) with ORR 75% (HL) and 86% (ALCL). This is the clearest
  example yet of format being THE success factor: the antibody and
  epitope are identical; only the payload and linker changed. For
  field 6 (failure modes), SGN-30 → SGN-35 is the canonical case:
  CD30 blockade alone (without cytotoxic payload) is insufficient
  because CD30 signaling blockade does not kill established tumor
  cells — only payload delivery does. For field 11 (differentiation),
  this means a naked anti-CD30 antibody for autoimmune indications
  (blocking CD30L/CD30 signaling without depleting CD30+ cells) is a
  fundamentally different therapeutic goal from brentuximab vedotin's
  depleting-ADC mechanism, and the failure of SGN-30 in oncology does
  NOT predict failure of a naked blocking antibody in autoimmunity.
  (PMID 22684302, PMID 30122950.)

  (2) **Payload-mediated vs target-mediated toxicity is the critical
  safety distinction for ADC target profiles.** Brentuximab vedotin's
  dose-limiting toxicities (peripheral neuropathy 22-56%, neutropenia
  20-35%) are entirely MMAE-mediated, not CD30-mediated — they reflect
  the cytotoxic payload's effect on microtubules in neuronal and
  rapidly dividing cells, not CD30-specific on-target effects. CD30
  has limited normal tissue expression, so the ADC's therapeutic
  index is driven by differential CD30 expression between tumor and
  normal cells. This confirms and extends the CD22 observation
  (payload-specific vs target-specific toxicity): for ANY ADC target,
  field 8 (safety) must explicitly separate payload-mediated toxicity
  from target-mediated toxicity. A new CD30 ADC with a different
  payload (non-microtubule-disrupting) could have a completely
  different safety profile — the payload, not the target, defines
  the therapeutic index. Neuropathy resolved in 73% of patients after
  cessation, confirming it is reversible and dose-related, not
  permanent. (PMID 22684302, PMID 30122950.)
- **ADC failed → BiTE succeeded: the cross-modality graveyard rescue.**
  When an ADC fails Phase 3 due to payload toxicity (not target
  invalidity), a bispecific T-cell engager (BiTE/TCE) against the
  same target can succeed by eliminating the cytotoxic payload
  entirely and replacing it with T cell-mediated killing. The DLL3
  case (Rova-T ADC failed Phase 3 due to PBD warhead toxicity →
  tarlatamab BiTE approved 2024) is the canonical example: the ADC's
  serosal effusions, thrombocytopenia, and skin reactions (PBD-
  driven, ~60% grade ≥3 in Phase 3) prevented adequate dosing and
  caused inferior OS; the BiTE's CRS/ICANS (immunostimulatory, mostly
  grade 1-2, manageable with step-up dosing) allowed effective dosing
  and achieved ORR 40%. For field 6 (failure/success modes), when an
  ADC fails due to payload toxicity, explicitly state that the
  target remains validated and a BiTE is a validated rescue modality.
  For field 11 (differentiation), the question is whether the ADC
  format can be rescued with a non-toxic payload (e.g., ZL-1310 with
  camptothecin for DLL3) or whether the BiTE format is inherently
  superior for targets where the tumor microenvironment supports
  T cell infiltration. This is the REVERSE of the CD30 pattern
  (naked Ab failed → ADC succeeded by ADDING a payload): here the
  ADC had the payload but the payload was the problem. The winning
  format can be a DIFFERENT modality entirely, not just an improved
  version of the same modality. (DLL3/CD3 profile, 2026-08-16,
  PMID 31215500, PMID 37355629, PMID 38730427.)
- **On-target off-tumor toxicity in BiTE/TCE profiles from low-level
  target expression in normal tissues.** BiTEs redirect T cells to
  kill any cell expressing surface target — there is no selectivity
  for tumor vs normal cells beyond target expression density. When
  a normal tissue expresses even low levels of the target on its
  cell surface (sharing a transcriptional regulator with the tumor),
  T cell redirection will kill those normal cells. Tarlatamab causes
  dysgeusia (32%) because taste bud cells express DLL3 (driven by
  ASCL1, the same transcription factor driving DLL3 in SCLC). This
  is a distinct on-target toxicity pattern from soluble-target
  antibodies (where toxicity comes from blocking the target's
  signaling function) — for BiTEs, the toxicity comes from KILLING
  cells that express the target, regardless of whether those cells
  are tumor or normal. For field 8 (safety) of BiTE/TCE profiles,
  enumerate ALL normal tissues expressing the target (even at low
  levels) and assess the on-target off-tumor killing risk. The
  therapeutic index depends on the RATIO of target expression
  (tumor vs normal surface density), not just presence/absence.
  (DLL3/CD3 profile, 2026-08-16, PMID 39876075.)
- **Target expression biomarker can be biologically rational but
  clinically unreliable.** DLL3 expression by IHC was expected to
  predict response to DLL3-targeted therapies, but clinical data
  are inconsistent: Rova-T FIH showed DLL3-high ORR 35% vs 0%, but
  Phase 2/3 did not confirm; tarlatamab showed responses regardless
  of DLL3 expression status. Tarlatamab is approved without a
  companion diagnostic. For field 7 (biomarker assays), do not
  assume that target expression always predicts response to
  target-directed therapy — verify with clinical data. Possible
  confounders: small FIH sample sizes, IHC technique variability,
  lack of contemporaneous biopsies in rapidly progressive diseases,
  heterogeneity between primary and metastatic target expression.
  Emerging liquid biopsy approaches (CTCs, circulating nucleic
  acids) and imaging (immunoPET) may provide more reliable real-time
  assessment than fixed-tissue IHC. (DLL3/CD3 profile, 2026-08-16,
  PMID 37355629, PMID 38730427.)

  (3) **Rapid internalization is the defining biological enabler for
  ADC target selection — confirmed across CD22 and CD30.** CD30 is
  rapidly internalized upon antibody binding and transported to
  lysosomes, where the cleavable linker is cleaved and MMAE is
  released. This is the same property documented for CD22 (ITIM-
  clathrin-mediated endocytosis). For any surface-marker target
  being profiled, the internalization rate is the primary determinant
  of ADC suitability. A target that does not internalize (e.g., CD20)
  can still work via ADCC/CDC but is a poor ADC target. The
  internalization rate should be assessed in field 2 (biological
  mechanism) alongside expression pattern. (PMID 22684302, PMID
  30122950.)

  (4) **PML boxed warning is a shared safety ceiling for
  immunosuppressive antibodies.** Brentuximab vedotin carries an FDA
  boxed warning for PML (JC virus reactivation), the same rare but
  fatal complication seen with efalizumab (anti-CD11a, withdrawn for
  PML) and natalizumab (anti-α4 integrin, PML risk stratified by JCV
  serostatus). While the mechanisms differ (BV depletes CD30+
  lymphocytes, efalizumab/natalizumab block T cell trafficking), the
  downstream effect is impaired immune surveillance. For field 8
  (safety), any antibody that causes significant lymphocyte depletion
  or immune suppression should be assessed for PML risk. JCV
  serostatus is a validated risk stratification biomarker. This
  cross-class pattern (CD11a → CD20 → CD30) suggests PML is a class
  ceiling for immunosuppressive antibodies, not a target-specific
  event. (PMID 22684302, CD11a profile, CD20 profile.)

  (CD30 profile, ~22K chars, 88 PMID citations, 5 unique PMIDs,
  working-docs/hitlist-profiles/cd30.md.)

- **2026-08-15 — CSF-1R/CSF1R key-paper-ingestion profile observations.**
  Fifteenth level-2 profile (approved tier, immunology/inflammation +
  oncology). CSF-1R is the **first target where both a small-molecule
  AND an antibody have achieved independent FDA approvals for different
  indications** — pexidartinib (small molecule) for TGCT (2019),
  vimseltinib (small molecule) for TGCT (2025), and axatilimab (IgG4
  antibody) for chronic GVHD (2024). 5 key papers ingested (2/5 PMC XML
  OA, 1/5 EPMC PDF, 1/5 jina-reader, 1/5 abstract-only — 80% full-text
  rate). ~33K chars, 5 papers, 17 authors. New observations:

  (1) **Dual-modality approval (small molecule + antibody) for the same
  target across different indications confirms druggability and
  isolates modality-vs-indication effects.** Unlike CD30 (antibody +
  ADC + CAR-T + bispecific — all antibody-based) or C5aR1 (small
  molecule only, antibody open), CSF-1R has FDA-approved drugs in BOTH
  modalities, each in a different disease. The small molecules succeeded
  in an oncology setting (TGCT — a macrophage-rich tumor), while the
  antibody succeeded in an inflammatory setting (cGVHD — macrophage-driven
  fibrosis). This pattern suggests the modality choice and disease
  selection are coupled: small molecules with broader kinase profiles
  may work better in oncology (broader target engagement including
  cancer cell CSF-1R), while antibodies with cleaner specificity profiles
  may be better suited for chronic inflammatory conditions (sustained
  macrophage signaling blockade with fewer off-target effects). For
  field 10 (competitive landscape) and field 11 (differentiation),
  when both modalities are approved, compare them head-to-head on
  safety profiles (pexidartinib hepatotoxicity boxed warning vs.
  axatilimab periorbital edema), dosing (oral daily vs. SC Q2W), and
  mechanism (kinase inhibition including cancer cell-autonomous effects
  vs. receptor blockade with IgG4).

  (2) **IgG4 isotype for CSF-1R signals blocking-not-depleting as the
  effective mechanism in cGVHD.** Axatilimab uses IgG4 (κ light chain),
  which minimizes Fc-mediated effector function — the mechanism is CSF-1R
  signaling blockade, not ADCC-mediated macrophage depletion. This
  contrasts with emactuzumab (IgG1 anti-CSF-1R, potentially depleting)
  and cabiralizumab (IgG4 anti-CSF-1R, blocking). The isotype choice
  is indication-dependent: blocking (IgG4) for inflammatory disease
  where sustained macrophage signaling inhibition is the goal and
  depletion would be too toxic; depleting (IgG1) for oncology/TGCT where
  macrophage removal is the therapeutic goal. For field 4 (antibody
  landscape), the isotype is not just a format choice — it encodes the
  therapeutic mechanism (block vs. deplete). For field 11
  (differentiation), an IgG1 depleting anti-CSF-1R for cGVHD might fail
  due to excessive macrophage depletion toxicity, while an IgG4 blocking
  antibody for TGCT might be insufficient because it doesn't remove the
  macrophages comprising the tumor mass. This generalizes the CD20
  Type I/II and CD2 epitope-mechanism pattern: the format (isotype,
  epitope) IS the mechanism.

  (3) **On-target class toxicity (periorbital edema) crosses modality
  boundaries.** Periorbital edema is the signature on-target AE across
  ALL CSF-1R inhibitors — pexidartinib (small molecule), vimseltinib
  (small molecule), and axatilimab (antibody). This confirms the toxicity
  is CSF-1R-mediated (tissue macrophage depletion disrupting periorbital
  fluid homeostasis), not off-target. For field 8 (safety), when a class
  toxicity crosses modalities (small molecule AND antibody), it is
  unambiguously on-target — the target biology itself creates the safety
  ceiling. This is the counterpart to the PML pattern (CD11a/CD20/CD30):
  PML is a shared ceiling for immunosuppressive antibodies across
  different targets, while periorbital edema is a shared ceiling for
  CSF-1R blockers across different modalities.

  (4) **Antibody failures in oncology (cabiralizumab, AMG 820) vs.
  antibody success in inflammation (axatilimab) mirrors the small-molecule
  experience.** CSF-1R blockade alone is insufficient in solid tumors
  (cabiralizumab failed in pancreatic cancer, AMG 820 failed in solid
  tumors), but effective in TGCT (pexidartinib/vimseltinib — where the
  tumor IS macrophages) and cGVHD (axatilimab — macrophage-driven
  fibrosis). The differential success is disease-dependent, not
  modality-dependent: both modalities fail in solid tumors and both
  succeed in macrophage-dominant diseases. For field 6 (failure modes),
  the key analysis is whether the disease pathology is macrophage-
  dependent enough that CSF-1R blockade alone is sufficient — TGCT
  (tumor mass = macrophages, yes), cGVHD (pathology = macrophage-driven
  fibrosis, yes), solid tumors (TME has redundant immunosuppressive
  pathways, no).

  (5) **Cold Spring Harbor Laboratory Press (CSHLP) exhibits the Branch
  1b pattern.** PMID 24890514 (Stanley & Chitu 2014, Cold Spring Harb
  Perspect Biol) had `inPMC: Y` but PMC XML returned front-matter only
  (6.7 KB, no body). EPMC PDF render succeeded (3.4 MB → 95K chars).
  Added CSHLP to the paper-ingest known-blocks table as the same Branch
  1b pattern as JCI Insight/OUP/ATS/EMBO J. (CSF-1R profile, ~33K
  chars, 5 papers, 17 authors, 5 unique PMIDs cited,
  working-docs/hitlist-profiles/csf-1r.md.)

- **2026-08-15 — CXCR4 key-paper-ingestion profile observations.**
  Sixteenth level-2 profile (approved tier, immunology/oncology). CXCR4
  (CD184, fusin) is a 7-TM GPCR whose sole ligand is CXCL12 (SDF-1); it
  is the first chemokine receptor profiled and the first GPCR target
  where the approved drug is a small molecule (plerixafor/AMD3100,
  Mozobil) for a non-oncology indication (HSC mobilization) while
  antibodies (ulocuplumab/BMS-936564) remain in clinical trials for
  hematologic malignancies. 5 key papers ingested (3/5 PMC XML full
  text — Yang 2023, Kashyap 2016, Ghobrial 2020; 2/5 abstract-only —
  Pozzobon 2016 Elsevier, Korbecki 2024 Leukemia/Springer Nature
  reference-list masquerade). ~28K chars, 5 papers, 56 authors, 5
  unique PMIDs cited. New observations:

  (1) **Small-molecule-approved, antibody-in-clical-trials is a
  variant of the C5aR1 pattern.** C5aR1 had small-molecule-approved,
  antibody-open (no antibody in trials); CXCR4 has small-molecule-
  approved AND antibody-in-clinical-trials (ulocuplumab Phase Ib/II in
  MM, Phase I in AML/Waldenström). The small molecule validates the
  target; the antibody is attempting to extend to oncology indications
  where the small molecule failed as monotherapy (plerixafor is
  ineffective alone in cancer due to resistance). This is a richer
  competitive landscape than C5aR1: the antibody has a clinical
  efficacy bar to beat (plerixafor for HSC mobilization) AND a clinical
  efficacy signal in oncology (ulocuplumab 55.2% ORR in MM with
  lenalidomide). For field 10 (competitive landscape), the small-
  molecule approval and the antibody clinical data together create a
  more differentiated competitive picture than "approved" or "clinical-
  trial" alone — the target is validated across modalities but in
  different indications.

  (2) **IgG4 blocking + ROS-mediated apoptosis is a unique dual-
  mechanism profile — distinct from CSF-1R's IgG4 blocking-only and
  CD30's ADC depleting.** Ulocuplumab (IgG4) deliberately lacks
  ADCC/CDC and functions as a "blocking antibody" (like axatilimab for
  CSF-1R), BUT it additionally induces apoptosis through a ROS-
  dependent, caspase-independent mechanism (PMID 26646452). This is
  neither pure blocking (CSF-1R axatilimab) nor pure depleting (CD20
  Type I/II) — it is a third pattern: **blockade + direct cytotoxic
  signaling**. The ROS mechanism may explain the selectivity for
  cancer cells (higher baseline ROS, higher CXCR4 density ≥8-fold over
  normal cells) without requiring immune effector function. For field
  4 (antibody landscape) and field 6 (success factors), the IgG4 +
  ROS mechanism is a format-is-mechanism example where the isotype
  choice (IgG4 = no effector function) is coupled with an intrinsic
  cytotoxic pathway (ROS) — different from both the CSF-1R pattern
  (IgG4 = pure blocking) and the CD2/CD20 pattern (IgG1 = ADCC-
  mediated depletion). The IgG4 + ROS pattern may generalize to other
  GPCR targets where direct signaling blockade alone is insufficient
  but immune-mediated depletion is contraindicated by widespread
  target expression on normal cells.

  (3) **Preferential cancer-cell killing without effector function
  challenges the "effector function required for efficacy" assumption.**
  Ulocuplumab preferentially induces apoptosis in CLL/cancer cell lines
  but NOT in normal lymphocytes (PMID 26646452), despite CXCR4 being
  expressed on both. The selectivity is driven by receptor density
  (cancer ≥8-fold higher) and cancer cell vulnerability to ROS, not by
  immune effector function. This is a notable counterexample to the
  CD2/CD20/CCR4 pattern where ADCC/effector function is the primary
  killing mechanism. For field 11 (differentiation), an IgG1
  ulocuplumab with added ADCC might NOT improve efficacy — the ROS
  mechanism is already selective for cancer cells, and adding ADCC
  could increase on-target toxicity against normal CXCR4+ cells. This
  suggests that for targets where the antibody has intrinsic cytotoxic
  signaling activity (not just blocking), the IgG4 format is the
  correct choice and IgG1 may be counterproductive.

  (4) **p53-independent activity is a clinically significant
  selectivity advantage for TP53-mutant cancers.** Ulocuplumab
  induces apoptosis in TP53-mutant/Del(17p) CLL, a population with
  poor prognosis and limited treatment options (PMID 26646452). The
  ROS-dependent, caspase-independent mechanism bypasses the p53
  pathway entirely. For field 3 (disease evidence) and field 6
  (success factors), p53 independence should be noted as a specific
  advantage for indications with high TP53 mutation rates (CLL, AML,
  MM). This is the first target profiled where the mechanism of
  action explicitly bypasses a common resistance pathway — an
  antibody-specific differentiation that small molecules targeting
  the same pathway (plerixafor) may not share.

  (5) **Combination therapy is essential — monotherapy resistance is
  the norm for CXCR4 blockade in cancer.** Plerixafor alone is
  ineffective in cancer due to tumor resistance (PMID 37497001).
  Ulocuplumab monotherapy was not tested clinically — all trials
  used combinations (lenalidomide/dex, bortezomib/dex, MEC,
  ibrutinib). The mechanism: CXCR4 blockade de-adheres tumor cells
  from the protective bone marrow niche, sensitizing them to other
  drugs (PMID 31672767). Not all combinations are equal —
  ulocuplumab + lenalidomide achieved 55.2% ORR vs. 25% for
  ulocuplumab + bortezomib (PMID 31672767), suggesting IMiD
  combinations are superior to proteasome inhibitor combinations
  for CXCR4 blockade strategies. For field 6 (failure modes),
  CXCR4 monotherapy resistance is a known failure mode; the
  combination partner choice is the critical success factor.

  (6) **EPMC authorId field can be a dict, not a string.** The
  EPMC core record's `authorList.author[].authorId` field, used for
  ORCID extraction in paper-ingest Phase 8, can return a dict object
  instead of a string. Naïve `ea.get('authorId', '').lower()` raises
  `AttributeError`. Always guard with `isinstance(..., str)` before
  string operations. Patched in the paper-ingest skill SKILL.md.
  (CXCR4 profile, ~28K chars, 5 papers, 56 authors, 5 unique PMIDs
  cited, working-docs/hitlist-profiles/cxcr4.md.)

- **2026-08-15 — Factor XIIa (FXIIa) key-paper-ingestion profile
  observations.** Seventeenth level-2 profile (approved tier,
  immunology/cardiovascular — HAE + thrombosis). FXIIa is the
  **first soluble protease target** and the **first
  cardiovascular/hemostasis target** profiled — all prior profiles
  were cell-surface receptors or circulating non-enzymatic proteins.
  Garadacimab (anti-FXIIa IgG4λ, CSL Behring) is approved for HAE
  prophylaxis. 5 key papers ingested (4/5 full text: 2 PMC XML OA,
  1 EPMC PDF render, 1 jina reader; 1/5 abstract-only — Wiley
  paywall, no PMC, no Wayback). ~28K chars, 87 PMID citations, 5
  papers, 37 unique author slugs. New observations:

  (1) **The thrombosis-without-hemostasis paradigm is the strongest
  target-safety rationale in the entire profile set.** FXII is
  essential for pathologic thrombosis but NOT for physiological
  hemostasis (tissue factor pathway compensates). FXII deficiency
  in humans (Hageman trait) causes no bleeding phenotype. This
  dissociation is the biological basis for safe FXIIa-targeted
  anticoagulation — a unique advantage over ALL other anticoagulant
  targets (heparin, warfarin, DOACs all carry bleeding risk). In
  long-term garadacimab data (≤5.5 years, n=172), no deaths, no
  drug-related SAEs, and no bleeding events were reported. For
  field 6 (success factors), this is the canonical example of the
  target biology itself providing the therapeutic index — the
  success factor is not the antibody design (epitope, format,
  dosing) but the target's non-essential role in hemostasis. For
  field 8 (safety), the absence of bleeding is mechanistically
  predicted, not merely observed. (PMID 26373901, PMID 26605293,
  PMID 41977511, PMID 42268494.)

  (2) **Upstream cascade positioning as a success factor — first
  confirmed example.** Garadacimab targets FXIIa at the very top
  of the contact activation pathway, blocking BOTH the coagulation
  arm (FXI activation → thrombin) and the inflammatory arm
  (prekallikrein → kallikrein → bradykinin). Downstream
  competitors (lanadelumab anti-kallikrein, berotralstat kallikrein
  inhibitor) block only the inflammatory arm. Network
  meta-analysis ranked garadacimab highest probability of being
  most effective HAE prophylactic (73%) vs lanadelumab q2w (26%).
  For field 6 (success factors), upstream positioning provides
  broader pathway coverage — this is the first target where the
  position in the signaling cascade (top vs middle) is a
  competitive advantage over same-pathway drugs. For field 10
  (competitive landscape), the competitive set includes both
  same-target antibodies and downstream-pathway drugs (different
  targets, same cascade). (PMID 42057602, PMID 41977511.)

  (3) **Soluble protease targets require a different epitope
  framework than surface receptors.** FXIIa is a circulating
  enzyme, not a cell-surface receptor. The antibody must
  distinguish the active form (FXIIa, cleaved at Arg353, two-chain)
  from the zymogen (FXII, single-chain, inactive) — both are the
  same protein at different conformational states. Garadacimab
  targets the catalytic domain (light chain, C-terminal), which is
  only accessible in the active conformation. For field 5 (epitope
  landscape), the epitope framework is active-vs-zymogen
  conformational selectivity, not the receptor-ligand-competition
  or cell-depletion framework used for surface receptors. An
  alternative epitope strategy (targeting the heavy chain /
  surface-binding domains to block activation rather than inhibit
  the active enzyme) is unexplored — this is a genuine
  differentiation opportunity. For field 9 (structural
  information), the zymogen-to-enzyme conformational change is the
  key structural consideration. (PMID 41977511, PMID 26605293.)

  (4) **Preclinical-to-clinical translational gap is a target-level
  limitation.** Despite strong preclinical evidence for FXIIa
  blockade in thrombosis (3F7 in cardiopulmonary bypass, stroke
  models, stent thrombosis), NO anti-FXIIa antibody has advanced
  to clinical trials for thrombosis/anticoagulation. Garadacimab
  succeeded only in HAE (a rare inflammatory disease), not in the
  much larger thrombosis market. For field 6 (failure modes),
  this is not an antibody failure but a translation gap — the
  target is validated preclinically for thrombosis but the
  clinical development path (large cardiovascular outcome trials,
  comparison with DOACs) is far more demanding than HAE (small
  rare-disease trials, clear efficacy endpoint). For field 11
  (differentiation), the thrombosis indication represents the
  largest unexplored market for this target — a differentiation
  opportunity if the clinical development risk can be managed.
  (PMID 26605293, PMID 26373901, PMID 41977511.)

  (5) **Variable response in HAE subtypes with normal C1INH is a
  biomarker-defined limitation.** Garadacimab showed >88% attack
  rate reduction in 2/3 HAE-FXII patients but only 19% in the
  third; HAE-PLG patients had inconsistent responses (2/3 had
  increased attack rates). For field 6 (failure modes), when a
  target's disease has multiple genetic subtypes with different
  pathogenic mechanisms (FXII gain-of-function vs plasminogen
  mutations), the upstream target (FXIIa) may be effective only
  in subtypes where the pathophysiology is FXII-dependent. For
  field 7 (biomarker assays), HAE genotyping (F12, PLG, SERPING1)
  is a predictive biomarker for FXIIa-targeted therapy — the
  first target profiled where the disease genotype predicts
  response to the target-specific antibody. (PMID 42057602.)

  (6) **IgG4 isotype for a soluble protease — blocking without
  effector function.** Garadacimab uses IgG4λ, which minimizes
  Fc-mediated effector function — appropriate for a blocking
  antibody against a circulating protease where cell depletion is
  irrelevant (the target is soluble, not cell-surface). This
  extends the isotype-mechanism pattern: IgG4 for blocking
  soluble mediators (garadacimab/FXIIa, dupilumab/IL-4Rα),
  IgG1 for depleting surface targets (rituximab/CD20,
  alemtuzumab/CD52), IgG4 for blocking surface receptors without
  depletion (axatilimab/CSF-1R, nivolumab/PD-1). For a soluble
  protease, IgG1 would be inappropriate — there are no cells to
  deplete, and Fc-mediated effector function risks immune
  complex formation with circulating antigen. (PMID 41977511.)

  (7) **AME Publishing (Ann Transl Med) exhibits the Branch 1b
  pattern.** PMID 26605293 (Worm 2015) had `inPMC: Y` but PMC
  XML returned front-matter only (10 KB, no body). EPMC PDF
  render succeeded (223 KB → 23K chars). Added AME Publishing to
  the paper-ingest known-blocks table as the same Branch 1b
  pattern as JCI Insight, OUP/ATS, CSHLP, ASCO/JCO. (Factor XIIa
  profile, ~28K chars, 87 PMID citations, 5 papers, 37 unique
  author slugs, working-docs/hitlist-profiles/factor-xiia.md.)

- **2026-08-15 — IFNAR1 key-paper-ingestion profile observations.**
  Eighteenth level-2 profile (approved tier, immunology/inflammation —
  SLE). IFNAR1 is the shared receptor subunit for ALL type I
  interferons (IFN-α subtypes, IFN-β, IFN-ω, IFN-ε, IFN-κ).
  Anifrolumab (anti-IFNAR1 IgG1κ, Saphnelo, AstraZeneca) was
  approved for moderate-to-severe SLE in 2021. 5 key papers ingested
  (5/5 full text: 2 PMC XML OA, 2 Wayback, 1 jina reader — 100%
  retrieval rate). ~25K chars, 5 papers, 36 unique author slugs. New
  observations:

  (1) **Receptor-level blockade vs ligand-level blockade is the
  defining target-strategy distinction for cytokine pathways with
  multiple ligands.** Anifrolumab (anti-IFNAR1, receptor-level)
  succeeded where rontalizumab and sifalimumab (anti-IFN-α,
  ligand-level) failed. The mechanistic explanation: anti-IFN-α
  antibodies neutralize only IFN-α subtypes, leaving IFN-β, IFN-ω,
  IFN-ε, and IFN-κ free to signal through IFNAR1 — residual type I
  IFN activity maintained disease. Blocking the shared receptor
  subunit blocks ALL ligands simultaneously, achieving complete
  pathway shutdown. This is the cleanest clinical proof of the
  "receptor > ligand" strategy when a receptor serves multiple
  ligands in the same pathway. For field 6 (failure/success modes),
  this is the headline distinction: rontalizumab failed because its
  mechanism was too narrow (ligand-specific), not because the
  pathway was wrong. For field 11 (differentiation), a receptor-level
  antibody is mechanistically superior to a ligand-level antibody
  for multi-ligand pathways — but carries broader on-target safety
  risk (see below). This generalizes the IL-17A brodalumab
  observation and the IL-7Rα shared-receptor-subunit observation:
  for targets where one receptor subunit is shared across multiple
  ligands or receptor complexes, targeting the shared subunit is
  the broader mechanism. The IFNAR1 case adds the clinical
  confirmation (approved vs failed) that was missing from the
  IL-17A/IL-7Rα cases.

  (2) **Endpoint selection can determine Phase III success or
  failure for the same drug.** TULIP-1 (anifrolumab Phase III) used
  SRI(4) as its primary endpoint and narrowly missed; TULIP-2 used
  BICLA (a composite requiring improvement in active disease AND no
  worsening in any organ system) as its primary endpoint and met it
  with P=0.001. The same drug, same dose, same population — a
  different primary endpoint turned a "failed" trial into an
  approval-enabling trial. For field 6, this is not a drug failure
  but a trial design issue. For SLE specifically (where endpoints
  are notoriously difficult), the BICLA endpoint may be more
  sensitive to IFN-pathway-targeted drugs than SRI(4), which
  requires a ≥4-point SLEDAI-2K reduction. When profiling
  IFN-pathway or cytokine-pathway antibodies in SLE, note which
  endpoint was used and whether the result is endpoint-dependent.

  (3) **On-target infection risk is an inherent cost of complete
  cytokine pathway blockade — not an off-target effect.** Blocking
  ALL type I IFN signaling through IFNAR1 compromises antiviral
  innate immunity, causing herpes zoster reactivation (5.1–7.2%
  anifrolumab vs 1.4–2.0% placebo across Phase II–III). This is
  mechanistically predictable: type I IFNs are the primary
  antiviral cytokines, and blocking their receptor impairs VZV
  immunity. The incidence was similar across IFNGS-high and
  IFNGS-low subgroups, confirming it is mechanism-driven, not
  subgroup-specific. For field 8 (safety), when a target's
  physiological role includes host defense, the on-target safety
  cost is inherent and manageable (VZV vaccination, antivirals)
  but cannot be eliminated by epitope or format engineering. This
  extends the C5/meningococcal pattern (complement blockade →
  encapsulated organism risk) to the antiviral cytokine domain
  (IFN blockade → viral reactivation risk). The general rule:
  blocking a pathway that serves host defense carries a
  predictable infection risk at the pathogen class the pathway
  protects against.

  (4) **IFNGS (interferon gene signature) as a predictive
  biomarker — greater treatment difference in IFNGS-high patients,
  but benefit present in both subgroups.** The pooled TULIP-1/TULIP-2
  analysis (PMID 35338035) showed treatment differences were
  greatest in IFNGS-high patients and those with ≥1 abnormal
  serological marker (low complement, anti-dsDNA+). However,
  benefit was observed in both IFNGS-high and IFNGS-low subgroups
  in TULIP-2. This is the biomarker pattern for a target where the
  pathway is broadly active (not restricted to biomarker-positive
  patients), but the magnitude of benefit is larger in
  biomarker-positive patients. For field 7 (biomarker assays),
  IFNGS is the key predictive biomarker — elevated in 50–73% of
  adult SLE patients. For field 6, the greater separation in
  IFNGS-high patients is consistent with the mechanistic rationale
  (patients with more active IFN signaling derive more benefit
  from blocking it). But the benefit in IFNGS-low patients
  suggests local tissue IFN signaling may not be captured by
  blood-based IFNGS assays — a caveat for biomarker-guided
  treatment strategies.

  (5) **100% full-text retrieval rate with the search-then-select
  delegation pattern in a mixed-publisher landscape.** 5/5 papers
  retrieved: 2 PMC XML OA (Arthritis Rheumatol, Ann Rheum Dis),
  2 Wayback Machine (NEJM, Scand J Immunol/Wiley), 1 jina reader
  (Springer/Drugs — reference-list masquerade, abstract used). The
  key enabler was selecting papers from OA-friendly journals where
  possible (Arthritis Rheumatol, Ann Rheum Dis are both PMC OA)
  plus NEJM (Wayback-recoverable) and Wiley (Wayback-recoverable).
  The only abstract-only-equivalent (Deeks/Drugs) was a review
  where the PubMed abstract was sufficient for the drug profile
  summary. This confirms the observation from IL-17A: journal
  mix determines retrieval rate. The search-then-select pattern
  (subagent runs esearch queries, selects from esummary metadata,
  then fetches) produces a well-curated paper set with higher
  OA-retrieval probability than pre-assigning PMIDs.

  (IFNAR1 profile, ~25K chars, 5 papers, 36 unique author slugs,
  working-docs/hitlist-profiles/ifnar1.md.)

- **2026-08-15 — IL-17RA key-paper-ingestion profile observations.**
  Nineteenth level-2 profile (approved tier, immunology/inflammation —
  psoriasis + psoriatic arthritis). IL-17RA is the shared co-receptor
  subunit for ALL IL-17 family cytokines (IL-17A, IL-17F, IL-17A/F,
  IL-17C, IL-17E/IL-25). Brodalumab (anti-IL-17RA IgG2, Siliq/Kyntheum)
  is the only approved anti-IL-17RA antibody. 5 key papers ingested
  (2/5 PMC XML OA — Majumder 2021 Annu Rev Immunol, Goepfert 2022
  Cell Reports; 1/5 Wayback — Lebwohl 2015 NEJM AMAGINE-2/3,
  abstract-level only; 2/5 abstract-only — Lebwohl 2018 JAAD and
  Krueger 2025 J Dermatol Sci, both Elsevier-blocked). ~28K chars,
  5 papers, 70 authors, 5 unique PMIDs cited. New observations:

  (1) **Tissue-dependent dual role is a distinct failure mode: the
  target is valid in one tissue and harmful to block in another.**
  IL-17 is pathogenic in skin (drives psoriatic inflammation) but
  protective in gut (maintains epithelial barrier, regulates microbiota,
  promotes tissue repair). IL-17RA blockade with brodalumab achieves
  the highest PASI 100 rates of any psoriasis biologic but was
  ineffective and exacerbated Crohn's disease — the same cytokine
  has opposite roles in different tissues. This is distinct from all
  previously documented failure modes: it's not wrong-target (the
  target works in skin), wrong-epitope (the antibody is fine),
  wrong-population (the population was correct), or wrong-endpoint
  (the Crohn's trials measured the right things). The failure is
  tissue-context-dependent: IL-17's homeostatic function in the gut
  outweighs its pathological contribution there. For field 6 (failure
  modes), when a cytokine/receptor has documented protective roles in
  one tissue and pathogenic roles in another, explicitly flag the
  tissue-dependent therapeutic window — the target is not globally
  valid or invalid, it's conditionally valid by tissue context. For
  field 11 (differentiation), a tissue-targeted delivery approach
  (skin-localized IL-17RA blockade sparing gut) could address this
  but is technically challenging for a systemic antibody. (PMID
  33577346, PMID 26422722.)

  (2) **Receptor-level blockade carries a neuroimmune safety dimension
  beyond the infection risk documented for IFNAR1.** Brodalumab's
  black box warning for suicidal ideation and behavior (SIB) may be
  mechanistically linked to its broad IL-17 family blockade: IL-17E/
  IL-25, which signals through IL-17RA, has documented neuroimmune
  functions (depression-like symptoms, neural-immune circuits, neuron
  excitability in mouse models — PMID 33577346). Anti-IL-17A antibodies
  (secukinumab, ixekizumab) that block only IL-17A do NOT carry the
  same SIB warning. This extends the IFNAR1 observation ("on-target
  infection risk from complete pathway blockade") into the
  neuroimmune domain: broader receptor-level blockade can touch
  ligands with CNS functions that ligand-specific antibodies don't
  engage. For field 8 (safety), when a shared receptor subunit serves
  ligands with neuroimmune roles, the receptor-level antibody's
  safety profile may include neuropsychiatric signals absent from
  ligand-specific antibodies. For field 11 (differentiation), this
  creates a safety-efficacy trade-off: receptor-level blockade offers
  broader efficacy (higher PASI 100) but may carry broader safety
  risks (SIB). A next-generation antibody that selectively blocks
  IL-17A/F binding via IL-17RA while sparing IL-17E/IL-25 binding
  could potentially eliminate the SIB signal while retaining psoriasis
  efficacy — this is a structurally enabled differentiation opportunity
  (the IL-17RA D1 domain has distinct binding sites for different IL-17
  family members — PMID 36260993). (PMID 28985956, PMID 33577346.)

  (3) **Receptor dimerization interface as a druggable target for
  partial blockade — a novel structural differentiation opportunity.**
  The Goepfert 2022 crystal structure (PMID 36260993, PDB 5n9b, 7zan)
  revealed that IL-17RA forms homodimers upon cytokine binding through
  a conserved interface (~750-820 Å², residues Thr69, Thr102, Asp103,
  Ala104, Ser105). The A104E dimerization-defective mutant retains
  IL-17A binding (SPR/ITC confirmed) but shows >5-fold reduced
  signaling sensitivity (EC50 shift for IL36G/CXCL1 induction). This
  is the first target profiled where the receptor's oligomerization
  interface — not the ligand-binding site — is a druggable target.
  An antibody targeting the dimerization interface could partially
  attenuate IL-17 signaling (reducing but not abrogating it),
  potentially offering a different efficacy-safety profile: enough
  blockade for psoriasis efficacy, potentially less on-target
  safety burden (candida risk, SIB signal). For field 5 (epitope
  landscape) and field 11 (differentiation), the dimerization
  interface is a structurally distinct epitope space from the
  ligand-binding site — it's not a competing epitope bin but a
  mechanistically different target. This generalizes to any
  receptor where ligand-induced oligomerization is required for
  signaling (cytokine receptors, RTKs): the oligomerization interface
  is a druggable target for partial blockade. (PMID 36260993.)

  (4) **Wayback snapshots of NEJM may return abstract-level content
  only, not full text.** The AMAGINE-2/3 pivotal trial (PMID 26422722,
  NEJM 2015) was retrieved via Wayback CDX API (multiple 200-status
  snapshots from 2015-2016), but the extracted content was
  abstract-level only (~2.3K chars) — the NEJM paywall prevented full
  article rendering even in the archived snapshot. This contrasts
  with the IFNAR1 profile where NEJM Wayback snapshots delivered full
  text. The difference may be snapshot age: 2015-era NEJM snapshots
  may have captured less rendered content than later snapshots. This
  confirms the paper-ingest skill's existing observation about
  multi-snapshot content variation but adds a new dimension: for
  NEJM specifically, even 200-status Wayback snapshots may be
  abstract-only if the paywall was active at the time of archiving.
  When the Wayback content is abstract-only, tag `fulltext_source:
  wayback` but note the content level — the profile can still cite
  the paper using the structured PubMed abstract.

  (5) **Two Elsevier papers (JAAD, J Dermatol Sci) confirm the
  deterministic Elsevier block.** Both PMID 28985956 (JAAD) and PMID
  41077515 (J Dermatol Sci) were abstract-only after three-source
  closure (EPMC inPMC=N, isOpenAccess=N, hasPDF=N; jina reader 404/
  422; no Wayback snapshots). J Dermatol Sci is a new Elsevier
  journal encounter but follows the same pattern as all previously
  documented Elsevier blocks (ScienceDirect, JAAD/JACI, Lancet
  family). No new publisher block entry needed — the Elsevier block
  is already comprehensively documented in the paper-ingest skill.

  (IL-17RA profile, ~28K chars, 5 papers, 70 authors, 5 unique PMIDs
  cited, working-docs/hitlist-profiles/il-17ra.md.)

- **2026-08-15 — IL-31Rα key-paper-ingestion profile observations.**
  Twentieth level-2 profile (approved tier, immunology/dermatology —
  prurigo nodularis + atopic dermatitis). IL-31Rα (IL31RA) is the
  receptor subunit for IL-31, the key cytokine driving chronic pruritus.
  Nemolizumab (anti-IL-31Rα, IgG4, Chugai→Galderma, Nemluvio/Mitchga)
  is the only approved anti-IL-31Rα antibody — approved for prurigo
  nodularis (FDA 2024) and atopic dermatitis. 5 key papers ingested
  (2/5 full-text: 1 Wayback NEJM, 1 jina-reader Lancet; 3/5
  abstract-only: Wiley/Allergy, Springer/Drugs ref-list masquerade,
  JAMA Dermatol PMCID-present-but-both-paths-fail). ~35K chars, 5
  papers, ~60 authors, 5 unique PMIDs cited. New observations:

  (1) **Itch-specific vs broad Th2 blockade is a distinct mechanistic
  differentiation pattern.** Nemolizumab (anti-IL-31Rα) specifically
  blocks the IL-31/itch pathway, while dupilumab (anti-IL-4Rα) broadly
  suppresses Th2 inflammation (IL-4 + IL-13). The NEJM trial discussion
  explicitly compares the two: "Dupilumab and nemolizumab have
  different treatment profiles." Nemolizumab's itch-specific mechanism
  provides rapid itch relief (detectable at week 1 in ARCADIA) but may
  not fully control all inflammatory components of AD — this is a
  narrower mechanistic profile than dupilumab's broad Th2 blockade.
  For field 6 (failure modes) and field 11 (differentiation), when a
  target's mechanism is pathway-specific (itch) vs broad
  (inflammation), the competitive positioning differs by indication:
  itch-dominant diseases (prurigo nodularis, where itch IS the
  pathology) favor the specific blocker; inflammation-dominant diseases
  (AD with significant skin lesions) may favor the broad blocker.
  Nemolizumab was approved for PN first — the indication where itch
  specificity is most advantageous. (PMID 32640132, 39067461.)

  (2) **"Worsening despite improvement" is a new paradoxical AE
  variant.** In the JP01 trial, worsening atopic dermatitis occurred in
  24% of nemolizumab patients (vs 21% placebo) — yet those patients
  still had reductions in pruritus VAS scores. The worsening AD was
  NOT correlated with the efficacy outcome. This is mechanistically
  distinct from on-target toxicity (the target is working — itch is
  reduced) and from lack of efficacy (the primary endpoint was met).
  It suggests the target pathway (IL-31) controls itch but not all AD
  inflammation — residual inflammation from other cytokines (IL-4,
  IL-13, IL-33) continues to drive skin lesions even when itch is
  suppressed. For field 6 (failure modes), this "partial pathway
  coverage" paradox is a new failure-mode variant: the antibody
  succeeds at its primary mechanism (itch blockade) but the disease
  has parallel inflammatory pathways that the target doesn't address.
  For field 8 (safety), worsening AD as an AE despite pruritus
  improvement should be flagged as a target-specific signal, not a
  generic drug toxicity. (PMID 32640132.)

  (3) **TARC/CCL17 elevation as a pharmacodynamic marker of unclear
  significance.** The JP01 trial found TARC increases occurred only in
  the nemolizumab group, not associated with EASI score changes. This
  is a cytokine homeostasis alteration from IL-31Rα blockade — the
  mechanism is unclear but it's not clinically significant in the
  trial. For field 8 (safety), cytokine biomarker shifts (like TARC)
  that occur only in the treatment group but lack clinical
  correlation should be noted as pharmacodynamic markers requiring
  long-term monitoring, not as actionable safety signals. (PMID
  32640132.)

  (4) **JAMA Network PMCID-present variant documented in paper-ingest
  skill.** PMID 39602139 (JAMA Dermatol, OLYMPIA 1) has a PMCID
  (PMC11840645, inPMC=Y) but both PMC XML (front-matter only) and EPMC
  PDF render (HTTP 404) fail — the same Branch 1b pattern as Blood/ASH.
  Updated the JAMA Network known-blocks table entry in paper-ingest
  with this PMCID-present variant. For target profiling, this means
  JAMA Dermatol papers — even with a PMCID — are abstract-only, and
  the profile must rely on the structured PubMed abstract for clinical
  trial data. (PMID 39602139.)

  (5) **Lancet PIIS URL form confirmed for a third profile session.**
  PMID 39067461 (Lancet, ARCADIA 1/2) was retrieved via jina reader
  using PIIS URL form — 14K bytes with complete structured abstract
  and results. Key detail for future sessions: the DOI suffix
  "S0140-6736(24)01203-0" starts with "S", which combines with "PII"
  to form "PIIS" — do NOT add an extra "S". (PMID 39067461.)

  (IL-31Rα profile, ~35K chars, 5 papers, ~60 authors, 5 unique PMIDs
  cited, working-docs/hitlist-profiles/il-31ra.md.)

- **2026-08-15 — IL-5 key-paper-ingestion profile observations.**
  Twenty-first level-2 profile (approved tier, immunology/inflammation
  — eosinophilic asthma, EGPA, HES, CRSwNP). IL-5 is the key cytokine
  for eosinophilopoiesis. Three approved antibodies target IL-5/IL-5R
  (mepolizumab anti-IL-5 IgG1, reslizumab anti-IL-5 IgG4, benralizumab
  anti-IL-5Rα afucosylated IgG1) and depemokimab (anti-IL-5,
  ultra-long-acting) is in late-stage development. 5 key papers
  ingested (4/5 full text: 1 PMC XML OA, 1 jina-reader Lancet PIIS,
  2 Wayback NEJM; 1/5 abstract-only — Elsevier/Pulm Pharmacol Ther,
  three-source closure). ~32K chars, 5 papers, ~45 unique author
  slugs, 5 unique PMIDs cited. New observations:

  (1) **Lineage-restricted cytokine target produces the cleanest safety
  profile in the entire profile set.** IL-5Rα expression is highly
  restricted to the eosinophil lineage — no other immune cell types
  respond to IL-5. This explains why anti-IL-5 antibodies have a safety
  profile similar to placebo across all Phase 3 trials: no
  immunosuppression, no infection increase, no malignancy signal. This
  contrasts sharply with broader cytokine blockade (IFNAR1 → herpes
  zoster reactivation, IL-17RA → candida/SIB, C5 → meningococcal risk).
  For field 6 (success factors) and field 8 (safety), when a cytokine's
  receptor is lineage-restricted (one cell type), the on-target safety
  cost is minimal — the therapeutic index is inherent in the target
  biology, not engineered through epitope or format choice. This is the
  cleanest clinical validation of the "narrow target = wide therapeutic
  index" principle. (PMID 22901886, 25199059, 39248309, 31920718.)

  (2) **Biomarker-selected population was the clinical breakthrough —
  the clearest example in the profile set.** Early anti-IL-5 studies in
  unselected asthma populations showed weak or negative signals. The
  DREAM trial (PMID 22901886) defined the phenotypic characteristics
  of responders (blood eosinophil count ≥150/μL at screening or
  ≥300/μL in prior 12 months, history of exacerbations, high-dose ICS
  use) and achieved ~50% exacerbation reduction. MENSA (PMID 25199059)
  confirmed these criteria. Reslizumab used a higher threshold (≥400/μL)
  and depemokimab used the mepolizumab criteria. For field 6 (failure
  modes), this is the canonical example of wrong-population failure:
  the target was correct, the antibody was correct, but treating
  unselected asthma (including T2-low/neutrophilic phenotypes) diluted
  the effect to non-significance. The fix was not a new antibody or
  epitope — it was a companion biomarker. For field 7 (biomarker
  assays), blood eosinophil count is the companion diagnostic for all
  approved anti-IL-5 antibodies — the first profile where the same
  biomarker gates all approved drugs against the same target.

  (3) **Shared βc receptor subunit creates a ligand-vs-receptor
  strategy distinction complementary to IFNAR1.** IL-5 signals through
  IL-5Rα (specific, eosinophil-restricted) + βc (shared with IL-3
  and GM-CSF). All approved antibodies target either the IL-5 ligand
  (mepolizumab, reslizumab, depemokimab) or IL-5Rα (benralizumab) —
  none target βc, because βc blockade would also inhibit IL-3 and
  GM-CSF signaling (broader myeloid effects). This mirrors the IFNAR1
  pattern in reverse: for IFNAR1, receptor-level blockade (anifrolumab)
  succeeded over ligand-level (anti-IFN-α) because the shared receptor
  was the broader target. For IL-5, ligand-level or specific-receptor-α
  blockade is preferred over shared-βc blockade because the shared
  subunit serves other cytokines whose blockade is undesirable. The
  general rule: when a receptor subunit is shared, the choice between
  ligand-specific vs shared-subunit targeting depends on whether
  blocking all ligands through the shared subunit is therapeutically
  desirable (IFNAR1: yes — all type I IFNs drive SLE) or undesirable
  (IL-5/βc: no — IL-3 and GM-CSF have distinct, needed functions). For
  field 11 (differentiation), the βc subunit is NOT a viable target
  for an antibody seeking to improve on existing anti-IL-5 therapy.

  (4) **Ultra-long-acting antibody as a dosing-frequency differentiation
  strategy.** Depemokimab achieves 6-monthly dosing (vs. 4-weekly for
  mepolizumab/reslizumab, 8-weekly for benralizumab) through enhanced
  binding affinity for IL-5, while maintaining comparable ~50%
  exacerbation reduction (SWIFT-1: 58%, SWIFT-2: 48%). For field 4
  (antibody landscape) and field 11 (differentiation), dosing
  frequency is a clinically meaningful differentiation axis for
  chronic biologics: fewer injections improve adherence, reduce
  healthcare utilization, and expand access. This is the first
  profile where a next-generation antibody's primary differentiation
  is PK/dosing (not epitope, mechanism, or format). The SWIFT
  secondary endpoint failure (SGRQ non-significant → hierarchical
  testing stopped) is a trial-design limitation, not a drug
  efficacy issue — the primary endpoint (exacerbation reduction) was
  robustly positive. (PMID 39248309.)

  (5) **Lancet PIIS URL form confirmed for a fourth profile session.**
  PMID 22901886 (Pavord 2012, DREAM trial, Lancet) was retrieved via
  jina reader using the PIIS URL form
  (thelancet.com/journals/lancet/article/PIIS0140-6736(12)60988-X/
  fulltext) — 61 KB, 31 section headings including full structured
  abstract with Background/Methods/Findings/Interpretation/Funding.
  This is the fourth confirmation of the PIIS URL technique (after
  IL-17A/IL-17F, CD22, IL-31Rα). For DREAM specifically, the
  DOI is 10.1016/S0140-6736(12)60988-X and the PIIS form is
  PIIS0140-6736(12)60988-X — note the DOI suffix starts with "S",
  combining with "PII" to form "PIIS" without an extra "S". (PMID
  22901886.)

  (6) **Late-onset phenotype as a within-target responder stratification
  factor.** The Brusselle post hoc analysis (PMID 28159511) found
  that reslizumab produced 75% exacerbation reduction in late-onset
  eosinophilic asthma (onset ≥40 years) vs. 42% in early-onset
  disease (interaction p=0.0083). Late-onset asthma is ILC2-driven
  (not Th2-driven), potentially more IL-5–dependent. For field 6
  (success factors), within-target phenotype stratification (by age
  of onset, not just biomarker count) can identify ultra-responder
  populations. For field 11 (differentiation), a development strategy
  focused specifically on the late-onset phenotype could achieve
  higher effect sizes than the broad eosinophilic asthma population.
  This is complementary to the biomarker-selected population strategy:
  the biomarker (eosinophil count) gates eligibility; the phenotype
  (onset age) predicts magnitude of response. (PMID 28159511.)

  (IL-5 profile, ~32K chars, 5 papers, ~45 unique author slugs, 5
  unique PMIDs cited, working-docs/hitlist-profiles/il-5.md.)

- **2026-08-15 — IL-6R key-paper-ingestion profile observations.**
  Twenty-second level-2 profile (approved tier, immunology/inflammation
  — RA, GCA, CRS, NMOSD, systemic sclerosis). IL-6R is the receptor for
  IL-6, existing in both membrane-bound (mIL-6R) and soluble (sIL-6R)
  forms. 4 approved anti-IL-6R antibodies (tocilizumab, sarilumab,
  satralizumab, levilimab) plus the selective trans-signalling inhibitor
  sgp130Fc/olamkicept (Phase 2). 5 key papers selected, 3 new paper
  pages written, 2 already existed in the brain. ~40K chars, 5 PMIDs
  cited. New observations:

  (1) **Classical vs trans-signalling duality is the clearest example
  of "selective pathway blockade" as a differentiation opportunity.**
  IL-6R signals via three modes: classical (mIL-6R on hepatocytes and
  some immune cells), trans-signalling (sIL-6R on cells lacking mIL-6R
  via gp130), and cluster signalling (IL-6–mIL-6R on transmitter cell
  activating gp130 on receiver cell). Anti-IL-6R antibodies (tocilizumab,
  sarilumab, satralizumab) block ALL modes globally. The selective
  trans-signalling inhibitor sgp130Fc (olamkicept) blocks only
  trans-signalling, preserving the regenerative and anti-inflammatory
  classical pathway. The clinical rationale: global IL-6R blockade
  causes intestinal perforation (classic IL-6 signalling mediates
  epithelial regeneration) — selective trans-signalling blockade
  avoids this on-target toxicity. This is the strongest profiled case
  where a selective pathway inhibitor (sgp130Fc) has a mechanistic
  safety advantage over global blockade, and it is the first target
  with a three-mode signalling architecture (vs the two-mode
  classical/trans pattern noted for IL-7Rα). For field 6 (failure/
  success modes) and field 11 (differentiation), targets with
  classical + trans-signalling duality (IL-6R, IL-11R) should
  explicitly evaluate whether selective trans-signalling blockade
  offers a safety advantage over global blockade. (PMID 37069261,
  PMID 33715009.)

  (2) **Anti-IL-6R succeeded more broadly than anti-IL-6 ligand — the
  receptor > ligand pattern with a twist.** Tocilizumab (anti-IL-6R)
  and sarilumab (anti-IL-6R) are approved for RA, GCA, CRS, NMOSD, and
  systemic sclerosis. Siltuximab (anti-IL-6) is approved only for
  Castleman disease; sirukumab (anti-IL-6) was rejected for safety;
  olokizumab and clazakizumab (anti-IL-6) are delayed. This extends
  the IFNAR1 receptor-vs-ligand observation with a NEW dimension: for
  IFNAR1, receptor-level won because the shared receptor blocks ALL
  ligands (IFN-α, -β, -ω, -ε, -κ). For IL-6R, both anti-IL-6 and
  anti-IL-6R neutralize the SAME ligand — the difference is NOT
  multi-ligand coverage. The difference is (a) anti-IL-6R also blocks
  IL-6R-dependent CNTF and IL-30/IL-27 signalling (cytokine crosstalk
  through the shared IL-6R), (b) anti-IL-6 forms immune complexes that
  increase circulating IL-6 levels (observed in Castleman disease —
  treatment discontinued), and (c) pharmacokinetic differences. For
  field 6 (failure modes) and field 11 (differentiation), when
  comparing anti-ligand vs anti-receptor antibodies targeting the SAME
  pathway, the receptor-level approach may be superior even when the
  ligand count is one, due to cytokine crosstalk through the shared
  receptor, immune complex pharmacokinetics, and off-target pathway
  blockade. (PMID 37069261.)

  (3) **Pre-existing paper pages reduce ingestion work — always check
  both `papers/` (brain) AND `working-docs/hitlist-profiles/papers/`
  (abstract-only staging directory) before searching PubMed.** 2 of 5
  selected landmark papers (PMID 25190079, Tanaka 2014; PMID 30995492,
  Kang 2019) already existed as paper pages in the brain from a prior
  profiling session. The dedup check (Phase 2 of paper-ingest) caught
  these before redundant ingestion. For orchestrators dispatching
  profiling subagents: when multiple profiles in the same therapeutic
  area share landmark papers (common for cytokine biology reviews),
  the dedup step saves significant time. The orchestrator can
  pre-check `papers/` for known key PMIDs and pass this information to
  the subagent. (PMID 25190079, PMID 30995492.)

  **Corollary (HMPV F profile, 2026-08-17): when the ENTIRE 3-5
  paper corpus already exists, skip PubMed search entirely.** All
  15 selected HMPV F papers were already ingested as abstracts in
  `working-docs/hitlist-profiles/papers/` — a staging subdirectory
  under the profiles working doc, distinct from the brain `papers/`
  directory. Subagents had collected them in a prior session and left
  them as `pmid_<id>.md` stubs plus a `hmpv_f_abstracts.json` summary.
  Because the full required corpus (3-5 papers; here 15) was already
  present, the profiling subagent skipped the PubMed E-utilities
  search step altogether and proceeded straight to reading the
  existing pages and writing the profile — saving ~3-5 minutes of
  API calls and rate-limit waits. **Two-directory check before
  searching PubMed:** (1) `papers/` (brain — full distillations),
  (2) `working-docs/hitlist-profiles/papers/` (abstract-only staging
  stubs from prior profiling sessions, often named `pmid_<id>.md`
  with an accompanying `<slug>_abstracts.json`). A `search_files` or
  `ls` for `pmid_*` / the target slug in the staging dir is a
  2-second check that can eliminate the entire search phase. Only
  fall back to PubMed E-utilities when the existing corpus is thinner
  than the 3-5 landmark papers the profile needs. (HMPV F profile,
  14 unique PMIDs cited,
  working-docs/hitlist-profiles/hmpv-f-glycoprotein.md.)

  (4) **Recycling antibody technology (satralizumab) is a PK-based
  differentiation strategy complementing the depemokimab ultra-long-
  acting pattern.** Satralizumab (anti-IL-6R, IgG2) uses pH-dependent
  binding to IL-6R: the antibody dissociates from IL-6R in the acidic
  endosome and is recycled to the circulation, extending its half-life
  and enabling subcutaneous dosing every 4 weeks. This is a second
  PK-based differentiation strategy (after depemokimab's 6-monthly
  dosing via enhanced affinity) observed in the profile set. The
  difference: depemokimab achieves long dosing intervals through
  higher affinity (slower off-rate), while satralizumab achieves it
  through antibody recycling (pH-dependent binding). For field 4
  (antibody landscape) and field 11 (differentiation), both PK
  engineering approaches — affinity enhancement and recycling
  technology — are validated clinical differentiation strategies for
  chronic-use antibodies where dosing frequency matters. (PMID
  33715009.)

  (5) **J-STAGE (Japan Science and Technology Information Aggregator)
  full text via jina reader.** PMID 31875623 (Kishimoto 2019, Keio J
  Med) was published on J-STAGE (`jstage.jst.go.jp`). No PMCID, no
  OA, EPMC all flags N. The jina reader proxy on the resolved
  publisher URL returned 18.9 KB containing the full abstract but
  no body text beyond it — this is a short review article where the
  abstract IS the primary content. Tagged `fulltext_source: jina-
  reader` with a note that the content is abstract-level. J-STAGE is
  a new publisher encounter — it is not a hard block (jina succeeded)
  but may deliver abstract-level content for short-format articles.
  For papers from Japanese journals (Keio J Med, Int Immunol), jina
  reader is the first-line retrieval path after EPMC. (PMID
  31875623.)

  (6) **On-target safety from blocking a dual-pathway receptor:
  intestinal perforation and hyperlipidemia.** Global IL-6R blockade
  blocks both the pro-inflammatory trans-signalling AND the
  regenerative classical signalling. Intestinal perforation occurs
  because classical IL-6 signalling via mIL-6R mediates intestinal
  epithelial regeneration — blocking it compromises mucosal repair.
  Hyperlipidemia occurs because IL-6 suppresses hepatic lipogenesis —
  blockade reverses this, raising LDL. These are on-target, mechanism-
  based toxicities intrinsic to global IL-6R blockade — they cannot be
  addressed by epitope or format engineering. The selective trans-
  signalling inhibitor (sgp130Fc) preserves classical signalling and
  is specifically designed to avoid the intestinal perforation risk.
  For field 8 (safety), when a target has both pathological
  (trans-signalling) and protective (classical) signalling modes, the
  on-target safety profile of global blockade includes the loss of
  the protective pathway's physiological function — enumerate which
  protective functions are compromised. For field 11
  (differentiation), selective blockade of the pathological mode is
  the primary differentiation opportunity. (PMID 37069261.)

  (IL-6R profile, ~40K chars, 5 papers [3 new, 2 pre-existing], 6
  unique author slugs proposed, 5 unique PMIDs cited,
  working-docs/hitlist-profiles/il-6r.md.)

- **2026-08-16 — DLL3/CD3 bispecific (tarlatamab) key-paper-ingestion
  profile observations.** Twenty-third level-2 profile (approved tier,
  oncology — SCLC, solid tumor). DLL3/CD3 is the **first bispecific
  T-cell engager profile for a SOLID TUMOR** and the **first
  "ADC failed, BiTE succeeded" graveyard-to-success story** in the
  profile set. Tarlatamab (Imdelltra, Amgen, HLE BiTE targeting DLL3
  on tumor cells × CD3 on T cells) was FDA-accelerated-approved May
  2024 for ES-SCLC after platinum chemotherapy. The prior DLL3-targeted
  ADC rovalpituzumab tesirine (Rova-T) FAILED Phase 3 (TAHOE: OS 6.3
  vs 8.6 months topotecan; MERU: 8.8 vs 9.9 months placebo). 5 key
  papers ingested at 100% full-text rate (4 PMC XML OA — J Hematol
  Oncol, Mol Cancer, Cancer; 1 publisher-jina for a Springer/Adis
  drug review with no PMCID/OA). ~57K chars, 247 PMID citations across
  5 key PMIDs, 43 unique authors. New observations:

  (1) **ADC failed → BiTE succeeded: format change from payload-
  dependent killing to immune-effector redirection.** This is the
  REVERSE of the CD30 pattern (naked Ab failed → ADC succeeded by
  ADDING a payload). For DLL3, the ADC (Rova-T) had the payload but
  failed because of PBD warhead toxicity (serosal effusions,
  thrombocytopenia, photosensitivity, skin reactions ~60% grade ≥3
  in Phase 3), preventing adequate dosing. The BiTE (tarlatamab)
  SUCCEEDED by ELIMINATING the cytotoxic payload entirely — replacing
  payload-dependent killing with T cell redirection (perforin/
  granzyme-mediated lysis). The toxicity profile shifted from
  payload-driven (ADC: effusions, thrombocytopenia, skin) to
  immunostimulatory (BiTE: CRS 53% mostly grade 1-2, ICANS 10% all
  grade 1-2), and the immunostimulatory toxicity proved more
  clinically manageable (step-up dosing, dexamethasone prophylaxis,
  tocilizumab). For field 6, when an ADC fails due to payload
  toxicity (not target invalidity), a BiTE against the same target
  is a validated rescue strategy — the target remains valid, the
  format must change. This extends the CD30 "format is THE success
  factor" insight: the winning format can be a DIFFERENT modality
  entirely, not just an improved version of the same modality. For
  field 11, the differentiation case for a new DLL3-targeting antibody
  must address whether the ADC format can be rescued with a non-PBD
  payload (ZL-1310 with camptothecin is in development) or whether
  the BiTE format is inherently superior for this target class.
  (PMID 31215500, PMID 37355629, PMID 38730427.)

  (2) **MHC-I independence is a solid-tumor-specific TCE advantage.**
  SCLC downregulates MHC-I to evade immune surveillance — this is a
  common immune evasion mechanism in solid tumors but less relevant
  in hematological malignancies (the setting for all prior BiTE
  profiles: blinatumomab/CD19-CD3, teclistamab/BCMA-CD3). TCEs
  activate T cells independent of MHC-I, bypassing this evasion. For
  field 2 (biological mechanism) and field 6 (success factors) of
  solid-tumor TCE profiles, explicitly note the MHC-I downregulation
  pattern in the tumor type and how the BiTE mechanism overcomes it.
  This is the key biological rationale for TCEs in solid tumors with
  impaired antigen presentation — it distinguishes TCEs from
  checkpoint inhibitors (which require intact MHC-I antigen
  presentation). (PMID 37355629.)

  (3) **PBD (pyrrolobenzodiazepine) payload toxicity is a distinct
  payload class profile.** The skill already documents calicheamicin
  (CD22: VOD/SOS), Pseudomonas exotoxin (CD22: HUS/CLS), and MMAE
  (CD30: neuropathy, neutropenia). PBD dimer toxicity is a fourth
  distinct profile: serosal effusions (pleural 31%, pericardial 12%
  in Phase 1), thrombocytopenia (11% grade ≥3), photosensitivity
  (7% grade ≥3), and skin reactions (8% grade ≥3, including
  erythema multiforme, palmar-plantar erythrodysesthesia). The
  proposed mechanisms are premature linker cleavage ("early cleavage")
  releasing PBD into circulation before target-cell internalization,
  and a bystander effect where released warhead diffuses to healthy
  non-target cells. For field 8 (safety) of any ADC profile with a
  PBD payload, the serosal effusion + photosensitivity + skin
  reaction triad is the characteristic PBD toxicity signature. For
  field 6, PBD payload toxicity is a format-specific failure mode
  — the ADC format with PBD is the problem, not the target. A
  next-generation ADC with a different payload (camptothecin,
  maytansinoid, auristatin) could rescue the ADC approach.
  (PMID 31215500, PMID 38730427.)

  (4) **Dysgeusia as an on-target, off-tumor AE from low-level target
  expression in normal tissue.** Tarlatamab causes dysgeusia (32%
  of patients) because ASCL1 — the transcription factor that drives
  DLL3 expression in SCLC — also regulates taste bud cell
  differentiation, and taste bud cells express DLL3. The BiTE
  redirects T cells to kill these DLL3-expressing taste bud cells.
  This is a distinct on-target toxicity pattern: not from the
  target's signaling function (like IL-6R intestinal perforation)
  but from low-level target expression in a normal tissue (taste
  buds) that shares a transcriptional regulator with the tumor.
  For field 8 (safety) of TCE/BiTE profiles, on-target off-tumor
  toxicity can arise from ANY normal tissue expressing the target,
  even at low levels, because T cell redirection is not selective
  for tumor vs normal cells expressing the same surface antigen.
  The therapeutic index of a BiTE depends on the RATIO of target
  expression (tumor vs normal), not just the presence/absence. For
  DLL3, the ratio is favorable (high surface expression in tumor
  vs low cytoplasmic in normal), but taste buds are an exception
  (surface DLL3 at low levels). (PMID 39876075.)

  (5) **Springer/Adis drug review retrieved via publisher-jina proxy.**
  PMID 39023700 (Dhillon 2024, Drugs — "Tarlatamab: First Approval")
  had no PMCID, no OA, inPMC=N. The fetch_fulltext.py script
  resolved doi.org to the Springer link.springer.com URL and
  retrieved 23K chars via the jina reader proxy (provenance:
  publisher-jina). This is the first profile where a Springer/Adis
  drug-approval review was successfully retrieved at full-text level
  via jina — extending the publisher-jina success cases beyond
  Annual Reviews (CD22) and J-STAGE (IL-6R). Springer drug-approval
  reviews (Drugs, Adis Insight profiles) are high-value for field 4
  (antibody landscape) and field 3 (disease evidence) because they
  contain approval date, regulatory pathway, dosing, and clinical
  trial summaries in a single source. (PMID 39023700.)

  (6) **DLL3 biomarker inconsistency — expression level does not
  predict response.** Despite the rationale that DLL3-high patients
  should respond better, clinical data are inconsistent across
  modalities. Rova-T FIH showed DLL3-high ORR 35% vs DLL3-low 0%,
  but Phase 2/3 did not confirm this. Tarlatamab DeLLphi-300 showed
  only a weak DLL3-response association; DeLLphi-301 showed responses
  regardless of DLL3 expression status. Possible explanations:
  limited FIH sample size, IHC technique variability, lack of
  contemporaneous biopsies in a rapidly progressive disease, and
  heterogeneity between primary and metastatic DLL3 expression.
  Tarlatamab is approved WITHOUT a companion diagnostic. For field
  7 (biomarker assays) of DLL3-targeted therapy profiles, note that
  DLL3 IHC is not a reliable predictive biomarker; emerging
  alternatives (DLL3+/CD45- CTCs, immunoPET) may improve patient
  selection. This is the first profile where the target expression
  biomarker is biologically rational but clinically unreliable —
  a caution against assuming that target expression always predicts
  response to target-directed therapy. (PMID 37355629, PMID 38730427.)

  (DLL3/CD3 profile, ~57K chars, 5 papers, 247 PMID citations, 43
  unique authors, working-docs/hitlist-profiles/dll3-cd3.md.)

- **2026-08-16 — gp100/CD3 bispecific (tebentafusp/ImmTAC) key-paper-
  ingestion profile observations.** Twenty-fourth level-2 profile
  (approved tier, oncology — uveal melanoma, solid tumor). gp100/CD3
  is the **first TCR-based bispecific** (ImmTAC) profile — fundamentally
  different from all prior BiTE profiles (blinatumomab/CD19-CD3,
  teclistamab/BCMA-CD3, tarlatamab/DLL3-CD3) which use antibodies for
  both arms. Tebentafusp (Kimmtrak, Immunocore) uses an engineered TCR
  for the tumor-targeting arm (recognizing the intracellular gp100280-288
  peptide presented by HLA-A*02:01) and an anti-CD3 scFv for the T-cell
  engaging arm. FDA approved January 2022 — the first approved TCR-based
  bispecific and the first approved therapy for uveal melanoma. 5 key
  papers ingested (4/5 full text via PMC XML OA — Clin Cancer Res,
  Ther Adv Med Oncol, J Immunother Cancer, Curr Opin Oncol; 1/5
  abstract-only — NEJM paywalled, jina blocked by Cloudflare,
  Wayback partial HTML only). ~31K chars, 107 PMID citations, 72
  authors, 5 unique PMIDs cited. New observations:

  (1) **TCR-based bispecific vs BiTE: the ImmTAC paradigm shift.** All
  prior bispecific profiles used antibodies for both arms (anti-tumor
  scFv + anti-CD3 scFv). Tebentafusp uses a soluble affinity-enhanced
  TCR for the tumor-targeting arm, recognizing a peptide-MHC complex
  (pHLA) rather than a cell-surface protein. This is the fundamental
  architectural distinction: BiTEs target cell-surface proteins (~10% of
  the proteome); ImmTACs target intracellular antigens presented on
  MHC class I (~90% of the proteome). For field 1 (target identity) and
  field 2 (biological mechanism) of TCR-based bispecific profiles,
  explicitly state that the target is a pHLA complex, not a surface
  protein, and that the TCR arm (not an antibody fragment) provides
  tumor specificity. The construct size is similar to a BiTE (~55 kDa)
  but the target space is fundamentally larger. For field 11
  (differentiation), the ImmTAC format's ability to target intracellular
  antigens is THE differentiation vs BiTEs — it is not a format tweak
  but a different druggable universe. (PMID 32816891, 35880455.)

  (2) **HLA restriction is the defining constraint of TCR-based
  bispecifics.** Tebentafusp requires HLA-A*02:01-positive patients
  (~30% of Caucasian populations, ~20-25% of Black/South Asian
  populations). This is analogous to a companion diagnostic but is a
  genetic restriction (HLA haplotype), not a biomarker (expression
  level). For field 6 (failure modes), HLA restriction is a population-
  level failure mode: a significant proportion of patients are
  fundamentally ineligible, not merely unlikely to respond. For field
  10 (competitive landscape), this limits market size directly (only
  HLA-A*02:01+ patients are eligible). For field 11
  (differentiation), developing ImmTACs against alternative HLA
  haplotypes (e.g., HLA-A*01, HLA-B*07) to cover non-A*02:01 patients
  is a direct expansion strategy. This constraint has no analog in
  BiTE profiles (BiTEs target surface proteins regardless of HLA
  type). (PMID 36970111.)

  (3) **Survival benefit dissociated from RECIST response — the most
  extreme example in the profile set.** Tebentafusp's phase 3 ORR is
  only ~9% (first-line) / 5% (previously treated), yet the OS benefit
  is robust (HR 0.51, P<0.001). Critically, a survival benefit was
  observed even in patients with best response of progressive disease
  (OS 15.3 vs 6.5 months, HR 0.43). This is a more extreme RECIST-OS
  disconnect than tarlatamab (which had ORR 40% with OS benefit) or
  blinatumomab (which had high CR rates). The proposed mechanism:
  tebentafusp modulates the tumor microenvironment (increased T-cell
  infiltration, cytokine release, epitope spreading) in ways that
  slow disease progression without shrinking measurable lesions. For
  field 6 (success factors), this means OS — not ORR — must be the
  primary endpoint for ImmTAC/TCE trials in solid tumors. For field 7
  (biomarker assays), ctDNA reduction at week 9 correlates linearly
  with OS and may be a better early response marker than RECIST. For
  field 6 (failure modes), the low ORR creates regulatory and clinical
  decision-making challenges — standard response criteria may
  prematurely disqualify benefiting patients. (PMID 34551229, 38844408,
  36970111.)

  (4) **On-target skin toxicity from lineage antigen expression on
  normal tissue.** gp100 is expressed on normal melanocytes, causing
  rash (83%), pruritus (69%). This is the same on-target off-tumor
  pattern as DLL3/taste buds (tarlatamab dysgeusia) but at much higher
  incidence — because melanocytes are abundant in skin while DLL3
  expression in taste buds is sparse. For field 8 (safety) of TCE/ImmTAC
  profiles targeting lineage antigens (melanocyte, B-cell, epithelial),
  on-target off-tumor toxicity is inherent to the target choice and
  scales with the abundance of the target in normal tissue. The
  toxicity is manageable (2% discontinuation, decreases after first
  3-4 doses) but is NOT a format problem — it cannot be solved by
  epitope or format engineering. It can only be solved by conditional
  activation (prodrug TCEs active only in the TME). For field 11
  (differentiation), conditional/prodrug ImmTACs are the primary
  strategy to reduce on-target skin toxicity from melanocyte gp100
  expression. (PMID 34551229, 35880455.)

  (5) **Step-up dosing is universal across TCE/ImmTAC modalities.**
  Tebentafusp uses a step-up regimen (20→30→68 µg over 2 weeks) to
  reduce CRS during induction — the same principle as tarlatamab's
  step-up dosing. Cytokine levels peak 4-6h post-infusion and decrease
  with subsequent doses. This confirms the step-up dosing pattern as
  universal for CD3-engaging bispecifics regardless of the
  tumor-targeting arm (antibody or TCR). For field 4 (antibody
  landscape) and field 8 (safety), step-up dosing is a standard design
  element for all TCE/ImmTAC constructs and should be documented as
  part of the dosing regimen. (PMID 36970111.)

  (6) **4/5 PMC XML OA success rate — the highest full-text retrieval
  rate for a solid-tumor oncology profile.** Four of five papers had
  PMCIDs with OA full text (Clin Cancer Res, Ther Adv Med Oncol, J
  Immunother Cancer, Curr Opin Oncol — all OA-friendly journals). Only
  the NEJM pivotal trial paper (PMID 34551229) was inaccessible — NEJM
  paywalled, jina blocked by Cloudflare, Wayback returned partial HTML
  with only the meta description. The NEJM abstract, however, was
  comprehensive (2,200 chars with full trial design, OS/PFS/safety data)
  — sufficient for profile grounding without full text. For
  orchestrators: ImmTAC/TCR-based bispecific papers tend to appear in
  immunology/oncology OA journals (high retrieval rate); the NEJM
  pivotal trial is the expected exception, but the NEJM structured
  abstract is typically self-sufficient for the profile. (PMID
  34551229, 32816891, 36970111, 38844408, 35880455.)

  (gp100/CD3 profile, ~31K chars, 5 papers, 107 PMID citations, 72
  authors, 5 unique PMIDs cited,
  working-docs/hitlist-profiles/gp100-cd3.md.)

- **2026-08-16 — Transthyretin (TTR) key-paper-ingestion profile
  observations.** Twenty-sixth level-2 profile (approved tier,
  neuroscience/cardiovascular — ATTR amyloidosis). TTR is the **second
  amyloid-targeting antibody profile** (after Aβ) and the **first
  non-neurodegenerative amyloid target** — ATTR deposits in peripheral
  nerves (ATTR-PN) and heart (ATTR-CM), not brain. Also the **first
  profile where non-antibody therapies dominate** (tafamidis,
  patisiran, inotersen, vutrisiran) and antibodies are the emerging
  modality. 5 papers ingested, 4/5 PMC XML OA (MDPI-family journals),
  1/5 abstract-only (Elsevier Neurochem Int). ~49K chars, 150 PMID
  citations. See `references/transthyretin-profile-observations.md`
  for full observations. Key new patterns: (1) **Conformation-specific
  cryptotope approach** — structure-based epitope selection comparing
  native tetramer vs. monomer/fibril accessibility; epitope burial
  depth is a quantifiable design parameter (13% accessible for TTR
  89-97). (2) **Native protein sequestration** — high circulating TTR
  (3.6–7.2 µM) can sequester antibodies with weak tetramer binding;
  deeply buried epitopes are preferred. (3) **Dual mechanism** —
  fibril inhibition (substoichiometric) + Fc-mediated immune
  clearance; distinct from both anti-Aβ antibodies and non-antibody
  TTR therapies. (4) **Natural antibody validation** — 3 ATTR-CM
  patients with spontaneous disease regression had natural anti-TTR
  antibodies; therapeutic Ab-A shares epitope overlap. (5)
  **Non-antibody-dominated target validation** — 4 approved non-
  antibody therapies validate the target; antibodies differentiate
  by clearing pre-existing deposits. (6) **PubMed search strategy**
  — review-focused queries miss key primary antibody papers; always
  add non-review queries ("anti-[target] monoclonal antibody",
  "[target] amyloid antibody clearance"). (TTR profile, ~49K chars,
  5 papers, 150 PMID citations, 21 authors,
  working-docs/hitlist-profiles/transthyretin.md.)

- **2026-08-16 — Anthrax PA key-paper-ingestion profile observations.**
  Twenty-seventh level-2 profile (approved tier, infectious disease /
  biodefense — inhalational anthrax). This is the **first infectious
  disease target profile** and the **first bacterial toxin target** —
  all prior profiles targeted human proteins (immunology, oncology,
  neuroscience, cardiovascular). 5 papers ingested, 3/5 PMC XML OA
  (Toxins, AAC, IDR — all MDPI-family or ASM OA journals), 2/5
  abstract-only (Annual Reviews, Springer book chapter — both
  paywalled, jina retrieved abstract + nav only). ~27K chars, ~35
  PMID citations. See `references/anthrax-pa-profile-observations.md`
  for full observations. Key new patterns:

  (1) **Bacterial toxin target — the gene/UniProt fields need
  adaptation.** The template says "Gene symbol: HGNC symbol" and
  "UniProt ID: primary UniProt accession" — both assume a human
  target. For bacterial toxin targets, the gene is a bacterial gene
  (pagA for B. anthracis PA) and the UniProt ID is for the bacterial
  protein (P13423), not a human protein. In field 1, note the organism
  explicitly and flag that this is NOT a human gene. The "cell types
  expressing" field in field 2 also inverts: the bacterium produces
  the target, not the host — instead, describe which host cells the
  toxin targets (via receptors CMG2, TEM8).

  (2) **FDA Animal Rule — the only approved-antibody tier with zero
  human efficacy data.** Both approved antibodies (raxibacumab 2012,
  obiltoxaximab 2016) were approved under the FDA Animal Rule (21
  CFR 601.90) because human efficacy trials are unethical/infeasible
  (anthrax is rare, lethal, primarily a bioterrorism scenario).
  Efficacy is extrapolated from two animal species (rabbits +
  cynomolgus macaques). This creates a unique evidence profile: field
  3 (disease evidence) cites "clinical success (via Animal Rule — no
  human efficacy trials)" rather than "clinical success" alone. Field
  6 (failure/success modes) must note that individual animal
  experiments were often not statistically significant — only the
  meta-analysis (23 experiments, combined RR 0.64) showed consistent
  benefit. No post-marketing human efficacy data exists and is
  unlikely ever to be collected.

  (3) **Government procurement market, not commercial pharma.** The
  market for anthrax anti-toxin antibodies is defined by US
  Strategic National Stockpile contracts under Project BioShield, not
  by patient demand. Field 10 (competitive landscape) should describe
  this as a government biodefense procurement market — Emergent
  BioSolutions effectively holds a monopoly on all three approved
  agents. Market size is set by government contracts, not by
  epidemiology. This shapes the competitive landscape fundamentally:
  pipeline depth is driven by stockpile redundancy requirements (two
  suppliers), not by commercial competition.

  (4) **Affinity-efficacy correlation across two approved antibodies
  targeting the same domain.** Both approved mAbs bind PA domain 4
  (the receptor-binding domain) but at different affinities:
  obiltoxaximab KD = 0.33 nM vs raxibacumab KD = 2.78 nM
  (approximately one log difference). In rabbit studies,
  obiltoxaximab showed higher survival (92.9%, 61.5%) vs raxibacumab
  (44.4%, 45.8%). While not a head-to-head comparison, this is the
  strongest published evidence that higher affinity correlates with
  better in vivo efficacy for anti-toxin antibodies targeting the
  same epitope/domain. For field 5 (epitope landscape) and field 6
  (success factors), KD comparison across approved antibodies is a
  high-value data point when available.

  (5) **Disease severity at treatment time is the primary efficacy
  determinant — even complete neutralization cannot save advanced
  disease.** Obiltoxaximab rapidly neutralized serum PA to below the
  limit of quantification in ALL animals (survivors and
  nonsurvivors), yet animals with advanced disease (bacteremia
  >10^5 CFU/ml) still died. This is a critical failure mode: the
  antibody achieves its pharmacologic effect (PA neutralization)
  but irreversible toxin-mediated organ damage has already occurred.
  For field 6, this is the headline failure mode — "late treatment /
  advanced disease" — and for field 11 (differentiation), it
  motivates bispecific (anti-PA + anti-LF) or combination approaches
  that might address pre-formed toxin damage.

  (6) **PubMed search strategy for infectious disease / biodefense
  targets.** Review-focused queries ("anthrax protective antigen AND
  (raxibacumab OR obiltoxaximab) AND review[pt]") returned 9 results;
  broader queries ("anthrax toxin AND antibody AND review[pt]")
  returned 47. The highest-value papers were identified through
  supplementary non-review queries ("raxibacumab AND (anthrax OR
  inhalational) AND (efficacy OR animal OR prophylaxis)" — 32
  results) that surfaced the pivotal primary efficacy paper
  (Yamamoto 2016, PMID 27431222) which was NOT tagged as a review.
  Always add non-review queries for biodefense/infectious disease
  targets — the pivotal animal efficacy studies are primary research
  papers, not reviews.

  (Anthrax PA profile, ~27K chars, 5 papers, 24 authors, 5 unique
  PMIDs cited, working-docs/hitlist-profiles/anthrax-pa.md.)

- **2026-08-16 — SLeX/CA19-9 profile: first carbohydrate antigen target
  — template field adaptations for non-protein targets.** The SLeX/CA19-9
  profile is the first target where the epitope is a carbohydrate
  (sialyl-Lewis X / sialyl-Lewis A tetrasaccharide), not a protein. This
  required systematic adaptation of multiple field-1 fields that assume
  a protein target. Key patterns:

  (1) **Carbohydrate antigen — gene/UniProt/MW/oligomerization fields
  are all "Not applicable."** The template says "Gene symbol: HGNC
  symbol" and "UniProt ID: primary UniProt accession" — both assume a
  protein target. For a carbohydrate epitope, there IS no gene or
  UniProt entry. Instead, field 1 should list the biosynthetic enzymes
  (FUT3, FUT7, ST3GAL3/4, B3GALT5 for sLeX/sLeA synthesis) as the
  "gene" context, note "Not applicable — carbohydrate epitope" for
  gene symbol and UniProt ID, and describe the carbohydrate structure
  (tetrasaccharide sequence) in the molecular weight field. The
  oligomerization field is also N/A — the epitope is displayed on
  diverse carrier glycoproteins (MUC1, MUC16) and glycolipids, not as
  a single oligomeric protein. This extends the bacterial toxin
  adaptation pattern (anthrax PA) to a new class: non-protein targets
  where the "target" is a post-translational modification, not a gene
  product.

  (2) **Epitope landscape (field 5) inverts for carbohydrate targets.**
  For protein targets, epitopes are linear or conformational protein
  surfaces mapped by crystallography/binning. For carbohydrate
  epitopes, the "epitope" IS the carbohydrate structure itself
  (sLeX = Neu5Acα2→3Galβ1→4(Fucα1→3)GlcNAc). Standard PDB
  antibody-protein crystallography does not apply — no PDB structures
  of anti-CA19-9 antibody-carbohydrate complexes were found.
  "Neutralizing" for a carbohydrate tumor antigen means blocking
  selectin-mediated adhesion (the biological function), but the
  antibodies in development (TE-1132, MVT-1075) are NOT neutralizing —
  they function as targeting moieties for radiotherapy delivery, not
  as selectin blockers. This distinction must be stated explicitly in
  field 5.

  (3) **Circulating antigen sink is a unique failure mode for shed
  carbohydrate antigens.** Unlike protein targets, CA19-9 is shed into
  blood circulation and acts as an antigen sink — systemically
  administered antibody is trapped by circulating CA19-9 before
  reaching the tumor. This requires pre-dosing with unlabeled antibody
  to bind circulating antigen first. This is a field-6 failure mode
  specific to shed carbohydrate antigens and should be flagged when the
  target is a serum biomarker (CA19-9, CEA, CA-125, etc.).

  (4) **3-paper profiles are viable for preclinical targets.** The
  task specified 3 papers (vs the usual 5). This is sufficient when the
  target is preclinical with limited literature and the 3 papers cover
  distinct aspects: mechanism (Kannagi 2004, sLeX/sLeA biosynthesis),
  therapeutic application (Chen 2023, TE-1132 ARC), and diagnostic
  application (McElroy 2008, surgical navigation). The 33% full-text
  retrieval rate (1/3) is lower than the 5-paper average (~60-80%) but
  was adequate for a preclinical target where the abstract + one full
  text paper provided enough mechanistic detail.

  (SLeX/CA19-9 profile, ~20K chars, 3 papers ingested (1/3 PMC XML OA,
  2/3 abstract-only), 3 unique PMIDs cited,
  working-docs/hitlist-profiles/slex-ca19-9.md.)

- **2026-08-16 — Von Willebrand Factor (vWF) key-paper-ingestion profile
  observations.** Twenty-eighth level-2 profile (approved tier,
  cardiovascular/metabolic — hemostasis/TTP). vWF is the **first
  nanobody therapeutic target profile** (caplacizumab/Cablivi is a
  bivalent VHH, ~15 kDa, not a conventional IgG) and the **first
  secreted soluble protein target** (all prior targets were
  cell-surface/membrane-bound). 5 papers ingested (1/5 PMC XML OA, 2/5
  Wayback NEJM, 2/5 abstract-only — Blood/ASH and JAMA both confirmed
  publisher blocks). 60% full-text retrieval. ~26K chars, 36 authors, 5
  unique PMIDs. See `references/von-willebrand-factor-profile-observations.md`
  for full observations. Key new patterns:

  (1) **Nanobody format creates a format-efficacy-safety trilemma.**
  The small size (~1/10 IgG) gives rapid tissue penetration and fast
  onset (field 6 advantage), but the short half-life requires daily SC
  dosing (convenience disadvantage). Critically, the short half-life IS
  a safety feature — rapid reversibility by withholding the drug (vWF
  function recovers within hours) is a nanobody-specific safety
  advantage over longer-acting IgG. A longer-acting format (PEGylated
  VHH, Fc-fused VHH, conventional IgG) would reduce dosing frequency
  but sacrifice this reversibility safety advantage. For field 4,
  describe VHH architecture explicitly; for field 8, note rapid
  reversibility as a designed safety mechanism.

  (2) **Secreted soluble target eliminates membrane-accessibility
  concerns.** For field 1, "Localization: secreted (circulating plasma
  protein)" — fully accessible to antibodies in circulation. Fields 5
  and 9 can note "Not applicable" for membrane-proximal regions. PK/PD
  for soluble targets: antibody distribution volume and target plasma
  concentration matter more than receptor occupancy on cells. This is
  the first profile where this consideration applies.

  (3) **Downstream-blockade strategy — block the consequence, not the
  cause.** Caplacizumab blocks vWF–platelet GPIb (downstream
  aggregation) but NOT the upstream ADAMTS13 deficiency (autoimmune
  cause). Relapse on discontinuation with persistent ADAMTS13 <10% is a
  mechanism-based failure (TITAN: 8 relapses, 7 with ADAMTS13 <10%).
  HERCULES mitigated this by extending treatment until ADAMTS13 recovery
  (biomarker-guided duration). Generalizable pattern for field 6: for
  downstream-blockade antibodies, treatment duration must be guided by
  the upstream cause's resolution biomarker, not the downstream effect's
  resolution. Always ask: does the antibody address the cause or the
  consequence? If the consequence, what biomarker signals the cause has
  resolved?

  (4) **On-target bleeding as mechanism-intrinsic therapeutic ceiling.**
  Bleeding (54–65% vs. 38–48% placebo) is not a side effect — it IS
  the mechanism of vWF blockade. No format or epitope change can
  eliminate it. The therapeutic index is acceptable in TTP
  (life-threatening, >90% mortality untreated) but would be narrow for
  chronic indications (stroke prevention). For field 8, note this is a
  therapeutic ceiling for the target class, not an antibody-specific
  issue.

  (vWF profile, ~26K chars, 5 papers, 36 authors, 5 unique PMIDs cited,
  working-docs/hitlist-profiles/von-willebrand-factor.md.)

- **2026-08-16 — Growth Hormone Receptor (GHR) key-paper-ingestion profile
  observations.** Thirty-third level-2 profile (approved tier,
  cardiovascular/metabolic — endocrine/acromegaly). GHR is the **first
  target where the approved biologic is a PEGylated protein antagonist,
  not a conventional antibody** (pegvisomant/Somavert = modified GH with
  G120R substitution, PEGylated for half-life) and the **first class I
  cytokine receptor target profiled**. 5 papers ingested, 1/5 PMC XML OA
  (Front Endocrinol — Dehkhoda 2018, 59K chars full text), 4/5
  abstract-only (Endocr Rev, Elsevier GH&IGF Res ×2, Nat Rev Dis Primers
  — all subscription, jina/Wayback blocked). 20% full-text retrieval.
  ~40K chars, 5 unique PMIDs, 16 authors. See
  `references/growth-hormone-receptor-profile-observations.md` for full
  observations. Key new patterns:

  (1) **Non-antibody biologic as the approved drug — PEGylated protein
  antagonist.** Pegvisomant is NOT an antibody, Fc-fusion, or nanobody —
  it is a recombinant GH molecule with G120R that blocks receptor
  dimerization, PEGylated for half-life. Field 4 must describe the format
  accurately ("PEGylated recombinant protein antagonist") rather than
  forcing it into antibody categories. The key success factor is
  structure-based design (crystal structure of GH-GHR complex → two-site
  binding → G120R site 2 mutant). This pattern generalizes to targets
  where the approved biologic is a modified ligand (etanercept = TNFR-Fc
  fusion, anakinra = IL-1 receptor antagonist) — the antibody space is
  completely open. For field 11, a conventional antibody is the primary
  differentiation opportunity.

  (2) **Preformed dimer + conformational activation = agonist risk for
  antibody approaches.** GHR exists as a preformed homodimer; activation
  requires a transmembrane crossover conformational change, not de novo
  dimerization. Bivalent antibodies risk cross-linking and activating the
  receptor (agonist activity). Early studies confirmed: bivalent mAbs to
  GHR ECD activated a GHR/G-CSFR hybrid, but only 1/8 showed weak agonism
  on full-length GHR — suggesting correct conformational change (not
  just cross-linking) is required. An anti-GHR antibody must block the
  conformational change, be screened as an antagonist, and consider
  monovalent formats. This generalizes to all preformed-dimer class I
  cytokine receptors (PRLR, EPOR, TPOR).

  (3) **GHR-deficient individuals show no cancer deaths — LOF genetic
  validation for an indication beyond the approved one.** Laron syndrome
  patients (GHR-deficient) have no cancer deaths — strong genetic
  evidence that GHR signaling promotes cancer. An SNP (P495T) impairing
  SOCS2-mediated GHR degradation extends signaling and correlates with
  lung cancer risk. For field 3, this provides human genetics validation
  for cancer (an unexplored indication), distinct from the approved
  indication (acromegaly). Always check whether LOF individuals show
  altered disease incidence for indications beyond the approved one.

  (4) **Jina false positive — 131K chars of references, not article body.**
  Nature Reviews Dis Primers jina retrieval returned 131K chars that
  appeared to be the reference list only (177 references, no body text).
  This is a new jina failure mode: large character count that initially
  appears to be full text but is actually just the references section.
  Always verify jina output by checking for article body markers
  (abstract text, section headers, discussion) before classifying as
  "publisher-jina" full text.

  (5) **PubMed search for non-antibody targets — "antagonist" not
  "antibody" as the search term.** `GHR AND antibody AND acromegaly AND
  review` returned only 1 result. `growth hormone receptor antagonist
  AND acromegaly` returned 15. For targets where the approved biologic
  is not a conventional antibody, include "antagonist," "PEGylated," and
  "receptor blocker" alongside "antibody" in search queries.

  (GHR profile, ~40K chars, 5 papers, 16 authors, 5 unique PMIDs cited,
  working-docs/hitlist-profiles/growth-hormone-receptor.md.)

- **2026-08-16 — Factor D (CFD/adipsin) key-paper-ingestion profile
  observations.** Thirty-fourth level-2 profile (clinical-trial tier,
  immunology — complement alternative pathway; also ophthalmology/GA).
  Factor D is the **rate-limiting serine protease of the alternative
  complement pathway** — a 24 kDa non-glycosylated soluble plasma protein
  produced primarily by adipocytes (hence "adipsin"). 5 papers ingested,
  2/5 PMC XML OA (Front Immunol ×2), 1/5 EPMC PDF (IOVS — inPMC:Y, OA:N),
  2/5 abstract-only (Bentham Curr Med Chem, Elsevier Lancet Haematol). 60%
  full-text retrieval. ~36K chars, 5 unique PMIDs, 42 authors. See
  `references/factor-d-profile-observations.md` for full observations.
  Key new patterns:

  (1) **Small-molecule-approved, antibody-failed — the open-antibody-space
  pattern with a known failure mode.** Danicopan (oral small molecule)
  approved FDA January 2025 for PNH (ALPHA Phase 3: +2.44 g/dL Hb,
  p<0.0001). Lampalizumab (anti-factor D Fab antibody) FAILED Phase III
  for GA after promising Phase II. This is distinct from C5aR1/GHR (small
  molecule approved, no antibody tried — open space, no precedent): Factor
  D has an antibody failure that must be analyzed and differentiated
  against. For field 4, document that the antibody failure is a specific
  failure mode, not target invalidation. For field 6, analyze WHY the
  antibody failed vs why the small molecule succeeded. For field 11,
  differentiation must be explicit (different epitope, format, route,
  indication, or biomarker-selected population).

  (2) **Self-inhibitory loop as conformational targeting challenge.**
  Factor D's self-inhibitory loop locks the catalytic triad inactive;
  activation requires a conformational change upon C3bB binding. Antibodies
  targeting the catalytic site face access limitations (sequestered in
  resting state). Locking factor D in the self-inhibited conformation or
  blocking the C3bB interface are unexplored antibody approaches. For
  fields 5 and 9, conformational states directly determine which epitopes
  are functionally relevant — a target with a conformational switch
  requires epitope mapping in both states. Generalizes to any serine
  protease with zymogen-to-active transitions.

  (3) **EPMC PDF as reliable fallback for inPMC:Y, OA:N papers.** PMID
  22003108 (IOVS) had inPMC:Y, OA:N, and PMC XML with no `<body>` element
  (metadata-only record). The EPMC PDF endpoint returned a full 342K PDF
  → 40K chars via pymupdf. This extends EPMC PDF success cases to non-OA
  papers with PMC metadata records but no XML body — higher yield than
  jina or Wayback for this paper state.

  (4) **Phase II success → Phase III failure (lampalizumab) — a distinct
  antibody failure trajectory.** First profile with this trajectory.
  Prior failed-antibody profiles failed earlier (Phase II or preclinical).
  The Phase II success proves target engagement; Phase III failure points
  to remediable factors (incomplete AP blockade, intravitreal-only route,
  AP bypass via kallikrein, Fab half-life). For field 6, richer than
  "didn't work" — Phase II success + Phase III failure = specific
  remediable failure analysis. For field 11, each failure reason suggests
  a differentiation strategy.

  (5) **Delegation with search instructions — complement target
  validation.** Subagent received search query templates + topic
  coverage requirements (not pre-identified PMIDs). Ran 4 esearch queries,
  screened 65 unique PMIDs via esummary, selected 5 covering all topics.
  Autonomously implemented the full paper-ingest pipeline (PubMed XML,
  Europe PMC, full-text ladder, paper page writing) using urllib.request
  directly. Validates the IL-17A delegation pattern for complement targets.

  (6) **Bentham Science (Curr Med Chem) publisher block confirmed.**
  Cloudflare-protected, jina returned CAPTCHA (496 chars), no Wayback
  snapshot. Add Bentham Science to known-blocks alongside ASH/Blood,
  ScienceDirect, Wiley, Karger. Abstract (1,432 chars) sufficient for
  context.

  (Factor D profile, ~36K chars, 5 papers, 42 authors, 5 unique PMIDs
  cited, working-docs/hitlist-profiles/factor-d.md.)

- **2026-08-16 — IL-15 key-paper-ingestion profile observations.**
  Thirty-fifth level-2 profile (clinical-trial tier, immunology/oncology).
  IL-15 is the **first dual-directional cytokine target profile** — the
  same cytokine is blocked with antibodies for autoimmune disease (RA,
  IBD, celiac, T1D) AND enhanced with superagonists for cancer (N-803/
  ALT-803, NKTR-255, hetIL-15). 5 papers ingested (4/5 full text: 3 PMC
  XML OA, 1 publisher-jina; 1/5 abstract-only — Annual Reviews). 80%
  retrieval rate. ~37K chars, 39 unique author slugs. See
  `references/il-15-profile-observations.md` for full observations. Key
  new patterns:

  (1) **Dual-directional cytokine targeting — first profile with both
  antagonist and agonist drugs.** All prior cytokine profiles had
  antibodies in a single direction (block OR agonize). IL-15 requires
  field 4 covering antagonists (anti-IL-15), agonists (IL-15
  superagonists), AND indirect blockers (JAK inhibitors). Fields 2, 6,
  8 must cover both directions with distinct mechanisms, failure modes,
  and safety profiles. For orchestrators: when delegating a cytokine
  target, check if both antagonist and agonist therapeutics exist — if
  so, instruct the subagent to cover both directions.

  (2) **Cell Press/Immunity PII URL pitfall.** PMID 30995502 (Leonard
  2019, Immunity) had PII `S1074-7613(19)30145-1` in PubMed XML. A
  guessed PII returned 404 (24K chars of nav chrome). Extracting the
  correct PII from `<ELocationID EIdType="pii">` and constructing the
  URL as `cell.com/<journal>/fulltext/<PII>` yielded 128K chars via
  jina. The DOI URL also returned 404 via jina — always use the
  publisher article URL with the correct PII, not the DOI URL.

  (3) **N-803/ALT-803 Fc-fusion cytokine — first non-antibody biologic
  in field 4.** N-803 is an IL-15 mutein + IL-15Rα sushi domain + IgG1
  Fc (an agonist Fc-fusion cytokine, not a conventional antibody). Field
  4's "format" and "epitope info" must be adapted: N-803's "epitope" is
  the IL-2Rβ/γc receptor complex (binds the receptor, not the
  cytokine). Generalizes to any Fc-fusion cytokine or PEGylated cytokine
  in the antibody landscape.

  (4) **Phase I clinical trial data for IL-15 superagonist.** PMID
  39948608 (Shapiro 2025, NCT04290546) is the first IL-15 superagonist
  Phase I trial in the profile corpus: CIML NK cells + N-803 ±
  ipilimumab in head/neck cancer. 100% Grade 3-5 AEs, 1 TRAE death,
  60% SD + 10% PR (transient). NK persistence was the limiting factor.
  Ipilimumab increased NK proliferation but reduced HLA-mismatched NK
  persistence. IL-15 does NOT expand Tregs (key IL-2 differentiator).

  (5) **Annual Reviews jina false positive — large output, abstract
  only.** PMID 10358752 (Waldmann 1999, Annu Rev Immunol): jina
  returned 58K chars but this was nav chrome + abstract (1,408 chars) +
  "Most Read"/"Most Cited" lists — not article body. Always verify jina
  output by checking for body text markers beyond the abstract. For
  Annual Reviews, abstract-only is expected; the structured abstract
  (1,000-1,500 chars) is typically sufficient for profile grounding.

  (IL-15 profile, ~37K chars, 5 papers, 39 unique author slugs, 5 unique
  PMIDs cited, working-docs/hitlist-profiles/il-15.md.)

- **2026-08-16 — Small-peptide-ligand target with small-molecule-only
  clinical history (Urotensin II profile).** U-II is the first target
  profiled where ALL clinical development was small-molecule receptor
  antagonists (palosuran/ACT-058362) and NO antibody was ever developed.
  The antibody competitive landscape (field 4) is genuinely zero — not
  sparse or blue ocean but empty. For profiling this class: (1) field 4
  enumerates the small molecules (clearly marked as NOT antibodies); (2)
  field 6 failure analysis must be translated into antibody-relevant
  lessons (what would an antibody do differently? PK, species
  cross-reactivity, target engagement measurability, specificity); (3)
  field 11 differentiation is the most important field — the entire case
  is built from scratch. This pattern applies to any peptide-ligand or
  GPCR target where the clinical modality was small-molecule-only.
  See `references/urotensin-ii-profile-observations.md`.

- **2026-08-16 — "Functionally silent" receptor system as a target
  failure mode (Urotensin II profile).** The UT receptor system is
  quiescent in normal physiology (slow U-II dissociation, rapid receptor
  sequestration, UT knockout mice normal BP, variable/absent U-II
  infusion response in healthy humans). Blocking a quiescent system
  produces minimal effect — consistent with palosuran's excellent safety
  but lack of efficacy. For field 6, the profile must classify whether
  the target is: a pathogenic driver (blockade = therapeutic), a
  compensatory/protective response (blockade = harmful/neutral), or a
  disease marker only (blockade = no effect). For U-II, evidence for a
  protective role exists (higher U-II = better outcomes in ESRD and
  acute MI). This protective-upregulation pattern generalizes to
  vasoconstrictor targets — the body may upregulate vasoconstrictors to
  maintain perfusion in failing hearts. See
  `references/urotensin-ii-profile-observations.md`.

- **2026-08-16 — Species-dependent receptor pharmacology as a
  preclinical translation failure (Urotensin II profile).** Palosuran
  has >100-fold lower affinity for rat UT receptors vs. human UT
  receptors. All preclinical efficacy came from rat models at
  suprapharmacological doses — it was uncertain whether effects were
  UT receptor-mediated or off-target. This is a generalizable pitfall:
  when the preclinical species has dramatically different target
  pharmacology from humans, the preclinical efficacy data may not
  predict human efficacy. For antibody targets, the equivalent is
  non-cross-reactive antibodies in preclinical species. An anti-U-II
  antibody targeting the conserved CFWKYC hexapeptide would cross-react
  across species — a structural advantage over small molecules. See
  `references/urotensin-ii-profile-observations.md`.

- **2026-08-16 — Wrong-indication clinical trial as a development
  strategy failure (Urotensin II profile).** Palosuran was tested in
  diabetic nephropathy, not heart failure — despite the strongest
  rationale being in heart failure. After the nephropathy trial failed,
  the entire program was terminated; no heart failure trial was ever
  conducted. For field 6, distinguish: target failure (target invalid),
  drug failure (wrong molecule), indication failure (wrong disease),
  program failure (wrong strategy — terminated before testing the right
  indication). For U-II, the failure was drug + indication + program
  failure. The target remains unvalidated in heart failure because it
  was never tested there. See
  `references/urotensin-ii-profile-observations.md`.

- **2026-08-16 — Expanding beyond the initial 5 papers when all are
  paywalled (Urotensin II profile).** All 5 initially selected landmark
  papers were paywalled (Nature, J Pharmacol Exp Ther, Hypertension,
  Clin Pharmacol Ther, Peptides) — 0/5 had PMC access. To achieve
  adequate full-text grounding, the search expanded to OA review papers
  in PMC: 3 OA papers (Br J Pharmacol ×2, Cardiovasc Hematol Disord
  Drug Targets ×1) provided ~203K chars of full text covering the same
  biology. Strategy: when initial landmark papers are all paywalled,
  search for comprehensive OA reviews in PMC. Br J Pharmacol and similar
  pharmacology journals are frequently OA and provide synthesized
  coverage of the same literature. See
  `references/urotensin-ii-profile-observations.md`.

- **2026-08-16 — Unreliable biomarker as a clinical development
  barrier (Urotensin II profile).** U-II plasma concentrations vary
  1,000- to 10,000-fold between studies (different assays, antibodies,
  cross-reactivity with URP/precursors). Without reliable measurement,
  the palosuran trial could not stratify patients, demonstrate target
  engagement, or correlate U-II with response. Generalizable for
  peptide targets: if the target cannot be reliably measured,
  biomarker-guided trial design is impossible. An anti-U-II antibody
  would solve this — free vs. total U-II can be measured using the
  antibody as the assay reagent. See
  `references/urotensin-ii-profile-observations.md`.

- **2026-08-16 — B7-H3 (CD276) key-paper-ingestion profile
  observations.** Thirty-sixth level-2 profile (clinical-trial tier,
  oncology — SCLC + pan-tumor). B7-H3 is the **first dual-mechanism
  target profiled**: the same molecule serves as both a T cell
  checkpoint (blockade enhances anti-tumor immunity) AND a
  tumor-associated antigen for ADC delivery (overexpressed on tumor
  cells and tumor vasculature). 5 papers ingested (2/5 PMC XML OA —
  Cancer Cell, JCO; 3/5 abstract-only — Cell Research, Trends
  Pharmacol Sci, Lancet Oncol). ~40K chars, 16 unique PMIDs cited.
  See `references/b7-h3-profile-observations.md` for full
  observations. Key new patterns:

  (1) **Dual-mechanism target — immune checkpoint + ADC antigen.**
  B7-H3 functions as a T cell checkpoint (PMID 28685773) AND a
  tumor-associated antigen for ADC targeting (PMID 28399408). These
  mechanisms require different antibody properties: checkpoint
  blockade needs surface-retaining signaling-disrupting antibodies;
  ADC targeting needs rapidly internalizing antibodies. Clinical
  development has overwhelmingly favored ADCs (ifinatamab deruxtecan,
  vobramitamab duocarmazine) over checkpoint blockade
  (enoblituzumab). The naked antibody showed only modest tumor
  growth delays — B7-H3's checkpoint function is "largely
  redundant for tumor growth" (PMID 28399408). For field 2 and 6,
  explicitly state which mechanism is clinically tractable.
  Generalizable: when a target has both checkpoint and
  antigen-delivery functions, profile both but flag which is
  clinically validated.

  (2) **Dual-compartment targeting — tumor cells + tumor
  vasculature.** B7-H3 is the **first target profiled with
  expression on both tumor cells AND tumor vasculature** (51% of
  tumors strongly positive on endothelial cells). The warhead
  determines whether vasculature targeting works: MMAE (tubulin
  inhibitor) is completely ineffective against CD276+ tumor
  endothelial cells because they express P-glycoprotein (P-gp/
  ABCB1/MDR1), which effluxes MMAE. PBD dimers and DXd (DNA-damaging
  payloads) are not P-gp substrates and effectively target both
  compartments — 60% cure rate in dual-compartment models (PMID
  28399408). The clinical success of ifinatamab deruxtecan (DXd)
  validates this. Generalizable: for any target expressed on tumor
  vasculature, the warhead must be non-P-gp-substratable. Include
  P-gp efflux status in field 6 for any ADC target with vascular
  expression.

  (3) **Warhead class effect (ILD) vs. target-specific safety.**
  ILD (12.4% rate, 1.5% grade 5) is a DXd ADC class effect shared
  with T-DXd and Dato-DXd — NOT B7-H3-specific. The profile must
  separate class-from-target toxicity in field 8. B7-H3 itself has
  low normal tissue expression and a >20,000 antibody binding
  sites/cell threshold that protects normal cells. No
  target-specific toxicity has emerged clinically. This
  distinction matters for differentiation: non-DXd payloads may have
  different ILD risk.

  (4) **Broad expression eliminates biomarker barrier.** B7-H3 is
  overexpressed in ≥50% of every solid tumor type (1,342 samples).
  In SCLC, 95% of cells are positive with no expression-response
  association (PMID 41086386). This eliminates the companion
  diagnostic barrier and enables pan-tumor enrollment (IDeate-
  PanTumor01: 34% ORR across 10 tumor types, PMID 41926962).
  Generalizable: for targets with near-universal expression,
  biomarker selection is unnecessary and pan-tumor enrollment is
  the strategic default.

  (5) **Receptor orphan status — checkpoint biology incompletely
  understood.** B7-H3's receptor remains unidentified (PMID
  40946079). Without knowing the receptor-binding interface,
  "neutralizing" vs "non-neutralizing" epitopes cannot be defined
  by receptor-competition. Epitope functionality is defined by
  internalization (for ADCs) or T cell functional assays (for
  checkpoint blockade). For orphan-receptor targets, note the
  status explicitly and adapt epitope/function definitions.

  (6) **Antibody binding site threshold as built-in safety
  mechanism.** >20,000 binding sites/cell needed for PBD-ADC
  cytotoxicity (PMID 28399408). This threshold protects normal
  cells with low B7-H3 expression. More potent payloads may lower
  the threshold and erode the safety margin. Document as a
  design constraint in field 8 and 11.

  (7) **JCO is a reliable PMC OA source for oncology clinical
  trials.** 2/5 papers had PMC XML OA: Cancer Cell (Seaman 2017)
  and JCO (Rudin 2026). JCO provides PMC OA for recent oncology
  trials — one of the most reliable full-text sources for clinical
  trial data. Lancet Oncology and Cell Research abstracts were
  self-sufficient for profile grounding.

  (B7-H3 profile, ~40K chars, 5 papers, 16 unique PMIDs cited,
  working-docs/hitlist-profiles/b7-h3.md.)

- **2026-08-16 — PSMA/FOLH1 key-paper-ingestion profile observations.**
  See `references/psma-profile-observations.md` for full detail. Clinical-
  trial tier, oncology (prostate cancer). 5 key papers ingested (4/5 PMC
  OA: NEJM, Clin Cancer Res ×2, Mol Pharm; 1/5 abstract-only: Eur Urol
  Focus — Elsevier). ~41K chars, 371 lines, 6 unique PMIDs cited. New
  observations:

  (1) **Non-antibody approved modality: small-molecule radioligand.** PSMA
  is the first target profiled where the approved drug (177Lu-PSMA-617/
  Pluvicto) is a small-molecule radioligand, not an antibody. It binds the
  enzymatic active site (binuclear zinc center), not a surface epitope. The
  profile handled this in field 4 by listing the radioligand with "Format:
  Radioligand — not an antibody" and "Isotype: N/A," then listing antibody
  approaches separately. Field 5 must distinguish small-molecule binding
  sites (active site) from antibody surface epitopes — they are different
  "bins" that do not compete. Generalizable: when the approved drug is a
  non-antibody modality, include it in field 4 with explicit annotations
  and compare modality formats head-to-head in field 6 (the small-molecule
  radioligand succeeded where antibody radioimmunotherapy had limited
  success — rapid clearance, no immunogenicity, simpler manufacturing).

  (2) **Task-context antibody identity errors: verify before trusting.**
  The delegation context stated "xaluritamig/AMG 160" as the PSMA
  bispecific. PubMed verification revealed xaluritamig is AMG 509 (STEAP1×
  CD3), NOT PSMA. AMG 160 (acapatamab) is the correct PSMA×CD3 bispecific.
  The names were conflated — both are Amgen bispecific T-cell engagers in
  prostate cancer. Generalizable: delegation contexts can contain wrong
  antibody-target associations, especially for molecules from the same
  company in the same indication. Verify every antibody identity claim
  (INN → target → company) via PubMed before incorporating it into field 4.
  A 30-second PubMed search confirms or corrects the association.

  (3) **Theranostic companion diagnostic co-approval.** PSMA is the first
  target profiled with a theranostic companion diagnostic co-approval.
  68Ga-PSMA-11 (Locametz) was approved simultaneously with Pluvicto; PSMA-
  positive status by PET was a VISION trial enrollment criterion. The
  companion diagnostic IS the biomarker assay (field 7) and the patient
  selection mechanism (field 6 success factor). Generalizable: when a
  target has an approved companion diagnostic, the diagnostic-therapy pair
  is a single theranostic system — profile both and note the regulatory
  linkage. For field 11, the theranostic pair creates a barrier to entry
  for new antibodies.

  (4) **Crossfire effect as heterogeneity mitigation.** 177Lu beta
  radiation has a path length of ~0.5-2 mm, enabling bystander killing of
  PSMA-negative cells adjacent to PSMA-positive cells. This partially
  addresses PSMA expression heterogeneity. ADCs and bispecifics lack this
  advantage. Generalizable: when profiling a target with expression
  heterogeneity, analyze whether any modality has a bystander mechanism.
  If yes, this is a field 6 success factor and field 11 differentiation
  dimension — modalities with bystander killing have an inherent advantage
  in heterogeneous-expression targets.

  (5) **On-target off-tumor toxicity from normal tissue expression.**
  PSMA is expressed on salivary glands, kidney proximal tubules, lacrimal
  glands, and small bowel — the radioligand's on-target radiation to these
  tissues causes dry mouth (38.8%) and renal toxicity (dose-limiting with
  impaired clearance). This is target-inherent, not format-limited.
  Generalizable: for targets with normal tissue expression, field 8 must
  enumerate the specific normal tissues and their physiological functions.
  The toxicity is on-target (the target is real on those tissues), not
  off-target. The therapeutic index is bounded by the tumor-to-normal
  expression ratio, not by antibody selectivity.

  (6) **High PMC OA rate for oncology clinical-trial papers.** 4/5
  papers (80%) had PMC OA full text — the highest rate for a clinical-
  trial tier profile. NEJM, Clin Cancer Res, and ACS journals (Mol Pharm)
  all provided PMC OA. Only Eur Urol Focus (Elsevier) was abstract-only.
  When pre-identifying landmark papers for oncology target profiling,
  prefer NEJM, Clin Cancer Res, and ACS journals over Elsevier/Wiley.

  (PSMA profile, ~41K chars, 5 papers, 6 unique PMIDs cited,
  working-docs/hitlist-profiles/psma.md.)

- **2026-08-16 — PVRIG key-paper-ingestion profile observations.**
  Thirty-seventh level-2 profile (clinical-trial tier, oncology — immune
  checkpoint). PVRIG (CD112R) is a nectin-family inhibitory checkpoint
  receptor on T cells and NK cells that binds CD112 (PVRL2/nectin-2). 6
  key papers ingested (4/6 PMC XML OA: J Exp Med, Cancer Immunol Res,
  J Hematol Oncol, Cancer Immunol Immunother; 1/6 jina reader on Cell
  Press/Structure journal — 94K chars; 1/6 abstract-only: Cancer Discovery
  news note, no PMCID). ~38K chars, 10 unique PMIDs cited. See
  `references/pvrig-profile-observations.md` for full detail. Key new
  patterns:

  (1) **Nectin-family checkpoint profiling: nonredundancy is the key
  differentiator from TIGIT.** PVRIG and TIGIT are in the same
  nectin/nectin-like receptor family but bind different ligands: PVRIG
  binds CD112 (PVRL2/nectin-2, Kd ~88 nM), TIGIT binds CD155 (PVR). They
  are **nonoverlapping, nonredundant inhibitory pathways** — dual blockade
  is additive/synergistic (PMID 30659054). For field 2 (biological
  mechanism) and field 11 (differentiation), explicitly state the
  nonredundancy: PVRIG is NOT "another TIGIT" — it governs a distinct
  ligand axis. The PVR:PVRL2 expression ratio varies by cancer type
  (breast/ovarian/prostate/endometrial enriched in PVRL2; melanoma/
  esophageal/colorectal enriched in PVR), providing a biomarker
  framework for patient selection (PMID 30659054). Generalizable to any
  multi-receptor checkpoint family where receptors share a costimulatory
  partner (CD226/DNAM-1) but bind different ligands.

  (2) **NK cell as primary effector — distinct from T cell-focused
  checkpoints.** Unlike PD-1 and TIGIT (primarily T cell checkpoints),
  PVRIG has a dominant NK cell effector mechanism. PVRIG+ tumor-
  infiltrating NK cells are exhausted (high CD96, TIGIT, Tim-3, PD-1,
  NKG2A); PVRIG blockade restores cytotoxicity and IFNγ production
  (PMID 34174928). NK cells are activated first (after 1st dose), with
  T cell activation following (after 2nd dose) via NK cell-derived
  cytokines (PMID 38554184). For field 2 (cell types expressing) and
  field 6 (success factors), identify the primary effector cell — NK vs
  T cell dominance has implications for Fc format selection, in vivo
  model choice, and biomarker strategy. Generalizable: for checkpoint
  receptors expressed on both T and NK cells, determine which effector
  dominates in vivo, not just which expresses the target.

  (3) **Fc format debate (IgG4 vs IgG1) — same question as TIGIT, NK
  cell biology provides the answer.** COM701 (Compugen, IgG4, weak Fc)
  is the most advanced clinical anti-PVRIG; IBI352g4a (Innovent, IgG1,
  full Fc) and SRF813 (Surface Oncology, IgG1) are alternatives.
  Preclinical data shows Fc-competent IgG1 is superior because it
  engages Fcγ receptors on myeloid cells, providing additional immune
  stimulation beyond ligand blockade — and NK cells (the primary
  effector) benefit from Fc-mediated myeloid activation (PMID
  38554184). For field 4 (antibody landscape), always note the isotype
  AND the Fc format rationale. For field 6 (failure modes), the Fc
  format is unresolved — if COM701 (IgG4) fails, it may be format, not
  target. Generalizable: for NK cell-dominant checkpoint targets, the
  Fc-competent IgG1 format may be superior because NK cell activation
  benefits from myeloid FcγR engagement, unlike T cell-dominant
  checkpoints where Fc-active antibodies risk depleting exhausted T
  cells.

  (4) **Structural uniqueness of the CC' loop as epitope differentiation
  target.** The PVRIG/Nectin-2 crystal structure (PMID 38626767)
  revealed a unique CC' loop (residues N81, G82, A83) that adopts an
  upward conformation absent in TIGIT, CD96, and DNAM-1. This CC' loop
  provides high-affinity binding via a "double-lock-and-key" mode and
  determines ligand selectivity (Nectin-2 vs Necl-5/CD155). For field 5
  (epitope landscape) and field 11 (differentiation), a target-specific
  structural feature like the CC' loop is a potential epitope
  differentiation target — an antibody specifically targeting the CC'
  loop could have a distinct mechanism. Generalizable: when a crystal
  structure reveals a target-specific structural feature absent in
  related family members, flag it as a potential epitope
  differentiation opportunity in field 11.

  (5) **PVRIG low on Tregs — unlike TIGIT.** TIGIT is highly expressed
  on Tregs, enabling Treg depletion with Fc-active antibodies. PVRIG is
  expressed at low levels on Tregs (PMID 38554184). This means anti-PVRIG
  cannot deplete Tregs via Fc-mediated mechanisms — the therapeutic
  effect is purely checkpoint blockade, not Treg modulation. For field
  6 (failure modes) and field 11 (differentiation), note whether the
  target is expressed on Tregs and whether Treg depletion is a viable
  mechanism. This is a key difference between PVRIG and TIGIT that
  affects Fc format strategy.

  (6) **Rapid internalization as a target accessibility limitation.**
  PVRIG rapidly internalizes from the cell surface in the absence of TCR
  signaling (PMID 30659054) — a regulatory mechanism analogous to
  CTLA-4. For field 9 (structural information) and field 6 (failure
  modes), rapid internalization may limit antibody binding and efficacy
  in vivo, particularly for Fc-dependent mechanisms requiring sustained
  surface engagement. Generalizable: for checkpoint receptors with
  regulated surface expression (PVRIG, CTLA-4), note the internalization
  kinetics and consider whether an antibody that stabilizes surface
  expression would be differentiated.

  (7) **Cell Press/Structure journal is jina-recoverable.** The
  PVRIG/Nectin-2 crystal structure paper (PMID 38626767, Structure
  journal, Cell Press/Elsevier) was retrieved via jina reader proxy on
  the direct fulltext URL (`r.jina.ai/https://www.cell.com/structure/
  fulltext/<PII>`) — 94,284 chars of complete body text. The PII was
  obtained from PubMed `elink.fcgi?cmd=prlinks`. This contradicts the
  paper-ingest skill's previous "Cloudflare interstitial" entry for
  Cell Press — jina reader works on the direct fulltext URL. Updated
  the paper-ingest known-blocks table. For target profiling, this means
  Cell Press structural papers (Structure, Cell, Immunity, etc.) are
  retrievable via jina, making them high-value full-text sources for
  field 5 (epitope landscape) and field 9 (structural information).

  (PVRIG profile, ~38K chars, 6 papers, 10 unique PMIDs cited,
  working-docs/hitlist-profiles/pvrig.md.)

- **2026-08-16 — PRAME key-paper-ingestion profile observations.**
  Thirty-eighth level-2 profile (clinical-trial tier, oncology — melanoma).
  PRAME is the **first intracellular target profiled** in the entire profile
  corpus — a cancer-testis antigen (CTA) that cannot be targeted by
  conventional surface-binding antibodies. All therapeutic approaches use
  TCR/MHC-restricted recognition of PRAME-derived peptides presented on
  HLA class I. 5 papers ingested (4/5 Europe PMC OA XML, 1/5 Jina reader
  on JCI DOI). 100% retrieval rate. ~37K chars, 14 unique PMIDs cited. See
  `references/prame-profile-observations.md` for full observations. Key
  new patterns:

  (1) **Intracellular CTA targeting — first non-surface target class.**
  All prior profiles cover surface/soluble/membrane targets accessible to
  conventional antibodies. PRAME is intracellular (nucleus, cytoplasm,
  Golgi) and requires pMHC-targeted approaches: TCR mimic (TCRm) antibodies,
  TCR-engineered T cell therapy (TCR-T), TCR-CD3 bispecifics (ImmTAC), and
  protein vaccines. Fields 4, 5, and 9 must be reframed: field 4 becomes
  "therapeutic landscape" (not just antibodies); field 5 epitopes are
  pMHC complexes (peptide + HLA allele + copy number); field 9 covers
  pMHC-TCRm/TCR complex structures. Generalizable to any intracellular
  CTA (NY-ESO-1, MAGE-A family, WT1).

  (2) **Proteasome-dependent epitope generation.** The ALY peptide
  (PRAME 300–309) is generated by the immunoproteasome but destroyed by
  the constitutive proteasome (β5i subunit is the key catalytic subunit).
  PRAME+ melanoma cells do not present ALY under baseline conditions —
  Pr20 TCRm did not bind despite high PRAME expression. IFN-γ treatment
  upregulates immunoproteasome subunits and dramatically increases pMHC
  density, enabling TCRm binding and ADCC (PMID 28628042). For field 2,
  document proteasome dependency. For field 6, this is both a vulnerability
  (cold tumors) and a combination opportunity (IFN-γ–inducing agents).

  (3) **HLA restriction as patient eligibility gate.** All current PRAME
  therapies require HLA-A*02:01 (~45% of Caucasians). This is a germline
  genetic test, not a tumor biomarker — it cannot change with disease
  evolution. HLA LOH in tumors is an immune escape mechanism unique to
  HLA-restricted approaches. For field 4, note HLA restriction per therapy.
  For field 6, HLA LOH is a tumor escape mechanism. For field 10, HLA
  restriction limits market size but is also a barrier to entry.

  (4) **Protein vaccine CD8+ T cell failure — CTA-specific pattern.** The
  GSK PRAME vaccine induced humoral and CD4+ responses in all 66 patients
  but NO CD8+ cytotoxic T cell responses (PMID 27843625). This reflects
  extremely low circulating CD8+ precursor frequency for CTAs. For CTA
  targets, protein vaccines are unlikely to generate CD8+ responses —
  TCR-T, TCE/ImmTAC, or peptide/RNA vaccines are recommended.

  (5) **Low pMHC copy number sufficiency.** ImmTAC kills with as few as 10
  pMHC/cell; IMA203 threshold ~40–50 copies/cell; PRAME425 TCE shows
  ~10-fold potency difference between 100 and 20 copies/cell. These
  thresholds are dramatically lower than conventional antibody targets
  (>20,000 for B7-H3 ADC). Document minimum pMHC copy number for activity
  and compare across modalities.

  (6) **Jina reader works for JCI.** PMID 28628042 (J Clin Invest, OA:N,
  "Free access" status) fully retrieved via Jina reader on DOI URL —
  94,656 chars. Add JCI to paper-ingest known-retrievable table.

  (PRAME profile, ~37K chars, 5 papers, 14 unique PMIDs cited,
  working-docs/hitlist-profiles/prame-cd3.md.)

- **2026-08-16 — 5T4/TPBG key-paper-ingestion profile observations.**
  Thirty-ninth level-2 profile (clinical-trial tier, oncology — oncofetal
  antigen). 5T4 is an LRR transmembrane glycoprotein expressed in >90% of
  many carcinomas (CRC, RCC, ovarian, NSCLC) with limited normal tissue
  expression. 15 papers ingested (all abstract-level via PubMed esearch/
  esummary/efetch + Europe PMC fallback). 28 unique PMIDs cited across the
  profile. ~32K chars, 262 lines. See
  `references/5t4-tpbg-profile-observations.md` for full observations.
  Key new patterns:

  (1) **PubMed efetch XML truncation with HTML-markup abstracts.** PMID
  28522587 (Mol Cancer Ther) had an abstract with `<i>`, `<sup>` tags
  embedded in `<AbstractText>`. Python's ElementTree `.text` returned
  only the text before the first tag (~1100 chars), silently truncating
  the abstract. Europe PMC's REST API returned the full 2000+ char
  abstract with tags as raw strings. This is a general pitfall for any
  journal that uses rich formatting in abstracts. Added as a pitfall
  above.

  (2) **ClinicalTrials.gov API v2 is essential for clinical-trial-tier
  targets.** 20+ trials identified across 7+ companies/formats
  (TroVax/MVA-5T4 vaccine, naptumomab antibody-superantigen, A1mcMMAF/
  PF-06263507 ADC, MEDI0641 ADC, XB010 ADC, GEN1044 CD3×5T4 bispecific,
  ALG.APV-527, JK06 ADC, CBA-1535 tribody, CAR-NK, TCR-T). PubMed
  alone missed terminated/withdrawn trials and did not systematically
  provide NCT IDs. ClinicalTrials.gov filled field 4 (antibody
  landscape) and field 6 (failure modes) with structured trial data
  (phases, statuses, interventions). Added as a pitfall above.

  (3) **UniProt demerged entries — search by gene symbol.** Q13440
  (task-brief UniProt ID) was demerged/inactive; Q13641 is the current
  active entry. Found by searching UniProt REST API by gene symbol
  (TPBG) + organism 9606. Extends the existing "verify UniProt IDs"
  pitfall with the demerge-specific pattern.

  (4) **Oncofetal antigen targeting pattern — dual vaccine + ADC
  pipeline.** 5T4 has the broadest format diversity of any profiled
  target: vaccine (Phase III), antibody-superantigen (Phase II/III),
  3+ ADCs (preclinical/Phase I), bispecific (Phase I/II terminated),
  CAR-T (preclinical), CAR-NK (Phase 1), TCR-T (preclinical), mRNA
  vaccine (preclinical). Two Phase III/II failures (TroVax TRIST,
  naptumomab) both showed biomarker-defined subgroups with benefit —
  the lesson is patient selection, not target invalidity. For field 6,
  document which format failed vs which target failed. For field 11,
  the ADC-CSC-depletion niche remains clinically unvalidated despite
  strong preclinical data.

  (5) **Cancer stem cell / tumor-initiating cell targeting as a
  differentiation mechanism.** 5T4 is expressed on TICs/CSCs in NSCLC
  (PMID 21540235), HNSCC (PMID 27780858), and breast cancer. Anti-5T4
  ADCs (A1mcMMAF, MEDI0641) ablated CSCs and prevented recurrence in
  preclinical models — a mechanistically differentiated approach from
  conventional cytotoxic or checkpoint therapies. For field 11, the
  CSC-depletion mechanism is a unique value proposition that should be
  noted for any oncofetal target with TIC expression.

  (5T4/TPBG profile, ~32K chars, 15 papers ingested, 28 unique PMIDs
  cited, working-docs/hitlist-profiles/5t4-tpbg.md.)

### CD45 observations (radioimmunotherapy target + lightweight subagent retrieval)

CD45 (PTPRC) is a **pan-hematopoietic transmembrane phosphatase** — the
first radioimmunotherapy-target profile (all prior targets used naked
mAb, ADC, bispecific, or CAR-T). 5 key papers identified; 3/5 full text
retrieved via jina reader on PMC article URLs (PMIDs 39298738 JCO
SIERRA Phase III, 19786617 Blood Pagel Phase I, 31582553 Haematologica
90Y Phase I); 2/5 abstract-only (PMID 7849300 Blood 1995, PMID 39754536
Expert Rev Hematol 2025). ~40K chars profile, 5 PMIDs, 85+ PMID
citations. New observations:

- **Radioimmunotherapy targets have a distinct mechanism profile.** The
  antibody is a passive delivery vehicle for radionuclide, not a
  signaling blocker. Fields 2 and 5 change: the "effect of blockade" is
  radiation-induced cell death, not pathway inhibition; the "epitope
  landscape" focuses on pan-isoform binding and biodistribution
  properties, not functional neutralization. The bystander radiation
  effect (β-emitter path length of several mm) is a key field 6 success
  factor — it can kill antigen-negative leukemic stem cells, a unique
  advantage over other immunotherapy modalities. For field 8 (safety),
  the primary toxicity (myelosuppression) is the intended therapeutic
  effect, not an adverse event — the safety profile is defined by the
  dose-limiting organ (liver, MTD 24 Gy for ¹³¹I-BC8), not by on-target
  pharmacology. (PMID 7849300, 19786617, 39298738.)

- **Crossover-confounded OS is a radioimmunotherapy trial-design
  pitfall.** The SIERRA Phase III trial met its primary endpoint (dCR
  17.1% vs 0%, P<0.0001) and EFS (HR 0.23) but NOT OS (HR 0.99, P=0.96),
  because 57% of control patients crossed over to receive apamistamab.
  High crossover dilutes the OS difference between arms — patients who
  would have died on control received the experimental drug and
  survived. For field 6 (failure modes), when a trial with crossover
  shows negative OS but positive primary/EFS endpoints, the OS
  negativity is a trial-design artifact, not a drug failure. EFS is
  the more reliable indicator in crossover designs. This pattern
  generalizes to any transplant-conditioning trial where the
  experimental arm is the only path to transplant for refractory
  patients. (PMID 39298738.)

- **Lightweight subagent full-text retrieval (without paper-ingest brain
  pages).** This profile was built by a delegated subagent using a
  direct retrieval pipeline that does NOT create brain paper pages:
  PubMed esearch → esummary (title/journal screening) → efetch (full
  abstracts) → NCBI ID Converter (`/pmc/utils/idconv/v1.0/`, needs `-L`
  flag to follow 301 redirects) → jina reader on PMC article URLs
  (`https://r.jina.ai/https://www.ncbi.nlm.nih.gov/pmc/articles/PMCID/`).
  This retrieved genuine full text for 3/5 papers (SIERRA trial,
  Pagel 2009, 90Y Phase I), sufficient to ground fields 2, 3, and 6 in
  full-text content. **This is a valid rigor level for delegated
  profiling when the subagent's task is profile-building, not brain
  curation.** The full `paper-ingest` pipeline (creating `papers/`
  pages, bibliography walks, author ledger) is appropriate when the
  orchestrator wants the papers in the brain; for pure profile
  generation, the lightweight pipeline is faster and sufficient. The
  delegation section above currently says "ingests the papers via
  `paper-ingest`" — this should be understood as "retrieves full text
  via the paper-ingest methodology" (identity resolution, full-text
  retrieval, abstracts for paywalled papers), not necessarily
  "creates brain paper pages." See `references/lightweight-subagent-retrieval.md`
  for the exact command sequence.

  **Key technical details for the lightweight pipeline:**
  - The NCBI ID Converter (`idconv`) returns 301 redirects — `curl -sL`
    (follow redirects) is required, not `curl -s`.
  - jina reader on PMC article URLs (`r.jina.ai/https://www.ncbi.nlm.nih.gov/pmc/articles/PMCID/`)
    returns full-text markdown including Abstract, Introduction,
    Methods, Results, and Discussion sections. For the SIERRA trial
    (JCO, PMC11709001), this returned ~50K chars of full text.
  - jina reader on DOI URLs (`r.jina.ai/https://doi.org/10.1200/JCO.23.02018`)
    also works for paywalled journals with PMC open-access copies.
  - Europe PMC search API (`ebi.ac.uk/europepmc/webservices/rest/search`)
    may return "not found" for recent papers — the NCBI ID Converter
    is more reliable for PMID→PMCID resolution.
  - The `efetch` XML from PMC (`eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc`)
    has a ~50K char response cap — for long papers, jina reader on the
    PMC article URL is a better full-text source.

  (CD45/PTPRC profile, ~40K chars, 5 papers (3/5 full text via jina on
  PMC URLs, 2/5 abstract-only), 85+ PMID citations,
  working-docs/hitlist-profiles/cd45.md.)

- **2026-08-16 — ApoC-III key-paper-ingestion profile observations.**
  Cardiovascular/metabolic profile (clinical-trial tier, dyslipidemia).
  6 papers ingested (2/6 full text via EPMC PDF + PMC XML; 4/6
  abstract-only — NEJM, JAMA Cardiol, ATVB all paywalled with CAPTCHA
  blocks on jina). ~34.5K chars, 34 KB. New observations:
  (1) **PubMed keyword searches for antibody approaches miss
  foundational antibody papers.** Searching "ApoC-III antibody" (162
  PubMed results) did not surface the key anti-apoC-III antibody paper
  (Khetarpal et al., Nat Med 2017, PMID 28825717) in the top 10. It was
  found by tracing reference 155 in the comprehensive review's full
  text (PMID 38039351), then searching PubMed by author name + key
  terms. Added as a pitfall in the Pitfalls section. This is especially
  relevant for targets where the dominant modality is non-antibody
  (ASO, siRNA, small molecule) — the antibody proof-of-concept paper
  is buried in review reference lists, not in keyword search results.
  (2) **EPMC PDF retrieval via `europepmc.org/api/getPdf?pmcid=<PMCID>`
  works for OUP journals even when `isOpenAccess: N`.** PMID 38039351
  (Cardiovasc Res, OUP) had EPMC `isOpenAccess: N` but `hasPDF: Y` and
  `inPMC: Y` — the EPMC PDF endpoint returned the full 6.8 MB publisher
  PDF, extractable to 116K chars via pymupdf. This is the Branch 1b
  path documented in paper-ingest, now confirmed for OUP.
  (3) **PubMed XML PMCID can resolve to a completely different article.**
  PMID 38583092 (SHASTA-2 trial, JAMA Cardiol) had PubMed XML PMCID
  PMC10033404, but `efetch db=pmc&id=PMC10033404` returned the full text
  of an evinacumab trial (different article entirely). The EPMC record's
  pmcid (PMC11000138) was front-matter-only (19 KB). The SHASTA-2
  abstract was ultimately extracted from the PMC11000138 front-matter
  XML, which contained the structured abstract with full trial data.
  This mirrors the CGRP profile's PMCID cross-article mismatch
  (PMID 32266704/PMC7066477).
  (ApoC-III profile, ~34.5K chars, 6 papers (2/6 full text, 4/6
  abstract-only), 6 PMID citations,
  working-docs/hitlist-profiles/apoc-iii.md.)

- **2026-08-16 — EBV gp350 key-paper-ingestion profile observations.**
  Fortieth level-2 profile (clinical-trial tier, infectious disease — viral
  glycoprotein). EBV gp350 is the **first viral envelope glycoprotein**
  target profiled and the **first infectious disease target** outside of
  oncology. 8 papers ingested with full text (2/8 publisher-jina on
  Elsevier/Cell Press, 3/8 PMC XML, 1/8 EPMC PDF, 2/8 also PMC XML); 1
  paper abstract-only (Elsevier, paywalled — Biomed Pharmacother).
  ~36.8K chars, 16 unique PMIDs cited. See
  `references/ebv-gp350-profile-observations.md` for full detail. Key
  new patterns:

  (1) **Antigenic supersite — a single dominant neutralizing epitope
  cluster.** gp350's CR2-binding site (CR2bs) at the D1–D2 interface is
  described as a "highly neutralization-sensitive antigenic supersite."
  ALL known neutralizing mAbs (72A1, ATX-350-1/2, 769A9, 770E11,
  Cy137C02, Cy651H02) target this region. This is structurally grounded:
  the CR2bs is glycan-free, constitutively accessible, and located at the
  apex of the gp350 molecule. For field 5 (epitope landscape), this is
  the cleanest epitope landscape profiled — one supersite, multiple
  overlapping mAbs, all structurally characterized. Generalizable to
  viral glycoprotein targets where the receptor-binding site is the
  single neutralization-sensitive region (cf. HIV Env CD4bs, RSV F
  site Ø).

  (2) **Non-essential attachment protein — partial in vivo protection.**
  gp350 mediates B-cell attachment but is NOT essential for B-cell
  infection (alternative receptors CR1/CD35, HLA-II can partially bypass).
  In humanized mouse challenge, anti-gp350 mAbs showed only PARTIAL
  protection (prevented splenomegaly but viral DNA detected in some
  spleens), while anti-gp42 and anti-gH/gL mAbs showed COMPLETE
  protection (PMID 41707657). For field 6 (failure modes), this is a
  target-biology limitation, not an antibody failure — even the best
  anti-gp350 mAb cannot achieve sterilizing immunity alone. The fix is a
  cocktail or bispecific targeting multiple glycoproteins.
  Generalizable to viral targets where the attachment protein is
  non-essential (e.g., CMV gB vs gH/gL).

  (3) **Murine antibody immunogenicity as a failure mode.** The prototypic
  anti-gp350 mAb 72A1 (murine IgG1) was clinically tested in a pilot study
  of EBV-seronegative liver transplant recipients. ALL participants
  developed anti-drug antibodies and one had a hypersensitivity reaction
  (PMID 41707657). This is a FORMAT failure (murine origin), not a TARGET
  or EPITOPE failure — the epitope (CR2bs) is correct. The fix is fully
  human or humanized antibodies (hu72A1, ATX-350 mAbs, 769A9/770E11).
  Generalizable: for any viral glycoprotein target with a historic murine
  mAb that showed partial efficacy but failed due to immunogenicity, the
  target is NOT invalidated — a human/humanized antibody targeting the
  same epitope is the next step.

  (4) **Receptor-Fc fusion as a novel antibody modality.** A CR2-Fc
  fusion (CR2 SCR1-2 domains fused to human IgG1 Fc) was constructed as
  a "receptor-body" that binds gp350 at nanomolar affinity (KD = 1.38 nM),
  competes with 72A1, and neutralizes EBV infection in B cells (PMID
  39792550). This is the first receptor-Fc fusion profiled as an
  antibody alternative. For field 4 (antibody landscape), include
  receptor-Fc fusions as a distinct format — they guarantee targeting
  the functionally critical receptor-binding site. Generalizable to any
  viral glycoprotein where the host receptor is a single-domain protein
  (CR2 SCR1-2, CD4 D1-D2 for HIV).

  (5) **Vaccine-elicited macaque mAbs as a discovery source.** The most
  potent anti-gp350 mAbs (Cy137C02, IC50 = 6 ng/mL; 769A9, IC50 = 11
  ng/mL) were isolated from gp350-ferritin nanoparticle-vaccinated
  cynomolgus macaques and EBV-infected human "elite neutralizers,"
  respectively — both >100-fold more potent than 72A1 (IC50 = 16
  μg/mL). For field 4 (antibody landscape), mAbs isolated from NHP
  vaccine studies and human elite neutralizers are a rich source of
  therapeutic candidates. Generalizable to any viral target with a
  vaccine program in NHPs.

  (6) **Glycan-free receptor-binding interface.** Despite 12
  N-glycosylation sites on gp350, the CR2-binding interface is
  completely glycan-free — no glycans shield the neutralization supersite
  (PMID 39792550). For field 9 (structural information), this makes the
  CR2bs fully accessible to antibodies without glycan shielding.
  Generalizable: for viral glycoproteins, map whether the
  receptor-binding site is glycan-free — this determines whether the
  neutralization epitope is directly accessible or requires
  glycan-compatible antibody approaches.

  (7) **Elsevier/Cell Press papers are jina-recoverable.** Both Immunity
  (PMID 39909035, 112K chars) and Cell Rep (PMID 39792550, 83K chars)
  were fully retrieved via jina reader on the Elsevier/Cell Press DOI
  redirect URL. This confirms the paper-ingest observation that Cell
  Press journals are jina-accessible via the linkinghub.elsevier.com
  redirect. For target profiling, Immunity and Cell Rep structural
  papers are high-value full-text sources for fields 5 and 9.

  (EBV gp350 profile, ~36.8K chars, 8 papers full text + 1 abstract-only,
  16 unique PMIDs cited, working-docs/hitlist-profiles/ebv-gp350.md.)

- **2026-08-16 — HBV surface antigen (HBsAg) key-paper-ingestion
  profile observations.** Forty-first level-2 profile (clinical-trial
  tier, infectious disease — viral envelope glycoprotein, second
  after EBV gp350). HBV HBsAg is the envelope protein of both HBV
  and HDV (satellite virus using HBsAg as its envelope). 5 papers
  selected; 2/5 full text retrieved (PMID 24492346 via EPMC PDF
  [mAbs, OUP/Landes Bioscience], PMID 41405995 via publisher-jina on
  Elsevier/Cell Press linkinghub redirect [Cell Reports, 105K chars]);
  3/5 abstract-only (PMID 37459920 J Hepatol, PMID 42465932 medRxiv,
  PMID 38679166 Antiviral Res — all Elsevier/paywalled with CAPTCHA
  blocks on jina). ~60K chars, 5 PMIDs, 20+ PMID citations. Key
  new patterns:

  (1) **Subviral particle (SVP) immune decoy as a target-biology
  challenge.** HBV produces SVPs (composed entirely of HBsAg) in
  10³–10⁶-fold excess over infectious virions, acting as immune
  decoys that absorb neutralizing antibodies and drive T/B cell
  exhaustion. This is a target-specific mechanism not seen in other
  profiled viral glycoproteins (EBV gp350, RSV F, HIV gp120, SARS-
  CoV-2 RBD). For field 2, document the SVP-to-virion ratio and its
  immune evasion implications. For field 6, the SVP "antigen sink"
  is a distinct failure mode — antibodies may be consumed
  subtherapeutically by SVPs before neutralizing infectious virions.
  The fix is higher dosing, Fc engineering for enhanced immune
  complex clearance, combination with siRNA to reduce total HBsAg
  production, or bispecific formats with superior avidity/endocytosis
  (PMID 41405995, 42465932). Generalizable to any viral target where
  non-infectious particles vastly outnumber infectious virions.

  (2) **Fc-dependent effector functions as the SOLE in vivo mechanism
  for a class of antibodies.** Anti-preS2 antibodies (Bc8.108,
  Bc8.121) showed robust in vivo antiviral activity entirely through
  Fc-dependent mechanisms (ADCC, CDC) despite low in vitro
  neutralization potency. Fc-silent N297A mutants completely lacked
  in vivo antiviral activity. This is the first target profiled where
  a distinct antibody epitope class depends ENTIRELY on Fc-effector
  function for in vivo efficacy — not just "augmented by" Fc function
  (as with afucosylated HIV bNAbs) but absolutely requiring it. For
  field 6, Fc-effector dependence is a distinct success/failure
  mode: the Fc format choice (wild-type vs GAALIE vs Fc-silent)
  is not a secondary optimization but a primary determinant of
  efficacy for this epitope class. Generalizable to any target where
  different epitope classes have different mechanistic dependencies
  (neutralization vs Fc-effector). (PMID 41405995.)

  (3) **Engineered Fc (GAALIE) as a differentiation platform for
  viral envelope antibodies.** Tobevibart (VIR-3434) uses a GAALIE
  Fc that increases activating FcγR binding, decreases inhibitory
  FcγRIIb binding, and converts immune complexes into potent DC
  activators and T-cell stimulators — a "vaccinal effect" beyond
  neutralization. This is the first profiled target where Fc
  engineering transforms the mechanism from passive neutralization
  to active immune reprogramming. For field 4 (antibody landscape)
  and field 11 (differentiation), Fc-engineered variants that
  enhance immune complex uptake and T-cell activation represent a
  new modality class distinct from naked IgG1. Generalizable to any
  chronic viral infection where immune tolerance is a barrier
  (HBV, HCV, HIV — the "vaccinal effect" concept). (PMID 40882923,
  42465932.)

  (4) **Combination antibody therapy with non-overlapping epitope
  bins — now validated in vivo for HBV.** Combining anti-preS2
  (Bc8.108) + anti-S (Bc8.327) bNAbs achieved 3.7 log₁₀ HBsAg
  reduction vs 1.7 and 3.0 log₁₀ for either alone, with sustained
  suppression. This validates the HIV combination bNAb paradigm
  (non-overlapping epitope bins) for HBV. For field 6, the
  combination strategy is a success factor; for field 11, bispecific
  versions (cf. C4D2-BsAb, PMID 24492346) that target two
  non-overlapping epitope bins in a single molecule are a
  differentiation opportunity. Generalizable to any viral target
  where multiple epitope classes with complementary mechanisms
  exist. (PMID 41405995.)

  (5) **medRxiv preprint DOI resolution failure.** PMID 42465932
  (medRxiv preprint) had a non-standard DOI (10.64898/2026.07.03.
  26357226) that the fetch_fulltext.py ladder could not resolve —
  Europe PMC had no record, and the DOI did not follow the standard
  medRxiv/bioRxiv format (10.1101/YYYY.MM.DD.NNNNNN). For
  preprints with non-standard DOIs, fall back to the medRxiv
  article URL directly or use PubMed abstract-only.

  (6) **Jina reader on ScienceDirect returns CAPTCHA/Cloudflare
  interstitial pages, not empty responses.** When jina reader
  attempts ScienceDirect URLs, it returns ~113K chars of content
  that is actually a Cloudflare "Are you a robot?" CAPTCHA page
  with embedded JavaScript — not the article text. This can be
  mistaken for successful retrieval if only character count is
  checked. Always verify jina output by checking the first ~200
  chars for "Just a moment" or "Are you a robot?" before treating
  the output as article full text. The fetch_fulltext.py script
  does not currently check for this. (Observed for both PMID
  37459920 [J Hepatol] and PMID 38679166 [Antiviral Res].)

  (7) **User intervention to halt paywalled paper retries is the
  expected correction pattern.** During this session, the user
  sent an out-of-band message: "If you're stuck retrying paywalled
  Elsevier papers, stop now. Use the abstracts you already have
  plus domain knowledge to write the HBV surface antigen profile.
  3 papers (even abstract-only) is sufficient. Write the profile
  NOW." This is the expected behavior when the paywalled paper
  timeout rule is not followed aggressively enough. The subagent
  had already spent significant time on retry attempts (jina
  direct, ScienceDirect jina, DOI-only jina) that all returned
  CAPTCHA pages. The lesson: check the FIRST retrieval result
  before attempting retries — if the first result is a CAPTCHA
  page, all subsequent attempts on the same publisher will also
  fail. Check immediately and proceed to abstract-only. The user
  expects abstract-only to be the default for Elsevier
  ScienceDirect, not the fallback after multiple failed attempts.

  (8) **OUP/Landes Bioscience journals (mAbs) are EPMC PDF-
  retrievable.** PMID 24492346 (mAbs, Landes Bioscience/OUP) had
  EPMC `inPMC: Y, isOpenAccess: N, hasPDF: Y` — the EPMC PDF
  endpoint returned the full article PDF, extractable to 41K chars.
  This confirms the paper-ingest Branch 1b path for mAbs/Landes
  Bioscience. For target profiling, mAbs is a high-value journal
  for antibody characterization papers (format, epitope, Fc
  engineering data) and is reliably retrievable via EPMC PDF.

  (HBV surface antigen profile, ~60K chars, 5 papers (2/5 full
  text, 3/5 abstract-only), 5 PMIDs, 20+ PMID citations,
  working-docs/hitlist-profiles/hbv-surface-antigen.md.)

- **2026-08-16 — Sortilin (SORT1) key-paper-ingestion profile
  observations.** Forty-second level-2 profile (clinical-trial tier,
  neuroscience — FTD/AD). Sortilin is a Vps10p-family type I
  transmembrane sorting receptor; the therapeutic strategy is NOT to
  block the target's function but to block its endocytic clearance of
  progranulin (PGRN), thereby elevating extracellular/CNS PGRN. This
  is the **second "inverse-target" profile** after progranulin itself
  (progranulin.md, same session batch) — the antibody targets the
  clearance receptor, not the disease-causing protein. 5 papers
  ingested with 100% full-text retrieval via PMC XML (all 5 had PMCIDs
  with open-access XML). ~50K chars, 204 PMID citations, 48 unique
  PMIDs found in PubMed search. See
  `references/sortilin-profile-observations.md` for full detail.
  Key new patterns:

  (1) **Inverse-target profiling — antibody targets the clearance
  receptor, not the disease protein.** Sortilin is the clearance
  receptor for PGRN; the disease (FTD-GRN) is caused by PGRN
  haploinsufficiency. The therapeutic antibody blocks sortilin to
  increase PGRN, not to inhibit sortilin's normal function. This
  inverts the standard profile framing: "effect of blockade" in
  field 2 describes a *beneficial* outcome (PGRN elevation), not an
  on-target pharmacology to manage. Field 6 success factors include
  "dual mechanism (competitive blockade + receptor down-regulation)"
  as the winning combination. Field 8 safety is framed around PGRN
  over-supplementation risks (metabolic, oncologic), not sortilin
  loss. Generalizable to any target where the antibody blocks a
  clearance/degradation pathway to elevate a deficient protein
  (cf. progranulin.md, SORT1 axis).

  (2) **Alternative scaffold (affibody) in the antibody landscape.**
  The sortilin profile is the first to include a non-IgG alternative
  scaffold (affibody-peptide fusion, ABD-A3-PGRNC15*) in field 4
  (antibody landscape). The affibody achieves comparable PGRN
  elevation to latozinemab (EC50 1.30 vs 0.68 nM, not significant)
  via biparatopic binding — the affibody moiety binds one epitope
  while the fused PGRN C-terminal peptide occupies the natural
  ligand site, achieving >380-fold affinity improvement through
  avidity. For field 4, include alternative scaffolds (affibody,
  nanobody, DARPins) as distinct entries when they target the same
  epitope class with a different format. For field 11, the small
  size (~6.5 kDa vs ~150 kDa IgG), bacterial producibility, and
  lower cost are differentiation factors for chronic CNS therapy.

  (3) **100% PMC XML retrieval for neuroscience OA journals.** All 5
  papers were retrieved via PMC XML with no paywall issues — the
  journal mix (J Transl Med, Front Immunol, Alzheimer's Res Ther,
  Alzheimer's Dementia, Neuron) all had inPMC=Y and accessible XML.
  This contrasts sharply with the C5 profile (20% retrieval) and
  HBV profile (40% retrieval). Neuroscience/FTD papers in OA-friendly
  journals (BioMed Central, Frontiers, Springer) have very high
  full-text retrieval rates. For delegation, neuroscience targets
  with papers in these journals are low-risk for the paywall timeout
  problem.

  (4) **Cross-species surrogate antibody as a standard pattern.**
  Latozinemab does not cross-react with rodent sortilin — a mouse
  cross-reactive surrogate (S15JG) was used for all mouse studies.
  This is the same pattern seen with latozinemab's progranulin
  profile. For field 4, document the surrogate antibody separately.
  For field 7 (assay systems), the surrogate's different epitope
  (slightly different from latozinemab within the β-propeller) is a
  caveat for translating mouse efficacy data to clinical predictions.

  (5) **Trans signaling paradigm — ligand and receptor on different
  cell types.** PGRN is secreted by activated microglia while
  sortilin is expressed on neurons (not microglia). The endocytosis
  occurs in trans: microglial PGRN → neuronal sortilin → lysosomal
  delivery. This was demonstrated by sciatic nerve injury
  experiments showing PGRN induction in activated microglia
  surrounding sortilin-positive motoneurons (PMID 21092856). For
  field 2, document the cell-type separation and trans signaling
  paradigm. For field 11, this means the therapeutic antibody must
  engage sortilin on neurons specifically — the cell-type-specific
  expression is a targeting advantage (no need to block sortilin on
  microglia, which don't express it).

  (6) **Existing sibling profile (progranulin.md) as a cross-reference
  resource.** The progranulin profile (same session) was an
  invaluable reference — it already contained the same latozinemab
  and AL101 clinical data, the same Sort1−/− mouse data, and the
  same epitope bin system. When profiling a target that is the
  binding partner / clearance receptor of an already-profiled target,
  read the sibling profile first to avoid redundant literature
  search and to ensure consistent cross-referencing. The two profiles
  are complementary: progranulin.md focuses on the disease-causing
  protein (the therapeutic goal is to elevate it), while sortilin.md
  focuses on the clearance receptor (the antibody target).

  (Sortilin/SORT1 profile, ~50K chars, 5 papers (5/5 full text via
  PMC XML), 204 PMID citations,
  working-docs/hitlist-profiles/sortilin.md.)

- **2026-08-16 — Renin (REN) key-paper-ingestion profile
  observations.** Forty-third level-2 profile (clinical-trial tier,
  cardiovascular — RAAS enzyme). Renin is the rate-limiting enzyme of
  the RAAS and the first secreted aspartic protease profiled. The
  clinical context is dominated by small-molecule renin inhibitors
  (remikiren, aliskiren) — no therapeutic antibody against renin has
  ever been developed. 7 papers ingested (1/7 full text via PMC XML;
  6/7 abstract-only — all paywalled). ~27K chars, 83 PMID citations.
  See `references/renin-profile-observations.md` for full detail.
  Key new patterns:

  (1) **Small-molecule-dominant target with no antibody pipeline.**
  Renin is the first profiled target where the entire clinical
  landscape is small-molecule (aliskiren approved, remikiren
  discontinued), and the only antibodies ever raised against it are
  research tools (PMID 6788795, 1548051). For field 4, list research
  mAbs alongside small-molecule inhibitors, each tagged "not an
  antibody." For field 10, state "no therapeutic antibodies in
  development" explicitly. For field 11, the differentiation framing
  is inverted: "why would an antibody be better than the approved
  small molecule" — answer: longer half-life, >99% active-site
  blockade, (P)RR co-targeting via bispecific.

  (2) **Reactive renin secretion as a mechanism-of-action ceiling.**
  Renin inhibition triggers compensatory reactive renin secretion.
  Aliskiren blocks only 90–95% of plasma renin activity; the expanded
  renin pool offsets BP-lowering at higher doses (600 mg = 300 mg
  plateau) (PMID 17485026). This is a target-inherent limitation,
  not drug-specific. For field 6, this is a distinct failure class —
  a "mechanism-of-action ceiling" separate from epitope, population,
  format, or trial-design failures. For field 11, >99% blockade or
  a depleting antibody (clearing circulating renin) are the
  differentiation opportunities.

  (3) **Dual RAAS blockade toxicity as a class effect (ALTITUDE).**
  ALTITUDE (PMID 23121378) stopped early — aliskiren + ACEi/ARB in
  diabetic CKD/CVD patients: hyperkalemia 11.2% vs 7.2%, hypotension
  12.1% vs 8.3%, possible nonfatal stroke increase. ONTARGET
  (ramipril + telmisartan) showed the same pattern. For field 6,
  the failure was dual RAAS blockade design + diabetic population,
  not the target. Monotherapy was safe. For field 8, dual RAAS
  blockade contraindications apply to any new renin agent including
  an antibody.

  (4) **100% paywall rate for cardiovascular landmark papers.** All
  7 papers were paywalled (OUP, AHA, Wiley, NEJM); only the EXCLI J
  review (PMID 26417326) retrieved via PMC XML. Lowest retrieval rate
  of any profile (1/7 = 14%). Cardiovascular papers from 1980s–2000s
  are in journals that predate OA. Abstract-only was sufficient —
  structured abstracts (ALTITUDE, remikiren PK) carried enough trial
  design and safety data to ground fields 2, 3, and 6.

  (5) **(Pro)renin receptor ((P)RR) as a bispecific co-target
  opportunity.** (P)RR activates prorenin non-proteolytically,
  contributing to tissue RAAS independent of circulating
  angiotensin II (PMID 26417326). No clinical agent targets (P)RR.
  A bispecific anti-renin + anti-(P)RR antibody could block both
  circulating and tissue RAAS in a single molecule, potentially
  avoiding the dual small-molecule RAAS toxicity of ALTITUDE.
  Blue-ocean opportunity specific to the renin/(P)RR axis.

  (Renin/REN profile, ~27K chars, 7 papers (1/7 full text, 6/7
  abstract-only), 83 PMID citations,
  working-docs/hitlist-profiles/renin.md.)

- **2026-08-16 — PAI-1/SERPINE1 key-paper-ingestion profile
  observations.** Forty-fourth level-2 profile (clinical-trial tier,
  cardiovascular — serpin/fibrinolysis). PAI-1 is a secreted serpin
  (not surface-bound) that inhibits tPA/uPA — the first profiled target
  where the therapeutic strategy is to block an endogenous inhibitor
  (i.e., inhibit the inhibitor) to restore a lost function
  (fibrinolysis). 5 papers ingested (3/5 via PMC XML, 2/5 via EPMC
  PDF); 0 abstract-only. ~41K chars, 14 additional abstracts
  batch-fetched for citation grounding, 25+ unique PMIDs cited. Key
  new patterns:

  (1) **Proactive paper substitution for paywalled originals.** 3 of 5
  initially selected papers (Elsevier/Wiley) were paywalled with no
  PMC copy and no jina recovery. Instead of falling back to
  abstract-only, additional PubMed searches found OA replacements
  covering the same topics (review, structural, oncologic), yielding
  5/5 full-text papers. Added as a pitfall in the Pitfalls section.
  The 2-minute paywall timeout applies to retrying a paywalled paper,
  not to finding an OA replacement.

  (2) **Glycosylation as a critical epitope-determining factor for
  antibody cross-reactivity.** PAI-1 has three N-glycosylation sites
  (Asn209, Asn265, Asn329); glycosylation at N265 in mouse PAI-1
  blocks recognition by MA-124K1 and MA-H4B3, which inhibit
  recombinant non-glycosylated PAI-1 in vitro but fail in vivo. This
  is a target-specific instance of the general principle: antibodies
  must be screened on the glycosylated form, not just recombinant
  protein. For field 2 (species cross-reactivity) and field 6
  (failure modes), glycosylation-dependent epitope masking is a
  distinct failure class. Generalizable to any secreted
  glycoprotein target with tissue-specific glycosylation.

  (3) **Three mechanistic classes of neutralizing antibodies — a
  template for serpin targets.** PAI-1 antibodies fall into three
  functional classes: (1) Michaelis complex blockers (prevent
  PAI-1/PA binding), (2) switching antibodies (induce substrate
  behavior), (3) latency accelerators (convert active to inactive
  form). Each class has distinct epitope locations and distinct
  vitronectin compatibility. For field 5 (epitope landscape) and
  field 6 (success/failure), this three-class framework is a
  template for profiling any serpin target where conformational
  state determines activity.

  (4) **Vitronectin shielding as a competitive landscape factor.**
  Vitronectin-bound PAI-1 is the predominant in vivo form. Small
  molecule inhibitors lose activity against vitronectin-bound
  PAI-1 (binding sites overlap), while switching antibodies are
  POTENTIATED by vitronectin. For field 6 and field 10, the
  vitronectin compatibility of each inhibitor class is a key
  competitive differentiator. Generalizable to any target with a
  high-abundance circulating cofactor that alters epitope
  accessibility.

  (PAI-1/SERPINE1 profile, ~41K chars, 5 papers (5/5 full text via
  PMC XML + EPMC PDF), 25+ PMID citations,
  working-docs/hitlist-profiles/pai-1.md.)

- **2026-08-16 — CD44 key-paper-ingestion profile observations.**
  Forty-fifth level-2 profile (preclinical tier, immunology — adhesion
  receptor / CSC marker). CD44 is a type I transmembrane
  glycoprotein, the principal hyaluronan receptor, with ≥20 isoforms
  (85-230 kDa) via alternative splicing. It is a ubiquitous target:
  expressed on virtually all cell types, making it both a broadly
  relevant therapeutic target and a challenging one (antigen sink,
  on-target/off-tumor toxicity). 3 papers ingested (0/3 full text —
  all Elsevier/Wiley, no PMC copies); 42K-char profile, 59 PMID
  citations across 3 ingested + 6 supplementary abstracts. Key new
  patterns:

  (1) **100% paywall survival via database supplementation.** All 3
  ingested landmark papers (Naor 1997, Siegelman 1999, Skandalis
  2019) were paywalled with no PMC copies and no jina/Wayback
  recovery. The complete 11-field profile was built from PubMed
  structured abstracts supplemented by UniProt (function, domains,
  glycosylation, topology) and PDB (15+ structures including
  antibody-bound 32NZ scFv complex). Fields 5 and 9 were grounded
  entirely in PDB structural data. This demonstrates that
  abstract-only is not a thin fallback — with database
  supplementation it can produce a full-depth profile. Added as a
  pitfall.

  (2) **Supplementary antibody-landscape abstracts.** The 3
  ingested biological papers (reviews) did not cover the clinical
  antibody landscape. Additional PubMed searches for known antibody
  names (RG7356, bivatuzumab, A3D8) retrieved 6 supplementary
  abstracts with Phase I clinical trial data (response rates, DLTs,
  MTDs, discontinuation reasons, fatal skin toxicity for
  bivatuzumab). These grounded fields 4, 6, and 8. Added as a
  pitfall — distinct from "batch-fetch for paywalled citation
  papers" because these are papers you wouldn't ingest as primary
  sources but whose clinical data is essential for the profile.

  (3) **UniProt entry-name search returns fragments.** Searching
  UniProt by `CD44_HUMAN` returned Q99900 (177-aa fragment, not the
  canonical entry). The correct approach is `gene:CD44 AND
  organism_id:9606`, which returns P16070 (742-aa canonical) plus
  isoform fragments. Added as a pitfall.

  (4) **PDB search requires POST.** The RCSB search API rejects GET
  requests with URL-encoded JSON. Use POST with
  `Content-Type: application/json`. Added as a pitfall.

  (5) **Topic-divided PubMed search for landmark paper selection.**
  For multi-role targets, searching 4 separate topic queries
  yielded 3 papers covering all biological roles more efficiently
  than one broad query. Added as a pitfall.

  (6) **Ubiquitous expression as a target-specific challenge.** CD44
  is expressed on virtually all cell types, creating a large antigen
  sink (TMDD at ≥1200 mg for RG7356) and on-target/off-tumor
  toxicity (bivatuzumab's fatal skin toxicity from CD44v6 on
  keratinocytes). For field 6 and 11, ubiquitous-expression targets
  require conditional activation, tumor-selective epitope targeting,
  or probody formats — systemic naked antibodies face an inherent
  therapeutic-index ceiling. This pattern generalizes to any
  ubiquitously expressed target (CD44, CD45, CD47).

  (CD44 profile, ~42K chars, 3 papers (0/3 full text, 3/3
  abstract-only), 59 PMID citations,
  working-docs/hitlist-profiles/cd44.md.)

### IL-35 observations (heterodimeric cytokine + subunit-sharing specificity challenge + Treg cytokine neutralization)

IL-35 (Interleukin-35) is a **heterodimeric cytokine** (IL-12p35/EBI3)
— the first profiled target where **subunit sharing between multiple
cytokines creates a fundamental antibody specificity challenge**. IL-35
shares its p35 subunit with IL-12 and IL-23, and its EBI3 subunit with
IL-27. Preclinical tier (immunology/oncology). 3 landmark papers ingested
(1/3 full text via PMC XML: Turnis 2016 Immunity, 35K chars; 1/3 via
publisher-jina: Collison 2007 Nature, abstract + figure legends only;
1/3 abstract-only: Yi 2024 Mol Cancer Ther, AACR Cloudflare block).
~37K chars profile, 10 unique PMIDs cited. Key new patterns:

- **Subunit-sharing cytokines require heterodimer-specific epitope
  targeting.** IL-35 shares EBI3 with IL-27 and p35 with IL-12/IL-23.
  A naive anti-EBI3 antibody would block both IL-35 and IL-27; a naive
  anti-p35 antibody would block IL-12 and IL-23 as well. The preclinical
  anti-IL-35 antibody (Ebi3-specific mAb) neutralizes IL-35 but NOT
  IL-27 — meaning the epitope is conformational and specific to the
  p35/EBI3 heterodimer context, not the EBI3 subunit alone. For field 1
  (target identity), explicitly note which subunits are shared with
  which other cytokines — this defines the cross-reactivity constraint.
  For field 5 (epitope landscape), the epitope MUST be on the
  heterodimer interface or a conformational surface unique to the
  heterodimer, not on an individual subunit. For field 6 (failure modes),
  subunit cross-reactivity is a distinct failure class: an antibody
  cross-reacting with IL-27 (via shared EBI3) would block a cytokine
  with opposing biological function (IL-27 is immunostimulatory in
  cancer, IL-35 is immunosuppressive). For field 11 (differentiation),
  an antibody targeting the p35–EBI3 interface (distinct from the
  p28–EBI3 interface of IL-27) is the specificity strategy.
  Generalizable to any heterodimeric cytokine where subunits are shared
  (IL-12/IL-23 share p40, IL-35/IL-27 share EBI3, IL-35/IL-12 share p35).
  (PMID 26872697.)

- **Treg-secreted cytokine neutralization (not Treg depletion) as a
  safer therapeutic strategy.** The IL-35 antibody neutralizes the
  cytokine without depleting Tregs — preserving Treg number and their
  non-IL-35 suppressive functions (IL-10, TGF-β). In contrast, total
  Treg depletion (Foxp3DTR) causes fatal autoimmune inflammation.
  Anti-IL-35 treatment showed NO inflammatory lesions in extensive
  histological analysis (lymph nodes, lungs, kidneys, liver, spleen,
  small intestine, skin), even with long-term (10-week) systemic
  administration. This is the canonical example of **cytokine
  neutralization as a safer alternative to cell depletion** for Treg
  targets. For field 6 (failure/success modes), the success factor is
  mechanism selectivity: blocking one of three Treg inhibitory cytokines
  (IL-35) while preserving the other two (IL-10, TGF-β) and the Tregs
  themselves. For field 8 (safety), this is the headline safety
  differentiator vs. Treg-depleting antibodies (anti-CTLA-4, anti-CCR8,
  anti-CD25). Generalizable to any Treg-secreted effector molecule
  where the goal is to partially disable Treg suppression without
  causing autoimmunity. (PMID 26872697.)

- **Treg-derived cytokine promoting T cell exhaustion — a dual
  mechanism for immunosuppression.** IL-35 not only suppresses T cell
  proliferation but also promotes T cell exhaustion by inducing
  expression of multiple inhibitory receptors (PD1, TIM3, LAG3) on
  CD8+ and CD4+ T cells in the tumor microenvironment. In
  Treg-specific IL-35 knockout mice (Foxp3Cre-YFP.Ebi3L/L), CD8+ T
  cells did NOT express multiple IRs — the majority were PD1neg/PD1int
  (~70-80%) vs. ~40-60% co-expressing 2-3 IRs in controls. This means
  IL-35 blockade addresses BOTH the suppression arm (enhanced
  proliferation/effector function) AND the exhaustion arm (reduced IR
  expression). For field 2 (biological mechanism), document both arms
  of the immunosuppressive mechanism. For field 6, the dual mechanism
  explains why anti-IL-35 was comparable to anti-PD1 in B16 melanoma
  — both target T cell exhaustion, but via different upstream drivers
  (Treg cytokine vs. checkpoint receptor). However, the anti-IL-35 +
  anti-PD1 combination showed NO additive benefit — suggesting
  overlapping or redundant exhaustion pathways. Generalizable to any
  Treg-secreted factor that promotes T cell exhaustion (IL-10, TGF-β
  may have similar dual mechanisms). (PMID 26872697.)

- **iTr35 cells — IL-35-induced infectious tolerance as a positive
  feedback loop.** IL-35 converts naive T cells into IL-35-producing
  induced regulatory T cells (iTr35 cells) via a unique STAT1–STAT4
  heterodimer signaling pathway. iTr35 cells are Foxp3-independent,
  stable in vivo, and mediate suppression via IL-35. This creates a
  positive feedback loop: Tregs produce IL-35 → converts naive T cells
  to iTr35 → iTr35 cells produce more IL-35. For field 2 (biological
  mechanism), the feedback loop amplifies immunosuppression in the
  tumor microenvironment. For field 6 (failure modes), this feedback
  loop could limit antibody efficacy if the antibody does not block
  iTr35 conversion (the antibody neutralizes existing IL-35 but new
  iTr35 cells may continue producing it). For field 11
  (differentiation), an antibody that blocks both IL-35 function AND
  iTr35 conversion (by preventing IL-35 receptor signaling) would be
  superior to one that only neutralizes soluble IL-35.
  (PMID 18033300, PMID 22306691.)

- **AACR journals (Mol Cancer Ther) are Cloudflare-blocked for jina
  reader.** PMID 37988561 (Mol Cancer Ther, 2024) returned a Cloudflare
  CAPTCHA interstitial page (~480 chars: "Just a moment...") via jina
  reader, not the article content. This confirms the paper-ingest
  known-blocks entry for AACR journals — the Cloudflare protection
  prevents all automated full-text retrieval (jina, direct curl, EPMC
  PDF). For target profiling, AACR journal papers are abstract-only by
  default. The EPMC abstract (1,399 chars) was sufficient for a review
  paper. This adds Mol Cancer Ther to the known-blocks alongside
  ScienceDirect/Elsevier and ASH/Blood. (PMID 37988561.)

- **Nature 2007 articles (no PMCID) return abstract + figure legends
  via jina, not full body text.** PMID 18033300 (Collison 2007,
  Nature) returned 88K chars via publisher-jina, but the content was
  the article page HTML rendered as markdown — cookie consent banners,
  navigation, abstract, figure legends, references, and "similar
  content" sections, but NOT the article body text (paywalled). The
  abstract (2,006 chars) and four figure legends were the usable
  content. This confirms the CXCR6 observation that subscription
  Nature research articles (no PMCID) are effectively abstract-only
  via jina. The figure legends DID contain useful information
  (experimental design descriptions for each figure). For target
  profiling, always extract figure legends from Nature jina output —
  they contain more experimental detail than the abstract alone.
  (PMID 18033300.)

(IL-35 profile, ~37K chars, 3 papers ingested (1/3 full text via PMC
XML, 1/3 abstract+figures via publisher-jina, 1/3 abstract-only via
EPMC), 10 unique PMIDs cited,
working-docs/hitlist-profiles/il-35.md.)

- **2026-08-16 — TAG-72 profile: PubMed search pollution by IAEA
  molecular imaging database entries; carbohydrate antigen with
  undefined mucin carrier; radioimmunotherapy-only landscape; 0%
  full-text retrieval for pre-2000 papers.** TAG-72 (tumor-associated
  glycoprotein 72) is a preclinical-tier oncology target — a sialyl-Tn-
  related glycan epitope on mucin-type glycoproteins. 3 papers ingested
  (all abstract-only, 0% full-text retrieval). ~25K chars, 3 unique
  PMIDs cited. New observations:

  (1) **PubMed searches for antibody target names are heavily polluted
  by IAEA Molecular Imaging Database entries.** Initial searches for
  "TAG-72 antibody[Title/Abstract]" and "TAG72 tumor-associated
  glycoprotein[Title/Abstract]" returned 5+ results each from the IAEA
  Molecular Imaging Database — entries by Cheng KT and Chopra A (2004,
  PMIDs in the 2064xxxx and 2204xxxx ranges) with titles like
  "Radioiodinated anti–TAG-72 CC49 Fab' antibody fragment" and
  "(124)I-Labeled humanized CH2-domain-deleted anti-TAG-72 monoclonal
  antibody." These are NOT research papers — they are database records
  that PubMed indexes. They dominated the relevance-sorted results,
  pushing actual landmark papers below the cutoff. **Fix:** Search
  with specific terms that include author names, clinical trial
  designations, or mechanism keywords rather than just the target
  name + generic terms. Working queries: "CC49[Title/Abstract] AND
  (clinical trial OR radioimmunotherapy)" and "TAG-72[Title/Abstract]
  AND (B72.3 OR monoclonal antibody)." The database entries do not
  contain "clinical trial," "phase," "B72.3," or author names like
  "Schlom," "Divgi," or "Alvarez" — these terms filter them out
  naturally. When a PubMed search for a target name returns >5 results
  from the same author (Cheng KT, Chopra A) with similar generic
  titles, re-run with more specific clinical/mechanism terms.

  (2) **Carbohydrate antigen with heterogeneous/undefined mucin
  carriers extends the SLeX/CA19-9 pattern.** The SLeX/CA19-9
  observation (2026-08-16) established that carbohydrate epitopes
  require "Not applicable" for gene symbol, UniProt ID, MW, and
  oligomerization. TAG-72 adds a new variant: the carrier glycoprotein
  is NOT a known, named mucin (unlike SLeX where MUC1/MUC16 are
  identified carriers). TAG-72 is defined *immunologically* — by B72.3
  and CC49 monoclonal antibody reactivity against a "high molecular
  weight mucin-like glycoprotein complex." The molecular identity of
  the carrier(s) is not fully characterized. For field 1, state "No
  single gene symbol — TAG-72 is a carbohydrate antigen (mucin-type
  O-glycan epitope)" and note that the epitope is defined by antibody
  reactivity, not by a specific gene product. For field 5 (epitope
  landscape), the "epitope" IS the glycan structure itself (sialyl-Tn-
  related), and B72.3/CC49 bind the same or overlapping epitope — there
  is no epitope binning data because the antigenic determinant is a
  single glycan structure. This extends the non-protein-target
  adaptation to targets where the molecular identity is defined by
  antibody reactivity rather than by biochemical characterization.

  (3) **Radioimmunotherapy-only antibody landscape — first target
  with NO non-radioimmunotherapy antibody format.** TAG-72 is the
  first target profiled where ALL clinical-stage antibodies (B72.3,
  CC49, humanized CC49, ΔCH2 constructs) are radioimmunoconjugates
  (131I, 177Lu, 90Y, 225Ac) or pretargeting fusion proteins. No naked
  IgG, ADC, bispecific, or CAR-T has been clinically tested. This
  creates a distinct differentiation opportunity pattern for field 11:
  the ENTIRE non-radioimmunotherapy format space is unexplored. An
  ADC against TAG-72 (delivering MMAE, DM4, SN-38, or deruxtecan) could
  achieve therapeutic efficacy without the marrow toxicity limitations
  of radioimmunotherapy. A bispecific T-cell engager (TAG-72 × CD3)
  analogous to cibisatamab (CEA × CD3) is feasible given TAG-72's
  adenocarcinoma expression profile. A CAR-T targeting TAG-72 is
  viable. For field 10 (competitive landscape), note that the
  radioimmunotherapy-only pipeline is both a validation (TAG-72 is
  antibody-accessible in vivo) and a gap (no cytotoxic-payload or
  immune-recruiting approach has been tested). For field 6 (failure
  modes), the radioimmunotherapy-specific failures (hematologic DLT,
  HAMA, poor bulky-disease penetration) are NOT inherent to the
  target — they are format-specific limitations that a different
  modality could overcome.

  (4) **0% full-text retrieval for pre-2000 subscription journal
  papers — abstracts alone are sufficient.** All 3 landmark papers
  (1987, 1995, 1997) were from subscription journals (Int J Gynecol
  Pathol, J Nucl Med, Gynecol Oncol) with no PMC copies, no OA, and no
  retrievable full text. This is the first profile with 0% full-text
  retrieval at the key-paper-ingestion level. The PubMed/EPMC
  abstracts (986–1,817 chars) were sufficient for profile grounding:
  the abstracts contained trial design (dose, patient count,
  endpoints), key findings (MTD, response rates, HAMA rate), and
  safety data (toxicity types). The profile's fields 2, 3, 6, and 8
  were adequately filled from abstract content alone. **Pre-2000
  papers from subscription journals are almost never in PMC** —
  Europe PMC's backfile coverage starts around 2000–2002 for most
  publishers. When profiling targets whose landmark papers are
  pre-2000, expect 0% full-text retrieval and proceed directly to
  abstract-only after the EPMC gate. Do NOT spend time on jina/Wayback
  for pre-2000 papers unless the EPMC gate shows inPMC=Y.

  (5) **HighWire journal pages via jina reader return navigation
  chrome only.** PMID 7699446 (J Nucl Med, 1995) had a HighWire
  "free resource" LinkOut URL. The jina reader proxy retrieved 34KB
  of content, but it was entirely navigation chrome, cookie consent
  banners, author lookup links, and "Cited By" sections — NOT the
  article body. The actual abstract text ("CC49 is a murine
  monoclonal antibody...") was not present in the jina output despite
  the 34KB size. This is a new publisher pattern: HighWire-hosted
  journals (jnm.snmjournals.org, possibly others) return
  article-landing-page chrome via jina, not article body text. The
  34KB size passes the standard Branch 1d size check (>3K chars) but
  contains zero usable body content. When a HighWire journal
  returns >20KB via jina but the abstract text from PubMed is NOT
  found within the jina output (grep for a distinctive abstract
  phrase), tag abstract-only — the jina output is nav chrome, not
  article body.

  (TAG-72 profile, ~25K chars, 3 papers ingested (3/3 abstract-only),
  3 unique PMIDs cited, working-docs/hitlist-profiles/tag-72.md.)

- **2026-08-17 — Nav1.9/SCN11A key-paper-ingestion profile
  observations.** Forty-sixth level-2 profile (preclinical tier,
  neuroscience — voltage-gated sodium channel). Nav1.9 is a TTX-
  resistant sodium channel preferentially expressed in peripheral
  nociceptive neurons; the first profiled ion channel target and the
  first where the entire therapeutic landscape is small-molecule
  (zero therapeutic antibodies in development). 8 papers ingested
  (3/8 full text: Huang 2017 JCI via EPMC PDF, Dib-Hajj 2015 Nat Rev
  Neurosci + Leipold 2013 Nat Genet via jina; 5/8 abstract-only).
  ~27K chars, 57 PMID citations. See
  `references/nav1-9-profile-observations.md` for full detail.
  Key new patterns:

  (1) **Ion channel target with no antibody pipeline — small-molecule-
  dominated landscape.** The entire Nav1.9 therapeutic landscape is
  small-molecule channel blockers (ANP-230 pan-Nav blocker, PMID
  40633498; suzetrigine Nav1.8 selective FDA-approved, PMID 40601424).
  The only antibodies are research tools (polyclonal peptide antibodies
  for immunolocalization, PMID 10683857). For field 4, explicitly state
  "No therapeutic antibodies in development." For field 11, the
  differentiation framing is "why would an antibody be better than small
  molecules" — answer: inherent subtype selectivity, long half-life,
  peripheral restriction (no BBB crossing). The VSD-targeting antibody
  approach validated for Nav1.7 (Lee et al. 2014, Cell) is the
  proof-of-concept but has not been extended to Nav1.9. Generalizes to
  any ion channel target with exclusively small-molecule therapeutics.

  (2) **Biphasic dose-response from human genetics — U-shaped
  excitability curve.** Nav1.9 gain-of-function mutations cause BOTH
  pain (familial episodic pain, painful neuropathy) AND insensitivity
  to pain (congenital insensitivity to pain), depending on the
  magnitude of the functional effect. Small depolarizations (~4-6 mV)
  cause hyperexcitability/pain; large depolarizations (~8-12 mV) cause
  inactivation of other NaV channels and hypoexcitability/insensitivity
  to pain (PMID 28530638). For field 6, this is a distinct failure class
  — "mechanism-of-action non-linearity." For field 11, a state-dependent
  antibody targeting the inactivated conformation could preferentially
  block hyperactive channels while sparing resting-state channels,
  widening the therapeutic index. Generalizes to any target with
  non-monotonic dose-response.

  (3) **Poor human-mouse ortholog conservation (73% identity).** Human
  and mouse Nav1.9 share only ~73% amino acid identity — notably lower
  than other mammalian sodium channel orthologs (>90% for Nav1.1-1.8).
  Functional differences between human L811P and mouse L799P orthologous
  mutations confounded direct comparisons (PMID 28530638). For antibody
  development, the extracellular loops (antibody-accessible regions) are
  the LEAST conserved parts of the protein — epitope conservation between
  human and rodent/cyno needs careful evaluation. Generalizes to any
  target with unusually low cross-species conservation where the
  antibody-accessible regions are the most variable domains.

  (4) **Nature Reviews articles via jina return references list, not
  body text.** The Dib-Hajj 2015 Nat Rev Neurosci review (PMID 26243570)
  was fetched via jina (42K chars) but the content was the numbered
  references list, not the review body text (paywalled). The reference
  list from a high-quality review is still valuable — it identifies the
  landmark papers the review authors considered most important. For
  target profiling, extract the reference list as a bibliography guide
  and rely on PubMed abstracts for actual content.

  (5) **PubMed DOI field errors — cross-check DOI against journal.**
  PMID 28530638 (Huang 2017, JCI) had a PubMed DOI field showing
  "10.1038/nprot.2009.90" (Nature Protocols) instead of "10.1172/JCI92373".
  EPMC retrieval via PMID worked correctly despite the wrong DOI. Always
  cross-check the DOI prefix against the publisher; use PMID for retrieval
  when the DOI looks suspicious.

  (6) **PubMed search strategy for ion channel targets — search by
  function, not by "antibody."** For ion channel targets with no
  antibody pipeline, search by function ("pain", "inflammatory",
  "channel blocker") rather than by "antibody" — the literature is
  about biology and small-molecule pharmacology. The broader functional
  query `sodium channel Nav1.9 pain[tiab]` (15 results) was far more
  productive than `Nav1.9 antibody[tiab]` (3 results). Also search for
  historical names (NaN for Nav1.9).

  (Nav1.9/SCN11A profile, ~27K chars, 8 papers ingested (3/8 full text,
  5/8 abstract-only), 57 PMID citations,
  working-docs/hitlist-profiles/nav1-9.md.)

- **2026-08-17 — Nav1.8/SCN10A key-paper-ingestion profile
  observations.** Forty-seventh level-2 profile (preclinical tier,
  neuroscience — voltage-gated sodium channel). Nav1.8 is the
  TTX-resistant, high-threshold nociceptor sodium channel encoded by
  SCN10A (UniProt Q9Y5Y9) — the first Nav subtype with an FDA-approved
  selective inhibitor (suzetrigine/VX-548, 30 Jan 2025). Like Nav1.9,
  zero therapeutic antibodies in development; the entire pipeline is
  small-molecule. 5 papers ingested (5/5 full text via Europe PMC
  fullTextXML — 100% retrieval rate). ~31K chars, 14 PMID citations.
  Key new patterns (distinct from the Nav1.9 observations):

  (1) **Europe PMC fullTextXML is the highest-yield full-text source
  for recent (post-2024) pain/neuroscience papers — 100% retrieval.**
  All 5 landmark papers (suzetrigine Phase 3 RCTs, pharmacology,
  Nav1.8/Nav1.7 interplay, FEPS genetics, human DRG neuron modulation)
  were retrieved as full XML body text via
  `europepmc.org/webservices/rest/<PMCID>/fullTextXML` (50–85K chars
  each after tag stripping). This contrasts with the Nav1.9 profile
  (3/8 via jina, 5/8 abstract-only) and earlier cardiovascular profiles
  (14–100% via mixed sources). The pattern: recent neuroscience/pain
  papers from Anesthesiology, Pain Ther, J Gen Physiol, Int J Mol Sci,
  and PNAS are overwhelmingly open-access in Europe PMC with valid
  PMC IDs and downloadable XML. For neuroscience target profiling,
  **try EPMC fullTextXML first for every paper with a PMCID** — it
  outperforms jina (which returns landing-page chrome for many
  journals) and avoids the publisher-block rabbit holes. The retrieval
  is a simple `urllib.request` to the fullTextXML endpoint; parse with
  regex tag-stripping (replace block tags with newlines, strip
  remaining tags, decode entities). Generalizes to any recent
  (post-2020) biomedical OA journal mix.

  (2) **On-target efficacy ceiling via paralog redundancy — distinct
  from the Nav1.9 U-shaped dose-response.** Even at concentrations
  25–250× the Kd, suzetrigine does not fully block repetitive firing in
  human DRG neurons — 14/15 neurons still fired ≥1 AP at 100 nM
  VX-548, and some fired multiple spikes (PMID 40424150). Two reasons:
  (a) human nociceptors express very large Nav1.8 currents so even
  >96% inhibition leaves nA-level residual current; (b) Nav1.7 current
  dominates the first spike and contributes to later spikes. This is a
  NEW failure-mode class — **paralog redundancy** — where a sibling
  channel (Nav1.7) covers the function the inhibited channel (Nav1.8)
  can no longer perform. It is mechanistically DISTINCT from the
  Nav1.9 biphasic observation (non-monotonic dose-response of the SAME
  channel). For field 6, this means a single-paralog antibody may have
  an intrinsic efficacy ceiling that no epitope, format, or dosing can
  overcome — the differentiation path is a **bispecific (Nav1.8 +
  Nav1.7) antibody** that blocks both paralogs. Generalizes to any
  multi-paralog target family where siblings are co-expressed and
  functionally redundant (Nav1.7/1.8/1.9 in nociceptors; EGFR/HER2/HER3
  in cancer; TNF/TNFβ in inflammation).

  (3) **Counterintuitive enhancement of excitability from partial
  Nav1.8 blockade.** Inhibiting Nav1.8 channels generally REDUCED the
  refractory period in 11/14 human DRG neurons — the smaller, narrower
  action potential activates K+ channels less completely, weakening the
  afterhyperpolarization — and in 5/21 neurons, maximum firing actually
  INCREASED (PMID 40424150). This is a paradoxical on-target effect
  unique to ion-channel targets: partial blockade can sometimes enhance
  the very excitability the drug/antibody is meant to suppress. For
  field 6 (failure modes), this is a distinct class — "paradoxical
  partial-blockade enhancement" — and for a long-acting antibody with
  less titratability than an oral small molecule, the risk is
  amplified (the effect persists for weeks, not hours). For field 11,
  a conformation-selective (closed-state) antibody that achieves near-
  complete (>99%) blockade would avoid this, whereas a partial blocker
  could worsen pain in a subset of neurons. Generalizes to any ion
  channel where the action-potential shape feeds back onto K+ channel
  activation.

  (4) **Rodent→human translational gap for ion-channel efficacy.**
  Mouse and rat DRG neurons depend on Nav1.8 for ~80% of the AP
  upstroke current, whereas human DRG neurons rely more on Nav1.7 for
  the initial upstroke (Nav1.8 contributes mainly to the peak and
  shoulder) (PMID 40424150). This means rodent pain models
  **overestimate** the efficacy of Nav1.8 blockade — a preclinical
  antibody that looks highly efficacious in mouse/rat models may
  translate to only partial efficacy in humans. This is DIFFERENT from
  the Nav1.9 cross-species observation (which was about epitope
  conservation and sequence identity). For field 2 (species cross-
  reactivity) and field 7 (assay systems), the rodent→human efficacy
  gap must be stated explicitly, and **primary human DRG neuron
  electrophysiology** (current clamp at 37°C) should be the primary
  preclinical readout for ion-channel antibody programs, not rodent
  behavioral pain models. Generalizes to any ion-channel target where
  the relative contribution of the target vs. its paralogs differs
  between species.

  (5) **"Neutralizing antibody" redefined for ion channels.** For
  classical antibody targets (cytokines, receptors), "neutralizing"
  means blocking ligand-receptor binding or triggering cell depletion.
  For an ion channel, "neutralizing" means **blocking ion conductance
  or locking the channel in a non-conducting conformation** —
  functionally equivalent to the small molecule's mechanism
  (suzetrigine stabilizes the closed state via VSD2; a pore-vestibule
  antibody would block conductance directly). For field 5 (epitope
  landscape), the most attractive antibody epitope on Nav1.8 is the
  **VSD2 S3–S4 extracellular loop** containing the unique "KKGS" motif
  (the suzetrigine binding site, absent from other human Nav subtypes)
  — an antibody binding this loop and allosterically restricting S4
  movement would be functionally neutralizing via closed-state
  stabilization, mimicking the drug without occluding the pore. A
  conformation-selective (closed-state) antibody is the ion-channel
  analogue of a "state-dependent" small molecule. For field 11, this
  reframes the differentiation: the antibody's value is not longer
  half-life alone, but achieving a mechanism (closed-state
  stabilization) that small molecules achieve transiently, sustained
  over weeks. Generalizes to any ion-channel antibody target where
  the drug binding site is an extracellular VSD loop (Nav1.7, Nav1.8,
  Nav1.9 all have VSD-targeted small molecules).

  (Nav1.8/SCN10A profile, ~31K chars, 5 papers ingested (5/5 full text
  via Europe PMC fullTextXML), 14 PMID citations,
  working-docs/hitlist-profiles/nav1-8.md.)

- **2026-08-17 — BDKRB2 (Bradykinin B2 Receptor) key-paper-ingestion
  profile observations.** Forty-eighth level-2 profile (preclinical
  tier, neuroscience — class A GPCR). B2R is the constitutive receptor
  for bradykinin; icatibant (peptide B2R antagonist) is approved for
  hereditary angioedema; no therapeutic antibodies exist. 19 papers
  reviewed (2 full-text via PMC OA XML, 17 abstract-level). ~37K chars,
  61 PMID citations. See
  `references/bdkrb2-profile-observations.md` for full detail.
  Key new patterns:

  (1) **UniProt REST API and PDB REST API as primary sources for
  fields 1 and 9.** `rest.uniprot.org/uniprotkb/<accession>.txt` returns
  flat-text annotation covering MW, topology domains (extracellular/
  cytoplasmic residue ranges), transmembrane helices, glycosylation
  sites, disulfide bonds, PTMs, alternative splicing, PDB
  cross-references, and keywords — all directly citable into the
  profile without literature retrieval. `data.rcsb.org/rest/v1/core/
  entry/<PDB_ID>` returns structure metadata (method, resolution,
  citation PMID). The UniProt → PDB → PubMed-title-search chain
  reliably finds structure papers that keyword searches miss. These
  APIs are fast, reliable, and parser-friendly (plain text / JSON).
  Add them to the standard profiling workflow before PubMed searching.

  (2) **GPCR with approved peptide antagonist, zero antibodies.**
  B2R has an approved peptide (icatibant) but zero therapeutic
  antibodies — PubMed searches for "bradykinin B2 antibody"[tiab] and
  "BDKRB2 antibody"[tiab] both returned 0. This extends the C5aR1
  pattern (approved small molecule, open antibody space) to peptides:
  the peptide validates the target clinically, the antibody space is
  completely open. The differentiation framing is "why antibody vs
  peptide" (half-life, chronic dosing, prophylactic use).

  (3) **Dual-direction GPCR modulation — antagonist AND agonist
  clinical-stage drugs.** B2R is the first profiled GPCR with BOTH an
  approved antagonist (icatibant for HAE) AND a clinical-stage agonist
  (labradimil for BBB disruption in glioma). Field 10 must list both
  modalities; field 11 must specify which direction the antibody takes
  and address the specific competitor in that modality. Agonist
  antibodies against GPCRs are technically challenging and carry
  constitutive-activation risks.

  (4) **BBB disruption as both opportunity and risk for neuroscience
  GPCR targets.** B2R agonism opens the BBB (drug delivery), B2R
  antagonism protects the BBB (stroke/TBI therapy). Field 3 lists both
  disease contexts; field 8 notes that a B2R antibody's effect on BBB
  integrity is a safety concern regardless of direction; field 11
  proposes a BBB-shuttle bispecific (anti-B2R + anti-TfR) for CNS
  penetration — a format differentiation unique to neuroscience targets.

  (BDKRB2 profile, ~37K chars, 19 papers reviewed (2 full-text, 17
  abstract-level), 61 PMID citations,
  working-docs/hitlist-profiles/bradykinin-b2.md.)

- **2026-08-17 — TrkB/NTRK2 key-paper-ingestion profile
  observations.** Forty-eighth level-2 profile (preclinical tier,
  neuroscience — AD/PD/obesity/cancer). TrkB is the high-affinity
  receptor for BDNF, a receptor tyrosine kinase expressed on CNS
  neurons. This is the **first profile where BBB penetration is the
  dominant challenge** and the **first neuroscience target with both
  agonist and antagonist antibody approaches documented**. 5 papers
  ingested (5/5 full text: 3 PMC XML OA, 1 EPMC PDF, 1 publisher-jina).
  100% retrieval rate. ~41K chars, 13 unique PMIDs cited. See
  `references/trkb-profile-observations.md` for full observations.
  Key new patterns:

  (1) **BBB penetration as the dominant, format-level failure mode for
  CNS antibody targets.** Unmodified TrkB agonist antibodies achieve
  only ~0.1-0.6% tissue-to-serum ratio in brain — insufficient for
  target engagement. The TXB4 VNAR-TfR1 brain shuttle (Ossianix)
  solved this: 12-fold higher brain concentrations (4.7 nM) and
  complete neuroprotection in 6-OHDA PD model. AS86 achieved marginal
  brain levels (~1 nM at 1.5 mg/kg IV) by exploiting the "leaky BBB"
  in AD pathology. For field 6, BBB penetration failure is a
  format-level, not target-level failure — it affects every antibody
  against a CNS target regardless of epitope or mechanism. For field
  11, the BBB shuttle approach (TfR1, IGF1R, VNAR, focused ultrasound)
  is the primary differentiation axis for CNS antibody therapeutics.
  Generalizes to all brain-targeted antibodies (anti-Aβ, anti-tau,
  anti-α-synuclein). Always document which BBB penetration strategies
  have been attempted and their outcomes for future CNS target
  profiles. (PMID 35890231, PMID 32550908, PMID 23700410.)

  (2) **Species-dependent paradoxical pharmacology — the NHP
  translational trap.** TAM-163 (humanized 29D7) causes weight LOSS
  in rodents (20% in mice, 12% in rats) but weight GAIN in NHPs (up
  to 35% in rhesus monkeys) with appetite stimulation — the direction
  of the pharmacological effect REVERSES between species. Not
  explained by differential exposure, brain penetration, or binding
  affinity. The "dual role" hypothesis: peripheral/CVO TrkB activation
  stimulates appetite while central activation suppresses it. This is
  a new failure-mode class — the most severe species-dependent
  translation failure observed in the profile corpus (direction
  reversal, not just quantitative difference). For field 6, rodent
  efficacy data cannot predict primate outcomes for TrkB agonist
  antibodies. Generalizable to any CNS target with species-different
  metabolic/appetite circuitry. (PMID 23700410.)

  (3) **Dual agonist + antagonist antibody approaches on a single
  neuroscience target.** TrkB is the first neuroscience target with
  both directions documented — extending the IL-15 dual-directional
  pattern to neuroscience. Agonist antibodies (29D7 → TAM-163, AS86,
  TXB4-TrkB) for neurodegeneration/repair; antagonist antibody
  (TrkB-IgL 5.11) for cancer/pain. The two directions have completely
  different mechanisms, indications, safety profiles, and BBB
  requirements. For orchestrators: when delegating a neuroscience
  receptor target, check if both agonist and antagonist antibody
  approaches exist — if so, instruct the subagent to cover both
  directions. (PMID 39247456, PMID 32550908, PMID 35890231.)

  (4) **Partial agonism as a deliberate safety design feature for
  chronic CNS antibody therapy.** TAM-163 is a partial TrkB agonist
  (lower maximal efficacy than BDNF) — likely a deliberate choice to
  limit receptor overactivation during chronic dosing. Combined with
  LALA Fc mutations (attenuated effector function), this is a two-layer
  safety design. For field 11, partial agonism is a format
  differentiation strategy for chronic CNS therapy. Generalizes to any
  receptor-targeting agonist antibody requiring chronic dosing (TrkA,
  TrkC, RET, other neurotrophin receptors). (PMID 23700410, PMID
  35890231.)

  (5) **IgM isotype as a development bottleneck for antagonist
  antibodies.** The only published neutralizing anti-TrkB antibody
  (TrkB-IgL 5.11) is IgM — therapeutically impractical (short
  half-life, poor tissue penetration, difficult to humanize). The
  IgG1 clones from the same campaign showed less consistent activity.
  Generalizable: the most functionally potent clone from hybridoma
  screening may not be in the therapeutically optimal isotype. For
  field 6, this is a format failure. For field 11, de novo IgG1
  discovery against the same epitope is the primary white space.
  (PMID 39247456.)

  (6) **Stage-dependent efficacy ceiling for synaptic repair
  antibodies.** AS86 was effective in APP/PS1 AD mice at early/mid-
  stage disease (6-month treatment, age 11 months) but ineffective at
  advanced stage (9-month treatment, age 14 months) — despite continued
  synaptic marker improvement. The mechanism (synaptic repair)
  requires viable neurons and fails when neuronal loss overwhelms.
  For field 6, the failure is timing of intervention, not the
  antibody or target. For field 11, biomarker-defined early
  intervention (prodromal AD, early PD) is the differentiation path.
  Generalizes to any neuroprotective/neuroregenerative antibody target.
  (PMID 32550908.)

  (7) **PubMed search term adaptation for receptor agonist + antagonist
  targets.** `"NTRK2 antibody therapeutic"[tiab]` returned zero —
  gene symbols are rarely used in antibody therapeutic papers.
  `"TrkB agonist antibody"[tiab]` was the highest-yield query.
  `"anti-TrkB"[tiab] AND antibody[tiab]` found antagonist antibodies.
  For orchestrators: provide search templates covering both agonist
  and antagonist directions plus gene-symbol fallback for receptor
  targets with dual-directional antibody approaches. (TrkB profile.)

- **2026-08-17 — Clusterin/CLU key-paper-ingestion profile
  observations.** Forty-ninth level-2 profile (preclinical tier,
  neuroscience — AD/PD/ALS/cancer). CLU (apolipoprotein J) is a secreted
  chaperone glycoprotein and major AD GWAS risk gene. 5 papers ingested
  (5/5 full text: 3 PMC XML, 1 publisher-jina, 1 Wayback). 100%
  retrieval rate. ~28K chars, 6 PMIDs cited. See
  `references/clusterin-profile-observations.md` for full detail.
  Key new patterns:

  (1) **Opposite therapeutic direction across disease areas — the
  "double-edged sword" pattern.** CLU is the first profiled target
  where the neuroscience direction (enhancement) is the OPPOSITE of
  the oncology direction (inhibition). In cancer, sCLU is cytoprotective
  (Ku70-Bax stabilization, therapy resistance) and CLU inhibition
  (custirsen antisense, AB-16B5 antibody) is the strategy. In AD, CLU
  is neuroprotective (Aβ chaperone, NF-κB suppression, complement
  inhibition) and CLU loss (GWAS risk allele) causes neuroinflammation
  and synapse loss — the strategy is enhancement. This is NOT
  dual-directional targeting (FasL, IL-15, TrkB) where the same
  antibody direction serves different diseases; here the target's
  biology is opposite in different tissues. For field 6, the critical
  failure mode is naively translating the oncology inhibition paradigm
  to neuroscience — an inhibitory anti-CLU antibody would worsen AD.
  For field 11, a CLU-enhancing antibody or CLU-Fc fusion is a blue
  ocean (no one is developing CLU enhancers for AD), but carries the
  risk that chronically elevating CLU could promote cancer. Generalizes
  to any target with tissue-specific opposite biology.

  (2) **GWAS risk allele direction directly informs antibody therapeutic
  direction.** CLU is the first neuroscience target where the GWAS
  risk allele direction (low CLU = risk) directly determines the
  antibody strategy (enhancement, not inhibition). Risk allele →
  reduced CLU → worse cognition; protective allele → increased CLU →
  preserved cognition (PMID 40311610). CLU deficiency (CRISPR KO) →
  NF-κB activation, C3/C1q upregulation, microglial synapse phagocytosis
  (PMID 40311610). For field 3, when GWAS risk allele direction is known,
  state the implied therapeutic direction: risk = loss-of-function →
  enhancement; risk = gain-of-function → inhibition. This is a direct,
  citable link from human genetics to antibody design.

  (3) **PubMed metadata DOI mismatch pitfall.** PMID 40311610 (Neuron
  2025) had a mismatched DOI in PubMed efetch XML — the DOI pointed to
  a Bioinformatics article, not the Neuron paper. `fetch_fulltext.py`
  resolved correctly via PMID (not DOI). Rule: always use PMID as the
  primary identifier for retrieval; if using `--doi`, verify the
  retrieved title matches the expected paper before distillation. The
  DOI in PubMed XML can be wrong for recently indexed papers.

  (4) **Contradictory biomarker vs. mechanistic evidence — the
  observational confounding paradox.** The Desikan human biomarker
  study (PMID 24378367) shows elevated CSF CLU + high amyloid = more
  atrophy (suggesting CLU accelerates neurodegeneration), while the
  Lish mechanistic study (PMID 40311610) shows CLU loss is deleterious
  (suggesting CLU is protective). The paradox resolves: the
  observational study measures CLU as a stress-response marker
  (upregulated in response to pathology), while the genetic/mechanistic
  study establishes the causal role (CLU loss worsens disease). For
  field 6, when observational and mechanistic evidence appear
  contradictory, present both and explain the confounding — biomarker
  correlation ≠ causation.

  (5) **Secreted chaperone as antibody target — no surface engagement
  needed.** CLU is the first neuroscience profile where the target is
  entirely extracellular (secreted, in plasma/CSF/interstitium). No
  ADCC/CDC mechanism is possible (target not cell-surface). CLU-Fc
  fusion or recombinant CLU supplementation is a viable alternative
  modality (analogous to enzyme replacement). Epitope landscape is
  conformation-dependent (lipidated vs. lipid-free CLU have different
  epitope exposure — TREM2 binds only lipidated CLU).

  (Clusterin/CLU profile, ~28K chars, 5 papers ingested (5/5 full text),
  6 PMIDs cited, working-docs/hitlist-profiles/clusterin.md.)

  (TrkB/NTRK2 profile, ~41K chars, 5 papers ingested (5/5 full text),
  13 PMID citations, working-docs/hitlist-profiles/trkb.md.)

- **2026-08-17 — tPA (Tissue Plasminogen Activator, PLAT) key-paper-ingestion
  profile observations.** Forty-plus level-2 profile (preclinical tier,
  cardiovascular — thrombolysis/stroke). tPA is the **first profiled target
  where the approved drug is a recombinant form of the target protein
  itself** (alteplase = recombinant tPA) — antibodies aim to *improve on*
  the approved protein, not fill a therapeutic gap. It is also the **first
  target with two mechanistically opposite antibody strategies**: (1)
  antibody-*targeted* thrombolysis (conjugate/bispecific MAbs that
  *potentiate* tPA by localizing it to the clot — 59D8, F36.23) and (2)
  antibody-*blockade* of tPA's harmful non-thrombolytic signaling
  (anti-tPA/NMDAR Glunomab, anti-LRP1). 5 key papers ingested (2/5 full
  text: 1 EPMC PDF render for 1987 PNAS, 1 PMC XML OA for 2014 review;
  3/5 abstract-only — NEJM, Circulation, Wiley). 40% full-text retrieval.
  ~43K chars, 10 PMIDs cited. See
  `references/tpa-profile-observations.md` for full observations.
  Key new patterns:

  (1) **Function-selective antibody — a third mechanism class.** Glunomab
  (anti-tPA/NMDAR) selectively blocks tPA's deleterious side-effect pathway
  (BBB breakdown, neuroinflammation via NMDAR/LRP1 signaling) while
  preserving its desired therapeutic activity (catalytic thrombolysis).
  This is distinct from neutralizing antibodies (block primary function)
  and potentiating antibodies (enhance/localize function). For fields 4/5,
  describe *which function is blocked and which is preserved*, not just
  "neutralizing/non-neutralizing." The epitope maps to the signaling
  interface (growth-factor domain), not the catalytic site. Generalizes to
  any target with separable beneficial and harmful functions.

  (2) **Dual-antibody-strategy target — two opposite directions, both
  valid for the same disease.** Unlike clusterin's "double-edged sword"
  (opposite biology in different tissues, one direction per disease), tPA
  has two antibody strategies moving in opposite mechanistic directions
  that *both* apply to stroke and could be combined in one bispecific
  (clot-targeting + signaling blockade). For field 10, the competitive
  landscape must include recombinant-protein competitors (alteplase,
  tenecteplase, reteplase) alongside the antibody pipeline (all
  preclinical) — the antibody competes with an approved protein drug and
  with mechanical thrombectomy, not with another antibody.

  (3) **Approved recombinant protein as the benchmark.** Field 3 must
  separate "evidence for the target" (strong — approved drug) from
  "evidence for an antibody against the target" (weak — all preclinical).
  Field 6's dominant failure mode is *translation*, not biology: 40 years
  of preclinical proof-of-concept (1987→2024) has not produced a clinical
  antibody candidate because the approved recombinant protein + thrombectomy
  already address much of the need. Generalizes to any target where a
  recombinant protein is already the approved drug and antibodies are the
  second-generation improvement.

  (4) **PubMed search for dual-strategy targets: run both drug-focused
  and antibody-focused queries.** The antibody-focused [tiab] queries
  missed the NINDS clinical-trial evidence (PMID 7477192) and the
  tPA–NMDAR mechanism papers. Adding `"NINDS" rt-PA stroke trial` and
  `"tissue plasminogen activator" neurotoxicity NMDA receptor` queries was
  necessary to capture the clinical-evidence anchor and the
  signaling-blockade rationale. For targets with an approved drug AND an
  emerging antibody strategy, run both drug-focused and antibody-focused
  queries; antibody queries alone will miss the clinical evidence.

  (5) **EPMC PDF render works for 1980s in-PMC papers.** PMID 3118374
  (Runge 1987, PNAS) retrieved via EPMC PDF render (21.9K chars) despite
  inPMC=Y, isOpenAccess=N — the PMC XML branch returned no <body>
  (metadata-only). Confirms fetch_fulltext.py branch 1b (EPMC PDF) is
  valuable for older in-PMC-but-not-OA papers. A good PMC-OA review
  (PMID 25780787, 30K chars) can substitute for multiple paywalled primary
  papers when it comprehensively cites and summarizes them.

  (tPA/PLAT profile, ~43K chars, 10 papers ingested (2/10 full text,
  8/10 abstract-only), 10 unique PMIDs cited,
  working-docs/hitlist-profiles/tpa.md.)

### Ephrin-B2 observations (transmembrane ligand + bidirectional signaling + preclinical neuroscience)

First preclinical-neuroscience profile of a **transmembrane ligand**
(ephrin-B2/EFNB2, class-B ephrin). 5 papers ingested (3/5 PMC XML full
text, 1/5 publisher-jina, 1/5 front-matter-only PMC). ~40K chars, 11
PMIDs cited. See `references/ephrin-b2-profile-observations.md` for
full observations. Key new patterns:

(1) **Bidirectional-signaling transmembrane ligand — agonism vs
antagonism reverses by disease.** Ephrin-B2 is a transmembrane ligand
with both forward signaling (into the EphB-receptor cell) and reverse
signaling (into the ephrin-B2-expressing cell via its C-terminal tail).
The therapeutic direction REVERSES by indication: blockade is
therapeutic in ALS (astrocyte ephrin-B2 is pathogenic), spinal cord
injury (glial scar), and neuropathic pain (nociceptor ephrin-B2 drives
central sensitization); activation/agonism is therapeutic in
anti-NMDAR encephalitis (stabilizes EphB2-NMDAR disrupted by patient
antibodies) and ischemic stroke (promotes angiogenesis). This extends
the dual-direction targeting pattern (FasL, TrkB, BDKRB2) to a
*transmembrane ligand* — the directionality analysis in fields 6 and
11 must state which direction applies to which disease and why. No
therapeutic antibody has been engineered for EITHER direction despite
strong preclinical mechanism — the agonist antibody for
encephalitis/stroke recovery is the highest-priority unexplored space.

(2) **Indication-context-dominated PubMed searches — pivot to
indication-specific queries.** Ephrin-B2 is ALSO the cell-entry
receptor for henipaviruses (Nipah/Hendra). The initial
`"ephrin-B2 antibody[tiab]"` and `"EFNB2 antibody[tiab]"` queries
returned mostly henipavirus virology (viral G-protein antibodies,
neutralization assays, vaccines), not neuroscience therapeutic
antibody work. After the generic queries return context-dominated
results, pivot to queries combining the target name with
indication-specific biology terms (`"ephrin-B2 synaptic plasticity"`,
`"ephrin-B2 neurodegeneration"`, `"ephrin-B2 spinal cord"`). These
surfaced the landmark neuroscience papers the generic "antibody"
queries missed. Generalizes to any target whose name is shared with a
dominant non-target context (viral receptor, oncology antigen,
developmental marker). Distinct from the "topic-divided search"
pattern (multiple roles of the SAME target) — here an unrelated field
dominates and drowns out the indication of interest.

(3) **Species cross-reactivity computation — naive alignment gives
wildly wrong identity.** A naive position-by-position zip of UniProt
`SQ` blocks gave 9.9% identity for human/mouse EFNB2 — obviously wrong.
Cause: the mouse sequence has a 3-residue N-terminal extension
relative to human; without an offset search, every position is
misaligned. Fix: slide one sequence against the other over ±10
residues, score matches at each offset, take the best. With the
offset applied, human/mouse EFNB2 showed 96.1% identity (97.4% in the
mature extracellular region). Always compute species cross-reactivity
with an offset search, not a naive zip — N-terminal signal-peptide
length differences are common across orthologs and corrupt a
position-by-position comparison.

(4) **UniProt MUTAGEN entries as epitope leads for field 5.** The
UniProt `.txt` flat-text format includes `FT MUTAGEN` entries
identifying functionally critical residues. For EFNB2, `MUTAGEN
121..122 /note="LW->YM: Complete loss of Nipah protein G binding"`
identified the LW motif as a functionally critical surface whose
mutation abolishes viral/receptor binding — a candidate functional
epitope for an antibody that could block pathogenic interactions while
sparing physiological EphB2-stabilizing interactions. When parsing
UniProt `.txt` for fields 1/9, also scan `FT MUTAGEN` for residues
whose mutation abolishes a relevant interaction — these are natural
epitope leads for field 5, more likely to be functionally neutralizing
than an arbitrary surface.

(Ephrin-B2/EFNB2 profile, ~40K chars, 5 papers ingested, 11 PMIDs
cited, working-docs/hitlist-profiles/ephrin-b2.md.)

### IGF-1 observations (secreted growth factor + cardiovascular tier + dual-ligand pipeline + UniProt structured data)

IGF-1 (Insulin-like Growth Factor 1, IGF1) is the **first cardiovascular-tier
profile of a secreted growth factor** — a 7.6-kDa circulating peptide with a
dual IGF-1/IGF-2 antibody pipeline developed entirely for oncology, not
cardiology. Built via delegated subagent using the lightweight retrieval
pipeline (direct PubMed E-utilities, no paper-ingest scripts). 8 search
queries, 12 abstracts fetched, UniProt P05019 flat-text parsed for
structural data. Abstract-only ingestion. ~59K chars, 25 unique PMIDs
cited. See `references/igf-1-profile-observations.md` for full observations.
Key new patterns:

(1) **UniProt flat-text `.txt` as a structured-data source beyond identity
verification.** The UniProt `.txt` format (`curl -sL 'https://www.uniprot.org/uniprot/<ID>.txt'`)
contains `FT SIGNAL`/`FT PROPEP`/`FT CHAIN` (mature protein boundaries),
`FT REGION` (domain architecture with notes), `DR PDB` (all PDB structures
with method, resolution, chain mapping), `CC -!- FUNCTION` (mechanism with
inline PMIDs), `CC -!- DISEASE` (MIM-linked disease associations), `CC -!-
SUBUNIT` (complex partners), and `SQ SEQUENCE` (MW). A single fetch +
grep/awk extracts all structured annotations for fields 1, 2, 3, and 9 —
faster and more reliable than manual literature lookup. For every target
profile, fetch the UniProt `.txt` early and use it as the primary
structured-data source. Generalizes the existing "verify UniProt ID" rule
(from the Properdin profile) into a systematic data-extraction step.

(2) **U-shaped dose-response as a partial-neutralization rationale.**
IGF-1 has a U-shaped relationship with cardiovascular mortality — both low
(aging, CVD mortality) and high (acromegaly, cardiac hypertrophy, CVD
mortality) levels increase risk (PMID 18793116, PMID 22491965). Complete
neutralization is a failure mode (deficiency pathology); partial
neutralization (maintaining 50–80% of circulating levels) is the
differentiation strategy. This extends the partial-neutralization pattern
from leptin (PMID 31495688) to the cardiovascular domain. For field 6,
state that complete neutralization is the failure mode. For field 8, the
U-shaped relationship means a narrow therapeutic index — the antibody must
titrate precisely. For field 11, partial neutralization is the
differentiation. Generalizes to any target with a U-shaped disease
relationship (hormones, growth factors, nutrient carriers).

(3) **Integrin co-receptor binding site as a function-selective antibody
epitope.** IGF-1 directly binds integrins (αvβ3, α6β4) at Arg-84/Arg-85,
forming a ternary complex with IGF-1R essential for full signaling (PMID
19578119). An antibody targeting the integrin-binding site would block
integrin-dependent signaling (vascular remodeling, restenosis) while
preserving IGF-1R-mediated cardioprotection. This is the **function-
selective antibody** pattern (analogous to tPA Glunomab, documented in
tPA profile observations) applied to a co-receptor binding site. For field
5, the co-receptor binding motif is a distinct epitope bin separate from
the receptor-binding interface. For field 11, it is the most compelling
unexplored epitope. Generalizes to any growth factor/cytokine that binds
both a signaling receptor AND a co-receptor/adhesion molecule (IGF-1/integrin,
FGF/HSPG, VEGF/αvβ3, CXCL12/ACKR3) — the co-receptor binding site is a
function-selective epitope.

(4) **INN name search in PubMed for clinical-trial antibody discovery.**
Generic `"IGF-1 antibody"[tiab]` queries returned mostly preclinical and
mechanistic papers, missing clinical trial reports. Searching PubMed by
the antibody's INN (`xentuzumab`, `MEDI-573`) was essential — PubMed's
thesaurus auto-translates INNs to supplementary concept terms, surfacing
all clinical and preclinical papers for that antibody. The `translationset`
in the esearch JSON confirms recognition: `{"from":"MEDI-573","to":"\"dusigitumab\"[Supplementary Concept] OR ..."}`.
For any target with known antibody drug candidates, always run INN/code-
name searches alongside generic target-name queries — the clinical evidence
is published under the INN, not the target name.

(IGF-1/IGF1 profile, ~59K chars, 12 papers (abstract-only), 25 unique PMIDs
cited, working-docs/hitlist-profiles/igf-1.md.)

### Alpha2-antiplasmin observations (serpin/fibrinolysis + ClinicalTrials.gov tier recalibration + ortholog PDB lookup)

Fiftieth-level profile (preclinical tier → recalibrated to clinical-trial,
cardiovascular — thrombolysis/VTE/stroke). Alpha2-antiplasmin (SERPINF2) is
the primary inhibitor of plasmin, the key fibrin-degrading enzyme. Built via
delegated subagent using the lightweight retrieval pipeline (direct PubMed
E-utilities + ClinicalTrials.gov API, no paper-ingest scripts). 8 PubMed
queries (all historical name variants), 15+ abstracts fetched, UniProt REST
API parsed for structural data, ClinicalTrials.gov API queried. Abstract-only
ingestion. ~42.5K chars, ~20 PMIDs cited. See
`references/alpha2-antiplasmin-profile-observations.md` for full observations.
Key new patterns:

(1) **ClinicalTrials.gov API v2 as a primary source for clinical-stage
antibody discovery — PubMed alone misses clinical programs.** PubMed
keyword searches found academic preclinical antibodies (RWR, JTPI-1, mAbs
49/70/77, published 1987-1997) but completely missed **TS23**, the sole
clinical-stage anti-α2AP antibody (Phase 1 completed: NCT03001544; Phase 2
ongoing: NCT05408546 / NAIL-IT trial for PE, sponsor: Translational Sciences,
Inc.). TS23 was found only via ClinicalTrials.gov API v2:
`clinicaltrials.gov/api/v2/studies?query.intr=alpha-2-antiplasmin+antibody`.
This extends the 5T4/TPBG observation (ClinicalTrials.gov for clinical-trial-
tier targets) to ALL tiers: even "preclinical" targets may have undisclosed
clinical programs. Small biotechs do not publish clinical results in PubMed.
Always query ClinicalTrials.gov before assigning a tier based on PubMed-only
evidence.

(2) **PDB structure lookup via ortholog UniProt cross-references.** The
human UniProt entry (P08697) had no PDB cross-references. The crystal
structure (PMID 18063751, Law et al 2008 Blood) was known from PubMed, but
the PDB ID was not findable via PubMed, Europe PMC, or direct RCSB/PDBe
search APIs (all returned 404). The PDB ID (**2R9Y**, 2.65 Å, mouse α2AP)
was found by querying UniProt REST API for the *mouse* ortholog
(Q61247, A2AP_MOUSE) and checking its cross-references, which DID contain
the PDB entry. Generalizes: when the human UniProt entry lacks PDB
cross-references but a structure paper exists, query ortholog UniProt
entries (mouse organism_id 10090, rat 10116). Crystal structures are often
solved with mouse/other species proteins but the PDB ID is only linked to
the species-specific UniProt entry.

(3) **Tier recalibration via ClinicalTrials.gov — most dramatic tier shift
in the profile corpus (preclinical → Phase 2).** The target was labeled
"preclinical" based on PubMed evidence of 1980s-1990s academic antibody
work with no PubMed follow-up. ClinicalTrials.gov revealed an active Phase 2
program (TS23, started 2015 Phase 1, entered Phase 2 in 2023). The gap
exists because the developer (Translational Sciences, Inc.) does not publish
in PubMed, and the founder (Dr. Guy Reed) moved from academia to industry.
**Rule:** For any "preclinical" cardiovascular or thrombotic target, run a
ClinicalTrials.gov query before assigning the tier. PubMed-only tier
assignment systematically misses small-biotech clinical programs.

(4) **Thrombus-specificity safety profile — α2AP inactivation without
bleeding.** α2AP inactivation dissolves thrombi *without* fibrinogen
degradation or bleeding, unlike all plasminogen activators (tPA, urokinase,
streptokinase). In PE models, α2AP inactivation was comparable to 3 mg/kg
r-tPA but caused *less* bleeding (P<0.001). For fibrinolytic system targets
(α2AP, PAI-1, TAFI), field 8 must explicitly compare the bleeding profile
to plasminogen activators. The primary safety axis is *thrombus specificity*
(does it cause systemic fibrinogen degradation?), not on-target vs off-target.

(5) **Context-specific on-target toxicity — pulmonary heart failure in AMI.**
Complete α2AP deficiency in mice with experimental AMI caused acute cor
pulmonale via VEGF overrelease (PMID 12239160). This is a disease-context-
specific on-target toxicity not detected in standard toxicology. The NAIL-IT
trial excludes AMI patients. For fibrinolytic targets, field 8 must include
disease-context-specific toxicities beyond standard bleeding risk.

(6) **PubMed search strategy for targets with historical name variants.**
Alpha2-antiplasmin has 4+ literature names. The highest-yield query used the
hyphenated form (`"alpha-2-antiplasmin" antibody[tiab]`, 112 results) which
captured 1980s-1990s landmark papers; the modern non-hyphenated form
(`"alpha2-antiplasmin" antibody[tiab]`, 26 results) captured recent papers.
Gene symbol queries (`SERPINF2 antibody[tiab]`, 2 results) were nearly
useless. For targets with historical name variants (especially pre-2000
targets), search all variants including hyphenated/non-hyphenated forms and
old synonyms.

(Alpha2-antiplasmin/SERPINF2 profile, ~42.5K chars, 15+ papers (abstract-only),
~20 PMIDs cited, working-docs/hitlist-profiles/alpha2-antiplasmin.md.)

- **2026-08-17 — Glucagon/GCG key-paper-ingestion profile observations.**
  Cardiovascular/metabolic target, preclinical tier (though two anti-GCGR
  antibodies reached Phase 1/Phase 2 — see below). Glucagon is a 29-aa secreted
  peptide hormone (preproglucagon, UniProt P01275, 180 aa, ~20.9 kDa) that
  raises blood glucose via hepatic GCGR. 14 key papers reviewed, ~52K chars,
  22 unique PMIDs cited (225 total citations). New observations:

  (1) **Two distinct antibody strategies for a secreted peptide hormone:
  ligand immunoneutralization vs receptor antagonism.** Glucagon is unique
  among profiled targets because two antibody architectures have been
  extensively validated: (a) anti-glucagon ligand antibodies (Glu-mAb, Brand
  et al. 1994, PMID 7851693) that sequester the circulating peptide; (b)
  anti-GCGR receptor antibodies (REGN1193, REMD-477) that block the receptor.
  The ligand approach requires very high binding capacity (Glu-mAb: 40
  nmol/mL, Kd 0.6×10¹¹ L/mol, 4 mL/kg dosing) because the peptide is
  continuously secreted — standard therapeutic antibody doses may be
  insufficient for stoichiometric sequestration. The receptor approach needs
  only receptor occupancy, not ligand stoichiometry, so dosing is more
  practical. **Rule:** For secreted peptide hormone targets (glucagon,
  somatostatin, GLP-1, GIP, etc.), field 4 must distinguish ligand-targeting
  vs receptor-targeting antibodies and note the dosing-capacity implication
  of ligand immunoneutralization. Ligand-targeting antibodies face a
  fundamental pharmacokinetic barrier for continuously secreted peptides.

  (2) **Cross-species conservation as preclinical advantage.** Mature glucagon
  (29 aa) is 100% identical across all mammalian species. GCGR is ~90%
  conserved human-to-mouse. The same Glu-mAb was used in rats and rabbits
  without re-engineering; REGN1193 worked in mice and cynomolgus monkeys;
  REMD-477 went from mice to humans. For fields 2 and 4, note the degree of
  cross-species conservation — 100% peptide identity means the same antibody
  can be used across all preclinical species and directly in humans,
  eliminating the need for species-specific surrogate antibodies. This is
  especially valuable for secreted peptide hormones (glucagon, somatostatin,
  insulin) which are typically ultra-conserved.

  (3) **PubMed E-utilities rate limiting (HTTP 429) with rapid sequential
  queries.** The first esearch batch (5 queries, 4s sleep between calls)
  succeeded cleanly. A second batch of 5 queries ~30s later hit HTTP 429
  (Too Many Requests) on queries 2 and 4, returning empty PMID lists. The
  issue is not the 4s inter-call sleep but the cumulative request rate over
  a short window — NCBI enforces ~3 requests/second sustained, and a burst
  of 10 esearch+efetch calls within ~60s can trigger throttling. **Fix:**
  When doing more than ~5-6 sequential E-utilities calls, increase the sleep
  to 5-6s between calls, or split across two execute_code calls with a
  longer natural gap between them. The efetch batch that ran 3s after the
  rate-limited esearch batch also succeeded — the rate limit clears within
  seconds, not minutes. Do NOT treat a 429 as a permanent block; retry after
  a brief pause.

  (4) **Tier recalibration via ClinicalTrials.gov — repeated pattern.**
  The target was labeled "preclinical" but PubMed searches revealed two
  clinical-stage anti-GCGR antibodies: REGN1193 (Regeneron, Phase 1 in
  healthy volunteers, PMID 28755409) and REMD-477 (REMD Biotherapeutics,
  Phase 2 RCT in T1D, NCT02715193, PMID 29283470). The preclinical label
  was based on the anti-glucagon ligand antibody approach (Glu-mAb, 1990s
  academic work), but the anti-GCGR receptor antibody approach had quietly
  advanced to Phase 2. This is the same pattern seen in the Alpha2-antiplasmin
  profile (preclinical → Phase 2 via ClinicalTrials.gov). **Rule (repeated
  from alpha2-antiplasmin):** For any "preclinical" target, run a
  ClinicalTrials.gov query or search for specific antibody program codes
  (REGN, REMD, etc.) before assigning the tier. PubMed-only tier assignment
  misses small-biotech clinical programs.

  (5) **On-target transaminase elevation as class effect of GCGR blockade.**
  REGN1193 Phase 1 showed small transient ALT/AST elevations (<3× ULN).
  Small-molecule GCGR antagonists from Merck, Pfizer, and Lilly all faced
  the same signal. This is mechanism-based (GCGR blockade disrupts hepatic
  amino acid catabolism, causing hepatic stress), not antibody-specific.
  For field 8, when a target has both antibody and small-molecule
  antagonists in development, check whether the safety signal is shared
  across modalities — a shared signal indicates on-target mechanism-based
  toxicity, while an antibody-only signal suggests Fc or format-related
  issues.

  (6) **No hypoglycemia as a counterintuitive safety advantage.** GCGR
  blockade does not cause hypoglycemia even in normoglycemic animals
  (8-week monkey study, PMID 26020795) or T1D patients (REMD-477 Phase 2,
  PMID 29283470). The body compensates via alternative glucose-maintaining
  mechanisms (ghrelin, amino acid metabolism, PMID 28487437). For field 8,
  for metabolic targets where the mechanism predicts a risk (blocking a
  glucose-raising hormone → hypoglycemia?), always check whether the
  predicted risk materializes in preclinical/clinical data —
  counterintuitive safety findings are important differentiation signals.

(Glucagon/GCG profile, ~52K chars, 14 papers reviewed (abstract-only),
22 unique PMIDs cited, working-docs/hitlist-profiles/glucagon.md. See
references/glucagon-profile-observations.md for detailed session notes.)

### ANP observations (secreted peptide hormone + receptor-targeted PAM antibody + cardiovascular tier + approved-peptide-format failure)

Fifty-first level-2 profile (preclinical tier, cardiovascular —
hypertension/heart failure/atrial fibrillation). ANP (Atrial Natriuretic
Peptide, NPPA) is a 28-amino-acid cardiac hormone secreted by atrial
cardiomyocytes; it signals through GC-A (NPR-A/NPR1), a particulate guanylyl
cyclase receptor, generating cGMP for natriuresis, vasodilation, and RAAS
suppression. Built via delegated subagent using the lightweight retrieval
pipeline (direct PubMed E-utilities, no paper-ingest scripts). 11 PubMed
queries (3 specified + 8 supplementary), 25+ abstracts fetched. Abstract-only
ingestion. ~61K chars, 49 unique PMIDs cited. See
`references/anp-profile-observations.md` for full observations. Key new
patterns:

(1) **Secreted peptide hormone where the therapeutic antibody targets the
*receptor*, not the peptide — the receptor-as-target pattern.** ANP is a
28-aa peptide (~3 kDa) with a plasma half-life of ~2–5 min — too small and
too short-lived to be a practical antibody target for chronic therapy.
Anti-ANP antibodies exist but only as immunoassay/diagnostic reagents
and one nanocarrier-targeting ligand (PMID 34575433). The therapeutic
antibody approach targets the *receptor* (GC-A/NPR-A): the 2026 Nature
Communications paper (PMID 41942428) reported two monoclonal antibodies
(XX16, REGN5308) that are positive allosteric modulators (PAMs) of GC-A,
with cryo-EM structures and in vivo antihypertensive efficacy. The receptor
has a large extracellular domain amenable to antibody binding, unlike the
tiny peptide. For field 1, when the target is a small secreted peptide,
explicitly state whether the antibody approach targets the peptide or the
receptor — and default to the receptor if the peptide is <5 kDa with a
short half-life. For field 4, list receptor-targeted antibodies separately
from peptide-targeted (immunoassay) antibodies. Generalizes to all small
peptide hormones (ANP, BNP, CNP, endothelin, adrenomedullin, relaxin,
ghrelin, GIP, GLP-1, somatostatin, apelin) — the receptor is the antibody-
accessible therapeutic target, not the peptide.

(2) **Positive allosteric modulator (PAM) antibodies as a new mechanism
class — ligand-independent agonist vs ligand-dependent PAM.** The ANP/GC-A
axis is the first profiled target where the antibody mechanism is **positive
allosteric modulation** — the antibody enhances endogenous ligand signaling.
XX16 is a ligand-independent agonist (stabilizes active GC-A dimer without
ANP); REGN5308 is a ligand-dependent PAM (requires ANP for full activation,
increases ANP binding affinity). This is a fourth mechanism class, distinct
from: (a) neutralizing (block primary function), (b) agonist (activate
independently, e.g., TrkB 29D7), (c) function-selective (block one function,
spare another, e.g., tPA Glunomab). PAM antibodies have a unique safety
advantage: ligand-dependent PAMs (REGN5308) preserve physiological feedback
(endogenous ANP release tracks atrial stretch), reducing the risk of
sustained overactivation. For field 4, add a "mechanism class" descriptor:
ligand-independent agonist / ligand-dependent PAM / neutralizing / function-
selective. For field 5, PAM antibody epitopes are *conformational* (receptor
dimerization interface / allosteric site), not linear — the cryo-EM structure
is essential for epitope mapping. For field 11, the ligand-dependent vs
ligand-independent choice is a safety-driven format differentiation.

(3) **Long-acting agonist antibody with non-titratable hypotension risk —
the agonist-format liability.** A monthly agonist antibody against a
vasodilatory pathway (ANP/GC-A) risks sustained, non-titratable hypotension
— the *agonist* analog of the ACE-neutralizing-antibody format liability
(ace.md, antagonist with non-titratable RAAS toxicity). For any agonist
antibody against a vasodilatory/natriuretic pathway, field 8 must flag
non-titratable hypotension as the primary safety liability and field 6 must
list it as the dominant failure-mode class. Mitigation strategies (for
field 11): (a) ligand-dependent PAM design (REGN5308, preserves feedback),
(b) partial agonism (lower maximal efficacy, analogous to TAM-163 partial
TrkB agonism for chronic CNS dosing), (c) conservative dosing with
hypotension monitoring, (d) patient selection (avoid hypovolemic/low-BP
patients). Generalizes to any agonist antibody against a vasodilatory or
blood-pressure-lowering pathway (ANP/GC-A, BNP/GC-A, adrenomedullin/ADM-R,
relaxin/RXFP1, CGRP/RAMP1).

(4) **Approved peptide agonist with no mortality benefit (carperitide) as a
peptide-format failure, while indirect augmentation (sacubitril/valsartan)
succeeded — target valid, format matters.** Carperitide (recombinant ANP,
approved in Japan for acute HF) shows no mortality benefit and possible
harm (PMID 25999241, PMID 39656827, PMID 40922889 meta-analysis) — a
*peptide-format* failure (short half-life requiring continuous IV infusion,
hypotension, renal function decline). Meanwhile, sacubitril/valsartan
(ARNI — neprilysin inhibition augments endogenous ANP/BNP + ARB) is approved
for HFrEF and beneficial in HFpEF (PMID 25176015, PMID 31475794) — proving
the *target* is valid. This extends the tPA "approved recombinant protein
as benchmark" pattern: when a direct peptide agonist fails clinically but
an indirect augmenter succeeds, the target is validated and the format is
the problem — a long-acting antibody PAM (months, not minutes) is the
differentiated opportunity. For field 3, separate "evidence for the target"
(strong — ARNI success) from "evidence for the direct peptide format" (weak
— carperitide failure). For field 6, the failure is format-specific
(short half-life, infusion delivery), not target-specific. Generalizes to
any short-lived peptide hormone where direct replacement failed but
indirect augmentation succeeded.

(5) **PubMed search for receptor-targeted antibodies must include receptor
name, not just peptide name.** Generic `"ANP antibody"[tiab]` and
`"atrial natriuretic peptide antibody"[tiab]` queries returned immunoassay
antibodies (anti-peptide RIA/ELISA) and old mechanistic papers — NOT the
therapeutic anti-receptor (GC-A) antibodies. The landmark anti-GC-A PAM
antibody paper (PMID 41942428, 2026) was found via `"natriuretic peptide
receptor" antibody[tiab]` and `"GC-A antibody"[tiab]` queries, not via
peptide-name queries. For secreted peptide hormones where the antibody
targets the receptor, run receptor-name queries (`"<receptor name>
antibody"[tiab]`, `"<receptor gene symbol> antibody"[tiab]`) alongside
peptide-name queries. The clinical/therapeutic antibody evidence is
published under the receptor name, not the peptide name. Generalizes to
all peptide-hormone targets where the antibody approaches the receptor.

(6) **NPPA loss-of-function mutations cause disease — the therapeutic
direction is agonism, not antagonism, for the general cardiovascular
population.** NPPA mutations (p.I137T, frameshift, p.Arg150Gln) cause
atrial fibrillation and atrial dilated cardiomyopathy (PMID 31034774,
31077706, 40838933); NPPA knockout mice develop hypertension and cardiac
hypertrophy (PMID 23981445). ANP *deficiency* is pathogenic — a neutralizing
(antagonist) anti-ANP or anti-GC-A antibody would worsen hypertension and
AF. The therapeutic direction is *agonism* (GC-A PAM) for cardiovascular
disease. A neutralizing antibody would only be relevant for rare ANP-excess
states (ANP-producing tumors, vasodilatory shock) — a narrow blue ocean.
For field 6, when the target's loss-of-function causes the disease of
interest, the neutralizing-antibody direction is a failure mode, not a
strategy. This is the cardiovascular analog of the clusterin "double-edged
sword" pattern (neuroscience: enhancement, not inhibition, for AD). For field 11,
state the therapeutic direction (agonism vs antagonism) explicitly and flag
the wrong direction as a known risk.

(ANP/NPPA profile, ~61K chars, 25+ papers (abstract-only), 49 unique PMIDs
cited, working-docs/hitlist-profiles/anp.md.)

### CFI observations (complement regulatory enzyme + augmentation-not-blockade + autoantibody precedent + Bruch's membrane barrier)

Complement factor I (CFI, gene CFI, UniProt P05156) is an 88 kDa secreted
serine protease that inactivates C3b/C4b — the **master regulatory enzyme**
of the complement cascade. This is the **first complement regulatory
enzyme (not effector)** profiled (prior complement targets — C5, C5a,
C3aR, C5aR1 — are all effectors or effector receptors where the antibody
blocks the effector). CFI is the first complement target where the
therapeutic direction is AUGMENTATION of a regulator, not blockade of
an effector. 10 papers, abstract-only (lightweight subagent retrieval
via PubMed E-utilities + urllib, no full-text retrieval attempted —
abstracts were 1.1k–2.4k chars, sufficient for level-2 grounding). ~31.5K
chars, 10 unique PMIDs cited. Key new patterns:

- **Complement regulatory enzymes require an augmentation-not-blockade
  framing, distinct from complement effector targets.** For all prior
  complement profiles (C5, C5a, C3aR, C5aR1), the antibody blocks an
  effector to dampen inflammation — the standard antagonist paradigm.
  CFI is an INHIBITOR of complement; a conventional neutralizing
  (antagonist) anti-CFI antibody would phenocopy CFI deficiency
  (uncontrolled complement activation, consumptive C3 deficiency, AMD/
  aHUS/infections) — i.e., it would CAUSE the diseases it is meant to
  treat. The therapeutic direction is therefore agonism/stabilization/
  cofactor-facilitation: an antibody that enhances or protects CFI
  function. This is the complement-specific instance of the
  loss-of-function → agonism pattern (cf. clusterin, ANP, PAI-1
  "inhibit-the-inhibitor"), but it carries a complement-cascade-topology
  framing that generalizes across the complement regulatory class (FI,
  FH, C4BP, CD46/MCP, CD55/DAF, properdin): for any complement
  REGULATOR whose deficiency drives disease, an augmenting antibody is
  correct and a blocking antibody is the failure mode. For field 6,
  state the effector-vs-regulator distinction and the resulting
  direction-of-effect explicitly; for field 11, flag that a blocking
  antibody is a known risk, not a strategy. The clinical-stage CFI
  program (GT005 AAV gene therapy, Gyroscope/Novartis, Phase I/II GA)
  validates the augmentation direction by supplementation, not
  blockade (PMID 37478687) — an antibody would need to match this
  mechanism. Agonist/stabilizing antibodies against soluble enzymes
  are technically rare (no approved precedent); the conformational
  activation of CFI (inactive zymogen → cofactor-bound active
  trimolecular complex) is the key untapped epitope axis — a
  conformation-selective antibody stabilizing the active state
  (PMID 37478687).

- **Pathogenic autoantibodies pre-validate both target accessibility
  AND the on-target safety risk of a blocking antibody.** Endogenous
  anti-CFI IgG autoantibodies were found in 31% of pediatric aHUS
  patients (low C3 in 73%, plasmapheresis-responsive) (PMID 32962820).
  This is a class-level pattern with two uses: (a) PROOF OF ACCESSIBILITY
  — a circulating self-protein that elicits functional IgG autoantibodies
  in vivo is antibody-accessible and immunogenic, de-risking the
  "can an antibody reach/engage this target" question; (b) PROOF OF
  ON-TARGET BLOCKADE TOXICITY — the autoantibody disease (aHUS,
  complement dysregulation) is exactly the toxicity a therapeutic
  blocking antibody would induce. For any target where pathogenic
  autoantibodies are documented (check the disease-evidence search),
  record in field 4 (antibody landscape) that autoantibodies exist as
  a non-therapeutic proof-of-concept, and in field 8 (safety) that
  the autoantibody phenotype is the predicted on-target toxicity of a
  blocking antibody. This dual use generalizes to any autoantibody-
  associated target (AChR in myasthenia, BP180/BP230 in pemphigoid,
  ADAMTS13 in TTP, FI/FH in aHUS). It also flags immunogenicity risk:
  a self-protein that already breaks tolerance endogenously may be
  immunogenic when dosed as a therapeutic-antibody target.

- **Bruch's membrane impermeability as an ophthalmology-specific
  delivery barrier requiring intravitreal delivery.** FI has a ~286-fold
  concentration gradient between systemic plasma and the eye, and
  Bruch's membrane (the extracellular matrix between RPE and choroid)
  is largely impermeable to FI (PMID 32516404). A systemically dosed
  anti-CFI antibody may therefore fail to engage the intraocular target
  — the eye is pharmacologically privileged for plasma proteins of
  this size. This is the first ophthalmology target profiled where a
  tissue-barrier (not BBB, not PK/half-life) is the dominant delivery
  constraint. For ophthalmology targets (AMD, GA, diabetic retinopathy,
  uveitis), add to field 9 (structural/delivery) a tissue-barrier note:
  does a plasma-to-eye gradient or a retinal barrier (Bruch's
  membrane, inner limiting membrane, RPE tight junctions) constrain
  systemic dosing? If so, field 11 (differentiation) should specify
  intravitreal delivery (matching the gene-therapy subretinal route)
  and an antibody format optimized for intravitreal PK (Fab/fragment
  for retina penetration, or full IgG for sustained intraocular
  half-life). This is the ophthalmology analog of the BBB-penetration
  pitfall documented for neuroscience targets (TrkB, clusterin).

- **PubMed search-term coverage for regulatory enzymes.** The
  highest-yield queries for CFI combined the protein name with
  indication ("factor I AMD", "complement factor I age-related macular
  degeneration") and with mechanism ("CFI deficiency"). "CFI
  antibody"[tiab] returned relevant autoantibody and bioactivity papers
  (PMID 32962820, 29782502) that the indication queries missed. For
  regulatory-enzyme targets, run four query classes: (1) protein name
  + antibody, (2) gene symbol + antibody, (3) protein name + lead
  indication, (4) protein name + deficiency/loss-of-function. The
  deficiency query is essential for regulatory enzymes (where
  loss-of-function disease defines the biology) and was the only query
  that surfaced the systematic-review and cerebral-inflammation
  papers (PMID 40713518, 32098865).

(CFI profile, ~31.5K chars, 10 papers (abstract-only), 10 unique PMIDs
cited, working-docs/hitlist-profiles/complement-factor-i.md.)

- **2026-08-17 — FGF19 key-paper-ingestion profile observations.**
  Cardiovascular/metabolic target, preclinical tier. FGF19 is a gut-derived
  endocrine hormone (216 aa, ~24 kDa, UniProt O95750) regulating bile acid
  synthesis, glucose/lipid metabolism, and energy homeostasis. Built via
  delegated subagent using the lightweight retrieval pipeline (direct PubMed
  E-utilities + UniProt REST, no paper-ingest scripts). 5 broad PubMed
  queries, 80 unique PMIDs, 16 landmark abstracts fetched. Abstract-only
  ingestion (no full-text retrieval — all via efetch XML abstract parsing).
  UniProt REST API queried for structural details. ~23K chars, 15 unique
  PMIDs cited. See `references/fgf19-profile-observations.md` for full
  observations. Key new patterns:

  (1) **Dual-modality secreted target with antagonism (cancer) and agonism
  (metabolic) as opposing therapeutic strategies — the FGF19 duality.**
  FGF19 is the first profiled target where the SAME secreted protein has two
  completely opposing antibody therapeutic directions: (a) **antagonism** —
  anti-FGF19 antibodies block FGF19–FGFR4 mitogenic signaling for HCC/colon
  cancer (PMID 17599042, 32061104); (b) **agonism** — FGF19 analogs (aldafermin/
  NGM282) activate FGF19 metabolic signaling for NASH/PSC/cardiovascular disease
  (PMID 29519502, 32781086, 30679232). The cancer and metabolic applications
  pull in opposite directions: blocking FGF19 risks bile acid toxicity (the
  metabolic function), while activating FGF19 risks oncogenesis (the mitogenic
  function). This is distinct from FGF21 (same subfamily), where only agonism
  is therapeutic. For field 2, document both "effect of blockade" AND "effect
  of activation" as therapeutically relevant — one is not harmful and the other
  beneficial; BOTH have therapeutic applications in different diseases. For
  field 11, the key differentiation question is which direction the new
  antibody takes. Generalizes to any endocrine hormone with dual mitogenic +
  metabolic signaling (FGF19, and potentially Wnt signaling modulators).

  (2) **Epitope selectivity resolves on-target mechanism-based toxicity — the
  N-terminal selective antibody paradigm.** First-gen anti-FGF19 antibodies
  (1A4) blocked ALL FGF19 activity (both mitogenic/FGFR4 and metabolic/CYP7A1),
  causing severe bile acid toxicity (hepatotoxicity, diarrhea) in cynomolgus
  monkeys (PMID 22268002). Second-gen antibodies (G1A8, HS29) target the
  N-terminus of FGF19 — selectively blocking mitogenic/FGFR4 signaling while
  sparing metabolic/bile acid regulation — with NO bile-acid side effects in
  NHP (PMID 32061104). This is the canonical example of epitope engineering
  solving on-target mechanism-based toxicity: the toxicity (bile acid
  dysregulation) and the efficacy (anti-tumor) share the same target, but
  different receptor axes (FGFR4 vs FGFR1c/KLB), and epitope selectivity
  separates them. For field 5 (epitope landscape) and field 6 (failure modes),
  when a target has on-target mechanism-based toxicity from broad blockade,
  check whether the efficacy and toxicity pathways diverge at the
  receptor/effector level — if so, epitope selectivity can decouple them. This
  generalizes to any secreted ligand with multiple receptor axes where one
  axis is therapeutic and another is protective (dual-receptor targets like
  LIGHT/HVEM+LTβR, CCL1/CCR8+AMFR — but here the selectivity is at the
  ligand-epitope level, not the receptor level).

  (3) **FGF19 agonist analog retains residual oncogenicity despite engineering
  — the uncoupling failure.** Aldafermin (NGM282) was engineered to separate
  FGF19's metabolic from mitogenic activities, but preclinical data show it
  retains oncogenic cooperation with MYC — short systemic treatment triggered
  rapid proliferative hepatic foci in p53-deficient/MYC-driven HCC mouse
  models (PMID 38228803). This is a distinct failure mode for engineered
  agonists: the design goal (uncoupling metabolic from mitogenic) was NOT
  fully achieved. For field 6, when an engineered analog claims functional
  uncoupling, verify with preclinical oncogenesis models — the uncoupling may
  be partial. For field 8 (safety), residual oncogenicity is a concern for
  any FGF19 agonist in patients with damaged, mutation-prone livers. This
  extends the "agonist-format liability" pattern (ANP/GC-A hypotension) to
  oncogenic risk: activating a pathway with dual metabolic + mitogenic
  signaling carries an intrinsic cancer risk that epitope engineering may
  reduce but not eliminate.

  (4) **PubMed exact-phrase queries for antibody targets can return zero —
  broaden to boolean field-restricted queries.** The initial queries
  `"FGF19 antibody"[tiab]`, `"fibroblast growth factor 19 antibody"[tiab]`,
  and `"FGF19 therapeutic"[tiab]` ALL returned 0 results — FGF19 antibody work
  is published under different phrasing ("anti-FGF19", "antibody-mediated
  inhibition of FGF19", antibody codes like "1A4" or "G1A8"). Broadening to
  boolean queries (`FGF19[tiab] AND (antibody[tiab] OR antibodies[tiab] OR
  therapeutic[tiab] OR antagonist[tiab] OR agonist[tiab])`) recovered 80
  unique PMIDs. **Rule:** When exact-phrase `[tiab]` queries return 0, do not
  assume the literature doesn't exist — reformulate as boolean combinations
  with the gene symbol plus relevant modality/functional terms. Also search
  for known drug/analog names (aldafermin, NGM282) and antibody codes as
  separate queries. The FGF19 antibody literature is real but not findable
  with naive phrase queries.

  (5) **UniProt REST API for structural target identity — efficient single-
  call enrichment for secreted protein profiles.** The UniProt JSON API
  (`rest.uniprot.org/uniprotkb/O95750.json`) provided signal peptide
  location (1–24), mature chain (25–216), disulfide bonds (Cys58–Cys70,
  Cys102–Cys120), PDB cross-references (1PWA, 2P23, 6KTR, 6NFJ), tissue
  specificity, and functional description in a single fast call with no rate
  limits. For abstract-only profiles (no full-text retrieval), UniProt is the
  primary source for fields 1 (identity) and 9 (structural information). The
  `features` array contains Signal/Chain/Disulfide bond/Domain entries with
  residue positions; the `comments` array contains FUNCTION/TISSUE_SPECIFICITY
  text. This extends the UniProt usage pattern from CCR4 (molWeight field) and
  5T4 (demerged entries) — UniProt is a first-class data source for target
  profiling, not just an ID-verification gate.

(FGF19 profile, ~23K chars, 16 landmark abstracts fetched, 15 unique PMIDs
cited, working-docs/hitlist-profiles/fgf19.md.)

- **2026-08-17 — CFH (complement factor H) key-paper-ingestion profile
  observations.** Ophthalmology target, preclinical tier (AMD primary);
  also nephrology (aHUS/C3G) and oncology (NSCLC, glioma). CFH (UniProt
  P08603) is a 1231-aa, 20-SCR-domain secreted plasma glycoprotein, the
  major soluble regulator of the alternative complement pathway. The
  Y402H variant (rs1061170) in SCR7 is the strongest common genetic risk
  factor for AMD (PMID 15761122). Built via delegated subagent using the
  lightweight retrieval pipeline (direct PubMed E-utilities + UniProt REST,
  no paper-ingest scripts). 5+ PubMed queries (CFH antibody, factor H AMD,
  Y402H, anti-factor H therapeutic), ~25 candidate abstracts fetched, 21
  PMIDs cited. Abstract-only ingestion. UniProt REST API queried for domain
  map (20 SCR domains with residue ranges), 8 glycosylation sites, tissue
  specificity, and function text. ~40K chars profile. Key new patterns:

  (1) **Conformational-selective surface targeting of a secreted/circulating
  protein — the "plasma sink evasion" paradigm.** GT103 (first-in-class
  anti-CFH antibody, fully human IgG3, Phase 1b NSCLC, NCT04314089) recognizes
  a conformationally distinct CFH epitope present on tumor-cell-associated
  CFH and tumor-derived exosomes but NOT on native soluble CFH or normal
  tissues (PMID 36995981, PMID 38555134, PMID 34133431). This is the key
  design lesson for antibodies against high-abundance plasma proteins
  (~2 µM for CFH): a naive antibody that binds soluble CFH would be
  sequestered by the plasma sink AND risk systemic complement
  dysregulation. A conformational-selective antibody that only recognizes
  the surface-bound disease conformation achieves tissue specificity despite
  the target being abundant in plasma. For field 5 (epitope landscape) and
  field 11 (differentiation), when the target is a secreted/circulating
  protein that deposits on cell surfaces in a conformationally distinct
  state, document: (a) whether a surface-specific conformational epitope
  has been identified; (b) whether the soluble form would sequester a
  non-selective antibody (plasma concentration); (c) whether conformational
  selectivity is the strategy to avoid systemic on-target toxicity. This
  generalizes to any circulating regulator/effector protein that changes
  conformation upon surface binding (complement regulators CFH/CFI/vitronectin,
  clusterin, potentially apolipoproteins on lipoprotein particles). It is
  distinct from the FGF19 epitope-selectivity pattern (different receptor
  axes from the same ligand) — here the selectivity is soluble-vs-surface
  conformation of the SAME target, not ligand-vs-receptor.

  (2) **Autoantibody disease as the pre-existing human toxicity profile for
  regulator-targeting antibodies.** Anti-CFH autoantibodies (FHAAs) cause
  atypical hemolytic uremic syndrome (aHUS) — thrombotic microangiopathy,
  AKI, hemolysis, ESRD — in ~10.9% of aHUS patients (PMID 33384694, PMID
  27452363). This means the clinical toxicity of therapeutic CFH blockade
  is already known from human autoantibody disease, BEFORE any therapeutic
  antibody is dosed. The GT103 Phase 1b saw a grade 3 AKI DLT at the lowest
  dose (0.3 mg/kg), consistent with this mechanism (PMID 39747856). For
  field 6 (failure modes) and field 8 (safety), when pathogenic autoantibodies
  against the target cause a recognized clinical disease, that disease IS
  the on-target toxicity profile of any therapeutic blocking antibody —
  the autoantibody literature is pre-existing human "toxicity data." Use
  it to define the safety ceiling, the organ systems at risk, and the
  clinical monitoring required. This generalizes to any regulator target
  where autoantibody-mediated disease exists (CFH/aHUS, AChR/myasthenia
  gravis, TSHR/Graves' disease, desmoglein/pemphigus, ADAMTS13/TTP). It is
  distinct from the FGF19 bile-acid toxicity (no autoantibody disease
  defines it) and the CD11a PML (not autoantibody-mediated).

  (3) **Bidirectional therapeutic direction across indications — the CFH/FGF19
  shared pattern.** CFH shares the FGF19 dual-modality pattern (above): CFH
  *blockade* = oncology direction (restore complement attack on tumors,
  GT103); CFH *augmentation* or FHR *blockade* = AMD direction (restore
  complement regulation at the RPE). The AMD direction is OPPOSITE to the
  direction with clinical-stage antibody development (oncology, GT103). For
  field 2, always document "effect of blockade" AND "effect of activation"
  as both therapeutically relevant. For field 11, the key differentiation
  question is which direction the new antibody takes, and whether it
  serves the hit-list indication or a different one. The CFH profile adds
  that the hit-list indication (AMD) may require the OPPOSITE mechanism
  from the one with clinical precedent (oncology) — a profiling trap if
  the subagent assumes the clinical-stage antibody validates the
  hit-list indication.

  (4) **PubMed query coverage for complement regulators — the
  autoantibody + therapeutic-antibody dual search.** The highest-yield
  queries combined: (a) "complement factor H"[tiab] + antibody/therapeutic
  (518 hits), (b) "CFH"[tiab] + AMD (942 hits), (c) "factor H"[tiab] +
  alternative complement pathway + antibody/inhibitor (165 hits), (d)
  "anti-factor H"[tiab] + antibody/autoantibody + therapeutic (86 hits),
  (e) "complement factor H" + cancer/tumor + antibody/immunotherapy
  (104 hits). Query (d) surfaced the autoantibody-disease literature
  (aHUS, C3G) essential for field 8 (safety); query (e) surfaced the
  GT103 clinical trial paper (PMID 39747856). For complement regulator
  targets, run BOTH autoantibody-disease queries AND therapeutic-antibody
  queries — they return non-overlapping literatures critical for
  different fields (8 vs 4/6). Also search for named therapeutic antibodies
  (GT103) once discovered in review abstracts — the Phase 1b trial paper
  (PMID 39747856) was found via a "factor H + cancer + antibody" query,
  not via the AMD/antibody queries.

(CFH profile, ~40K chars, 21 unique PMIDs cited,
working-docs/hitlist-profiles/complement-factor-h.md.)

- **2026-08-17 — GDF11 key-paper-ingestion profile observations.**
  Cardiovascular target, preclinical tier. GDF11 (Growth Differentiation
  Factor 11, gene GDF11, UniProt O95390) is a TGF-β superfamily ligand with
  89% amino acid identity to myostatin/GDF8 in the mature domain. Built via
  delegated subagent using the lightweight retrieval pipeline (direct PubMed
  E-utilities + UniProt REST + PDB REST, no paper-ingest scripts). 8+ PubMed
  queries (3 specified + 5+ supplementary for seminal papers, controversy,
  receptor biology, structures, clinical trials), 43+ unique PMIDs
  identified, 20+ landmark abstracts fetched via efetch XML parsing. Also
  queried UniProt REST API (O95390) for structural details and PDB REST API
  for 5 crystal structures. ClinicalTrials.gov API v2 queried (0 GDF11-
  specific trials). Abstract-only ingestion. ~52K chars, 27 unique PMIDs
  cited. See `references/gdf11-profile-observations.md` for full
  observations. Key new patterns:

  (1) **Therapeutic-direction-ambiguous target — neither blockade nor
  augmentation is clearly correct, the "direction trap."** GDF11 is
  protective in cardiovascular disease (anti-hypertrophic, anti-pyroptosis,
  anti-aneurysm) — blocking it would worsen cardiovascular outcomes. But
  augmenting it causes dose-dependent cachexia and death at supraphysiologic
  doses. This is fundamentally different from the FGF19/CFH dual-modality
  pattern (where blockade and augmentation serve different indications):
  here BOTH directions carry serious risk for the SAME indication. For
  field 11, the differentiation opportunity is not "which direction" but
  "how to modulate within a narrow therapeutic window" — e.g.,
  activated-form-specific antibodies, conditional/prodrug formats, or
  conformation-selective modulators. For field 6, flag the direction
  ambiguity as the primary strategic risk. Generalizes to any target
  with a narrow therapeutic window where the same pathway is both
  protective (low dose) and pathologic (high dose).

  (2) **Homologous-ligand cross-reactivity as the defining antibody
  engineering challenge — the GDF11/myostatin paradigm.** GDF11 and
  myostatin/GDF8 share 89% mature-domain identity (90% similarity).
  Standard antibody selection produces cross-reactive reagents; the
  SOMAmer (aptamer) field solved this with counter-selection (positive
  selection for GDF11 + counter-selection against GDF8), achieving Kd
  0.05-1.2 nM with no GDF8 binding (PMID 31638376). No antibody has
  achieved this specificity. For field 5 (epitope landscape), when the
  target has a highly homologous family member, document: (a) the %
  identity, (b) whether any binding reagent (antibody or aptamer) has
  achieved discrimination, (c) the structural basis for discrimination
  (the non-conserved 11% of residues). For field 11, the GDF11-specific
  antibody that discriminates from myostatin is a clear white-space
  opportunity — the aptamer proof-of-concept shows it's achievable.
  Generalizes to any TGF-β superfamily ligand pair with high homology
  (GDF11/GDF8, activin A/activin B, BMP9/BMP10).

  (3) **Activated vs total circulating form as the clinically predictive
  biomarker — the prodomain-cleavage distinction.** Total GDF11/GDF8 levels
  do not predict cardiovascular outcomes or incident HF (PMID 37624693),
  but activated GDF11/8 (post-prodomain-cleavage form, detected by a
  dual-specific aptamer) strongly predicts cardiovascular events (HR 0.43)
  and mortality (HR 0.33) in 11,609 patients (PMID 40664633). For field 7
  (assay systems) and field 3 (disease evidence), when the target exists
  in latent and active forms, document which form is clinically predictive
  — the total-level biomarker may be a null result while the activated-form
  biomarker is strongly predictive. For field 11, an antibody selective
  for the activated form could serve as both a therapeutic (targeting only
  the disease-relevant form) and a companion diagnostic. Generalizes to
  any TGF-β superfamily ligand with prodomain-mediated latency (GDF11,
  myostatin, activins, BMPs).

  (4) **Controversial foundational biology as a profiling challenge.** The
  seminal GDF11 paper (Loffredo 2013, PMID 23663781) reported that GDF11
  reverses age-related cardiac hypertrophy — but the age-related decline
  was not reproduced (PMID 27304512), GDF11 is not associated with incident
  HF in humans (PMID 37624693), and all subsequent skeletal muscle studies
  found GDF11 inhibits regeneration (PMID 31144559). For field 3, present
  the controversy explicitly — cite both the seminal finding AND the
  contradicting evidence with PMIDs. Do not resolve the controversy by
  choosing one side; present both and let the reader weigh. For field 6,
  the controversy itself is a failure mode — a target whose foundational
  biology is contested carries elevated risk for any therapeutic program.

  (5) **PDB REST API as a one-call structure survey for field 9.** The
  RCSB PDB REST API (`data.rcsb.org/rest/v1/core/entry/{PDB_ID}`) provides
  structure title, method, and resolution in a single fast call per PDB ID.
  Combined with UniProt cross-references (which list PDB IDs), this gives a
  complete structural inventory for field 9 without leaving the
  lightweight retrieval pipeline. For GDF11, 5 PDB structures were
  identified and characterized: apo GDF11 (5E4G, 1.5Å), GDF11:follistatin
  (5JHW), and receptor ternary complexes (6MAC, 7MRZ). This extends the
  UniProt-first pattern — UniProt gives the PDB IDs, PDB REST gives the
  descriptions, all without full-text retrieval.

(GDF11 profile, ~52K chars, 27 unique PMIDs cited,
working-docs/hitlist-profiles/gdf11.md.)

- **2026-08-17 — Sudan ebolavirus GP key-paper-ingestion profile
  observations.** Preclinical-tier infectious disease target. Sudan
  virus glycoprotein (SUDV GP), UniProt Q66814 (standalone reviewed
  entry) — the surface class I fusion glycoprotein of *Orthoebolavirus
  sudanense*, structural homolog of EBOV (Zaire) GP but antigenically
  distinct. No approved SUDV vaccine or therapeutic; the FDA-approved
  EBOV antibodies (ansuvimab, REGN-EB3/Inmazeb) are ineffective against
  SUDV. Built via direct PubMed E-utilities using the two-step curl form
  (`urllib.parse` to build URL, `curl` via `subprocess.run` to fetch).
  5 queries, 34 unique PMIDs, 12 landmark abstracts via efetch XML.
  Abstract-only ingestion. UniProt Q66814 grounded field 1. ~35K chars,
  18 unique PMIDs cited. See
  `references/sudan-ebolavirus-gp-profile-observations.md` for full
  observations. Key new patterns:

  (1) **Read the already-profiled homolog first — format + differentiation
  axis.** SUDV GP is structurally homologous to EBOV GP, for which an
  approved-tier profile already existed (`ebola-gp.md`). Loading that
  profile before writing provided (a) exact field-depth/format
  calibration (antibodies per field 4, epitope-bin granularity in field
  5, how field 3 framed the PALM trial) and (b) the differentiation axis
  — every field contrasts SUDV GP against the already-characterized EBOV
  GP. The central unmet-need narrative ("approved EBOV antibodies are
  ineffective against SUDV; pan-ebolavirus antibodies are the active
  development front") came directly from the EBOV profile's field 4 and
  field 2. The domain map, oligomerization, and native-vs-cleaved GP
  conformational axis were transferable with SUDV UniProt confirmation,
  roughly halving the work of fields 1, 2, and 5. Rule: before profiling
  a target, grep `working-docs/hitlist-profiles/` for its family and
  load the closest profiled homolog; contrast throughout rather than
  starting from scratch. Generalizes to any target family with an
  already-profiled close homolog (ebolaviruses, flaviviruses, integrins,
  chemokine receptors, Fc-gamma receptors).

  (2) **Preclinical-tier infectious-disease target with no approved
  therapy → field 3 organized by model tier, not trial phase.** The
  TEMPLATE.md field 3 is implicitly shaped around clinical evidence
  types. For an approved-tier target like EBOV GP, field 3 led with the
  PALM RCT. For SUDV GP — no approved therapy, no clinical trial — field
  3 was restructured by preclinical model tier: (1) SUDV-specific
  cocktail in NHP, (2) pan-ebolavirus cocktails in NHP/ferret, (3)
  cross-reactive antibodies in rodent models, (4) mechanistic/structural
  evidence. State the unmet-need ("no approved therapy/vaccine for
  SUDV") explicitly in the first disease-evidence block — it is the
  field's organizing principle, not an aside. Generalizes to any
  preclinical-tier infectious-disease target: organize field 3 as a
  descending model-tier ladder (NHP → ferret → rodent → mechanistic).

  (3) **Conserved epitope ≠ cross-species neutralization — validate
  against the target species.** BDBV223 targets the GP2 stalk, the
  most sequence-conserved region across ebolaviruses, yet neutralizes
  BDBV and EBOV but NOT SUDV, despite stalk conservation (PMID
  30996276). Targeted mutagenesis to enhance SUDV GP recognition
  indicated additional determinants lie outside the visualized
  interactions — likely quaternary assembly or membrane-interacting
  regions. For field 5, conservation at the sequence/structural level
  does not guarantee functional breadth against a given species. For
  field 6, "conserved epitope but species-specific non-neutralization"
  is a distinct failure category requiring engineering of the
  additional (quaternary/membrane) determinants. Generalizes to any
  conserved-epitope antibody strategy across a viral family: validate
  against each species; do not assume conservation confers breadth.

  (4) **UniProt REST grounds field 1 for standalone viral
  glycoproteins.** SUDV GP has a standalone reviewed UniProt entry
  (Q66814) providing domain regions (RBD 54–201, mucin-like 305–485,
  fusion peptide 524–539), 12 N-linked glycosylation sites, MW (~75
  kDa, 676 aa), and topology — via a single
  `curl https://rest.uniprot.org/uniprotkb/Q66814.json` call. This
  contrasts with the ZIKV NS1 profile (polyprotein Q32ZE1, no
  standalone entry → field 1 from literature). Rule: for viral
  surface/structural proteins, check for a standalone UniProt entry
  first; if one exists, a single REST call grounds field 1's
  domain/MW/glycosylation/topology. Fall back to literature only for
  polyprotein-encoded fragments with no standalone entry.

  (5) **GP fusion-loop escape mutation under antibody pressure — a
  GP-targeted antibody escape mechanism.** In an EBOV-infected,
  mAb-treated NHP, a single GP fusion-loop mutation resisted
  neutralization AND increased growth kinetics and virulence,
  contributing to atypical/persistent disease (PMID 33436428). For
  field 6, this is distinct from the M2 "delayed antigen expression"
  escape — here the epitope itself mutates under pressure, selecting
  more-virulent variants. For field 11, this motivates multi-epitope
  cocktail design (pair non-overlapping bins, as RIID F6-H2 and the
  pan-ebolavirus cocktails do) to resist escape. Generalizes to any
  viral surface glycoprotein under antibody pressure: escape mutations
  can increase virulence, not just evade neutralization, making
  cocktail breadth a safety requirement, not only an efficacy strategy.

- **2026-08-17 — P. aeruginosa PcrV profile: first anti-virulence
  structural-protein target (non-toxin bacterial target).** PcrV is a
  structural component of the type III secretion system (T3SS)
  injectisome — not a toxin, not a viral entry protein, not a human
  protein. Anti-PcrV antibodies block the *delivery machinery* (the
  translocon pore), not a circulating toxin. This is a distinct
  mechanological class from anthrax PA (toxin neutralization) and from
  all viral targets (entry blockade). 8 PubMed E-utilities queries (3
  [tiab] + 5 supplementary), 21 unique PMIDs retrieved, abstract-level
  synthesis (abstract-only acceptable per task spec). ~34K chars, 154
  PMID citations, 21 unique PMIDs, 3 NCT IDs, 5 PDB structures. Key new
  patterns:

  (1) **Anti-virulence vs anti-toxin distinction — the antibody blocks
  a contact-dependent apparatus, not a circulating factor.** Anthrax
  PA is secreted, circulates, and is neutralized in the bloodstream.
  PcrV is assembled on the bacterial surface at the T3SS needle tip
  and requires bacterial-host cell contact for function. Anti-PcrV
  antibodies block translocon pore formation/size at the
  bacterium-host interface. This means: (a) the antibody must reach the
  site of bacterial-host contact (lung epithelium, not just serum);
  (b) efficacy depends on T3SS expression being active — which is
  variable and disease-stage-dependent; (c) the mechanism is
  anti-virulence (disarming the pathogen) not bactericidal (killing
  it). For field 2, explicitly describe the contact-dependent
  mechanism. For field 6, note that anti-virulence antibodies may need
  combination with antibiotics or Fc effector function for bacterial
  clearance.

  (2) **Target expression level as a population-dependent failure
  mode.** KB001 (PEGylated anti-PcrV Fab') failed its primary endpoint
  (time-to-antibiotics) in a Phase 2 CF trial because T3SS expression
  is low in chronic CF P. aeruginosa infections (PMID 29292092). The
  target was insufficiently expressed in the chosen disease setting.
  However, the VAP Phase 2a trial showed a promising trend (31–33% vs
  60% pneumonia incidence) in mechanically ventilated patients — an
  acute setting where T3SS is upregulated. This is a population
  mismatch, not a target failure. For field 6, this is a distinct
  failure mode from "wrong epitope" or "wrong format" — the target is
  valid but disease-stage-dependent expression must be considered.
  For field 11, recommend patient stratification by target expression
  (e.g., T3SS expression biomarker in sputum/blood) for clinical
  trials. This pattern generalizes to any anti-virulence target where
  the virulence factor is conditionally expressed (quorum sensing,
  biofilm, T3SS, T6SS).

  (3) **Fab' fragment without Fc effector function is a format
  liability for anti-bacterial antibodies.** KB001 was a PEGylated
  Fab' fragment — no Fc, so no complement-mediated killing (CDC),
  opsonophagocytosis, or ADCC. The antibody's only mechanism was
  passive T3SS blockade. The Fc-modified V2L2-MD study (PMID 40821801)
  demonstrated that adding C1q-enhancing Fc mutations significantly
  improved complement deposition, opsonophagocytic killing, and
  reduced bacterial burden in vivo. For field 6, the Fab-only format
  limited bacterial clearance — a format failure mode unique to
  anti-bacterial antibodies (for anti-toxin antibodies, Fab-only is
  acceptable because the toxin is neutralized directly). For field 4,
  always note whether the antibody format includes Fc effector
  function. For field 11, a full IgG with Fc engineering is a clear
  differentiation opportunity for anti-bacterial-structural-protein
  targets.

  (4) **Bacterial structural protein — UniProt field needs organism
  annotation.** Like anthrax PA, PcrV is a bacterial protein. The
  UniProt ID (G3XD49) is for P. aeruginosa PAO1, not a human protein.
  Multiple UniProt entries exist for different strains (G3XD49 for
  PAO1, A0A0H2Z8G0 for PA14, O30527 for P. aeruginosa generally). In
  field 1, list the strain-specific accession and note the organism
  explicitly. The gene symbol is a bacterial gene (pcrV) with no HGNC
  equivalent. This follows the anthrax PA adaptation pattern.

  (5) **Infectious disease PubMed search — [tiab] queries for
  bacterial targets have good recall.** Unlike the FABP4 preclinical
  target (where [tiab] queries returned zero), PcrV [tiab] queries
  returned 1–84 results. "PcrV type III secretion"[tiab] returned 84;
  "PcrV antibody"[tiab] returned 1. The narrow [tiab] query worked
  here because PcrV is a distinctive term that appears in title/abstract
  of the relevant literature. Supplementary queries ("KB001
  Pseudomonas aeruginosa", "mAb166 PcrV Pseudomonas", "PcrV structure
  crystal Pseudomonas") surfaced additional clinical and structural
  papers. For bacterial targets with unique gene names, [tiab] queries
  are effective; supplement with antibody code names and structure
  queries.

  (PcrV profile, ~34K chars, 8 PubMed queries, 21 unique PMIDs,
  abstract-level synthesis, 5 PDB structures, 3 NCT IDs,
  working-docs/hitlist-profiles/p-aeruginosa-pcrv.md.)

(Sudan ebolavirus GP profile, ~35K chars, 18 unique PMIDs cited,
working-docs/hitlist-profiles/sudan-ebolavirus-gp.md.)

- **2026-08-17 — M. tuberculosis LAM profile: first glycolipid target
  and first intracellular-pathogen target.** Preclinical-tier infectious
  disease target. Lipoarabinomannan (LAM / ManLAM) — the major cell wall
  glycolipid of *M. tuberculosis*. Not a protein: a non-ribosomal
  lipoglycan. Surface-exposed, shed into urine (basis for urine LAM
  diagnostic tests). Built via direct PubMed E-utilities (two-step curl
  form). 8+ queries with progressive broadening, 72 candidate PMIDs
  screened, 14 landmark abstracts fetched (7 primary + 7 supplementary).
  Abstract-only ingestion. No UniProt (glycolipid, not protein).
  14 unique PMIDs cited, ~40K chars. See
  `references/m-tb-lam-profile-observations.md` for full observations.
  Key new patterns:

  (1) **Glycolipid target class — UniProt does not apply, epitope is
  carbohydrate.** LAM is the first profiled target that is NOT a protein.
  No UniProt entry, no HGNC gene symbol, no single-chain sequence. Field 1
  (Target identity) must be adapted: gene symbol → biosynthetic enzyme
  operon (*embCAB*); UniProt ID → N/A (optionally list biosynthetic enzyme
  UniProt entries for reference); key domains → glycan structural motifs
  (PI anchor, mannan core, arabinan domain, mannose caps, tailoring
  modifications); MW → heterogeneous population (~17–35 kDa). Field 5
  (Epitope landscape) describes carbohydrate epitopes — oligosaccharide
  motifs, not protein linear/conformational epitopes. No antibody–glycan
  co-crystal structures typically in PDB; epitope data from glycan
  microarrays and functional competition. Generalizes to any non-protein
  target: glycolipids (LAM, LPS, gangliosides), polysaccharide capsules,
  glycoconjugates.

  (2) **Intracellular pathogen — antibody redirects uptake pathway, not
  direct neutralization.** M. tuberculosis survives within macrophage
  phagosomes — fundamentally different from all prior infectious disease
  targets (secreted toxins, viral surface glycoproteins, bacterial
  surface structural proteins). P1AM25 (human IgG1, PMID 37733444)
  demonstrates antibody-mediated protection IS achievable: the mechanism
  is FcγR-dependent enhanced phagocytosis redirecting mycobacteria from
  the immunoevasive MR/DC-SIGN pathway to the bactericidal FcγR pathway.
  The antibody doesn't penetrate the host cell; it changes the uptake
  pathway at the cell surface. For field 6, the fraction of extracellular
  vs. intracellular bacilli may limit antibody access — a PK/PD
  consideration not present for toxin/viral targets. Generalizes to any
  intracellular bacterial target (Salmonella, Listeria, Brucella,
  Legionella, Chlamydia).

  (3) **Fc-effector function as a BINARY requirement — not just
  beneficial.** P1AM25 as murine IgG2a (FcγR-binding) was protective, but
  murine IgG1 and non-FcγR-binding IgG were NOT — despite identical Fab
  specificity (PMID 37733444). This is stronger than the PcrV observation
  (Fab-only was a liability, Fc engineering improved efficacy): for
  anti-LAM antibodies, Fc-effector function is non-negotiable. The
  protective mechanism is entirely FcγR-dependent, not direct
  neutralization. For field 6, "wrong Fc isotype" is a distinct failure
  mode from "wrong epitope" — both are fatal but independent axes. For
  field 11, Fc optimization (afucosylation for FcγRIIIa/ADCC, FcγR-biased
  variants) is a clear differentiation opportunity (PMID 40449485).
  Generalizes to any antibody against an intracellular pathogen where
  the mechanism is opsonophagocytosis: Fc-effector function IS the
  mechanism, not an enhancement.

  (4) **Glycan motif-level epitope specificity determines protection.**
  P1AM25 (protective) and two other high-affinity human IgG1 anti-AM mAbs
  (non-protective) all target the arabinomannan (AM) domain — same domain,
  different oligosaccharide motifs (PMID 37733444). Epitope specificity at
  the glycan motif level is the single determinant of protection. This is
  the glycolipid analog of the FGF19 N-terminal selectivity pattern:
  different glycan motifs on the same domain separate protective from
  non-protective antibodies at equal affinity. For field 5, glycan
  epitope mapping requires synthetic oligosaccharide libraries and glycan
  microarrays — not peptide scanning. For field 6, "high affinity to the
  wrong glycan motif" is a distinct failure mode. Generalizes to any
  glycan-targeting antibody (anti-LPS, anti-capsular polysaccharide,
  anti-ganglioside).

  (5) **Diagnostic-to-therapeutic cross-validation for glycolipid
  targets.** LAM has a mature diagnostic antibody pipeline (Alere LF-LAM,
  Fujifilm SILVAMP TB-LAM, 93% sensitivity) alongside an early therapeutic
  antibody pipeline (P1AM25, Grace 2025 mAb). The diagnostic antibodies
  validate target accessibility and clinical relevance but have NOT been
  evaluated for therapeutic function. For field 4, list diagnostic and
  therapeutic antibodies separately — different optimization criteria
  (diagnostic: sensitivity/specificity; therapeutic: Fc effector function
  + protective epitope). For field 11, the MTX epitope (diagnostic,
  species-specific) is an unexplored therapeutic target — an anti-MTX
  IgG1 with Fc-effector function could be a companion
  diagnostic-therapeutic pair. Generalizes to any target with both
  diagnostic and therapeutic antibody pipelines.

(M. tb LAM profile, ~40K chars, 8+ PubMed queries, 14 unique PMIDs,
abstract-level synthesis, working-docs/hitlist-profiles/m-tb-lam.md.)

- **2026-08-17 — M. tuberculosis ESAT-6 profile: second M. tb target,
  first virulence-effector (toxin-analog) target for intracellular
  pathogens.** Preclinical-tier infectious disease target. ESAT-6 (EsxA,
  Rv3875, UniProt P9WNK5) is a 6 kDa secreted M. tuberculosis protein —
  the founding member of the WXG100/ESAT-6 family, exported via the
  ESX-1/type VII secretion system. Absent from all BCG strains (RD1
  deletion). Has multiple virulence functions: pore formation (phagosome
  escape), TLR2 signaling inhibition, direct T-cell IFN-γ suppression,
  MMP-10-driven tissue destruction, macrophage apoptosis via
  miR-155/SOCS1, and Th17 promotion. Built via direct PubMed E-utilities
  (two-step urllib form). 11 search queries, 78 candidate PMIDs screened,
  20 landmark abstracts fetched (efetch XML, batches of 5–10). Abstract-only
  ingestion. UniProt P9WNK5 grounded field 1. ~45K chars, 20 unique PMIDs
  cited. Key new patterns:

  (1) **Dual-role paradox — target is both a virulence factor AND a
  protective immunogen.** ESAT-6 promotes Th17 responses that enhance
  vaccine efficacy (PMID 22102818) while also suppressing TLR2 signaling
  (PMID 17486091), inhibiting T-cell IFN-γ (PMID 20006311), and forming
  membrane pores (PMID 18852239). Complete antibody-mediated neutralization
  could impair Th17-mediated protection — the same protein that drives
  pathogenesis also drives a protective immune response. For field 6,
  this is a strategic risk distinct from simple on-target toxicity: the
  antibody could worsen infection by neutralizing a protective immunogen.
  For field 11, an epitope-selective approach (blocking TLR2-binding/
  pore-forming domains while preserving Th17-promoting domains) may be
  necessary, but the domains may overlap. Generalizes to any
  virulence factor that is also an immunogen (many bacterial secreted
  proteins serve dual roles).

  (2) **Blue ocean therapeutic antibody space for validated
  diagnostic/vaccine antigens.** ESAT-6 has a mature diagnostic pipeline
  (QuantiFERON-TB Gold IGRA, EC skin test Phase III, immunosensors,
  lateral flow assays) and a clinical-stage vaccine pipeline (H56:IC31
  Phase 1) but ZERO disclosed therapeutic antibody programs. The target
  is "validated" (diagnostic specificity, vaccine immunogenicity) yet
  the therapeutic antibody space is completely unexplored. For field 10,
  this is a distinct competitive landscape category: not "saturated"
  (many antibodies), not "graveyard" (failed antibodies), not "blue
  ocean" (no one has heard of the target) — it is "validated target,
  unexplored modality." For field 11, the differentiation opportunity is
  mechanistic: converting a validated diagnostic/vaccine antigen into a
  passive immunotherapy target, using the toxin-neutralization paradigm
  (analogous to raxibacumab/bezlotoxumab). Generalizes to any
  diagnostic/vaccine antigen with defined virulence functions that has
  never been explored for passive antibody therapy.

  (3) **Small protein — limited epitope surface, short functional
  domains.** At 95 amino acids (~6 kDa apparent MW), ESAT-6 has a very
  small surface for antibody binding. The functional domains are
  extremely short: the TLR2-binding domain is 6 C-terminal residues
  (PMID 17486091), the MMP-10-inducing domain is a 15-aa peptide
  (PMID 27654284). Generating high-affinity neutralizing antibodies
  against such small epitopes is challenging. For field 5, document the
  functional domain sizes explicitly — epitope surface area constrains
  antibody design. For field 11, this is a known risk: the small target
  surface may limit achievable affinity and specificity. Generalizes
  to any small secreted virulence factor (<10 kDa) with short
  functional motifs.

  (4) **pH-dependent conformational switch — heterodimer vs free
  monomer.** ESAT-6 forms a tight 1:1 heterodimer with CFP-10 at
  neutral pH (the secreted, stable, T-cell-recognized form). At acidic
  phagolysosomal pH (~5.0), the heterodimer dissociates and free
  ESAT-6 inserts into membranes to form pores (PMID 18852239). For
  field 5, antibodies must target the relevant conformational state
  in vivo — the secreted heterodimer (for extracellular neutralization)
  or the free monomer (for blocking pore formation). For field 9,
  document the conformational states and their pH dependence. This is
  distinct from viral glycoprotein conformational states (pre/post-
  fusion) because the switch is driven by dissociation of a binding
  partner (CFP-10), not by proteolytic cleavage. Generalizes to any
  protein that changes oligomeric state with pH to expose functional
  domains.

(M. tb ESAT-6 profile, ~45K chars, 11 PubMed queries, 20 unique PMIDs,
abstract-level synthesis, working-docs/hitlist-profiles/m-tb-esat-6.md.)

- **2026-08-17 — P. falciparum AMA1 profile: first malaria/parasite
  invasion-ligand target, first vaccine-antigen target with clinical
  trial failure as primary evidence.** Preclinical-tier infectious
  disease target. AMA1 (Apical Membrane Antigen 1, UniProt Q7KQK5, 622
  aa, ~72 kDa type I transmembrane protein) is a P. falciparum
  merozoite invasion ligand that forms the moving junction via AMA1–
  RON2 interaction. Built via direct PubMed E-utilities (two-step
  urllib form). 5 search queries, 72 candidate PMIDs screened, 35
  landmark abstracts fetched (efetch XML, batches of 5). Abstract-only
  ingestion (no full-text retrieval — most papers paywalled). UniProt
  Q7KQK5 grounded field 1 (domains, disulfide bonds, 14 PDB structures).
  ~68K chars, 35 unique PMIDs cited. Key new patterns:

  (1) **Vaccine-antigen targets have a fundamentally different profile
  shape from host-protein antibody targets.** For host-protein targets
  (TNF, PD-1, CD20), the clinical evidence in field 3 is from
  therapeutic antibody trials. For AMA1, the clinical evidence is from
  VACCINE trials — FMP2.1/AS02(A) Phase 2 (PMID 21916638, NEJM 2011),
  FMP2.1/AS01 CHMI (PMID 26908756), AMA1-DiCo Phase 1 (PMID 28947345).
  The "antibody landscape" in field 4 is dominated by research mAbs
  (1F9, 4G2dc1, R31C2, humAbAMA1, 75B10, 826827, WD34 i-body) rather
  than clinical-stage therapeutics — NO therapeutic anti-AMA1 antibody
  has entered clinical trials. The clinical failure mode (antigenic
  polymorphism causing strain-specific vaccine efficacy) is a VACCINE
  failure, not an antibody failure — the therapeutic antibody space is
  completely unexplored despite extensive preclinical antibody data.
  For field 3, cite vaccine trial results (Phase 2 efficacy, CHMI) as
  the primary clinical evidence, then note that therapeutic antibodies
  are preclinical. For field 6, the failure modes come from vaccine
  trials (antigenic polymorphism, immunodominance of variable
  epitopes, GIA not correlating with efficacy) but the success
  factors come from antibody engineering (conserved epitope targeting,
  non-RON2-blocking mechanisms). Generalizes to any pathogen antigen
  where vaccines have been tested clinically but therapeutic antibodies
  have not (AMA1, CSP, MSP-1, RH5, various viral glycoproteins).

  (2) **Antigenic polymorphism is the central failure mode for
  pathogen-surface-antigen targets.** AMA1 is one of the most
  polymorphic vaccine candidates — the immunodominant cluster 1 loop
  (c1L) in Domain I is under strong balancing selection, meaning the
  natural immune response targets the most variable regions. The
  FMP2.1/AS02(A) Phase 2 trial failed its primary endpoint (17.4%
  efficacy, P=0.18) but showed 64.3% allele-specific efficacy (P=0.03)
  against vaccine-strain-matched parasites (PMID 21916638). The
  allele-specific efficacy was not sustained into the second malaria
  season (PMID 24260195). This is fundamentally different from
  host-protein targets where the failure mode is typically wrong
  epitope, wrong population, or safety — here it is the TARGET ITSELF
  that varies across pathogen strains. For field 6, antigenic
  polymorphism should be the headline failure mode for any
  pathogen-surface-antigen target. For field 11, the key
  differentiation opportunity is targeting CONSERVED epitopes that the
  natural immune response under-selects (the 1e-loop, the pan-species
  conserved cleft, non-RON2-blocking epitopes like 75B10's). A
  rationally designed therapeutic mAb bypasses the immunodominance
  problem entirely — the antibody targets a conserved epitope
  regardless of what the human immune system naturally prefers. This
  is the strongest argument for therapeutic antibodies over vaccines
  for polymorphic pathogen antigens. Generalizes to any highly
  polymorphic pathogen surface antigen (HIV Env, influenza HA,
  PfMSP-1, bacterial capsular polysaccharides).

  (3) **Dual-stage (multi-life-cycle-stage) targets are a distinct
  advantage unique to pathogen antigens.** AMA1 is essential for BOTH
  merozoite invasion of erythrocytes AND sporozoite invasion of
  hepatocytes — making it unique among malaria vaccine targets in
  being required across multiple life-cycle stages. Antibodies like
  826827 (PMID 39632799) and WD34 i-body (PMID 39174515) block both
  blood-stage and liver-stage infection. No host-protein target has
  this dual-stage property — it is a pathogen-antigen-specific
  advantage. For field 2, explicitly document which life-cycle
  stages the target is essential for. For field 11, dual-stage
  inhibition is a differentiation dimension that no single-stage
  target can match — a single antibody could both treat acute
  disease (blood-stage) and prevent relapse/liver-stage infection.
  Generalizes to any pathogen antigen essential across multiple
  life-cycle stages (PfCSP for sporozoite + early liver stages,
  influenza HA for attachment + fusion, HIV Env for entry).

  (4) **UniProt ID lookup — never guess; always search.** The initial
  attempt to fetch PfAMA1 used a guessed UniProt ID (Q8IJX8) which
  returned Endonuclease ALBA3 — a completely unrelated P. falciparum
  protein. The correct ID (Q7KQK5) was found by searching UniProt
  with `protein_name:"apical membrane antigen" AND organism_id:36329`.
  For pathogen targets (especially parasitic), gene names and protein
  names are less standardized than for human proteins — always
  search UniProt by protein name + organism ID rather than guessing
  an accession. The UniProt search API
  (`rest.uniprot.org/uniprotkb/search?query=...&format=json`) is the
  reliable path. For P. falciparum, organism_id 36329 (3D7) or 5833
  (species) narrows the search. (AMA1 profile, 2026-08-17.)

  (5) **Abstract-only profiling at scale: 35 papers, no full-text
  retrieval, high-quality result.** The AMA1 profile was built
  entirely from PubMed abstracts (no full-text retrieval attempted —
  most key papers were in paywalled journals: NEJM, PLoS Pathog,
  Nat Commun, Cell Rep Med). The structured abstracts (often
  1,000–2,000 chars with Background/Methods/Results/Conclusions)
  provided sufficient detail to fill all 11 fields at a level adequate
  for prioritization. The profile is 68K chars with 35 unique PMIDs
  cited — comparable in depth to profiles built with full-text
  ingestion. This validates the existing observation that "rich EPMC
  abstracts compensate for missing full text" (C5 profile
  observation, 2026-08-15) and extends it: for well-studied targets
  with a large PubMed literature, abstract-level synthesis with a
  LARGE paper set (20-35 papers) can match or exceed key-paper-
  ingestion level (3-5 papers with full text) in total information
  coverage. The tradeoff is breadth (more papers, abstracts only)
  vs depth (fewer papers, full text). For infectious disease targets
  with extensive literature (AMA1, MSP-1, CSP, HIV Env), the breadth
  approach may be preferable — the key findings appear in multiple
  papers, so missing any single full text is less damaging.
  (AMA1 profile, 2026-08-17.)

(P. falciparum AMA1 profile, ~68K chars, 5 PubMed queries, 35 unique
PMIDs, abstract-level synthesis, working-docs/hitlist-profiles/
p-falciparum-ama1.md.)
