---
name: daily-task-manager
description: Task lifecycle — add, complete, defer, and review tasks. A task is a task page in tasks/, one file per task, with deadline and priority in frontmatter.
triggers:
  - "add task"
  - "complete task"
  - "defer task"
  - "what are my tasks"
  - "task list"
  - "review tasks"
---

# Daily task manager — the task lifecycle

A task is a **`task` page** — one markdown file in `tasks/`, identified by its
slug, exactly like every other page kind (`DESIGN.md` §2.2: "a tracked to-do
with a deadline"). There is no running list and no single tasks file: each task
is its own page, so it is searchable, linkable, and visible to the attention
contract. `briefing` and `daily-task-prep` read these pages' deadlines — keeping
the frontmatter accurate is what makes the brief trustworthy.

> **Conventions:** `skills/conventions/page-kinds.md` (the `task` kind),
> `skills/conventions/frontmatter.md` (the schema), `skills/conventions/graph-and-links.md`
> (forward links), `_brain-filing-rules.md`, `_output-rules.md`,
> `skills/conventions/capabilities.md` (the harness contract).

## Capabilities

`brain-read`, `brain-write`, `brain-search`. Universal — works under any
harness. (The companion `briefing` and `daily-task-prep` consume these
pages and bring the Hermes-only calendar/inbox dependency; this skill
only authors them.)

## The task page

A `task` page carries the shared frontmatter spine plus the fields its job
needs. Lifecycle state lives in frontmatter, not in a separate list:

```yaml
---
kind: task
slug: r01-aims-page-draft
title: "Draft Specific Aims page — repertoire-aging R01"
importance: 0.7
due: 2026-06-15
priority: P1            # P0 urgent · P1 this week · P2 this month · P3 backlog
status: open            # open · done · deferred
links: [grants/<slug>]
tags: [grant-deadline]
---
```

The body holds the substance — what the task actually requires, context,
sub-steps. `due`, `priority`, and `status` are the fields the attention contract
reads; keep them honest.

## Phases

1. **Resolve the task.** For complete / defer / review of an existing task,
   use `brain-search` for the matching `task` page and read it before
   acting. For an add, check first that no equivalent task page already exists.

2. **Execute the action:**
   - **Add** — create `tasks/<slug>.md`. Set `due`, `priority`, `status: open`.
     Link forward to the `grant`, `project`, or `meeting` the task serves via
     `links:`. Use your human's own phrasing for the title (`_output-rules.md`).
   - **Complete** — set `status: done` and add a `completed:` date field. The
     page stays in `tasks/`; it is not moved or deleted. Done state is a
     frontmatter field, queryable like any other.
   - **Defer** — push `due` to the new date and record the reason in the body
     (`Deferred 2026-05-18: blocked on co-PI sign-off`). Leave `status: open`.
   - **Review** — search `tasks/` for `status: open`, read the pages, and
     present them ordered by `due` then `priority`. This is a read; it edits
     nothing.

3. **Write the page.** Never blind-overwrite — read current state first; if the
   page was edited very recently (your human may have touched it in Obsidian), append
   or hold rather than clobber (`brain-ops`, `VISION.md` §4.1).

## What a task is for

The deadlines that matter to the research program: grant submissions, progress
reports, paper submissions, IRB renewals, peer-review obligations, research
travel. A task page exists so a deadline is *tracked* — and so `briefing` can
escalate it as it approaches. Personal-life to-dos and lab-state chores are out
of scope (`DESIGN.md` §11): there is no task page for them.

## Output

When the action edits the brain, report it plainly — the slug, the action, the
new state — no LLM preamble. A review returns the open tasks ordered by deadline.

## Anti-patterns

- Maintaining one running `tasks.md` list instead of one page per task.
- Adding a task with no `due` or no `priority`.
- Completing a task by deleting the page — set `status: done`, keep the page.
- Deferring without recording a reason in the body.
- Creating a task for out-of-scope personal or lab-admin work.
- Blind-overwriting a `task` page your human may have just edited.
