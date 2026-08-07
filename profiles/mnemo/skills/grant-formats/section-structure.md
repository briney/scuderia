# Section structure — your human's within-section conventions

This file holds your human's structural conventions for individual grant sections —
paragraph-level organization, what each paragraph does, and where the prose has
flexibility vs. rigidity. It is **your human's style**, not an NIH mandate: the
mechanism files (`nih-r01.md`, `nih-r21.md`) carry package-level requirements
from the NOFO; this file carries the within-section architecture your human uses to
satisfy them.

`STYLE.md` §1 is explicit: document structure belongs to the skill side, not
the character. This file is that structure. `STYLE.md` governs how the prose
reads once the structure is set; this file governs what the structure is.

`grant-section` consults this file when drafting. `grant-coherence` consults it
when checking structural compliance — treating these as strong preferences,
not hard compliance failures (the NOFO and your human's judgment on a specific
application override them).

## Evidence base

The conventions below are inferred from 16 ingested grants with verbatim
Specific Aims text (3 funded, 13 not funded). The analysis is corpus-derived:
patterns observed across multiple proposals, not an idealized template
imposed from theory. Where funded and not-funded grants diverge in structure,
the divergence is noted. The sample is small — funded-vs-not-funded differences
are flagged as hypotheses, not conclusions.

---

## Specific Aims page

The Specific Aims page is the anchor of the application — the first section a
reviewer reads and the one every downstream section must answer to. It is
mechanism-independent: 1 page regardless of R01, R21, R03, or other NIH
mechanism.

### Canonical structure (4 blocks)

**Block 1 — Background paragraph** (1 paragraph, 5–11 sentences)

Opens the page. The problem, the gap, why current approaches fall short. Leads
with the disease or biological context, narrows to the specific scientific
challenge, and ends on the insufficiency that motivates the proposal. No
methods, no aims, no hypothesis statement — pure problem framing.

This paragraph is always present and always first (16/16 grants). It is rigid
in position, flexible in length: 4 sentences for an R21 or pilot, up to 11 for
an R01 where the background is doing more work.

**Block 2 — Goal/hypothesis + transition paragraph** (1 paragraph, 4–9
sentences)

States the overarching goal, central hypothesis, or overall hypothesis of the
project, then transitions to the aims with a phrase like "We propose the
following Specific Aims:" or "We will accomplish this through the following
Specific Aims:."

Observed in 9/16 grants as a combined goal+transition paragraph. In 4/16, the
goal/hypothesis is stated but the transition is implicit (the aims simply
follow). In 3/16, there is no explicit goal/hypothesis statement at all — the
aims follow the background with a transition phrase only.

The funded R01s in the corpus both use the combined goal+transition form: a
single paragraph that carries the hypothesis or goal statement *and* the
transition to aims. This makes the logical flow — problem → what we'll do
about it → here's how — seamless in two paragraphs. With only 3 funded grants
this is a hypothesis, not a conclusion, but it is the strongest structural
signal in the corpus.

**Flexible: goal placement.** When the background is complex or the conceptual
framing needs more setup (seen in computationally oriented proposals), the
goal/hypothesis may be deferred to a third paragraph. In these cases (3/16
grants), paragraph 2 is a continuation of the background — deepening the gap
or introducing the approach concept — and paragraph 3 carries the
goal/hypothesis and transition. This is acceptable but costs page space; the
2-paragraph form is preferred when the background can carry its weight in one
paragraph.

**Block 3 — Aim paragraphs** (one paragraph per aim, 3–5 sentences each)

Each aim is a single paragraph. The aim header is the first line, formatted as:

> **SPECIFIC AIM 1: [Concise statement of what will be done].**

The header is followed by the aim body: rationale, approach, and (optionally)
a hypothesis statement and expected outcomes. The body is 3–5 sentences
(~500–700 characters) in a single paragraph.

**Aim count.** 3 aims in 11/16 grants (the dominant pattern for R01s). 2 aims
in 3/16 (R03, R21, and one R01 with sub-aims). The Colton pilot (1/16) uses a
compressed single-paragraph format with inline aims, which is mechanism-specific
and not the NIH pattern.

**Aim body: the objective-hypothesis-approach pattern.** A newer structure
(3/16 grants, all recent) explicitly opens each aim body with three labeled
sentences: "The objective of this aim is..." → "Our hypothesis is that..." →
"Our approach is to..." This pattern is internally consistent within a grant:
if one aim uses it, all aims use it. It is not yet universal, but it is clean,
reviewer-friendly, and worth adopting as a default. The older pattern (10/16
grants) embeds the same content implicitly — the rationale, hypothesis, and
approach are present but not labeled.

**Flexible: aim body organization.** Whether the aim body uses the explicit
objective-hypothesis-approach labels or the implicit form, the content is the
same: what you'll do, why you expect it to work, and how you'll do it. The
explicit form is preferred for new grants; the implicit form is acceptable for
revisions of existing grants that already use it.

**Sub-aims.** One grant (r01ai196064) uses sub-aims (Aim 1a, 1b, 1c, 1d) within
a parent aim. This is acceptable when a single aim encompasses multiple
distinct activities that are logically grouped, but it risks reading as
over-scoped. Use sparingly.

**Block 4 — Products/outcomes paragraph** (1–2 sentences, NEW)

A brief closing paragraph after the last aim, naming the concrete products
and outcomes of the project. This block is **not yet present in the corpus**
(0/16 existing grants), and is introduced here as a new convention.

The justification is reviewer evidence, not corpus evidence. Across multiple
grants, reviewers have flagged the absence of named deliverables:

- The Ebola multi-omics R01 was scored with the explicit critique
  "insufficiently specific deliverable — the proposal reads as a
  data-gathering exercise whose actionable insight is promised but not
  concretely named." The resubmission was triaged.
- The R21 polymorphic immune locus grant received R1's "so what" critique:
  "lacks a clear articulation of the scientific significance of acquiring such
  information."
- The AbLM grants (r01ai193616, r01ai195002, r03ai199781) were repeatedly
  reviewed as "training and evaluation of a model" with an underspecified
  biological payoff.
- The paired-chain coevolution R01 (in draft) explicitly identifies this as
  the recurring critique across three study sections: "the biological
  question it answered was not stated compellingly."

The products paragraph is the structural fix. It forces the Specific Aims page
to answer "so what does the field get?" in 1–2 sentences at the bottom — not a
vague promise of future impact, but the concrete deliverable: a dataset, a
tool, a validated model, a vaccine candidate, a patent. Where the existing
corpus leaves this unsaid and lets reviewers fill in the blank (they fill it
in unfavorably), the products paragraph names it.

### What is rigid vs. flexible

| Element | Status | Notes |
|---|---|---|
| Background paragraph first | **Rigid** | 16/16 grants. Always opens the page. |
| Goal/hypothesis before aims | **Strong preference** | Present in 13/16. The 3 without it are weaker for the omission. |
| Goal + transition in one paragraph | **Preferred** | The funded R01s both do this. Defensible to split, but costs space. |
| "SPECIFIC AIM N: [title]" header format | **Rigid** | 15/16 NIH grants. The Colton pilot uses inline "Aim N:" which is mechanism-specific. |
| One paragraph per aim | **Rigid** | Universal. Never multi-paragraph aim bodies on the Aims page. |
| 3–5 sentences per aim body | **Flexible** | The range is tight (mode 4), but long aims (5 sentences) are acceptable when the approach is complex. |
| Objective-hypothesis-approach pattern in aim body | **Preferred for new grants** | 3/16 use the explicit labeled form. Clean, reviewer-friendly. Implicit form acceptable for revisions. |
| 3 aims for R01 | **Strong preference** | 11/16 grants. 2 aims seen in R03/R21 and one R01 with sub-aims. |
| Products/outcomes closing paragraph | **New convention** | Not in the corpus. Added based on recurring reviewer critiques of unnamed deliverables. |
| "SPECIFIC AIMS" title at top of page | **Flexible** | Present in 12/16. Some grants omit it; the page functions either way. |

### What the funded grants do differently

With the caveat that the funded sample is small (3 grants: 2 R01s, 1 Colton
pilot), the structural signals are:

1. **Goal + transition in one paragraph.** Both funded R01s combine the
   hypothesis/goal statement and the transition to aims into a single
   paragraph. The not-funded grants sometimes split these, sometimes omit the
   goal entirely.
2. **3 aims.** Both funded R01s have 3 aims. (The Colton pilot has 3 inline
   aims in a compressed format.)
3. **No closing paragraph.** The funded grants do not have a products
   paragraph — but neither do the not-funded grants. The products paragraph is
   a new convention motivated by reviewer critiques, not by a funded-vs-not
   difference.

### Page budget

1 page. The structure above — 2 pre-aim paragraphs (background + goal/transition)
+ 3 aim paragraphs (each ~500–700 characters) + 1 products paragraph (1–2
sentences) — fits comfortably in 1 page with standard margins (11pt, 0.5in).
The products paragraph adds ~2 lines; if the page is tight, compress the
background paragraph rather than dropping the products paragraph.

---

## Significance section (Research Strategy)

The Significance section makes the case for why the problem matters and why
solving it would advance the field. It is the first section of the Research
Strategy and is reviewed under the "Importance of the Research" factor
(`grant-formats/nih-r01.md`).

### Evidence base

13 grants with verbatim Significance text (2 funded R01s, 11 not funded). The
Ebola survey grant (r01ai187759) is excluded from the structural analysis below
because its verbatim extraction line-wrapped at ~80 chars, fragmenting
paragraphs into 25 single-line shards. The remaining 12 grants give a clean
picture of the paragraph architecture.

### Page budget

Mechanism-dependent. The Significance section shares the Research Strategy
page budget with Innovation and Approach: ~12 pages for R01, ~6 for R21, ~3 for
R03. Within that shared budget, Significance typically gets 2–4 pages for an
R01, 1–2 for an R21, and ~1 for an R03. The proportions are not mandated by the
NOFO — the division between Significance, Innovation, and Approach is your human's
choice — but they reflect what the corpus shows.

### Canonical structure (5 zones)

The Significance section is not a single argumentative arc like the Specific
Aims page. It is a **labeled-topic survey**: a sequence of paragraphs, many
with bold-label headers, each establishing one piece of the significance case.
The section moves through five functional zones, though not all grants use all
five and the order is somewhat flexible.

**Zone 1 — Disease/background (always present, always first).**

Opens the section. The disease, its global health burden, the inadequacy of
existing countermeasures. In pathogen-focused grants, this is the viral
threat, transmission, and clinical impact. In computational grants, this is
the biological problem the model addresses. 4–13 sentences, 1–3 paragraphs.

This zone is rigid in position (first) and universal (12/12 grants). It is
flexible in length: a single dense paragraph for an R03, up to 3 paragraphs for
an R01 where the epidemiological context is doing more work.

**Zone 2 — Scientific gap / problem (present in most, variable position).**

Names the specific gap the proposal addresses: what is not known, what current
approaches miss, why existing tools are insufficient. Often signposted with
"However," "Despite," "Unfortunately," or "Although." 4–10 sentences, 1–2
paragraphs.

Present in 10/12 grants. When present, it typically follows the
disease/background zone, but in some grants the gap is woven into the
background paragraphs rather than stated separately. The funded R01s both
state it explicitly.

**Zone 3 — Prior art and method landscape (present in most, uses labeled
headers).**

Surveys the existing approaches, tools, or biological knowledge that the
proposal builds on or improves upon. This is the most structurally variable
zone — its content is domain-specific (HIV bnAbs, antibody language models,
sequencing technologies, vaccine design strategies) and its paragraph count
depends on how much landscape needs establishing.

Present in 11/12 grants. Often uses bold-label headers to organize the
landscape: "HIV bnAbs.", "Predictive models of Ab sequence and structure.",
"Traditional vaccine development.", "Strategies for next-generation vaccine
development.", "Long-lived plasma cells.", "Limitations of existing AbLMs.",
"Structure-to-sequence models like ProteinMPNN...". The labels name the topic
of each paragraph, making the section scannable. This is your human's signature
structural move in the Significance section — the labeled-topic survey.

**Zone 4 — NIH-mandated paragraphs (present in most, uses fixed labels).**

Several NIH-required paragraphs appear under fixed bold-label headers, woven
into the Significance section:

- **"Rigor of prior research."** — Present in 10/12 grants. Frames the
  proposal's approach within the broader context of how the field has
  conducted rigorous prior work, and how this proposal maintains or extends
  that rigor. Not a preliminary-data section — it is about the robustness of
  the scientific premise.
- **"Investigators."** — Present in 6/12 grants. Names the team and their
  qualifications. More common in grants with multi-PI or
  multi-investigator structures; absent in single-PI grants where the
  investigator case is made elsewhere.
- **"Relevant biological variables."** — Present in 3/12 grants. Addresses
  sex as a biological variable, age, demographics, and other factors that
  NIH requires be considered.
- **"Scientific rigor."** — Present in 3/12 grants. Describes the
  methodological rigor of the proposed approach: proven methods,
  replicates, controls, statistical design.
- **"Preliminary results."** — Present in 5/12 grants as a short bulleted
  list at the end of the Significance section, summarizing key preliminary
  findings. The full preliminary data appears later in the Approach section;
  this is a teaser that demonstrates feasibility.

These paragraphs are not optional content — NIH's review instructions require
them. Their placement within Significance (as opposed to a separate section)
is your human's convention, and it is the norm for NIH applications: the Research
Strategy is a continuous document, and these labeled paragraphs are
interspersed where they best support the argument.

**Zone 5 — Preliminary results teaser (present in some, at end).**

A short bulleted list of key preliminary findings, introduced by the header
"Preliminary results." and closed by a transition sentence ("These
preliminary results, which are discussed in more detail later in this
proposal, demonstrate the feasibility of our approach..."). Present in 5/12
grants, always at the end of the Significance section, serving as a bridge to
the Approach.

### The narrative arc

The overall movement is: **disease → gap → landscape → prior art → rigor →
preliminary evidence**. The section starts broad (the problem), narrows to
the specific gap, surveys what the field has tried, establishes the rigor of
the approach, and ends with evidence that the proposed work is feasible.

Not all grants follow this exact sequence. The most common variation is the
position of the "Rigor of prior research" and "Investigators" paragraphs:
some grants place them early (after the background), others late (after the
landscape survey). The computational grants (r01ai193616, r01ai196064,
r03ai199781) tend to compress zones 2–3 into a tighter methodological
argument, while the pathogen-focused grants (arenavirus, astrovirus, CoV,
Ebola, HIV) give more space to the disease/background zone.

### What is rigid vs. flexible

| Element | Status | Notes |
|---|---|---|
| Disease/background first | **Rigid** | 12/12 grants. Always opens the section. |
| Named gap statement | **Strong preference** | 10/12. Funded grants both state it explicitly. |
| Bold-label headers for topics | **Strong preference** | 11/12 grants. The labeled-topic survey is your human's signature structure. |
| "Rigor of prior research." paragraph | **Required (NIH)** | 10/12. NIH-mandated content; the label is conventional. |
| "Investigators." paragraph | **Flexible** | 6/12. Present in multi-investigator grants; single-PI grants may omit. |
| "Preliminary results." teaser | **Flexible** | 5/12. More common in R01s where preliminary data strengthens feasibility. |
| "Relevant biological variables." | **Required (NIH)** | 3/12. NIH-mandated; the low rate likely reflects older applications. |
| "Scientific rigor." | **Required (NIH)** | 3/12. Same — increasingly required in recent applications. |
| Zone order | **Flexible** | Disease → gap → landscape is the common spine, but the NIH-mandated paragraphs can be placed where they best support the argument. |

### What the funded grants do differently

With 2 funded R01s, the sample is too small for robust claims. Two
observations, both consistent with reviewer critique patterns:

1. **Explicit gap statement.** Both funded R01s state the gap explicitly —
   "There are no FDA-approved vaccines or treatments for arenaviruses" (arenavirus
   R01) and the HIV vaccine gap framed as insufficient data for immunogen
   design (ENDURE R01). The not-funded grants that omit an explicit gap
   statement (r01ai198816, r01ai196064) received reviewer critiques about
   unclear significance or underspecified "so what."

2. **Preliminary results teaser at the end.** The arenavirus R01 (funded)
   ends with a bulleted preliminary-results list and a transition sentence.
   The ENDURE R01 (funded) does not — its preliminary data lives in the
   Approach. This split is not a funded-vs-not-funded signal; it reflects
   whether the Significance section needs a feasibility bridge to the
   Approach, which depends on the proposal.

### Reviewer critique patterns

The most common Significance-specific critique across the corpus is the
**"so what" problem** — reviewers stating that the proposal's significance is
underspecified, the deliverable is unnamed, or the biological question is
unclear. This appears in:

- r03ai199781: R2 "The central biological or functional question being
  addressed is unclear... The proposal reads as methodologically rich but
  scientifically unfocused."
- r01ai173495: "insufficiently specific deliverable — a data-gathering
  exercise whose actionable insight is promised but not concretely named."
- r21ai194140: R1 "lacks a clear articulation of the scientific significance
  of acquiring such information."
- r01ai198816: R1 "the application could more crisply quantify global HAstV
  incidence and DALYs to underscore importance."

This critique is not a structural problem — it is a content problem. But the
structure can help prevent it: the gap statement (zone 2) should name *what
the field would gain*, not just *what is missing*. The gap is not "we don't
have X" — it is "without X, we cannot do Y, and Y matters because Z." The
Significance section's job is to make Y and Z as legible as X.

---

## Innovation section (Research Strategy)

The Innovation section identifies what is new: concept, approach, methodology,
or instrumentation. It is the second section of the Research Strategy and is
reviewed under the "Importance of the Research" factor alongside Significance
(`grant-formats/nih-r01.md`). Innovation is not novelty for its own sake
(`SOUL.md` §3, novelty-premium) — it is the case that what is new is also
useful, and that the novelty is genuine, not a repackaging of established
methods.

### Evidence base

13 grants with verbatim Innovation text (2 funded R01s, 11 not funded). The
Ebola survey grant (r01ai187759) is excluded from structural analysis because
its verbatim extraction line-wrapped at ~80 chars, fragmenting paragraphs into
single-line shards. The remaining 12 grants give a clean picture.

### Page budget

Mechanism-dependent and the most variable of the three Research Strategy
sections. The Innovation section is typically the shortest — often just 1–2
pages for an R01, sometimes less. Two grants (r03ai199781, r21ai194140)
compress it to a single paragraph. The computational grants (r01ai193616,
r01ai195002, r01ai196064) tend to give it more space (2–3 paragraphs) because
the innovation claims are the methods themselves. The pathogen-focused grants
are often the most compact — their innovation is in the combination of
established tools applied to a new system, not in the tools themselves.

### Canonical structure (3 blocks)

The Innovation section is the most structurally variable of the Research
Strategy sections. Unlike Significance, which follows a consistent zone
sequence, the Innovation section adapts its structure to the type of
innovation being claimed. Three structural blocks recur, but their presence
and order depend on the proposal.

**Block 1 — Framing sentence (optional, ~1 sentence).**

Many grants open with a single framing sentence that declares the section's
scope. The most common form is a variant of:

> "This highly innovative proposal is inspired by several recent discoveries by
> our group:"

or

> "This proposal is both technically and conceptually innovative."

This sentence is present in 5/12 grants. It is always followed by the
innovation paragraphs it introduces. The framing sentence is a convention,
not a requirement — grants that omit it simply begin with the first innovation
paragraph. The grants that use it tend to be the computational ones where the
innovation is distributed across multiple distinct methodological advances.

**Flexible: whether to use the framing sentence.** Use it when there are
multiple distinct innovation points to enumerate; omit it when the innovation
is a single conceptual or methodological advance that is better stated without
preamble.

**Block 2 — Innovation paragraphs (always present, 1–6 paragraphs, often
labeled).**

The core of the section. Each paragraph describes one innovation — a method
developed by the lab, a conceptual advance, or a novel combination of
approaches. The number of innovation paragraphs varies with the proposal:

- **1 paragraph** (2/12 grants): the R03 (r03ai199781) and R21
  (r21ai194140) compress all innovation into a single paragraph. This is
  appropriate for mechanism-limited grants where the innovation is a single
  architectural or methodological choice.
- **3 paragraphs** (6/12 grants): the most common pattern. Three distinct
  innovations, each in its own paragraph.
- **4–6 paragraphs** (4/12 grants): used when the proposal combines multiple
  methodological advances from different collaborators or when the innovation
  spans several distinct tools.

Each innovation paragraph typically follows this internal structure:

1. **Name the innovation** (often a bold-label header: "mAb-maker: a structural
   ensembling framework for de novo mAb discovery.", "Electron Microscopy
   Polyclonal Epitope Mapping (EMPEM).", "StepwiseDesign: a novel in silico
   framework for Ab engineering.").
2. **What it is and what is new** (2–4 sentences): the method or concept, what
   it does, and what makes it different from existing approaches.
3. **What it enables** (1–3 sentences): what this innovation makes possible
   that was not possible before, or what it improves over the prior state.

The bold-label header pattern echoes the Significance section's labeled-topic
survey, but here the labels name innovations, not background topics. This is
the same structural move applied to a different purpose: making the section
scannable and letting each innovation stand on its own.

**Rigid: each innovation in its own paragraph.** No innovation paragraph mixes
two distinct innovations. Each gets its own paragraph and its own label.

**Block 3 — Risk-mitigation paragraph (optional, ~2–4 sentences).**

A closing paragraph that acknowledges the risk inherent in the innovative
approaches and describes how it is mitigated. The most common form is a
variant of:

> "This proposal utilizes a variety of cutting-edge methods, each is proven
> and reasonably well established, which mitigates overall risk."

or

> "To maximize our chances of success, we have provided lower risk alternative
> approaches whenever possible."

Present in 4/12 grants. More common in grants with higher-risk innovation
profiles (the computational and de novo discovery grants). The
risk-mitigation paragraph is the Innovation section's version of the
Approach section's "Potential Problems and Alternative Approaches" — but
shorter and more strategic, addressing the overall risk posture rather than
specific failure modes per aim.

**Flexible: whether to include the risk-mitigation paragraph.** Include it
when the innovation is genuinely high-risk and the mitigation is real; omit it
when the innovations are established methods applied in a new context and the
risk is obviously low.

### Two structural archetypes

The corpus falls into two archetypes based on where the innovation lives:

**Archetype A — Methodological innovation (computational grants).** The
innovations are the methods themselves: new models, new architectures, new
computational frameworks. Each innovation paragraph names a tool developed by
the lab and what it does that no existing tool does. The framing sentence is
often present. The risk-mitigation paragraph is often present. The section is
longer (3–6 paragraphs). Examples: r01ai193616, r01ai195002, r01ai196064,
r03ai199781, r01ai197993.

**Archetype B — Applied innovation (pathogen-focused grants).** The
innovations are in the application of established methods to a new system, a
new cohort, or a novel combination of tools. The innovation paragraphs name
technologies (EMPEM, antigen barcoding, structural pipelines) and what they
enable in this specific context. The framing sentence is usually absent. The
section is shorter (1–4 paragraphs). Examples: r01ai171438, r01ai192456,
r01ai198816, r01ai185017.

The distinction matters because it determines what the Innovation section
needs to prove. Archetype A must prove the method is genuinely new and not a
repackaging of existing tools — this is where the "merely training another
AbLM does not require much conceptual innovation" critique (r01ai193616, R1)
lands. Archetype B must prove the combination or application is novel and not
just "standard methods applied to a new pathogen" — this is where the
"polyclonal epitope mapping coupled with ELISA and pseudoneutralization is a
standard protocol" critique (r01ai171438, R2) lands.

### What is rigid vs. flexible

| Element | Status | Notes |
|---|---|---|
| Innovation paragraphs present | **Rigid** | 12/12. The core of the section. |
| Each innovation in its own paragraph | **Rigid** | No mixing distinct innovations in one paragraph. |
| Bold-label headers for innovations | **Strong preference** | 10/12 grants use labeled headers. The 2 that don't are single-paragraph sections. |
| Framing sentence at top | **Flexible** | 5/12. Use when enumerating multiple innovations; omit otherwise. |
| Risk-mitigation paragraph at end | **Flexible** | 4/12. Include for high-risk proposals; omit when risk is obviously low. |
| Section length | **Flexible** | 1 paragraph (R03/R21) to 6 paragraphs (R01 computational). Driven by mechanism and innovation type. |
| Section archetype (methodological vs. applied) | **Determined by proposal** | Not a choice — it follows from what the innovation is. But the section should be explicit about which archetype it is, so the innovation claim is pitched correctly. |

### What the funded grants do differently

With 2 funded R01s, the sample is small. Two observations:

1. **The arenavirus R01 (funded) uses an explicit framing sentence** that
   distinguishes "technically and conceptually innovative" and immediately
   establishes the risk posture ("we have provided lower risk alternative
   approaches whenever possible"). This frames the innovations that follow as
   bold but hedged — a combination the committee credited as "highly
   innovative overall" despite R2's note that individual methods are
   "fairly standard for the field." The framing sentence made the novelty
   argument before the reviewers could form the "standard methods" objection.

2. **The ENDURE R01 (funded) was criticized on the innovation axis** —
   Reviewers 2+3: "Multimerization schemes and adjuvant systems have been
   studied extensively in this field." The committee resume: "Innovation is
   weakened by the fact that multimerization schemes and adjuvant systems have
   been studied." The funded grant survived despite this, not because of it.
   The lesson: when the innovation is in the combination (applied
   archetype), the section must frame the *combination* as the novel unit,
   not the individual components. The ENDURE R01's Innovation section
   enumerates each component's innovation (DFM mouse, EMPEM, SMNP, ED
   immunization) but the reviewers correctly noted that the individual
   components are established. The combination — all axes in a single
   fate-mapped readout — is the genuine innovation, and the section could
   have made this case more forcefully.

### Reviewer critique patterns

Two recurring Innovation-specific critiques:

1. **"Standard methods" critique** (applied archetype). Reviewers note that
   the individual methods are established, even if the application is new.
   This is the R2 critique on the arenavirus R01 ("polyclonal epitope mapping
   coupled with ELISA and pseudoneutralization is a standard protocol") and
   the R2+3 critique on the ENDURE R01 ("multimerization schemes and adjuvant
   systems have been studied extensively"). The structural defense: when the
   innovation is a combination, the section must frame the combination as the
   innovation, not list the components as if each were individually novel.

2. **"Merely training another X" critique** (methodological archetype).
   Reviewers note that scaling or reapplying an established method is not
   innovation. This is the R1 critique on the AbLM R01 ("Primary goal is the
   generation of a very large Ab dataset using established methods") and the
   R2 critique on the sparse AbLM R03 ("The central biological or functional
   question being addressed is unclear... methodologically rich but
   scientifically unfocused"). The structural defense: the innovation
   paragraph must name what is architecturally or conceptually new, not just
   what is bigger. If the only novelty is scale, say so — and then justify
   why scale itself is the innovation (new capabilities unlocked at that
   scale, not just more of the same).

Both critiques are the innovation-section version of the "so what" pattern
seen in Significance: the reviewer is not arguing the work is bad, but that
the novelty claim has not been earned. The Innovation section's job is to earn
it — to show not just what is new, but why the new thing is a contribution the
field did not already have.

---

## Approach section (Research Strategy)

The Approach section is the experimental plan — the largest and most
substantive section of the Research Strategy. It is reviewed under the "Rigor
and Feasibility" factor (`grant-formats/nih-r01.md`) and is where the
application is won or lost: the most common reviewer critique across the
corpus targets the Approach, not Significance or Innovation.

### Evidence base

11 grants with verbatim Approach text (2 funded R01s, 9 not funded). The
Ebola survey grant (r01ai187759) is excluded — its verbatim extraction
line-wrapped at ~80 chars, fragmenting the text. The remaining 10 grants
yield 27 aims total (6 funded, 21 not funded).

### Page budget

Mechanism-dependent. The Approach section gets the largest share of the
Research Strategy page budget: ~7–9 pages for an R01 (of 12 total), ~3–4 for
an R21 (of 6 total), ~1–2 for an R03. The division between Significance,
Innovation, and Approach is your human's choice; the corpus shows Approach
consistently getting 60–75% of the available pages.

### Canonical per-aim structure (4 labeled subsections)

Each aim in the Approach section follows a recurring internal structure of
labeled subsections. The subsections are not all present in every aim, but the
sequence is consistent when they are:

**Subsection 1 — Rationale and Preliminary Data** (present in 16/27 aims).

Establishes the scientific basis for the aim: the biological or methodological
rationale, the preliminary data that supports feasibility, and the hypothesis
being tested. Often the longest subsection within an aim (50–60% of the aim's
text). Labeled as "Rationale and Preliminary Data." or "Background and
Preliminary Data." — the label varies but the function is the same.

Some aims (particularly in the computational grants) split this into two
subsections: a standalone "Rationale." paragraph followed by "Rationale and
Preliminary Data." This doubles the preliminary-data real estate but costs
space. The single-subsection form is preferred; the split is acceptable when
the conceptual rationale needs its own paragraph before the data is
introduced.

**Subsection 2 — Experimental Approach** (present in 20/27 aims).

The experimental plan: what will be done, how, and with what tools. Organized
by activity, with bold-label headers for each experimental step: "Sample
procurement and processing.", "Sequencing and annotation.", "Model training.",
"Functional evaluation of engineered bnAbs.", "Pre-filtering of Ab sequences."
The number of labeled activities varies from 2 to 9 per aim, driven by the
complexity of the experimental plan.

This subsection uses the same labeled-topic pattern seen in Significance and
Innovation — but here the labels name experimental steps, not background
topics or innovations. The pattern is consistent across the entire Research
Strategy: bold-label headers organize the content and make the section
scannable.

**Subsection 3 — Expected Outcomes / Expected Results** (present in 23/27
aims).

Names what the aim will produce. Labeled as "Expected Outcomes." or "Expected
Results." or "Anticipated Results." — the label varies, the function is the
same. Often structured as a bulleted or numbered list of concrete deliverables:
datasets (with sample counts and sequencing depths), models (with parameter
counts and architectures), engineered antibodies (with variant counts),
structures (with resolution targets).

This subsection is the Approach's version of the products/outcomes paragraph
introduced for the Specific Aims page. It answers "what does this aim
produce?" at the aim level, not the project level. The 4 aims that omit it
(2 funded, 2 not funded) are the most compressed aims in the corpus — they
weave outcomes into the Experimental Approach rather than stating them
separately.

**Subsection 4 — Potential Problems and Alternative Approaches** (present
in 20/27 aims).

Acknowledges the risks and describes alternatives. Labeled as "Potential
Problems and Alternative Approaches." or "Potential Challenges and
Alternative Approaches." or "Potential Pitfalls and Alternative Approaches."
Typically 2–5 sentences per major risk, with a specific alternative for each.

This subsection is where reviewers test whether the PI has anticipated
failure modes. The corpus pattern: name 1–3 specific risks, each with a
concrete alternative. Vague statements ("if this fails, we will try other
approaches") are a tell — reviewers flag them. The strongest pitfall sections
name the risk, explain why the alternative is feasible, and (when possible)
cite preliminary data showing the alternative has worked before.

### Subsection sequence patterns

The most common full sequence across all aims:

| Sequence | Count | Example |
|---|---|---|
| Rationale/Prelim → Experimental Approach → Outcomes → Pitfalls | 5 | r01ai195002 (all 3 aims) |
| Rationale/Prelim → Experimental Approach → Results → Pitfalls | 3 | r01ai185017 (all 3 aims) |
| Rationale/Prelim → Experimental Approach → Results → Pitfalls | 2 | r01ai193616 (both aims) |
| Background/Rationale → Experimental Approach → Results → Pitfalls | 2 | r21ai194140 (both aims) |
| Experimental Approach → Results | 2 | r01ai192456 (Aims 1–2) |
| Results → Pitfalls | 3 | r01ai198816 (all 3 aims) |

The dominant pattern (16/27 aims) is the full 4-subsection sequence:
Rationale/Prelim → Experimental Approach → Outcomes/Results → Pitfalls. Aims
that omit subsections tend to be either compressed (the ENDURE R01, where
aims are short and the rationale lives in the Significance section) or
early-draft (the arenavirus R01 Aim 1, which has no detected labels because
the subsection headers are not bold-labeled in the verbatim).

### The aim header

Each aim opens with the aim header line, formatted identically to the
Specific Aims page:

> **SPECIFIC AIM 1: [Concise statement of what will be done].**

The header is followed immediately by the first subsection. There is no
separate "Aim overview" paragraph between the header and the first labeled
subsection — the aim's narrative begins with Rationale/Preliminary Data or
Experimental Approach.

### Within-aim paragraph organization

Within each labeled subsection, paragraphs are organized by topic, often with
their own sub-labels. The Experimental Approach subsection is the most
granular: it typically has 3–9 sub-labeled paragraphs, each describing one
experimental step. The Rationale/Preliminary Data subsection is usually 1–3
paragraphs, with preliminary data figures referenced inline. The
Outcomes/Results subsection is often a bulleted list. The Pitfalls subsection
is 1–3 paragraphs, each addressing one risk.

### Aim independence

Reviewers assess whether aims are independent or serially dependent. Serial
dependency — Aim 2 requires Aim 1 to succeed — is a recurring critique
(r01ai173495: "substantial interdependency between Aims 1 and 3";
r01-paired-chain-coevolution: "Train → Benchmark → Apply... Serial
dependency; tells reviewers the enabling technology is not ready"). The
Approach section should make aim independence visible: each aim's
Rationale/Preliminary Data subsection should establish that the aim can
proceed on its own preliminary data, not on the output of a prior aim. When
aims are genuinely dependent, the dependency should be acknowledged and the
risk addressed in Pitfalls — not hidden.

### What is rigid vs. flexible

| Element | Status | Notes |
|---|---|---|
| Aim header format ("SPECIFIC AIM N: [title]") | **Rigid** | Same format as the Specific Aims page. |
| Labeled subsections within aims | **Strong preference** | 20/27 aims use labeled subsections. The 7 that don't are either early-draft or compressed. |
| Rationale/Preliminary Data subsection | **Strong preference** | 16/27 aims. Omitting it risks the "insufficient feasibility evidence" critique. |
| Experimental Approach subsection | **Strong preference** | 20/27 aims. The core of the aim. |
| Expected Outcomes/Results subsection | **Strong preference** | 23/27 aims. The aim-level version of the products paragraph. |
| Pitfalls/Alternative Approaches subsection | **Strong preference** | 20/27 aims. NIH reviewers look for this explicitly. |
| Subsection order | **Rigid when present** | Rationale → Approach → Outcomes → Pitfalls. No aim reverses this sequence. |
| Number of sub-labeled activities within Experimental Approach | **Flexible** | 2–9 per aim, driven by complexity. |
| Aim independence framing | **Strong preference** | Each aim should be self-justifying on its own preliminary data. |
| Subsection label wording | **Flexible** | "Expected Outcomes" vs "Expected Results" vs "Anticipated Results" — same function, different label. |

### What the funded grants do differently

With 2 funded R01s (6 aims), the sample is small but reveals two patterns:

1. **Compressed aims without losing substance.** The ENDURE R01 (funded) has
   the shortest aims in the corpus (4,500–5,800 chars each) but received
   Approach scores of 2, 3, and 4 — strong. Its aims omit the
   Rationale/Preliminary Data subsection because the rationale lives in the
   Significance section and the preliminary data is woven into the
   Experimental Approach. This works because the Significance section is
   unusually thorough (the longest in the corpus) and the aims are tightly
   scoped. The compression is deliberate, not an oversight.

2. **Pitfalls subsection present on the riskiest aim.** Both funded R01s
   include a Pitfalls subsection — the arenavirus R01 on Aim 3 only (the
   functional/structural characterization aim, where the cryoEMPEM innovation
   carries the most risk), and the ENDURE R01 on Aim 3 only (the dosing
   regimen aim, where the escalating-dose strategy is the most
   experimental). The funded grants do not put Pitfalls on every aim — they
   put it where the risk is, and the reviewers credit the precision.

The not-funded grants that put Pitfalls on every aim (r01ai185017,
r01ai193616, r01ai195002, r01ai195002-01) are not penalized for it — but they
are also not rewarded, because the Pitfalls content is often generic ("we
have extensive experience with this method"). The lesson: Pitfalls should
address the *specific* risks of the *specific* aim, not provide a generic
risk-mitigation paragraph.

### Reviewer critique patterns

Three recurring Approach-specific critiques:

1. **Insufficient preliminary data.** The most devastating critique in the
   corpus. The Ebola R01 (r01ai173495) was triaged because "none of the
   preliminary data included Ebola-specific results" — the methods were
   proven on other pathogens, but not the one being proposed. The fix is
   not structural — it is content: the Rationale/Preliminary Data subsection
   must include preliminary data *for the specific system being proposed*,
   not just for the methods in general.

2. **Aim interdependency.** Reviewers penalize aims that cannot proceed
   independently. The structural defense: each aim's
   Rationale/Preliminary Data subsection should establish that the aim has
   its own preliminary data, its own tools, and its own deliverable — even
   if the aims are complementary. When dependency is genuine, name it and
   address it in Pitfalls.

3. **Underspecified experimental detail.** Reviewers flag Experimental
   Approach subsections that are too high-level — "lacks detailed
   experimental plan on testing specific parameters" (r21ai194140, R2), "not
   carefully considered" (r21ai194140, R1 on ONT error rate). The
   sub-labeled activities within Experimental Approach should be specific
   enough that a reviewer can judge feasibility: which platform, which
   parameters, which controls, which sample sizes. Vague descriptions of
   proven methods are safe when the method is truly standard; they are a
   weakness when the method is being adapted or pushed to new scale.

---

## Project Summary / Abstract

The Project Summary (also called the Abstract) is a standalone document — the
first thing a reviewer reads and the only section a non-specialist program
officer or the public will see. It must be readable by a non-specialist and
must make sense without the rest of the application.

### NIH constraint

**30 lines of text.** This is an NIH-wide limit for all activity codes
(R01, R03, R21, etc.), confirmed against the live NIH Table of Page Limits
(grants.nih.gov, accessed 2026-07-30). It is a line limit, not a page limit —
the text must fit in 30 lines of standard formatting. The NOFO can override
this; confirm against the specific announcement.

### Evidence base

16 grants with verbatim Project Summary text (2 funded R01s, 1 submitted P01,
13 not funded).

### Canonical structure (3 blocks)

**Block 1 — Background and problem (1 paragraph, 4–8 sentences).**

The disease or scientific problem, its significance, and the gap the proposal
addresses. Written for a non-specialist: define terms, avoid jargon, and make
the significance legible without assuming the reader knows the field. This
paragraph mirrors the Specific Aims page's background paragraph but is pitched
at a broader audience.

Present in 16/16 grants. Always first. Rigid in position, flexible in length
(4–8 sentences, driven by how much context the non-specialist needs).

**Block 2 — Approach and aims (1 paragraph, 3–7 sentences).**

What the proposal will do and how. Two structural variants:

- **Inline aim list** (7/16 grants): the paragraph states the overarching goal
  and then lists the Specific Aims inline — "Specific Aim 1: [title]. Specific
  Aim 2: [title]." or "In Aim 1, we will... In Aim 2, we will..." This is a
  compressed version of the Specific Aims page, with the aim titles stated
  but no aim-body text. Common in computational grants and newer proposals.

- **Narrative approach** (9/16 grants): the paragraph describes the approach
  and expected outcomes without listing the aims as a structured list. The
  aims are referenced narratively ("we will perform a deep survey...") rather
  than enumerated. Common in pathogen-focused grants.

Both variants are acceptable. The inline aim list is more scannable; the
narrative approach is more readable for a non-specialist. The choice depends
on whether the aim titles themselves are self-explanatory enough to stand
alone.

**Block 3 — Public Health Relevance (1 paragraph, 2–3 sentences,
optional).**

A closing paragraph labeled "Public Health Relevance." that states the
public-health impact in plain language. Present in 6/16 grants. This paragraph
is not NIH-mandated for the Project Summary — it is a convention your human
sometimes uses, particularly in pathogen-focused grants. When present, it
echoes the Project Narrative (see below) but is pitched at the Abstract
level.

**Flexible: whether to include the Public Health Relevance paragraph.**
Include it when the public-health framing adds value for a non-specialist
reader and the 30-line budget allows. Omit it when the background paragraph
already conveys the public-health significance or when space is tight.

### What is rigid vs. flexible

| Element | Status | Notes |
|---|---|---|
| Background paragraph first | **Rigid** | 16/16 grants. |
| Approach/aims paragraph | **Rigid** | 16/16 grants. Always second. |
| Inline aim list vs. narrative approach | **Flexible** | 7/16 inline; 9/16 narrative. |
| Public Health Relevance paragraph | **Flexible** | 6/16. Not NIH-mandated for the Abstract. |
| 30-line limit | **Rigid (NIH)** | Hard limit. NOFO can override. |
| Non-specialist readability | **Rigid (NIH)** | The Abstract must be readable by a non-specialist. |

### Reviewer critique patterns

One reviewer critique directly targeted the Project Summary:

- r01ai193616: R4 "the project summary is not well written. It begins by
  implying that there is an abundance of Ab data but not enough analysis, and
  finishes by stating that Ab datasets are needed to be developed before
  models can be built. I think their point is that the current (large) datasets
  are not optimal because they are not light-heavy chained paired..."

The critique is about logical consistency: the Summary's opening (data
abundance) and closing (data needed) appear contradictory. The structural
lesson: the background paragraph and the approach paragraph must tell a
single coherent story. If the background says "we have X" and the approach
says "we need X," the reader sees a contradiction even when the nuance (we
have unpaired data but need paired data) is clear in the Research Strategy.
The Abstract does not have space for nuance — the story must be
self-consistent at the level it is told.

---

## Project Narrative

The Project Narrative is a 3-sentence public-health relevance statement. It
is the plainest-language piece of the application — written for a lay audience,
not for a scientist.

### NIH constraint

**Three sentences.** NIH-wide for all activity codes (excluding C06, UC6, G20).
Confirmed against the live NIH Table of Page Limits (grants.nih.gov, accessed
2026-07-30). This is a sentence limit, not a line or page limit — exactly
three sentences.

### Evidence base

16 grants with verbatim Project Narrative text (2 funded R01s, 1 submitted
P01, 13 not funded).

### Canonical structure (3 sentences)

The Narrative is too short for a multi-paragraph structure. It is three
sentences that together answer: why does this matter for public health?

The corpus shows a consistent 3-sentence arc:

**Sentence 1 — The problem (1 sentence).** Names the disease or scientific
challenge in plain language. Often opens with the pathogen or condition name
and its health impact. "HIV is an extremely challenging target for vaccine
development due to its ability to rapidly mutate and evade the human immune
system." / "Human arenaviruses cause devastating hemorrhagic fever disease
that results in thousands of deaths every year." / "Viral diarrheal diseases
cause significant suffering worldwide, particularly among children."

**Sentence 2 — The approach (1 sentence).** What the proposal will do about
it, in plain language. "In this proposal, we will use sophisticated AI models
to better understand targetable features of immature precursors of broadly
neutralizing antibodies." / "Using a singular cohort of Lassa fever survivors
in Eastern Sierra Leone, we will perform a detailed survey of the human
antibody response to arenavirus infection."

**Sentence 3 — The payoff (1 sentence).** What the field gains — the
translational or public-health outcome. "to better understand viral
mechanisms of immune evasion and to identify conserved sites of viral
vulnerability which can be exploited by the immune system." / "and the most
efficient developmental routes toward broad neutralization."

This 3-sentence arc (problem → approach → payoff) is present in 13/16
grants. The 3 grants that exceed 3 sentences (r01ai178165 at 5, r01ai180120
at 4, r01ai196064 at 4) are not violating the NIH limit by intent — they
use longer, compound sentences that the regex sentence-splitter counts as
multiple sentences. But the structure is the same: problem → approach →
payoff.

### What is rigid vs. flexible

| Element | Status | Notes |
|---|---|---|
| Three sentences | **Rigid (NIH)** | Hard limit for all activity codes (excl. C06, UC6, G20). |
| Problem → approach → payoff arc | **Strong preference** | 13/16 grants follow this arc cleanly. The 3 that deviate still follow it loosely. |
| Plain language (lay audience) | **Rigid (NIH)** | The Narrative must be readable by a non-scientist. |
| "Public Health Relevance" label | **Not used** | 0/16 grants include this label in the Narrative itself. (The label appears in the Abstract, not the Narrative.) |

### What the funded grants do differently

Both funded R01s have exactly 3 sentences, following the problem → approach
→ payoff arc cleanly. The not-funded grants that exceed 3 sentences
(r01ai178165 at 5, r01ai180120 at 4, r01ai196064 at 4) are not penalized for
it — the NIH limit is about the submitted document, and these may have been
edited down in the final submission. But the structural observation holds:
the funded grants are the most compressed, with no wasted words.

The funded Narratives are also the shortest in character count (598 and 737
chars), suggesting that the funded versions are the most tightly edited. The
not-funded Narratives range from 582 to 1092 chars, with the longer ones
risking the 3-sentence limit by using compound or run-on constructions.

### Relationship to the Project Summary

The Narrative and the Summary's Public Health Relevance paragraph (when
present) cover the same ground — public-health impact in plain language. They
should not be identical. The Summary's PHR paragraph is a condensed version
pitched at the Abstract level (2–3 sentences within the 30-line budget); the
Narrative is a standalone 3-sentence statement. The two can share language
but should not be copy-pasted — the Narrative should be more specific about
the public-health payoff, the Summary's PHR more integrated with the
scientific narrative.
