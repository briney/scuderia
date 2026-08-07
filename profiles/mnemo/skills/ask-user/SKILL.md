---
name: ask-user
description: The choice-gate pattern — present 2-4 options, stop the turn, and branch on the user's response. Used by other skills when a decision point genuinely needs Bryan's input before proceeding.
triggers:
  - "present options"
  - "ask before proceeding"
  - "choice gate"
  - "user decision"
---

# Ask user — the choice-gate pattern

The canonical way to gate on a decision: present a small set of options, stop,
and let Bryan choose. This is not async/await — in a conversational agent,
"gating" means presenting the choices and ending the turn so the next message is
the answer.

## Capabilities

None beyond conversational output. Universal — works under any harness.

## What this guarantees

- 2-4 options, never more — past four, the choice is harder than the task.
- Always an escape hatch — Skip, Cancel, or "none of these".
- The turn stops the moment the choices are presented — no follow-up tool calls,
  no preemptive work, no default-and-proceed.
- One question per message — choice gates are never stacked.
- Self-explanatory labels — an action verb plus a qualifier, never "Option 1".

## How gating works

1. Present the choices — numbered options.
2. Stop the turn. No more tool calls, no further messages.
3. Bryan's response begins the next turn.
4. Read the response, acknowledge briefly, branch.

## When to use it

- An ambiguous request with several valid readings.
- A destructive or brain-wide operation — bulk deletes, overwrites, a sweep that
  touches many pages.
- A filing or routing decision where the wrong choice is expensive to undo.
- A priority call — which thread to push first.
- Any fork where a wrong default wastes real work.

## When not to use it

- Clear, unambiguous instructions — just do the work.
- Low-stakes decisions — pick the best option and mention it.
- The user has already stated a preference.

## How to present choices

A clear question, a line or two of context, numbered options, an escape hatch:

```
How should I file this?

This bioRxiv preprint introduces a new method as much as it reports a result.

1. Paper-facet page — file under papers/, link the method
2. Two pages — a paper page and a methods/ page, linked
3. Method page only — the result is incidental
4. Skip — leave it in _drop/ for now
```

If the platform supports interactive buttons, use them — the label and the
question carry the same content as the numbered form.

## Handling the response

- Read the response — a number, a label, or free text.
- Acknowledge briefly — "Going with the two-page split."
- Branch and execute the chosen path.
- Map loose text gracefully: "the first one" / "A" / "1" → option 1; a partial
  word → fuzzy-match the labels; "none of those" → offer alternatives; an
  unrelated message → Bryan moved on, drop the gate.

## Examples

### Gating a destructive brain-wide operation

```
This will rewrite frontmatter on 213 pages flagged with KIND_MISMATCH.

The vault is under git, so the change is revertable — but it is a large diff.

1. Run it — fix all 213 in committed batches
2. Test first — fix 5, show the diffs, then decide
3. Show me the list — review the flagged pages before any change
4. Cancel — leave them flagged
```

### A filing decision

```
Where should this go?

The transcript names a collaborator who already has a page at
people/jane-okafor.md, and it is mostly a discussion of the antibody-LM project.

1. Interaction page — standalone at interactions/2026-05-18-jane-okafor.md, linked to both
2. Append to the project page — projects/antibody-lm
3. Both — a meeting page, linked from the project
4. Skip — do not file this
```

## Used by other skills

`ingest` and its specialists reach for this on a genuinely ambiguous route;
`enrich` uses it for a merge-vs-create call; `maintain` uses it before a
destructive sweep. When a new skill needs a decision point, it references this
pattern rather than inventing its own.

## Anti-patterns

- Continuing the turn after presenting choices — "while you decide, I'll start
  on..." defeats the gate.
- Picking a default and proceeding silently — if it mattered enough to ask, it
  mattered enough to wait.
- More than 4 options — group, summarise, or split into staged questions.
- No escape hatch — every gate must let the user decline.
- Stacking multiple gates in one message — only one can be answered.
- Cryptic labels — "Option 1" forces a re-read of the context.
- Gating a low-stakes decision — reserve gates for forks where rework is costly.
