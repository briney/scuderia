# Convention: skill hygiene

Cross-cutting rules for every skill that authors, edits, or maintains other
skills — `skill-creator` and `cron-operations` above all, and any future meta
skill. These operationalize the `SOUL.md` spine (no fabricated confidence,
never ship a regression) for the *skill set itself*: the skills are the mind's
procedures, so a broken skill is a broken procedure.

Read alongside `skills/skill-creator/SKILL.md` (the authoring procedure) and
`skills/conventions/quality.md` (the page-level twin of this convention).

## The eval contract

Every skill declares what "good output" means for *itself* — as a fourth,
**optional** frontmatter field `eval_contract`:

```yaml
eval_contract:
  goal: |
    One or two sentences: what this skill is for, and what "excellent"
    looks like in the real world. Be concrete and skill-specific — not a
    generic restatement of "the output is good."
  dimensions:
    - "DIMENSION_NAME — the specific question this dimension answers for THIS skill"
    # 3-6 dimensions, tuned to the skill. A briefing skill might pin
    # FACTUAL_INTEGRITY, SUBJECT_ANCHOR, WHY_IT_MATTERS, CLICKWORTHY.
  hard_fails:
    - "A failure mode that zeroes the contract regardless of other scores."
    # e.g. "Any fabricated citation = automatic failure."
```

Three things matter about this field:

- **It is the goal written down *before* evaluating, not after.** A skill
  without a contract has no stated bar; an edit to it has no baseline to be
  measured against.
- **It is skill-specific, never generic.** Generic dimensions catch slop but
  miss whether the output achieved *this* skill's purpose. The dimensions
  answer one question each about the skill's real job.
- **It is the forward-compatible seam.** Today the contract is a
  *prose-grounding* device — read it, argue against it, in words. Later, if a
  scoring harness (`DESIGN.md`'s eval-lane, unbuilt) lands, this exact field is
  already machine-readable: its `goal` feeds `--task`, its `dimensions` feed
  `--dimensions`. The cheap version now does **not** foreclose the robust one;
  it *is* the correct first layer of it. Do not degrade the field's
  machine-readability for present convenience — keep `goal`/`dimensions`/
  `hard_fails` as named keys.

Where the contract is absent on an existing skill, infer it (from the body,
from user corrections, from the schedule that invokes it) or ask — one tight
question — before editing; then write it back. Editing the contract is itself
a skill edit and re-read through the no-regression law below.

## The no-regression law — forward only, never back

An edit to a skill must leave it no worse than it was. "Better" and "worse"
here mean *against the skill's own eval contract*, on the same task you could
have run before the edit.

The cheap form (today, no harness): before shipping an edit, re-read the
contract and answer in prose — *does the new version score at least as high on
every dimension the old one did?* If the answer is no on any dimension, the
edit does **not** ship as-is; re-fix or revert, and say so. A silent "worse"
is the one failure this law exists to prevent.

The robust form (later, when a scoring harness lands): the same law, with
numbers — new overall ≥ prior overall, no dimension regressed by more than a
small epsilon. The discipline is identical; only the instrument changes. Do
not wait for the harness to practice the discipline.

Two consequences:

- **Forward only.** An edit that passes absolute review but regresses a
  dimension is still a regression. Absolute pass is necessary, not sufficient.
- **Idempotent improvement.** Never rewrite a skill from scratch when
  improving it. Preserve what works, fix the delta, keep the version history
  forward. (A pure deterministic bug fix, whose behavior is fully locked by
  the changed script, may bypass re-argument — but the re-read below still
  runs.)

## Re-read and re-verify — the standing regression check

Atticus skills are mostly *procedural markdown*, not code; the handful with
real scripts (`paper-ingest/scripts`, `mailbox-drain/scripts`,
`feed-emit/scripts`, `granola-meeting-sync/scripts`) are the exception, not the
rule. There is no test runner, and none is wanted — the correct regression
check for a procedural skill is a **read-back**, not a test suite.

After any edit, re-read and re-verify:

1. **Re-read the SKILL.md** against the current resolver and conventions —
   does it still route, still cite the conventions by path, still hold?
2. **Re-check the referenced script** (if any) — does it still exist, still
   run, still match what the skill claims it does? No dead paths.
3. **Re-check every checklist item that *previously* passed** — not just the
   one you touched. If an item that used to pass now fails, the edit broke
   something; fix before shipping.

This is the same read-back discipline `brain-ops` applies to pages. It is the
whole of what "tested" means here — and it is sufficient, because the skill's
behavior is an instruction set the mind follows, not a function to exercise.

## The scheduled-run gate — edit nothing that backs a cron, unrun

Many atticus skills back scheduled jobs: `briefing`, `synthesis-briefing`,
`literature-sweep`, `rem-cycle` (and its phase delegates), `funding-sweep`,
`monitor-the-situation`, `ingest-pending-papers`, and friends. Two rules for
these:

1. **Log-and-inspect first.** The scheduled job must run through a logged,
   inspectable path — a `cron` job with a recorded `last_status` and a dream
   report, not a bare shell pipeline that runs silently. `cron-operations`
   owns the "why did this job fail" side; this rule is the "don't edit the
   skill out from under a live job" side. Ghost runs are the #1 source of
   silent breakage.
2. **Re-run a representative task before shipping.** Editing a
   schedule-backed skill is not done until you have re-run one representative
   live task through the edited skill and re-read the real output it would
   produced — against its eval contract, forward-only. The principle is
   constant ("re-run the highest-bar task, the output the human reads most
   critically"); the *specific* input is never hardcoded into the skill body.
   Capture the output to a file, do **not** post it to a live channel during
   the check.

Write the hard rule into any schedule-backed skill's body:

```markdown
⛔ NO-REGRESSION + RE-RUN GATE: any edit to this skill must (1) re-run a
representative scheduled task, (2) re-read its real output against the eval
contract, (3) hold forward-only. A worse output does not ship.
```

## Anti-patterns

- Shipping a skill edit that regresses a contract dimension ("worse") — the
  forward-only law has no quiet exception.
- Evaluating a skill on generic dimensions instead of its own `eval_contract`.
- Editing a schedule-backed skill without re-running a representative task and
  re-reading its real output.
- Inventing a test suite where a read-back is the honest check — procedural
  markdown doesn't run in `bun test`.
- Editing one checklist item and skipping the re-read of the rest.
- Hardcoding one deployment's people or channels into a skill body — declare
  the principle, let each deployment fill the specific input.
- Rewriting a skill from scratch to fix it — idempotent improvement preserves
  what works.
