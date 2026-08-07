# Convention: funding sources — the open-API query layer

The structured, auth-free sources where federal funding opportunities and
funding-relevant federal actions land. Two skills scan them: `monitor-the-situation`
(stateful watch for named, awaited items) and `funding-sweep` (profile-driven scan
for what fits the lab). This file is the **single source of truth** for the source
layer so the two skills never drift apart.

All bound to `fetch-url` — no code, the endpoints are the prose. Same discipline as
`literature-sweep`: bound each query to a recency window where the source supports a
date filter; diff on **stable IDs**, never on page text or HTML.

> **Conventions:** `capabilities.md` (`fetch-url`, `nih-reporter-fetch` are named
> capabilities), `_output-rules.md` (deterministic links — the resolvable URL comes
> from the API response, never reconstructed).

## The federal sources

| Source | Covers | Endpoint | Diff key |
|---|---|---|---|
| Federal Register | Rules, notices, funding-relevant federal actions | `www.federalregister.gov/api/v1/documents.json` | `document_number` |
| grants.gov | Live/forecasted federal funding opportunities (all agencies) | `api.grants.gov/v1/api/search2` (POST) | opportunity `number` |
| NIH Guide | NIH RFAs / NOFOs / notices | `search.grants.nih.gov/guide/api/data` | `docnum` |
| NIH RePORTER | Funded NIH awards (context, not opportunities) | `api.reporter.nih.gov/v2/projects/search` (POST) | `project_num` |

### Federal Register

GET with `conditions[term]` (URL-encode; wrap a phrase in `%22...%22` for exact
match), optional `conditions[agencies][]=<slug>`, and
`conditions[publication_date][gte]=<since>` to bound the window. Request only the
fields you diff on: `document_number`, `title`, `publication_date`, `agencies`,
`html_url`. The diff key is `document_number`.

Two query strengths for the same target: an **exact-phrase tripwire** (returns zero
until the event — non-zero *is* the signal) and a **broader agency-filtered net**
(catches items phrased differently). Run both; judge every new hit against the
caller's bar.

### grants.gov

POST JSON to `search2`:
`{"keyword":"...","rows":25,"oppStatuses":"forecasted|posted"}`. The keyword is a
loose full-text OR, so `hitCount` is large and noisy — **filter titles client-side**
and diff on opportunity `number`. **Match the phrase, never the bare substring:**
a bare-substring filter on "genesis" fires on `patho·genesis`. Use word-boundary
matching (`\bgenesis mission\b`, case-insensitive).

grants.gov aggregates **all federal agencies** — NSF, DOD, DOE, NIH, and more — so
it is both the Tier-1 NIH-adjacent source and the Tier-3 general federal net. Filter
by agency where the caller wants to narrow.

### NIH Guide

GET `search.grants.nih.gov/guide/api/data?query=<term>&type=active` (JSON, no auth).

**`type=active` is a required request parameter, not a response filter.** Without it
the endpoint returns only administrative `notices` (`doctype: NOT`) sorted by
relevance — never the funding opportunities. With `&type=active` it returns live
RFAs/PARs/PAs (`doctype: RFA | PAR | PA`). This is the single most important
parameter and the easiest to get wrong: omit it and the NIH funding scan silently
returns zero real opportunities.

Response shape: `data.hits.hits[]`, each with a `_source` carrying the diffable
fields — `docnum` (the RFA/PA/NOT number — **the diff key**), `title`, `doctype`,
`reldate` (release), `expdate` (**expiration — an opportunity is open until this
date, so filter on `expdate >= today`, NOT on a recent `reldate`; unlike a
publication, an active NOFO released 18 months ago is still open**), `primaryIC`,
`ac` (activity codes, e.g. `R01`, `R21`). The `query` is loose full-text, so apply
the **phrase-matching discipline below** against the title, never a bare substring.
Diff on `docnum` (`RFA-*`, `PAR-*`, `NOT-*`, `PA-*`). A weekly-TOC RSS feed exists
(`grants.nih.gov/grants/guide/newsfeed/fundingopps.xml`) as a fallback, but the
search API is preferred — structured JSON with stable IDs beats an XML parse of the
whole week.

### NIH RePORTER

POST JSON to `api.reporter.nih.gov/v2/projects/search`:
`{"criteria":{"terms":"...","fiscal_years":[...]},"limit":25}`. This returns
**funded awards, not opportunities** — it is context, not a scan target. Use it to
answer "who already holds funding in this space, under what mechanism, at what
institute" when judging fit or a Significance pitch. Diff key is `project_num`.

## Phrase-matching discipline

Every keyword source (grants.gov, NIH Guide, Federal Register `term`) is a loose
full-text OR. The precision comes from **client-side title filtering with
word-boundary matching**, not from the API. A bare-substring match is the classic
false-positive generator (`patho·genesis` for "genesis"). Always match whole phrases
against the title field, case-insensitive, before treating a hit as real.

## What this convention does not cover

- **Foundation RFP pages** — no unified API exists. Each foundation is a
  per-source scrape or RSS check, brittle and best-effort. Those live in the
  skill that scans them (`funding-sweep` Tier 2), documented per foundation, not
  here — this file is the *structured-API* layer only.
- **Eligibility judgment** — whether a hit is worth pursuing (PI status, indirect-cost
  cap, mechanism fit) is the caller's bar, not a property of the source. `funding-sweep`
  owns that in `FUNDING-PROFILE.md`.
