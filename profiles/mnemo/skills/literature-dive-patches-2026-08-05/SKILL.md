---
name: literature-dive-patches-2026-08-05
description: "Patch pending literature-dive: EMFILE and SS PMID fixes."
triggers:
  - "patch literature-dive skill"
---

# literature-dive — profile-side patches (2026-08-05)

The authoritative `literature-dive` SKILL.md lives in the vault at
`skills/literature-dive/SKILL.md`. This skill records patches
from the 2026-08-05 non-enveloped virus glycoprotein dive session.

## Patch 2026-08-05: Raise FD limit before dispatching subagents

### Add to Phase 2 (Review ingest) and Phase 4 (Tier 1 ingest)

The macOS default soft FD limit is 256 (`ulimit -n`). This is too low
for a literature dive that dispatches parallel subagents. Observed
2026-08-05: the non-enveloped virus glycoprotein dive crashed with
`OSError: [Errno 24] Too many open files` at Phase 2, killing both
the orchestrator and all 3 dispatched subagents (they failed instantly
with `[Errno 24] Too many open files: '/System/Library/CoreServices/SystemVersion.plist'`).
Same root cause as the dashboard FD exhaustion
(`hermes-remote-access/references/fd-exhaustion-incident.md`).

**Fix: run `ulimit -n 4096` at the first terminal command of the dive,
before any subagent dispatch.** This raises the soft limit for the
agent process's shell and is inherited by subagents. Each new session
inherits the login default (256); do not assume a prior session's
`ulimit` carries over.

### Crash recovery pattern

1. Restart Hermes (clears the FD leak).
2. Run `ulimit -n 4096` immediately.
3. Use `session_search` to find the crashed session and reconstruct
   state: which phase, which reviews/papers selected, which batches
   dispatched, which files written.
4. Check filesystem for partial writes (`ls papers/`).
5. Resume from the failure point — do not restart from Phase 1.

## Patch 2026-08-05: Semantic Scholar reference PMIDs can be wrong

### Add to Phase 3 (Tier classification)

When using the Semantic Scholar Graph API to retrieve a review's
reference list (fallback when full text is paywalled), the PMIDs in
`references.externalIds.PubMed` can resolve to completely different
papers. Observed 2026-08-05: the Moti 2026 HEV-calicivirus review's
Semantic Scholar reference list cited Guu 2009 HEV VLP with PMID
19652487, which resolves to a Japanese encephalitis vaccine paper
(Shirafuji 2009). The correct PMID is 19622744, confirmed via CrossRef
DOI lookup (`10.1073/pnas.0904848106` → PMID 19622744).

Same class of error as the DOI cross-check pitfall in `paper-ingest`.
Semantic Scholar is reliable for DOIs but less reliable for PMIDs.

**Fix: cross-check Semantic Scholar reference PMIDs before using
them.** Verify each PMID via PubMed E-utilities and check the returned
title matches. If they disagree, find the correct PMID via CrossRef
DOI lookup then PubMed esearch. Do not pass unverified PMIDs to
subagents.

## Patch 2026-08-05: PubMed E-utilities 429 rate limiting

Rapid sequential E-utilities calls trigger HTTP 429. Fix: add `sleep 2`
between calls. The rate limit resets quickly — a 3-second pause is
usually sufficient.

## Companion vault-side skills that should absorb these patches

- `literature-dive/SKILL.md` — Phase 2/4 EMFILE prevention, Phase 3
  SS PMID verification, Phase 3 E-utilities rate limiting.
- The existing `literature-dive-patches` skill carries the 2026-08-04
  patches (batching, non-duplicative selection, ledger race). These
  2026-08-05 patches should be appended there or folded into the
  vault-side `literature-dive/SKILL.md`.
