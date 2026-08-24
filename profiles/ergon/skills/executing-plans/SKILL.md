---
name: executing-plans
description: Use when you have a written implementation plan to execute with review checkpoints — load, review critically, execute each task with its verifications, report when complete.
triggers:
  - "execute this plan"
  - "implement the plan"
  - "run the implementation plan"
---

# Executing Plans

*Adapted from [obra/superpowers](https://github.com/obra/superpowers) (MIT,
© 2025 Jesse Vincent), vendored 2026-08-24. Subagent references retargeted
to `delegate_task`; sibling-skill references un-namespaced.*

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Announce at start:** "I'm using the executing-plans skill to implement this
plan."

**Note:** if the plan's tasks are independent and substantial, prefer
`subagent-driven-development` (delegate_task) over executing inline — fresh
subagents per task with review beats one long context.

## The Process

### Step 1: Load and Review Plan
1. Ensure an isolated workspace: use `using-git-worktrees` to create one or
   verify the existing one
2. Read plan file
3. Review critically — identify any questions or concerns about the plan
4. If concerns: raise them with your human partner before starting
5. If no concerns: create todos for the plan items and proceed

### Step 2: Execute Tasks

For each task:
1. Mark as in_progress
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Mark as completed

### Step 3: Complete Development

After all tasks complete and verified:
- Announce: "I'm using the finishing-a-development-branch skill to complete
  this work."
- **REQUIRED SUB-SKILL:** Use `finishing-a-development-branch`
- Follow that skill to verify tests, present options, execute choice

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing starting
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing** (spine: never guess
parameters).

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** — stop and ask.

## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip verifications (`verification-before-completion`)
- Reference skills when plan says to
- Stop when blocked, don't guess
- Never start implementation on main/master branch without explicit user
  consent
