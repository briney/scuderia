# Yellow fever virus E profile observations (2026-08-17)

Preclinical-tier infectious disease target. Yellow fever virus envelope
(E) protein — the class II viral fusion glycoprotein of *Orthoflavivirus*
(YFV, the prototype flavivirus). YFV is viscerotropic (hepatitis, the
"yellow" fever) with a 5–10% case-fatality rate and ~200,000 cases/year.
The live-attenuated 17D vaccine is one of the most effective ever made
but faces supply/distribution gaps; no approved therapeutic antibody exists.
One antibody (TY014) reached Phase 1 (NEJM 2020).

Built via direct PubMed E-utilities using `urllib.request` (not the
two-step curl form — `urllib.request.urlopen` works directly from
`execute_code`; no `subprocess`/`curl` needed on macOS). 8+ queries
(relevance-sorted `esearch` + `esummary` for screening, `efetch` XML for
abstracts), 59 unique PMIDs across all queries, 20 key paper abstracts
fetched and parsed. Abstract-only ingestion (no full-text retrieval — all
via `efetch` XML abstract parsing). UniProt P03314 (YFV 17D polyprotein)
queried via REST for field 1: E protein chain boundaries (residues
286–778, 493 aa), domain architecture, fusion loop (383–396),
transmembrane helices, glycosylation, receptor binding (LRP1/LRP4/VLDLR).
The WNV E profile (`west-nile-virus-e.md`) was loaded as the closest
profiled homolog for format calibration and differentiation. ~72.6K chars,
25 unique PMIDs cited,
working-docs/hitlist-profiles/yellow-fever-virus-e.md.

## Key new patterns

### 1. DIII in vivo failure — the cross-flavivirus DIII paradox

The 864-cIgG antibody (DIII-specific, humanized) neutralized YFV 17D-204
in vitro but had **zero protective capacity** in the AG129 mouse model
(PMID 27126613). This directly contrasts with West Nile virus, where
the DIII lateral ridge (DIII-lr) antibody E16 is the *most* potently
neutralizing and therapeutically effective antibody, protecting hamsters
even 5 days post-infection (PMID 16193056, PMID 17041857). For WNV,
DIII-lr is the validated therapeutic epitope; for YFV, DIII in vitro
neutralization does not guarantee in vivo protection.

This is a cross-flavivirus DIII paradox: the same domain yields the most
protective antibodies in one flavivirus (WNV) and a non-protective
antibody in another (YFV). The mechanism is unclear from the abstract
alone — possible explanations include (a) different in vivo epitope
accessibility on YFV vs WNV virions, (b) different Fc effector
requirements, or (c) the AG129 (IFN receptor-deficient) model being a
stricter test than the hamster model used for WNV E16.

**Generalizes to flavivirus E protein profiling broadly:** do not assume
that an epitope class validated in one flavivirus will transfer to
another. For each flavivirus E profile, explicitly state whether DIII
antibodies are protective in vivo, not just neutralizing in vitro. In
field 6 (failure modes), the DIII in vivo failure must be listed as a
distinct failure mode with its PMID, not generalized from other
flavivirus profiles.

### 2. The "double-lock" mechanism defines a new epitope class

The 5A antibody (PMID 30625326, Cell Reports 2019) and the YD6/YD73
antibodies (PMID 36199277, Innovation 2022) bind YFV E in **both pre-fusion
(dimer) and post-fusion (trimer) conformations**, enabling a "double-lock"
neutralization mechanism that prevents both virus attachment AND
endosomal fusion. Crystal structures were solved in both states for both
5A and YD6.

This is distinct from all previously profiled flavivirus E antibody
mechanisms: WNV E16 blocks at a post-attachment fusion step (one lock);
WNV-86 targets mature virions preferentially (binding mode, not
mechanism). The "double-lock" is a mechanistic class that cross-cuts
epitope location — 5A targets an invariant site, YD6/YD73 target the
prM-binding supersite at the dimer interface — but both share the
pre+post-fusion binding geometry.

**For field 5 (epitope landscape),** the "double-lock" class should be
listed as a distinct epitope classification category. For field 4
(antibody landscape), antibodies with solved structures in both
conformational states should be flagged. For field 11 (differentiation),
the "double-lock" mechanism is a first-in-class differentiation opportunity
that has not been clinically translated for any flavivirus.

### 3. Subdominant but vulnerable: the prM-binding supersite

The prM-binding site at the E dimer interface is a "supersite" targeted
by ultra-potent antibodies (YD6, YD73 — complete protection as both
prophylactics and therapeutics). However, these antibodies were "present
in minute traces in YFV-infected individuals but contributed significantly
to neutralization" (PMID 36199277). This is a subdominant but vulnerable
site — the opposite of the immunodominant fusion loop, which is
abundant but ADE-prone.

**Generalizes to vaccine/immunogen design:** the most therapeutically
effective epitope may be subdominant in natural infection. A profiling
pattern for field 5: note the immunodominance rank of each epitope
(dominant vs subdominant) AND its protective value. Subdominant-but-
vulnerable sites are prime epitope-based vaccine design targets because
they avoid the immunodominant ADE-prone response while targeting a
structural vulnerability.

### 4. Genotype-specific vaccine escape — structural basis for surveillance reevaluation

South American YFV strains carry amino acid changes at two sites in
central domain II and the DI-DII hinge that reduce susceptibility to
vaccine-induced antibodies (PMID 34998466, Cell Host Microbe). The 17D
vaccine is derived from an African isolate (Asibi); South American
genotypes diverge at the exact regions targeted by the neutralizing
response. A single residue (R380) in 17D E stabilizes the virion and
reduces fusion loop exposure; virulent strains have different morphology
(PMID 41006244, Nat Commun 2025 — first high-res YFV cryo-EM).

**For field 3 (disease evidence),** genotype-specific escape should be
listed as a distinct disease-evidence block (not folded into general
"preclinical" evidence). For field 6 (failure modes), the genotype
escape is a structural failure mode with a defined molecular basis
(specific DII/DI-DII hinge residues). For field 10 (competitive
landscape gaps), cross-genotype validation against South American
strains is a required gap.

**Generalizes to all flavivirus profiles:** if the vaccine strain and
circulating strains are from different genotypes/lineages, explicitly
flag the genotype gap in fields 3, 6, and 10. Check whether the vaccine
strain's E protein sequence matches circulating strains at the key
neutralizing epitopes.

### 5. urllib.request works directly — no curl subprocess needed

The session used `urllib.request.urlopen()` directly from `execute_code`
for all PubMed E-utilities and UniProt REST calls. This is simpler than
the "two-step curl form" (`urllib.parse` to build URL, `curl` via
`subprocess.run` to fetch) documented in the Sudan ebolavirus GP
observations and the `lightweight-subagent-retrieval.md` reference. Both
approaches work; `urllib.request` is pure Python with no shell dependency.

**Rate-limiting note:** PubMed E-utilities return HTTP 429 (Too Many
Requests) if queries are fired in rapid succession without sleeps. The
3–5s sleep between calls documented in the skill is necessary. When 429
is hit, a 10s wait + retry resolves it. Wrap each call in a 3-attempt
retry with exponential backoff.

### 6. UniProt standalone entry for viral polyprotein targets

UniProt P03314 (YFV 17D polyprotein) provided the complete domain map
via a single REST call: chain boundaries for all cleavage products (C,
prM, M, E at 286–778, NS1–NS5), glycosylation sites, transmembrane
helices, fusion loop region, and functional annotations including
receptor binding (LRP1, LRP4, VLDLR). This contrasts with some viral
proteins that lack standalone UniProt entries and must be grounded from
literature alone.

**Rule:** for flavivirus E proteins (and other viral structural proteins
encoded as polyprotein fragments), check for a UniProt polyprotein entry
first. The polyprotein accession provides chain boundaries, domain
annotations, glycosylation, and functional text in one call — grounding
field 1's domain/MW/topology section. The E protein's residue numbers
within the polyprotein (e.g., fusion loop at 383–396 of polyprotein =
~98–111 of E protein) must be stated in both coordinate systems to
avoid confusion with papers that use E-protein-relative numbering.
