---
name: ingest-pending-papers
description: "Drain the paper-ingest queue — find every paper page with `needs-ingest: true` and fill it in. Orchestrates one `delegate_task` per stub so each paper-ingest runs in an isolated subagent context, by design, so the queue size cannot compact this session and a single bad DOI cannot derail the drain."
triggers:
  - "ingest pending papers"
  - "process the key citations"
  - "fill in the stub paper pages"
  - "drain the paper-ingest queue"
  - a scheduled run (future)
---

# ingest-pending-papers — drain the paper-ingest queue

This skill exists for one reason: to keep `grant-ingest` (and, eventually, the
paper-ingest redesign that walks bibliographies) from running inline paper
ingests. Inline paper ingestion stacks an unbounded number of paper
distillations on top of an already-large parent ingest, and the resulting
context size is the single most reliable trigger for mid-task compaction —
the dominant historical failure mode for the grant-ingest skill.

The split is producer/consumer:

- **Producers** (`grant-ingest`, `paper-ingest` Phase 7) create `paper`
  pages as **stubs** — frontmatter + a citation entry + nothing else.
  `grant-ingest` sets `needs-ingest: true` unconditionally (the grant rule
  — every key citation in a grant is queued). `paper-ingest` defaults
  `needs-ingest` to `false` and flips it to `true` only when the stub's
  `len(cited_by)` first crosses 5 (the threshold gate). Citation edges
  accumulate in the `cited_by` field over time.
- **Consumer** (this skill) reads `papers/` for `needs-ingest: true`,
  chains to `paper-ingest` for each stub via the UPDATE-a-stub path, and
  reports.

Producers and consumer never share a session. The producer writes the queue
and stops; the consumer drains it later, in a fresh context.

> **Conventions:** `conventions/frontmatter.md` (the `needs-ingest`,
> `cited_by`, `ingest_attempts`, `last_ingest_attempt` fields on `paper`),
> `conventions/brain-first.md` (the consumer is brain-first by construction
> — it reads existing pages and updates them),
> `conventions/preprint-retrieval.md` (bioRxiv/medRxiv full text around the Cloudflare block),
> `conventions/capabilities.md` (the harness contract).

## Capabilities

`brain-read` (scan `papers/` for `needs-ingest: true`), `brain-write`
(via delegated `paper-ingest`), `spawn-subagent` (one per stub — the
context-isolation lever this whole producer/consumer split exists for).
Each delegated subagent in turn needs `paper-ingest`'s capabilities.

## What this guarantees

- The set of stubs created upstream (by `grant-ingest` today, by future
  paper-side skills later) gets distilled into full `paper` pages without
  ever burdening the producer's session.
- A single failed ingest does **not** halt the queue. The skill continues
  through the remaining stubs and reports per-paper status at the end.
- Failures are recorded on the failing page (via `paper-ingest`'s
  `## Ingest log` mechanism), so the next run of this skill can read the
  log and skip known-broken DOIs instead of retrying blindly.
- `cited_by` is preserved across every fill — the skill never touches it
  directly; `paper-ingest` is responsible for preservation.

## Why this is its own skill rather than a flag on `paper-ingest`

A single-paper invocation (`paper-ingest`) and a queue-drain invocation are
different jobs with different failure semantics, different reporting
formats, and — eventually — different scheduling profiles. The queue drainer
is a thin orchestrator; `paper-ingest` is the per-paper worker. Conflating
them puts `paper-ingest` in the awkward position of needing to know whether
it was called for one paper or for many.

## Concurrency model — delegate per stub

This skill is an orchestrator. The per-paper work is done in subagents via
the `spawn-subagent` capability — under Hermes that binds to
`delegate_task`; under other harnesses it binds to the harness's equivalent
(`Agent` under Claude Code). One stub per subagent, in batches up to the
user's `delegation.max_concurrent_children` (currently 3). Each subagent
runs `paper-ingest` against a single stub in its own isolated context — so
the queue size has no effect on the orchestrator's context, and no
individual paper-ingest can compact this session.

The phase notes below name `delegate_task` directly because the Hermes
binding's batching semantics (`max_concurrent_children`, the bundle-N-tasks
form) are load-bearing for the orchestrator's tool-call telemetry. Under a
different harness the binding looks different; the *contract* (spawn N
isolated subagents each running paper-ingest) is what the skill depends on.

This is the spine carve-out written into `SOUL.md` §2 ("Ingest with your
own hands"): paper stubs created upstream are already vetted decisions
about what belongs in the brain, so the mechanical fill (DOI resolution,
abstract, body distillation) can be delegated. Stubs created *here* — i.e.
fresh paper-ingest on a source the user just handed over — are still
hand-ingested; that's not this skill's job.

Three things keep the carve-out safe:

- **Per-stub verification.** After each subagent returns, the orchestrator
  re-reads the page and confirms `needs-ingest: false`, the `stub` tag is
  gone, and `cited_by` is preserved. A subagent claiming success without
  the file showing it is a failure, logged as such.
- **Identity is fixed upstream.** The stub already has its citation seed
  and (where known) DOI in `## Citation`. The subagent is not deciding
  what paper this is; it's resolving and filling.
- **No nested delegation.** Subagents are leaves and cannot spawn their
  own workers, by user config.

### Model selection caveat

`delegate_task` does not currently take a model parameter — subagents
inherit the parent's model. So this skill buys *context isolation*, not
*cost reduction*: running the orchestrator under Opus means every
subagent also runs under Opus. That is fine — the win we are after is
compaction avoidance.

If per-task model selection lands in Hermes, **this skill must be
revisited before opting subagents into a smaller model**. The spine
carve-out is currently context-only; extending it to cost requires
explicit guidance about which models are appropriate paper-ingest
delegates, which has not been written yet. Do not assume a smaller model
is safe for paper distillation just because the API supports it.

## Phases

1. **Find the queue.** Use `search_files target=content` against `papers/`
   for `needs-ingest: true`. (Also acceptable: `tags: [stub]` as a
   secondary signal, but `needs-ingest: true` is canonical.) List every
   stub page along with its `title`, `cited_by`, `ingest_attempts`, and
   `last_ingest_attempt`. Order the queue by `len(cited_by)` descending —
   high-edge stubs first, since they have the most evidence of being
   worth the time.

2. **Read each stub's `## Ingest log`.** A stub may have failed previous
   attempts. If the log shows a terminal-looking diagnostic ("DOI
   unresolvable; suggest manual lookup", "paywalled with no PMC and no
   OA"), skip the stub in this run and note it in the final report. The
   user decides whether to manually intervene or to tag the page
   `unresolvable` and remove from the queue. Do *not* silently retry
   what previously failed for a documented terminal reason.

2.5. **Validate stub seed identifiers before delegating.** Stub seeds are
   transcribed by producer skills from citing papers' reference lists and
   can carry the wrong DOI, PMID, or both (observed: the McCaleb 2024 stub
   carried a different paper's DOI from the same reference list;
   literature-dive Tier-1 task contexts were ~70% wrong on 2026-08-05).
   Run the pre-dispatch validator over the whole queue in one batch:

   ```bash
   python3 skills/paper-ingest/scripts/validate_identifiers.py \
       --batch /tmp/queue_citations.json --recover
   ```

   Build the batch JSON from each stub's `## Citation` entry and
   frontmatter: `title`, `author` (first-author surname), `year`, plus
   whatever of `pmid`/`doi`/`pmcid` the stub carries (~2s per citation;
   this step runs once per drain, not per delegation batch). Then:

   - `validated` — dispatch as normal.
   - `recovered` — patch the stub's seed identifiers (frontmatter
     `doi`/`pmid` and the `## Citation` entry) to the corrected values,
     note the correction in the stub's `## Ingest log`, then dispatch
     with the corrected identifiers in the task context.
   - `HOLD` — do not dispatch. Note in the final report for manual
     resolution (same treatment as a terminal-diagnostic skip).
   - `retracted: true` — surface in the final report; do not dispatch
     without asking the user (a retracted paper may still warrant a
     page, but that is a human call).

3. **Delegate `paper-ingest` per stub, in batches.** Group remaining stubs
   into batches of up to 3 (the configured `max_concurrent_children`). For
   each stub in a batch, spawn a subagent via `delegate_task` with:

   - `goal`: "Run the `paper-ingest` skill against the existing stub page
     `papers/<slug>.md` as the UPDATE target. Fill the body sections,
     preserve `cited_by` exactly, flip `needs-ingest: true` → `false`,
     remove the `stub` tag. On failure, append a diagnostic to the page's
     `## Ingest log` and leave `needs-ingest: true`."
   - `context`: the stub's absolute path, the citation entry from its
     `## Citation` section (as the identity-resolution seed), any DOI/PMID
     already on the page, and the current `cited_by` list (so the subagent
     can verify it preserved them).
   - `toolsets`: `['file', 'web', 'terminal']`.
   - Return contract: one of `SUCCESS`, `FAILURE: <phase> — <diagnostic>`,
     or `SKIP: <reason>`. Nothing else.

   Submit the batch and wait for all results. Do *not* duplicate the
   stub-fill logic in the orchestrator — `paper-ingest`'s UPDATE path is
   the only place that knows how to fill a stub.

4. **Verify each delegated fill before declaring success.** Subagent
   return summaries are self-reports, not ground truth. For every stub
   the subagent claimed `SUCCESS` on, the orchestrator must:

   - `read_file` the page;
   - confirm `needs-ingest: false` in frontmatter;
   - confirm the `stub` tag is gone;
   - confirm `cited_by` matches what the orchestrator passed in (same
     entries, same order — the subagent must not have rewritten it).
     **Use a precise extractor that stops at the next top-level YAML key,
     not a context window like `grep -A6` which spans into `links:` and
     produces false alarms:**

     ```bash
     sed -n '/^cited_by:/,/^[a-z]/p' <page.md> | grep '^  - '
     ```

     Also confirm `cited_by` contains *only* `grants/<slug>` and
     `papers/<slug>` entries — `methods/`, `concepts/`, `projects/`,
     `hypotheses/`, `people/`, `institutions/` slugs in `cited_by` are a
     violation (those belong in `links:`). One such violation was observed
     in a 2026-05-20 drain and is now explicit in `paper-ingest`'s
     contract, but the verifier here is the safety net.
   - confirm at least the canonical body sections expected by
     `paper-ingest` are present (not empty).
   - confirm the **required frontmatter invariants** from `paper-ingest`
     hold on the filled page (see its "Required frontmatter after a
     successful fill" section). A subagent that flipped `needs-ingest`
     to `false` while leaving any of these empty has not actually filled
     the page:

     ```bash
     # All required identity fields must be non-empty.
     # authors: must be a non-empty list of people/<slug> entries.
     python3 - <<'PY' "<page.md>"
     import sys, re, yaml
     p = open(sys.argv[1]).read()
     fm = yaml.safe_load(p.split('---', 2)[1])
     errs = []
     for k in ('doi', 'venue', 'year', 'status', 'title'):
         if not fm.get(k):
             errs.append(f"missing/empty: {k}")
     authors = fm.get('authors') or []
     if not authors:
         errs.append("authors is empty")
     bad = [a for a in authors if not re.match(r'^people/[a-z0-9-]+$', str(a))]
     if bad:
         errs.append(f"authors not in people/<slug> form: {bad[:3]}")
     print('\n'.join(errs) if errs else 'OK')
     PY
     ```

     A non-`OK` return is a verification failure regardless of what the
     subagent claimed.

   This invariant exists because the 2026-05-20 drain produced 26 of 29
   filled pages with `authors: []` and most with `venue: ""`, all of
   which the orchestrator had counted as SUCCESS. The subagent return
   string is a self-report; only the read-back is ground truth.

   If any check fails, the result is recorded as a failure in this
   session's tally — even if the subagent claimed success. Re-flip
   `needs-ingest: true` if the subagent left it false but the page is
   clearly incomplete, so the next drainer run picks it up.

   A failed batch entry does not halt the queue. Continue to the next
   batch. Per-stub `## Ingest log` entries (written by the subagent's
   `paper-ingest` invocation on real failures) are how cross-session
   memory of broken DOIs accumulates; the orchestrator's tally is just
   for the run summary.

5. **Enqueue propagation for every successful fill.** For each stub that
   verified as SUCCESS in step 4, append a packet to
   `docs/rem-cycle/inbox.yaml`:

   ```yaml
   - id: <YYYY-MM-DD>-<slug>
     page: papers/<slug>
     event: stub-filled
     date: YYYY-MM-DD
     consumed_by: []
   ```

   This closes the blind spot: a filled stub never appears in
   `git log --diff-filter=A` (the file already existed), so without the
   packet the dream never learns the page now has content. Plain list
   append under `items:` — never rewrite the whole file. Dedup on `id`.

6. **Final report.** When the queue is drained (or every remaining stub
   has been deliberately skipped), produce a single summary:

   ```
   ingest-pending-papers — run summary

   Queue size at start:        N stubs
   Successfully ingested:      X
   Failed (logged on page):    Y
   Skipped (prior terminal):   Z

   Failures:
     - papers/<slug-1> — phase 1 (resolve identity): CrossRef returned no
       match; PubMed lookup also failed. Suggest manual DOI.
     - papers/<slug-2> — phase 9 (archive raw source): no OA PDF, no PMC.
       Suggest setting needs-enrichment: true and routing to
       restructure-thin-page.

   Skipped:
     - papers/<slug-3> — last attempt 2026-05-15 logged "DOI 10.x/y
       unresolvable; no record in CrossRef, PubMed, or bioRxiv. Likely
       malformed citation in the source grant." Suggest manual
       intervention.
   ```

   The report is the only output of the skill. The actual changes are on
   the per-paper pages.

## Anti-patterns

- **Running this skill in the same session as `grant-ingest`.** It defeats
  the entire point of the producer/consumer split. Always a fresh session.
- **Halting the queue on a single failure.** A bad DOI on stub #3 should
  not block stubs #4 through #N. `paper-ingest` logs the failure on the
  per-paper page; this skill reports it in the summary and moves on.
- **Reimplementing the stub-fill logic here.** This skill is an
  orchestrator. The actual work of filling a stub — DOI resolution,
  abstract extraction, body distillation, `cited_by` preservation,
  `needs-ingest` flip, `## Ingest log` append — belongs to `paper-ingest`.
  This skill calls it; it does not duplicate it.
- **Retrying a stub that previously failed with a terminal diagnostic.**
  The `## Ingest log` on the stub records why a prior run gave up. Read
  it; skip the stub and note the skip in the report; don't burn cycles
  on a known-broken DOI.
- **Touching `cited_by` directly.** This skill never writes to that
  field. Edges accumulate via the producer skills (`grant-ingest` adds
  `grants/<slug>` when it cites a paper; future paper-side skills add
  `papers/<slug>` when one paper cites another). The drainer just
  triggers fill.
- **Trying to "auto-determine" the right model for the subagents.** Subagents
  inherit the parent's model; `delegate_task` does not accept a model
  parameter. Do not invent a way to set one. When per-task model selection
  lands in Hermes, this skill gets revisited with explicit guidance —
  until then, all subagents run under the parent.
- **Skipping the verification step in Phase 4.** A subagent returning
  `SUCCESS` is a self-report, not a fact. The carve-out in `SOUL.md` §2
  that lets this skill delegate at all is contingent on read-back
  verification of every claimed fill. If verification is skipped, the
  spine is being violated; do not skip it for speed.
- **Running batches larger than `max_concurrent_children`.** The user's
  configured cap is the contract. Larger batches will be silently
  truncated by `delegate_task` and you will lose track of which stubs
  actually ran.
- **Inline-chaining when the queue is small.** "Only three stubs, I'll
  just do them here in the orchestrator" is the most common way the
  delegation discipline breaks. The producer/consumer split is a *contract*
  about context isolation, not an optimization that's optional when the
  queue is short. Delegate even when the queue is one stub: Phase 3 is the
  contract regardless of N. The user can verify this is happening from the
  tool stream (see "Running this skill — kickoff and monitoring" below).

## Running this skill — kickoff and monitoring

This section is for the *user* invoking the drain, not for the orchestrator
running it. The orchestrator already has its instructions above.

### Kickoff prompt (paste verbatim at session start)

```
Run ingest-pending-papers. Phase 3 = one delegate_task per stub batched at
max_concurrent_children — never inline-chain paper-ingest yourself, even if
the queue is short. Phase 4 read-back verification is mandatory for every
stub the subagent claims SUCCESS on. State up front whether you are
delegating or chaining inline before you start, so I can tell from your
first reply which mode you're in.
```

The last sentence is the cheap tell. A smaller model that intends to
inline-chain will often say so when asked directly, even when its later
output looks like delegation. If the first reply talks about "running
paper-ingest on each stub" without mentioning `delegate_task`, abort the
session and start a fresh one with the prompt re-pasted.

### Monitoring signals from the tool stream

Three observable invariants tell you the orchestrator is doing what it
claims, regardless of what its prose says:

  1. **One `delegate_task` call per batch.** The tool-call telemetry is
     authoritative. A session draining N stubs in batches of 3 should show
     `ceil(N/3)` `delegate_task` calls. Zero `delegate_task` calls means
     the orchestrator is inline-chaining; abort.
  2. **Orchestrator context stays flat.** Context grows by the stub list at
     the top (small) and the per-batch return summaries (small), and *not*
     by paper bodies. If you see paper abstracts or distilled bodies in
     the orchestrator's tool outputs, paper-ingest is running inline.
  3. **Phase 4 read-backs are visible.** After each batch returns, you
     should see `read_file` calls against the just-filled stub pages — one
     per claimed success. No read-back = no verification = spine violation.

These three signals are independent of model size, prompt fidelity, and
the orchestrator's own narration. When they all hold, the drain is honest.

