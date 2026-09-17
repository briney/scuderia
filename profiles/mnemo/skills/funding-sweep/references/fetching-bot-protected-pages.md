# Fetching bot-protected funder pages — conditional fallback

Load when a configured funder's page fails normal retrieval (browser
challenge, 403 on curl, search-engine blocks). One confirmed case anchors
this guidance (2026-08-10, a DOE contributor portal); the fallback pattern
generalizes.

## What failed (dated route observations, 2026-08-10 — that one site)

- `browser_navigate` — Cloudflare challenge page; the checkbox iframe did
  not clear the site itself.
- `curl -sL -A <browser UA>` — HTTP 403, small challenge body.
- Google (browser) — `/sorry` IP block; DuckDuckGo (browser + html/lite) —
  captcha.
- Bing (browser) — Cloudflare checkbox; after clearing it, the phrase query
  was ignored (irrelevant results); result pages were readable via DOM
  extraction.

Treat these as scoped negative evidence for that site on that date, not
permanent provider-wide prohibitions — retry the normal route first on a
new page.

## What worked

- `curl -sL "https://r.jina.ai/<full-url>"` — HTTP 200, full rendered page
  as clean markdown, no API key. Also worked for subpages and for
  energy.gov announcement pages.
- The reader's search endpoint (`s.jina.ai/<query>`) — HTTP 401: the reader
  works unauthenticated; search does not.

## Notes

- Reader output preserves tables, headings, and links — good enough to
  extract deadline tables and program structure verbatim.
- For .gov sites the reader also returns `Published Time` metadata when
  present — useful for dating announcements.
- energy.gov newsroom search pages are JS-rendered ("Loading search
  results...") even through the reader — navigate known listing pages
  instead of the search UI.
- The reader fallback is cross-class (any skill fetching arbitrary URLs).
  If the active profile installs a general blocked-page-recovery skill,
  prefer it; do not assume every mnemo deployment installs one.
