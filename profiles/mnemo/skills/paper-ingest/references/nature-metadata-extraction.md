# Nature article access and metadata

Load for nature.com body/metadata extraction or an ambiguous preview. Outcomes
are article- and session-specific. Records from August–September 2026 include
complete OA bodies, subscription previews, and institutional-browser access;
none establishes a universal rule for a Nature journal or the flagship.

## Establish the actual access state

1. Resolve the article URL from verified metadata/DOI redirect. Modern paths
   often use the DOI suffix; older articles can use another local identifier.
2. Retrieve direct HTML or navigate with the authorized browser. Compare its
   title/DOI to the resolved identity. A “full access” banner is a lead, not
   proof that the extracted body includes every section.
3. Inspect `div.c-article-body` and the actual h2/h3 section structure. Nature
   articles can use thematic headings rather than Introduction/Results.
   Read body paragraphs through the article's end, check methods, captions,
   tables and supplements, and distinguish body from reference/chrome blocks.
   There is no minimum paragraph count that proves full text.
4. If HTTP gives a preview but the existing institutional session supplies
   body, extract from that live DOM rather than the saved preview. A blocked
   browser route goes through publisher-blocks and the shared browser owner;
   it does not authorize bypassing login or entitlement.

An accepted-article-in-press state (published online before the Version of
Record) has its own shape: the HTML carries abstract and page chrome but no
`data-title` body sections, the article `.pdf` URL returns the HTML shell
rather than PDF bytes, and PubMed may not yet index the DOI. Inspect the
page's own attachment links for an accepted-proof variant — a
`<suffix>_reference.pdf` path can appear alongside the standard `.pdf` —
and verify actual bytes before treating any listed URL as served. A
user-supplied accepted-version PDF is the authoritative body for this
state: label it as provided, record provenance, and do not fall back to
abstract-only closure while it is in hand.

For a genuinely partial source, use only the abstract and other actually
visible components, name their limits, and retain enrichment under the main
closure contract. An extended-data caption can support its own stated result;
it cannot license reconstruction of unseen Methods or Findings.

## Metadata and attribution

Read repeated `citation_*` metadata where present:

| Fields | Use / caveat |
|---|---|
| `citation_title`, `citation_doi`, `citation_journal_title`, `citation_article_type` | Cross-check identity and article type with structured records. |
| `citation_author`, `citation_author_institution` | Full byline and affiliation leads; do not blindly zip unequal or multi-affiliation lists. Verify associations in the author block/structured metadata. |
| `citation_publication_date`, `citation_online_date`, volume/issue/firstpage/lastpage | Distinguish online and issue dates. Online-first values such as pages 1–9 may be internal PDF pagination; omit unverified bibliographic volume/pages. |
| `citation_reference` | Reference strings may be semicolon-separated fields or free-text citations with DOI links. Preserve the literal citation; validate identifiers before dispatch. |
| `citation_pdf_url`, source attachment links | Leads for separate original-PDF/supplement attempts, not proof of download. |

ORCIDs may be author-block links or structured fields. Associate each with the
correct author; an unassigned ORCID list is not a wiring table. Check identifier
shape including a possible X checksum and retain null when not verified.

## Body, figures, and tables

Extract headings, paragraphs, and lists in source order, saving full output
before chunked reading. Preserve superscripts/subscripts, units, inequalities,
and table coordinates; distinguish exponents from citation footnotes. Regex
tag-stripping can concatenate values or truncate nested markup, so check
quantitative claims against the rendered source/PDF.

Inspect main `<figcaption>` elements and Extended Data figure sections; their
placement differs between article templates. Inspect actual `<table>` cells
or follow the observed “Full size table” links, often `/tables/<n>`. Some
reviews expose full cells only there. Neither zero inline tables nor the
presence of a table caption establishes that the table is absent or extracted.

Data/code availability, funding, author information, and references may remain
visible on paywall previews. They support those metadata claims, not a full
body claim. A large reader response containing these sections is still partial
when the scientific body is missing.

Keep source representation and route truthful: browser Nature HTML may use
`nature-browser`; direct publisher HTML/PDF uses the corresponding actual
label, with exact URL/method/version in the log. Preserve existing provenance
labels rather than relabeling prior ingests. PDF acceptance and source closure
remain in paper-ingest Phase 4.
