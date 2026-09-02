# skill_manage quirks — resolver scope, write gates, deadlocks

Consolidated 2026-09-02 from five disposable probe skills (deleted after
extraction: `skillmanage-resolver-probe`, `skillmanage-toplevel-probe`,
`test-find-path`, `test-skill-can-i-write`, `grant-section-test`) and the
`ml-conference-paper-ingest` session notes of the same date. Consult this
before debugging a skill_manage failure — the boundaries below are
structural, not transient.

## Resolver scope

- `skill_manage` resolves only **top-level skills** in the active profile
  (`skills/<name>/SKILL.md`). Skills reached through a category symlink
  (e.g. `skills/atticus/ → ~/git/scuderia/profiles/mnemo/skills/`) return
  "Skill not found in active profile" — all three name forms fail
  (`paper-ingest`, `atticus:paper-ingest`, `atticus/paper-ingest`; tried
  2026-09-02). Do not burn calls retrying name variants.
- Fix path: edit category-dir skills **on disk** at their real path
  (`~/git/scuderia/profiles/mnemo/skills/<name>/SKILL.md`). The
  instance's memory carries the same rule; this note is the durable
  in-repo record.

## Write gates

- `skill_manage` **can** create and patch top-level skills in the active
  profile (confirmed twice by probes, 2026-08).
- The read-before-write gate can **deadlock** when `skill_view` dedupes
  (`content_returned: false`): the gate never registers the load, so the
  patch never proceeds. Workaround: `write_file` on a `references/` path
  does not require the gate — use it for support-file additions when a
  SKILL.md patch is blocked.

## Probe hygiene

- A disposable probe skill is the sanctioned way to map a new boundary:
  create, observe, delete in the same session, then fold the finding
  into this file.
- Any probe must declare `triggers` in its frontmatter — a probe without
  it is a frontmatter-lint ERROR (the 2026-09-02 lint failure that
  surfaced this cleanup was exactly that).
- Never leave a probe in the tree: it loads into the skill index every
  session and costs context for zero procedure.
