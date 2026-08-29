# Target Profile Template

> This template defines the structure for comprehensive target profiles
> in the antibody hit list project. Each profile is a durable, reusable
> record — facts about the target, not judgments about its priority.
> Prioritization scoring is applied separately, querying these profiles
> with different weights for different use cases.

## Profile fields

### 1. Target identity
- **Canonical name**: the standard protein name
- **Gene symbol**: HGNC symbol
- **UniProt ID**: primary UniProt accession
- **Protein family**: family or superfamily membership
- **Localization**: secreted / surface / intracellular (with note on antibody accessibility)
- **Molecular weight**: approximate (kDa)
- **Oligomerization**: monomer / dimer / trimer / etc.
- **Key domains**: functional domains relevant to antibody targeting

### 2. Biological mechanism
- **Primary function**: what the protein does
- **Pathway**: which signaling pathway(s)
- **Effect of blockade**: what happens when you inhibit with an antibody
- **Effect of activation**: what happens when you stimulate (if relevant)
- **Cell types expressing**: which cells produce/display the target
- **Downstream signaling**: key signaling cascades
- **Physiological role**: normal biological function
- **Species cross-reactivity notes**: human/mouse/rat/cyno conservation (relevant for preclinical)

### 3. Disease evidence
For each disease with evidence:
- **Disease**: indication name
- **Evidence type**: human genetics / clinical success / clinical failure / preclinical / mechanistic
- **Evidence summary**: 1-2 lines with key finding
- **Key references**: PMID(s) — minimum one per disease

### 4. Antibody landscape
For each known antibody (approved or in development):
- **INN / code name**: international nonproprietary name or company code
- **Company**: developer
- **Format**: naked IgG / Fab / ADC / bispecific / Fc-fusion / nanobody / etc.
- **Isotype/subclass**: IgG1 / IgG2 / IgG4 / etc.
- **Phase**: approved / Phase 3 / Phase 2 / Phase 1 / preclinical
- **Indication**: disease being treated
- **Outcome**: approved / positive / mixed / negative / withdrawn / ongoing
- **Epitope info**: known epitope description if available
- **Key reference**: PMID or approval date

### 5. Epitope landscape
- **Mapped epitopes**: known epitopes with description (linear vs conformational, domain)
- **Structural data**: PDB IDs, cryo-EM structures of antibody-target complexes
- **Neutralizing vs non-neutralizing**: which epitopes correlate with functional blockade
- **Conformational states**: does the target have conformational states that matter for epitope access?
- **Immunodominant regions**: known immunodominant epitopes (if any)
- **Epitope classification**: Type I / Type II / etc. (where applicable, e.g. CD20, EGFR)
- **Competing epitope bins**: groups of antibodies that compete for the same epitope

### 6. Known failure modes and success factors
- **Success factors**: what made winning antibodies succeed (epitope, format, dosing, population, timing)
- **Failure modes**: what went wrong with prior antibodies — with mechanism:
  - Wrong epitope (off-target or non-functional)
  - Wrong population (too late-stage, too broad, biomarker-negative)
  - Safety (on-target toxicity, off-target, immunogenicity)
  - Format (wrong isotype, wrong Fc function, wrong half-life)
  - Dosing/PK (subtherapeutic, wrong schedule)
  - Trial design (endpoint, comparator, sample size)
- **Reference**: PMID or clinical trial NCT ID for each failure/success

### 7. Assay systems
- **Functional assays**: neutralization, receptor binding, cell-based, ADCC, CDC, etc.
- **In vivo models**: animal models used to validate the target/antibody
- **Key readouts**: primary efficacy endpoints in preclinical models
- **Biomarker assays**: companion diagnostics or predictive biomarkers
- **Available cell lines**: standard cell lines for the target

### 8. Safety profile
- **Known toxicities**: on-target and off-target
- **Mechanism of toxicity**: why the toxicity occurs (if known)
- **Organ-specific**: liver, kidney, CNS, joint, cardiac, etc.
- **Managed vs unmanaged**: can the toxicity be controlled (dose, format, patient selection)?
- **Therapeutic index**: if known or estimable
- **Black box warnings**: for approved antibodies against this target
- **Clinical safety data**: key safety findings from trials

### 9. Structural information
- **Available structures**: PDB IDs for target alone and antibody-bound
- **Glycosylation**: N-linked / O-linked sites relevant to epitope access
- **Conformational states**: open/closed, active/inactive, oligomeric states
- **Epitope accessibility**: buried vs exposed, conformational vs linear
- **Membrane-proximal regions**: relevant for antibodies needing close membrane approach
- **Oligomerization interface**: if target is oligomeric, which faces are accessible

### 10. Competitive landscape
- **Pipeline depth**: number of known antibodies in development (approved + clinical + disclosed preclinical)
- **Companies involved**: key players
- **Patent landscape**: key patents (if known)
- **Market size**: approximate market for the indication (if known)
- **Gaps**: unexplored formats, epitopes, or approaches

### 11. Differentiation opportunities
*This field is judgment, clearly marked as such. It is the only field that
contains opinion rather than fact.*
- **Format differentiation**: could a different format (bispecific, ADC, conditional) improve on existing antibodies?
- **Epitope differentiation**: is there an unexplored epitope that could be functionally superior?
- **Population differentiation**: is there a biomarker-defined subset where the target would work better?
- **Mechanism differentiation**: is there a different mechanism of action (agonist vs antagonist, depleting vs blocking)?
- **Known risks**: what could go wrong with a new antibody against this target?

## Conventions
- **File naming**: `working-docs/hitlist-profiles/<target-slug>.md`
- **No frontmatter**: these are working docs, not brain pages
- **Fact vs judgment**: fields 1-10 are facts (cite PMIDs). Field 11 is judgment (clearly marked).
- **Empty fields**: acceptable — write "Unknown" or "No data" rather than speculating
- **References**: PMID in parentheses after each claim (e.g., "(PMID 12345678)")
- **Multiple diseases**: field 3 lists each disease separately with its own evidence type
- **Multiple antibodies**: field 4 lists each antibody separately
- **Tier label**: each profile header includes the tier (approved / clinical-trial / failed-clinical / preclinical) from the hit list
