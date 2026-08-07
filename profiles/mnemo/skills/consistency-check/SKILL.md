---
name: consistency-check
description: >
  Find contradictions and expired facts — incompatible claims across the graph,
  conflicts in the hypothesis supports/refutes evidence graph, and time-sensitive
  facts that have gone stale. Distinguishes a genuine conflict from mere
  succession. Runs standalone ("find contradictions", "check consistency") or as
  rem-cycle phase 4.
triggers:
  - "find contradictions"
  - "check consistency"
  - "conflicting claims"
  - "stale facts"
  - "audit the hypothesis graph"
---

# Consistency check — contradictions and expired facts

Growth accretes not just duplicates and missing links but *disagreements*: two
pages stating incompatible facts, a paper cited as both support and refutation, a
"forthcoming" that shipped a year ago. Most apparent contradictions are only
**succession** — a fact that was true and is now superseded — and the discipline
of this whole skill is telling that apart from a genuine conflict.

> **Conventions:** `rem-cycle-contract.md` (tiers, the phase result),
> `graph-and-links.md` (the `supports:`/`refutes:` hypothesis evidence graph,
> forward-only), `frontmatter.md` (the temporal fields — a paper's `status`, a
> grant's `status`/`deadline`/`decision_date`, a task's due date),
> `skills/conventions/quality.md` (cite-or-flag). Character: `SOUL.md` — surface the
> conflict, never paper over it to keep the graph tidy.

## Capabilities

`brain-search`, `brain-read`, `brain-write`. `brain-write` is used **auto** only
to flag an unambiguously-expired fact `stale`; every contradiction and every
resolution is *proposed*.

## Scope — the line against the neighbours

- `maintain`'s *stale-pages* dimension = a page whose **synthesis lags** newer
  evidence (an out-of-date body). This skill = a **time-sensitive fact that
  expired** (a dated claim gone false) and **incompatible claims**. Synthesis-lag
  → `maintain`; contradiction/expiry → here.
- `citation-fixer` = a claim with **no source**. This skill = a claim that
  **conflicts** with another, or with the clock.
- `entity-resolution` = two nodes, one thing. This skill = one entity, two
  **incompatible facts**. A **slug-form or publication-year artifact** (a slug
  year differing from the `year:` field — usually preprint-year vs
  publication-year) is *not* a factual conflict; it belongs to
  `entity-resolution` / `frontmatter-guard`. This skill owns **semantic**
  conflicts (incompatible claims about the world), not naming artifacts.

## What this guarantees

- **Succession is not conflict.** Check temporal metadata *first*: two claims with
  different validity windows are a *supersession* (was → is), not a
  contradiction. Only same-window incompatible claims are conflicts.
- **Never silently pick a winner.** A genuine conflict goes to the queue with
  **both** evidence spans (`evidence` is a *list* of the two spans —
  `rem-cycle-contract.md`); the resolution is Bryan's.
- **No external lookups.** A flip that needs the outside world (did this preprint
  publish? was this paper retracted? was this grant funded?) is `detect_only` —
  reported for a waking fetch, never resolved here (`rem-cycle-contract.md`, the
  no-external-I/O principle). Don't conflate it with a plain approve/reject.
- The only auto write is a `stale` flag on an unambiguously-expired fact —
  **adding `stale` to the page's `tags:`** (tags are free-form, `frontmatter.md`),
  a non-destructive marker, never a deletion.

## The surfaces

### The hypothesis evidence graph (the distinctive one)

A `hypothesis` carries `supports:` and `refutes:` edges. Hunt:

- a paper in **both** `supports:` and `refutes:` for one hypothesis — an error or
  a genuinely two-edged result; propose review with the paper's finding quoted.
- two hypotheses whose evidence sets conflict (one's support is the other's
  refutation) — propose surfacing the tension.
- a hypothesis whose net evidence has **flipped** (refutations now outweigh
  support) — not a conflict; report it as a status signal for Bryan.

### Cross-page attribute conflicts

Sample pairs of claims about the same entity/attribute — a person's affiliation,
a paper's venue/year, a grant's mechanism, a number. Incompatible **and same
validity window** → conflict (propose, both spans). Different windows →
succession: treat the current value as canonical, note the prior as superseded,
do not raise a conflict.

### Expired time-sensitive facts

A task past its due date; a grant `status: under-review` whose `decision_date`
has passed; a "next week" / "forthcoming" / "in press" / "submitted" written long
ago. **Unambiguously** expired → **auto** flag `stale` (add `stale` to `tags:`).
Ambiguous (still plausibly true) → propose. A resolution that needs the outside
world (the actual publication or decision) → `detect_only`, report. **Grants are
the primary temporal surface** — their `status` / `decision_date` / `submitted`
fields give real validity windows; pages without dated metadata fall back to
prose judgment, so weight the succession test to where the dates actually are.

## As a rem-cycle phase

Under the orchestrator (`rem-cycle-contract.md`): the orchestrator passes `mode`
(dry-run | normal); emit the fenced-yaml phase result — `committed[]`
(unambiguous `stale` flags only), `proposed[]` (every contradiction + ambiguous
stale, with **both** evidence spans, confidence, `target_exists`), `metrics`
(`hypothesis_conflicts`, `attribute_conflicts`, `stale_flagged`, `stale_proposed`,
`pages_scanned`). Cheap scanning (grep the `supports:`/`refutes:` edges and the
date fields) is unbudgeted; adjudication respects the mutation budget. If the
hypothesis/dated-page set outgrows one pass, rotate a slice via a cursor. No
chaining — surface a status flip for the waking pipeline, do not fetch.

The hypothesis-conflict surface is **dormant until `hypothesis` pages exist** —
with zero hypotheses the phase runs only the grant-staleness and
attribute-conflict surfaces and reports thin. That is expected, not a failure;
the phase earns its keep once the evidence graph is populated (`topic-synthesis`,
phase 5).

## Output

- **As a phase:** the fenced-yaml phase result.
- **Standalone:** the conflicts surfaced inline with both sides, plus any
  `stale` flags applied.

## Anti-patterns

- Calling a succession a contradiction — check validity windows first; "was" then
  "is" is an update, not a conflict.
- Silently resolving a conflict by picking a side — propose with both spans.
- Reaching outside the vault to resolve a status or retraction — detect and
  report; that is a waking concern.
- Flagging a still-plausible fact `stale` — reserve the auto flag for unambiguous
  expiry; propose the rest.
- Hand-writing a backlink when noting supersession — inbound edges are derived.
