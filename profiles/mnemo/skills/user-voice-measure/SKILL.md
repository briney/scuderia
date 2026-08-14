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
---

# User-voice measure — the writing fingerprint into `USER/VOICE.md`

The **derived** half of the writing-voice split (`DESIGN.md` §7,
`docs/decisions/user-directory.md`). `USER/<name>.md` §6 holds the
**judgment** — argument-level decisions, human-approved. This skill holds the
**measurement** — sentence length, tell-frequency, banned boilerplate — computed
from the human's own writing and written to `USER/VOICE.md`. Where a measured
fact conflicts with a generic default in `STYLE.md` §4–§5, the measured fact
wins: the corpus is the human's actual prose, not a hypothetical.

This is the soma analogue of the GBrain `draft-in-voice` skill's
"building a voice profile" half, adapted to a single-user brain where the
subject is the human themselves and the corpus already exists in the brain
(no consent step, no corpus-gathering step — see "What we changed").

> **Conventions:** `skills/conventions/capabilities.md` (the harness
> contract), `skills/conventions/quality.md` (honest flagging),
> `skills/conventions/brain-first.md` (pull from the brain before going
> external), `STYLE.md` §2 and §4–§5 (the voice standard this measures
> against).

## Capabilities

- **Required:** `brain-read`, `brain-write` (only on `USER/VOICE.md`).
- The measurement script is pure stdlib Python — no external dependency.

## What this guarantees

- Extracts the fingerprint **only from `## Verbatim` sections** — the
  human's preserved submitted prose — never from `## Draft` (that is the
  mind's writing) and never from third-party description.
- Separates narrative prose from list/scaffold-heavy verbatim; sentence-length
  statistics come from narrative prose only.
- Writes only `USER/VOICE.md`. Never edits `USER/<name>.md` — the spine
  stays under the human's hand.
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
    --brain <brain-root> --out USER/VOICE.md
```

The script (stdlib only):

- Splits `## Verbatim` into narrative vs. structured prose (median sentence
  length ≥ ~18 words marks narrative; anything shorter is list/scaffold-heavy
  and excluded from length statistics, still scanned for tells).
- Strips citation markers (`[1,2]`), ALL-CAPS section headers, figure
  captions, and source-hash preamble lines before counting.
- Computes: sentence-length distribution (median / mean / p10–p90 / p95,
  narrative only), em-dash density per 1,000 words, and counts of the
  tell-phrases from `STYLE.md` §4–§5 (`leverage`, `in order to`, `not
  only … but also`, `it is important to note`, `pivotal`, `paradigm shift`,
  etc.).
- Emits the `## The fingerprint` section of `USER/VOICE.md` plus a
  provenance block (grant count, sentence count, date).

### 3. Interpret against `STYLE.md`

Read the numbers against the generic defaults. The load-bearing move: a
corpus-count that *contradicts* a `STYLE.md` ban (e.g. "leverage" at
22/98k words means do not blanket-ban it) is a **finding**, surfaced in the
report — not a reason to silently override the default either way. The
measured fact wins, and the skill says so explicitly in `VOICE.md`.

### 4. Blind validation — the discriminating test

The profile is not "current" until it survives a blind check, mirroring the
GBrain builder's validation step:

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

## What we changed from GBrain `draft-in-voice`

GBrain's builder is for ghostwriting *another person* — it requires a consent
step (Step 0), a 20+-sample / 6+-month corpus-gathering bar, and a
per-person `people/<slug>-voice` page. Here the subject is the **human
themselves**, and the corpus **already lives in the brain** (`## Verbatim`
sections, first-party by construction). So:

- **No consent step** — it is the human's own published/submitted writing, and
  the artifact (`USER/VOICE.md`) is never posted or sent by the mind; it only
  informs how the mind writes *for* the human. GBrain's consent exists to
  stop impersonation; there is no impersonation here.
- **No corpus-gathering bar** — the bar GBrain enforces (20+ samples, 6+
  months) is for assembling a stranger's voice from scattered posts. The
  `## Verbatim` corpus is already threshold-satisfying where it exists, and
  the skill refuses cleanly where it does not.
- **No per-person page** — one human, one brain, one `USER/VOICE.md`. The
  `people/<slug>-voice` page is a multi-subject abstraction we do not need.
- **The blind check is the one thing we kept wholesale** — it is the piece
  worth stealing, the test that would reveal a fake fingerprint.

## Output

- An updated `USER/VOICE.md` (fingerprint + provenance, with
  `validated`/`not-validated` recorded).
- A terse session report: corpus size, headline sentence-length stats, and the
  findings that override a `STYLE.md` default.

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
