# Convention: bioRxiv / medRxiv preprint retrieval

**Read this before fetching a bioRxiv or medRxiv preprint** (a `10.1101/...`
DOI, or a `biorxiv.org` / `medrxiv.org` link).

`www.biorxiv.org` and `www.medrxiv.org` sit behind a Cloudflare challenge.
`fetch-url` (WebFetch / curl) against them returns an **HTTP 403 challenge
page**, not the paper — even with a browser `User-Agent`. The links that the
bioRxiv API hands back (`pdf_url`, `jatsxml`) point straight at that blocked
domain, so they are **not** fetchable either. Treat metadata and full text as
two separate retrievals through two different hosts.

## The retrieval chain

1. **Metadata + abstract — always, from the API.** GET
   `https://api.biorxiv.org/details/{biorxiv|medrxiv}/{DOI}`. Open, no auth,
   not Cloudflare-gated. Use it for identity (title, authors, date, version,
   category, `published_doi`) and the verbatim abstract. This is the
   `biorxiv-fetch` convenience over `fetch-url` (`conventions/capabilities.md`).

2. **Full text — try these, in order:**
   1. **Published version first.** If the API returns a real `published_doi`,
      the preprint has been peer-reviewed — prefer that version and resolve it
      through the normal `pubmed-fetch` / PMC open-access path. A published
      paper beats a preprint anyway (flip `status: preprint` → `published`).
   2. **Europe PMC** — the Cloudflare-free full-text route for indexed
      preprints. Resolve the DOI to a `PPR` id:
      `GET https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:"{DOI}"&format=json&resultType=core`,
      then read `fullTextUrlList` for the `pdf` "Open access" entry on
      `europepmc.org` (the `…/api/fulltextRepo?pprId={id}&type=FILE&…` URL) and
      fetch it; `https://europepmc.org/article/PPR/{id}` is the HTML form.
      Note: `…/{PPR}/{id}/fullTextXML` usually **404s for preprints** — use the
      PDF / HTML route, not the XML one.
   3. **PDF in hand via `_drop/`.** your human can open the paper in a browser
      (which solves the captcha) and drop the PDF. A PDF in `_drop/` follows
      the normal source path and `conventions/raw-source-archive.md`.

3. **Hard rule — never `fetch-url` `www.biorxiv.org` / `www.medrxiv.org`.** Do
   not request the `.full.pdf` or the `.source.xml` (`jatsxml`) URLs, and do
   not treat the API's `pdf_url` / `jatsxml` fields as fetchable. They 403.
   Hitting the 403 and giving up is the failure this convention exists to
   prevent — go to Europe PMC instead.

## Fallback when no full text is reachable

A very recent preprint may not be in Europe PMC yet, may have no published
version, and may have no dropped PDF. That is the existing abstract-only path:
distill from the API abstract, set `needs-enrichment: true`, and append an
`## Ingest log` entry — e.g. *"biorxiv full text Cloudflare-blocked; not yet in
Europe PMC; retry when indexed."* `ingest-pending-papers` /
`restructure-thin-page` complete the page once the full text is available.

## Propagating the convention

When a skill spawns a sub-agent that will fetch a preprint, point it here:

> Read `skills/conventions/preprint-retrieval.md` before fetching a bioRxiv /
> medRxiv preprint.
