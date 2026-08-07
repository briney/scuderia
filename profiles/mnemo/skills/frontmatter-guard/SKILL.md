---
name: frontmatter-guard
description: Validate page frontmatter against the schema — opening and closing fences, parseable YAML, the spine fields present, and the directory matching the page's kind. Repair the mechanical breakages; flag the ones that need a human.
triggers:
  - "validate frontmatter"
  - "check frontmatter"
  - "fix frontmatter"
  - "frontmatter audit"
  - "brain lint"
---

# Frontmatter guard — keep the schema honest

Every brain page opens with a YAML frontmatter block. When that block is
malformed, the page falls out of search, breaks the graph, and confuses every
skill that reads it. This skill is the **structural** member of the audit
cluster: it scans frontmatter against the schema and repairs the mechanical
breakages. See `RESOLVER.md` "Audit cluster" for the scope split — broad
health lives in `maintain`, citation-claim health lives in `citation-fixer`.

> **Conventions:** `skills/conventions/frontmatter.md` (the schema this validates
> against), `skills/conventions/page-kinds.md` (kind ↔ directory, plus the
> "Slug conventions" section — per-kind slug form),
> `skills/conventions/quality.md` (citations — separate audit; see
> `skills/citation-fixer/SKILL.md`),
> `skills/conventions/capabilities.md` (the harness contract),
> `skills/conventions/rem-cycle-contract.md` (the phase result + commit tiers, when run
> as a rem-cycle phase-1 delegate).

## Capabilities

`brain-read`, `brain-write`. Universal — works under any harness. Note
the **two-tier check**: the mechanical structural checks (YAML
parseable, kind ↔ directory, slug shape lowercase/hyphen/ASCII,
filename match, importance range) are enforced on every push by the CI
lint at `.github/scripts/lint-frontmatter.py`; this skill is the LLM
pass that catches *form*-level issues lint cannot reach.

### Slug-form audit (owned here)

The per-kind slug *form* — surname-first for `people/`
(`<surname-firstname>`), `<first-author-surname>-<year>-<topical-tag>`
for `papers/`, etc. — is enforced by this skill, not by `maintain`.
The CI lint warns on two-token people slugs that lead with a known
first name (heuristic), but only an LLM pass can decide whether
`smith-john` is correctly `<surname-firstname>` or incorrectly
`<firstname-firstname>` for a person actually named John Smith.

When run with the `audit slug shapes` trigger, this skill walks every
page under `people/` (and, with effort budget, the other kinds) and
flags slugs that violate the per-kind form, with a proposed correction.
The bug class this catches is the load-bearing one PR #19 named:
*back-links to the wrong shape silently fail to wire* — `paper-ingest`
and `grant-ingest` both key on the citation form, so a misordered
people slug breaks the author back-link chain.

## What this guarantees

- Every page scanned starts and ends its frontmatter with a `---` fence.
- The YAML between the fences parses.
- The spine fields are present (`kind`, `slug`, `title`, `importance`, `links`,
  `tags`).
- `kind` is set and matches the directory the page lives in.
- `slug` is present and unique across the brain.
- Mechanical breakages are repaired; breakages that need a human are flagged,
  never silently patched.

## Validation classes

| Code | Meaning | Repairable? |
|---|---|---|
| `MISSING_OPEN` | File does not start with `---` | No — needs a human |
| `MISSING_CLOSE` | No closing `---` before the body | Yes |
| `YAML_PARSE` | The frontmatter does not parse as YAML | Sometimes — depends on the cause |
| `KIND_MISMATCH` | `kind` is absent, or disagrees with the directory the file is in | Yes |
| `NULL_BYTES` | Binary corruption (`\x00`) in the file | Yes |
| `NESTED_QUOTES` | Unescaped inner quotes — `title: "Phil "Nick" Last"` | Yes |
| `EMPTY_FRONTMATTER` | Open and close fences present, nothing between | No — needs a human |

A page can also simply be **missing a spine field** (e.g. no `importance`, no
`tags`). That is not corruption — it is an incomplete page. Flag it; supply a
sensible value only when the page content makes it obvious, otherwise leave it
for the author.

## Phases

1. **Scan.** Walk the page-kind directories (`page-kinds.md`). For each `.md` file, read the
   leading frontmatter block. Hold the commit until the audit is reviewed.
2. **Classify.** Check each page against the validation classes above and
   against the spine. Record the page slug, the class, and whether it is
   repairable.
3. **Report.** Surface the counts in plain language — how many pages, grouped by
   class, with a sample of affected slugs. Do not dump raw structures.
4. **Repair the mechanical breakages.** For `MISSING_CLOSE`, `NULL_BYTES`,
   `NESTED_QUOTES`, `KIND_MISMATCH`, and the tractable `YAML_PARSE` cases, edit
   the file directly. The vault is a git repository — git history is the safety
   net, so make the fix in place; do not leave `.bak` files.
5. **Flag the rest.** `MISSING_OPEN` and `EMPTY_FRONTMATTER` almost always mean
   an author started a page and did not finish. Naming the page for the author
   is the right move; inserting fences around an unfinished draft is not.

## Repairs

- **`MISSING_CLOSE`** — insert a closing `---` immediately before the first body
  line (the first heading or paragraph after the YAML).
- **`KIND_MISMATCH`** — the directory is authoritative for `kind`. A page in
  `methods/` is `kind: method`. Set `kind` to match the directory; if `kind` is
  absent, add it. If the page genuinely belongs to a different kind, that is a
  filing error, not a frontmatter error — move the file and re-slug rather than
  rewriting the field (`_brain-filing-rules.md`).
- **`NULL_BYTES`** — strip the `\x00` bytes and re-save as clean UTF-8.
- **`NESTED_QUOTES`** — re-quote the value correctly: switch the outer quotes to
  single, or escape the inner quotes.
- **`YAML_PARSE`** — fix it only when the cause is unambiguous (a stray tab, an
  unquoted colon, a bad indent). When the parse failure could mean several
  things, flag it for a human instead of guessing.

Before any repair, confirm the page was not edited very recently — Bryan may
have it open in Obsidian. If it was, hold rather than clobber.

## Output

- A terse audit summary: total pages with issues, a count per class, a sample of
  slugs.
- After a repair pass: how many pages were fixed, by class, and which were left
  flagged for a human and why.
- State how many files a repair pass will touch *before* running it.

## As a rem-cycle phase

Invoked by the orchestrator as part of **phase 1 (hygiene)**, this skill runs
under `skills/conventions/rem-cycle-contract.md`:

- **Mode.** `dry-run` (report every fix, write nothing) or `normal` (auto-tier
  commits, propose-tier queues). Default `dry-run`.
- **Tiers** (mapping the validation classes):
  - *Auto* → `committed[]` (`category: frontmatter-fix`): the mechanical repairs
    — `MISSING_CLOSE`, `NULL_BYTES`, `NESTED_QUOTES`, `KIND_MISMATCH` (set the
    field to match the directory), a tractable `YAML_PARSE`, and a missing spine
    field whose value the page content makes obvious.
  - *Propose* → `proposed[]`: every judgment call — `MISSING_OPEN`,
    `EMPTY_FRONTMATTER`, an ambiguous `YAML_PARSE`, a filing **move** (a page in
    the wrong directory — moving and re-slugging rewrites inbound refs), and a
    **slug-form correction** (renaming a slug rewrites every inbound `[[slug]]`,
    so it is never auto; a same-name permutation also feeds `entity-resolution`'s
    dedup — flag the pair).
- **Output.** Emit the fenced-yaml phase result — `committed[]`, `proposed[]`
  (with evidence + `target_exists`), `metrics` (`pages_scanned`, counts per
  validation class, `fixes_applied`); no `cursor`. No chaining — the orchestrator
  routes; surface a slug/identity duplicate for `entity-resolution` rather than
  acting on it.

## Anti-patterns

- Auto-fixing `MISSING_OPEN` or `EMPTY_FRONTMATTER` — these need a human; the
  page is an unfinished draft, not corruption.
- In phase mode: auto-fixing a slug rename or a filing move — both rewrite
  inbound references, so both are proposed, never committed.
- Rewriting `kind` to silence a `KIND_MISMATCH` when the page is actually in the
  wrong directory — that is a filing move, not a field edit.
- Leaving `.bak` files behind. Git history is the safety net.
- Guessing at an ambiguous `YAML_PARSE` instead of flagging it.
- Dumping raw audit data instead of summarising it in plain language.
- Treating a missing spine field as corruption — it is an incomplete page.
