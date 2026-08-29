# API Templates & Resource Endpoints

Proven endpoints, query patterns, and code snippets for the target-hitlist
workflow. Each section is a copy-paste-ready recipe.

## 1. Antibody Society Web Tables

Three pages, scraped via urllib. HTML tables parsed with regex.

```python
import urllib.request, re

def scrape_table(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        html = r.read().decode('utf-8', errors='replace')
    trs = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
    rows = []
    for tr in trs:
        cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]', tr, re.DOTALL)
        cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
        if cells and len(cells) > 1:
            rows.append(cells)
    return rows

approved      = scrape_table("https://www.antibodysociety.org/antibody-therapeutics-product-data/")
late_stage    = scrape_table("https://www.antibodysociety.org/antibodies-in-late-stage-clinical-studies/")
approved_inds = scrape_table("https://www.antibodysociety.org/resources/approved-antibodies/")
```

### Column layouts (as of 2026-08)

**Approved (product data)** — 20 columns:
INN, Brand Name, Target, Format, Specificity, Sequence source, Backbone,
Light Chain, Conjugated/unconjugated, Linker, Payload, Payload MoA,
Fc Modifications, Reason for Fc Mods, Therapeutic Area, Indication First
Approved, First EU approval year, First US approval year, First global
approval, Expression system

**Late-stage** — 17 columns:
Drug Code(s), INN, Target, Format, Specificity, Sequence source,
Isotype (Fc), Light Chain, Conjugated/Fused, Linker, Payload/Fused moiety,
Fc Mutations, Phase, Late-stage Indications, Therapeutic Area, Company,
Licensee/Partner

**Approved (with indications)** — 6 columns:
INN, Brand name, Target; Format, 1st indication, 1st EU approval year,
1st US approval year

### Target extraction

The Target column may contain format info after a semicolon. Split on `;`
and take the first part:

```python
target = row[target_col].split(';')[0].strip()
```

### Therapeutic Area column (for disease-area classification)

- `Immune-mediated disorders` -> immunology
- `Cancer` / `Antineoplastic` -> oncology
- `Cardiovascular / hemostasis` -> cardiovascular
- `Neurological disorders` -> neuroscience
- `Ophthalmology` -> ophthalmology
- `Metabolic disorders` -> metabolic
- `Musculoskeletal Disorders` -> musculoskeletal
- `Genetic Diseases` -> rare disease
- `Infectious diseases` -> infectious disease

## 2. "Antibodies to Watch" Series (mAbs, open access)

### Find all installments

PubMed search: `Kaplon H[au] AND Reichert JM[au] AND antibody[tiab]`
Returns ~20 papers from 2014-2026.

Known PMIDs (newest first):
41560619 (2026), 39711140 (2025), 38178784 (2024), 36472472 (2023),
35030985 (2022), 33459118 (2021), 31847708 (2020), 30516432 (2019),
29300693 (2018), 27960628 (2017), 26651519 (2016), 25484055 (2015)

### Pull full text + tables from PMC

```python
# 1. Get PMC ID from PubMed esummary (look for articleids idtype='pmc')
# 2. Pull XML from Europe PMC:
epmc_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/PMC{pmcid}/fullTextXML"
# 3. Extract table-wrap elements:
tables = re.findall(r'<table-wrap[^>]*>(.*?)</table-wrap>', xml, re.DOTALL)
# 4. Parse rows from each table:
trs = re.findall(r'<tr[^>]*>(.*?)</tr>', tbl, re.DOTALL)
cells = [re.sub(r'<[^>]+>', '', c).strip()
         for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]', tr, re.DOTALL)]
```

### ATW 2026 table structure (4 tables)

- Table 1: 2025 first approvals (19 antibodies)
- Table 2: Regulatory review (26 antibodies)
- Table 3: Late-stage non-cancer pipeline
- Table 4: Late-stage cancer pipeline

## 3. PubMed E-utilities (REST API)

Entrez Direct CLI is NOT installed. Use REST API via urllib.

### Base URL (important)

```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
```

Do NOT use `https://eutils.ncbi.nlm.nih.gov/nih-annotator/eutils/` — that
returns HTTP 404. The correct path is `/entrez/eutils/`.

### Rate limits

- Sleep 5s between sequential calls (2–3s is insufficient and triggers
  HTTP 429; 5s is reliable)
- After 3x HTTP 429, stop and wait 15+s
- Semantic Scholar fallback: `api.semanticscholar.org/graph/v1/paper/search`

### Query patterns for family sweep

```
# Broad (count hits):
"{protein}"[tiab] AND (antibody OR therapeutic)[tiab] AND ({disease_terms})[tiab]

# Targeted (confirm antibody development):
"{protein}"[tiab] AND (antibody OR monoclonal) AND (clinical OR trial OR phase)[tiab]

# Drug-name resolution (for unknown drugs from ClinicalTrials.gov):
{drug_name}[tiab] AND (antibody OR target OR monoclonal)[tiab]
```

### Exact-phrase [tiab] pitfall

Quoted phrases with [tiab] (e.g., `"Pseudomonas aeruginosa exotoxin A
antibody"[tiab]`) return 0 results unless the EXACT phrase appears verbatim
in a title or abstract. Break into AND-style queries instead:

```
# BAD — returns 0:
"Pseudomonas aeruginosa exotoxin A antibody"[tiab]

# GOOD — returns 78+:
Pseudomonas aeruginosa exotoxin A[tiab] AND antibody[tiab]
```

### esearch + esummary + efetch code pattern

```python
import urllib.request, urllib.parse, json, time
import xml.etree.ElementTree as ET

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# 1. esearch — get PMIDs
params = urllib.parse.urlencode({
    'db': 'pubmed', 'term': query, 'retmax': 20,
    'retmode': 'json', 'sort': 'relevance',
})
url = f"{BASE}/esearch.fcgi?{params}"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = json.loads(urllib.request.urlopen(req, timeout=30).read())
pmids = data['esearchresult']['idlist']
time.sleep(5)

# 2. esummary — get titles/dates/journals (batch, JSON)
params = urllib.parse.urlencode({
    'db': 'pubmed', 'id': ','.join(pmids), 'retmode': 'json',
})
url = f"{BASE}/esummary.fcgi?{params}"
data = json.loads(urllib.request.urlopen(req, timeout=30).read())
for pmid in pmids:
    entry = data['result'][pmid]
    title = entry.get('title', 'N/A')
    pubdate = entry.get('pubdate', 'N/A')
time.sleep(5)

# 3. efetch — get full abstracts (batch, XML — MUST use ElementTree, not regex)
params = urllib.parse.urlencode({
    'db': 'pubmed', 'id': ','.join(pmids),
    'retmode': 'xml', 'rettype': 'abstract',
})
url = f"{BASE}/efetch.fcgi?{params}"
xml_data = urllib.request.urlopen(req, timeout=30).read().decode('utf-8')
root = ET.fromstring(xml_data)  # ElementTree — regex parsing FAILS

for article in root.findall('.//PubmedArticle'):
    pmid = article.find('.//PMID').text
    title = ''.join(article.find('.//ArticleTitle').itertext())
    abstract_parts = []
    for ab in article.findall('.//AbstractText'):
        abstract_parts.append(''.join(ab.itertext()))
    abstract = ' '.join(abstract_parts) if abstract_parts else 'No abstract available'
    # Year, journal, first author similarly extractable
```

**Why ElementTree, not regex:** Greedy regex `<PubmedArticle>.*?<PMID>{pmid}</PMID>.*?</PubmedArticle>`
matches the FIRST article for ALL PMIDs in the batch, because `.*` spans
across article boundaries. ElementTree correctly parses the XML tree.

### UniProt and PDB for target identity (fields 1, 9)

```python
# UniProt REST — protein identity (name, MW, domains, function, catalytic activity)
url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.json"
data = json.loads(urllib.request.urlopen(
    urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}),
    timeout=30).read())

# RCSB PDB — structural data
url = f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id}"
data = json.loads(urllib.request.urlopen(
    urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}),
    timeout=15).read())
# struct.title, exptl[0].method, rcsb_entry_info.resolution_combined[0]
```

## 4. ClinicalTrials.gov API v2

No authentication. REST GET.

### Active trials

```
GET https://clinicaltrials.gov/api/v2/studies
  ?query.intr=monoclonal+antibody
  &query.cond=<disease>
  &countTotal=true
  &pageSize=100
```

### Terminated/withdrawn trials

Add: `&filter.overallStatus=TERMINATED,WITHDRAWN,SUSPENDED`

### Extract drug names

```python
for study in data.get('studies', []):
    for interv in study.get('protocolSection', {}) \
            .get('armsInterventionsModule', {}).get('interventions', []):
        if interv.get('type') == 'DRUG':
            name = interv.get('name', '').strip()
```

### Noise filtering

Drug names are messy. Build an exclusion set for:
- Dose variants: "140 mg brodalumab"
- Biosimilars
- Non-antibody concomitant drugs: methotrexate, prednisone,
  cyclophosphamide, cyclosporine, azathioprine, mycophenolate, tacrolimus,
  tofacitinib, etc.
- Non-drug entries: placebo, "best supportive care", "standard of care"

### Observed volumes (2026-08)

- Immunology: 2,845 active + 369 terminated / 34 conditions
- Oncology: 34,964 active + 5,557 terminated / 73 cancer types
- Neuroscience: 1,809 active + 318 terminated / 57 conditions

### Failed-trial graveyard pattern (neuroscience)

Neuroscience had the largest failed-clinical tier (22 targets) — the
"graveyard" of antibody drug development. The failed targets were NOT
found via ClinicalTrials.gov drug-name extraction (which returned mostly
already-known drugs). They were found via domain knowledge: knowing the
specific failed antibody names and mapping them to targets.

Known neuroscience failed-antibody → target mappings:

| Drug | Target | Indication | Phase |
|------|--------|-----------|-------|
| Bapineuzumab | Aβ N-terminal | Alzheimer | Phase 3 |
| Solanezumab | Aβ monomer | Alzheimer | Phase 3 |
| Gantenerumab | Aβ oligomer/fibril | Alzheimer | Phase 3 |
| Crenezumab | Aβ oligomer | Alzheimer | Phase 2 |
| Ponezumab | Aβ C-terminal | Alzheimer | Phase 2 |
| Semorinemab | Tau | Alzheimer | Phase 2 |
| Tilavonemab | Tau N-terminal | AD/PSP | Phase 2 |
| Zagotenemab | Tau oligomers | Alzheimer | Phase 2 |
| Bepranemab | Tau mid-region | Alzheimer | Phase 2 |
| BIIB092 | Tau | FTD/TBI | Phase 2 |
| Cinpanemab | Alpha-synuclein | Parkinson | Phase 2 |
| Nevanimab | Alpha-synuclein | Parkinson | Phase 2 |
| Tanezumab | NGF | Osteoarthritis pain | Phase 3 |
| Fasinumab | NGF | Pain | Phase 3 |
| Opicinumab | LINGO-1 | MS remyelination | Phase 2 |
| Cilengitide | αvβ3/αvβ5 integrin | Glioblastoma | Phase 3 |
| Omburtamab | B7-H3 | Glioma (radioimmunotherapy) | Phase 2/3 |

All of these targets are still IN per the binary bar. The Aβ graveyard is
the canonical example: 5 antibodies failed, then aducanumab/lecanemab/
donanemab succeeded — same target, different epitope/conformation.

## 5. Target Name Normalization

Gene symbols are the most reliable dedup key. Common aliases:

| Canonical | Aliases |
|-----------|---------|
| TNF | TNF-a, TNF-alpha |
| BAFF/BLyS (TNFSF13B) | BLyS, BAFF, CD257 |
| IL-17A (IL17A) | IL-17, IL-17a |
| IL-4Ra (IL4R) | IL-4R alpha |
| IL-23 p19 (IL23A) | IL-23p19, IL-23 P19 |
| Complement C5 (C5) | C5, Complement 5 |
| FcRn (FCGRT) | FcRn, neonatal Fc receptor |
| RANKL (TNFSF11) | RANK-L, RANKL |
| TSLP | Thymic stromal lymphopoietin |
| P-selectin (SELP) | CD62, CD62 (aka P-selectin) |

### Merging duplicates

```python
ev_order = ['approved', 'clinical-trial', 'failed-clinical', 'preclinical', 'mechanistic']
# Keep HIGHEST evidence type (lowest index). Combine drugs + indications.
```

## 6. Cross-area Target Handling

Targets may appear in multiple area lists. This is correct — each area
records the evidence relevant to that area's diseases. Do NOT dedup across
areas.

Common cross-area targets:
- PD-1, PD-L1, CTLA-4, LAG-3, TIGIT, TIM-3 — oncology + immunology
- CD20, CD19, CD22, CD38, CD52 — oncology + immunology
- CD3 — oncology (engagers) + immunology
- CD40/CD40L — oncology (agonist) + immunology (antagonist)
- CSF-1R — oncology (TGCT) + immunology (GVHD)
- VEGF/VEGFR — oncology + ophthalmology + cardiovascular
- Complement C5, C3 — immunology + ophthalmology + cardiovascular
