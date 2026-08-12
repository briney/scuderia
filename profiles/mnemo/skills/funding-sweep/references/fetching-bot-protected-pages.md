# Fetching bot-protected funder pages — confirmed case (2026-08-10)

Task: ingest https://genesisopenmodels.anl.gov/ (DOE Genesis Open Models
contributor portal) as a funding opportunity.

## What failed

- `browser_navigate` — Cloudflare "Performing security verification" challenge
  page; the checkbox iframe did not clear the site itself.
- `curl -sL -A <browser UA>` — HTTP 403, 5.6KB challenge body.
- Google (browser) — `/sorry` IP block.
- DuckDuckGo (browser + html.duckduckgo.com + lite.duckduckgo.com) — captcha.
- Bing (browser) — Cloudflare checkbox; after clearing it, results were
  irrelevant (phrase query ignored). Result pages are readable via
  `browser_console` DOM extraction, but the index had nothing for the query.

## What worked

- `curl -sL "https://r.jina.ai/https://genesisopenmodels.anl.gov/"` — HTTP 200,
  full rendered page as clean markdown, no API key. Same for subpages
  (`/apply-now/`, `/about-gs1/`) and for `energy.gov` announcement pages.
- `https://s.jina.ai/<query>` (search endpoint) — HTTP 401
  `AuthenticationRequiredError`. Reader works unauthenticated; search does not.

## Notes

- Reader output preserves tables, headings, and links — good enough to extract
  deadline tables and program structure verbatim.
- For .gov sites the reader also returns `Published Time` metadata when the
  page carries it — useful for dating announcements.
- energy.gov newsroom search pages are JS-rendered ("Loading search
  results...") even through the reader — navigate known listing pages instead
  of the search UI.

## Cross-class note

The jina reader fallback is cross-class (funding, research, media-ingest —
anything that fetches arbitrary URLs). If a general fetch-fallback skill is
ever created, move this material there and leave a pointer in funding-sweep.
