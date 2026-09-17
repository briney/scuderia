---
name: user-voice-measure
description: Measure your human's writing voice into USER/VOICE.md — extract a quantized fingerprint (sentence length, tell-frequency, banned boilerplate, register) from his ## Verbatim corpus (preserved submitted prose in ingested grants and papers), then run a blind validation check. Writes only the derived file; never touches USER/<name>.md. Manual invocation only.
triggers:
  - "measure my writing voice"
  - "build a voice profile"
  - "update VOICE.md"
  - "refresh the writing fingerprint"
  - "measure my voice"
  - "voice profile"
eval_contract:
  goal: Derive a faithful statistical fingerprint of the human's own submitted prose and validate it blind, without ever touching the human-owned spine.
  dimensions:
    - "CORPUS — only ## Verbatim first-party prose is measured; ## Draft and third-party text never enter"
    - "FIDELITY — reported statistics match what the measurement actually computes"
    - "SEPARATION — narrative vs structured prose is distinguished, and each claim states which pool it came from"
    - "BLIND CHECK — the profile is not called current until it survives the interleaved draft test"
  hard_fails:
    - Writing to USER/<name>.md or any file other than USER/VOICE.md in a production run (an explicitly authorized scratch/output-path run is the sanctioned exception).
    - Reporting a statistic the script does not compute.
---

# User-voice measure — the writing fingerprint into `USER/VOICE.md`

> **Git closeout:** Follow `skills/git-ops/SKILL.md`. Close the verified measured voice-profile changes and approved supporting artifacts after the skill checks. Never stage unrelated human-owned user-model edits.

The **derived** half of the writing-voice split (`DESIGN.md` §7,
`docs/decisions/user-directory.md`). `USER/<name>.md` §6 holds the
**judgment** — argument-level decisions, human-approved. This skill holds the
**measurement** — sentence length, tell-frequency, banned boilerplate — computed
from the human's own writing and written to `USER/VOICE.md`. Where a measured
fact conflicts with a generic default in `STYLE.md` §4–§5, the measured fact
wins: the corpus is the human's actual prose, not a hypothetical.

> **Conventions:** `skills/conventions/capabilities.md` (the harness
> contract), `skills/conventions/quality.md` (honest flagging),
> `skills/conventions/brain-first.md` (pull from the brain before going
> external), `STYLE.md` §2 and §4–§5 (the voice standard this measures
> against).

## Capabilities

- **Required:** `brain-read`, `brain-write` (only on `USER/VOICE.md`, or on an
  explicitly authorized scratch/output path for rehearsal runs).
- The measurement script is pure stdlib Python — no external dependency.

## What this guarantees

- Extracts the fingerprint **only from `## Verbatim` sections** — the
  human's preserved submitted prose — never from `## Draft` (that is the
  mind's writing) and never from third-party description.
- Writes only `USER/VOICE.md` in a production run. Never edits
  `USER/<name>.md` — the spine stays under the human's hand.
- Reports where the corpus teaches something that *contradicts* a `STYLE.md`
  default, rather than silently applying the generic rule.
- Runs a blind validation check (below) before calling the profile current.

## Phases

### 1. Locate the corpus

Find every brain page carrying a `## Verbatim` section: `grep -rl
"^## Verbatim" grants/ papers/` from the brain root. These are the
human's preserved submitted prose, blockquoted with source hashes. `## Draft`
sections are excluded by rule.

If no `## Verbatim` exists (a young brain), the skill refuses cleanly:
"the corpus is too thin to measure" — same honesty as `STYLE.md` §2's
cold-start stance. Do not measure from drafts or from memory.

### 2. Run the measurement

```
python3 skills/user-voice-measure/scripts/measure_voice.py \
    --instance <instance-root> --out USER/VOICE.md
```

**Helper contract — actual behavior (verified against the script):**

- **CLI arguments.** `--instance` and `--brain` are accepted aliases for
  the instance root; `--out` defaults to `USER/VOICE.md` and accepts
  relative or absolute paths (an explicitly authorized `--out` scratch
  path is a sanctioned rehearsal run — it is not a violation of the
  write-scope rule, which protects `USER/<name>.md`, not scratch output).
  If the CLI fails before any file write, treat invocation as blocked:
  do not paper over it by editing the script inline during a measurement
  run, and do not report a measurement as performed when invocation was
  blocked.
- **Rewrite scope.** `rewrite_section` replaces everything from the
  `## The fingerprint` header to end-of-file with the new fingerprint plus a
  `## Provenance` section. Any static content placed after the fingerprint
  header would be discarded on a successful run. Keep `USER/VOICE.md`
  structured so the fingerprint and provenance are the trailing sections.
- **Tell-scan pool.** Tell-phrase counts are computed over the **narrative**
  sentence pool only; structured (list/scaffold-heavy) sentences are
  classified but not scanned for tells. The script's own output labels
  this ("narrative corpus only") — trust that label over any broader claim.
- **Reported statistics.** The script computes median, p10–p90, p95, and
  em-dash density (indexed sorted-sample percentiles); it does not compute a mean
  sentence length. Read the emitted table, not a remembered field list.
- **Pre-count stripping.** Before counting, the script strips **certain
  specific noise classes** — bracketed citation markers (`[1,2]`-style),
  ALL-CAPS section headers, figure-caption lines, and source-hash preamble
  lines. This is not a blanket removal of all third-party material: text
  that is neither a caption line nor one of those marker classes passes
  through to the pools. To know exactly which pages and sentences were
  eligible in a given run, inspect the corpus the script reports (or a
  filtered scratch copy), not this summary.

The script otherwise (stdlib only):

- Splits `## Verbatim` pages into narrative vs. structured prose (median
  sentence length ≥ ~18 words marks narrative).
- Emits the `## The fingerprint` section of `USER/VOICE.md` plus a
  provenance block (page count, sentence counts, date).

### 3. Interpret against `STYLE.md`

Read the numbers against the generic defaults. The load-bearing move: a
corpus-count that *contradicts* a `STYLE.md` ban (e.g. "leverage"
appearing hundreds of times means do not blanket-ban it) is a **finding**,
surfaced in the report — not a reason to silently override the default
either way. The measured fact wins, and the skill says so explicitly in
`VOICE.md`.

### 4. Blind validation — the discriminating test

The profile is not "current" until it survives a blind check:

1. Hold out 5 real sentences the fingerprint's numbers were **not** derived
   from (pull them from `## Verbatim` sections in grants/papers excluded from
   the measurement run, or from a section after the measured range).
2. Draft 3 short test sentences in the human's voice from the fingerprint.
3. Interleave the 3 drafted with the 5 real, and show the mixed set to the
   human. If the drafts do not stand out, mark the profile `validated` in
   `VOICE.md`'s provenance. If they do, note **which** tell exposed them,
   refine the fingerprint, and repeat once.

This is `SOUL.md` §3's discriminating experiment applied to voice: the test
that could *kill* the profile, not the one that flatters it.

### 5. Write `USER/VOICE.md`

Write the fingerprint and provenance. Never touch `USER/<name>.md`. Report a
terse confirmation: corpus size, the headline numbers, and the one-or-two
findings that override a `STYLE.md` default.

## Output

- An updated `USER/VOICE.md` (fingerprint + provenance, with
  `validated`/`not-validated` recorded).
- A terse session report: corpus size, headline sentence-length stats, and
  the findings that override a `STYLE.md` default.

## Anti-patterns

- Measuring from `## Draft` sections (the mind's writing) or secondary
  description — first-party `## Verbatim` only.
- Writing to `USER/<name>.md` — the spine is the human's; this skill never
  touches it.
- Silently applying a `STYLE.md` default that the corpus contradicts.
- Skipping the blind check and calling the profile current.
- Inventing a signature move or tell the measurement did not actually find.
- One draft in the blind check instead of three — a single foil hides the
  voice-vs-angle tradeoff.
- Reporting a statistic the helper does not compute (e.g. a mean sentence
  length) — read the emitted table.
