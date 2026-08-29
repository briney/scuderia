# Zika NS1 profile observations (2026-08-17)

Infectious disease target, preclinical tier. Zika virus non-structural
protein 1 (ZIKV NS1) — a secreted flavivirus glycoprotein (~46-55 kDa
monomer, obligatory dimer, higher-order oligomers). Built via direct
PubMed E-utilities using `urllib` (not curl/subprocess — the subagent
had proper DNS access). 5 broad PubMed queries, 62 unique PMIDs, 21
landmark abstracts fetched via efetch XML parsing. Abstract-only
ingestion (no full-text retrieval — abstracts were 500-2800 chars,
sufficient for level-2 grounding). UniProt polyprotein accession Q32ZE1
used for target identity (no standalone NS1 UniProt entry). ~3.8K
words, 29 unique PMIDs cited, working-docs/hitlist-profiles/zika-ns1.md.

## Key new patterns

### 1. Secreted viral non-structural protein as antibody target — non-neutralizing but protective, no ADE risk

Zika NS1 is the first profiled target that is a **secreted viral
non-structural protein** (not a surface/entry glycoprotein like EBV
gp350, not a toxin like anthrax PA). Anti-NS1 antibodies are
**non-neutralizing** — they do not block virus entry. Protection is via
two distinct mechanisms: (a) **Fc-effector function** (ADCC/ADCP)
eliminating infected cells that surface-display NS1 (PMID 30385750,
34056709), and (b) **pathogenesis blockade** — antibodies that block
NS1-mediated endothelial dysfunction and vascular leakage (PMID
33414220). The key strategic advantage: anti-NS1 antibodies do NOT
induce antibody-dependent enhancement (ADE) of disease, unlike
anti-envelope (E) antibodies in flaviviruses (PMID 30385750, 30940710,
33414219). For field 2, document "effect of blockade" as
pathogenesis-inhibition + Fc-mediated infected-cell clearance, NOT
virus neutralization. For field 6 (success factors), the ADE
avoidance is the primary strategic advantage — state it explicitly as
the reason NS1 is preferred over E as a vaccine/therapeutic target.
For field 11, the non-neutralizing mechanism is a differentiation
opportunity (different from all anti-surface-protein antibodies that
work by neutralization). Generalizes to any flavivirus NS1 (dengue,
West Nile, Japanese encephalitis, yellow fever) and potentially to
other viruses with secreted non-structural virulence factors where
the surface/entry protein carries ADE or immunopathology risk.

### 2. NS1 oligomeric polymorphism affects antigenicity — screen against the physiologically relevant form

NS1 exists in multiple oligomeric states: dimer (membrane-associated,
essential for viral replication), tetramer (predominant form of
recombinant secreted NS1 per cryo-EM, PMID 40295651), hexamer
(classically described secreted form, trimer of dimers), and
HDL-associated (infection-derived sNS1 embedded in a high-density
lipoprotein particle, PMID 40295651, 38777094). These forms have
different antigenicity — antibodies selected against recombinant
NS1 (tetramer) may not recognize infection-derived NS1 (HDL-associated).
The skill's review (PMID 38777094) explicitly calls for a nomenclature
to distinguish rsNS1 (recombinant) from isNS1 (infection-derived) based
on the polymorphic nature affecting antigenicity. For field 9
(structural information), document all oligomeric states and their
biological context. For field 5 (epitope landscape), note which
oligomeric form was used to map each epitope. For field 11
(differentiation), flag that antibody screening should use
infection-derived NS1, not just recombinant antigen — a mismatch
between screening antigen and physiological form is a known risk. This
is structurally analogous to the CFH "plasma sink evasion" pattern
(conformational selectivity for surface-bound vs soluble form) but
specific to oligomeric-state polymorphism rather than
soluble-vs-surface conformation.

### 3. Cross-reactivity/autoimmunity duality — immunodominant antigen with autoimmune potential

NS1 is an immunodominant viral antigen, and the anti-NS1 antibody
response is characterized by cross-reactivity to self-antigens.
Anti-NS1 B cell clones show sequence features of pathogenic
autoreactive antibodies, and self-reactive clones are found in
germinal centers after both infection and immunization (PMID 34292314).
This creates a dual-use pattern: (a) NS1 is highly immunogenic —
excellent for vaccine antigen design and diagnostic test development
(robust, long-lasting antibody responses); (b) the immunodominant
response includes autoreactive clones linked to Guillain-Barré
syndrome — a safety concern for therapeutic antibodies and a risk
for NS1-based vaccines. For field 6 (failure modes), the
autoimmunity risk is the primary safety liability — state it
explicitly with PMID. For field 8 (safety), the autoantibody
cross-reactivity is the known on-target toxicity. For field 11
(differentiation), the epitope selection strategy should avoid
self-reactive epitopes — targeting non-autoreactive epitopes is a
clear differentiation opportunity. This generalizes to any viral
antigen where molecular mimicry drives autoimmunity (flavivirus NS1
and GBS, Campylobacter LOS and GBS, SARS-CoV-2 and autoimmune
manifestations).

### 4. Broad-spectrum anti-flavivirus potential via conserved NS1 epitopes

Cross-reactive antibodies targeting conserved NS1 epitopes protect
against multiple flaviviruses. The 1G5.3 antibody (cocrystallized with
both DENV and ZIKV NS1) blocks NS1-mediated cell permeability across
dengue, Zika, and West Nile viruses, and therapeutically reduces
viremia and improves survival in all three murine models — with
protection independent of Fc effector function (PMID 33414219). The
2B7 antibody simultaneously antagonizes both the NS1 wing domain (cell
binding) and β-ladder (downstream signaling), blocking endothelial
dysfunction across DENV, ZIKV, and WNV (PMID 33414220). For field 4
(antibody landscape), include cross-reactive/broad-spectrum
antibodies as a distinct category. For field 10 (competitive
landscape), broad-spectrum anti-flavivirus NS1 antibodies are a gap —
no clinical-stage broad-spectrum anti-NS1 therapeutic exists. For
field 11 (differentiation), a broad-spectrum approach (one antibody
treating dengue + Zika + West Nile) addresses a larger market than
ZIKV-only and maintains relevance despite waning ZIKV epidemic
activity. This generalizes to any viral family with conserved
non-structural proteins (flavivirus NS1, potentially coronavirus
NSP proteins, influenza NS1).

### 5. PubMed [tiab] quoted-phrase queries return 0 even when literature is abundant — drop field restriction entirely

The initial queries `"Zika NS1 antibody"[tiab]`, `"Zika
non-structural protein 1"[tiab]`, and `"Zika NS1 diagnostic"[tiab]`
ALL returned 0 hits — but plain unqualified searches (`Zika virus
NS1 antibody` without quotes or [tiab]) returned 272-453 hits each.
This is distinct from the FGF19 pattern (where the fix was boolean
queries WITH [tiab]: `FGF19[tiab] AND (antibody[tiab] OR ...)`).
Here the simplest fix was removing the field restriction entirely —
PubMed's default search handles multi-word keyword combinations
well without explicit [tiab] tags. The [tiab] + quoted-phrase
combination is the problem: PubMed's [tiab] field does not index
quoted phrases the same way the default search does. **Rule:** When
`[tiab]` quoted-phrase queries return 0, the first fallback should
be plain keyword searches (no quotes, no field tag). If those
return results, the literature exists — use the plain search. Only
if plain searches also return 0 should you construct boolean
[tiab] queries with individual term tags. This is a simpler, faster
fallback than the FGF19 boolean-construction approach and should be
tried first.

## Technical notes

- **urllib worked in this subagent context.** Unlike prior sessions
  where urllib failed with DNS errors in subagent execute_code
  contexts, this session's urllib calls succeeded. The task context
  specified "via urllib" explicitly. The skill's existing note about
  preferring curl/subprocess remains valid as a fallback, but urllib
  is not universally broken in subagent contexts — it depends on the
  environment.
- **Rate limiting (HTTP 429) encountered on 3rd query.** Solved by
  increasing sleep between calls from 1s to 5s. The ~3 req/min rate
  limit is real; batch esearch + esummary as a pair with 3-5s gaps.
- **efetch XML parsing for abstracts.** Used
  `xml.etree.ElementTree` to parse PubMed efetch XML, extracting
  AbstractText elements (including Label attributes for structured
  abstracts), ArticleTitle, author names, journal, year, and DOI.
  This is the standard lightweight retrieval pattern for
  abstract-only profiles.
- **No UniProt REST call made.** ZIKV NS1 has no standalone UniProt
  entry — it is part of the viral polyprotein (Q32ZE1). Structural
  details were sourced from the literature (crystal/cryo-EM papers)
  rather than UniProt. For viral non-structural proteins encoded
  within a polyprotein, UniProt may not provide the granular domain
  map that it does for standalone human proteins.
