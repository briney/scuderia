# Tier A full-sweep recipe

Proven pattern for generating all 182 Tier A entries from the fetched source
data. Validated 2026-08-18.

## Prerequisites

- `raw/_antibodysociety_approved_table.json` — parsed Antibody Society table
- `raw/_atw2026_fulltext.xml` — ATW 2026 full text (for pipeline entries)
- All templates in `templates/` already written
- Pilot batch (~27 entries) already validated

## Entry generation from the approved table

The approved table has 168 data rows. Row 0 is the header:
`['INN', 'Brand name', 'Target; Format', '1st indication approved/reviewed',
'1st EU approval year', '1st US approval year']`

For each row:

1. **Parse INN**: strip embedded newlines (e.g., "Gemtuzumab\nozogamicin" ->
   "gemtuzumab ozogamicin")
2. **Parse target + format**: split the "Target; Format" column on `;`
3. **Determine modality** from the format string:
   - `"adc"` in format -> `adc`
   - `"bispecific"` -> `bispecific`
   - `"fab"` or `"scfv"` -> `fragment`
   - `"immunotoxin"` or `"toxin"` -> `immunoconjugate`
   - `"i131"` or `"radio"` -> `radioimmunoconjugate`
   - else -> `naked-igg`
4. **Determine status** from US/EU year columns:
   - Year present (no `#`) -> `approved`
   - `Review` -> `filed`
   - `#` with single year -> `withdrawn`
   - `2017;\n2000#` pattern -> `approved` (re-approved, with failed appendix)
5. **Determine origin** from format: humanized > chimeric > murine > human
6. **Determine areas** via `determine_areas()` with word-boundary regex

## Area-assignment function

```python
def determine_areas(target, indication, inn):
    areas = []
    ind_lower = (indication or "").lower()
    target_lower = (target or "").lower()
    def has_term(text, term):
        return bool(re.search(r'\b' + re.escape(term) + r'\b', text))

    cancer_terms = ["cancer", "tumor", "leukemia", "lymphoma", "myeloma",
                    "carcinoma", "melanoma", "sarcoma", "mesothelioma",
                    "blastoma", "neoplasm", "myelofibrosis"]
    if any(has_term(ind_lower, t) for t in cancer_terms):
        areas.append("oncology")

    imm_terms = ["arthritis", "psoriasis", "crohn", "colitis", "lupus",
                 "multiple sclerosis", "asthma", "dermatitis", "angioedema",
                 "vasculitis", "graft", "transplant", "uveitis",
                 "scleroderma", "pemphigus", "thyroiditis", "spondylitis",
                 "pustular"]
    if any(has_term(ind_lower, t) for t in imm_terms):
        areas.append("immunology-inflammation")

    cv_terms = ["cholesterol", "lipid", "atherosclerosis", "diabetes",
                "obesity", "thrombosis", "hypercholesterolemia",
                "cardiovascular", "hypertension"]
    if any(has_term(ind_lower, t) for t in cv_terms):
        areas.append("cardiovascular-metabolic")

    oph_terms = ["macular degeneration", "amd", "diabetic retinopathy",
                 "glaucoma", "dry eye", "uveitis", "paroxysmal", "pnh",
                 "hereditary", "fibrodysplasia", "osteoporosis"]
    if any(has_term(ind_lower, t) for t in oph_terms):
        areas.append("ophthalmology-rare")

    neuro_terms = ["migraine", "alzheimer", "parkinson", "als",
                   "neuropathy", "headache", "epilepsy", "stroke",
                   "sclerosis"]
    if any(has_term(ind_lower, t) for t in neuro_terms):
        areas.append("neuroscience")

    inf_terms = ["rsv", "covid", "sars-cov", "ebola", "hiv", "influenza",
                 "infection", "sepsis", "endotoxin", "anthrax", "rabies"]
    if any(has_term(ind_lower, t) for t in inf_terms):
        areas.append("infectious-disease")

    if not areas:
        if any(t in target_lower for t in ["pd-1", "pd1", "pd-l1", "her2",
               "egfr", "vegf", "vegfr", "cd20", "cd19", "cd33", "cd30",
               "cd22", "cd38", "her3", "trop", "bcma", "epcam",
               "tissue factor", "dll3", "gd2", "folate"]):
            areas.append("oncology")
        elif any(t in target_lower for t in ["tnf", "il-5", "il-6", "il-17",
                  "il-23", "baff", "c5", "complement", "c1s", "factor d",
                  "rankl", "il-12", "il-36", "fcrn", "ige"]):
            areas.append("immunology-inflammation")
        elif any(t in target_lower for t in ["vegf-a", "vegf", "factor"]):
            areas.append("ophthalmology-rare")
        elif any(t in target_lower for t in ["cgrp"]):
            areas.append("neuroscience")
        else:
            areas.append("oncology")

    seen = set()
    return [a for a in areas if not (a in seen or seen.add(a))]
```

## Non-table entries (14 total)

Approved antibody-derived therapeutics NOT in the Antibody Society mAb table.
Source from domain knowledge with `source_quality: medium`:

### Fc-fusions (8)
- etanercept (Enbrel) -- TNF; immunology-inflammation
- aflibercept (Eylea/Zaltrap) -- VEGF; ophthalmology-rare, oncology
- romiplostim (Nplate) -- TPO receptor; immunology-inflammation
- dulaglutide (Trulicity) -- GLP-1 receptor; cardiovascular-metabolic
- albiglutide (Eperzan) -- GLP-1 receptor; cardiovascular-metabolic
- efanesotocoz alfa (Alvega) -- Factor VIII-Fc; ophthalmology-rare
- rurioctocoz alfa (Adynovate) -- Factor VIII-Fc; ophthalmology-rare
- eftrenonacoz alfa (Alprolix) -- Factor IX-Fc; ophthalmology-rare

### CAR-T products (6)
- tisagenlecleucel (Kymriah) -- CD19; oncology; 4-1BB
- axicabtagene ciloleucel (Yescarta) -- CD19; oncology; CD28
- brexucabtagene autoleucel (Tecartus) -- CD19; oncology; CD28
- lisocabtagene maraleucel (Breyanzi) -- CD19; oncology; 4-1BB
- idecabtagene vicleucel (Abecma) -- BCMA; oncology; 4-1BB
- ciltacabtagene autoleucel (Carvykti) -- BCMA; oncology; 4-1BB

## Index regeneration

After all entries are written, regenerate all six `index/` files + master
index by parsing each entry's `Therapeutic area(s)` field. Each area file is a
markdown table: INN | Brand | Target(s) | Modality | Status | Entry path.
The master index includes modality and status breakdowns.

## Verified results (2026-08-18)

- 182 total entries
- Modality: naked-igg 132, adc 15, bispecific 14, fc-fusion 8, car-t 6,
  fragment 6, immunoconjugate 1
- Status: approved 163, filed 11, withdrawn 8
- Index: oncology 95, immunology-inflammation 48, infectious-disease 16,
  ophthalmology-rare 14, neuroscience 12, cardiovascular-metabolic 6
- 208 total files in the corpus directory
