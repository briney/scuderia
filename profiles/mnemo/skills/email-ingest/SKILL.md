---
name: email-ingest
description: Use when ingesting work email via Spark CLI.
triggers:
  - "ingest email"
  - "email sync"
  - "spark email pull"
  - "email distillation"
  - cron-driven email sync
---

# Email ingestion — work email as a brain source stream

Your human's work email (you@institution.edu) is a raw source: archived to R2
under the `email/` prefix, distilled into existing brain pages (person,
project, grant, institution), with notable threads becoming `interaction`
pages (`channel: email`) through the notability gate.

**Read-only.** The Spark CLI exposes read-only access to the work account.
The mind never writes, sends, or drafts email. This is by design — email is
a source stream, not a communication channel for the brain.

> **Conventions:** `conventions/raw-source-archive.md` (R2 `email/` prefix),
> `conventions/page-kinds.md` (email scope note), `conventions/quality.md`
> (the notability gate).

> **Design record:**
> `skills/brain-schema-evolution/references/email-modality-2026-08-01.md`
> — the full architecture decision, including the `meeting` → `interaction`
> rename that made email threads a first-class page kind.

> **Phase 0 calibration:**
> `working-docs/email-phase0-calibration-2026-08-01.md` — the hand-distilled
> 20-thread calibration that produced the notability gate rules.

## Architecture: three layers

1. **Raw archive (R2, `email/` prefix).** One object per *thread* — the
   `spark thread` command returns the full thread in one call, so the
   adapter hashes and archives the entire thread output. Threads grow
   over time (a single thread can span months), but the archive is
   write-once: a re-pull returns the same text, producing the same hash.
   Archive everything the work account returns; triage happens at
   distillation, never at pull time. Both Inbox and Sent are pulled —
   Bryan's replies contain half the signal.

2. **Triage + distillation (the default path).** A cron-driven distiller
   runs the read → enrich → write loop over new mail, dropping noise and
   writing facts into existing person / project / grant / institution pages.
   The highest-value extracts are **commitments and state changes** (not
   person enrichment, which is secondary).

3. **Thread pages for the gated tail.** Most threads are noise; a thin tail
   (PO correspondence, collaboration negotiation, decision threads) earns
   `interaction` pages via the notability gate. Volume is controlled by
   the gate, not by kind absence.

## The Spark CLI adapter

The source adapter is the Spark CLI (`/usr/local/bin/spark`), which
requires Spark Desktop running. The adapter is behind a thin normalizer so
a future mail-provider switch doesn't touch the brain.

Adapter script: `~/.hermes/profiles/<instance>/scripts/spark-email-sync.py`
Supports: `--backfill` (full archive, skips existing), `--test N` (limit),
default mode (incremental sync since last_sync watermark).

See `references/spark-cli-interface.md` for the verified CLI capabilities,
commands, output format, and the pagination-cap gotcha.

## The notability gate

Calibrated from 20 hand-distilled threads (Phase 0, 2026-08-01). See
`references/notability-gate.md` for the full gate rules, tier system, and
extract types.

### Gate summary

A thread earns an `interaction` page if ANY of:
- 3+ messages with substantive research discussion (not scheduling)
- Grant score / award notice with discussion / summary statement
- Decision to start/modify/terminate a collaboration
- Experimental data exchange with interpretation and next steps
- A commitment from Bryan with a concrete deadline and deliverable

A thread is enrichment-only if it mentions people/projects/grants but is
logistical or administrative. Everything else is noise — no page, no
enrichment.

## Contacts ledger

Email encounters far more correspondents than the brain has people pages
for. A contacts ledger keyed on **email address** (a stable identifier —
entity resolution is easier than the author-name problem) holds one line per
correspondent. Promotion to a full `person` page happens at the second
substantive touch, a named role on a grant/project, or Bryan's flag.
Implementation details are deferred (extend `people/_ledger.yaml` vs.
separate contacts ledger is an open question).

## Phases

- **Phase 0 — probe + calibrate.** DONE (2026-08-01). Verified CLI, pulled
  one week, hand-distilled 20 threads, calibrated gate. Full backfill
  (Inbox + Sent, ~17K messages, ~2700+ unique threads) archived to R2.
- **Phase 1 — raw-archive cron.** Script-only (`no_agent`) job pulling new
  mail → R2 `email/`, with a sync-state watermark.
- **Phase 2 — distillation with review.** Daily LLM cron; Bryan reviews
  output for a week.
- **Phase 3 — autonomous**, with thread-page creation gated.

## Anti-patterns

- Writing email on your human's behalf — the CLI is read-only and the mind never
  sends email.
- Creating a page for every thread regardless of notability.
- Discarding messages at pull time — archive everything, triage at
  distillation.
- Pulling Inbox only — Sent contains half the signal (Bryan's commitments
  and decisions).
- Relying on `total_pages` from the first listing page — Spark caps at
  "20+"; keep paging until empty (see `references/spark-cli-interface.md`).
