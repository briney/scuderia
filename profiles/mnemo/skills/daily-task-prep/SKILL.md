---
name: daily-task-prep
description: Morning preparation — calendar lookahead, meeting context, yesterday's open threads, and active-task review. Extends briefing with actionable prep for the day ahead.
triggers:
  - "morning prep"
  - "prepare for today"
  - "what's on my plate"
  - "day prep"
---

# Daily task prep — get the day ready

Where `briefing` *curates attention*, prep *readies action*. It extends the
brief: same brain, same attention contract, but the output is what Bryan should
*do* before and during today — meeting prep cards, unresolved threads to pick
back up, the tasks that need a decision today.

> **Conventions:** `skills/conventions/brain-first.md` (the lookup chain),
> `skills/conventions/quality.md` (citations),
> `skills/conventions/capabilities.md` (the harness contract). This skill extends
> `skills/briefing/SKILL.md` — read it first; the four attention-contract
> properties apply here too.

## Capabilities

- **Required:** `brain-read`, `brain-search`, `calendar-read`,
  `user-model-query`.
- **Optional:** `gmail-read` (for inbox-derived prep items).
- **Hermes-only:** `calendar-read`, `gmail-read`. Under harnesses
  without them, this skill refuses cleanly — the prep is fundamentally
  about today's external calendar, not the brain's static state.

## What this guarantees

- Every meeting today is loaded with context: attendee `people` pages, the
  thread connecting them to Bryan, the open items between them.
- Yesterday's unresolved threads are surfaced, not dropped.
- Active `task` pages are reviewed by deadline and priority.
- The output is **actionable** — what to do, not merely what exists.

## Phases

1. **Calendar lookahead.** For each `meeting` page dated today, build a prep
   card: read the meeting page, then the `people` page of every attendee — who
   they are, recent threads with Bryan, open items between them. End each card
   with the prep itself: what Bryan should know walking in, what decision the
   meeting needs from him.

2. **Yesterday's open threads.** Find what moved yesterday and did not close —
   meeting follow-ups, a hypothesis left mid-argument, a grant section paused, a
   reply owed. Cross `RESEARCH.md` threads with recently-changed pages. Flag each
   unresolved item with enough context to resume it cold.

3. **Active-task review.** Read the `task` pages in `tasks/`. Surface the ones
   that need attention today — by deadline proximity and the `priority`
   frontmatter field (`daily-task-manager` owns the lifecycle and the schema).
   Apply the escalation curve from `briefing`: a task due today is loud, one due
   in three weeks is a whisper.

4. **Compile the prep brief.** Per-meeting context cards, then open threads,
   then today's tasks. Each item carries the next action, not just a label.

## Output

Delivered text, not a brain page — follows `_output-rules.md`. Read-only: prep
reviews the brain, it does not edit it.

```
MORNING PREP — {date}
Meetings today: {N}

## {meeting title} — {time}
Attendees: {name} — {context from people/<slug>}
Threads: {recent interactions, open items}
Prep: {what to know, what decision is needed}

## OPEN THREADS
- {thread from yesterday} — {context to resume it} — {next action}

## TASKS DUE / NEAR
- {task} — due {date}, priority {P} — {next action} — [[tasks/<slug>]]
```

Cite facts inline so Bryan can trace them, and name coverage gaps — an attendee
with no `people` page is a gap worth stating.

## Anti-patterns

- Listing meetings without loading attendee `people` pages.
- Dropping yesterday's unresolved threads.
- Presenting tasks with no deadline or priority order.
- Informational output — a prep card with no next action has not done the job.
- Editing the brain while prepping — prep is read-only.
