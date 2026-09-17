---
name: brain-architecture-audit
description: Use when auditing or redesigning the brain's machinery.
triggers:
  - "examine/improve how the brain works"
  - "is <maintenance mechanism> optimal"
  - "how does knowledge propagate / get synthesized"
  - any proposed change to the brain's machinery, phases, or cron schedule
eval_contract:
  goal: |
    Find where the brain's machinery diverges from its own claims, with
    measured numbers, and turn the finding into a spec your human can act on.
  dimensions:
    - "MEASUREMENT — every load-bearing claim about behavior is tested against corpus/git numbers, not skill prose"
    - "DIVERGENCE_FRAMING — plumbing vs circulation, structural vs tuning named separately, drain measured before throughput is scaled"
    - "SPEC_DISCIPLINE — output is a spec carrying the measured numbers and an explicit out-of-scope section, not direct implementation"
  hard_fails:
    - Recommending a redesign from impressions instead of measurements.
    - Proposing throughput scaling before a measured drain exists.
    - Leaving the entry point pointing at companion files that do not exist.
---

# Brain-architecture audit — measure the machine before redesigning it

The brain's skills describe *intent*; the corpus and git history describe
*reality*. They diverge. A mechanism can be fully wired (contract, phases,
tiers, invariants) and still produce nothing, because its output channel has
no drain, its budget is a rounding error against ingest rate, or its declared
edges are never written. The audit's job is to find that divergence with
numbers, not impressions.

The measurement procedure is in §2 and the spec format is in §5; neither
requires a companion file. When the instance has a prior audit, compare
against its recorded measurements and scope, then measure current behavior.
Keep private audit evidence and specs in the instance.

> **Conventions:** this skill governs *design evaluation*, not execution.
> Implementation of what it produces touches vault skills and cron — that is
> foreground work (vault skills are human-owned; see Pitfalls). The spec file
> is the durable artifact and lives in the vault.

## 1. Prime directive

**Read the design docs first, then verify every load-bearing claim against
measurement.** Skill prose will say things like "the weekly-read trust
surface" or "rotating slice so every page is periodically reconsidered."
Each such claim becomes a measurement: how often is it actually read? What is
the actual rotation period? If the answer embarrasses the claim, that is the
finding.

## 2. The measurement battery

Run all of these for any propagation/maintenance audit (all verified; adjust
paths to the page dirs involved). The inline commands are the battery; work
the results into the spec's measured-numbers section.

**Throughput vs. capacity — per channel.**
```bash
# ingest rate (the demand side), per day
git log --since="30 days ago" --diff-filter=A --pretty=format:%ad --date=short -- papers/ | sort | uniq -c
# corpus size now vs. at some past date (growth since a mechanism was tuned)
git rev-list -1 --before="YYYY-MM-DD" HEAD | xargs -I{} git ls-tree -r --name-only {} -- papers/ | wc -l
```
Then read the mechanism's per-run cap from its skill/state file (e.g.
`_state.yaml` budgets, "hard cap: 5 papers per run") and compute months to
clear backlog or complete one rotation. A rotation period longer than the
corpus doubling time is a structural finding, not a tuning issue.

**Drain rate of human-in-the-loop queues — the single most diagnostic check.**
(Historical: the rem-cycle review queue was frozen 2026-08-15 after exactly
this check found a zero drain rate. The recipe stands for any future
human-gated surface.)
```bash
# how many queue items were EVER checked off, across all history
git log -p --follow -- docs/rem-cycle/QUEUE.md | grep -c "^+- \[x\]"
```
A propose-only pipeline whose human drain rate is zero is dead regardless of
proposal quality. Also check whether any *attention surface* (the briefing,
monitors) ever reads the queue — grep the briefing skill for the queue's
filename. Invisible queue = undrainable queue.

**Declared-but-never-written edges.**
```bash
# the design declares these typed edges; how many actually exist?
grep -rh "^supports:" papers/ concepts/ methods/ | wc -l
grep -rh "^refutes:" papers/ concepts/ methods/ | wc -l
```
A channel defined in conventions with zero instances is a design failure even
when the plumbing is perfect — the propagation loop was never closed.

**Coverage and distribution.**
```bash
grep -l "concepts/" papers/*.md | wc -l            # papers with ≥1 concept edge
grep -rl "^links: \[\]" papers/ | wc -l            # papers with empty links
# inbound-link distribution per concept (head vs. orphans)
for c in concepts/*.md; do s=$(basename $c .md); echo "$(grep -rl "concepts/$s" papers/ | wc -l | tr -d ' ') $s"; done | sort -rn
```

**Mechanism activity.** Count the mechanism's actual output markers (e.g.
`grep -rh "\[unconfirmed\]" concepts/ | wc -l`, `grep -rh "^### 20" concepts/`
for Shifts entries) and read `_state.yaml` + the last several history reports
— not just the most recent one — to see trends, no-op streaks, and repeated
`Skipped` reasons.

## 3. Diagnostic framing

What the numbers usually mean:

- **Plumbing works, circulation blocked.** Errors→0 and clean commits prove
  the machinery runs; zero drains / zero typed edges prove nothing reaches
  the store's structure. Name both halves separately.
- **The human-attention single point of failure.** Any pipeline that ends in
  "only your human can act" needs a measured drain rate. Zero → the fix is a
  drain (visibility inside the attention contract + a one-word approval
  path), not more proposals.
- **Time-driven rotation vs. bursty ingest.** Fixed nightly windows over a
  cursor starve when ingest is bursty (literature dives add 40 papers in a
  day). The fix class is event-driven work items drained first, with the
  cursor demoted to background defrag.
- **Maintenance vs. consolidation.** Appending a tag (`## Shifts`) is
  maintenance; rewriting the store in light of accumulated tags (a Thesis
  re-synthesis loop) is consolidation. A system that only appends never
  integrates. Check which of the two the "sleep" phase actually does.
- **Structural bottleneck vs. tuning.** Turn limits, child timeouts, shared
  budget pies, and monolithic orchestrators are structural; window sizes are
  tuning. A skill's own history section documenting repeated limit raises
  (90→150→200) is the tell.

## 4. Proposal discipline

- **Rank by leverage; fix the drain before scaling throughput.** Scaling
  proposal generation without a drain only grows a larger dead queue.
- **Graduated autonomy pattern** (when proposing autonomous execution of
  anything judgment-adjacent): narrow whitelisted classes only; age gate;
  class track-record gate from a decision ledger (N human approvals, 0
  reversions, self-arming); per-run cap; visible inline banner with revert
  command; auto-disable the class on first reversion; detect-and-log trial
  week before the whitelist opens; written kill criteria. Human veto stays
  absolute.
- **Decompose before scaling.** If the orchestrator's turn limit is the
  ceiling, splitting into per-unit jobs + aggregator is what unlocks
  "unlimited tokens" — not raising limits again.
- Every proposed change must be trial-runnable (`test-before-bulk`) and
  independently revertible via git. Sequence: visibility-only trial →
  self-arming gates → expansion.

## 5. Writing the spec

House style: file
`docs/specs/<YYYY-MM-DD>-<name>-design.md`; header block with Date / Status /
Builds-on; motivation carrying the **measured numbers** (a spec without
measurements is an opinion); numbered design sections; an **Open questions**
section for your human's calls; a rollout/migration order; an explicit
out-of-scope section naming the follow-on specs.

Close the reviewed spec through `skills/git-ops/SKILL.md` under repository
commit/push authorization. An audit does not itself authorize implementation
or publication of unrelated work.

## Pitfalls

- Trusting skill prose over measurement. The skill said "weekly-read trust
  surface"; git history said zero items ever checked. Measure.
- Counting file *additions* as the whole ingest signal — `--diff-filter=A`
  misses in-place stub fills, which then never enter any downstream pipeline.
- Diagnosing from the most recent dream report alone; read `_state.yaml` and
  several history files for trends.
- Proposing throughput increases before the drain exists.
- Implementing vault-side changes from an audit session. Vault skills
  (`skills/`) are human-owned; the audit's deliverable is the spec +
  a flagged implementation order. Edits happen in foreground with your human.
- Claiming the spec is published without the git-ops commit and remote read-back.
