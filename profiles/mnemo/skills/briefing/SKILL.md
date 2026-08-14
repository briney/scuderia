---
name: briefing
description: Compose the daily brief — the attention contract in action. Reads the brain plus the live Calendar and Gmail capabilities, spawns `literature-sweep` for recent publications, writes the rolling `BRIEFING.md`, and Hermes delivers it. Surfaces calendar and meetings, deadlines, publications of interest, threads in flight, a short focus list, and what fell through the cracks.
triggers:
  - "daily briefing"
  - "morning briefing"
  - "what's happening today"
  - "deadline status"
  - the scheduled morning brief
---

# Briefing — the attention contract in action

The brief is not a list-printer. It is the **attention contract** (`VISION.md`
§5, `DESIGN.md` §4.5) made concrete: a filter on your human's attention that surfaces
signal and silences noise. The skill *composes* the brief — against the brain,
and against your human's live calendar and inbox — writes the result to the rolling
`BRIEFING.md`, and Hermes *delivers* it — to Telegram at the scheduled hour, or
to the terminal on request (`DESIGN.md` §6.3). This skill owns the editorial
judgment, nothing else.

> **Conventions:** `skills/conventions/brain-first.md` (the lookup chain),
> `skills/conventions/quality.md` (citations), `skills/conventions/importance-scoring.md` (the
> salience score the relevance bar leans on),
> `skills/conventions/capabilities.md` (the harness contract).

## Capabilities

- **Required:** `brain-read`, `brain-search`, `gmail-read`,
  `calendar-read`, `user-model-query`, `deliver-message` (or at minimum
  `send-notification` + `schedule-job`).
- **Hermes-only:** `gmail-read`, `calendar-read`, `deliver-message`,
  `send-notification` — the attention contract is fundamentally a
  delivery loop. Under harnesses that don't provide these (Claude Code),
  this skill **refuses cleanly**: it can still compose a
  brain-only brief on synchronous request, but the calendar/inbox
  surface is empty and there is no out-of-band delivery channel.

## The attention contract — four properties

Every brief honors all four. They are the difference between a trusted filter
and one more thing pinging your human.

1. **A relevance bar drawn from the user model.** What matters is what matters
   *to your human specifically* — read from `USER/<name>.md` via `user-model-query`, not
   a global heuristic. Consult your human's declared priorities, taste, and what
   he has named as in- vs. out-of-scope; weight the brief against that,
   alongside page `importance`.
2. **A default of silence.** Nothing surfaces unless it clears the bar. A quiet
   day produces a short brief — or a near-empty one. Padding the brief to look
   thorough breaks the contract.
3. **Escalation that scales with stakes and proximity.** A grant deadline at
   T-90 is a whisper — one line, low in the brief. At T-30 it is a clear
   heading. At T-7 it leads the brief and says exactly what is unfinished. The
   same proximity curve applies to progress reports, paper submissions, IRB
   renewals, and review obligations.
4. **An auditable ignore-report.** Close every brief with a short, explicit
   "here is what I decided you could ignore" — the items that did not clear the
   bar and why. The filter must be *legible* so your human can correct it; a
   black-box filter cannot earn trust.

## Phases

1. **Set the relevance bar.** Read `USER/<name>.md` via `user-model-query` for
   your human's declared priorities, domain priors, and what they have named as in-
   vs. out-of-scope. This is what separates signal from noise for the rest of
   the brief — do it first.

2. **Today's calendar and inbox.** Read today's events via `calendar-read`
   and scan recent mail via `gmail-read` (under Hermes both are bound through
   spark-cli — the binding is documented in `docs/harnesses/hermes.md`, not
   here). The calendar is the real schedule; the inbox surfaces meeting invites,
   replies owed, and deadline-bearing messages. Route what you find into the
   sections below — an event into meetings, a hard date into deadlines, a reply
   owed into today's focus. When the capability is unavailable, say so plainly
   and compose from the brain alone.

3. **Today's meetings.** For each event on today's calendar, find its `meeting`
   page if one exists, then read the `people` pages of each attendee for
   context — who they are, the thread that connects them to your human, the last
   interaction. When an attendee has no `people` page, name the gap ("no page
   for J. Okafor — consider enrich").

4. **Deadlines bearing down.** Read deadline fields from `grant` and `task` page
   frontmatter, the funding context in `RESEARCH.md`, and any hard dates pulled
   from the inbox. The deadlines that matter: grant submissions, progress
   reports, paper submissions, IRB renewals, peer-review obligations, research
   travel. Compute T-minus for each and apply the escalation curve from property
   3 — proximity *and* stakes set how loud each one is. A T-90 grant is a
   whisper; a T-7 grant leads.

5. **Recent publications.** Spawn `skills/literature-sweep/SKILL.md` as a
   parallel sub-agent — it is heavy, keep it off the main pass. It returns a
   ranked shortlist of very recent work matching the research program. Fold in
   only the items that clear the relevance bar from phase 1; the rest belong in
   the ignore-report, not the brief.

6. **Threads in flight.** Surface the open research threads with recent
   movement — projects with activity, hypotheses gathering evidence, a grant
   section mid-draft. `RESEARCH.md` is the map of threads in flight; cross it
   with pages changed recently to find what is genuinely moving.

6a. **Standing monitors.** Read `MONITORS.md` (vault root, operational state —
   `skills/monitor-the-situation/SKILL.md` owns it). Surface any item whose
   `state.last-fired` is newer than the last brief *and* whose `routing` is
   `briefing-only` or `both` — these are significant hits the monitor sweep
   caught and routed to the brief. Give each one line with its resolvable link.
   `immediate`-only hits were already pushed to Telegram and do not repeat here.
   Most days no monitor has fired — then this section is absent, not padded.
   This is a read; the brief never edits `MONITORS.md`.

6b. **Funding opportunities.** Read `last-surfaced` from `FUNDING-PROFILE.md` (vault
   root, operational state — `skills/funding-sweep/SKILL.md` owns it). This is a
   **read of the cron's output, never a re-run of the sweep** — funding-sweep is
   stateful and the daily cron is its sole driver (see that skill's driver contract).
   Fold `last-surfaced.items` into the DEADLINES surface — a funding opportunity is
   deadline-bearing and deserves the same proximity escalation. If `last-surfaced.date`
   is stale (older than ~2 days — the cron likely failed), say so rather than
   presenting old hits as current. An empty `items` on a fresh date means the sweep
   ran and nothing cleared the bar — that section is simply absent, not padded.

7. **Notable recent brain changes.** Pages created or substantially edited since
   the last brief, filtered by `importance` and the relevance bar — not every
   touched file, only the ones that clear the bar.

7a. **Brain review queue.** Read `docs/rem-cycle/QUEUE.md`. Take up to 3
    unchecked items, ranked confidence desc then age desc, excluding qids in
    `_state.yaml → briefing.last_surfaced` (rolling — nothing nags daily).
    Render each as one line: ordinal · qid · category · target · the change ·
    conf · age. Update `last_surfaced` (this is the brief's one permitted write
    beyond BRIEFING.md). Empty queue → section absent, not padded. Approval path
    in the section footer: `approve 1-2` / `reject 2` / `approve all` — executed
    by `queue-drain`.

8. **Today's focus.** Two or three bullets — no more — naming the highest-stakes
   things your human should be thinking about or working on today. This is a
   synthesis of the loudest items from phases 4–7, not a task list:
   `daily-task-prep` owns the detailed, actionable version. If nothing rises to
   the top, say so rather than manufacturing focus items.

9. **Resurface what fell through the cracks.** Occasionally — *not* every day —
   surface one high-impact item that has genuinely gone quiet: a stalled thread,
   an unanswered obligation, a paper revision left untouched. The gate is
   strict: the item must be (a) high-impact, and (b) *neglected*, not
   deliberately postponed — a moderate-importance item put off on purpose never
   qualifies. Most days this section is empty. If you cannot name why an item is
   both important and forgotten, leave it out.

10. **Compose the ignore-report.** List what was considered and dropped,
    briefly, with the reason. This is a required section, not an optional one.

## Source precedence

When the brain and the user-model bar point different ways, neither overrides
the other — `USER/<name>.md` sets *what your human cares about*, the brain holds *what
is true and what is due*. Surface a real deadline even if `USER/<name>.md` does not
flag the topic; let the user-model bar govern the softer, judgment-call
items.

## Output

The brief follows `_output-rules.md` (deterministic links, no slop, no LLM
preamble). It is written to **`BRIEFING.md` at the vault root** — a rolling
delivery artifact, overwritten every run; git history is the archive of past
briefs. Hermes delivers the same text to Telegram. `BRIEFING.md` is *not* a
brain page: it has no `kind`, it lives in no page directory, and it is excluded
from the knowledge graph. Composing the brief is otherwise **read-only** — it
never creates or edits brain pages unless your human explicitly asks. Writing
`BRIEFING.md` is the one exception, and it is a delivery artifact, not knowledge.

When a weekly **synthesis briefing** newer than the last daily brief exists
(`docs/rem-cycle/briefings/<date>.md`, written by `synthesis-briefing`), surface a
one-line pointer to it. That weekly digest — precipitated hypotheses and concept
movements — is a distinct *intellectual* surface from this daily *attention* brief:
point to it, do not inline it.

```
DAILY BRIEF — {date}

TODAY'S FOCUS
- {one of the 2-3 highest-stakes things for today}

MEETINGS TODAY
- {time} {meeting title}
  {attendee} — {one line of context from people/<slug>}

DEADLINES
- {item} — T-{N}, {grant/task slug} — {what is unfinished, if close}

RECENT PUBLICATIONS
- {title} — {authors, year} — {why it clears the bar} — {DOI/PMID/arXiv id}

THREADS IN FLIGHT
- {project/hypothesis} — {recent movement}

MONITORS                                      (omit the section entirely when nothing fired)
- {item title} — {what changed} — {resolvable URL}

RECENT IN THE BRAIN
- {kind/slug} — {what changed}

BRAIN REVIEW QUEUE                            (omit the section entirely when empty)
1. `{qid}` {category} · {target} · {the change} · conf {N} · {age}d
2. `{qid}` {category} · {target} · {the change} · conf {N} · {age}d
   reply "approve 1-2" / "reject 2" / "approve all"

RESURFACED                                    (omit the section entirely when empty)
- {item that fell through the cracks} — {why it matters, why it surfaces now}

DECIDED YOU COULD IGNORE
- {item} — {why it did not clear the bar}
```

Cite facts inline so your human can trace and judge freshness:
"co-PI on [[grants/<slug>]] [Source: people/j-okafor, updated
2026-05-02]". When a page is stale (untouched 30+ days), say so rather than
presenting it as current.

## Anti-patterns

- Padding the brief to look thorough — silence is the default.
- A flat deadline list with no proximity escalation — T-90 and T-7 must not read
  the same.
- A bloated "today's focus" — it is 2-3 bullets, not the actionable task list
  `daily-task-prep` owns.
- Resurfacing a deliberately-postponed item, or running the resurface section
  every day — it is rare and reserved for high-impact neglect.
- Ignoring the review queue — an invisible queue never drains; the brief is its
  only regular surface.
- Omitting the ignore-report — an unauditable filter cannot earn trust.
- Composing from memory instead of reading the `meeting`, `people`, `grant`, and
  `task` pages, or the live calendar and inbox.
- Uncited facts, or stale context presented as fresh.
- Editing brain pages while composing — the brief is read-only against the brain
  (`BRIEFING.md`, the delivery artifact, aside).
- Treating `BRIEFING.md` as a brain page, or filing the brief into a page
  directory — it is a delivery artifact, not knowledge.
