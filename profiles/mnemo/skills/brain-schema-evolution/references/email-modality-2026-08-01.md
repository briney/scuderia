# Worked example: email modality + the `meeting` → `interaction` rename (2026-08-01)

The second live exercise of `brain-schema-evolution`: your human proposed adding
email as a brain modality — his work email is exposed to a read-only CLI
(Spark), making cron-driven ingestion straightforward. The design conversation
produced one scope ruling, one new source stream, and the highest-blast-radius
schema change the brain has taken: renaming the `meeting` kind to
`interaction`. This note is the design record.

## The scope question (Step 1)

Email is a **source stream**, not a new content domain. The scope boundary
(`VISION.md` §6, `page-kinds.md`) is unchanged: research-program content is
in, personal-life content is out — structurally, by having nowhere to file
it. Two things make email comfortable under the existing line:

- The lab-management expansion (2026-07-30) explicitly deferred "automated
  project-state maintenance — meeting ingestion first, email/Slack streams
  later" as a known unsolved problem. Email ingestion is the named
  implementation of an already-approved open item, not a scope expansion.
- Personal mail is excluded **upstream**: only your human's work account is exposed
  to the Spark CLI. The raw archive never contains personal mail, and
  non-research-program work mail (HR, admin, listserv churn) simply produces
  no pages — the structural exclusion operates at the page layer as usual.

No north-star revision was required. `VISION.md` / `DESIGN.md` edits in this
unit of work are the kind rename only.

## The architecture: three layers

1. **Raw archive (R2, `email/` prefix).** One object per *message* — threads
   grow, and the archive is write-once, so a thread is assembled at distill
   time, never stored as a mutable whole. Key shape: `email/<sha256>.<ext>`
   per `raw-source-archive.md`. **Archive everything the work account
   returns; triage happens at distillation, never at pull time** — storage is
   cheap, and a pull-time filter that eats a real message is unrecoverable.
   Distilled pages carry `sources:` pointers exactly as grant pages do.
2. **Triage + distillation (the default path).** A cron-driven distiller runs
   the standard read → enrich → write loop over new mail, dropping noise and
   writing facts into existing person / project / grant / institution pages.
   The highest-value extract is **commitments and state changes** ("I'll have
   the sequences Friday", "the JIT deadline moved") feeding `tasks/` and the
   briefing — person enrichment is real but secondary; it is the filing
   destination, not the payload.
3. **Thread pages for the gated tail.** Most threads are noise; a thin tail
   (PO correspondence, collaboration negotiation, decision threads) passes
   the graph-hub test — a grant-negotiation thread needs inbound edges from
   the grant page, the PO's person page, the institution page. Those become
   `interaction` pages with `channel: email`. Volume is controlled by the
   existing notability gate (`skills/conventions/quality.md`), not by kind absence.

## The rename: `meeting` → `interaction`

The naive design was a `channel:` field on `meeting`. your human rejected it as
clunkier than renaming the kind — and he was right. The kind already covered
conference talks, which are not meetings; `interaction` is what it always
meant, and email threads (plus future Slack / phone / hallway modalities)
slot in without further schema conversations. The measured cost was small:
64 files with `kind: meeting`, exactly one page with inbound `[[meetings/…]]`
wikilinks (child-declares-parent edges mean almost nothing links in), four
skills, the docs, the linter, and `auto_push.sh`. The cost only grows once
email ingestion binds new skills and pages to the old name — so it was done
now, as the first schema step of this unit of work.

### Schema changes

| Change | Detail |
|---|---|
| Kind renamed | `meeting` → `interaction`; directory `meetings/` → `interactions/` |
| Field renamed | `attendees:` → `participants:` on all 63 existing pages (channel-neutral term; no skill parses the field programmatically — verified against `enrich` and `RESOLVER.md`) |
| New optional field | `channel:` on `interaction` — `in-person` \| `video` \| `phone` \| `email`, free text (the `grant.mechanism` precedent: not an enum). **Not backfilled** on pre-rename pages — the channel of historical meetings is not recorded and must not be fabricated |
| R2 prefix added | `email/` for raw email. Prefixes name the **source stream**, not the page kind: Granola transcripts stay at `meetings/` (existing objects are write-once and their keys are recorded in page frontmatter — no migration) |
| Convention broadened | `raw-source-archive.md` framed the archive as "nothing binary enters git." Email raw is *text*; it is archived out-of-git because it is correspondence (the repo pushes to GitHub) and because the archive exists for re-derivation. The convention now says so |

### What was deliberately NOT done

- **No `thread` kind.** The notable tail rides the renamed `interaction`
  kind; extending beats adding (Step 3).
- **No R2 key migration.** Existing `meetings/<hash>.json` objects stay;
  pointers in `avi.md`, `dzne.md`, and the 63 interaction pages remain valid.
- **No historical-doc rewrite.** Dated plan/spec/history docs
  (the instance's private `docs/plans/`, `docs/specs/`,
  `docs/rem-cycle/history/*`) record a point in time and keep their `meetings/`
  references. Living documents (AGENTS, README, DESIGN, TODOS, conventions,
  skills) were updated.
- **Skill names unchanged.** `granola-meeting-sync` syncs meetings and
  `meeting-ingestion` ingests meeting transcripts — meetings remain meetings;
  `interaction` is the broader kind they file under.

## The people-growth problem

Email ingestion will encounter far more correspondents than the graph has
people pages for. The solution is the **author-ledger precedent**: identity
lives in a ledger, pages are created through the notability gate. A contacts
ledger keyed on **email address** (a stable identifier — entity resolution
gets *easier* than the author-name problem, not harder) holds one line per
correspondent; promotion to a full `person` page happens at the second
substantive touch, a named role on a grant/project, or your human's flag. One-off
correspondents are named in prose on thread/project pages. Ledger mechanics
are deferred to the email-ingest skill design (extend `people/_ledger.yaml`
vs. a separate contacts ledger is an open question there).

## Rollout executed (Step 4)

1. This design note.
2. Conventions: `page-kinds.md` (kind table, email-as-source scope note),
   `frontmatter.md` (the `interaction` kind section), `raw-source-archive.md`
   (`email/` prefix, source-stream naming, email subsection).
3. Linter: `KINDS` map updated (`.github/scripts/lint-frontmatter.py`).
4. Skills: `meeting-ingestion`, `granola-meeting-sync`, `ask-user`,
   `RESOLVER.md` — vault copies and profile copies (identical edits).
5. Migration: `git mv meetings interactions`; `kind:` and `attendees:` sed
   across the 63 pages; `colton-consortium.md` wikilinks fixed;
   `auto_push.sh` `CONTENT_PATHS` updated. Verified by linter + residual
   greps. your human reviewed the shape in conversation before execution.

## Open items — the email build-out (Phase 0 onward)

- **Phase 0 — probe + calibrate.** Verify the Spark CLI's actual interface
  (incremental sync, folder/label filtering, output format, thread vs.
  message granularity — all unknown as of 2026-08-01). Hand-pull one week of
  mail; hand-distill ~20 threads to calibrate the notability gate.
- **Phase 1 — raw-archive cron.** Script-only (`no_agent`) job pulling new
  mail → R2 `email/`, with a sync-state watermark (the
  `.granola-sync-state.json` pattern).
- **Phase 2 — distillation with review.** Daily LLM cron; your human reviews
  output for a week before autonomous operation.
- **Phase 3 — autonomous**, with thread-page creation gated.
- **New skills to write:** an email source adapter (the `granola-meeting-sync`
  analog) and the distiller. The adapter must be shaped so a future
  mail-provider switch doesn't touch the brain — Spark CLI behind a thin
  normalizer.
- **Contacts ledger** implementation (see above).
- **Briefing / task wiring** for extracted commitments.
