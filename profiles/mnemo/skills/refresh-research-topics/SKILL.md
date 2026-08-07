---
name: refresh-research-topics
description: Keeps RESEARCH.md synchronized with the brain — auto-adds Bryan's explicit artifacts, auto-enriches existing entries, proposes derived topics to QUEUE.md. Weekly scheduled run plus on request.
triggers:
  - "refresh research topics"
  - "update RESEARCH.md"
  - "RESEARCH.md is stale"
  - a scheduled run (weekly)
---

# refresh-research-topics — keep RESEARCH.md synchronized with the brain

`RESEARCH.md` is the research program's state file: skills read it for
thread context, `literature-sweep` builds its query profile from it, the
attention contract reads its funding context. It decays by default — the
brain moves every day; a hand-maintained summary does not. This skill is
the standing refresh: it reconciles RESEARCH.md against the brain on a
weekly cadence, under a three-tier automation model (agreed with Bryan
2026-08-06).

> **Conventions:** `brain-ops` (never blind-overwrite; RESEARCH.md is a
> curated file — patch sections, don't regenerate the document),
> `skills/conventions/quality.md` (every claim traceable to a brain page),
> `docs/rem-cycle/rem-cycle-contract.md` (the decision ledger, QUEUE.md
> proposal format).

## The three-tier model

| Tier | What | Action | Approval |
|---|---|---|---|
| **1 — Explicit artifacts** | New `grants/` or `projects/` pages Bryan created (grant-ingest, direct request) | Add to RESEARCH.md automatically | None — Bryan's own artifact |
| **2 — Enrichment of existing entries** | Open questions, thread status, funding status, publication pipeline — driven by ingestions and page updates | Rewrite in place automatically | None — logged in the decision ledger |
| **3 — Derived topics** | New topics *inferred* by maintenance/synthesis (a concept cluster with no RESEARCH.md home, an emerging thread in ingestion patterns) | Propose to `docs/rem-cycle/QUEUE.md` | **Required** — never written directly |

Tier 3 mirrors the standing grant (2026-08-04) that synthesis queue items
never auto-execute. Approval paths are the existing ones: conversational
queue-drain, rem-cycle phase 0, or brief replies.

## Capabilities

`brain-read`, `brain-search`, `brain-write` (RESEARCH.md, QUEUE.md,
decision ledger). No external I/O.

## Phases

1. **Load current state.** Read `RESEARCH.md` in full. Read the refresh
   cursor from `docs/rem-cycle/_state.yaml`
   (`research_topics.last_run`). Read `docs/rem-cycle/inbox.yaml` for
   page-write packets since the last run.

2. **Tier 1 — add explicit artifacts.** List `grants/*.md` and
   `projects/*.md` created since the last run (inbox packets first; git
   log as backstop). For each new page: read its frontmatter and opening
   section; write a RESEARCH.md entry in the house style (one-line
   framing + current open question for domains; funder / status / amount
   / deadline for funding context). Skip pages whose status is `dropped`
   or `dormant`. Provenance test: `grants/` pages are always
   Bryan-explicit (grant-ingest is Bryan-initiated). `projects/` pages
   created by a *synthesis* process are NOT tier 1 — they are tier 3;
   check the page's creation context (its ingest log / Shift trail)
   before treating a project page as explicit.

3. **Tier 2 — enrich existing entries.** For each entry already in
   RESEARCH.md, re-read the linked page(s) and update what changed:
   - **Domains:** the open question (has the project page reframed it?),
     the framing line (has the project pivoted?).
   - **Threads:** status movement (stage completions, new next steps) —
     from the project page and recent concept `## Shifts`.
   - **Funding context:** status transitions visible on grant pages
     (`submitted` → `funded`, `planned` → `dropped`, new deadlines).
   - **Publication pipeline:** derive from `papers/` entries with
     `status: preprint` — list lab-authored manuscripts in flight, most
     recent first. (This section is chronically stale by hand; the
     refresh owns it.)

   **The flag-don't-guess rule.** When a page's state contradicts
   RESEARCH.md in a way that needs a human call — a `planned` grant
   whose deadline passed, a `submitted` grant with a decision the page
   doesn't record — do NOT resolve it. Add an inline `> **Flag
   (date):**` blockquote stating the contradiction. Flags are the
   refresh's way of asking Bryan a question in writing. (Exemplar: the
   GCGH diagnostics grant, flagged 2026-08-06 backfill, resolved by
   Bryan same-day as dropped.)

4. **Tier 3 — propose derived topics.** Look for research activity with
   no RESEARCH.md home:
   - Concept pages created since the last run that cluster (3+ pages
     sharing a theme) without mapping to an existing domain.
   - Ingestion patterns: a burst of paper pages on a theme not covered
     by any active domain.
   - Hypotheses or notes that have attracted 3+ supporting paper links
     without a project to anchor them.
   For each candidate, write a QUEUE.md proposal (per the rem-cycle
   contract format): the proposed RESEARCH.md entry text, the evidence
   (the pages and their links), and the reasoning. Never write tier-3
   topics into RESEARCH.md directly.

5. **Write and log.** Patch RESEARCH.md section by section (never
   regenerate the file). Update the `Last refresh:` line in the header.
   Append one `decisions.yaml` entry per tier-1/tier-2 write with the
   revert banner. Update the cursor (`research_topics.last_run`).
   Commit: `refresh-research-topics: <n> added, <m> enriched, <k>
   proposed, <f> flagged`.

6. **Report.** A compact summary: entries added, entries enriched,
   QUEUE.md proposals (with qids), flags raised. This is the job's
   deliverable output.

## What this guarantees

- RESEARCH.md never silently drifts from the brain — tier 1 and tier 2
  keep it synchronized with explicit activity.
- No inferred topic enters the research program's state file without
  Bryan's explicit approval — tier 3 proposals are visible in QUEUE.md
  with evidence attached.
- Every automatic write is logged and revertible (decision ledger +
  commit history).
- Contradictions surface as flags, not silent edits.

## Anti-patterns

- **Regenerating RESEARCH.md wholesale.** The file carries curated
  framing (Bryan's voice in entry text). Patch sections; preserve
  hand-written lines that are still accurate.
- **Treating synthesis-created pages as tier 1.** A project page born
  from topic-synthesis is an inference, not an explicit artifact —
  wrong tier.
- **Guessing status transitions.** A deadline that passed is a flag,
  not a `dropped`. A missing decision is a flag, not a `not-funded`.
- **Letting the publication pipeline go stale silently.** If no
  `status: preprint` papers exist, say so in the section rather than
  leaving a placeholder that looks like neglect.
- **Proposing tier-3 topics without evidence.** A QUEUE.md proposal
  must name the pages and links that justify the topic — a vibe is not
  a proposal.
