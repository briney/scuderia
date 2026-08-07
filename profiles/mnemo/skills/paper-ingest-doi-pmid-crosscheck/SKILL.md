---
name: paper-ingest-doi-pmid-crosscheck
description: "Reference: cross-check stub DOI against PMID during paper-ingest identity resolution. Stubs created by grant-ingest or bibliography walks can carry the wrong DOI — the PMID is the authoritative resolver. Companion to paper-ingest and paper-ingest-pubmed-resolver."
triggers:
  - "stub DOI mismatch during paper ingest"
  - "PMID resolves to different DOI than the stub"
  - "DOI correction during stub fill"
---

# DOI/PMID cross-check during paper-ingest stub fill

This is a **reference companion** to the `paper-ingest` skill. It documents
a discovery from the McCaleb 2024 stub-fill session (2026-07-17).

## The problem

A stub page (`needs-ingest: true`) carries identity fields (DOI, title,
authors) that were transcribed from a citing paper's bibliography. These
fields can be **wrong**:

- The DOI may belong to a *different* paper in the same reference list
  (transcription error during grant-ingest or bibliography walk).
- The author list may be garbled or attributed to the wrong paper.
- The title may be paraphrased or incomplete.

In the McCaleb 2024 session, the stub `liu-2024-foxo-deletion-blocks.md`
carried DOI `10.4049/immunohorizons.1800032` (Immunohorizons) and was
attributed to "Liu Y, et al." The PMID 38796853 resolved to a completely
different paper: McCaleb et al. 2024, *Cell Reports*, DOI
`10.1016/j.celrep.2024.114283`. The Immunohorizons DOI belonged to a
Gallagher 2018 paper that appeared in the same PubMed reference list —
the wrong reference was transcribed into the stub.

## The fix: PMID as authoritative resolver

When a stub carries **both** a `doi` and a `pmid`:

1. **Resolve the PMID** through PubMed E-utilities (text abstract + XML).
2. **Compare** the DOI returned by PubMed to the stub's `doi` field.
3. **If they disagree**, trust the PMID (NLM-authoritative identifier):
   - Correct `doi`, `title`, `venue`, and `authors` to match the PubMed
     record.
   - Correct `pmcid` from the PubMed XML `ArticleIdList`.
   - Note the correction in `## Analysis` so the discrepancy is traceable:
     "The stub was created with DOI X; PMID Y resolves to DOI Z. The
     Immunohorizons DOI belongs to [different paper]. Fields corrected
     to the Cell Reports publication."
4. **Re-derive author slugs** from the PubMed XML `AuthorList` ( LastName /
   ForeName), not from the stub's `## Citation` text.

### Why PMID is more trustworthy than a stub DOI

- The PMID is assigned by NLM after bibliographic verification. A DOI in a
  stub was transcribed by an upstream skill from a citing paper's reference
  list, which may have dozens of references — easy to pick the wrong one.
- PubMed E-utilities return structured, curated metadata: `AuthorList` with
  `LastName`/`ForeName`, `ArticleTitle`, `Journal/Title`, `ELocationID`
  (DOI), `ArticleIdList` (PMID, PMCID, DOI). This is the authoritative
  record.
- CrossRef is also authoritative for DOI resolution, but if the stub's DOI
  is wrong, CrossRef will happily resolve it — to the wrong paper. The PMID
  is the cross-check that catches the mismatch.

## When only a DOI is present (no PMID)

If the stub has a DOI but no PMID, resolve via CrossRef
(`api.crossref.org/works/<DOI>`) and check that the returned title matches
the stub's title. If they disagree, the DOI is wrong — search PubMed by
title to find the correct PMID, then proceed as above.

## When only a PMID is present

This is the cleanest case — resolve the PMID through PubMed and use the
returned DOI. No cross-check needed.

## Relationship to paper-ingest-pubmed-resolver

This reference complements `paper-ingest-pubmed-resolver` (PubMed XML for
metadata when CrossRef is unavailable) and `paper-ingest-browser-fulltext`
(browser for full text when terminal curl is denied). Together, the three
references cover the identity-resolution failure modes that paper-ingest
encounters in practice.

## Session evidence

McCaleb MR, Miranda AM, Khammash HA, Torres RM, Pelanda R. "Regulation of
Foxo1 expression is critical for central B cell tolerance and allelic
exclusion." Cell Reports. 2024;43(6):114283.
DOI: 10.1016/j.celrep.2024.114283. PMID: 38796853. PMCID: PMC11246624.

Stub `liu-2024-foxo-deletion-blocks.md` carried DOI
10.4049/immunohorizons.1800032 (Gallagher et al. 2018, Immunohorizons — a
different paper in the same reference list). PMID 38796853 resolved to the
McCaleb Cell Reports paper. All identity fields corrected; the slug was
preserved (pre-existing page path).

## Related: needs-enrichment when full text is browser-blocked

In the same session, the paper had a PMCID (open access) but all browser
paths to the full text were blocked: Cell.com (Cloudflare), PMC
(reCAPTCHA), Europe PMC (abstract only). The distillation was done from the
PubMed abstract + XML metadata. **The `needs-enrichment: true` flag should
have been set** per paper-ingest Phase 10, but was omitted — a detailed
abstract does not substitute for figure-level results and methods detail.
This is a pitfall to watch for: when full text is inaccessible despite the
paper being nominally open-access, set the flag regardless of how rich the
abstract-based distillation appears.
