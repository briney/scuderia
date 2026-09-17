# Publisher access and archive recovery

Load when publisher retrieval fails, a preview is returned, or original files
need browser access. Paper-ingest Phase 4 is the sole acceptance/closure owner.
The observations below select routes to try, not publisher-wide prohibitions
or permission to stop at an abstract.

## Routing

- Resolve the actual article URL/PII from verified metadata or DOI redirect.
  Parentheses in a DOI require shell quoting; a publisher's path need not
  equal the DOI suffix. Use original-page links for PDFs and supplements.
- If a verified PMCID exists, try XML and applicable PDF/repository routes
  under `pubmed-pmc-retrieval.md`. EPMC flags can lag; a PMCID or publisher-OA
  lead warrants an attempt even when another flag says closed.
- Try direct article/PDF access and applicable reader, authorized browser,
  mirror, or repository routes. A Jina DOI-redirect failure does not establish
  failure of the publisher's direct article URL. Jina wrappers are not JSON
  API responses or original PDF bytes. Honor service credentials/Retry-After;
  use bounded retries rather than repeatedly calling a failing endpoint.
- S2 GREEN/BRONZE URLs and Unpaywall publisher/repository locations are leads,
  not proof of retrieval. A 2026-09-05 Cell Press example was available via a
  BRONZE lead despite EPMC/Unpaywall closed flags. Contradiction requires
  checking the available copy, not choosing an index as universally correct.
- A long response can be just abstract, references, page chrome, or challenge
  HTML. Inspect the actual source body and relevant tables/figures; reject
  previews as full text. Nature thematic headings need the Nature reference,
  not a fixed Introduction/Results grep or paragraph-count threshold.

## Original-file browser route

When ordinary HTTP returns a wall, or a PDF viewer does not download, load
`web/blocked-page-recovery` Route 5 if installed. That reference owns CDP
attachment, normal navigation, download routing, bounded challenge attempts,
and cookie-bridged recovery. For publisher-specific escalation, load
`research/publisher-fulltext-workarounds/references/cdp-publisher-route-matrix.md`
when that companion is installed. Otherwise use the harness's supported
browser and the same acceptance/boundary rules; report unavailable capability.

Use one controller for a shared browser; do not take over another session.
A browser's existing institutional entitlement may expose a body that curl
cannot. Login/MFA/payment or missing entitlement is a user-action boundary,
not a CAPTCHA to bypass. Never log credentials or session cookies.

Observe the article identity and each actual attachment href. Download with
the browser's supported mechanism, verify file magic and native parsing, and
check identity/association and coverage against the article. An HTML file
named `.pdf`, or a browser page-print, is not the original manuscript. A first
HTML download can succeed after normal navigation; keep rejected and accepted
bytes distinct, and never infer cross-origin clearance. Attempt each supplement
independently, including non-PDF types. Restore any changed download routing.

## Wayback discovery and extraction

Try `https://archive.org/wayback/available?url=<encoded-article-url>` and read
the returned snapshot timestamp/URL. If needed, use CDX:
`https://web.archive.org/cdx/search/cdx?url=<encoded-url>&output=json&filter=statuscode:200&limit=5`.
Read the header row before interpreting returned columns. Try promising
snapshots with bounded retries; 200, large stored length, and a timestamp
alone do not establish full text. Preserve snapshot provenance/date and verify
the article/version rather than presenting archived content as a live page.

Try observed URL variants (`/doi/full/`, `/doi/`, `.long`, content paths),
including pre-migration domains. Remove scripts/style/chrome for reading,
but do not discard short blocks: headings, numbers, and table cells matter.
If CDX times out or returns 503, try another applicable route or report an
unavailable archive. An archive outage is never abstract-only closure.

## Bounded route observations

These summarize earlier retrieval records retained by the 2026-09 audit.
Unless a date is stated, the original run date is unavailable here. They are
not fresh tests of every article or current service availability.

| Source/pattern | Useful route or observed failure; what to check next |
|---|---|
| OUP/ATS; JCI Insight; CSHLP; AME; EMBO Press | Some PMC deposits returned metadata-only XML while EPMC PDF succeeded. EMBO EPMC XML also returned empty. Verify the individual article and representation. |
| ASCO/JCO; Taylor & Francis | PMCID→EPMC PDF worked for some articles; without one, `/doi/full/` snapshots sometimes supplied body. Taylor & Francis Jina previews can contain only chrome/abstract. Browser is another route. |
| Cell Press; JBC; JACI; Lancet | Direct article URLs using verified PIIs worked where DOI-reader routes failed. Obtain PII from the article's metadata/redirect; do not synthesize it from arbitrary DOI text. Cell Press `/fulltext/` can be free-to-read despite a closed OA flag. |
| AHA | Jina was intermittent; some articles have PMC copies. Inspect both leads. |
| Aging and Disease | Reader returned template chrome; S2 supplied a direct publisher PDF. Validate PDF content. |
| NEJM | Older post-embargo snapshots sometimes contained body; tested recent-era snapshots contained previews. Snapshot date relative to publication is a search clue, not a fixed six-month access guarantee. |
| AACR | Legacy `.long` snapshots sometimes contained body where other paths had chrome. Resolve actual domain/path and try browser access if necessary. |
| Wiley | Some 2020–2021 snapshots carried full text despite misleading OA flags. Verify version and complete body. |
| Portland Press | Legacy biochemsoctrans.org paths found snapshots missed under the migrated domain. Try both observed forms. |
| ScienceDirect | Tested snapshots contained only JS-shell/preview text. This does not rule out live browser or repository retrieval. |
| Nature family | Both complete OA/institutional bodies and subscription previews occurred. Load `nature-metadata-extraction.md`; classify the article's actual access state, not the journal name. |
| Rockefeller/JEM | Earlier HTTP/reader/archive failures were followed by a reported successful CDP retrieval. Try authorized browser access; neither success nor failure is universal. Check PMCID/embargo metadata per article, not a fixed deposit-window rule. |
| ASH/Blood; JAMA | Restricted PMC XML and missing EPMC PDFs occurred. Check remaining repository/publisher/browser leads. |
| Thieme; ADA/Diabetes | Maintenance pages, missing snapshots, or archive errors occurred. Recheck applicable live routes; these are not permanent closure. |
| AAI/J Immunol | An S2 PDF lead returned redirect HTML; legacy jimmunol.org full-text snapshots may help. Check actual bytes. |
| SAGE/Atypon | Unpaywall 422 and S2 null occurred. An API error is not a closed-access finding. |
| ProEd/Index Copernicus; Springer World J Surg; Wolters Kluwer/AAN; Karger | Prior attempts included Portico redirects, restricted XML, empty PDFs, reference-only readers, and challenges. Evaluate the specific article's remaining routes under the main closure contract. |

Never convert this table into a list of publishers that can be declared
abstract-only without attempts. Keep actual source URL, access/representation,
failed routes, and accepted provenance in the paper's Ingest log.
