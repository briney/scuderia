---
name: paper-ingest-patches-2026-08-05b
description: "Use when patching paper-ingest. Corrigan 2021 patches."
triggers:
  - "patch paper-ingest skill"
---

# paper-ingest — patches 2026-08-05b (Corrigan 2021 session)

Patches discovered during the Corrigan et al. 2021 (Cell Reports, FP
priming / trimer base, PMID 33826898) stub-fill session. Two durable
lessons for folding into the vault `paper-ingest` SKILL.md and the
`paper-ingest-doi-pmid-crosscheck` companion.

## Patch 1: Correct DOI + wrong PMID (same-journal near-identical suffix)

### Add to Phase 1 (the PMID can be the wrong identifier — not just the DOI)

The 2026-07-17 patch established that a stub's seed DOI can be wrong and
should be cross-checked against the PMID. The 2026-08-05a patch (Bedard
session) found both can be wrong. This patch found the **symmetric**
case: the stub's DOI is **correct** but the PMID is **wrong**, and the
wrong PMID resolves to a different paper in the **same journal** with a
near-identical DOI suffix (108937 vs 109873 — both valid Cell Reports
DOIs differing by a few digits).

**The title comparison is the universal gate.** After resolving the
stub's PMID via PubMed E-utilities, compare the PubMed-returned
`<ArticleTitle>` to the stub's `title:` field — not just the DOI. If
the titles disagree, the PMID is wrong even if the DOI might be right.
Then run a PubMed title search to find the correct PMID and confirm by
matching the PubMed-returned DOI to the stub's DOI. The title check
catches all three variants (wrong DOI only, wrong PMID only, both wrong);
a DOI-only or PMID-only comparison misses at least one.

**Do not assume the PMID is always the clean identifier.** A stub
created by a bibliography walk may have pulled the PMID from a citation
that referenced a different paper in the same journal issue. The two
identifiers can be corrupted independently from different sources.

Observed 2026-08-05 (Corrigan 2021): stub carried PMID 34686327 and
DOI 10.1016/j.celrep.2021.108937. PMID 34686327 resolved to Isaev et
al., "Pan-cancer analysis of non-coding transcripts… HOXA10-AS in
gliomas" (DOI 10.1016/j.celrep.2021.109873) — a glioma paper, not the
HIV vaccine paper the stub described. The stub's DOI was correct. PubMed
title search → correct PMID 33826898 → DOI match confirmed. Only the
PMID was corrected; the DOI was right all along.

**Summary of all three DOI/PMID cross-check variants:**

| What's wrong | What's right | Gate | Fix |
|---|---|---|---|
| DOI | PMID | Compare PubMed DOI to stub DOI | Trust PMID, correct DOI |
| PMID | DOI | Compare PubMed title to stub title | Title search for correct PMID, confirm DOI match |
| Both | Neither | Title comparison is the only gate | Title search, replace both |

### Companion to update

`paper-ingest-doi-pmid-crosscheck/SKILL.md` — add a "The symmetric case:
correct DOI + wrong PMID" section before the "Relationship to
paper-ingest-pubmed-resolver" section, with the three-variant summary
table.

## Patch 2: Verify author slugs against the ledger before writing frontmatter

### Add to Phase 8 (pre-write slug verification)

**Deriving the author slug from the PubMed middle initial can produce a
slug that does not match the existing ledger entry.** PubMed XML
`<ForeName>` gives the full given name (e.g. "Marit") but the author may
already be in the ledger under `<surname>-<given>` without the middle
initial (e.g. `van-gils-marit`, not `van-gils-marit-j`). If you build
the frontmatter `authors:` list from PubMed names alone without checking
the ledger, the slugs won't resolve and Phase 10 will fail.

**The fix:** Before writing the frontmatter `authors:` list, for each
author, grep the ledger by surname to find the existing entry's exact
slug. Use the existing slug in the `authors:` list — the ledger slug is
authoritative for the slug form (the frontmatter is the canonical
reference the lint resolves against, per the 2026-08-02 patch). Only
create a new slug when no existing entry is found by name or surname.

This is a **pre-write** check, distinct from the Phase 10 post-write
verification (`paper-ingest-verification` companion). The pre-write
check avoids the patch cycle; the Phase 10 check catches it if missed.

Observed 2026-08-05 (Corrigan 2021): guessed `people/van-gils-marit-j`
from PubMed ForeName "Marit" + middle initial "J"; ledger had
`van-gils-marit`. Caught at Phase 10 (author resolution check); fixed
the frontmatter and appended the citation to the correct entry. A
pre-write surname grep would have avoided the patch.

### Companion to update

`paper-ingest-verification/SKILL.md` — add a note to §3 (name-based
duplicate check) that the same ledger-by-surname grep should be done
*before* writing the frontmatter, not just after.
