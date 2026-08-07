---
name: paper-ingest-patches-2026-08-05
description: "Profile-side patch pointer for the paper-ingest vault skill."
triggers:
  - "patch paper-ingest skill"
---

# paper-ingest — profile-side patches

The authoritative `paper-ingest` SKILL.md lives in the vault at
`skills/paper-ingest/SKILL.md` and is loaded by `skill_view`
from there. When `skill_manage` cannot patch the vault copy directly, record
the patch here so a future vault-edit session can fold it in.

## Patch 2026-08-05: Both PMID and DOI wrong, no-trailing-newline append pitfall, sibling inbox.yaml corruption

Discovered during the Bedard et al. 2019 (PNAS, iNKT/ER-stress) stub fill.
Three durable lessons.

### Add to Phase 1 (both PMID and DOI can be wrong — not just the DOI)

The 2026-07-17 patch established that a stub's seed DOI can be wrong
and should be cross-checked against the PMID. This session found a
more severe variant: **both the PMID and the DOI in the stub are
wrong, and the PMID resolves to a completely unrelated paper in a
different field.** The stub carried PMID 31611305 and DOI
10.1073/pnas.1901555116. PMID 31611305 resolved to Hahamy & Makin,
J Neurosci 2019 ("Remapping in Cerebral and Cerebellar Cortices…") —
a neuroscience paper, not the immunology paper the stub described.
The DOI was also wrong (10.1073/pnas.1901555116 vs. the correct
10.1073/pnas.1910097116 — a single-digit difference in the PNAS
article number, likely a transcription error).

**The fix:** After resolving the stub's PMID via PubMed E-utilities,
**compare the PubMed-returned `<ArticleTitle>` to the stub's
`title:` field.** If they disagree (different title, different field,
different author list), the PMID itself is wrong. Do NOT assume the
DOI is correct either — both identifiers can be corrupted from the
same source. Run a PubMed title search
(`esearch.fcgi?db=pubmed&term=<title+keywords>&retmode=json`) to find
the correct PMID, then resolve the correct DOI from the PubMed XML
`<ELocationID EIdType="doi">`. Log both corrections prominently in
the Ingest log. The title-mismatch check is the gate that catches
this — a DOI-only cross-check against a wrong PMID will silently
"confirm" the wrong paper.

Observed 2026-08-05 (Bedard 2019): stub PMID 31611305 → Hahamy &
Makin (neuroscience); PubMed title search "Sterile activation
invariant natural killer T cells ER-stressed" → correct PMID
31690657 → correct DOI 10.1073/pnas.1910097116. Both stub
identifiers replaced.

### Add to the concurrency-hazard section (no-trailing-newline append pitfall)

**`cat >> file.yaml` silently concatenates onto the last line when
the target file's last line lacks a trailing newline.** The ledger
(`people/_ledger.yaml`) and the rem-cycle inbox
(`docs/rem-cycle/inbox.yaml`) may not end with `\n` — a prior write
or a sibling's append can leave the file without a trailing newline.
A subsequent `cat >>` then glues the new content directly onto the
last line, producing invalid YAML (e.g. `slug: he-jun- affiliations:`
on a single line) that `yaml.safe_load` rejects.

**The fix:** Before appending, emit a newline:
```bash
printf '\n' >> people/_ledger.yaml && cat /tmp/entries.yaml >> people/_ledger.yaml
```
Or verify the append with `yaml.safe_load` immediately afterwards —
if it fails, the concatenation-on-last-line pitfall is the likely
cause. This is distinct from the sibling-reset hazard (2026-08-02
patch) — the file is not wiped, it is malformed at the junction.

Observed 2026-08-05 (Bedard 2019 ledger append): first `cat >>`
produced no new entries in `yaml.safe_load` output because the
content concatenated onto the `slug: he-jun` line (no trailing `\n`).
Fix: `printf '\n' >>` then `cat >>`, then verify.

### Add to the concurrency-hazard section (sibling inbox.yaml YAML corruption)

**A sibling subagent can append entries to `docs/rem-cycle/inbox.yaml`
with wrong indentation, producing invalid YAML that blocks all
subsequent appends.** The inbox is a YAML list under `items:` — each
entry should be `  - id: …` (2-space indent) with fields at 4-space
indent. Siblings have been observed using 0-indent for `- id:` and
2-space for fields, which breaks the block-mapping structure.

**The fix:** When the inbox fails `yaml.safe_load`, read the tail of
the file and look for `- id:` at column 0 (should be column 2). Patch
the malformed entries to correct indentation before appending your
own entry. Your own append should use the correct 2-space/4-space
indent. Do NOT rewrite the whole file — use `patch` to fix only the
malformed lines, then append your entry. This is the same hazard
class as the ledger concurrency issues (sibling produces malformed
YAML in a shared file), applied to the inbox rather than the ledger.

Observed 2026-08-05 (Bedard 2019 inbox append): two sibling entries
(pancera-2013, henry-2019) had 0-indent `- id:` and 2-space fields;
my correctly-indented entry was between them. `yaml.safe_load` failed
at the 0-indent line. Fix: `patch` corrected both sibling entries to
2-space/4-space indentation; inbox then parsed cleanly with 43 items.
