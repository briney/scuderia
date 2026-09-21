# Preprints and published conference versions

Load for arXiv, bioRxiv/medRxiv, or published-twin resolution. The main skill
owns identity, source acceptance, completeness, and integration. Do not infer
publication, version equivalence, or complete authorship from the task brief.

## arXiv metadata and version selection

Use `https://arxiv.org/abs/<id>` and its submission history. Record the
selected version and fetch its versioned abs/HTML/PDF URLs. Metadata includes
`citation_title`, repeated `citation_author` (often Family, Given), dates,
abstract, and PDF URL. Decode entities and preserve complete names. Use the
first-submission year for an arXiv-only citation; record revision dates
separately, not as a replacement publication year. A requested older version
or withdrawal investigation can require v1; never default every paper to v1.
Flag withdrawals prominently and inspect any replacement/superseding paper.

The Atom API (`export.arxiv.org/api/query?id_list=<ids>`) is an optional
structured source when available. It carries entry ID/version, title, authors,
summary, first published/updated dates, and sometimes a related journal DOI.
Map entries by returned ID, never input order. That journal DOI is not the
arXiv record's own `10.48550/arXiv.<id>` DOI; verify their relationship.
API timeouts reported in July 2026 and host restrictions in September did not
block all abs/HTML/PDF routes. Use bounded attempts, not a permanent API ban.

For arXiv DOI metadata use DataCite, e.g.
`https://api.datacite.org/dois/10.48550/arXiv.<id>`, with identity checks.
Crossref absence does not prove a DOI lacks registration: arXiv identifiers
are not generally Crossref deposits. Capture verified creator ORCIDs where
available; otherwise use null. Paperclip metadata and Jina abs-page views
are fallbacks, not stronger identity evidence than the original source.
Inspect the actual author field shape; do not assume a fixed name delimiter.

## Published twins

Check the original venue/proceedings/OpenReview record, supplemented by DBLP,
Semantic Scholar venue metadata, or OpenAlex. A brief's venue claim is a lead,
not proof; an arXiv-only index result does not prove no twin exists. Search the
title and open the primary venue record when indexes lag or block access.
A DBLP HTTP 200 bot-challenge body was observed 2026-09-16; unavailable JSON
is not a negative result. Confirm acceptance/publication rather than submission.

When the published version has its own verified DOI, prefer that identity.
The brain may already hold the preprint as a stub under the preprint DOI or
arXiv ID, and dedup run with the published identifiers can return clean
while that stub exists; search the vault for the preprint identity too and
fill the existing stub rather than creating a second page. A preprint-era
page can also hold a FULL distillation, not a stub: dedup on the published
DOI matches that page by title, and the request is a publication transition,
not a new page. Update the existing page in place — move frontmatter
status/DOI/venue/year to the published identity, keep the preprint DOI in
a `biorxiv`/`arxiv` field and the slug unchanged, add a source entry for
the accepted-version document, and append a publication note recording
what the published version changed or that content is unchanged from the
distilled preprint revision. While there, audit the preprint ingest's
author wiring: verify every byline author's ledger entry cites the page —
a preprint-era ingest can wire only a subset of the byline, with the rest
citing only a related sibling paper; backfill the missed edges. Flag
preprint-era same-person slug duplicates for entity-resolution rather than
merging mid-transition, and record the transition as a propagation event
so rem-cycle phases see the update. For a venue
without a separate article DOI, the existing convention retains
the verified arXiv DOI while recording the confirmed conference venue/year
and using that year in the slug. Log the preprint/publication distinction;
do not silently rewrite every older in-text citation. Reconcile display-name
variants against the source authors rather than creating duplicate people.
If no published twin is established, retain preprint status and the search
limitation; an inaccessible index does not justify claiming exhaustive absence.

## Proceedings repositories (ACL Anthology and similar)

Anthology-style proceedings sites serve complete metadata and open full
text: the landing page carries `citation_title`, repeated `citation_author`,
conference title, publication date, DOI, `citation_pdf_url`, and page
numbers as meta tags, plus the abstract in the page body. Use
`citation_pdf_url` rather than guessing a filename; the PDF serves with a
plain request. Watch for title variants: a landing-page H1 can differ from
the PDF title page and even from the site's own `citation_title`. The
proceedings document (PDF title page) is the authoritative title; record
the variant in the ingest log, because open indexes may carry the
landing-page H1 and a canonical-identity check will compare against it.

## Text, PDFs, and mirrors

For the selected version try direct `arxiv.org/html/<id>v<N>` and
`arxiv.org/pdf/<id>v<N>` as available. The helper may also supply a candidate
via its generic publisher route; its `--out <prefix>` remains required.
HTML is not universally available or lossless. Preserve whole text on disk
or read chunks through the end; never call a 50,000-character slice full text.
Inspect mathematical notation, table cells, conversion warnings, captions,
and appendices against the original PDF where needed. Downloading HTML does
not discharge the independent manuscript-PDF attempt.

Paperclip is an optional indexed mirror, not necessarily a local/offline
cache. Load `skills/paperclip-search/SKILL.md` when using it. Use observed IDs
(e.g. `arx_<id>`); `cat --full /papers/<id>/content.lines` supplies text.
Check body/version/authors against the original abs record. September 2026
observations included missing recent papers, abstract-length bodies, empty
author fields, and index dates mistaken for publication dates. Byte size is
only a warning signal; section content, references, and version establish
coverage. Prefer direct source retrieval when the mirror is stale. A failed
Jina proxy or missing Wayback snapshot is not source closure.

Use truthful provenance (`arxiv-html`, `arxiv-pdf`, `paperclip-arxiv`, or
the actual accepted route) and record source URL/version. Preserve historical
labels; do not call downloaded PDFs `provided-pdf`. That label is for an
input actually supplied by the user.

## bioRxiv / medRxiv

1. Resolve the full DOI through
   `https://api.biorxiv.org/details/{biorxiv|medrxiv}/<full-doi>`; inspect the
   actual collection/field shape for title, complete authors, abstract,
   date/version, and published-version DOI (often `published`). Verify a
   reported published twin before preferring it. The observed `10.64898`
   prefix uses the same bioRxiv metadata workflow; do not restrict to 10.1101.
2. Select the requested/current source version and follow its `.full.pdf`,
   HTML, and available repository links. The helper's special branch covers
   only 10.1101 and can fall back to v1; its output does not settle version.
   `source.xml` has been front-matter-only in observed bioRxiv retrievals;
   inspect body presence rather than assuming JATS implies complete text.
3. EPMC may index the preprint under a PPR record: query by DOI, then inspect
   `fullTextUrlList` for the actual repository PDF/HTML URL. PPR fullTextXML
   endpoints have returned 404; do not guess a PMC identifier for a PPR record.
4. If direct access is blocked, try applicable authorized browser, reader,
   repository, mirror, or archive routes. Reader URLs use the observed
   publisher article URL rather than a DOI redirect. Respect authentication,
   Retry-After, and bounded challenge handling from the publisher reference.
   Older Cloudflare failures do not justify forbidding all future direct
   PDF requests. Proxy-rendered PDF text is not original PDF bytes. Treat a
   Cloudflare 1015 page or a 0-byte API response as a transient rate limit,
   not a block: wait 45-60 s and retry the same direct URL before routing
   around it. Versioned URLs rate-limit independently, so one version can
   serve while another 1015s; retry the requested version after the wait
   rather than silently substituting an older one.
5. Inspect all named individual authors even if the record also has a
   collective/corporate name. Only genuinely individual-free authorship
   warrants an empty author list; the corresponding author is not a substitute
   for the full byline.

When using a preprint instead of an existing published version, retain
`needs-enrichment: true` and name the substitution. If no full text can be
obtained, record the versioned-source and alternate-route outcomes; use the
available abstract only with explicit limitations and enrichment. Report
unresolved access failures, not invented closed records or a complete ingest
whose source-check obligations remain unmet.
