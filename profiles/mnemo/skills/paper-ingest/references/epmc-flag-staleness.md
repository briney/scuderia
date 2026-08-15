# Europe PMC OA-flag staleness vs PubMed PMCID

Session note (2026-08-15, Zhao 2026 ijbs.133650, PMID 42524620):

The Europe PMC core record (`EXT_ID:<PMID>&resultType=core`) reported
`isOpenAccess: N`, `inPMC: N`, `inEPMC: N`, `hasPDF: N`, `pmcid: None`
for this Ivyspring *Int J Biol Sci* eCollection article. A literal
reading of the paper-ingest Branch 0 fast-path ("when all flags are
N/None ... fall straight to branch 3") would have declared the paper
abstract-only and skipped PMC XML.

This would have been wrong. The Phase-1 PubMed XML carried
`<ArticleId IdType="pmc">PMC13412187</ArticleId>`, and
`efetch.fcgi?db=pmc&id=PMC13412187&rettype=xml` returned the complete
238 KB article XML (all 9 sections). The PMC XML was the full text;
`fulltext_source: pmc-xml` was correct and no `needs-enrichment` flag
was warranted.

## Why EPMC flags lag

Europe PMC's `isOpenAccess`/`inPMC` metadata is updated on its own
ingest cycle and is not authoritative for OA status the way a PMCID in
PubMed's own record is. For smaller/OA-native publishers (Ivyspring,
MDPI, Frontiers, Hindawi, BMC) that deposit directly to PMC, the PMC
full text is often present and fetchable before EPMC's flags catch up.
Observed: EPMC `inPMC: N` while PubMed `<ArticleId IdType="pmc">` is
populated and `efetch db=pmc` succeeds.

## Rule

**A PMCID present in the Phase-1 PubMed XML overrides stale Europe PMC
flags.** The Branch 0 gate is a *publisher-block* fast-path ("don't
round-trip a known-blocked publisher when all flags are N"), not an
*OA authority*. Whenever `<ArticleId IdType="pmc">` appears in the
PubMed XML, always attempt `efetch db=pmc` (Branch 1) before falling
to Branch 3. Only declare abstract-only when `efetch db=pmc` itself
returns front-matter-only or an error — not when EPMC merely reports N.

This mirrors the existing EPMC-PDF-render rule (Branch 1b: "Delivers
the publisher PDF even when `isOpenAccess: N`, as long as `inPMC: Y`")
but extends it to the case where EPMC reports `inPMC: N` yet PubMed's
own record carries the PMCID.
