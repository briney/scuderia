---
name: remind
description: Create a time-based reminder — "remind me to X at TIME" creates a cron job that delivers across all gateways and logs to working-docs/reminders-log.md.
triggers:
  - "remind me to"
  - "remind me at"
  - "set a reminder"
  - "remind me"
---

# Remind — lightweight time-based reminders

A reminder is a non-research, non-task nudge: "check if Spark is running,"
"follow up on the MTA thread," "take a break." It is not a `task` page (those
are research-program deliverables with deadlines) and not a brain page (no
kind, no frontmatter, no graph edges). The record is an append-only log line
in `working-docs/reminders-log.md`; the delivery is a cron job.

The separation from `tasks/` is deliberate. `daily-task-manager` is
research-program-scoped — grant deadlines, paper submissions, progress
reports. Reminders are the lighter-weight complement: operational nudges,
personal prompts, "check on X" items that don't warrant a page but do warrant
a durable record. If a reminder turns out to be research-program-relevant, it
can be promoted to a `task` page — same promotion pattern as other
working-docs content.

> **Conventions:** `working-docs/README.md` (the log is not a brain page),
> `brain-ops` (never blind-overwrite the log — read before appending).

## Capabilities

`cronjob` (create the delivery job), `file` (append to the log). The cron
job runs with `deliver=all` (gateway-agnostic) and `attach_to_session=true`
(conversational — the user can reply and the agent has context).

## What this guarantees

- Every reminder fires across all connected gateways (Telegram, Buzz, future
  platforms) — no per-gateway configuration.
- Every reminder is logged to `working-docs/reminders-log.md` with the fire
  time, content, and a status field that updates when the reminder fires.
- One-shot reminders clean up after firing (the cron job runs once; the log
  entry persists).
- Recurring reminders ("every Monday at 9am") use a recurring cron schedule;
  the log entry records the recurrence.
- The reminder is conversational: `attach_to_session=true` means the user can
  reply and the agent has the reminder's context.

## Phases

1. **Parse the request.** Extract the time and the content from natural
   language:
   - "remind me tomorrow at 9:30am to check on Spark" → one-shot, 2026-08-03T09:30
   - "remind me every Monday at 9am to review the funding sweep" → recurring
   - "remind me in 2 hours to email Dennis" → one-shot, now + 2h
   - "remind me at 3pm" → one-shot, today 15:00 (content from context)

   Convert to an ISO 8601 timestamp with timezone. Default timezone is
   your human's local timezone (America/Los_Angeles). For relative times
   ("tomorrow", "in 2 hours"), compute from the current time.

2. **Create the cron job.** Use `cronjob` with:
   - `schedule`: ISO timestamp for one-shot, or cron expression for recurring.
   - `deliver`: `all` (gateway-agnostic).
   - `attach_to_session`: `true` (conversational — replies come back to the
     agent with context).
   - `prompt`: a self-contained instruction to deliver the reminder. Include
     the reminder content verbatim, plus any context the agent needs to act
     on the reply (e.g., "if Spark is up, re-run the backfill script at X").
   - `name`: `reminder-<short-slug>` for identification.
   - For recurring reminders, `repeat=forever` and a cron schedule.

3. **Append to the log.** Read `working-docs/reminders-log.md` first (never
   blind-overwrite), then append a new line:

   ```
   - 2026-08-03 09:30 | spark-check | Check if Spark Desktop is running, re-run backfill if up | status: scheduled | job: 13a653d2c68a
   ```

   Fields, pipe-separated:
   - **fire time** — ISO timestamp (local timezone, readable)
   - **slug** — short identifier for the reminder
   - **content** — the reminder text, verbatim from the request
   - **status** — `scheduled` → `fired` → `completed` (or `cancelled`)
   - **job** — the cron job ID (for reference; the job is the delivery
     mechanism, the log is the record)

4. **Confirm.** Tell your human plainly: the reminder is set, when it fires, and
   what it will say. No preamble.

## When the reminder fires

The cron job's prompt should instruct the agent to:
1. Deliver the reminder content to your human.
2. If the reminder has an actionable follow-up (e.g., "re-run the backfill"),
   offer to do it or do it if the context is clear.
3. Update the log entry's status from `scheduled` to `fired` (or `completed`
   if the action was taken).

## Promotion to task

If a reminder is research-program-relevant (e.g., "remind me to follow up
on the RCA MTA by Friday"), consider promoting it to a `task` page via
`daily-task-manager` instead of — or in addition to — this skill. The test:
does this have a research-program deadline that `briefing` should track? If
yes, it's a `task`. If it's a nudge with no deliverable, it's a reminder.

## Anti-patterns

- Creating a `task` page for a lightweight nudge — use the log instead.
- Using `deliver=origin` or a single gateway — reminders should be
  gateway-agnostic (`deliver=all`).
- Omitting `attach_to_session` — the user should be able to reply and have
  the agent act on the reply with context.
- Blind-overwriting the log — read before appending (`brain-ops`).
- Not recording the cron job ID in the log — the ID is how you find and
  cancel a reminder later.
- Creating a reminder without a clear, actionable content string — "remind
  me about that thing" is not a reminder; clarify before creating.

## Future expansion: per-reminder gateway selection

Currently all reminders use `deliver=all` (fan out to every connected
gateway). This is correct while there is only one real gateway (Telegram).
When multiple gateways are live (Buzz, Slack, etc.), the user may want to
target a reminder to a specific gateway — e.g., a work-related reminder to
Buzz, a personal one to Telegram. Implementation is deferred until there
are multiple gateways to select from; the `deliver` parameter on `cronjob`
already supports per-platform targeting (`deliver='telegram:...'`,
`deliver='buzz:...'`), so the plumbing exists — only the skill-level
parsing ("remind me on Buzz to...") and the log format (add a gateway
field) need to be added when the time comes.
