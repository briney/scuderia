# IL-15 Target Profile Observations (2026-08-16)

Thirty-fifth level-2 profile (clinical-trial tier, immunology/oncology —
autoimmune disease + cancer). IL-15 is the **first dual-directional cytokine
target profile**: the same cytokine is blocked with antibodies for autoimmune
disease (RA, IBD, celiac, T1D) AND enhanced with superagonists for cancer
immunotherapy (N-803/ALT-803, NKTR-255, hetIL-15). 5 key papers ingested
(4/5 full text: 3 PMC XML OA — Trends Immunol, Immune Netw, J Hematol Oncol;
1/5 publisher-jina — Immunity/Cell Press; 1/5 abstract-only — Annual
Reviews). 80% full-text retrieval rate. ~37K chars, 5 unique PMIDs cited,
39 unique author slugs.

## Key new patterns

### (1) Dual-directional cytokine targeting — first profile with both antagonist and agonist drugs

All prior cytokine target profiles featured antibodies in a single direction:
either blocking the cytokine (anti-TNF, anti-IL-5, anti-IL-6R, anti-IL-17A)
or agonizing the pathway (IL-2 superagonist Proleukin). IL-15 is the first
target where field 4 (antibody landscape) covers BOTH antagonists (anti-IL-15
antibodies for autoimmune) AND agonists (IL-15 superagonists for cancer)
plus indirect blockade (JAK inhibitors). The dual-directional approach
requires:
- Field 2: "effect of blockade" AND "effect of activation" as equally
  important subsections.
- Field 4: three mechanistic categories — antagonists, agonists, indirect
  blockers.
- Field 6: separate failure-mode subsections for antagonist vs. agonist.
- Field 8: two distinct safety profiles (immune suppression vs. cytokine
  toxicity + leukemogenesis risk).
- Field 11: epitope-based selectivity (blocking trans-presentation vs.
  cis-signaling).

For orchestrators: when delegating a cytokine target profile, check whether
the target has both antagonist and agonist therapeutics — if so, instruct
the subagent to cover both directions in fields 2, 4, 6, 8, and 11.

### (2) Cell Press/Immunity PII URL — correct PII required for jina retrieval

PMID 30995502 (Leonard 2019, Immunity) had PII `S1074-7613(19)30145-1` in
PubMed XML. A guessed PII (`S1074-7613(19)30128-2`) returned a 404 page
(24K chars of navigation chrome). After extracting the correct PII from
the PubMed XML `<ELocationID EIdType="pii">` element, jina returned 128K
chars of full article content.

**Pitfall**: Never guess Cell Press PII URLs. Always extract the PII from
`<ELocationID EIdType="pii">` and construct the URL as
`https://www.cell.com/<journal>/fulltext/<PII>`. The DOI URL
(`doi.org/10.1016/...`) also returned 404 via jina for this article —
use the publisher article URL with the correct PII, not the DOI URL.

### (3) N-803/ALT-803 — Fc-fusion cytokine superagonist, not a conventional antibody

N-803 (formerly ALT-803, ImmunityBio) is an IL-15 superagonist: IL-15 mutein
+ IL-15Rα sushi domain + IgG1 Fc. It is NOT a conventional antibody — it is
an Fc-fusion cytokine that agonizes the IL-15 receptor. This is the first
target profile where field 4 includes an Fc-fusion cytokine as a drug entry.
Field 4's "format" and "epitope info" must be adapted for non-antibody
biologics: N-803's "epitope" is the IL-2Rβ/γc receptor complex (it binds
the receptor, not the cytokine).

### (4) Phase I clinical trial data for IL-15 superagonist (N-803 + CIML NK cells)

PMID 39948608 (Shapiro 2025) is a first-in-human Phase I trial of CIML NK
cells + N-803 ± ipilimumab in relapsed/refractory head and neck cancer
(n=11, NCT04290546). Key findings:
- Safety: 100% Grade 3-5 AEs, 1 TRAE-related death, DLT 1/10.
- Efficacy: 60% stable disease, 10% partial response (transient).
- NK cell persistence was the limiting factor.
- Ipilimumab increased early NK proliferation but reduced HLA-mismatched
  NK persistence (earlier contraction).
- IL-15 does NOT expand Tregs — the key differentiator from IL-2.

This grounds fields 3, 6, and 8 in clinical evidence rather than
preclinical-only data — the first IL-15 superagonist Phase I trial data
in the profile corpus.

### (5) Annual Reviews jina false positive — abstract + nav, not body text

PMID 10358752 (Waldmann & Tagaya 1999, Annu Rev Immunol) had no PMCID, no
OA. Jina returned 58K chars but examination revealed this was navigation
chrome + abstract (1,408 chars) + "Most Read"/"Most Cited" lists — not the
article body. The article is behind the Annual Reviews paywall.

**Pitfall**: Annual Reviews jina output can be large (50K+ chars) but
contain only the abstract and site navigation. Always verify jina output
by checking for body text markers (section headers, discussion paragraphs)
beyond the abstract. For Annual Reviews, abstract-only is the expected
outcome — the structured abstract is typically comprehensive (1,000-1,500
chars) and sufficient for profile grounding.

### (6) PubMed esearch with field tags — urllib.parse.quote handles bracket encoding

The task specified URL-encoding brackets in field tags (`[` → `%5B`, `]`
→ `%5D`). Using `urllib.parse.quote()` on the full query string handles
this automatically. When constructing PubMed esearch URLs with field tags
like `review[pt]`, use `urllib.parse.quote()` on the entire query string
rather than manually encoding individual brackets.

(IL-15 profile, ~37K chars, 5 papers, 39 unique author slugs, 5 unique
PMIDs cited, working-docs/hitlist-profiles/il-15.md.)
