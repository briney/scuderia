---
name: retroactive-linking-shard-worker-observations
description: "Use when shard worker hits EMFILE or needs sync guidance."
triggers:
  - "shard worker EMFILE"
  - "retroactive linking observations"
  - "shard worker frontmatter sync"
  - "shard worker path prefix"
---

# Shard-worker observations — EMFILE, frontmatter sync, edge cases

Reference for `retroactive-linking-shard-worker`. Durable, cross-session
observations from shard runs too detailed for the SKILL.md pitfalls list.

## Shard path prefix mismatch (shard 15)

The shard file (`/tmp/stage_b_shard_15.txt`) listed paths WITH a vault-scope
prefix: `<vault>/papers/doria-rose-2015-cap256-vrc26-lineage.md`. But the
session's working directory is already the vault root. The naive
construction `<vault-root>/<shard-path>` produces a doubled
doubled `<vault>/<vault>/papers/...` path that does not exist.

**Fix:** strip the vault-scope prefix from shard paths before joining with
the vault root. The prompt's instructions explicitly say to strip both the
vault-scope prefix and the `.md` suffix when writing result entries — the
same stripping applies when constructing read paths.

**Cost:** 2 wasted read_file calls before the pattern was recognized.

## All-stub shard pattern (shard 15)

All 10 pages in shard 15 were stubs or near-stubs (`needs-ingest: true`,
body limited to `## Citation` / `## Stub` / `## Ingest log` / short
`## Context` / `## Abstract` sections, no full
Context/Approach/Findings/Limitations/Analysis).

**Expected outcome for an all-stub shard:**
- 0 new body LINKs (no analytical prose with verbatim entity mentions)
- 0 PROPOSEs (citation shorthand in ingest logs is not analytically
  load-bearing — see below)
- 1–3 frontmatter-links-populated entries (from pre-existing body wikilinks
  in `> [!info] Stub` callouts or `## Ingest log` sections never mirrored
  into `links: []`)

**Recognition signal:** if the first 2–3 pages read are all stubs with
`needs-ingest: true` and only citation/stub/ingest-log sections, the rest
of the shard is likely the same. Accelerate by skipping deep candidate
generation — just scan for pre-existing body wikilinks and sync frontmatter
`links:`.

## Ingest-log citation shorthand ≠ analytical mention (shard 15)

Shard 28 established that "Author Year" shorthand in *analytical prose*
can be a PROPOSE if load-bearing. Shard 15 refines this: when the
"Author Year" mention lives inside an `## Ingest log` section, it is
**bibliographic metadata** describing why the stub was created, not
analytical prose. Even if the target page EXISTS and the relationship is
real (stub created from that paper's bibliography walk), the ingest log is
not making an analytical claim that depends on the cited paper — it is
documenting provenance. SKIP these for both LINK and PROPOSE.

**Examples from shard 15:**
- "Stub created during bibliography walk of Dankwa 2024" → SKIP (ingest log)
- "Complementary to Walker-Sperling 2025" in ingest log → SKIP (metadata)
- "The computational design software used in Holt 2023" in ingest log → SKIP

**Contrast:** if the same "Walker-Sperling 2025" mention appeared in a
`## Findings` or `## Analysis` section arguing that two papers together
challenge a paradigm, THAT would be a PROPOSE candidate.

## Antibody-name mentions in ingest logs (shard 15)

Gaebler 2022 ingest log: "Dual-bnAb trial (3BNC117 + 10-1074) in PLWH with
ATI" — 3BNC117 and 10-1074 are antibody names. Pages exist
(`caskey-2015-3bnc117-viremia`, `caskey-2017-10-1074-suppresses-viremia`).
But the mention is in an ingest log describing the trial, not an analytical
link to the Caskey papers. The antibody names the molecule, not the paper.
SKIP — same reasoning as ingest-log citation shorthand.

## EMFILE total lockout under parallel burst-wave workers (shard 31)

Shard 28 documented EMFILE on *batched* file ops (3+ parallel calls). Shard 31
hit a more severe variant: with many shard workers running concurrently, the
host fd table saturated so completely that **every** file/shell/process tool
returned `[Errno 24]` for ~5 minutes — not just batched calls.

### What keeps working during total EMFILE lockout

- `skill_view` — reads from the skill directory via a persistent connection.
- `session_search` — uses the session SQLite DB (already-open handle).

Both bypass new-fd spawning. This distinguishes fd *exhaustion* (these tools
still work) from a total system failure (they wouldn't).

### Recovery path

1. Retry a trivial `terminal` command (e.g. `true`) every ~30–60 s.
2. `terminal` recovers first and most reliably. The moment it returns, all
   other file tools follow within seconds.
3. Do NOT abandon the shard — wait it out, then proceed with strictly
   sequential (never batched) file operations for the rest of the run.

### Write fallback

If `write_file` is still failing after `terminal` recovers, write the result
file via `cat > <path> << 'EOF' … EOF` through `terminal`. The heredoc path
spawns fewer fds than `write_file` and succeeded where `write_file` failed
(observed in shard 31).

## Frontmatter-sync pattern confirmed at scale (shard 31)

8 of 10 pages in shard 31 were mature paper pages (importance 0.55–0.90,
full Context/Approach/Findings/Limitations/Analysis sections) that arrived
already body-wikilinked but with `links:` unsynchronized. The shard-28
pattern held: ~0 new body LINKs, ~2–5 frontmatter-sync entries per mature
page. Total: 1 new body LINK (IgFold in ghostfold), 8 frontmatter-sync
mutations across 8 pages.

## Grant-identifier shorthand in Analysis sections

Several pages reference grants by identifier shorthand in their Analysis
sections (e.g. "R01AI180120 grant's Aim 3", "R01AI180120" as a label).
These are NOT verbatim entity names (the page slug is
`r01ai180120-prepandemic-cov-bnab-west-africa`), so they do not qualify for
LINK. A `cites:` edge from paper→grant is also invalid direction (the grant
cites the paper via `cited_by`, not vice versa). SKIP these — the
relationship is already captured in the grant's `cited_by` frontmatter.

## Pages with zero body wikilinks

The pinto-2021-s2p6 page had NO `[[...]]` body wikilinks at all, despite
being a rich, mature page. Its Analysis section discusses grants and
projects by shorthand label ("preexisting-cov-immunity / R01AI180120 Aim 3:")
rather than by wikilink. This is a filing-style variation, not a gap to
force-fill — the frontmatter `links:` carries the relationships. SKIP.
