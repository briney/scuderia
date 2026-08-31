---
name: style-promote
description: Use when back-porting a demonstrated STYLE feature, rule, or whole domain from an ergon instance to the profile template — genericized, privacy-checked, manifest-wired.
triggers:
  - "promote style"
  - "back-port style"
  - "push STYLE to the profile"
  - "promote this style feature"
  - "STYLE to template"
  - "upstream a style rule"
---

# style-promote — instance → profile back-port for STYLE/

The ergon STYLE contract: the **profile template** (`profiles/ergon/STYLE/`
in the scuderia checkout) is the broadcast — opinionated but generic
defaults every instance is scaffolded with. The **instance copy**
(`<instance>/STYLE/`) is the record — instance-owned, diverges freely, and
keeps the full provenance (run slugs, project pointers, panel context).
New style content is always *earned* in an instance run first
(`STYLE/STYLE.md` §5: crystallization, not speculation). Promotion moves
the demonstrated, genericizable part of that earning upstream so every
current and future instance inherits it.

## When to use

- The human pulls the trigger: "promote this style feature/domain" after a
  run has crystallized something demonstrably useful.
- This skill is **manual-trigger only**. Never promote unprompted, on a
  schedule, or as a side effect of a render/figure run.

## When NOT to promote

- Content not yet demonstrated in a corrected run (that is speculation —
  `STYLE/STYLE.md` §5 forbids it).
- Instance-specific taste the human wants kept local (their call, not
  yours — if unsure, ask).
- Anything instance-private. **The scuderia repo is public.** See the
  privacy gate below; it is a hard stop, not a checklist to rush.

## Procedure

1. **Resolve the scuderia checkout.** The template skills are symlinked
   into the harness profile: `readlink ~/.hermes/profiles/<instance>/skills/ergon`
   gives `<scuderia>/profiles/ergon/skills`. If that path does not resolve,
   ask the human for the checkout location — do not guess.
2. **Diff instance vs template**, file by file:
   `diff -ru <instance>/STYLE <scuderia>/profiles/ergon/STYLE`.
   Expected standing noise: the template `STYLE.md` carries a
   template-reader preamble (stripped at scaffold) and `{{INSTANCE_NAME}}`
   placeholders, and every file's provenance lines are genericized
   upstream. Everything else in the diff is a candidate for promotion —
   walk it hunk by hunk.
3. **Select.** For each candidate: whole new file (new modality, type, or
   asset) or new/changed rules in an existing file. Confirm the selection
   with the human before writing — promotion is their call.
4. **Genericize.** In the promoted text:
   - Drop run-directory paths (`runs/<slug>`), `agora://` project slugs,
     panel/project names, mAb identifiers, and any name of a specific
     private experiment. Replace with "a demonstrated run in the founding
     instance" (or "…in an instance run") plus the date.
   - Keep: dates, "user correction; locked" markers, public PDB IDs,
     sequence motifs, and the actual rule content. The *rule* travels;
     the *history* stays home.
   - `{{INSTANCE_NAME}}` placeholders belong only in files that already
     use them (the spine). Do not introduce new placeholders elsewhere.
5. **Privacy gate (hard stop).** The scuderia remote is public
   (`github.com/briney/scuderia`). Before writing, grep the staged
   template text for instance-private residue and expect zero hits:
   `grep -rniE "agora://|runs/20[0-9]{2}|<instance-name>" <changed files>`.
   Panel names and antigen-project identifiers from private work fail this
   gate too — when in doubt, genericize harder.
6. **Wire new files into the manifest.** Every new template file needs a
   `files:` entry in `profiles/ergon/manifest.yaml` (template and target
   paths are the same; only the spine uses `strip_header: true`). Parent
   directories are created automatically at scaffold — no `dirs:` entries
   needed. A new type file also needs its row added to the parent modality
   file's routing table in the template.
7. **Write the template; never touch the instance copy.** The instance
   keeps its full-provenance version. Promotion never overwrites, prunes,
   or "syncs down."
8. **Verify** (all three, in the scuderia checkout):
   - Scaffold: `python3 setup/scuderia init --profile ergon --name styletest --path /tmp/ergon-styletest && python3 setup/scuderia doctor --path /tmp/ergon-styletest` — must pass; then `rm -rf /tmp/ergon-styletest`.
   - Substitution audit: `grep -rn "{{" /tmp/ergon-styletest/STYLE/` on a fresh scaffold → zero hits; and the scaffolded `STYLE/STYLE.md` must start with the body (preamble stripped, `{{INSTANCE_NAME}}` replaced).
   - If the spine was edited: confirm the template preamble still ends
     with a bare `> ---` line — that terminator is what `strip_header`
     keys on; losing it leaks the preamble into every new instance.
9. **Commit and cross-stamp.**
   - Commit the scuderia checkout: `ergon STYLE: promote <feature/domain> from <instance> (<run slug>)`. Do not push without the human's go — the remote is public.
   - Cross-stamp the instance file's header with one line:
     `Promoted to the profile template at scuderia@<sha> (<date>); this copy remains the full-provenance record.` Commit the instance repo.
   - Record the promotion in the instance's run log if the earning run is
     still open.

## Pitfalls

- **Substitution runs on every copied file**, including YAML and `.cxc`
  presets. Only the exact tokens `{{INSTANCE_NAME}}` / `{{CREATED}}` are
  replaced, but a stray `{{CREATED}}` in a comment would still be eaten —
  audit fresh scaffold output when promoting assets.
- **The template preamble is reader-facing only.** Anything an instance
  must keep (the instance-ownership note, tier rules) goes in the body
  below `> ---`.
- **Forked divergence is owned by the instance.** If an instance has
  edited a file you are promoting into, promote only the generic hunks —
  do not "reconcile" by overwriting the instance's local locks.
- **Palette changes regenerate presets.** `palettes.yaml` is canonical;
  `assets/chimera/*.cxc` are generated from it. Promoting palette edits
  means regenerating and promoting the presets in the same commit.
- **Doctor does not (yet) check that manifest files exist in instances.**
  The scaffold test in step 8 is the real verification — do not skip it.
