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

## Change-scoped verification

Select checks by the behavior changed, not by the skill's size, history, or
scheduled status. Read back the affected instructions against the existing
`eval_contract`, resolver, and conventions; inspect immediate callers and
check referenced paths and command interfaces where the edit affects them.
Do not weaken quality dimensions or safety obligations to make an edit pass.

| Change | Required evidence |
|---|---|
| Wording, routing, or procedural clarification without an operational behavior change | Read back affected instructions and callers; check affected references and command interfaces. No live run or fabricated test suite. |
| Deterministic code | Reproduce the affected failure where applicable; run affected offline tests and immediate caller checks. |
| Model prompt or scientific interpretation behavior | Use a bounded representative example and inspect its output against the affected quality dimensions. |
| Deployment, imports, packaging, or serving integration | Run focused import/relocation/interface checks; use a bounded real integration check where offline evidence cannot establish the changed behavior. |
| Archive migration or cleanup | Verify the affected archive inputs, outputs, and preserved evidence. |

For mixed changes, combine the applicable rows. A Markdown edit that changes
model behavior or operational decisions is not merely a wording correction.
Name the changed behavior, checks run, results, and remaining limitations in
the normal closeout; no separate acceptance dossier is required.

Broaden validation only for a concrete dependency, failure, or unresolved risk
introduced by the change. Do not automatically re-check every previously
passed checklist, replay historical acceptance drivers, rebuild old experiment
environments, or hash unrelated archives. Preserve useful regression tests;
run the affected suite, expanding it when the evidence warrants doing so.

This policy governs maintenance of mnemo skills, including edits to this
policy. External authoring or execution recipes do not automatically require
pressure scenarios, repeated model samples, TDD for procedural prose, or
whole-workflow reruns. Use such checks only when the changed behavior needs
them. Keep each skill's existing quality contract and operational safety gates.

## Scheduled skills and live validation

Being schedule-backed does not itself require a live rerun. Apply the matrix
above. When a scheduled or live path actually needs validation:

- Use a bounded, logged, inspectable run and capture its output to a file.
  Inspect the real output against the affected contract dimensions; report
  execution status separately from delivery status.
- Use isolated inputs and outputs. Do not deliver test messages, advance
  production cursors, drain production queues, or mutate production state
  merely to test an edit. Preserve authorization and spending limits.
- Inspect job prompts, logs, and serving bindings when those are affected.
  `cron-operations` owns diagnosis of scheduled failures. If the required
  check cannot run, report the limitation and hold the affected change.

Reference this convention from consuming skills rather than copying a
blanket rerun gate into each skill.

## Anti-patterns

- Shipping a known regression against a skill's `eval_contract`.
- Calling changed model or operational behavior a wording correction to avoid
  its required check.
- Running a live task solely because a skill is scheduled.
- Inventing a test suite or pressure campaign for a procedural read-back.
- Re-enacting a historical acceptance campaign without a concrete reason.
- Ignoring affected callers, broken references, or a failed required check.
- Hardcoding one deployment's people or channels into a template.
- Rewriting an entire skill when a targeted correction preserves what works.
