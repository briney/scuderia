---
name: user-model-reflect
description: Read recent session transcripts and append a dated block of candidate observations about how your human is working — recurring patterns, recent emphases, inferred blind spots, things they reached for, things they dismissed. Writes to USER/OBSERVATIONS.md. Never edits USER/<name>.md. Manual invocation only; no schedule is wired.
triggers:
  - "run user-model-reflect"
  - "reflect on what I've been working on"
  - "summarize recent observations about how I work"
  - "what have you been learning about me"
  - "update the observations sidecar"
---

# User-model reflect — append candidate observations to the sidecar

The user model is a directory of siblings (`USER/`):

- **`USER/<name>.md`** — declared, human-authored, always loaded. The
  authoritative spine. your human owns it.
- **`USER/OBSERVATIONS.md`** — observed, written by this skill on
  demand. A *staging file*, not always-loaded, not part of
  `user-model-query`'s return shape. Your human reads it when they want to
  refresh `USER/<name>.md` (likely in response to grant reviewer critiques,
  periodic self-review, etc.).
- **`USER/VOICE.md`** — derived, the measured writing fingerprint. Written
  by its own producer, not this skill.

This skill is what produces the sidecar's content. It is invoked
manually. **No schedule is wired** — running on a cadence (cron under
Hermes, `/schedule` + `CronCreate` under Claude Code) is possible if
periodic reflection turns out to be useful, but the skill is fully
usable on demand without automation.

> **Conventions:** `skills/conventions/capabilities.md` (the harness contract,
> including `read-conversation-history` and `brain-write`),
> `skills/conventions/quality.md` (citations and honest flagging).

## Capabilities

- **Required:** `read-conversation-history`, `brain-read`, `brain-write`
  (only on `USER/OBSERVATIONS.md`), `user-model-query`.
- The skill refuses cleanly if `read-conversation-history` is
  unavailable — it writes a dated no-op stub to `USER/OBSERVATIONS.md`
  so the absence is auditable rather than silent.

## What this guarantees

- Never edits `USER/<name>.md`. The declared spine stays under your human's hand.
- Never duplicates content already in `USER/<name>.md` or in an earlier
  observation block in `USER/OBSERVATIONS.md`.
- Appends a single dated block per invocation; never rewrites prior
  blocks.
- Observations are *candidate*, not authoritative. Frame them as
  patterns observed, with the sessions that produced them; do not
  state them as settled facts about your human.
- When an observation contradicts something `USER/<name>.md` already says,
  surface the contradiction rather than silently absorbing it — your human
  is the only one who can resolve it.

## Phases

### 1. Determine the window

Default: observations since the last dated block in
`USER/OBSERVATIONS.md`. If the file is empty (no prior block) or
has only the initial preface, default to the last 14 days of
transcripts.

The user may override: "run user-model-reflect over the last week",
"…since the R01 resubmission", etc. Accept either a duration or a
session-anchor.

### 2. Read recent transcripts

Use `read-conversation-history` to load the transcripts in the window.

**Claude Code binding.** Transcript files live under
`~/.claude/projects/<encoded-cwd>/<session-uuid>.jsonl`, one JSONL per
session. Each line is a record with at least `{ type, timestamp,
sessionId, ... }`; user and assistant turns carry
`message: { role, content }`. The encoded-cwd is the absolute path of
the project root with `/` replaced by `-` (e.g.
`-Users-<you>-git-<instance>`). Read the JSONL files modified
within the window; filter to `type ∈ {user, assistant}` records;
extract `message.content` plus `timestamp` and `sessionId`.

**Hermes binding.** Hermes's native session store — see the Hermes
adapter for the API. The capability is the same; the access path
differs.

If `read-conversation-history` is not provided by the current harness,
skip to Phase 6 (the no-op stub).

### 3. Read the existing user model

- Read `USER/<name>.md` in full (via `user-model-query` — declared layer).
- Read the existing dated blocks in `USER/OBSERVATIONS.md` (via
  `brain-read`).

These exist to **prevent duplication**: an observation worth recording
is something neither file already states. If the spine already says
"your human reaches for mechanism over correlation," do not re-observe
that he does it.

### 4. Surface candidate observations

Look for material that would help the mind engage your human better in
future sessions. The categories worth attending to:

- **Recurring patterns** — moves your human made repeatedly in the window
  (a framing he kept returning to, a critique he kept levying, a
  question he kept asking).
- **Recent emphases** — what he's been working on most, which projects
  pulled the most attention, which threads he picked up vs. dropped.
- **Inferred blind spots** — things he reached for first that a
  discriminating-experiment posture would have questioned; cases where
  a confound went unscanned until late; analogies he transferred
  across the immunology/AI seam without testing them.
- **Tools and methods reached for** — what he treats as the default
  baseline, what he dismisses on contact, what makes him pause.
- **Engagement preferences confirmed or contradicted** — response
  length, where he wants pushback vs. where he doesn't, what
  energizes him vs. drains him.

Each observation is supported by *evidence from the transcripts* — at
least one session and a brief quote or paraphrase. An observation
without a grounded reference is removed.

**Discipline.** Three to seven observations per pass is the right
range. More than that and the signal-to-noise drops; fewer and the
pass wasn't worth running. If the window genuinely supports only one
or two observations, write only one or two.

### 5. Write the dated block

Append a block at the bottom of `USER/OBSERVATIONS.md` in this shape:

```markdown
## YYYY-MM-DD — <one-line summary of the window>

> Window: <duration or session-anchor>. Sessions read:
> <N transcripts spanning <date-range>>.

- **<short observation label>.** <One- to three-sentence
  observation, framed as a pattern observed in the window.>
  *Evidence: [session-id-1], [session-id-2] — "<paraphrase or quote>".*
- … (3–7 entries total)
```

Use `brain-write` to append; do not rewrite prior blocks; do not
touch `USER/<name>.md`.

### 6. The no-op stub (when transcripts are unavailable)

If `read-conversation-history` is not available under this harness,
append a stub:

```markdown
## YYYY-MM-DD — no observations (transcripts unavailable)

> `read-conversation-history` is not wired under this harness. The
> reflect skill ran and exited cleanly with no observations.
```

This keeps the absence auditable — your human sees that the skill ran,
even if it produced nothing.

## Output

- A short, terse confirmation in the session: "Appended N
  observations to `USER/OBSERVATIONS.md` (window: …). Top theme: …."
- If the skill ran but found no novel observations (everything was
  already in `USER/<name>.md` or earlier blocks), say so plainly and skip
  the append.

## Anti-patterns

- Writing to `USER/<name>.md`. The spine is your human's. This skill never
  touches it.
- Restating something `USER/<name>.md` already says. The sidecar exists to
  add to the spine, not echo it.
- Promoting an observation into a fact. Frame as a pattern observed
  in a specific window; let your human decide whether it generalizes.
- Surfacing observations the transcripts do not support. Every entry
  carries grounded evidence.
- Running ambient or in the background. The skill is explicit and
  manually invoked; if periodic reflection ever proves worth it,
  scheduling is wired separately.
- Performing depth ("here is what I have learned about you").
  Observations are notes, not pronouncements.
