# Skill Library Audit — Recipe & Cross-Reference Deletion Checklist

The systematic procedure for inventorying all skills to find bloat,
duplication, and retirement candidates. Used successfully 2026-08-28
to identify and retire the `target-*` trio (446KB → 0).

## When to run

- "Inventory all skills" / "find bloated skills" / "audit the skill library"
- After a major skill rework (e.g. paper-ingest streamlining) — check
  whether other skills have the same disease.
- Periodically as part of `maintain` or `brain-architecture-audit`.

## Step 1: Measure every skill by size

Two locations to scan:
- Instance: `skills/` in the instance root (e.g. `~/git/atticus/skills/`)
- Template: `~/git/scuderia/profiles/mnemo/skills/` (mnemo profile, read-only
  to skill_manage — edit on disk directly)

```bash
# SKILL.md sizes, sorted largest first
find <skills-dir> -name "SKILL.md" -exec wc -c {} \; | sort -rn | head -40

# Total directory sizes (SKILL.md + references/ + scripts/ + templates/)
for d in <skills-dir>/*/; do
  name=$(basename "$d")
  size=$(du -sh "$d" 2>/dev/null | cut -f1)
  echo "$size  $name"
done | sort -rh
```

The threshold: any SKILL.md over ~40KB is a candidate. Total directory
size over ~50KB (with linked files) warrants investigation.

## Step 2: Diagnose the bloat pattern

For each candidate skill, extract section headers and per-section line
counts:

```bash
grep -n '^#' <SKILL.md>  # section headers with line numbers
wc -l <SKILL.md>         # total lines
```

Then compute per-section sizes. The canonical bloat signatures:

1. **Observation sections** — per-target/per-item writeups (500-700
   lines each) embedded inline instead of in `references/` files.
2. **Narrative changelogs** — a "Changelog" section that is actually
   full session writeups (3,000+ lines), not dated bullet entries.
3. **Encyclopedic lookup tables** — reference material that belongs in
   `references/<topic>.md`.
4. **Provenance annotations** — "Observed: PMID XXX, YYYY-MM-DD" tags
   scattered through the procedure.

The tell: if >50% of the file is session outputs and the actual
procedure is <350 lines, the skill has the bloat disease.

## Step 3: Check for content duplication

Before deleting or streamlining, check whether the skill's content
already exists elsewhere:

```bash
# Are inline observations also in reference files?
ls <skill-dir>/references/ | wc -l
# Diff observation filenames against existing reference profiles
comm -12 \
  <(ls <skill-dir>/references/ | sed 's/-profile-observations.md//' | sort) \
  <(ls <reference-corpus>/profiles/ | sed 's/\.md//' | sort) | wc -l

# Is the methodology already captured in a reference corpus master.md?
grep -c "binary bar\|scope rules\|discovery methodology\|gap-fill" \
  <reference-corpus>/master.md
```

If 65 of 71 observation files already have corresponding final profiles
in a reference corpus, the skill is superseded — a Mode D retire, not
Mode C streamline.

## Step 4: Check for template-vs-instance duplicates

A skill may exist in both `skills/atticus/` (instance-local, evolved)
and `skills/` (template, stale):

```bash
for skill in $(ls skills/); do
  if [ -d "skills/atticus/$skill" ]; then
    echo "DUPLICATE: $skill"
    echo "  instance: $(wc -c < skills/$skill/SKILL.md) bytes"
    echo "  template: $(wc -c < skills/atticus/$skill/SKILL.md) bytes"
    diff skills/$skill/SKILL.md skills/atticus/$skill/SKILL.md > /dev/null \
      && echo "  identical" || echo "  DIFFERENT (instance is evolved)"
  fi
done
```

The instance-local copy is always the evolved one (it has real
operational learnings). The template copy is stale. Delete the template
copy, keep the instance one.

## Step 5: Check for cross-references before deleting

Before deleting any skill, grep for references to it across:
- `RESOLVER.md` — the routing table (critical)
- Other skills' SKILL.md files — "Relationship to other skills" sections
- Other skills' `references/` files — source-extraction notes, etc.
- Cron job config: `~/.hermes/profiles/<profile>/cron/jobs.json`
- Brain pages and working-docs (informational — these usually just
  mention the skill name, not its path, and don't need updating)

```bash
grep -rn "skills/<skill-name>" \
  ~/git/scuderia/profiles/mnemo/skills/ \
  ~/git/atticus/ \
  ~/.hermes/profiles/atticus/cron/ \
  2>/dev/null | grep -v ".git/" | grep -v "references/"
```

For each hit, patch the reference to point to the replacement (typically
the reference corpus `master.md` or `templates/` path).

## Step 6: Rescue unique content, then delete

1. **Diff the skill against its replacement** (reference corpus,
   master.md, etc.). Move only the un-duplicated pieces to the corpus's
   `notes/` directory (create it if it doesn't exist).
2. **Typical rescued content**: methodology notes not in master.md, API
   code templates, orphan observation files without final profiles.
3. **Delete the skill directory** (`rm -rf`).
4. **Commit separately** in each repo (scuderia for template skills,
   atticus for rescued reference files).
5. **Push both repos.**

## Step 7: Verify

```bash
# Skills gone
ls <skills-dir> | grep -E "<deleted-skill-names>" || echo "clean"

# No broken references remain
grep -rn "skills/<deleted-skill-name>" \
  ~/git/scuderia/profiles/mnemo/ \
  ~/git/atticus/ \
  ~/.hermes/profiles/atticus/cron/ \
  2>/dev/null | grep -v ".git/" || echo "clean"
```
