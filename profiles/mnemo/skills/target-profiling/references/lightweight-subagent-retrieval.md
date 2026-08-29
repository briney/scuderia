# Lightweight subagent full-text retrieval for profile building

When a delegated subagent's task is building a target profile (not curating
brain pages), the full `paper-ingest` pipeline (creating `papers/` pages,
bibliography walks, author ledger) is unnecessary overhead. This documents
the lighter-weight retrieval sequence used successfully for the CD45
profile (2026-08-16), which retrieved genuine full text for 3/5 papers
and grounded fields 2, 3, and 6 in full-text content.

## When to use this vs the full paper-ingest pipeline

- **Use this (lightweight)** when: the subagent is building a profile
  working doc, the papers don't need to be in the brain, and the
  orchestrator only needs the profile + PMID list as output.
- **Use full `paper-ingest`** when: the orchestrator wants the papers
  as brain pages (for future concept linking, bibliography walks, or
  when the papers are independently valuable beyond this profile).

## The pipeline (all via `execute_code` + urllib)

### Step 0: Initial cooldown

```python
import time
# CRITICAL: Wait 10-15s before the FIRST E-utilities call.
# The very first request can hit 429 if NCBI's rate-limit window was
# exhausted by a prior session or concurrent process. An initial
# cooldown prevents this and is cheaper than a failed first call.
time.sleep(10)
```

### Step 1: PubMed search (esearch)

```python
import urllib.parse, time, urllib.request, json

def http_get(url, max_retries=4, base_delay=15):
    """HTTP GET with exponential backoff retry on 429."""
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'HermesAgent/1.0 (research)'})
            with urllib.request.urlopen(req, timeout=45) as resp:
                return resp.read().decode()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                delay = base_delay * (attempt + 1)  # 15s, 30s, 45s, 60s
                print(f"  429, waiting {delay}s (attempt {attempt+1}/{max_retries})...")
                time.sleep(delay)
            else:
                raise
    raise Exception(f"Failed after {max_retries} retries")

q = urllib.parse.quote("apamistamab Iomab-B AML")
url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={q}&retmax=15&retmode=json&sort=relevance"
data = http_get(url)  # handles 429 internally
```

**Rate-limit handling (3 layers):**
1. **Initial cooldown**: sleep 10-15s before the first E-utilities call.
   The very first request can 429 if NCBI's window was exhausted by a
   prior session — an initial cooldown is cheaper than a failed call.
2. **Between-call sleep**: sleep 4-5s after every esearch/esummary/efetch.
3. **Retry with exponential backoff**: wrap EVERY call in a retry loop
   (3-4 attempts, 15s → 30s → 45s waits on 429). Do NOT just retry once
   after 15s — the rate limit may persist for 30-60s under load.

Run multiple search terms to maximize recall.

### Step 2: Title/journal screening (esummary)

```python
batch_str = ",".join(pmids)
url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={batch_str}&retmode=json"
data = http_get(url)  # reuse the same retry wrapper
time.sleep(5)
```

Score by keyword hits in title (e.g., "cd45", "radioimmunotherapy",
"aml", "conditioning") to rank relevance. Select 3-5 landmark papers.

### Step 3: Full abstracts (efetch)

```python
import xml.etree.ElementTree as ET

batch_str = ",".join(key_pmids)
url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={batch_str}&rettype=abstract&retmode=xml"
xml_data = http_get(url)
time.sleep(5)

root = ET.fromstring(xml_data)
abstracts = {}
for article in root.findall('.//PubmedArticle'):
    pmid_elem = article.find('.//PMID')
    if pmid_elem is None:
        continue
    pmid = pmid_elem.text
    abs_parts = []
    for abs_elem in article.findall('.//Abstract/AbstractText'):
        label = abs_elem.get('Label', '')
        text = ''.join(abs_elem.itertext())
        if label:
            abs_parts.append(f"{label}: {text}")
        else:
            abs_parts.append(text)
    abstracts[pmid] = ' '.join(abs_parts) if abs_parts else ''
```

For many papers, the structured abstract (Background/Methods/Results/
Conclusions) is sufficient for fields 3, 6, and 8. Mark paywalled
papers as abstract-only.

### Step 4: PMID → PMCID resolution (NCBI ID Converter)

```bash
curl -sL -H "Accept: application/json" \
  "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids=PMID"
```

**Critical:** Use `-L` (follow redirects). Without it, the API returns
301 Moved Permanently and the JSON parse fails. This was a debugging
step in the CD45 session.

Returns `pmcid` and `doi` for papers with PMC open-access copies.

### Step 5: Full text via jina reader on PMC article URLs

```bash
curl -sL "https://r.jina.ai/https://www.ncbi.nlm.nih.gov/pmc/articles/PMCID/" --max-time 45
```

This returns full-text markdown including Abstract, Introduction,
Methods, Results, Discussion, References, and author disclosure
sections. For the SIERRA trial (PMC11709001), this returned ~50K
chars of full text from a paywalled JCO paper.

**Alternative URL forms that also work:**
- `https://r.jina.ai/https://doi.org/10.1200/JCO.23.02018` (DOI URL)
- `https://r.jina.ai/https://haematologica.org/article/view/...`
  (publisher direct URL — but may return journal CMS chrome, not
  article body; always verify content)

### Step 6 (fallback): PMC efetch XML

```bash
curl -sL "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=PMCID&rettype=xml"
```

**Pitfall:** PMC efetch has a ~50K char response cap. For long papers
(many references, long discussion), the response is truncated. jina
reader on the PMC article URL is more reliable for complete full text.

## Verification checklist

After retrieval, before writing the profile:
- [ ] At least 3/5 papers have full text (not just abstracts)
- [ ] Fields 2, 3, and 6 cite specific full-text content, not just
      abstract summaries
- [ ] PMIDs cited in the profile match the ingested paper set
- [ ] Abstract-only papers are marked as such (not presented as
      full-text-grounded)

## UniProt target identity lookup (field 1 anchoring)

UniProt REST API provides canonical name, gene symbol, MW, sequence
length, domain annotations with exact residue ranges, disulfide bonds,
transmembrane regions, glycosylation sites, and PDB cross-references —
filling most of field 1 and part of field 2/9 in a single API call.

### NEVER guess the UniProt accession — always search

For pathogen targets (especially parasitic), gene names and protein
names are less standardized than for human proteins. Guessing an
accession by pattern (e.g., Q8xxx for P. falciparum) will return an
unrelated protein. The AMA1 session (2026-08-17) guessed Q8IJX8 which
returned Endonuclease ALBA3 — completely unrelated. The correct ID
(Q7KQK5) was found by searching UniProt.

### Search by protein name + organism

```python
import urllib.request, urllib.parse, json

def search_uniprot(query, size=10):
    params = urllib.parse.urlencode({
        'query': query, 'format': 'json', 'size': size,
    })
    url = f"https://rest.uniprot.org/uniprotkb/search?{params}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

# For P. falciparum 3D7: organism_id 36329
# For P. falciparum (species): organism_id 5833
results = search_uniprot('protein_name:"apical membrane antigen" AND organism_id:36329')

# Extract key info
for r in results.get('results', []):
    acc = r['primaryAccession']
    name = r['proteinDescription']['recommendedName']['fullName']['value']
    seq_len = r['sequence']['length']
    mass = r['sequence']['molWeight']
    print(f"{acc} | {name} | {seq_len}aa | {mass}Da")
```

Then fetch the full record for the correct accession:

```python
url = f"https://rest.uniprot.org/uniprotkb/{acc}.json"
data = json.loads(urllib.request.urlopen(
    urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}),
    timeout=30).read())

# Extract:
# - Disulfide bonds: features where type == 'Disulfide bond'
# - Transmembrane: features where type == 'Transmembrane'
# - PDB structures: uniProtKBCrossReferences where database == 'PDB'
# - Function: comments where commentType == 'FUNCTION'
```

### Common organism IDs for infectious disease targets

| Organism | organism_id |
|----------|-------------|
| P. falciparum 3D7 | 36329 |
| P. falciparum (species) | 5833 |
| P. vivax | 5855 |
| M. tuberculosis | 1773 |
| S. aureus | 1280 |
| B. anthracis | 1392 |
| V. cholerae | 666 |
| C. difficile | 1686 |
| Influenza A | 11320 |
| SARS-CoV-2 | 2697049 |

## What this pipeline does NOT do

- No brain paper pages (`papers/` directory)
- No bibliography walk (cited references are not resolved to stubs)
- No author ledger entries
- No frontmatter/schema validation
- No graph linking

These are `paper-ingest` responsibilities. Use the full pipeline when
the papers need to live in the brain.

## Paper page format (for working-docs/hitlist-profiles/papers/)

When writing individual paper pages to the profile's `papers/` directory,
use this simple format (not the full brain paper-ingest format):

```
# PMID {pmid}

**Title**: {title}
**Journal**: {journal}
**Year**: {year}
**PMID**: {pmid}
**Authors**: {first 5 authors, comma-separated, " et al." if more}

## Abstract

{full abstract text}
```

One file per PMID, named `pmid_{PMID}.md`. These are working-doc
reference files, not brain pages — no frontmatter, no wikilinks.
