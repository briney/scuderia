---
name: literature-dive-patches-2026-08-05c
description: "Use when patching literature-dive: subagent PMID/DOI wrong."
triggers:
  - "patch literature-dive skill"
---

# literature-dive — profile-side patches

## Patch 2026-08-05: PMID/DOI in Tier 1 task context is unreliable

### Add to Phase 4 (Subagent failures section, after the existing "Subagent failures" paragraph)

```markdown
**PMID/DOI in task context is unreliable.** The task context passed to a
subagent — the PMID and DOI from the review's reference list — can be
wrong at alarmingly high rates. In the ebolavirus dive (2026-08-05),
7 of 10 Tier 1 subagents found that the PMID, DOI, or *both* in
the task context resolved to a completely different paper than intended.
Examples: PMID 30270042 (the Batra 2018 RBBP6 paper) → a colonic
IBD paper; DOI 10.1016/j.cell.2015.12.048 (Wang 2016 GP-NPC1)
→ a translocon paper.

**The PMID and DOI you send to a subagent are a suggestion, not a
guarantee.** Four rules:
1. Tell each subagent in the task context to verify PubMed identity as
   Phase 1, *before* full-text fetch — do not assume the provided
   PMID/DOI is correct.
2. On subagent return, verify the written page has the *correct* PMID/DOI
   — compare to what the subagent's summary actually resolved to, not the
   values you provided in the task context.
3. If multiple subagents return different corrected PMIDs for the same paper,
   one is still wrong — re-check both against PubMed.
4. Subagents catching this pattern self-correct reliably; the risk is the
   orchestrator *not verifying* the corrected identity and writing a page
   linked to the wrong paper.

Observed 2026-08-05 (ebolavirus dive): 7/10 Tier 1 subagents
required PMID/DOI correction. The Batra 2018 subagent failed to write
the file entirely; when re-ingested directly, the wrong PMID had to be
independently rediscovered. The existing "Subagent failures" anti-pattern
("do not assume 'completed' means 'file written'") caught the missing
file; the newly recognized pattern is that even a successfully written file
may have been found under a corrected PMID different from the one you tasked
it with — verify that too.
```

### Companion vault-side skills that should absorb this patch

- `literature-dive/SKILL.md` — Phase 4 Subagent failures section; the
  PMID/DOI unreliability finding is a new dimension of what "subagent
  completed" does and doesn't guarantee.
