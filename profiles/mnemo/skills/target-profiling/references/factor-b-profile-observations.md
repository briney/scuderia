# Factor B (CFB) — Profile Observations

> Session: 2026-08-16
> Profile: `working-docs/hitlist-profiles/factor-b.md` (~48K chars)
> Papers: 5 ingested, 4/5 PMC XML OA, 1/5 publisher-jina (Elsevier/Lancet)
> PMIDs: 40028332, 30926668, 31024533, 36897252, 33765419
> Tier: Clinical-trial | Area: Immunology/inflammation (complement)

## What makes Factor B distinctive in the profile set

Factor B is the **first complement serine protease** target profiled —
distinct from complement fragments (C5a), complement receptors (C5aR1),
and intact complement proteins (C3, C5, properdin). FB is the catalytic
subunit of the AP C3/C5 convertase (C3bBb), not a receptor or a fragment.

## Key new patterns

### 1. Zymogen-to-activate-form conformational selectivity as epitope strategy

Factor B circulates as a latent zymogen (Ba folded over Bb, active site
occluded). Upon C3b binding and FD cleavage, the Bb fragment is the active
catalytic subunit. Two clinical-stage antibodies (SAR443809/Sanofi,
NM8074/NovelMed) selectively bind Bb (activated form) but NOT latent FB.

This is a **new epitope strategy pattern**: targeting a conformational
state that only exists when the pathway is active. Benefits:
- **Lower target-mediated drug disposition** — Bb levels are much lower
  than total FB (2–3 µM), so less drug is scavenged by inert target.
- **Sustained inhibition** — NHP data: ≥90% AP inhibition for 12+ days
  after a single IV/SC dose (SAR443809), vs BID oral for small molecules.
- **Mechanism differentiation** — the antibody only acts where the AP is
  active (at sites of inflammation/disease), not systemically.

For field 5 (epitope landscape) of zymogen targets (complement proteases,
caspases, zymogen convertases), document the conformational selectivity
explicitly: "binds activated form (Xa) but not zymogen (X)." This is the
antibody equivalent of the "conformation-specific" approach used for
transthyretin (native tetramer vs amyloid fibril). (PMID 36897252.)

### 2. Small-molecule-approved, antibody-in-development target

FB is the **second profile** (after C5aR1/avacopan) where an oral small
molecule (iptacopan, Novartis) is approved and antibodies are in
clinical development (SAR443809 Ph1, NM8074 Ph2). This pattern creates a
specific competitive landscape shape:

- **The small molecule sets the efficacy bar.** Iptacopan: 82% Hb
  improvement in PNH (APPLY-PNH), 38.3% proteinuria reduction in IgAN
  (APPLAUSE). An antibody must match or exceed this.
- **The small molecule sets the convenience bar.** Iptacopan is oral
  BID. An antibody (SC/IV) must justify its route — the differentiation
  case is less frequent dosing (weekly/monthly vs BID) and sustained
  inhibition (no troughs/pharmacologic breakthrough).
- **The antibody space is clinically validated but unoccupied.** No
  anti-FB antibody is approved. The target is validated (small molecule
  succeeded), but the antibody modality is open.

For field 10 (competitive landscape) and field 11 (differentiation),
when the approved drug is a small molecule, the antibody differentiation
case is: (1) dosing frequency, (2) sustained inhibition without troughs,
(3) different safety/PK, (4) efficacy in small-molecule non-responders.
The small molecule is NOT a competitor to an antibody in the traditional
sense — it is the target validation that makes the antibody program
viable. (PMID 40028332, PMID 33765419.)

### 3. Two non-competing epitope bins on a multi-domain target

FB has two functional subunits: Ba (C3b-binding, CCP domains) and Bb
(catalytic, VWA + SP domains). Two epitope bins exist:
- **Bb-targeting** (SAR443809, NM8074) — blocks convertase catalytic
  activity. These antibodies likely compete with each other.
- **Ba-targeting** (FB28.4.2) — blocks C3b-FB binding, prevents
  convertase formation. Non-competing with Bb antibodies (different
  subunit).

This is the first profile with **non-competing epitope bins on different
subunits of the same protein** (vs same-domain competing bins like
anti-CD20 Type I vs Type II). For field 5, note the subunit basis of
epitope binning. A bispecific targeting both bins (anti-Ba × anti-Bb)
would provide dual mechanism blockade — a field 11 differentiation
opportunity. (PMID 36897252, PMID 40028332.)

### 4. Pathogenic autoantibodies as target biology (not therapeutics)

Factor B autoantibodies (FBAAs) are found in ~5–10% of C3G patients.
They stabilize (rather than inhibit) the C3 convertase — the opposite
of therapeutic antibodies. They bind Bb, like the therapeutic
candidates, but functionally activate rather than block.

For field 4 (antibody landscape), pathogenic autoantibodies are NOT
therapeutics but are evidence that: (1) Bb is immunogenic in humans,
(2) the Bb epitope is accessible to antibodies in vivo, (3) antibodies
modulating convertase activity have functional consequences (disease-
causing). This is the first profile where endogenous autoantibodies
against the target are documented — they validate the druggability of
the epitope while demonstrating that epitope selection determines
function (stabilizing vs inhibiting). (PMID 31024533.)

### 5. 4/5 PMC XML OA — high retrieval rate for complement/immunology OA journals

Four of five papers had PMC XML full text (Front Immunol ×2, PNAS, Blood
Advances — all OA). Only the Lancet Haematology Phase 2 trial (PMID
33765419) was paywalled; retrieved via publisher-jina (Elsevier
linkinghub resolved by doi.org, jina fetched the abstract + reference
list). The Lancet abstract was self-sufficient (structured with full
trial design, results, and safety data in ~1,600 chars).

For orchestrators: complement biology papers cluster in OA-friendly
journals (Front Immunol, Blood Advances, PNAS). The expected exception
is the clinical trial paper (often in Lancet/NEJM), but the structured
abstract is typically adequate. (PMID 40028332, 30926668, 31024533,
36897252, 33765419.)

### 6. PubMed search without field tags works better for complement targets

The task's specified search terms with bracket-encoded field tags
(`factor B%5Btiab%5D AND complement AND antibody AND review%5Bpt%5D`)
returned 0 results — the encoded tags were too restrictive. Broader
natural-language queries ("factor B complement alternative pathway
antibody review") returned 10 results with high relevance. Five queries
across topic areas (biology, inhibitor, therapy, disease, drug name)
yielded 39 unique PMIDs, from which the 5 best were selected.

For complement targets with common protein names (Factor B, Factor D,
properdin), natural-language esearch queries without field tags
outperform bracket-tagged queries. The field tags (especially
`[tiab]`) can over-restrict when the target name is also a common
word. (Observed: Factor B profile session, 2026-08-16.)
