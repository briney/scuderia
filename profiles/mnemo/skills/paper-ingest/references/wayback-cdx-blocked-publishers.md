# Wayback CDX for blocked publishers — session findings

## Summary

Three publishers previously marked "No PMCID → abstract-only (genuinely unreachable)"
in the known-blocks table were successfully retrieved via Wayback CDX API in the
CD19/CD3 bispecific profile session (2026-08-16). The common pattern: CDX finds
200-status snapshots of the publisher article page, and the archived HTML contains
the full article body (not a paywall preview), extractable via `<article>` tag regex
or full-page HTML stripping.

## Publishers and results

### Science (AAAS) — PMID 18703743 (Bargou 2008)
- **Previous skill note**: "Wayback CDX API times out"
- **CDX result**: 3 snapshots (status 200) for `science.org/doi/10.1126/science.1158545`
- **Extraction**: 268 KB HTML → 8.5K chars from `<article>` tag
- **Content level**: Full research report (Science format — short body, ~8.5K is
  expected for a 4-page Science paper). Abstract + body text + references + affiliations.
- **Tag**: `fulltext_source: wayback`

### AACR (Cancer Res) — PMID 19509221 (Baeuerle & Reinhardt 2009)
- **Previous skill note**: "No PMCID → abstract-only (genuinely unreachable)"
- **CDX result**: 5 snapshots for `/content/69/12/4941` and 4 snapshots for `.long` variant
- **Extraction**: The `.long` URL variant yielded 219 KB HTML → 26.7K chars (full review
  article body with all sections). The non-`.long` URL yielded 73 KB — mostly page chrome.
- **Key insight**: AACR `.long` URLs are the full-text view; prefer them in CDX queries.
- **Tag**: `fulltext_source: wayback`

### ASCO (JCO) — PMID 21576633 (Topp 2011)
- **Previous skill note**: Only documented EPMC PDF for PMCID-present articles; no
  fallback documented for no-PMCID articles.
- **CDX result**: 5 snapshots for `ascopubs.org/doi/<doi>` and 1 for `/doi/full/<doi>`
- **Extraction**: The `/doi/full/` variant yielded 255 KB HTML → 33.5K chars with
  complete Abstract, Introduction, Patients and Methods, Results, Discussion, References.
- **Tag**: `fulltext_source: wayback`

## Confirmed: Leukemia/Nature subscription reference-list masquerade — PMID 28028314

- `fetch_fulltext.py` returned `publisher-jina` provenance with 62K chars.
- On inspection: the entire output was the reference list (numbered entries with
  author/journal/DOI links). Zero body paragraphs. No abstract. No section headings.
- This confirms the Nature/Springer subscription "reference-list masquerade" pattern
  already documented in the known-blocks table for Nature Medicine and Springer/Drugs.
- Correctly handled as `abstract-only` with `needs-enrichment: true`.
- **Validation rule**: when jina returns content for a Nature/Springer subscription
  article, grep for section headings or body paragraphs (sentences longer than a
  reference citation) before tagging `jina-reader`. If only references, treat as
  abstract-only.

## CDX extraction recipe (Python, stdlib only)

```python
import urllib.request, urllib.parse, json, re, html as html_mod

def cdx_search(article_url):
    cdx_url = f"https://web.archive.org/cdx/search/cdx?url={urllib.parse.quote(article_url, safe='')}&output=json&limit=5&filter=statuscode:200"
    with urllib.request.urlopen(cdx_url, timeout=60) as r:
        rows = json.loads(r.read())
    return rows[1:] if len(rows) > 1 else []  # skip header row

def fetch_snapshot(article_url, timestamp):
    snap_url = f"https://web.archive.org/web/{timestamp}/{article_url}"
    with urllib.request.urlopen(snap_url, timeout=60) as r:
        return r.read().decode("utf-8", "replace")

def extract_article(html):
    # Try <article> tag first, then <main>, then full page
    match = re.search(r"<article[^>]*>(.*?)</article>", html, re.DOTALL | re.IGNORECASE)
    if match:
        html = match.group(1)
    html = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?i)</(p|div|section|article|h[1-6]|li|tr)>", "\n\n", html)
    text = re.sub(r"<[^>]+>", "", html)
    text = html_mod.unescape(text)
    lines = [" ".join(l.split()) for l in text.splitlines()]
    return "\n\n".join(l for l in lines if len(l) > 50)  # filter boilerplate

# Usage:
# snapshots = cdx_search("https://www.science.org/doi/10.1126/science.1158545")
# for snap in snapshots:
#     html = fetch_snapshot(article_url, snap[1])  # snap[1] = timestamp
#     text = extract_article(html)
#     if len(text) > 2000:
#         break
```

## General principle

The known-blocks table's "No PMCID → abstract-only" verdicts were based on specific
session observations where CDX was either not attempted or timed out. CDX API
timeouts are transient (the skill already documents this for NEJM). Before declaring
abstract-only for ANY blocked publisher, always attempt Wayback CDX with:
1. The `&filter=statuscode:200` parameter to pre-filter usable snapshots
2. Multiple URL variants (e.g., `/doi/<doi>`, `/doi/full/<doi>`, `/content/<vol>/<issue>/<page>`, `.long`)
3. A 10s retry if the first CDX call times out
4. `<article>` tag extraction, falling back to full-page HTML stripping
