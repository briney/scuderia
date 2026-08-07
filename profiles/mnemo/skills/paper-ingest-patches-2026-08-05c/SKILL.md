---
name: paper-ingest-patches-2026-08-05c
description: "Use when patching paper-ingest. Alvarado 2021 patches."
triggers:
  - "patch paper-ingest skill"
---

# paper-ingest — patches 2026-08-05c (Alvarado 2021 session)

Patches discovered during the Alvarado et al. 2021 (Nat Commun, broadly
cross-reactive norovirus mAbs, PMID 34262046) ingest session. Three
durable lessons for folding into the vault `paper-ingest` SKILL.md and
the `paper-ingest-pubmed-resolver-v2` companion.

## Patch 1: Existing person page slug with Jr/Sr/III suffix

### Add to Phase 8 (check existing person pages by surname before finalizing `authors:`)

The 2026-08-05b patch (Corrigan session) covered verifying author slugs
against the *ledger* before writing frontmatter. This patch covers the
related but distinct case: an author has an existing **person page**
(not just a ledger entry) whose slug includes a suffix (Jr, Sr, III)
that PubMed XML `<ForeName>` does not carry.

**Before finalizing the frontmatter `authors:` list, search for existing
person pages by surname and align slugs to the existing pages — including
any suffix.** An existing person page may use a slug form the agent did
not anticipate: `people/crowe-james-e-jr` (with "Jr" suffix),
`people/smith-john-iii`, etc. If the agent builds the `authors:` list
from PubMed XML `<LastName>`/`<ForeName>` alone, it will produce
`people/crowe-james-e` (no suffix), which does not match the existing
page's slug. The lint resolves `authors:` entries against person pages
and the ledger by exact string match, so a mismatched slug silently
breaks the author back-link.

**The fix:** After deriving the initial `authors:` slug list from PubMed
XML, grep the `people/` directory for each author's surname:

```bash
ls people/ | grep -i '<surname>'
```

If an existing person page matches by surname, read its frontmatter
`slug:` field and use that exact slug in the `authors:` list. This
catches suffix variants (Jr/Sr/III), middle-initial variants, and
multi-word surname variants the PubMed XML does not disambiguate.

Observed 2026-08-05 (Alvarado 2021): PubMed XML gave "Crowe, James E.
(JE)"; initial slug `people/crowe-james-e`; existing page at
`people/crowe-james-e-jr` (slug includes "Jr" suffix). Fix: aligned
`authors:` to `people/crowe-james-e-jr` and added the paper to Crowe's
`author_on:` list (Branch 1).

**Relationship to the 2026-08-05b patch:** The 2026-08-05b patch checks
the *ledger* (`people/_ledger.yaml`) for existing entries by surname.
This patch checks the *person pages* (`people/*.md`) for existing pages
by surname. Both checks are needed: an author may have a person page
without a ledger entry (if they were promoted past the threshold), or a
ledger entry without a person page (if they haven't yet been promoted).
The person-page check catches suffix variants the ledger check misses
because person pages were hand-curated with the suffix, while ledger
entries may not carry it.

### Companion to update

`paper-ingest-pubmed-resolver-v2/SKILL.md` — add this to the Phase 8
section (after the non-ASCII slug derivation patch from 2026-08-02).

## Patch 2: Task-warned DOI verification

### Add to Phase 1 (task-warned DOI — a new variant of seed-DOI cross-check)

The 2026-07-17 patch established that a stub's seed DOI can be wrong and
should be cross-checked against the PMID. The 2026-08-05b patch (Corrigan
session) found the symmetric case: correct DOI + wrong PMID. This patch
covers a third variant: the *task itself* warns that the DOI may belong
to a different paper.

**When the task warns that a DOI may belong to a different paper, always
resolve the PMID via PubMed and verify.** A parent task (literature-dive,
idea-ingest) may flag uncertainty about a seed DOI — e.g., "this may be
Hu 2022's DOI, check carefully." This happens when a co-author has their
own papers and a citation might conflate them. The PMID is the
authoritative resolver: resolve the PMID via PubMed XML, extract the DOI
from `<ELocationID EIdType="doi">`, and compare to the task's seed DOI.
If they match, the seed DOI is confirmed. If they disagree, the PubMed
DOI is authoritative (same as the 2026-07-17 seed-DOI correction).

**Also check whether the "wrong" author name appears in the actual
`<AuthorList>`.** The confusion often arises because the author is a
mid-author on the correct paper (not the first author), which is why the
DOI was suspected to belong to a different paper by the same author. In
this case, the DOI was correct all along — the task's warning was a
false alarm caused by not recognizing the mid-author's presence.

Observed 2026-08-05 (Alvarado 2021): task warned "this may be Hu 2022's
DOI, check carefully" — PubMed confirmed DOI 10.1038/s41467-021-24649-w
belongs to Alvarado 2021; Liya Hu is a mid-author (not first author),
which is the source of the confusion.

### Companion to update

`paper-ingest-doi-pmid-crosscheck/SKILL.md` — add a "Task-warned DOI"
section alongside the existing seed-DOI and wrong-PMID cases.

## Patch 3: Branch 1 vs Branch 3 when task says "no ledger entries"

### Add to Phase 8 (clarify the scope of "do not create author ledger entries")

**A task may say "Do NOT create author ledger entries" — this refers to
Branch 3 only, not Branch 1.** Branch 3 is appending new entries to
`people/_ledger.yaml` for authors without a person page. Branch 1 is
updating `author_on:` on an existing person page. The task's "no ledger
entries" instruction skips Branch 3 only. If an author already has a
person page, the agent must still add the paper to that person's
`author_on:` list — this is an update to an existing page, not a new
ledger entry.

**Always check for existing person pages even when told not to create
ledger entries.** The `author_on:` update is a separate operation from
ledger entry creation. Skipping it leaves the person page's authorship
graph incomplete — the person page does not list the paper, and the
graph edge is missing.

Observed 2026-08-05 (Alvarado 2021): task said "Do NOT create author
ledger entries." James E. Crowe Jr. had an existing person page
(`people/crowe-james-e-jr.md`). The agent correctly added the paper to
Crowe's `author_on:` list (Branch 1) while skipping Branch 3 for the
other 7 authors (no ledger entries created).

### Companion to update

`paper-ingest-pubmed-resolver-v2/SKILL.md` — add a note to the Phase 8
section clarifying the Branch 1 / Branch 3 distinction when the task
says "no ledger entries."

## Session evidence

### Alvarado 2021 (Nat Commun, norovirus broadly cross-reactive human mAbs)

Alvarado G, Salmen W, Ettayebi K, Hu L, Sankaran B, Estes MK,
Venkataram Prasad BV, Crowe JE Jr. "Broadly cross-reactive human
antibodies that inhibit genogroup I and II noroviruses."
Nat Commun. 2021;12(1):4320. DOI: 10.1038/s41467-021-24649-w.
PMID: 34262046. PMCID: PMC8280134.

- **Task-warned DOI:** Task warned "this may be Hu 2022's DOI, check
  carefully." PubMed confirmed DOI belongs to Alvarado 2021; Liya Hu is
  a mid-author. Erratum noted: Nat Commun 2021 Oct 14;12(1):6090.
- **Existing person page slug with Jr suffix:** Initial slug
  `people/crowe-james-e`; existing page at `people/crowe-james-e-jr`.
  Fix: aligned `authors:` and added to `author_on:`.
- **Branch 1 vs Branch 3:** Task said "no ledger entries"; agent still
  updated Crowe's `author_on:` (Branch 1) while skipping Branch 3.
- **PMC full text:** `isOpenAccess: Y`, `inPMC: Y`, `hasPDF: Y`. PMC XML
  (122 KB) via E-utilities — complete article, no browser calls needed.
- **ORCIDs:** PubMed XML had zero ORCIDs. Europe PMC REST returned 7/8
  (Alvarado has none). Confirms the two-line ORCID capture path is
  necessary even for well-funded Nature-family papers.
