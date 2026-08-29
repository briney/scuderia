# Sudan ebolavirus GP profile observations (2026-08-17)

Preclinical-tier infectious disease target. Sudan virus glycoprotein
(SUDV GP) — the surface class I fusion glycoprotein of *Orthoebolavirus
sudanense*, structural homolog of EBOV (Zaire) GP but antigenically
distinct. No approved SUDV vaccine or therapeutic; the FDA-approved EBOV
antibodies (ansuvimab, REGN-EB3/Inmazeb) are ineffective against SUDV.
Built via direct PubMed E-utilities using the two-step curl form
(`urllib.parse` to build the URL, `curl` via `subprocess.run` to fetch).
5 queries, 34 unique PMIDs, 12 abstracts fetched via efetch XML parsing.
Abstract-only ingestion (abstracts 800–3100 chars, sufficient for
level-2 grounding). UniProt Q66814 (standalone reviewed entry) used for
field 1. 18 unique PMIDs cited, ~35K chars,
working-docs/hitlist-profiles/sudan-ebolavirus-gp.md.

## Key new patterns

### 1. Read the already-profiled homolog first — format + differentiation axis

SUDV GP is structurally homologous to EBOV GP, for which an approved-tier
profile already existed (`ebola-gp.md`). Loading that profile before writing
provided two things no PubMed search could: (a) exact field-depth/format
calibration (how many antibodies per field 4, how granular the epitope bins
in field 5, how field 3 framed the PALM trial), and (b) the differentiation
axis — every field could contrast SUDV GP against the already-characterized
EBOV GP. The central unmet-need narrative ("approved EBOV antibodies are
ineffective against SUDV; pan-ebolavirus antibodies are the active
development front") came directly from reading the EBOV profile's field 4
(ansuvimab, REGN-EB3) and field 2 (species cross-reactivity note that
mAb114 does not cross-neutralize other species).

For field 1, the domain map (GP1 RBD/glycan cap/MLD, GP2 fusion loop/HR/
transmembrane), oligomerization (trimer), and the native-vs-cleaved GP
conformational axis were all transferable from the EBOV profile with SUDV
UniProt confirmation. This roughly halved the work of fields 1, 2, and 5.

Generalizes to any target family with an already-profiled close homolog:
ebolaviruses (EBOV→SUDV→BDBV), flaviviruses (dengue-E / zika-E / dengue-NS1 /
zika-NS1), integrin family members, chemokine receptors, Fc-gamma receptors.
Rule: before profiling a target, grep `working-docs/hitlist-profiles/` for
its family and load the closest profiled homolog. Contrast throughout
rather than starting from scratch.

### 2. Preclinical-tier infectious-disease target with no approved therapy → field 3 organized by model tier, not trial phase

The TEMPLATE.md field 3 ("Disease evidence") is implicitly shaped around
clinical evidence types (human genetics / clinical success / clinical
failure / preclinical / mechanistic). For an approved-tier target like
EBOV GP, field 3 led with the PALM randomized controlled trial. For SUDV
GP — no approved therapy, no clinical trial — field 3 was restructured by
preclinical model tier: (1) SUDV-specific cocktail in NHP, (2) pan-
ebolavirus cocktails in NHP/ferret, (3) cross-reactive antibodies in
rodent models, (4) mechanistic/structural evidence. Each tier carries its
own evidence weight and its own PMID.

This is the structural pattern for any preclinical-tier infectious-disease
target: organize field 3 as a descending model-tier ladder (NHP → ferret
→ rodent → mechanistic), since there is no clinical trial to anchor it.
State the unmet-need ("no approved therapy/vaccine for SUDV") explicitly
in the first disease-evidence block — it is the field's organizing
principle, not an aside.

### 3. Conserved epitope ≠ cross-species neutralization — validate against the target species

BDBV223 (from a Bundibugyo survivor) targets the GP2 stalk, which is the
most sequence-conserved region across ebolaviruses — the rationale for
stalk-directed antibody design. Yet BDBV223 neutralizes BDBV and EBOV but
NOT SUDV, despite stalk conservation (PMID 30996276). The crystal structure
showed the binding interferes with trimeric bundle assembly and stabilizes
a conformation separating GP monomers, but targeted mutagenesis to enhance
SUDV GP recognition indicated additional determinants lie outside the
visualized interactions — likely involving quaternary assembly or
membrane-interacting regions.

For field 5 (epitope landscape), conservation at the sequence/structural
level does not guarantee functional breadth against a given species. For
field 6 (failure modes), "conserved epitope but species-specific
non-neutralization" is a distinct failure category that cannot be fixed by
epitope optimization alone — it requires engineering the additional
(quaternary/membrane) determinants. For field 11 (differentiation), the
unexploited opportunity is to engineer stalk antibodies for SUDV
recognition by targeting the determinants BDBV223 lacks. Generalizes to
any conserved-epitope antibody strategy across a viral family: validate
against each species; do not assume conservation confers breadth.

### 4. UniProt REST grounds field 1 for standalone viral glycoproteins

SUDV GP has a standalone reviewed UniProt entry (Q66814) providing domain
regions (RBD 54–201, mucin-like 305–485, fusion peptide 524–539),
12 N-linked glycosylation sites, molecular weight (~75 kDa, 676 aa),
and topology (extracellular 33–650, transmembrane 651–671, cytoplasmic
672–676). A single `curl https://rest.uniprot.org/uniprotkb/Q66814.json`
call grounded field 1 (and field 9 glycosylation) concretely beyond what
abstracts provided.

This contrasts with the ZIKV NS1 profile, where no UniProt REST call was
made because NS1 is encoded within the viral polyprotein (Q32ZE1) with no
standalone entry — field 1 was sourced from literature instead (see
zika-ns1-profile-observations.md). Rule: for viral surface/structural
proteins, check for a standalone UniProt entry first (`rest.uniprot.org/
uniprotkb/search?query=<virus> <protein>+AND+reviewed:true`); if one
exists, a single REST call grounds field 1's domain/MW/glycosylation/
topology. Fall back to literature only for polyprotein-encoded fragments
with no standalone entry.

### 5. GP fusion-loop escape mutation under antibody pressure — a GP-targeted antibody escape mechanism

In an EBOV-infected, mAb-treated NHP, a single GP fusion-loop mutation
resisted antibody-mediated neutralization AND increased viral growth
kinetics and virulence, contributing to atypical/persistent disease
(PMID 33436428). This is a documented GP-targeted antibody escape
mechanism relevant to any ebolavirus GP antibody, including SUDV.

For field 6 (failure modes), GP fusion-loop escape is a distinct category
from the M2 "delayed antigen expression" escape (influenza-m2 observations)
— here the epitope itself mutates under pressure, selecting more-virulent
variants. For field 11 (differentiation), this motivates multi-epitope
cocktail design (pair non-overlapping bins, as RIID F6-H2 and the pan-
ebolavirus cocktails do) to resist escape. Generalizes to any viral
surface glycoprotein where a single epitope is under antibody pressure:
escape mutations can increase virulence, not just evade neutralization,
making cocktail breadth a safety requirement, not only an efficacy
strategy.

## Technical notes

- **Two-step curl form worked cleanly.** `urllib.parse.quote` to build the
  esearch URL, `subprocess.run(["curl","-sS","--max-time","30",url],...)`
  to fetch. No DNS errors (unlike some prior subagent `urllib.request`
  failures), no HTTP 429 rate limits at 4–5 s sleeps across 5 esearch +
  1 esummary + 1 efetch calls. The skill's note about preferring
  curl/subprocess remains valid; urllib.request was not attempted.
- **efetch XML for abstracts.** `efetch.fcgi?db=pubmed&id=<csv>&rettype=
  abstract&retmode=xml` parsed with `xml.etree.ElementTree`, extracting
  AbstractText (including Label attributes for structured abstracts),
  ArticleTitle, authors, journal, year, DOI. Standard lightweight
  retrieval pattern for abstract-only profiles.
- **esummary title scoring for landmark selection.** After 34 unique
  PMIDs, esummary titles were keyword-scored (sudan/ebola/gp/monoclonal/
  neutraliz/cocktail) to rank and select 12 landmark abstracts. Effective
  for triage when the PMID pool exceeds the fetch budget.
- **No dedicated SUDV GP–antibody co-structure in the retrieved set.**
  Fields 5 and 9 (epitope/structural) were grounded by analogy to the
  extensively structurally characterized EBOV GP (see ebola-gp.md, PDB
  7TN9 et al.) plus cross-reactive antibody structures that include
  SUDV-relevant data (BDBV223 stalk, rEBOV-515/442, mAb 11886 bridging
  epitope). A dedicated SUDV GP–antibody complex structure would further
  strengthen fields 5 and 9.
