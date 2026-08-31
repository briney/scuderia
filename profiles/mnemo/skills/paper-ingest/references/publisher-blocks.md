# Publisher-specific retrieval behavior

Consult this reference when a publisher blocks the general retrieval tree
(Phase 4 of paper-ingest). The general decision for ANY publisher:

1. PMCID present → try PMC XML → EPMC PDF render → Wayback CDX
2. No PMCID → try jina reader on publisher URL → Wayback CDX → abstract-only
3. Before declaring abstract-only: check paperclip mirror (bioRxiv/arXiv),
   check S2 `openAccessPdf` (GREEN = lead to chase), validate body presence

**Reference-list masquerade** (applies to all subscription Springer/Nature/
Wolters Kluwer content): jina returns 50K+ chars that passes the size check
but the content is entirely reference titles — no body paragraphs. Always
grep for body section headings (Introduction, Methods, Results, Discussion)
before tagging `fulltext_source: jina-reader`. If only references, treat as
abstract-only.

---

## EPMC flag staleness

Europe PMC's `isOpenAccess`/`inPMC`/`hasPDF` flags are not always fresh.
A PMCID present in the Phase-1 PubMed XML (`<ArticleId IdType="pmc">`)
overrides stale EPMC flags — **always try `efetch db=pmc` when PubMed XML
carries a PMCID, even if EPMC reports all-N.** This affects all publishers,
not just OA-native ones (confirmed for Ivyspring, Springer Nature/Nature
Aging, and others). Only declare abstract-only when `efetch db=pmc` itself
returns front-matter-only or an error — not when EPMC merely says N.

The reverse also holds: the PubMed XML PMCID can itself be stale/superseded.
If `efetch db=pmc` with the PubMed XML PMCID returns front-matter only
(no `<body>` element, <10 KB), check the EPMC core record's `pmcid` field
for a *different* PMCID and retry.

## NEJM Wayback timing

NEJM articles are paywalled for ~6 months after publication, then become
free on nejm.org. Wayback snapshots captured during the paywall window
archive the preview page (abstract only). Snapshots captured after the
embargo window archive the full-text page (38–50K chars body).

- Papers published <6 months ago: don't expect full text from any Wayback
  snapshot. Try S2 `openAccessPdf` first; if blocked, abstract-only.
- Papers published 6–24 months ago: try latest snapshots first (most likely
  post-embargo).
- Recent (2024+) NEJM articles: ALL Wayback snapshots return abstract-only
  regardless of era — the modern paywall preview page is what gets archived.

---

## CDX extraction recipe (Python, stdlib only)

```python
import urllib.request, urllib.parse, json, re, html as html_mod

def cdx_search(article_url):
    cdx_url = (f"https://web.archive.org/cdx/search/cdx"
               f"?url={urllib.parse.quote(article_url, safe='')}"
               f"&output=json&limit=5&filter=statuscode:200")
    with urllib.request.urlopen(cdx_url, timeout=60) as r:
        rows = json.loads(r.read())
    return rows[1:] if len(rows) > 1 else []  # skip header row

def fetch_snapshot(article_url, timestamp):
    snap_url = f"https://web.archive.org/web/{timestamp}/{article_url}"
    with urllib.request.urlopen(snap_url, timeout=60) as r:
        return r.read().decode("utf-8", "replace")

def extract_article(html_text):
    match = re.search(r"<article[^>]*>(.*?)</article>", html_text,
                      re.DOTALL | re.IGNORECASE)
    if match:
        html_text = match.group(1)
    html_text = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html_text)
    html_text = re.sub(r"(?i)</(p|div|section|article|h[1-6]|li|tr)>", "\n\n", html_text)
    text = re.sub(r"<[^>]+>", "", html_text)
    text = html_mod.unescape(text)
    lines = [" ".join(l.split()) for l in text.splitlines()]
    return "\n\n".join(l for l in lines if len(l) > 50)
```

CDX API guidance:
- `&filter=statuscode:200` pre-filters at API level (more reliable than
  client-side filtering — unfiltered queries can return only 301/302s).
- Timeouts are transient — retry once after 10s. After 2 consecutive 503s,
  the CDX service is down; declare abstract-only.
- Multiple 200 snapshots can differ in completeness — try each in sequence
  (largest `length` first), keep the one with the most body text.
- Try multiple URL variants: `/doi/<doi>`, `/doi/full/<doi>`,
  `/content/<vol>/<issue>/<page>`, `.long`.
- For migrated domains, try BOTH old and new URL forms (e.g.
  `biochemsoctrans.org` and `portlandpress.com`).

---

## Publisher entries (by pattern)

### Pattern: Branch 1b (PMCID present, XML body restricted, EPMC PDF works)

These publishers deposit in PMC but restrict XML body download —
`efetch db=pmc` returns front-matter only (~6–14 KB, no `<body>`).
`europepmc.org/api/getPdf?pmcid=<PMCID>` delivers the full publisher PDF.
Tag `fulltext_source: epmc-pdf`.

| Publisher | Domain | Notes |
|---|---|---|
| OUP / ATS | academic.oup.com, atsjournals.org | Standard Branch 1b |
| JCI Insight | insight.jci.org | EPMC PDF + jina reader both work |
| CSHLP | cshperspectives.org, cshlpress.org | EPMC PDF: ~3.4 MB → 95K chars |
| ASCO / JCO | ascopubs.org | EPMC PDF: ~541 KB → 58K chars. No PMCID → Wayback CDX on `/doi/full/` works (255 KB → 33K chars) |
| AME Publishing | atm.amegroups.org, jgo.amegroups.org | EPMC PDF: ~223 KB → 23K chars |
| Taylor & Francis | tandfonline.com | PMCID → EPMC PDF (~60K chars). No PMCID → Wayback CDX on `/doi/full/`. Jina returns 27–30 KB page chrome+abstract (validate body) |
| EMBO Press | embopress.org | EPMC `fullTextXML` also fails (0 bytes, distinct from HTTP 404). EPMC PDF: ~730 KB → 34K chars |

### Pattern: Jina works on direct/publisher article URL

These publishers block curl/DOI-URL but jina reader succeeds on the correct
direct article URL form.

| Publisher | Domain | Working URL form | Notes |
|---|---|---|---|
| Elsevier / Lancet | thelancet.com | `thelancet.com/journals/<journal>/article/PIIS<id>/fulltext` | DOIs contain parens → 404 via jina. PIIS form: strip `10.1016/` prefix from DOI, prepend `PII` to the suffix. The "S" in "PIIS" comes from the DOI suffix — do NOT add an extra S |
| Cell Press | cell.com | `cell.com/<journal>/fulltext/<PII>` | PII from PubMed XML `<ArticleIdList>` or `elink.fcgi?cmd=prlinks`. Use `/fulltext/` not `/pdf/` |
| ASBMB / JBC | jbc.org | `jbc.org/article/<PII>/fulltext` | Resolve DOI → PII via `linkinghub.elsevier.com/retrieve/pii/<PII>`. Jina on DOI URL returns 404 |
| Elsevier / JACI | jacionline.org | `jacionline.org/article/S<PII>/fulltext` | Jina on DOI URL 404s. Try PIIS URL via jina before declaring abstract-only |
| AHA Journals | ahajournals.org | `ahajournals.org/doi/<doi>` | Jina succeeds intermittently. Some Circ Res articles are in PMC (OA) and work normally via PMC XML |
| Aging and Disease | aginganddisease.org | S2 `openAccessPdf` → direct PDF curl | JS-rendered CMS; jina returns template chrome. S2 provides PDF URL at `aginganddisease.org/EN/PDF/<DOI>`. Tag `fulltext_source: publisher-oa` |

### Pattern: Wayback CDX is the reliable path

These publishers block jina reader but Wayback CDX finds 200-status
snapshots with full body text.

| Publisher | Domain | CDX URL form | Notes |
|---|---|---|---|
| NEJM | nejm.org | `nejm.org/doi/full/<doi>` and `nejm.org/doi/<doi>` | Skip jina entirely (403s). Direct `urllib.request` on snapshot URL → 189–270 KB HTML → `<article>` extraction → 38–50K chars. See NEJM timing note above |
| AACR | clincancerres.aacrjournals.org, cancerres.aacrjournals.org | `.long` URL variant | `.long` yields full body (219 KB → 27K chars); non-`.long` is page chrome |
| Wiley | onlinelibrary.wiley.com | `onlinelibrary.wiley.com/doi/full/<DOI>` | 2020–2021 era snapshots → 500–600 KB HTML → 90–95K chars. Works for OA articles even when `isOpenAccess: N` |
| Portland Press | portlandpress.com | Legacy `biochemsoctrans.org/content/<vol>/<issue>/<page>` | CDX returns nothing for `portlandpress.com` (post-migration) — must use old domain |
| ScienceDirect | sciencedirect.com | N/A — **Wayback does NOT work** | Snapshots load successfully but body is JS-rendered (SPA) — only abstract, keywords, abbreviations present. This is a distinct failure mode from Cloudflare CAPTCHA |

### Pattern: Nature subscription journals — metadata extraction

Nature subscription research journals (Nature Biotechnology, Nature
Medicine, Nature Methods, Nature Struct Mol Biol, Nature Machine
Intelligence) and Nature Reviews (Immunology, Drug Discovery) are
paywalled. The full extraction technique is in
`references/nature-metadata-extraction.md`.

- **Nature Reviews**: jina returns only the reference list. Direct curl
  gets abstract + Key points + Glossary + figure captions + reference list.
- **Nature subscription research**: direct curl on `nature.com/articles/
  <doi-suffix>` succeeds (no Cloudflare block) — the HTML `<head>` carries
  rich `citation_*` meta tags (authors, affiliations, ORCIDs, full
  reference list, figure captions, data/code availability). Try jina
  first (may return metadata sections); meta-tag extraction is fallback.
- **Nature OA research articles** (Nature, Nature Communications) render
  full body via browser — distinct from subscription journals.

### Pattern: All paths fail → abstract-only

These publishers are genuinely unreachable from this host — all retrieval
paths fail (Cloudflare/CAPTCHA on jina, no Wayback snapshots or
abstract-only snapshots, no PMCID or PMCID-present-but-restricted).

| Publisher | Domain | Notes |
|---|---|---|
| Rockefeller UP (JEM) | rupress.org | Cloudflare defeats jina, Wayback, and browser |
| ASH Publications (Blood) | ashpublications.org | PMCID present but XML front-matter only, EPMC PDF returns "No PDF file found" |
| JAMA Network | jamanetwork.com | No snapshots. PMCID-present variant: XML front-matter, EPMC PDF 404 |
| Thieme | thieme-connect.com | German maintenance page; Wayback snapshots fail (403/498) |
| ADA (Diabetes) | diabetesjournals.org | No Wayback snapshots |
| AAI (J Immunol) | journals.aai.org, jimmunol.org | S2 `openAccessPdf` false positive (HTML redirect, not PDF). Legacy `jimmunol.org/cgi/content/full/` URL may work via Wayback |
| SAGE / Atypon | journals.sagepub.com | Unpaywall 422 (DOI prefix 10.1177). S2 null |
| ProEd / Index Copernicus | doi.org → Portico | DOI prefix 10.1358. All alternatives fail |
| Springer / World J Surg | link.springer.com | PMCID present but ALL paths fail (XML metadata-only, EPMC PDF no PDF, fullTextXML 404, jina CAPTCHA, CDX 503) |
| Wolters Kluwer / AAN | neurology.org | Jina reference-list masquerade (64–70 KB). Wayback snapshots are abstract-only. Some 2015+ articles may have PMCID — check EPMC |
| Karger | karger.com | Cloudflare Turnstile |

For all of these: three-source closure (EPMC all-N + Unpaywall closed + S2
CLOSED/null), tag `fulltext_source: abstract-only`, `needs-enrichment: true`.
PubMed structured abstract is the primary content source.
