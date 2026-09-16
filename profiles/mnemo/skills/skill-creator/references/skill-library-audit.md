# Skill-library audit, restructuring, and retirement

Load for a library audit, a substantial restructure, or a retirement decision.
Use the authoring and verification procedure in `../SKILL.md`; this reference
adds the work needed to preserve rules across moves or deletions.

## Audit before implementation

1. **Inventory canonical sources.** Resolve profile bindings and symlinks;
   inspect instance-private and platform skill roots without counting the same
   real file twice. Record worktree changes. Include every entry point, owned
   support file, shared/root reference, resolver, and scheduled consumer.
   Separate source files, executable helpers/tests, and generated caches.
2. **Measure, then read.** Count lines and bytes programmatically. Entry points
   above roughly 500 lines or 40 KB merit inspection, not automatic splitting.
   Directory size is not loaded context. Read full procedures and dependencies;
   identify semantic duplication even when no files are byte-identical.
3. **Map rules to owners.** For each section, distinguish core procedure,
   conditional retrieval/recovery, executable mechanics, private evidence,
   and completed-run history. Identify competing rules and check them against
   current contracts and implementation before recommending which survives.
   Do not assume the newest anecdote is authoritative.
4. **Assign every file a disposition.** Keep, fix, streamline/restructure, or
   review for retirement; name the evidence and proposed owner. For moves,
   specify the load condition. For a missing companion, recover and verify
   it or remove the unsupported promise; do not invent an implementation.
   Reconcile inventory and disposition counts in code.
5. **Separate approval from findings.** An audit yields recommendations, not
   permission to merge, delete, change schedules, or publish. Implementation
   proceeds only within the user's approved scope. Report current facts
   separately from judgments and unverified deployment assumptions.

## Restructure while preserving behavior

- Keep the ordered pipeline and required gates in the entry point. Move
  source-specific branches, examples, and failure recovery into coherent
  topical references with explicit load conditions.
- Before removing text, record each unique rule as kept, merged, corrected,
  moved, or removed, with its destination or reason. Extract first, cut second.
- Integrate everyday rules into the step they affect. Do not move an entire
  pitfall appendix into an always-loaded reference. Retain bounded negative
  evidence needed to choose a recovery path; discard duplicated run narration.
- Keep scripts/tests unless inspection establishes they are superseded.
  Imports, test discovery, scheduled execution, and other skills are consumers
  even when the owning entry point does not mention a helper.
- Preserve private measurements and campaign results in the instance if they
  remain useful; never move them to another public-template file. Compare
  existing instance records before copying. Git preserves obsolete procedure
  and run history that has no remaining operative role.
- Compare divergent copies by real path, content, history, and ownership.
  A category directory may be a symlink, not an instance fork. Do not delete
  a template because another copy is labeled instance-local.

## Retire only a spent job

A completed campaign is not sufficient evidence of obsolescence. Confirm that
there is no plausible future invocation and that unique reusable content has
another verified home. Reusable bootstrap skills may still serve new instances.

Before removal, search resolver rows, other skills and support files, scripts,
imports/tests, brain references, scheduled prompts, and wrappers. Assign every
retained responsibility to a replacement, including non-Git side effects such
as feed refresh. Repair consumers first. Delete only approved, owned paths via
supported tools; a short redirect may be appropriate for a retired request.
Do not delete unrelated probes or caches as part of a prose cleanup.

## Verification and delivery

- Read the whole revised procedure and its callers; resolve paths in their
  declared namespace (skill-relative, profile-relative, or instance-relative).
- Parse frontmatter and run available governance checks, stating what they
  actually validate. Name-collision checks do not prove semantic consistency.
- Exercise changed scripts and representative scheduled paths as required by
  `skill-hygiene.md`; never post test output to live channels.
- Compare bytes that representative invocations actually load, including
  always-required references. Do not infer token savings from directory size
  or set an arbitrary percentage reduction that encourages deleting rules.
- Reconcile approved dispositions with the final changed-path list and the
  rule-retention checklist; record held items explicitly.
- Follow `skills/git-ops/SKILL.md` and each repository's authorization. No
  broad staging, automatic deletion, or unconditional commit/push. Preserve
  unrelated human edits and report local commits separately from publication.
