---
name: tool-landscape-survey
description: Use when surveying OSS tools for a domain. Recon recipe.
triggers:
  - "survey the landscape"
  - "what tools exist for"
  - "what techniques do other projects use"
  - "landscape research"
  - "ecosystem survey"
  - "what are we missing compared to"
---

# tool-landscape-survey — reconnaissance on a tool/agent ecosystem

Ephemeral web recon: given a domain (e.g. "agent systems for literature
ingestion"), enumerate the serious projects, extract *how each one works*
(sources, identity handling, full-text access, clever techniques, known
weaknesses), and end with a ranked "what we should steal" section. Factual,
URL-cited, uncertainty flagged — never padded.

## Recon recipe (ordered)

1. **GitHub API first — it's the ground truth for OSS.**
   - Repo card: `curl -s https://api.github.com/repos/<org>/<repo>` → stars,
     `pushed_at` (staleness signal), description.
   - Directory listing (technique discovery without cloning):
     `curl -s https://api.github.com/repos/<org>/<repo>/contents/<path>` —
     e.g. a `retrievers/` or `clients/` dir listing tells you exactly which
     APIs a project queries.
   - Find the real repo: `api.github.com/search/repositories?q=<name>&sort=stars`
     — orgs move repos (OpenScholar lives under the lead author's account,
     not allenai).
   - READMEs via `raw.githubusercontent.com/<org>/<repo>/<branch>/README.md`
     (try `main` then `master`).
   - **Pitfall:** unauthenticated API ≈ 60 req/hr. Budget calls; batch;
     if rate-limited mid-run, fall back to raw files + HTML and say so.
2. **Community weaknesses — HN Algolia API, no key needed.**
   - Find threads: `https://hn.algolia.com/api/v1/search?query=<q>&tags=story`
   - Full comment trees: `https://hn.algolia.com/api/v1/items/<id>` —
     founder comments on Launch HN threads are often the *best* technical
     detail available for closed startups.
   - **Pitfall:** the items API returns JSON with raw control chars embedded
     in comment HTML — `json.loads` fails; strip `[\x00-\x1f]` (except \n)
     before parsing, or parse with `strict=False`.
3. **Package registries verify claims.** PyPI JSON API
   (`pypi.org/pypi/<pkg>/json`) confirms a package exists, its version, and
   maintenance state. A 404 on the expected name is itself a finding.
4. **Vendor blogs/docs for proprietary systems.** Fetch + strip HTML
   (`re.sub` script/style/tags, `html.unescape`, collapse whitespace).
   Engineering blogs (e.g. Elicit's) often disclose real architecture.
   **Pitfall:** Cloudflare-gated sites (Consensus) return a JS-challenge
   page — mark the system **unverified** and report only what public
   sources say, explicitly flagged. Never fill the gap with guesses.
5. **Papers for the published systems** (arXiv abstracts) — limitations
   sections are pre-written "known weaknesses."

## Output shape

Per system: (1) retrieval sources/APIs, (2) identity handling
(DOI/PMID/dedup/citation verification), (3) full-text access/paywall
strategy, (4) clever techniques worth stealing, (5) known weaknesses with
links to issues/threads. Then the money section: **"Techniques a pipeline
like ours likely does NOT already do"** — deduplicated, ranked by judged
usefulness to *our* system, each one actionable.

## Rules

- Cite a URL for every major claim; star counts and dates make claims
  checkable later.
- Distinguish verified-from-source vs inferred vs unverifiable. Say which.
- Weaknesses must come from real complaints (issues, HN, paper limitation
  sections) — not hypothesized ones.
- Don't write to the user's vault; this is recon, output goes to the
  requester.

## References

- `references/scientific-literature-agent-systems.md` — condensed 2026-08
  survey of PaperQA2, OpenScholar/ScholarQA, STORM, GPT-Researcher,
  deep-research clones, Elicit/Undermind/Consensus: their techniques and
  the ranked steal-list for a markdown-vault brain.
