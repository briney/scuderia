---
name: email-ingest
description: Use when ingesting work email via Spark CLI.
triggers:
  - "ingest email"
  - "email sync"
  - "spark email pull"
  - "email distillation"
  - cron-driven email sync
eval_contract:
  goal: |
    Archive and distill the work mailbox into existing brain pages without
    ever writing email, with the notability gate as the only path to an
    interaction page.
  dimensions:
    - "READ_ONLY — no write command (draft/action/comment/event) is ever invoked; reads stay scoped to the configured work account"
    - "ARCHIVE_FIDELITY — everything returned is archived (Inbox and Sent), one R2 object per thread version"
    - "GATE_DISCIPLINE — interaction pages only through the notability gate; noise gets no page and no enrichment"
    - "SOURCE_TRUTH — CLI and adapter claims match the installed adapter script and `spark help`, not a missing reference"
  hard_fails:
    - Sending, drafting, or acting on email from any account.
    - Creating an interaction page for a thread that fails the notability gate.
    - Claiming archival or distillation completion without verifying the output.
---

# Email ingestion — work email as a brain source stream

Your human's work email (you@institution.edu) is a raw source: archived to R2
under the `email/` prefix, distilled into existing brain pages (person,
project, grant, institution), with notable threads becoming `interaction`
pages (`channel: email`) through the notability gate.

**Read-only, by policy.** The Spark CLI also has write commands (`draft`,
`action`, `comment`, `event`, `contact-action`) and can see every account
configured in Spark Desktop — the bare `Inbox` folder is the cross-account
unified inbox. This skill never invokes a write command and scopes all reads
to the configured work account. Email is a source stream, not a
communication channel for the brain.

> **Conventions:** `skills/conventions/raw-source-archive.md` (R2 `email/` prefix),
> `skills/conventions/page-kinds.md` (email scope note), `skills/conventions/quality.md`
> (the notability gate).

> **Design record:**
> `skills/brain-schema-evolution/references/email-modality-2026-08-01.md`
> — the full architecture decision, including the `meeting` → `interaction`
> rename that made email threads a first-class page kind.

> **Calibration evidence:** keep source threads and adjudicated examples in
> the instance. The operational gate below does not require a private report.

## Architecture: three layers

1. **Raw archive (R2, `email/` prefix).** One object per *thread version* —
   the `spark thread` command returns the full thread in one call, so the
   adapter hashes and archives the entire thread output, keyed on that
   hash. Threads grow over time (a single thread can span months), so a
   re-pull of a grown thread returns changed text, a new hash, and a new
   object; an unchanged re-pull rewrites the same key harmlessly.
   Archive everything the work account returns; triage happens at
   distillation, never at pull time. Both Inbox and Sent are pulled —
   your human's replies contain half the signal.

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
default mode (incremental sync since last_sync watermark). It has no
argument parser — every invocation runs a sync (`--test` still writes to R2
and advances the watermark), so read the script rather than probing it.

**Verified CLI surface** (re-check with `spark help <subcommand>`; the CLI
evolves): `emails` returns a fixed-width listing and `thread <message-id>`
returns structured text with headers and bodies. Do not parse them as JSON.
Inspect other read-command help before using it; attachment output is not
an email listing. Resolve thread IDs from work-account-scoped listings.
The `emails` listing takes `--page`/`--page-size` and Gmail-style `--filter`
operators (e.g. `after:YYYY/MM/DD` for incremental pulls), and folder
arguments must be the work account's qualified folders
(`<work-address>:Inbox`, `<work-address>:Sent`).

## The notability gate

Apply the research-program scope in the instance's AGENTS.md first. Personal
and lab-operational mail does not become brain content. The tiers below
are the complete operational gate; private calibration examples are evidence,
not an additional required procedure.

### Tier 1: interaction page

A thread earns an `interaction` page if ANY of:
- 3+ messages with substantive research discussion (not scheduling)
- Grant score / award notice with discussion / summary statement
- Decision to start/modify/terminate a collaboration
- Experimental data exchange with interpretation and next steps
- A commitment from your human with a concrete deadline and deliverable

### Tier 2: enrichment only

Update existing pages without a thread page when logistics reveal a
research-program delta: project status in scheduling mail, an award or
reporting notification without discussion, or a relevant administrative
request. A mere mention with no new fact warrants no edit.

### Tier 3: no action

Newsletters, marketing, routine notifications without research content,
and other noise get no page and no enrichment.

Extract grant state changes into grant pages; collaboration decisions and
project status into project pages; sourced roles and affiliations into
person/institution pages. Preserve experimental interpretation and material
exchange details in the qualifying interaction, without turning private
correspondence into established scientific evidence. Route research-program
commitments and deadlines through `skills/daily-task-manager/SKILL.md`;
route person promotion through `skills/enrich/SKILL.md`. Retain message-level
source attribution and avoid duplicating facts from overlapping thread versions.

## Contacts ledger

Email encounters far more correspondents than the brain has people pages
for. A contacts ledger keyed on **email address** (a stable identifier —
entity resolution is easier than the author-name problem) holds one line per
correspondent. Promotion to a full `person` page happens at the second
substantive touch, a named role on a grant/project, or your human's flag.
Implementation details are deferred (extend `people/_ledger.yaml` vs.
separate contacts ledger is an open question).

## Phases

- **Phase 0 — probe + calibrate.** DONE (2026-08-01). Verified CLI, pulled
  one week, hand-distilled 20 threads, calibrated gate. Full backfill
  (Inbox + Sent, ~17K messages, ~2700+ unique threads) archived to R2.
- **Phase 1 — raw-archive cron.** Script-only (`no_agent`) job pulling new
  mail → R2 `email/`, with a sync-state watermark.
- **Phase 2 — distillation with review.** Daily LLM cron; your human reviews
  output for a week.
- **Phase 3 — autonomous**, with thread-page creation gated.

## Anti-patterns

- Writing email on your human's behalf — read-only is this skill's policy;
  the CLI itself has write commands, and none of them is ever invoked.
- Creating a page for every thread regardless of notability.
- Discarding messages at pull time — archive everything, triage at
  distillation.
- Pulling Inbox only — Sent contains half the signal (your human's commitments
  and decisions).
- Relying on `total_pages` from the first listing page — Spark caps the
  reported total at "20+" in the observed adapter format; continue until an
  empty page rather than treating that cap as the last page. If the format
  changes or parsing fails, stop and report it rather than claiming completion.
