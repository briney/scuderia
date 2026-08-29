# ClinicalTrials.gov REST API v2 — Usage Guide

## Endpoint

Base URL: `https://clinicaltrials.gov/api/v2/studies`

No authentication required. Returns JSON.

## Key parameters

| Parameter | Purpose | Example |
|-----------|---------|---------|
| `query.intr` | Intervention name | `monoclonal antibody` |
| `query.cond` | Condition/disease | `rheumatoid arthritis` |
| `filter.overallStatus` | Trial status | `TERMINATED,WITHDRAWN,SUSPENDED` |
| `countTotal` | Return total count | `true` |
| `pageSize` | Results per page | `50` (max 1000) |

## Python pattern (urllib)

```python
import urllib.request, urllib.parse, json, time

ct_base = "https://clinicaltrials.gov/api/v2/studies"

def search_trials(condition, failed_only=False):
    params = {
        'query.intr': 'monoclonal antibody',
        'query.cond': condition,
        'countTotal': 'true',
        'pageSize': '50',
    }
    if failed_only:
        params['filter.overallStatus'] = 'TERMINATED,WITHDRAWN,SUSPENDED'
    
    query_string = '&'.join(
        f'{k}={urllib.parse.quote(str(v))}' for k, v in params.items()
    )
    url = f"{ct_base}?{query_string}"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
    
    total = data.get('totalCount', 0)
    studies = data.get('studies', [])
    
    # Extract drug names from intervention fields
    drugs = set()
    for study in studies:
        protocol = study.get('protocolSection', {})
        arms = protocol.get('armsInterventionsModule', {})
        interventions = arms.get('interventions', [])
        for interv in interventions:
            name = interv.get('name', '')
            itype = interv.get('type', '')
            if itype == 'DRUG' and name:
                drugs.add(name.strip())
    
    return total, drugs
```

## Drug name extraction — the noise problem

ClinicalTrials.gov intervention names are extremely messy. A single drug
appears under many variants:

- Dose prefixes: "140 mg brodalumab", "210mg Brodalumab"
- Brand names: "Humira", "adalimumab", "adalimumab (Humira)"
- Biosimilar names: "Amgevita 40Mg Solution for Injection"
- Combination entries: "Adalimumab, Etanercept, Golimumab or infliximab"
- Non-antibody concomitant drugs mixed in

### Exclusion list (partial)

Filter out these non-antibody / non-drug terms before processing:

```
placebo, saline, methotrexate, cyclophosphamide, glucocorticoids,
prednisone, prednisolone, dexamethasone, methylprednisolone,
cyclosporine, azathioprine, mycophenolate, tacrolimus, sirolimus,
leflunomide, tofacitinib, baricitinib, filgotinib, upadacitinib,
fostamatinib, apremilast, abrocitinib,
glatiramer, fingolimod, dimethyl fumarate, teriflunomide, siponimod,
ozanimod, ponesimod, interferon, interferon beta, pegylated interferon,
infliximab (if just checking), adalimumab (if just checking),
5-fluorouracil, capecitabine, gemcitabine, cisplatin, carboplatin,
paclitaxel, docetaxel, irinotecan, oxaliplatin, pemetrexed,
temozolomide, doxorubicin, vincristine, vinblastine, etoposide,
imatinib, sorafenib, sunitinib, pazopanib, regorafenib, cabozantinib,
lenvatinib, vandetanib, lapatinib, gefitinib, erlotinib, afatinib,
osimertinib, crizotinib, ibrutinib, idelalisib, venetoclax,
palbociclib, ribociclib, abemaciclib, olaparib, niraparib,
ruxolitinib, aliskiren, aspirin, heparin, warfarin, clopidogrel,
tissue plasminogen activator, alteplase, nimodipine, levodopa,
carbidopa, memantine, donepezil, rivastigmine, riluzole, edaravone,
pyridostigmine, neostigmine, amifampridine,
standard of care, best available, investigator choice, physician choice,
supportive care, best supportive care, radiation, chemotherapy,
hormone therapy, immunotherapy, targeted therapy,
observation, follow-up, screening, biopsy, surgery,
dose, escalation, expansion, phase 1, phase 2, phase 3,
arm, group, cohort, vehicle, sham,
vitamin, calcium, magnesium, potassium, glucose, dextrose, albumin,
immunoglobulin, IVIG, plasma, plasmapheresis, transfusion, infusion,
cell, cells, transplant, transplantation, CAR-T, T-cell, NK cell,
vaccine, gene therapy,
```

### Resolving unknown drug names to targets

Novel drug names (not in the exclusion list, not a known antibody) require
PubMed follow-up:

```python
# Search PubMed for the drug name + "antibody" + "target"
query = f'{drug_name}[tiab] AND (antibody OR monoclonal OR target)[tiab]'
# Fetch the first abstract and identify the target from the text
```

## Rate limiting

ClinicalTrials.gov does not aggressively rate-limit, but sleep 0.3-0.5s
between sequential calls as a courtesy. Each condition requires two calls
(active + failed), so 50 conditions = 100 calls = ~50 seconds.

## Observed trial volumes (2026-08-15)

| Area | Active trials | Terminated/withdrawn |
|------|---------------|---------------------|
| Immunology (34 conditions) | 2,845 | 369 |
| Oncology (73 cancer types) | 34,964 | 5,557 |
| Neuroscience (57 conditions) | 1,809 | 318 |
| Infectious disease (57 conditions) | 1,720 | 302 |
| Cardiovascular/metabolic (53 conditions) | 1,361 | 199 |
| Ophthalmology/rare (58 conditions) | 3,694 | 639 |
