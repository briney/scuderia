---
name: remind
description: Create a time-based reminder — "remind me to X at TIME" creates a cron job and logs to working-docs/reminders-log.md. Delivery goes to an explicitly supported connected destination when the user asks for a notification.
triggers:
  - "remind me to"
  - "remind me at"
  - "set a reminder"
  - "remind me"
eval_contract:
  goal: Turn a conversational time-based nudge into a scheduled delivery with a durable, readable log record — nothing more.
  dimensions:
    - "PARSING — time, timezone, and content are extracted exactly; the default timezone is the human's local one"
    - "DELIVERY — the destination is set explicitly and only to a destination the installed runtime actually supports"
    - "RECORD — the log line is appended (never blind-overwritten) with fire time, slug, content, status, and job ID"
    - "SCOPE — a research-program deliverable with a deadline is promoted to a task, not kept here"
  hard_fails:
    - Creating a reminder with no clear, actionable content string.
    - Blind-overwriting the log or omitting the cron job ID from it.
    - Promising a live message to a destination that was never configured.
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

> **Conventions:** `working-docs/README.md` (log, not graph data),
> `brain-ops` (read before appending), `skills/git-ops/SKILL.md` (owned-log
> closeout). For a scheduling/delivery failure, load `cron-operations`.

## Capabilities

`schedule-job`, `deliver-message`, `read-file`, `edit-file`. Hermes binds these
through the installed cron management tool; inspect its current schema before
creating a job. A missing notification channel is a real delivery limitation.

## Procedure

1. **Resolve time and content.** Preserve the requested reminder text. Check the
   actual clock and the user's configured timezone; clarify an unresolved
   timezone, ambiguous wall time, or missing content. For "in N minutes/hours,"
   use the tool's explicit one-shot relative form (Hermes: `in 2h`), not its
   recurring interval form (`2h`). For an absolute time, compute an ISO timestamp
   with the intended timezone; use the stated recurrence for recurring jobs.
2. **Resolve delivery.** Prefer the originating messaging conversation when it
   is a supported destination. From CLI, `local` saves output and `origin`
   does not create a live terminal-message channel. If notification is wanted,
   use a user-approved, connected destination; ask when the destination is
   unknown. `all` broadcasts to connected home channels only when that fan-out
   is intended. Do not change gateway configuration to make a reminder work.
   Delivery is one-way unless supported session attachment was explicitly
   enabled; broadcasts are never attached. Record any no-delivery-path notice.
3. **Create and verify the job.** Set schedule, destination, descriptive
   `reminder-<slug>` name, and a self-contained prompt. One-shot jobs use the
   one-shot schedule/default or `repeat: 1`; recurring jobs omit `repeat`
   unless a finite integer count was requested. Never pass `repeat: forever`
   to an integer field. The prompt includes exact reminder text and the log
   location/entry identity; its final response is delivered by the scheduler,
   not sent a second time by the agent. Follow-up actions require their own
   authorization; a reminder alone does not authorize a backfill or other work.
   Read back the exact returned job ID, schedule/next fire time, recurrence and
   destination. Do not claim success from a create response with an unresolved
   warning or a mismatched read-back.
4. **Append and verify the log.** Read `working-docs/reminders-log.md`, append
   one line, and read back that entry while preserving existing content:

   ```text
   - <fire time with timezone or recurrence> | <slug> | <verbatim content> | status: scheduled | job: <actual job ID> | deliver: <destination>
   ```

   Keep existing log records unchanged; the destination is an explicit suffix
   on new records. A log-write failure does not undo an existing job: report
   the partial state and repair the log without creating a duplicate reminder.
5. **Confirm and close.** State what will fire, when and where, including
   local-only output when applicable. Validate the owned log change and use
   `git-ops` under repository authorization; a nested run returns paths and
   verification to its parent. Never stage unrelated working documents.

## At fire time

The job reads the exact log entry and returns the reminder as its final
response. Mark that entry `fired` only when execution occurs; use `completed`
only for a separately authorized follow-up that actually completed, or
`cancelled` when the reminder was cancelled. Preserve the rest of the log.
Execution and delivery are separate: a fired status does not prove the message
reached its destination. One-shot completion is scheduler-managed; do not
promise physical deletion of its historical job record.

Procedure edits use an isolated scheduling/parser/log rehearsal with captured
output, not a production reminder or test message.

## Promotion to task

If a reminder is research-program-relevant (e.g., "remind me to follow up
on the RCA MTA by Friday"), consider promoting it to a `task` page via
`daily-task-manager` instead of — or in addition to — this skill. The test:
does this have a research-program deadline that `briefing` should track? If
yes, it's a `task`. If it's a nudge with no deliverable, it's a reminder.

## Anti-patterns

- Turning a lightweight nudge into a graph task without a research deliverable.
- Promising delivery or reply continuity that the verified job does not support.
- Creating a duplicate job after only the log write failed.
- Executing follow-up work merely because its name appears in a reminder.
