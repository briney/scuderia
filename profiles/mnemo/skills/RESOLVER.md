# Skill resolver

This is the dispatcher. It maps an incoming request to the skill that handles
it. Skills are the implementation — **read the skill file before acting.** If two
skills could match, read both; skills are designed to chain.

A skill *references* the character (`SOUL.md`, `STYLE.md`); it never restates it.
Cross-cutting rules live in `skills/conventions/`.

**Path resolution.** References of the form `skills/…` are
profile-root-relative: they resolve in the soma checkout
(`profiles/mnemo/skills/…`) and through the harness skills binding (on
Hermes, the category symlink under `~/.hermes/profiles/<instance>/skills/`).
Brain paths (`papers/`, `docs/rem-cycle/`, `USER/<name>.md`, …) resolve from the
brain root — the session cwd.

## The shape of the skill set

The mind is one mind doing three jobs (`VISION.md` §2, `DESIGN.md` §4.2). The job
skills are grouped into three clusters below. Underneath them sits the
**brain-building and upkeep** work that fills and tends the knowledge graph, and
a small **meta** group. Two skills are **always-on** — they run on every turn,
not in response to a trigger.

## Always-on

| When | Skill |
|---|---|
| Every brain read, write, lookup, or citation | `skills/brain-ops/SKILL.md` |
| Every inbound message — capture your human's thinking and entity mentions (spawn in parallel, never block) | `skills/signal-detector/SKILL.md` |

## Thought-partner cluster

Running a brainstorm is the *character* operating, not a skill — it has no single
trigger (`VISION.md` §2.5). These skills are what the thought partner reaches for
mid-conversation: grounding a claim, checking the literature, sharpening a map.

| Trigger | Skill |
|---|---|
| "What do we know about", "tell me about", "background on", a graph/relationship question | `skills/query/SKILL.md` |
| "Verify this claim", "is this study real", "check this paper", "trace this to source" | `skills/academic-verify/SKILL.md` |
| "What's new about", "current state of", "what changed", literature scan | `skills/literature-research/SKILL.md` |
| "Synthesize my concepts", "find patterns across my notes", "build my intellectual map", "trace how this idea evolved" | `skills/concept-synthesis/SKILL.md` |
| "Synthesize what we know about", "build a concept page on", "what does the brain say about", "consolidate the papers on" | `skills/topic-synthesis/SKILL.md` |
| "Deep literature dive", "comprehensive literature review of", review-anchored deep exploration with synthesis | `skills/literature-dive/SKILL.md` |

## Grant-writing cluster

The output side of grant work (`VISION.md` §2.2): producing a new application,
multi-section and multi-week. These skills additionally load `STYLE.md` and
hold the whole application in view; cite-or-flag is non-negotiable. They draft
into one `grant` page and chain heavily — read each skill's phases.

| Trigger | Skill |
|---|---|
| "Start / plan a grant", "let's write an R01", a NOFO dropped with intent to apply | `skills/grant-plan/SKILL.md` |
| "Draft / revise a section" — Specific Aims, Significance, Innovation, Approach, a resubmission Introduction | `skills/grant-section/SKILL.md` |
| "Check the grant", "review the whole application", the pre-submission coherence gate | `skills/grant-coherence/SKILL.md` |
| "Fix the citations", "build the bibliography", resolve needs-citation flags | `skills/grant-citations/SKILL.md` |
| "I submitted the grant", post-submission close-out and graph propagation | `skills/grant-finalize/SKILL.md` |

Format references for R01 and R21 live in `skills/grant-formats/` — not skills
(no trigger); the cluster consults them. `grant-ingest` (brain-building, below)
is the *input* side — it builds the `## Verbatim` corpus this cluster learns
your human's voice from.

## Research-logistics cluster

The attention contract (`VISION.md` §5, `DESIGN.md` §4.5): surface what matters,
silence what does not, escalate with stakes.

| Trigger | Skill |
|---|---|
| Daily briefing, "what's happening today", deadline status | `skills/briefing/SKILL.md` |
| Weekly synthesis digest — the PUSH: precipitated hypotheses + concept `## Shifts` + QUEUE triage, archived to `docs/rem-cycle/briefings/` ("weekly synthesis briefing", "what precipitated this week"); the weekly *intellectual* digest, distinct from the daily *attention* `briefing` | `skills/synthesis-briefing/SKILL.md` |
| Standing publication sweep — recent papers across the research program's interests | `skills/literature-sweep/SKILL.md` |
| Standing change-detection watch — "monitor / watch for / notify me when X happens"; maintains `MONITORS.md` and sweeps structured open-API sources daily for a significant new hit | `skills/monitor-the-situation/SKILL.md` |
| Morning prep, meeting context, planning the day | `skills/daily-task-prep/SKILL.md` |
| Task add / complete / defer / review | `skills/daily-task-manager/SKILL.md` |
| "Remind me to", "remind me at", "set a reminder" — lightweight time-based nudge (not a research task); creates a cron job + logs to `working-docs/reminders-log.md` | `skills/remind/SKILL.md` |

## Brain-building and upkeep

Filling the knowledge graph, and keeping it healthy.

| Trigger | Skill |
|---|---|
| Generic "ingest this" — auto-routes to a specialist below | `skills/ingest/SKILL.md` |
| A scientific paper — peer-reviewed or preprint, any format | `skills/paper-ingest/SKILL.md` |
| A grant — an application package, summary statement, or reviewer critiques | `skills/grant-ingest/SKILL.md` |
| Drain the paper-ingest queue — fill in stub papers that grant-ingest (or other producers) flagged with `needs-ingest: true` | `skills/ingest-pending-papers/SKILL.md` |
| A shared link, article, or idea | `skills/idea-ingest/SKILL.md` |
| A video, podcast, book, repo, or non-paper PDF | `skills/media-ingest/SKILL.md` |
| A meeting transcript | `skills/meeting-ingestion/SKILL.md` |
| "Pull meetings from Granola", "sync Granola meetings", cron-driven daily meeting sync | `skills/granola-meeting-sync/SKILL.md` |
| A voice memo | `skills/voice-note-ingest/SKILL.md` |
| Capture a discussion — "capture this convo", "record what we just discussed", "save this discussion" | `skills/conversation-capture/SKILL.md` |
| Create or update a person / institution page | `skills/enrich/SKILL.md` |
| Restructure a raw-text or stub page into a useful one | `skills/restructure-thin-page/SKILL.md` |
| Draw a relationship or process as a diagram — "make a diagram", "flowchart", "visualize the pipeline" (renders as a Mermaid block in Obsidian; sidecar to the page-authoring skills, never standalone) | `skills/mermaid-diagrams/SKILL.md` |
| Deep semantic re-linking — re-read pages against the current graph and add forward edges that weren't possible at ingest ("link this page", "re-link the brain") | `skills/retroactive-linking/SKILL.md` |
| Bootstrap the concept layer — one-time backward distillation of umbrella concepts from the existing projects/grants/papers ("seed the concept layer", "distill concepts from the grants") — distinct from `concept-synthesis` (which dedups/tiers/maps ambient idea-stubs) | `skills/concept-seeding/SKILL.md` |
| Update concepts from recent papers — the autonomous reinforce pass that appends **facts-only** `## Shifts` evidence entries (what a source showed, cited; no opinion) ("reinforce the concepts", "what recent papers moved our concepts"); runs as rem-cycle phase 6 or standalone. The directed lane (an explicit concept call-out at ingest) lives in `paper-ingest` | `skills/reinforce/SKILL.md` |
| Single highest-value attention target — the daily intersect pass; scans the whole brain and surfaces ONE cross-cutting thing (a hypothesis to consider, a grant idea, a dive-trigger) into the dream report's "One thing" section, labeled opinion, never a page ("find concept intersections", "what's the one thing I should look at", "surface the highest-value idea"); rem-cycle phase 8 or standalone | `skills/intersect/SKILL.md` |
| Concept-stub coalescence — the weekly pass that reads `is_concept_stub: true` notes and (≥3 independent signals + "so what") auto-aggregates a cluster into a `concept` page — facts only, never a hypothesis ("coalesce the concepts", "which stubs should become concepts"); rem-cycle phase 5c or standalone. Distinct from `intersect` (below) | `skills/concept-coalesce/SKILL.md` |
| Shard a large list across `delegate_task` batches — the dispatch/yield/verify loop any multi-batch campaign shares (enrichment sweeps, deep dives, corpus backfills, rem-cycle phases); loaded alongside the consuming skill's domain-specific phase | `skills/batch-drain/SKILL.md` |
| Scheduled offline consolidation — "run a rem cycle", "dream", the nightly/weekly maintenance job that runs phases as subagents and writes a dream report | `skills/rem-cycle/SKILL.md` |
| Duplicate/merge/split of the identity-keyed kinds + the author ledger — "find duplicate pages", "dedupe the brain", "audit the author ledger", "are these two the same" | `skills/entity-resolution/SKILL.md` |
| Contradictions + expired facts — "find contradictions", "check consistency", "conflicting claims", "stale facts", "audit the hypothesis graph" | `skills/consistency-check/SKILL.md` |

### Reference-corpus cluster

Skills that build and enrich the durable non-graph corpora under
`references/` (see `references/README.md` in the brain). Corpus builders own
the curated fields; enrichment skills each own exactly one machine-generated
block and rewrite it wholesale.

| Trigger | Skill |
|---|---|
| "Build / extend the therapeutic antibody registry", "antibody molecule database", Tier A–D sweep of `references/therapeutic-antibodies/` | `skills/therapeutic-antibody-registry/SKILL.md` |
| "Get sequences for <antibody>", "enrich sequences", "refresh the sequence block" — VH/VL from the Thera-SAbDab mirror into the machine-owned `## Sequences` block | `skills/antibody-sequence-search/SKILL.md` |
| "Get structures for <antibody>", "enrich structures", "compute the epitope contacts" — SAbDab mirror + sequence-similarity search + computed contacts into the machine-owned `## Structures` block | `skills/structure-search/SKILL.md` |
| "Patent search for <antibody>", "enrich patents", "what's the IP situation" — Google Patents XHR + pataa BLAST into the machine-owned `## IP & exclusivity` block (US-only; estimated expiries always labeled) | `skills/patent-search/SKILL.md` |
| "Build the antibody target hit-list", "rank viruses/targets for mAb discovery" | `skills/target-hitlist/SKILL.md` |
| "Profile this target" — deep per-target profile at key-paper-ingestion level | `skills/target-profiling/SKILL.md` |

### Audit cluster

Three skills share the "audit the brain" job, separated by *scope*:

- **`frontmatter-guard`** — *structural*. Frontmatter shape: required
  fields, kind ↔ directory, slug form (mechanical lint runs in CI;
  this skill is the LLM-pass companion for per-kind judgment, including
  the load-bearing surname-first **slug-form audit** for `people/`).
- **`citation-fixer`** — *cited-claim health*. Every substantive claim
  carries a verifiable source or an honest `[needs-citation]` flag;
  this skill enforces the `SOUL.md` §2 spine across the brain.
- **`maintain`** — *broad health*. Orphans, stale pages, missing
  back-edges, importance-score recompute. The general sweep; chains
  into the two narrower skills when their bug class surfaces.

Run one when the problem class is known; run `maintain` when the
question is "is the brain healthy?"

**Linking depth.** `maintain`'s *missing-forward-links* dimension is the
cheap, inline pass — a verbatim, unlinked mention on a page it happens to
read. `retroactive-linking` (brain-building, above) is the deep,
cursor-driven pass that *generates* non-verbatim candidates (semantic
neighbours, shared-neighbour pairs, co-citation) and rotates over the whole
corpus. `maintain` chains into it for the deep pass, as it chains into the
two audit skills.

| Trigger | Skill |
|---|---|
| Brain health check, orphans, stale pages, link/citation audit | `skills/maintain/SKILL.md` |
| "Validate frontmatter", "fix frontmatter", "brain lint", "audit people slug shapes" | `skills/frontmatter-guard/SKILL.md` |
| "Citation audit", "fix citations" | `skills/citation-fixer/SKILL.md` |

## Meta

| Trigger | Skill |
|---|---|
| "Create a skill", "improve this skill" | `skills/skill-creator/SKILL.md` |
| Present options, gate on a user decision | `skills/ask-user/SKILL.md` |
| "Migrate from Obsidian / Notion / Logseq", import an existing vault | `skills/migrate/SKILL.md` |
| "Run user-model-reflect", "reflect on what I've been working on", "update the observations sidecar" — append a dated block of candidate observations about how your human is working to `USER/OBSERVATIONS.md`. Manual invocation only; no schedule wired. | `skills/user-model-reflect/SKILL.md` |
| "Measure my writing voice", "build a voice profile", "update VOICE.md" — extract the writing fingerprint (sentence length, tell-frequency) from the `## Verbatim` corpus into `USER/VOICE.md`, then run a blind validation check. Manual invocation only; no schedule wired. | `skills/user-voice-measure/SKILL.md` |

## Identity and context

| When | Read |
|---|---|
| Who the mind is — voice, posture, the inviolable spine | `SOUL.md` (auto-loaded) |
| How the mind writes for external readers (grants, papers) | `STYLE.md` — grant-writing work only |
| The state of the research program — active domains, threads, funding, pipeline | `RESEARCH.md` — read explicitly; not auto-loaded |
| How a request maps to a skill, the vault layout | `AGENTS.md` |

## Conventions — cross-cutting, apply to every brain-writing skill

- `skills/conventions/page-kinds.md` — the page kinds and their directories
- `skills/conventions/frontmatter.md` — the YAML schema
- `skills/conventions/graph-and-links.md` — wikilinks, typed links, derived backlinks
- `skills/conventions/importance-scoring.md` — the `[0, 1]` research-salience score
- `skills/conventions/raw-source-archive.md` — the `_drop/` → R2 pipeline and git pointers
- `skills/conventions/brain-first.md` — check the brain before going external
- `skills/conventions/quality.md` — citations, forward-only linking, the notability gate
- `skills/conventions/author-ledger.md` — `people/_ledger.yaml`; paper-author page creation is threshold-gated, not judgment-gated
- `skills/conventions/rem-cycle-contract.md` — the rem-cycle phase interface: structured phase result, the two commit tiers, run mode, protected classes
- `skills/conventions/test-before-bulk.md` — never batch without testing one first
- `skills/conventions/skill-hygiene.md` — the eval contract, the no-regression law, the scheduled-run gate; governs every edit to a skill
- `skills/conventions/concept-stub-capture.md` — capture-cheap/decide-later: file transient ideas as `is_concept_stub: true` notes, defer the concept/hypothesis judgment to `concept-coalesce`
- `skills/_brain-filing-rules.md` — where a new page goes
- `skills/_output-rules.md` — output quality standards

## Disambiguation

When multiple skills could match:

1. Prefer the most specific skill (`meeting-ingestion` over `ingest`).
2. For a shared URL, route by content type (scientific paper → `paper-ingest`,
   article → `idea-ingest`, video → `media-ingest`). A paper routes to
   `paper-ingest` whatever form it arrives in — PDF, DOI, or link.
3. When a request is genuinely ambiguous and the wrong choice is expensive, gate
   on the user — see `skills/ask-user/SKILL.md`.
4. Chaining is explicit in each skill's phases (e.g. an ingest skill chains into
   `enrich` for each entity it surfaces).
5. `literature-research` answers a *named* topic ("what's new about X");
   `literature-sweep` runs the standing, untargeted scan over the whole research
   program and is what `briefing` invokes. Topic given → `literature-research`;
   no topic, daily scan → `literature-sweep`. `literature-dive` is a deeper
   campaign than either — it starts from a review, ingests foundational primary
   literature in tiers, searches for what the review missed, and synthesizes
   a concept page. "What's new" → `literature-research`; "comprehensive deep
   dive with synthesis" → `literature-dive`.
6. `paper-ingest` is per-paper (one DOI, one PDF, one link); `ingest-pending-papers`
   is the queue drainer that runs many `paper-ingest` invocations in
   succession against pre-created stubs. One paper to ingest → `paper-ingest`;
   "process the stubs grant-ingest left behind" → `ingest-pending-papers`.
7. **The four "what does the brain know about X" skills.** They differ on
   *source*, *output*, and *durability*:
   - `query` — answers conversationally from the brain, files nothing.
     Use for a one-shot question that needs an answer right now.
   - `literature-research` — scans for *new* external literature on the
     topic; files a `note` with the delta against what the brain holds.
     Use when the question is "what's new about X."
   - `concept-synthesis` — dedupes and tiers your human's *own* `concept` and
     `note` stubs over time. Operates on his intellectual history, not on
     the literature. Use for "synthesize my concepts," "find patterns
     across my notes."
   - `topic-synthesis` — consolidates many `paper` pages into one
     durable `concept` or `hypothesis`. Operates on the literature
     already in the brain. Use when the question warrants a permanent
     page, not a conversational answer.
8. `maintain` adds an obvious inline link (a verbatim mention on a page it is
   already reading); `retroactive-linking` runs the systematic, semantic
   re-linking pass over the corpus (non-verbatim candidates, cursor rotation).
   One page's obvious gap → `maintain`; "re-link the brain", or the deep pass,
   → `retroactive-linking`.
9. `maintain` is a single, on-demand health sweep you read the results of now;
   `rem-cycle` is the scheduled orchestrator that *runs* maintenance phases
   (including `maintain` and `retroactive-linking`) as subagents and writes a
   dream report to `docs/rem-cycle/`. "Is the brain healthy right now?" →
   `maintain`; "run the nightly/weekly consolidation", "dream" → `rem-cycle`.
10. `remind` and `daily-task-manager` both create time-based nudges, but split
    by *scope and weight*: `daily-task-manager` creates `task` pages for
    research-program deliverables with deadlines (grant submissions, progress
    reports, paper submissions) that `briefing` tracks. `remind` creates a
    cron job + a log line in `working-docs/reminders-log.md` for lightweight
    operational nudges ("check if Spark is running", "follow up on that email")
    that don't warrant a brain page. Research deadline with a deliverable →
    `daily-task-manager`; "remind me to X at TIME" with no deliverable →
    `remind`. A reminder can be promoted to a task if it turns out to be
    research-program-relevant.
11. `concept-synthesis` and `entity-resolution` both merge duplicates and share
    the merge mechanism (`aliases:`, fold edges), but split by *kind*:
    `concept-synthesis` dedupes `concept` / `note` pages (your human's ideas);
    `entity-resolution` dedupes the identity-keyed kinds (`paper`, `person`,
    `institution`, `method`) and the author ledger, and additionally *splits*
    an entry that fused two people. Duplicate concept → `concept-synthesis`;
    duplicate paper/author/ledger entry → `entity-resolution`.
12. Three "is the brain internally OK?" audits split by defect: `maintain`'s
    stale-pages = a body whose **synthesis lags** new evidence; `citation-fixer`
    = a claim with **no source**; `consistency-check` = a claim that **conflicts**
    with another or has **expired** (contradictions + time-sensitive staleness,
    incl. the hypothesis `supports:`/`refutes:` graph). Out-of-date synthesis →
    `maintain`; missing citation → `citation-fixer`; contradiction / stale fact →
    `consistency-check`.
13. `concept-seeding` and `concept-synthesis` both author `concept` pages but
    differ by job and timing: `concept-seeding` is the **one-time bootstrap** that
    distills umbrella concepts *backward* from the applied corpus
    (`projects/` / `grants/` / `papers/`) into a near-empty layer; `concept-synthesis`
    is the **ongoing** dedup / tier / map over ambient idea-stubs (and is the skill
    `concept-seeding` *calls* for its Phase-5 map refresh). "Seed" / "bootstrap" /
    "distill from the grants" against an empty `concepts/` → `concept-seeding`;
    "synthesize my concepts" / "tier" / "build my map" over existing stubs →
    `concept-synthesis`.
14. The concept-layer skills split by *what they do to a concept*: `concept-seeding`
    **creates** the layer (one-time bootstrap); `concept-synthesis` **curates**
    ambient stubs (dedup / tier / map); `reinforce` **updates** existing concepts'
    `## Shifts` from new papers (appends facts-only evidence entries); `intersect`
    **ranks** — surfaces the single highest-value cross-cutting attention target (as
    labeled opinion, never a page); `topic-synthesis` builds a durable synthesis
    **page** on a named topic. Note that **no autonomous skill creates a
    hypothesis** — hypotheses fall out of conversation with your human only.
    "What recent papers moved our concepts" / "reinforce the concepts" →
    `reinforce`; "what's the one thing I should look at" / "surface the
    highest-value idea" → `intersect`; otherwise per rules 11 and 13.
15. `synthesis-briefing` and `rem-cycle`'s dream report both live under
    `docs/rem-cycle/` and read like "the weekly report", but split by audience: the **dream report**
    (`history/<date>.md`) is *a ten-second glance* — One thing + Done + Flags —
    for confirming the dream ran and spending your attention on the one thing; the
    **synthesis briefing**
    (`briefings/<week>.md`) is *reading-shaped* — the week's precipitated hypotheses
    and concept movements, for your human to act on. "Did the cycle run / what did it do"
    → `rem-cycle`; "what precipitated this week" / "weekly synthesis briefing" →
    `synthesis-briefing`.
16. `conversation-capture` vs. the ambient/atomic captures. `signal-detector`
    captures the *atoms* of thinking (a thesis, an objection, a framing) to
    `notes/` ambiently on every message, no trigger; `conversation-capture`
    captures the deliberate *thread-level* artifact on your human's trigger, as a
    `conversation` page (with a `mode` and often an `about:` anchor) — and links
    the notes `signal-detector` already dropped rather than duplicating them. A
    `note` is first-person thinking filed ambiently; an `interaction` is a
    documented interaction event — meeting / 1:1 / talk / email thread — with
    participants; a `conversation` is a human↔mind
    discussion captured on request. Passing mention / single framing →
    `signal-detector`; considered whole on request → `conversation-capture`.
17. `concept-coalesce` vs. `intersect` vs. `concept-synthesis` — the three
    concept-layer *producers* split by **job, not source**. `concept-coalesce`
    **fact-aggregates** a coalesced concept-stub cluster (`is_concept_stub: true`
    notes, ≥3 independent signals + "so what") into a `concept` page — routine,
    mechanical, facts-only, never a hypothesis. `intersect` **ranks** — the single
    highest-value cross-cutting attention target across the whole brain, surfaced as
    labeled opinion into the report, never a page. `concept-synthesis`
    **dedups/tiers/maps** ambient idea-stubs across the whole corpus. A stub
    cluster pointing at one recurring idea → `concept-coalesce`; "what's the one
    thing I should look at" → `intersect`; organic dedup/tier/map over
    `concept`+`note` stubs → `concept-synthesis`. And note: **no skill creates a
    hypothesis** — hypotheses fall out of conversation with your human only.
