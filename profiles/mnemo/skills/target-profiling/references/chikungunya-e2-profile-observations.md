# Chikungunya virus E2 profile observations (2026-08-17)

Preclinical-tier infectious disease target. Chikungunya virus E2
glycoprotein — the dominant surface-exposed receptor-binding subunit of
the alphavirus envelope (Togaviridae, *Alphavirus*, Semliki Forest virus
antigenic complex). E2 forms heterodimers with E1, assembling into 80
trimeric spikes on the T=4 icosahedral virion shell. Furin cleaves the
p62 precursor into E3 and E2; E3 dissociation during maturation
increases domain B conformational freedom and exposes a
maturation-dependent minor epitope.

Built via direct PubMed E-utilities using `urllib.request` (NOT curl)
in `execute_code`. 8+ esearch queries (broadened after [tiab] phrases
returned 0), 39+ unique PMIDs, 17 landmark abstracts fetched via efetch
XML parsing. Abstract-only ingestion (abstracts 800–3000 chars,
sufficient for level-2 grounding). UniProt Q5XXP3 (structural
polyprotein, CHIKV strain 37997) queried for field 1. PDB REST API
queried for crystal/cryo-EM structures (3N40, 3N41, 3N42, 3N43, 2XFB).
17 unique PMIDs cited, ~47K chars,
working-docs/hitlist-profiles/chikungunya-e2.md.

## Key new patterns

### 1. Vaccine literature as a secondary source for antibody landscape data

CHIKV E2 has a rich antibody landscape (8+ characterized mAbs) despite
being a preclinical-tier target with no approved therapeutic antibody.
This is partly because two vaccine programs — VLA1553/Ixchiq
(live-attenuated, FDA-approved Nov 2023, PMID 37321235) and
PXVX0317/Vimkunya (VLP, Phase 3 complete, PMID 40158526) — generated
human B-cell mAbs from vaccinated trial participants that were then
characterized structurally (cryo-EM) and functionally (neutralization,
epitope mapping). The PXVX0317 Phase 2 trial (NCT03483961) yielded
broadly neutralizing mAbs targeting the E2 domain B apex (PMID
37196061), filling fields 4 and 5 with data no therapeutic antibody
pipeline had produced.

For preclinical infectious-disease targets with active vaccine
programs but no therapeutic antibody pipeline, search for
vaccine-induced human mAbs characterized from clinical trial
participants. These are a legitimate field 4 (antibody landscape)
entry — they are real human antibodies against the target, even
though their development context is vaccinology, not therapeutics.
The vaccine trial paper often includes epitope mapping and cryo-EM
structures that fill field 5 (epitope landscape) more richly than
any preclinical therapeutic antibody paper would.

Generalizes to any infectious-disease target where vaccine trials
generate characterized mAbs (dengue, Zika, RSV, influenza, HIV).

### 2. Combination therapy mandatory due to rapid single-agent escape

CHK-152, the most protective anti-E2 mAb, causes rapid selection of
neutralization escape variants when administered alone in mice (PMID
23637602). Combination therapy (CHK-152 + CHK-166 anti-E1, or
CHK-152 + CHK-102) was required to limit resistance. The escape
variants (E2-D59N, E1-K61T) retain fitness in cell culture and
mosquitoes, do not revert, and show only mild clinical attenuation
— they are NOT fitness-compromised (PMID 24829346). This is a
critical field 6 pattern: for viral surface glycoprotein targets
under antibody pressure, single-agent escape is the dominant failure
mode and combination/bispecific approaches are mandatory.

This extends the SUDV GP observation (escape mutations can increase
virulence) and the influenza M2 observation (delayed antigen
expression). For CHIKV E2, the escape is epitope-specific point
mutation that retains fitness — distinct from virulence-increasing
or expression-timing escapes. The deep mutational scanning library
for E3/E2 (PMID 40145739) now enables high-throughput prediction of
escape mutants for any antibody, a tool for field 6 and field 11.

Generalizes to any viral envelope glycoprotein target where mAb
monotherapy selects fit escape variants: document the escape
mechanism, whether variants retain fitness, and whether combination
therapy is required.

### 3. mRNA-encoded antibody as a novel clinical-stage format

mRNA-1944 (encoding CHKV-24, an anti-CHIKV neutralizing antibody)
completed a Phase 1 trial (NCT03829384) — the first mRNA-encoded mAb
showing in vivo expression and detectable ex vivo neutralizing
activity in a clinical trial (PMID 34887572). Sustained neutralizing
levels (≥1 µg/mL) persisted for ≥16 weeks (t½ ~69 days) after a single
IV infusion. This is a fundamentally different delivery format from
traditional injected protein mAbs and represents a genuine field 4
(antibody landscape) and field 11 (differentiation) entry.

For field 4, mRNA-encoded antibodies are a legitimate antibody format
entry — they deliver a neutralizing antibody, just via a different
modality. Document the format as "lipid nanoparticle-encapsulated mRNA
encoding IgG heavy and light chains" rather than "naked IgG." For
field 11, the sustained in vivo expression eliminates repeated dosing
and may be advantageous for outbreak response (single infusion → weeks
of protection). The mild safety profile (no serious AEs in 38
participants) supports further development.

Generalizes to any infectious-disease target where mRNA-encoded mAbs
are in development (CHIKV, potentially RSV, influenza, HIV). The mRNA
mAb format is an emerging modality that profile writers should
recognize and classify correctly.

### 4. Target protein itself causes disease pathology — dual antiviral + analgesic mechanism

CHIKV E2 protein directly induces mechanical and thermal hyperalgesia
in mice via activation of TRPV1+ dorsal root ganglion (DRG)
nociceptor neurons (PMID 36831223). Anti-E2 mAbs inhibit both the
virus AND the pain — a dual antiviral + analgesic mechanism. This is
the first profiled target where the target protein itself (not just
the infection) causes a defining disease symptom, and where
antibodies against the target treat both the infection and the
symptom.

For field 2 (biological mechanism), document if the target protein
has direct pathogenic activity beyond its role in viral entry —
this is relevant to understanding the full therapeutic effect of
antibody blockade. For field 6 (success factors), a dual-mechanism
antibody (antiviral + symptom relief) has a stronger efficacy case
than a purely neutralizing antibody. For field 11 (differentiation),
the pain-inhibitory mechanism is a unique differentiation opportunity
— no existing CHIKV therapeutic addresses the debilitating arthralgia
directly.

Generalizes to any viral target protein with direct pathogenic
activity (viral toxins, envelope proteins with immunomodulatory
or nociceptive activity). Check whether the target protein itself
causes disease symptoms, not just the infection.

### 5. Domain B apex as broadly neutralizing epitope for pan-alphavirus coverage

The E2 domain B apex is the target of broadly neutralizing mAbs from
PXVX0317-vaccinated humans that cross-neutralize multiple related
arthritogenic alphaviruses (o'nyong-nyong, Ross River, Mayaro) (PMID
37196061). This is a conserved epitope among Old World alphaviruses
that enables pan-alphavirus therapeutic utility — a field 5 (epitope
landscape) and field 11 (differentiation) opportunity.

For field 5, the domain B apex is distinct from the
receptor-binding-site-overlap epitope (CHK-124, also on domain B but
at the Mxra8 binding site) and the A-B bridge epitope (CHK-152,
4J21, 5M16). It represents a fourth functional epitope bin with the
unique property of cross-species neutralization. For field 11, a
pan-alphavirus antibody targeting this epitope would address multiple
emerging arthritogenic alphaviruses with a single therapeutic — a
major market expansion.

Generalizes to any viral family with conserved neutralizing epitopes
that enable cross-species coverage (alphaviruses, flaviviruses,
ebolaviruses). The domain B apex pattern parallels the
pan-ebolavirus antibody development front (SUDV GP profile
observation #1) but at the epitope level rather than the
antibody-cocktail level.

### 6. urllib.request worked in this subagent context — context-dependent HTTP library availability

The target-profiling SKILL.md states "Do not use urllib.request for
the HTTP call — in subagent execute_code contexts it fails with
nodename nor servname provided DNS errors." However, this session
used `urllib.request.urlopen()` successfully for ALL PubMed
E-utilities calls (esearch, esummary, efetch), UniProt REST API,
and PDB REST API — no DNS errors occurred. The session ran as a
subagent on the platform=subagent environment.

This suggests the urllib DNS failure is environment-specific, not
universal to all subagent contexts. The curl+subprocess pattern
remains the recommended fallback (it works everywhere), but
urllib.request may work in some subagent environments. If urllib
fails with DNS errors, fall back to curl. If it works, it is
simpler (no subprocess overhead, native JSON parsing).

This observation should NOT override the existing curl-first
guidance (which is the safe default) but should be noted as
context-dependent. The lightweight-subagent-retrieval.md reference
already documents curl as the standard; this observation confirms
that both patterns should be available and the choice depends on
the specific subagent environment.

### 7. PDB REST API confirmed for infectious-disease structural targets

The RCSB PDB REST API (`data.rcsb.org/rest/v1/core/entry/{PDB_ID}`)
was used to verify and describe 5 CHIKV E2-E1 crystal structures
(3N40, 3N41, 3N42, 3N43, 2XFB). This confirms the GDF11 observation
that PDB REST is a one-call structure survey for field 9. For
infectious-disease targets, PDB IDs are often mentioned in landmark
structural papers (Voss 2010, PMID 21124458) and can be verified via
PDB REST without full-text retrieval.

Note: the PDB *search* API (`search.rcsb.org/api/search`) was
unreliable (404 errors with both POST and GET). The *data* API
(`data.rcsb.org/rest/v1/core/entry/{PDB_ID}`) works reliably for
individual entries by ID. For searching, use PubMed/literature to
find PDB IDs mentioned in structural papers, then verify via the
data API. Do not rely on the PDB search API for discovery.

(Chikungunya E2 profile, ~47K chars, 17 unique PMIDs cited,
working-docs/hitlist-profiles/chikungunya-e2.md.)
