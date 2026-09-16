# Skill-management lookup and write failures

Load only when a skill-management operation fails. Runtime observations can
expire; compare the current tool schema and resolved path before using them.

## Diagnose the failure

1. Resolve the skill's actual home. Profile category directories may be
   symlinks into a platform checkout; do not create a duplicate local skill.
2. Distinguish a lookup failure from an ownership/protection refusal. An older
   runtime tested on 2026-09-02 failed to resolve category-symlink skills through
   `skill_manage`; this failure was reproduced for a mnemo category binding on
   2026-09-16. It does not establish the limits of every runtime or binding.
   Inspect the current schema and result rather than retrying name variants
   or assuming only top-level skills are supported.
3. If the management tool cannot resolve a permitted platform target, use the
   repository's normal file tools at its canonical home after reading it and
   checking authorization. A protection refusal is different: stop or obtain
   approval; do not route around it with direct filesystem writes.
4. If read-before-write validation reports an unseen skill despite a prior
   load, reload it. If a deduplicated response still leaves the gate blocked,
   report the failure rather than using an unguarded support-file write to
   evade the check.

## Disposable probes

Use a probe only when documentation and read-only inspection cannot answer
an operational question. Keep it in an authorized private scratch location,
not the platform skill index. If testing requires a registered skill, give it
valid frontmatter, track the exact owned path, and remove it in the same
session after recording the general rule. Do not remove somebody else's probe
or promote a probe inventory into permanent procedural context.
