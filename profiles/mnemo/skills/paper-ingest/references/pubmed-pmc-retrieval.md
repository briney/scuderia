# PubMed identity and PMC retrieval

Load for PubMed-indexed identity or a PMC source. Paper-ingest Phase 4 owns
universal source acceptance and closure; no branch failure below replaces it.
Use unique PMID/slug-prefixed files and validate identity at each transition.

## Metadata

Fetch the article's PubMed XML from E-utilities (`db=pubmed`, `id=<PMID>`,
`rettype=xml`, `retmode=xml`). The text abstract form can provide a second
readable view. Parse ArticleTitle with `itertext()` and all labeled
AbstractText elements; preserve every individual AuthorList entry, affiliations,
ORCIDs, journal/date, publication types, and correction relationships.

Scope identifiers to the article's own `PubmedData/ArticleIdList`, not all
`.//ArticleId` nodes: references can contain unrelated IDs. Use article
`ELocationID` DOI when present, then its own ArticleIdList (often needed for
older papers). The same list may carry the PII used by Elsevier/Cell Press.
Use `elink ... cmd=prlinks` for publisher links when necessary; an arbitrary
related-article result is not the article's own PMCID.

When DOI fields or indexes disagree, compare title, authors, year/version,
and publisher metadata; neither PubMed nor EPMC wins automatically. Log a
verified correction. DOI-less papers retain explicit null and source evidence.
ErratumFor/ErratumIn disambiguates a correction from the primary; CommentOn
identifies the target of an editorial, which can legitimately have no abstract.

EPMC query: `EXT_ID:<PMID> AND SRC:MED`, `resultType=core&format=json`.
Parse `resultList.result`, select the matching ID/source, and inspect DOI,
PMCID, authors/ORCIDs, `isOpenAccess`, `inPMC`, `inEPMC`, `hasPDF`, and source
URLs. URL-encode raw query parameters once. The helper uses EXT_ID alone;
verify its selected result rather than assuming the first hit is correct.
A day-old record was absent from EPMC on 2026-09-01 despite PubMed/publisher
metadata being available: empty results are unavailable evidence, not all-N.

If primary metadata is temporarily inaccessible, S2's
`graph/v1/paper/DOI:<doi>?fields=title,abstract,externalIds,authors.name,venue,publicationDate,openAccessPdf`
is a fallback candidate; cross-check the intended identity. PMID-form lookup
has returned empty in past use. GREEN/BRONZE PDF URLs are retrieval leads.

## Body and original files

1. Try PMC XML for a verified PMCID regardless of stale EPMC access flags:
   `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=<PMCID>&rettype=xml`.
   EPMC `https://www.ebi.ac.uk/europepmc/webservices/rest/<PMCID>/fullTextXML`
   is another XML route. Compare the front/article-meta title to the identity.
2. If XML is metadata-only, check whether the canonical EPMC record supplies
   a different PMCID; resolve it before retrying. Front-matter-only XML is
   one route failure, not abstract-only closure.
3. Try `https://europepmc.org/api/getPdf?pmcid=<PMCID>` when applicable,
   including some non-OA `inPMC:Y` deposits. It may fail or serve an author
   manuscript rather than publisher-final copy. Validate bytes, identity,
   version/representation, and content; never construct a PMCID from a PMID.
4. Follow article-page manuscript/supplement links independently. Observed
   PMC supplement hrefs can use `/articles/instance/<numeric-id>/bin/`, not
   a guessed legacy path. If the response is challenge HTML, load the
   article normally in the authorized browser and use the observed links.
   Keep rejected responses distinct from verified downloads.
5. When Unpaywall or another record indicates publisher OA despite EPMC all-N,
   follow that lead. A hybrid-OA Nature example was recorded 2026-09-05.
   A PMCID, repository lead, or browser entitlement still warrants its own
   route; do not infer completeness from any access flag.

The owned parser emits sections, paragraphs, and some captions, not table
cells or the bibliography; floats outside body can be omitted. Inspect the
original XML elements or PDF for load-bearing quantities. For parse repair,
reference extraction, and Cell Press caption/resource quirks, load
`skills/pmc-xml-tools/SKILL.md`. Preserve the downloaded original before repair.
