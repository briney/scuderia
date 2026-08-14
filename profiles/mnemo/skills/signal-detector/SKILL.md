---
name: signal-detector
description: Always-on ambient capture — fires on every inbound message to catch your human's original research thinking and entity mentions, and file them to the brain. Spawned as a parallel sub-agent; never blocks the response, never announced.
triggers:
  - every inbound message (always-on)
---

# Signal Detector — ambient brain capture

A lightweight sub-agent that fires on every inbound message and captures two
things with **equal priority**:

1. **your human's original research thinking** — a thesis, an objection, a framing,
   a brainstorm aside. Preserved verbatim.
2. **Entity mentions** — papers, methods, concepts, people, institutions named
   in passing.

Original thinking is at least as valuable as entity extraction. The ideas are
the intellectual capital; the entities are bookkeeping. Both compound over time.

> **Conventions:** `skills/conventions/quality.md` (the notability gate, citations,
> forward-only linking), `skills/conventions/graph-and-links.md` (edge forms),
> `_output-rules.md` (exact-phrasing preservation),
> `skills/conventions/capabilities.md` (the harness contract).

## Capabilities

`brain-search`, `brain-read`, `brain-write`, `spawn-subagent` (the skill
itself runs as a parallel sub-agent, never blocking the main response).
`brain-search` optional.

## What this guarantees

- Fires on every message — no exception unless the message is purely
  operational ("ok", "thanks", "do it").
- Runs in parallel — spawned as a sub-agent, never blocks the main response.
- Captures your human's thinking in their **exact phrasing** — no paraphrase, no
  grammar cleanup. The language *is* the insight (`_output-rules.md`).
- Detects entity mentions and creates or enriches the right pages.
- Logs a one-line signal summary so the ambient loop stays debuggable.

## Phase 1 — capture original thinking (primary)

When your human expresses a thought, observation, thesis, or framing that is *theirs*
— something he generated, not a fact he is relaying — capture it:

- A reflection or brainstorm capture → `notes/<slug>.md` (a `note` page).
- A reusable framework or principle → `concepts/<slug>.md` (a `concept` page).
- A testable claim worth tracking evidence on → `hypotheses/<slug>.md` (a
  `hypothesis` page).

Default to `notes/` when in doubt — first-person thinking lives there.

**Concept stubs: capture cheap, defer the judgment** (`conventions/concept-stub-capture.md`).
When the idea is a *candidate lens* — a recurring way of thinking, a framing, a
persistent bet — but it is not yet obviously a full `concept`, do **not** force
the triage at capture. File it as a `note` with `is_concept_stub: true` and a
forward link, verbatim, no synthesis. Do not decide here whether it is a
"reusable framework" vs "testable claim" vs "riff" — that is
`concept-coalesce`'s job, later, once you can see whether it recurred. Only
promote to `concepts/` or `hypotheses/` when the shape clearly fits *right now*;
everything candidate-shaped becomes a stub.

Capture rules:

- **Verbatim.** Quote your human's words in a quote block. Use his own terminology
  for the slug and title.
- **Attribute.** `[Source: your-human, <context>, YYYY-MM-DD]` — his direct
  statements are the highest-authority source (`skills/conventions/quality.md`).
- **Link forward.** Add `[[kind/slug]]` wikilinks to the papers, methods,
  concepts, people, and institutions the thought touches. An unlinked note is
  a thin note.

## Phase 2 — capture entity mentions (secondary)

For each paper, method, concept, person, or institution the message names:

1. **Search the brain** — does a page already exist? Run the name through
   `brain-search`.
2. **No page** — apply the notability gate (`skills/conventions/quality.md`). If it is
   load-bearing for the research program, create the page; if it is a one-off
   mention, do not.
3. **Thin page** — chain to `enrich` (for a person or institution) or
   `restructure-thin-page` (for a stub page) to flesh it out.
4. **Rich page** — add the new detail with a citation, or no action if the
   message adds nothing.

People are collaborators, students, postdocs, and paper authors. Institutions
are labs, universities, consortia, and funders.

Link forward only — `[[kind/slug]]` wikilinks in prose and typed edges
(`links:`, `cites:`, `supports:`, `refutes:`) in frontmatter. Never hand-write
a backlinks section; inbound edges are derived (`skills/conventions/graph-and-links.md`).

## Phase 3 — log the signal

Always emit a one-line summary so the ambient loop is debuggable:

- `Signals: 0 ideas, 0 entities (skipped: operational)`
- `Signals: 1 idea (→ notes/chronic-antigen-drift), 2 entities (→ people/jane-doe, papers/smith-2025)`

## Output

No visible output to your human. The skill runs silently; its product is the brain
pages it writes and the one-line signal log.

## Anti-patterns

- Blocking the main response to finish signal capture.
- Paraphrasing your human's thinking instead of preserving exact phrasing.
- Creating a page for a non-notable one-off mention.
- Announcing the capture ("I've saved that to the brain").
- Running on a purely operational message.
- Filing a framework to `notes/` when it is plainly a `concept`, or a research
  fact your human is relaying as if it were their own original thinking.
