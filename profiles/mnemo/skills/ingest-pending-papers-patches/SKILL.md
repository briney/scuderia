---
name: ingest-pending-papers-patches
description: "Patch pending ingest-pending-papers vault skill."
triggers:
  - "patch ingest-pending-papers skill"
---

# ingest-pending-papers-patches — profile-side patches

The authoritative `ingest-pending-papers` SKILL.md lives in the vault at
`skills/ingest-pending-papers/SKILL.md`. When `skill_manage` cannot
patch the vault copy directly, record the patch here so a future vault-edit
session can fold it in.

## Patch 2026-08-05: Phase 1 queue discovery — use YAML frontmatter parsing, not search_files content search

### Replace Phase 1 in the vault SKILL.md

```markdown
1. **Find the queue.** The canonical method is an `execute_code` script
   that reads each `papers/*.md` file, parses the YAML frontmatter with
   `yaml.safe_load`, and filters on `fm.get('needs-ingest') is True`.
   This yields the true stub set in one pass — and also extracts
   `cited_by`, `ingest_attempts`, `last_ingest_attempt`, and `title` for
   sorting. Order by `len(cited_by)` descending — high-edge stubs first,
   since they have the most evidence of being worth the time.

   Do **not** use `search_files target=content` for `needs-ingest: true`
   as the primary method. It has two known bugs observed on 2026-08-05:
   - **False positives:** the content search matches `needs-ingest: true`
     appearing *inside body text* — particularly in `## Ingest log`
     entries that quote the field name. A 2026-08-05 drain found 121
     content matches but only 84 YAML-verified stubs.
   - **Silent truncation:** the default `limit=100` silently truncates
     queues over 100 stubs. A 2026-08-05 queue of 121 was read as 100,
     hiding 21 stubs from the orchestrator. Always specify `limit=500`
     if you do use `search_files` as a secondary check.

   The `execute_code` approach avoids both bugs because it parses the
   actual YAML frontmatter (not body text) and has no artificial limit.
```

### Add to Phase 3 (subagent context guidance)

```markdown
**Include a `venue` vs `journal` field-name warning in the subagent
context.** Subagents sometimes resolve the journal name correctly from
PubMed but write it to a `journal:` YAML key instead of the schema-required
`venue:` key. The Phase 4 frontmatter invariant check catches this as a
verification failure, but it wastes a round-trip. Add this line to every
batch's subagent context:

> IMPORTANT: use the frontmatter field name 'venue' (not 'journal') for
> the journal name, and include 'year'.

Observed 2026-08-05: two subagents (hung-2021, jain-2015) wrote `journal:`
instead of `venue:`. The orchestrator caught both in Phase 4 and fixed
them with a `patch` call, but the fix should be preventive, not reactive.
```

### Add to Phase 4 (duplicate-merge verification)

```markdown
**Phase 4 verification must handle the duplicate-merge case.** When a
subagent discovers the stub is a duplicate of an already-ingested
canonical page, it deletes the stub and merges `cited_by` into the
canonical page (per the paper-ingest 2026-07-24 stub-rename patch). The
Phase 4 verification flow must account for this:

1. If the stub file still exists — standard verification (read file,
   check needs-ingest: false, authors, cited_by, body sections).
2. If the stub file does NOT exist — it was a duplicate-merge. Verify
   the canonical page instead:
   - Identify the canonical page (the subagent's return summary names it).
   - Read the canonical page.
   - Confirm `needs-ingest: false`.
   - Confirm the stub's `cited_by` entries were merged into the canonical
     page's `cited_by` list (the entries the orchestrator passed in the
     subagent context should all appear in the canonical page's
     `cited_by`).
   - Confirm the canonical page has body sections (it was already
     ingested, so it should — but verify).

Do NOT report a failure when the stub file is missing — that is the
expected outcome of a duplicate-merge. Only report failure if the
canonical page is also missing or the `cited_by` merge didn't land.

Observed 2026-08-05: 4 stubs across the drain were duplicates
(bhiman-2015-v1v2-bnab-maturation, bonsignori-2011-ch01-v2v3,
doria-rose-2015-cap256-vrc26-25-new-member,
doria-rose-2015-cap256-vrc26-lineage). The orchestrator's verification
correctly checked for the deleted-file case and verified the canonical
pages instead.
```
