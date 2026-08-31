# Nature subscription research journals — paywalled metadata extraction

Session note (2026-08-17, Su et al. 2025, ProTrek, Nature Biotechnology,
PMID 41039041, DOI 10.1038/s41587-025-02836-0):

## The problem

The paper-ingest Branch 2 note says "Nature research-article pages render
reliably" via browser — `nature.com/articles/<doi-suffix>` yields the
complete body. This is true for **open-access** Nature research articles
(Nature, Nature Communications, etc.). It is **NOT true for subscription
Nature research journals** like Nature Biotechnology, Nature Medicine
(subscription articles), Nature Methods, Nature Structural & Molecular
Biology, etc.

For ProTrek (Nature Biotechnology, subscription, no PMCID, not OA), both
jina reader and direct browser navigation returned only the abstract +
"subscription content" paywall notice. The body text was unreachable.

## The technique: `citation_*` meta tags

Direct `curl -sL "https://www.nature.com/articles/<doi-suffix>"` succeeds
(no Cloudflare block) and returns ~400 KB of HTML. The body is paywalled,
but the `<head>` section contains a rich set of `citation_*` meta tags
that provide structured metadata sufficient for a meaningful partial
distillation:

| Meta tag | Content |
|---|---|
| `citation_title` | Full article title |
| `citation_doi` | DOI |
| `citation_author` | Each author name (one tag per author) |
| `citation_author_institution` | Each author's affiliation (paired with author) |
| `citation_journal_title` | Journal name |
| `citation_volume`, `citation_issue` | Volume/issue |
| `citation_firstpage`, `citation_lastpage` | Page range |
| `citation_publication_date` | Print date (YYYY/MM) |
| `citation_online_date` | Online date (YYYY/MM/DD) |
| `citation_article_type` | Article type (e.g., "Brief Communication") |
| `citation_reference` | Full reference list — each reference as a semicolon-delimited citation string |
| `citation_pdf_url` | PDF URL (subscription-gated) |
| `citation_issn` | ISSN |

Additionally, the HTML body contains:
- **Figure captions** — `<figcaption>` elements with full caption text
  (3 main + 6 extended-data captions extracted for ProTrek)
- **Extended Data figure captions** — the full text of ED Fig captions
  (often substantial: 300–1200 chars each, containing methodological detail)
- **Data availability** section — full text (precomputed embedding URLs,
  GitHub links, database sources)
- **Code availability** section — full text (license, repository URLs,
  Colab links)
- **Author ORCIDs** — embedded in the author block with `orcid.org/<id>` links

## Extraction recipe

```bash
curl -sL "https://www.nature.com/articles/<doi-suffix>" -o /tmp/nature_page.html
```

Then parse with Python:

```python
import re

with open('/tmp/nature_page.html') as f:
    html = f.read()

# Authors + affiliations (parallel lists)
authors = re.findall(r'<meta name="citation_author" content="([^"]+)"', html)
affs = re.findall(r'<meta name="citation_author_institution" content="([^"]+)"', html)

# ORCIDs — in the HTML body, not meta tags
orcid_matches = re.findall(r'orcid\.org/([0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4})', html)

# References — each in a citation_reference meta tag
refs = re.findall(r'<meta name="citation_reference" content="([^"]+)"', html)

# Figure captions
fig_caps = re.findall(r'<figcaption[^>]*>(.*?)</figcaption>', html, re.DOTALL)
for cap in fig_caps:
    text = re.sub(r'<[^>]+>', ' ', cap)
    text = re.sub(r'\s+', ' ', text).strip()

# Data/Code availability — in content div/section elements
sections = re.findall(r'<(?:div|section)[^>]*(?:data-test|class)="[^"]*(?:article|content|body|main)[^"]*"[^>]*>(.*?)</(?:div|section)>', html, re.DOTALL)
for sec in sections:
    text = re.sub(r'<[^>]+>', ' ', sec)
    text = re.sub(r'\s+', ' ', text).strip()
    if 'Data availability' in text or 'Code availability' in text:
        # Extract the data/code availability text
        pass
```

## When to use this

When a Nature research-journal paper is:
- Not open access (`isOpenAccess: N`)
- Not in PMC (`inPMC: N`, no PMCID)
- Jina reader returns only abstract + paywall notice
- No bioRxiv preprint exists

Set `needs-enrichment: true`, `fulltext_source: abstract-only`, and distill
from: abstract + figure/ED captions + data/code availability + reference
list + author affiliations/ORCIDs. This produces a page that is richer
than abstract-only but still partial — the Findings section will need
`[needs-citation]` markers for claims that require the full body text.

## Which journals this applies to

Confirmed: Nature Biotechnology (subscription), Nature Medicine
(subscription), Nature Machine Intelligence (subscription).
Likely applies to: Nature Methods, Nature Structural & Molecular Biology,
Nature Chemical Biology, Nature Neuroscience, and other subscription
Nature research journals (as distinct from Nature Reviews, which are
already in the known-blocks table with a different failure mode — jina
returns only the reference list, not even the abstract).

Does NOT apply to: Nature (flagship), Nature Communications — these
are either OA or render full body via browser (per the Branch 2 note).

## Nature Machine Intelligence (confirmed 2026-08-19)

Chen et al. 2026, "VITAL," *Nature Machine Intelligence*, DOI
10.1038/s42256-026-01291-z — published same day (not yet in PubMed,
EPMC, or Semantic Scholar). Direct curl on `nature.com/articles/
s42256-026-01291-z` returned full HTML. The `<head>` carried
`citation_*`, `dc.*`, and `prism.*` meta tags (title, DOI, authors,
journal, publication date, first/last page, PDF URL). The embedded
`dataLayer` JSON-LD carried the full author list, publication date
(unix timestamp + string), journal metadata, and article type.

**Jina reader returns more than abstract + paywall for Nature
subscription research articles.** The existing note above says jina
returns "abstract + subscription content paywall notice" — but for
this Nature Machine Intelligence article, jina returned 67 KB including:
the full abstract, the complete reference list (45 refs with DOIs and
Google Scholar links), author affiliations with Chinese names, data
availability (GitHub URL), code availability (GitHub + Zenodo DOI + web
server URL), funding, contributions, competing interests, peer review
information (named reviewer), Extended Data figure captions, and
supplementary information links. This is substantially more than
abstract-only and enabled a complete bibliography walk (45 references
parsed with DOIs), author ledger entries (6 authors with affiliations),
and a meaningful `needs-enrichment` distillation — without needing the
`citation_*` meta tag extraction at all. **Try jina reader first; the
meta-tag extraction is the fallback when jina's yield is insufficient.**
The jina yield may vary by article — the ProTrek (Nature Biotech)
session found jina returned only abstract + paywall, while this NMI
article returned the full metadata sections. The difference may be
journal-specific or article-specific; always check the jina output
size and content before deciding whether the meta-tag extraction is
needed.

## Nature Medicine (confirmed 2026-08-18)

PMID 32661391, Suriben et al. 2020, "Antibody-mediated inhibition of
GDF15-GFRAL activity reverses cancer cachexia in mice" — Nature Medicine
subscription article, no PMCID, EPMC gate all-N. Direct curl on
`nature.com/articles/s41591-020-0945-x` returned 384 KB HTML. The `<head>`
carried 105 `citation_*` meta tags (28 `citation_author`, full
`citation_reference` list of 32 refs, journal/volume/issue/pages/dates).
The HTML body contained the abstract, 4 figure captions, and the Data
Availability section (PDB 6WMW, GEO GSE149263) — but no Methods/Results/
Discussion body text (paywalled). Wayback CDX found one 200-status
snapshot (2020-07-17, 51 KB) that was also a paywall preview (same
abstract + figure captions + references, no body). The jina reader proxy
returned the reference-list masquerade (30 KB, all references, no body).
Distillation from abstract + figure captions + data availability +
reference list + author/affiliation/ORCID metadata produced a richer
page than pure abstract-only. The SKILL.md publisher table for Nature
Medicine now cross-references this extraction recipe.

## Distillation quality

The extracted metadata enables a distillation that is substantially
better than pure abstract-only:
- **Findings**: figure/ED captions often contain specific quantitative
  results and methodological detail — reconstruct findings from these,
  marking claims that require body text with `[needs-citation]`
- **Approach**: data/code availability sections reveal model architecture,
  training data, evaluation datasets, and software stack
- **Connections**: the full reference list enables identification of
  brain-adjacent papers and prior work by the same group
- **Author ledger**: complete author list with affiliations and ORCIDs
- **Limitations**: note the paywall and mark `needs-enrichment: true`
