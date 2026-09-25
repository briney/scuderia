---
name: skill-creator
description: Use when creating or improving a procedural skill.
triggers:
  - "create a skill"
  - "new skill"
  - "improve this skill"
eval_contract:
  goal: |
    Produce a routed, executable procedure with one authoritative home per
    rule, preserving working behavior without accumulating incident history.
  dimensions:
    - "SCOPE — one recognizable job, with explicit boundaries against its neighbors"
    - "RETENTION — working rules and bounded failure conditions survive the edit"
    - "LOADING — core gates remain inline; optional depth loads only when needed"
    - "VERIFICATION — references, callers, and representative outputs agree"
  hard_fails:
    - Losing a working rule without an explicit, justified disposition.
    - Leaving contradictory operative instructions or broken required references.
    - Copying private instance content into the platform template.
    - Bypassing write protection or publishing without repository authorization.
---

# Skill creator

Author or improve the procedure for one recognizable job. A skill has one
`SKILL.md` entry point; optional support files belong in `references/`,
`templates/`, `scripts/`, or `assets/`, not loose beside the entry point.
The entry point carries the ordered procedure, standing preferences, and
required safety/identity/verification gates. It is not a session log.

> **Read first:** repository `AGENTS.md` (ownership and privacy),
> `skills/RESOLVER.md` (routing), `skills/conventions/capabilities.md`
> (named capabilities), and `skills/conventions/skill-hygiene.md`
> (eval contract, no-regression law, and change-scoped verification).
> Reference character and conventions rather than restating them.

## Capabilities

`brain-read`, `brain-write`. Operates on skill files and the resolver;
execution and scheduling capabilities depend on the skill being validated.

## Choose the mode

| Situation | Mode and required reading |
|---|---|
| Recurring job has no adequate owner | Create; load `templates/skill-template.md` when drafting the new entry point. |
| Existing job needs a correction or new input | Improve; change the operative step and its affected callers. |
| Working procedure is obscured by repetition or conditional detail | Streamline; load `references/skill-library-audit.md` before restructuring. |
| Whole-library audit or possible retirement | Audit/retire; load `references/skill-library-audit.md`. An audit alone authorizes no edits or deletion. |
| Skill-management lookup or write fails | Load `references/skillmanage-quirks.md`; verify the current runtime before applying old observations. |

## Procedure

1. **Establish the job and scope.** Name the trigger, expected recurrence,
   inputs, output, and nearest existing owner. A one-off task or a trivial
   helper does not need a skill; a task-agnostic trait belongs in the character.
   Extend an existing owner when it already covers the job. Split separately
   invoked intents; keep source variants and occasional recovery in references.
   A shared scheduling or mutation procedure can have one owner referenced by
   its consumers instead of several inline implementations.

2. **Read current state.** Resolve symlinks and canonical homes. Read the full
   existing skill, relevant support files, resolver row, and consuming skills.
   Inspect referenced scripts and scheduled prompts where they affect the change.
   Compare divergent copies by content, history, and ownership; neither an
   instance copy nor a template copy wins automatically. Record pre-existing
   changes and re-read immediately before editing; preserve concurrent work.

3. **Declare the evaluation bar.** Set or infer the skill-specific
   `eval_contract` before editing, following `skill-hygiene.md`. Its named keys
   are `goal`, `dimensions`, and `hard_fails`. An existing skill without a
   contract needs one grounded in its current obligations, not a weaker bar
   designed to make the edit pass. Record the behavior to preserve and the
   exact contradiction, missing dependency, or new requirement being addressed.

4. **Apply the delta at its owner.** Update the step that governs the behavior;
   remove the superseded instruction from summaries, examples, templates,
   anti-patterns, and callers. Do not append a dated Bug section or another
   overriding hard rule. Keep regression evidence where it is useful: tests
   for executable behavior, a concise counterexample for judgment, or a
   scoped diagnostic and recovery rule in a conditional reference. Preserve
   dates and tested scope when they limit a negative retrieval observation;
   git holds the incident narrative. Never turn one failed request into a
   permanent provider-wide prohibition.

5. **Keep loading selective.** Aim for a concise entry point, often 60–160
   lines, without treating size as a correctness test. Extract conditional
   detail before cutting its old copy. Name the condition for each reference
   load at the relevant step. Templates are read when producing that output;
   scripts are invoked for executable mechanics, not pasted into every caller.
   Do not require every invocation to read an extracted appendix and then
   claim a context reduction. Preserve separate branches when one helper
   implements only part of the contract.

6. **Route and place the result.** Add or update the resolver row in the
   correct cluster, including disambiguation where needed. Generalizable
   mnemo procedures belong in the scuderia profile; private evidence and
   instance state remain in the instance. Use the supported management/write
   tools at the permitted canonical home. A resolver limitation is not
   permission to bypass a protection refusal. Frontmatter uses `name`,
   `description`, `triggers`, and `eval_contract`; do not invent other keys.
   Start the description with a self-contained trigger: "Use when …".

7. **Verify against the old behavior.** Reload the edited entry point, inspect
   the complete procedure and affected callers, parse frontmatter, and resolve
   concrete support paths. Run referenced helpers when their behavior or
   invocation changed; keep existing tests. A procedural read-back is the
   semantic check, not a fabricated test score. Select further checks by the
   changed behavior under `skill-hygiene.md`, not by scheduled status. When
   execution is required, capture and inspect output without live delivery. If validation is blocked, report the
   block and do not call the unit complete. Audits and restructures also
   require the retention and loaded-byte checks in the audit reference.

## Output and closeout

Return the changed paths, corrected behavior, validation evidence, and any
remaining limitation. A new skill includes its resolver row; an improvement
updates routing only when the task boundary changed.

Every persistent-writing skill must declare its completed-unit boundary,
required validation, and standalone-versus-child owner. Reference
`skills/git-ops/SKILL.md` for closeout rather than copying Git commands or
snapshot-recovery recipes. For this skill, the completed unit is the validated
procedure plus required support files and repaired callers. A child returns
paths and checks; the authorized top-level owner handles Git closeout.
