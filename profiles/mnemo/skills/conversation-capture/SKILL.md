---
name: conversation-capture
description: Capture a discussion — on Bryan's one-line trigger, distill the current session into a durable `conversation` page (discussion / explainer / fit), preserve his key phrasings verbatim, archive the raw transcript to R2, and chain forward into the graph.
triggers:
  - "capture this convo"
  - "record what we just discussed"
  - "save this discussion"
  - "capture this as a fit assessment"
  - a request to capture the current conversation
---

# Conversation capture — the deliberate thread-level artifact

Turn the discussion that just happened into a `conversation` page. This fires on
a **manual trigger** from Bryan — his judgment is the gate for what deserves a
page (full design lives in the instance's private `docs/specs/`). The
skill does not run ambiently and must not interrogate; capture with what the
session gives you, infer the rest, and let Bryan correct.

> **Conventions:** `_brain-filing-rules.md`, `skills/conventions/quality.md`
> (citations, exact-phrasing preservation), `skills/conventions/graph-and-links.md`
> (forward-only edges, derived backlinks), `skills/conventions/raw-source-archive.md`
> (the R2 archive), `_output-rules.md` (exact-phrasing preservation),
> `skills/conventions/capabilities.md` (the harness contract),
> `skills/conventions/frontmatter.md` (the `conversation` schema).

## Capabilities

- **Required:** `brain-read`, `brain-write`.
- **Preferred:** `read-conversation-history` — the transcript is a completeness
  cross-check on the in-context session (Phase 2). When absent, capture from the
  live conversation in context; early turns may be truncated if the session was
  compacted.
- **Best-effort:** `raw-source-archive-upload` — Hermes natively, Claude Code
  when rclone + R2 is configured. When absent, still write the distilled page
  and flag it for a later archival pass (`tags: [needs-archive]`); do not fail.
- **Optional:** `brain-search` — resolve anchor and linked pages by name
  (Phases 3, 6); falls back to keyword search under Claude Code.

## What this guarantees

- Fires only on Bryan's trigger — never ambiently (that is `signal-detector`'s
  job; this skill captures the *thread*, not the *atoms*).
- Your human's key phrasings are preserved **verbatim** in quote blocks; the mind's
  side is distilled.
- The raw session transcript is archived to R2; the page carries a `sources:`
  pointer and the transcript never enters git.
- The page is filed by `mode` with the right body shape, wired to any anchor via
  `about:`, and chained forward into the graph.

## The split: verbatim human, distilled mind

Preserve Bryan's load-bearing phrasing **verbatim** — the exact words carry
signal a paraphrase loses (`_output-rules.md`). The archived transcript (Phase 4)
is the full raw record; the page is a distillation that keeps his exact words
where they matter and interprets the rest.

- Keep: `"I don't think a per-token masking objective even sees the pairing signal"`
- Not: `Bryan doubted that masking captures pairing`

## Phases

1. **Receive the trigger.** Bryan may name the mode ("...as a fit assessment")
   or an anchor — honor it. Otherwise infer both. Never block on a question the
   session already answers.

2. **Read the session.** Distill from the conversation in context, cross-checked
   against the session transcript (`read-conversation-history`) so a long or
   compacted session does not lose its early turns. The source is channel-
   agnostic — a Hermes TUI discussion and a Telegram one are captured the same
   way; record where it happened in `channel:`.

3. **Classify and anchor.** Pick the `mode` — first clear match:
   - **`explainer`** — the session was walking through one dense paper to
     understand it. Almost always single-anchored (`about: [papers/<slug>]`).
   - **`fit`** — the session assessed whether a technique/model suits a use
     case. Capture the **verdict** (`fit` / `no-fit` / `undecided`) *with its
     reason* — a `no-fit` is retained as a decision record, never dropped.
   - **`discussion`** — a science-driven back-and-forth (the default). May
     anchor on a page, keep the paper that sparked it, or carry no `about:` at
     all (a free-standing idea) — then it wires through `links:` alone.

   Set `about:` only when the conversation is *centrally about* the page(s);
   leave it absent otherwise. Everything else the talk touched goes in `links:`.

4. **Archive the transcript.** Send the raw session transcript through the
   `_drop/` → R2 pipeline; record the git-tracked pointer in the page's
   `sources:` frontmatter (`skills/conventions/raw-source-archive.md`). The transcript
   never enters git. If `raw-source-archive-upload` is unavailable, skip the
   upload, write the page anyway, and tag it `needs-archive`.

5. **Write the page.** Frontmatter per `skills/conventions/frontmatter.md`; body shape
   by `mode` (below). Set `importance` low by default (~0.3) and raise it for a
   weighty capture (an explainer of a key paper); Bryan can override.

6. **Chain forward.** Add `[[kind/slug]]` wikilinks and typed edges to every page
   the conversation connects to. Never hand-write backlinks — they are derived
   (`skills/conventions/graph-and-links.md`). Then:
   - **`discussion`** that moved a concept → chain to `reinforce` (a directed
     Shift) / `concept-synthesis`; a testable claim that fell out → seed a
     `hypotheses/` page.
   - **`fit`** → link the technique/model and the use-case (`project`/`concept`).
   - **`explainer`** → stands alone; may optionally enrich the anchor paper's
     understanding, but the artifact lives here, keeping `papers/` uniform.
   - Link the atomic `notes/` `signal-detector` already dropped this session
     rather than re-deriving them.

## Page shapes by mode

```markdown
---
kind: conversation
slug: <anchor-stem>-<mode>            # or a readable topical slug
title: "<short descriptive title>"
mode: discussion | explainer | fit
about: [papers/<slug>]               # omit when free-standing
status: open | settled               # optional; defaults to open
verdict: fit | no-fit | undecided    # required iff mode: fit
channel: tui | telegram | other      # optional
date: YYYY-MM-DD
importance: 0.3
links: [concepts/<slug>]
tags: [conversation]
sources:
  - hash: sha256-...
    r2_key: conversations/....txt
    filename: "YYYY-MM-DD-<slug>.txt"
    ingested: YYYY-MM-DD
    provenance: "<harness> session, YYYY-MM-DD"
---

# <Title>
```

- **`discussion`** — a distilled **arc** of the exchange (what was proposed, the
  objection, where it landed), Bryan's load-bearing phrasings quoted verbatim,
  and an **## Outcome** line: what moved, what stayed open.
- **`explainer`** — the distilled **explanation** of the paper, standalone.
- **`fit`** — **## Question** (what, for what use case) → **## Considerations**
  (the reasoning, pro and con) → **## Verdict** (matching `verdict:`, with the
  reason).

## Citation

Attribute Bryan's statements as direct — the highest-authority source
(`skills/conventions/quality.md`):

```
[Source: Bryan, conversation, YYYY-MM-DD]
```

## Anti-patterns

- Running ambiently or on a non-trigger message — this is manual; atoms are
  `signal-detector`'s job.
- Interrogating Bryan for mode/anchor the session already answers.
- Paraphrasing his load-bearing phrasing instead of quoting it verbatim.
- Dropping a `fit`'s verdict, or discarding a `no-fit` — the negative decision
  is the value.
- Filing a captured discussion as a `note`, or into the anchor paper page.
- Committing the raw transcript into git instead of archiving it to R2.
- Hand-writing a backlinks section — inbound edges are derived.
