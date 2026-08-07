---
name: literature-dive-patches-2026-08-05b
description: "Use when patching literature-dive. REST API, 429, batching."
triggers:
  - "patch literature-dive skill"
---

# literature-dive — profile-side patches (2026-08-05b)

The authoritative `literature-dive` SKILL.md lives in the vault at
`skills/literature-dive/SKILL.md`. This skill records patches
from the 2026-08-05 enveloped and non-enveloped virus entry mechanisms
dive sessions. The existing `literature-dive-patches` skill carries the
2026-08-04 patches (batching, non-duplicative selection, ledger race);
these 2026-08-05b patches should be appended there or folded into the
vault-side `literature-dive/SKILL.md`.

## Patch 2026-08-05: Entrez Direct CLI not installed — use REST API

### Fix in Phase 1 (Review discovery)

The current SKILL.md's PubMed search template uses `esearch -db pubmed`,
which requires the Entrez Direct CLI tools (`esearch`, `efetch`,
`esummary`). These are **not installed** on this system. The search must
use the PubMed E-utilities REST API via curl instead. Replace the
template with a REST API equivalent:

```bash
# REST API equivalent (always available, no install needed)
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=<URL-encoded-query>&retmode=json&retmax=30" 2>/dev/null | python3 -c "
import sys, json; d = json.load(sys.stdin); print(','.join(d['esearchresult']['idlist']))
"
# Then fetch summaries in a SINGLE batch call (comma-separated IDs):
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=<comma-separated-IDs>&retmode=json" 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
for uid in d['result']['uids']:
    r = d['result'][uid]
    print(f'PMID {uid} | {r.get(\"fulljournalname\",\"\")} | {r.get(\"pubdate\",\"\")}')
    print(f'  {r.get(\"title\",\"\")}')
"
```

### Add to Phase 1 (PubMed rate limiting — 429 handling)

PubMed E-utilities REST API aggressively rate-limits (HTTP 429). When
running multiple sequential `esummary` or `efetch` calls:
- **Batch ID lookups**: pass comma-separated IDs in a single `esummary`
  call rather than one call per ID.
- **Sleep between calls**: add `sleep 3-5` between sequential API calls.
  The 2-second sleep from the 2026-08-05 EMFILE patch is sometimes
  insufficient; 429s were observed with 2-3 second sleeps during the
  2026-08-05 entry-mechanisms dive.
- **Fallback to Semantic Scholar**: when PubMed 429s repeatedly, use
  `api.semanticscholar.org/graph/v1/paper/search?query=<query>&fields=title,externalIds,year`
  for review discovery. Note that Semantic Scholar also rate-limits
  (429) under load — if both are blocked, wait 10-15 seconds before
  retrying.
- **Do NOT loop on 429**: if three consecutive calls fail with 429,
  stop and wait 15+ seconds. The tool loop warning fires after 3
  failures on the same command.

## Patch 2026-08-05: Multi-batch delegation is the standard for large dives

### Add to Phase 4 (Tier 1 ingest)

For dives with >6 Tier 1 papers, the standard pattern observed across two
successful dives (enveloped entry mechanisms: 12 papers in 4 batches;
non-enveloped entry: 6 reviews in 2 batches) is:

1. Dispatch the first batch of 3 subagents.
2. While they run, continue orchestrator work in the foreground:
   build the virus/topic list, search for additional papers, draft
   the concept page skeleton.
3. When the batch returns, verify files on disk, then dispatch the
   next batch.
4. Repeat until all papers are dispatched.
5. After the last batch returns, do a bulk read-back verification
   (Python script checking all files at once — frontmatter parses,
   DOIs present, authors populated, body sections present).

This overlaps orchestrator thinking time with subagent execution time.
The orchestrator is never idle — there is always foreground work
(taxonomy, virus lists, concept page drafting) that does not depend
on the subagent results.

**The 3-paper batch is the dispatch unit.** Do not attempt to dispatch
more than 3 in a single `delegate_task` call (rejected by the runtime).
For overflow, dispatch a separate single-task call — it queues and
runs when a slot frees.

## Patch 2026-08-05: Auto-snapshotter can beat your explicit commit

### Add to Phase 7 (Commit before synthesising)

The auto-snapshotter (`auto_push.sh`, every 5 min) can commit your
subagent-written paper pages under a generic `auto: snapshot` message
**before** you get to your explicit `git commit`. This is not a failure
— the files are still committed and pushed — but the descriptive commit
message is lost, replaced by the generic snapshot message. Observed
2026-08-05: 28 paper files from the enveloped entry dive were committed
by the auto-snapshotter as `auto: snapshot — <instance>/ (28)` before the
orchestrator's explicit commit.

**Mitigation:** Commit immediately after each batch returns and is
verified, rather than waiting until all batches are done. The window
between batch completion and commit should be minutes, not the 10+
minutes it takes to write a concept page. If the auto-snapshotter
beats you, the descriptive message is lost but the content is preserved
— do not re-commit or amend (that rewrites history).

## Patch 2026-08-05: Existing brain content should seed the virus/topic list

### Add to Phase 4 (as a foreground task during subagent execution)

While Tier 1 subagents are ingesting, the orchestrator should build the
comprehensive virus/topic list in the foreground. This list is the data
structure the concept page synthesis is built on. The pattern observed
in both entry-mechanisms dives:

1. Read the existing related concept pages (e.g. `viral-glycoproteins-
   enveloped-viruses` for the enveloped dive, `non-enveloped-virus-
   surface-domains` for the non-enveloped dive) to identify what the
   brain already knows.
2. Use the spine review's framework (e.g. Helenius 2018's 7-step entry
   program, Breach 2018's 4-step penetration paradigm) as the organizing
   structure.
3. Compile a working document at `working-docs/<topic>-virus-list.md`
   listing every human-infecting virus family, its entry mechanism,
   receptor(s), endocytic route, penetration trigger, and penetration
   location.
4. Assign each virus family to an entry class based on the literature.
5. This working doc is NOT a brain page (no frontmatter) — it is a
   transitory document that informs the concept page synthesis. The
   concept page is the durable artifact.

This foreground work does not depend on the subagent results and can
proceed in parallel with the ingest batches.

## Companion vault-side skills that should absorb these patches

- `literature-dive/SKILL.md` — Phase 1 REST API search template,
  Phase 1 429 rate-limit handling, Phase 4 multi-batch delegation pattern,
  Phase 7 auto-snapshotter commit race, Phase 4 foreground virus-list
  compilation.
- The existing `literature-dive-patches` skill carries the 2026-08-04
  patches (batching, non-duplicative selection, ledger race). These
  2026-08-05b patches should be appended there or folded into the
  vault-side `literature-dive/SKILL.md`.
