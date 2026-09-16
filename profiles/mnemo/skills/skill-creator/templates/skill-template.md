---
name: <skill-name>
description: "Use when <recognizable trigger>. <One-line behavior>."
triggers:
  - "<trigger phrase>"
eval_contract:
  goal: |
    <The task-specific result and what excellent output means.>
  dimensions:
    - "<DIMENSION — a question about this skill's output>"
  hard_fails:
    - "<A failure that invalidates the output>"
---

# <Skill title>

<One recognizable job; its boundary against the nearest existing skill.>

> **Conventions:** <path> (<what it owns>).

## Capabilities

<Named capabilities from skills/conventions/capabilities.md.>

## What this guarantees

- <Required result.>

## Procedure

1. **Establish inputs.** <Required context and entry conditions.>
2. **Perform the work.** <Ordered steps; references have explicit load conditions.>
3. **Verify.** <Source/read-back checks; executable checks for scripts.>

## Output and closeout

<Output shape, citations, and limitations. For persistent writes: completed-unit
boundary, exact owned paths, validation, and standalone-versus-child owner;
reference skills/git-ops/SKILL.md rather than repeating Git mechanics.>

## Anti-patterns

- <A non-obvious failure mode not already covered by the operative steps.>
