---
name: paper-ingest
description: "Profile-side patch pointer for the paper-ingest vault skill."
triggers:
  - "patch paper-ingest skill"
---

# paper-ingest — profile-side patches

The authoritative `paper-ingest` SKILL.md lives in the vault at
`skills/paper-ingest/SKILL.md` and is loaded by `skill_view`
from there. When `skill_manage` cannot patch the vault copy directly, record
the patch here so a future vault-edit session can fold it in.

## Patch 2026-07-17: Seed DOI cross-check + PMC full-text path

### Add to Phase 1 (after the "CrossRef via browser" paragraph)

```markdown
**Cross-check the stub's seed DOI against the PMID.** A stub's
`## Citation` block or frontmatter `doi` can carry the *wrong* DOI.
This happens when the stub was created from a citation that referenced
a *different* paper by the same authors — a companion primary research
paper, a preprint→published pair, or an erratum. If the stub carries a
`pmid`, resolve it via PubMed and compare the PubMed-returned DOI to
the stub's seed DOI. If they disagree, the PubMed DOI is authoritative
(PubMed is the canonical record). Log the correction in the analysis or
a brief note; do not silently overwrite without flagging the
discrepancy. Observed instance (2026-07-17): stub
`tan-2018-self-reactivity-spectrum` carried DOI
`10.4049/jimmunol.1801565` (the companion J Immunol primary research
paper, PMID 30962292), but the stub's PMID 31631352 resolved to DOI
`10.1111/imr.12818` (the Immunological Reviews review article). The
companion paper was a *reference inside* the review, not the review
itself — the stub creator conflated the two.

**PMC full text via E-utilities (open-access articles).** When the
paper has a `pmcid` (from the PubMed XML fetched in Phase 1), the
full article body is available as structured XML via PMC
E-utilities:
`curl -sL "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=<PMCID>&rettype=xml"`
The response contains the complete `<body>` with `<sec>` sections,
`<p>` paragraphs, and `<xref>` cross-references — sufficient for
structural distillation without browser scraping. This is the
preferred full-text path for open-access papers (NIHMS manuscripts,
fully OA articles). For paywalled articles with no PMC copy, fall
back to the browser-based extraction pattern
(`references/full-text-access.md`).
```

### Add to Anti-patterns section

```markdown
- **Trusting the stub's seed DOI without cross-checking against the
  PMID.** A stub's `## Citation` block or frontmatter `doi` can carry
  the wrong DOI — typically when the stub was created from a citation
  that referenced a *different* paper by the same authors (companion
  primary research paper, preprint→published pair). Always resolve the
  PMID (if the stub carries one) via PubMed and compare the returned DOI
  to the seed DOI. If they disagree, PubMed is authoritative. Observed
  2026-07-17: Tan 2018 review stub carried the companion J Immunol
  paper's DOI instead of the review's own DOI.
```

### Reference file to create

`references/pubmed-pmc-full-text-paths.md` — consolidates the three
full-text/metadata paths (PubMed XML identity, PMC XML full text, browser
fallback) with session evidence from Zhao 2019, Tan 2018, and Pelanda 2022.
The companion reference skill `paper-ingest-pubmed-resolver` already
carries this content in its SKILL.md.

## Patch 2026-07-18: Path-fix, Nature.com full-text path, erratum-PMID disambiguation, Europe-PMC ORCIDs, ledger duplicate-merge

### Fix the authoritative-path reference (this file AND the companions)

The path `skills/atticus/paper-ingest/SKILL.md` (a stale harness-binding path used in the
prior version of this pointer's frontmatter description, the "The
authoritative" paragraph, and copied verbatim in every companion
reference skill's body) **does not exist**. The real vault location is
`skills/paper-ingest/SKILL.md` — no `atticus/` segment under
`skills/`. A 2026-07-18 session wasted a search round-trip on the wrong
path and had to reconstruct the workflow from the companion references +
conventions + an exemplar page.

**Fix in the vault SKILL.md:** the `description:` and any in-body path
reference should read `skills/paper-ingest/SKILL.md`.
**Fix in each companion** (`paper-ingest-pubmed-resolver`,
`paper-ingest-doi-pmid-crosscheck`, `paper-ingest-fallback-patterns`,
`paper-ingest-browser-fulltext`, `paper-ingest-full-text-access`): their
bodies reference `skills/atticus/paper-ingest/SKILL.md` —
correct to `skills/paper-ingest/SKILL.md`.

### Add to the full-text decision tree (Phase 4 / references/full-text-access.md)

```markdown
**Nature.com publisher pages render the full article body reliably.**
When the paper is in a Nature-family journal (Nature, Nature Immunology,
Nature Methods, Nature Communications, etc.) and is free-to-read or the
session has access, `browser_navigate` to
`https://www.nature.com/articles/<doi-suffix>` (e.g. `ni.3494` for
`10.1038/ni.3494`) yields the complete article: all Results
subsections, Discussion, Methods, figure captions. Extract via
`browser_console` with
`document.querySelector('article').innerText.substring(N, N+15000)` and
paginate. This is a distinct path from (a) PMC OA, which often hits
reCAPTCHA, and (b) the generic "journal HTML" branch — Nature's template
is one of the most reliably-rendered publisher layouts and should be
tried *before* the generic journal-HTML fallback when the DOI resolves
to nature.com. Observed 2026-07-18 (Locci 2016, Nat Immunol): PMC OA
curl blocked + PMC browser reCAPTCHA + Europe PMC minimal DOM, but
nature.com rendered all 8 Results subsections + Discussion cleanly.
```

### Add to Phase 1 (erratum-PMID disambiguation)

```markdown
**When a PubMed title search returns multiple PMIDs, check for an
erratum pair.** A title search can return both the primary paper and
its published erratum (same title, prefixed "Erratum:" in the erratum's
`<ArticleTitle>`). Disambiguate via the PubMed XML
`<CommentsCorrectionsList>`: the erratum carries
`<CommentsCorrections RefType="ErratumFor">` pointing at the primary
PMID, and the primary carries `<CommentsCorrections RefType="ErratumIn">`
pointing at the erratum. The primary paper is the one with
`<PublicationType>` "Journal Article" (not "Published Erratum") and the
full `<Abstract>`. Always record the erratum's PMID in the Ingest log
when one exists — it is part of the paper's bibliographic record.
Observed 2026-07-18 (Locci 2016): title search returned 27376469
(primary) and 27648551 (erratum); the erratum's
`<CommentsCorrections RefType="ErratumFor">` confirmed 27376469 as
primary.
```

### Add to Phase 8 (ORCID capture)

```markdown
**Europe PMC's author-ORCID section supplements PubMed XML.** PubMed XML
`<Identifier Source="ORCID">` often carries only the senior/corresponding
author's ORCID. When the paper is on Europe PMC
(`https://europepmc.org/article/MED/<PMID>`), the "ORCIDs linked to this
article" section lists ORCIDs for multiple authors with the mapping
explicit (`AuthorName | ORCID`). Fetch via `browser_console`:
`Array.from(document.querySelectorAll('a[href*="orcid.org"]')).map(a => ({orcid: a.href.replace('https://orcid.org/',''), ctx: a.closest('li,p,div,span')?.textContent.trim().substring(0,80)}))`.
Observed 2026-07-18 (Locci 2016): PubMed XML had only Crotty's ORCID;
Europe PMC supplied Wu (0000-0002-9302-8904) and Mikulski
(0000-0002-1918-9216) as well.
```

### Add to the concurrency-hazard section (sibling ledger duplicates)

```markdown
**A sibling subagent can create a duplicate ledger entry for the same
author.** When `ingest-pending-papers` runs paper-ingest subagents in
parallel on companion papers (e.g. Locci 2016 and Carnathan 2020, which
share senior author Shane Crotty), each subagent takes Branch 3 for the
shared author and appends a separate `people/_ledger.yaml` entry. Unlike
the `cited_by` hazard (which `patch` handles because the target is a
single field), a duplicate *entry* requires an explicit merge after the
fact. The merge: keep the entry with the ORCID (ORCID is the
disambiguation key per `author-ledger.md`), union the `citations` lists
(deduped), union the `affiliations` (deduped), and delete the ORCID-less
duplicate. Verify with `yaml.safe_load` that there is exactly one entry
per slug after the merge. Observed 2026-07-18: two `crotty-shane` entries
— one with ORCID + locci citation (this session), one without ORCID +
carnathan citation (sibling) — merged into one with ORCID, both
citations, and 4 affiliations.
```

### Reference file to create

`references/nature-full-text-path.md` — documents the Nature.com
publisher-page extraction path with the exact selector/pagination
commands and the 2026-07-18 Locci session evidence. Complements
`references/full-text-access.md` (the decision tree) and
`references/pubmed-pmc-full-text-paths.md` (the PMC/E-utilities path).

### Companion references that should absorb these patches

- `paper-ingest-full-text-access/SKILL.md` — add the Nature.com branch
  to the decision tree.
- `paper-ingest-pubmed-resolver/SKILL.md` — add the erratum-PMID
  disambiguation and the Europe-PMC ORCID supplement.
- `paper-ingest-fallback-patterns/SKILL.md` — add the ledger
  duplicate-merge hazard alongside the existing `cited_by` concurrency
  hazard (§3 of that file).
- All five companions — fix the `skills/atticus/paper-ingest/`
  path reference per §1 above.

## Patch 2026-07-19: Workflow-reconstruction protocol, slug-initial vs full-firstname

Discovered across four 2026-07-19 stub-fill sessions (Lodberg 2021, Harrison
2005, Kuranobu 2020, Ota 2003). The full-text/publisher-block and
concurrency/tirith patches from these sessions were folded into the companions
(`paper-ingest-full-text-access` gained the branch-0 Europe-PMC-REST gate,
three-source closure, and the Known-publisher-blocks table for
Elsevier/Wiley/Karger + the Nature counter-example; `paper-ingest-fallback-patterns`
gained §5 tirith file-intermediary, §6 Europe PMC REST ORCIDs, §7 `links:`
concurrency hazard). Two patches remain here.

### Workflow-reconstruction protocol (there is no Phase 1-N document)

This pointer and the five companions describe paper-ingest by *facet* (identity
resolution, full-text access, fallbacks, concurrency) but no single file
assembles the numbered Phase 1-N sequence. When a session needs the end-to-end
workflow and no assembled SKILL.md materializes, reconstruct it:

1. Read this pointer for accumulated patches (each says "Add to Phase X").
2. Read the five companions for phase detail: `paper-ingest-pubmed-resolver`
   (Phase 1 identity), `paper-ingest-full-text-access` (Phase 4 decision tree,
   incl. the branch-0 OA gate), `paper-ingest-browser-fulltext` (Phase 4 browser
   extraction), `paper-ingest-fallback-patterns` (Phase 1 fallbacks + Phase 7 +
   concurrency), `paper-ingest-doi-pmid-crosscheck` (Phase 1 DOI/PMID cross-check).
3. Read `skills/conventions/frontmatter.md` (paper-kind schema), `author-ledger.md`
   (Phase 8), `page-kinds.md` (slug forms), `graph-and-links.md` (typed edges).
4. Read one recent exemplar (e.g. `papers/carnathan-2020-activin-a-adjuvanticity.md`)
   for body anatomy (Abstract / Context / Approach / Findings / Limitations /
   Analysis).
5. Assemble: Phase 1 (identity — PubMed XML + CrossRef, DOI/PMID cross-check,
   erratum disambiguation), Phase 3 (retraction check via `<PublicationTypeList>`),
   Phase 4 (full-text — branch-0 OA gate → PMC → Nature → known-block pass-through
   → abstract-only + `needs-enrichment: true`), Phase 7 (threshold-gated
   bibliography walk), Phase 8 (author ledger Branch 1/2/3 + ORCID capture),
   Phase 10 (verification — YAML parses, ledger valid, links resolve, no dup slugs).

The durable fix is a real assembled SKILL.md; until then this protocol is the
working substitute.

### Slug-initial vs full-firstname (Phase 8)

`page-kinds.md` convention is `<surname>-<given>` with the *full* first name
(`carnathan-diane`, not `carnathan-d`). PubMed XML gives `<ForeName>` (full) and
`<Initials>`. When a parent agent explicitly specifies `people/<surname>-<initial>`
(e.g. `people/lodberg-a`), follow the task instruction — but record the full
first name in the ledger `name:` field so a later normalization pass can expand
the slug. Observed 2026-07-19: Lodberg 2021 task specified `people/lodberg-a`;
`ForeName=Andreas` would conventionally yield `lodberg-andreas`; slug followed
the task, `name` stored "Andreas Lodberg".

## Patch 2026-07-24: Stub slug renaming, different-slug ledger duplicates, person-page author_on concurrent-edit malformation

### Add to Phase 5 (stub replacement / slug renaming during literature-dive ingest)

```markdown
**When a literature-dive task specifies a different slug than the existing
stub, rename the stub — do not create a duplicate.** A parent agent
(literature-dive, idea-ingest) may specify `papers/<author>-<year>-<descriptive>`
as the target slug, while a bibliography-walk stub already exists at
`papers/<author>-<year>-<different-descriptive>` for the same paper (same
DOI). Both slugs resolve to the same real-world object; creating a second
page would fragment the graph. The correct workflow:

1. Create the paper page at the task-specified slug with full content.
2. Copy the existing stub's `cited_by` list into the new page's `cited_by`
   (append-only — preserve all entries).
3. Delete the old stub file.
4. Log the rename in the Ingest log: "Paper page created from existing stub
   `<old-slug>` (same DOI), renamed to `<new-slug>` per literature-dive task
   specification."

Before deleting, grep the vault for references to the old slug in other
pages' frontmatter `links:` or body wikilinks — if any exist, update them
to the new slug. (In practice, stubs rarely accumulate inbound links before
being filled, but verify.) Observed 2026-07-24: Lee 2008 stub at
`lee-2008-ebola-gp-survivor-antibody` was replaced with
`lee-2008-ebola-gp-kz52-structure` per literature-dive task spec; `cited_by`
from flyak-2016 and bornholdt-2016 preserved; no inbound links to the old
slug found.
```

### Add to the concurrency-hazard section (different-slug, same-person ledger duplicates)

```markdown
**A sibling subagent can create a ledger entry for the same person under a
different slug.** The 2026-07-18 patch covered same-slug duplicates (two
`crotty-shane` entries). A more subtle variant: the sibling uses
`<surname>-<given>-<middle-initial>` (e.g. `lee-jeffrey-e`) while you use
`<surname>-<given>` (e.g. `lee-jeffrey`), or vice versa. Searching the ledger
by your intended slug misses the sibling's entry because the slugs differ.

**The fix:** Before appending a new ledger entry, search by *name*, not
just by slug:
```bash
grep -i "name: <Full Name>" people/_ledger.yaml
```
If an existing entry matches by name (even under a different slug), merge
your citation into it rather than creating a new entry. The merge: append
your `papers/<slug>` to the existing entry's `citations:` list, union
`affiliations` (deduped), and keep the existing slug. If the existing entry
has an ORCID and yours does not, keep the ORCID. Do not create a new entry
under a different slug for the same person — this fragments the citation
count and delays promotion past the 5-citation threshold.

Observed 2026-07-24 (Lee 2008): Sibling subagent ingesting Hashiguchi 2015
had already added `lee-jeffrey-e` (with middle initial) to the ledger. This
session added `lee-jeffrey` (without middle initial) — a duplicate for the
same person (Jeffrey E. Lee, Scripps). Fix: merged the Lee 2008 citation
into the existing `lee-jeffrey-e` entry and removed the duplicate
`lee-jeffrey` entry. Same issue for `fusco-marnie` (sibling had the entry
from Hashiguchi 2015; this session created a duplicate).
```

### Add to the concurrency-hazard section (person-page author_on malformation)

```markdown
**A sibling subagent can modify a person page between your read and your
patch, producing malformed YAML.** When patching `author_on:` on a person
page (Branch 1 of Phase 8), the `patch` tool may apply your old_string
against a file that a sibling has already modified — the result can be a
doubled key (e.g. `author_on:\n  author_on:`) with wrong indentation,
producing invalid YAML.

**The fix:** When `patch` reports a sibling-modification warning
("_warning: ... was modified by sibling subagent ..."), always re-read the
file and verify the YAML is well-formed. If the frontmatter is malformed
(doubled keys, wrong indentation), re-read the current content and apply a
corrective patch against the actual (post-sibling) state. Do not assume the
patch succeeded cleanly — the warning means the file changed under you, and
the result may not be what you intended.

Observed 2026-07-24 (Saphire page): A sibling subagent modified
`saphire-erica.md` concurrently. The `patch` produced
`author_on:\n  author_on:\n    - papers/lee-2008-...` (doubled key, nested
indentation). Fix: re-read the file, applied a corrective patch replacing
the doubled-key block with a properly indented single `author_on:` list.
```

## Patch 2026-08-02: Sibling ledger wipe, post-reset slug reconciliation, non-ASCII slug derivation

Discovered during the He et al. 2026 (AID/TET2/Irf4, PMID 42043375, 21
authors) ingest. Three durable lessons. The full-text path (PMC OA via
E-utilities + `pmc_xml_body_parser.py`) worked cleanly — no new
full-text learning. The ledger concurrency and slug-derivation issues
are the durable learnings.

### Add to the concurrency-hazard section (sibling full-ledger reset/wipe)

```markdown
**A sibling subagent can REWRITE the entire `people/_ledger.yaml`,
wiping your appended entries.** Prior patches (2026-07-18, 2026-07-24)
covered in-place concurrent edits — duplicate entries, malformed `author_on:`,
changed `links:`. A more severe variant: the sibling does a *full-file
reset* (its own clean re-dump of the ledger), which silently discards every
entry you appended in this session. You discover this only when a later
verification step (`grep` for your slugs, or `yaml.safe_load` + set
membership) reports your entries missing — the `patch` tool's
sibling-modification warning fires per-edit, not for a wholesale rewrite
that happened between two of your tool calls.

**The fix (verify-after-append, don't trust a single append):**
1. After appending your author entries, re-read the ledger with
   `python3 -c 'import yaml; ...'` and assert (a) `yaml.safe_load` parses
   (sibling's rewrite is valid but may differ in formatting), (b) your
   slugs are present, (c) `collections.Counter` reports no duplicate
   slugs, (d) the count of entries citing your paper equals your author
   count.
2. If entries are missing, re-append them. If duplicates appeared (the
   sibling's reset re-added an entry for an author you also merged),
   re-merge: keep the entry with the ORCID, union `citations` (deduped),
   union `affiliations` (deduped), delete the duplicate.
3. If a slug you wrote was normalized differently by the sibling's
   rewrite (e.g. `westerberg-lisa-s` in your frontmatter vs
   `westerberg-lisa` in the sibling's ledger), the **frontmatter is
   authoritative** (it is the canonical reference the lint resolves
   against). Patch the ledger slug to match the frontmatter, not the
   reverse — changing the frontmatter would break the `authors:` → ledger
   resolution the lint checks.

Observed 2026-08-02 (He 2026, 21 authors): Appended 21 entries; a sibling
subagent (`sa-2-98da72ff` / `sa-1-449bd59b`) reset the ledger to its own
clean dump, dropping 19 of my 21 new entries (the 2 merged-into-existing
entries survived because the sibling preserved the originals). On
re-verification, `westerberg-lisa-s` was missing — the sibling's reset had
re-added it as `westerberg-lisa` (no middle initial). Fix: re-appended
the 19 dropped entries, then patched the ledger slug `westerberg-lisa` →
`westerberg-lisa-s` to match the frontmatter. Final: 21/21 resolve, no
duplicates.

**Operational note:** the `cat >> people/_ledger.yaml << 'EOF'` heredoc
form is NOT reliable for appending entries — long affiliation strings
get line-wrapped by the terminal in ways that diverge from the heredoc
source, and a sibling reset can interleave. Prefer building the YAML
block in Python (with explicit short strings that won't wrap) and
writing via a single `write_file`/`patch` call, then verifying.
```

### Add to Phase 8 (non-ASCII author slug derivation from PubMed XML)

```markdown
**Naïve regex slugification of `<LastName>`/`<ForeName>` mangles
accented and non-ASCII names.** PubMed XML carries names with diacritics
(Rômulo, Søren, José, Ström). A slugifier like
`re.sub(r"[^a-z0-9]+", "-", s.lower())` strips the entire accented
character, producing `r-mulo` (from Rômulo), `s-ren` (from Søren),
`jos` (from José), `str-m` (from Ström) — broken slugs that won't
match the frontmatter `authors:` list.

**The fix:** ASCII-fold *before* slugifying, decomposing accented
characters to their base form (Rômulo→Romulo, Søren→Soren, José→Jose,
Ström→Strom). Two options:

```python
# Option A: unicodedata (stdlib, no deps)
import unicodedata, re
def slugify(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii','ignore').decode()
    s = re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
    return s

# Option B: build slugs by hand for a known author list
# (safer for a single paper — you see and control each slug)
authors = [
  ("d-aulerio", "roberta", ""),      # D'Aulerio → d-aulerio-roberta
  ("galvani", "romulo", "g"),        # Rômulo → galvani-romulo-g
  ("degn", "soren", "e"),            # Søren → degn-soren-e
  ("fuster", "jose", "j"),           # José → fuster-jose-j
  ("strom", "lena", ""),             # Ström → strom-lena
  ("westerberg", "lisa", "s"),       # Lisa S. → westerberg-lisa-s
]
```

The frontmatter `authors:` list and the ledger `slug:` field MUST use
identical slugs — the lint resolves `authors:` entries against the
ledger by exact string match. Build the slug list once, use it for
both. Note also: the `name:` display field should retain the original
diacritics (`Søren Egedal Degn`) for human readability — only the slug
is ASCII-folded. If a pre-existing ledger entry for the same author
uses the diacritic-retaining slug form (e.g. `degn-søren-e`), match
that form rather than forcing ASCII — but the vault convention is
ASCII-folded slugs, so pre-existing diacritic slugs are rare.

Observed 2026-08-02 (He 2026): 21 authors, 5 with diacritics
(Rômulo, Søren, José, Ström, and the apostrophe in D'Aulerio). The
naïve slugifier produced broken slugs (`r-mulo`, `s-ren`); hand-built
slugs with ASCII folding matched the frontmatter and resolved cleanly.
```

## Patch 2026-08-02: yaml.dump ledger-rewrite pitfall, task-specified wrong-author slug, ORCID-null default

### Add to the concurrency-hazard section (yaml.dump whole-file rewrite during ledger merge)

**Never use `yaml.dump()` to rewrite the entire `people/_ledger.yaml` file
during a duplicate-entry merge.** When a same-slug or different-slug duplicate
is found and needs merging, `yaml.dump` reformats every entry in the file —
reordering keys, collapsing or expanding multiline strings, changing
indentation — producing a massive diff that touches 3,000+ unrelated entries
and risks clobbering concurrent sibling edits. The file will parse correctly
afterwards, but the collateral reformatting makes the git diff unreadable and
can interfere with siblings that are mid-edit.

**The fix:** use `patch` (targeted string replacement) to merge the specific
entries:
1. Append the new citation to the existing entry's `citations:` list via
   `patch` (old_string = the last citation line + the `name:` line;
   new_string = same + new citation line inserted before `name:`).
2. For affiliation union, if the existing entry is missing affiliations the
   duplicate has, `patch` the affiliations block to add them.
3. Delete the duplicate entry's block via `patch` (old_string = the entire
   `- slug: <dup-slug>` through the last field of that entry; new_string =
   empty string).

If a script-based merge is genuinely unavoidable (e.g., the duplicate block
is hard to isolate by string match), a script that reads, merges in memory,
and writes back is acceptable — but ONLY if no siblings are concurrently
editing the file. In a parallel `ingest-pending-papers` context, always
prefer `patch`.

Observed 2026-08-02 (Pae 2020): merged a same-slug `meyer-hermann-michael`
duplicate (sibling had ORCID + Tas 2016 citation; this session had no ORCID
+ Sander 2020 citation). The `yaml.dump` rewrite reformatted the entire
26,000-line file. The merge was semantically correct but the diff was
enormous. Lesson: use `patch` for the merge next time.

### Add to Phase 1 (task-specified wrong first-author name)

**A parent task (literature-dive, idea-ingest) may specify the wrong
first-author name** — e.g., "Sander et al." when the PMID resolves to "Pae
et al." (no author named Sander appears on the paper). This happens when the
task was created from a secondary citation, a misremembered authorship, or a
conflation with a companion paper. The PMID/DOI is authoritative for
authorship, just as it is for the DOI itself (2026-07-17 patch). Always
verify the first-author name against the PubMed XML `<AuthorList>` (first
`<Author>` element's `<LastName>`/`<ForeName>`). If the task-specified name
disagrees with PubMed:
- Use the PubMed authorship in the frontmatter `authors:` list and in all
  ledger entries (the correct author slugs).
- File at the task-specified slug per the literature-dive instruction (the
  slug is a task spec, per 2026-07-24 patch), but record the correct
  authorship in the page body and Ingest log.
- Flag the discrepancy prominently in the Ingest log with a dedicated
  subsection so a future normalization pass can rename the file and update
  inbound links.

Observed 2026-08-02 (Pae 2020): task said "Sander et al., JEM 2020, PMID
33332554" but PMID 33332554 resolved to Pae et al. (first author Juhee Pae,
senior author Gabriel D. Victora, 13 authors, no "Sander"). Filed at
`papers/sander-2020-cyclin-d3-inertial-cycling-dz` per task spec;
frontmatter `authors:` led by `people/pae-juhee`; ledger entries use
correct author slugs.

### Add to Phase 8 (ORCID-null when both PubMed and Europe PMC lack ORCIDs)

**When both PubMed XML and Europe PMC core search lack ORCIDs for a paper's
authors, set `orcid: null` for all new ledger entries.** Do not fabricate
ORCIDs from memory or external searches — the ledger's `orcid` field is the
disambiguation key, and an incorrect ORCID is worse than a null one. The
two-line ORCID capture path is:
1. PubMed XML `<Identifier Source="ORCID">` — first line.
2. Europe PMC REST core search — second line:
   `curl -s "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=<PMID>&resultType=core&format=json"`
   Parse `resultList.result[0].authorList.author[].orcid`.
When both return empty, `orcid: null` is the correct value. Do not spend
additional tool calls searching for ORCIDs beyond these two sources.

Observed 2026-08-02 (Pae 2020): neither PubMed XML nor Europe PMC core
search returned ORCIDs for any of the 13 authors. All 11 new entries set
`orcid: null`.

### Companion references that should absorb these patches

- `paper-ingest-fallback-patterns/SKILL.md` — add the yaml.dump
  whole-file rewrite pitfall alongside the existing ledger-duplicate
  hazards (§3 same-slug, §8 different-slug). The yaml.dump pitfall is the
  merge-method hazard; the existing §3/§8 cover the detection-and-merge
  logic.
- `paper-ingest-pubmed-resolver-v2/SKILL.md` — add the Europe PMC REST
  core search ORCID endpoint, the null-when-both-lack default, and the
  E-utilities rate-limit retry note. Also create the missing
  `scripts/pmc_xml_body_parser.py` referenced in §4.
- `paper-ingest-doi-pmid-crosscheck/SKILL.md` — add the authorship
  cross-check (task-specified first-author name vs PubMed `<AuthorList>`).

## Patch 2026-08-05: Wayback Machine full-text retrieval for Cloudflare-blocked publisher pages

### Add to Phase 4 (full-text decision tree, after the Nature.com branch)

```markdown
**The Wayback Machine is a reliable full-text source for Cloudflare-blocked
publisher pages.** When a paywalled article's publisher page (e.g.,
Annual Reviews, Elsevier/ScienceDirect) blocks both `curl` and
`browser_navigate` with Cloudflare bot detection, and no PMC open-access
copy exists, the Internet Archive Wayback Machine
(`https://web.archive.org/web/*/<publisher-url>`) may have a cached
snapshot that renders the full article body as static HTML — bypassing
the Cloudflare gate because the snapshot was crawled earlier and served
from the archive's infrastructure.

**Procedure:**
1. Construct the publisher URL from the DOI (e.g.,
   `https://www.annualreviews.org/content/journals/10.1146/annurev-virology-092818-015550`).
2. Query the Wayback Machine API for the closest snapshot:
   `curl -s "https://archive.org/wayback/available?url=<publisher-url>"` —
   returns JSON with the `closest` snapshot timestamp and URL.
3. `browser_navigate` to the snapshot URL (or `curl` the snapshot HTML if
   the browser is unnecessary). The snapshot renders the article body as
   static HTML — no JavaScript hydration, no Cloudflare challenge.
4. Extract the article text from the HTML. For Annual Reviews, the body
   text is in `<div class="html_fulltext">` (may be hidden via CSS but
   present in the source HTML). Parse with regex or `browser_console`:
   `document.querySelector('.html_fulltext').innerText.substring(0, 50000)`.
5. The reference list may be present in the HTML or may need to be
   obtained separately via the Europe PMC REST references endpoint:
   `curl -s "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:<doi>&resultType=core&format=json"`
   → `resultList.result[0].referenceList`.

This is a fallback path — try PMC OA and the publisher page first. The
Wayback Machine snapshot may be stale (missing recent corrections) or
may not have captured the full article if the publisher served content
dynamically at crawl time. But for Cloudflare-blocked paywalled
articles with no OA copy, it is often the only viable full-text source.

Observed 2026-08-05 (Greber & Flatt 2019, Annu Rev Virol): Annual
Reviews page blocked to both `curl` (Cloudflare 403) and
`browser_navigate` (Cloudflare challenge page). No PMCID, no PMC OA
copy, no Europe PMC PDF. Wayback Machine snapshot
(20221017074513) of the annualreviews.org article page delivered 990 KB
HTML with 142K chars of article body covering all sections. Reference
list (153 entries) obtained from Europe PMC REST references endpoint.
Full distillation completed from this text.
```

### Companion references that should absorb this patch

- `paper-ingest-full-text-access/SKILL.md` — add the Wayback Machine
  branch to the full-text decision tree, after the Nature.com branch
  and before the abstract-only fallback.
- `paper-ingest-browser-fulltext/SKILL.md` — note the Wayback Machine
  as a browser-free HTML extraction path (the snapshot HTML can be
  fetched via `curl` and parsed with regex, no `browser_navigate`
  needed).

## Patch 2026-08-03: Enqueue a rem-cycle propagation packet after every page write

### Add as the final phase (after the page write, with the commit step)

```markdown
N. **Enqueue propagation.** Append an item to `docs/rem-cycle/inbox.yaml`:

   ```yaml
   - id: <YYYY-MM-DD>-<slug>
     page: papers/<slug>
     event: ingest            # or: stub-filled, when filling an existing stub
     date: YYYY-MM-DD
     consumed_by: []
   ```

   This is how the dream learns the page exists without waiting for a cursor —
   the rem-retro and rem-reinforce jobs drain the inbox first each night.
   Dedup on `id`: if the exact id is already present, skip. The append is a
   plain YAML list append under `items:` — never rewrite the whole file
   (sibling ingest subagents append concurrently; a full-file rewrite wipes
   their entries — the same hazard class as the ledger resets above).
```

## Patch 2026-08-05b: Reader-proxy (jina) full-text branch, bioRxiv version discipline — FOLDED into companions

Born from a full-text-reliability brainstorm + live verification on
2026-08-05 (the bioRxiv/Cloudflare pain point). **These changes are already
folded into the companions** — this entry is the audit trail.

### Folded into `paper-ingest-full-text-access/SKILL.md`

- **New branch 1c** — bioRxiv preprint full text (pointer to the
  `paper-ingest-biorxiv-preprint-fulltext` companion).
- **New branch 1d — reader proxy (r.jina.ai) for Cloudflare-blocked
  domains.** Verified live 2026-08-05: `curl -sL
  "https://r.jina.ai/https://www.biorxiv.org/content/<doi>v<N>.full"`
  returned 132K chars of clean markdown (Introduction, all Results
  subsections, Discussion, 53 references, figure captions) for the Wang
  2026 Cell preprint (10.1101/2025.10.27.684659) — a page that 429s
  direct `curl` (.full, .full.pdf, .source.xml all Cloudflare error 1015).
  Single terminal call, no browser, no API key at the free tier.
  Limitations recorded in the branch: rate limits (~20 req/min free),
  markdown not XML, defeats bot-detection but NOT true paywalls, no figure
  images.
- **New branch 2b — Wayback Machine** (the 2026-08-05 patch above, folded:
  extended to bioRxiv `.full`/`.full.pdf` snapshots, added availability-API
  429 backoff guidance, positioned as fallback AFTER 1d).
- **Known-blocks table:** added Cell Press (cell.com); added a note that
  branch 1d is worth one attempt before Abstract-only for any tabled
  domain.

### Folded into `paper-ingest-biorxiv-preprint-fulltext/SKILL.md`

- **Step 0 — version check via api.biorxiv.org.** The API host is NOT
  Cloudflare-blocked (HTTP 200 verified 2026-08-05) and returns latest
  `version`, submission `date`, `jatsxml` URL, and publication status.
  Always distill the latest version; record it in the Ingest log.
- **Retrieval order changed:** jina reader proxy FIRST (single curl) →
  browser click-through fallback → Wayback second fallback. The
  browser-only technique from 2026-08-02 is now the fallback, not the
  primary path.

### Negative results from the same verification pass (do not re-try blindly)

- Europe PMC PPR route: metadata-only for the Wang preprint (inEPMC: N,
  hasPDF: N) — not a general bioRxiv full-text backdoor for recent
  preprints.
- Semantic Scholar `openAccessPdf`: empty for the same preprint.
- OpenAlex: does not index the preprint DOI (404) — aggregators lag fresh
  preprints; they remain useful for published papers.

### What was deliberately NOT built (deferred, awaiting Bryan's call)

- `scripts/fetch_fulltext.py` — an executable ladder walking the whole
  decision tree with retries/backoff and a provenance tag.
- A structured `fulltext_source:` frontmatter field for papers.
- An embargo re-check sweep (monthly cronjob re-running the branch-0 gate
  on `needs-enrichment: true` pages).
- Figure-image retrieval (PMC OA bundles, vision-assisted distillation).

## Patch 2026-08-05c: Tier-1 build-out — ladder script, fulltext_source field, embargo sweep, figure retrieval

Bryan approved Tiers 1 + light Tier 2 same-day. Everything below is BUILT
and verified — this entry is the audit trail.

### Built: `skills/paper-ingest/scripts/fetch_fulltext.py`

Executable form of the full-text decision tree. Stdlib-only (+ pymupdf for
the EPMC PDF branch). Walks: Europe PMC gate → PMC XML → EPMC PDF render →
bioRxiv (api version check + jina) → publisher jina → Wayback, with
retry/backoff. Prints JSON: `provenance` (the `fulltext_source` tag),
`chars`, `text_file`, `figures_dir`, `notes`. Verified 2026-08-05 against
three historical cases:
- Wang 2026 preprint (doi 10.1101/2025.10.27.684659) → `biorxiv-jina`,
  131,765 chars.
- Frasca 2020 (PMC7371527) → `pmc-xml`, 41,311 chars.
- Kwon 2016 (PMC4907239) → `epmc-pdf`, 63,890 chars. NOTE: the gate now
  shows `isOpenAccess: Y` for Kwon — the embargo LIFTED between 2026-08-01
  and 2026-08-05. Direct evidence for the embargo sweep below.

Also created `scripts/pmc_xml_body_parser.py` (the missing script
referenced by `paper-ingest-pubmed-resolver-v2` §4 — reuses the parser in
fetch_fulltext.py).

### Built: `fulltext_source:` frontmatter field (Tier 1E)

Documented in `skills/conventions/frontmatter.md` (paper queue/provenance
table, alongside a newly-documented `needs-enrichment` row). Tags:
`pmc-xml` | `epmc-pdf` | `biorxiv-jina` | `biorxiv-browser` |
`publisher-jina` | `nature-browser` | `wayback` | `provided-pdf` |
`abstract-only`. The linter has no page-field whitelist, so no lint change
was needed. paper-ingest Phase 4 should copy the script's `provenance`
into the page.

### Built: embargo re-check sweep (Tier 1F)

`skills/paper-ingest/scripts/embargo_recheck.py` — monthly cron
(`embargo-recheck`, `0 6 1 * *`, no_agent, deliver=local) over every
`needs-enrichment: true` paper. Reports `new-pmcid` (deposit landed after
ingest) and `oa-flipped` (embargo lifted). Silent when nothing flips.
First live run 2026-08-05 found 4 of 112: bond-2024 (oa-flipped,
PMC11481455), kanekiyo-2013 (new-pmcid, PMC8312026), lewis-2024
(oa-flipped, PMC11680396), morianos-2020 (new-pmcid, PMC7275751) — all
queued for re-enrichment.

### Built: figure retrieval (light Tier 2G)

`fetch_fulltext.py --figures` scrapes the PMC article page for
`cdn.ncbi.nlm.nih.gov/pmc/blobs/...` figure URLs and downloads them.
Verified: Leem 2022 (PMC9278498) → 6 figure JPEGs (fx1 + gr1–5).
Negative results folded into the full-text-access companion: NCBI's
oa.fcgi bulk host refuses this host (404/550, two packages); Europe PMC's
image backend dies with HTTP/2 stream errors. Storage default: EPHEMERAL
(/tmp) — figures are distillation-time working material; a permanent
vault figure archive is a deferred design question. `vision_analyze` can
read fetched figures into Findings.

### Deferred: Paperpile MCP as the upstream source

Bryan's call 2026-08-05: when a Paperpile MCP exists, the FIRST full-text
lookup becomes "search Bryan's Paperpile library by DOI; if present, pull
the PDF from there" — his library is already-licensed full text with
PDFs, better than any scraping ladder. Heavier Tier-2/3 options
(persistent browser profile, FlareSolverr, computer-use against his
desktop Chrome, EZproxy) are deferred until the Paperpile MCP landscape
is known. When it lands, insert it as branch 0b (after the Europe PMC
gate, before PMC XML) in the decision tree AND in fetch_fulltext.py.

## Patch 2026-08-05d: Pre-dispatch identifier validation — `scripts/validate_identifiers.py`

Born from the identifier-wrongness pain point (ebolavirus dive 2026-08-05:
7/10 Tier-1 task contexts carried a wrong PMID, DOI, or both) plus a
three-way landscape sweep (open-source agent systems, MCP ecosystem,
validation-API live tests — findings in
`working-docs/literature-ingestion-hardening-2026-08-05.md`). The script
verifies that candidate identifiers resolve to the intended paper BEFORE
a subagent is dispatched to ingest it.

### Built: `skills/paper-ingest/scripts/validate_identifiers.py`

- **Input:** citation triple (title, first-author surname, year) +
  candidate `pmid`/`doi`/`pmcid`, single-citation flags or `--batch` JSON.
- **Match rule** (GROBID/anystyle-convergent): token_set_ratio ≥ 90 AND
  first-author surname match AND year ±1; REVIEW band 75–89; never title
  alone (corrections/replies/sister papers share titles).
- **Sources:** OpenAlex for DOI (~0.3s, returns canonical PMID/PMCID +
  `is_retracted`; Crossref fallback), PubMed esummary batched (one call
  for all PMIDs), NCBI idconv for PMCID (covers PMC archive only —
  "not found" ≠ invalid), plus PMID↔DOI cross-consistency.
- **Recovery (`--recover`):** Europe PMC exact-phrase TITLE search (best
  free title lookup in live testing; Crossref `query.bibliographic` is
  NOT reliable — it matches reference lists and returns commentaries) →
  PubMed esearch ladder. Acceptance requires the full PASS rule;
  identifiers are REPLACED with the recovered ones.
- **Output:** dispatch-ready JSON — `validated` / `recovered` (corrected
  ids) / `HOLD` (do not dispatch); `retracted: true` surfaced.
- **Live-verified** against the ebolavirus-dive failures (Batra 2018 →
  PMID 30550789; Wang 2016 → 26771495, DOI .044 not .048), good controls,
  a PMCID-only case, and retraction detection (Wakefield 1998).
  ~2s per citation.

### Wired into the dispatching skills (2026-08-05)

- `literature-dive` Phase 3.5: validate the Tier-1 list before presenting
  to Bryan; Phase 4 dispatches from the validator's `dispatch` list, never
  the raw bibliography identifiers.
- `ingest-pending-papers` Phase 2.5: validate the whole stub queue in one
  batch before delegating; `recovered` identifiers patched into the stub
  (frontmatter + `## Citation` + Ingest-log note) before dispatch; `HOLD`
  reported, not dispatched; `retracted: true` surfaced for a human call.

### Phase 7 (bibliography walk) — deferred decision

Phase 7 stub seeds are the upstream source of wrong identifiers, but
validating every seed at walk time adds latency to every walk. Decision
2026-08-05: rely on the drainer's Phase 2.5 validation to catch bad seeds
before they cost a subagent dispatch. If stub-seed wrongness proves common
enough to pollute the queue (watch for clusters of `recovered`/`HOLD` in
drain reports), revisit inline validation at walk time.
