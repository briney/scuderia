---
name: brain-ops
description: The core read/write cycle for the brain — brain-first lookup, the read-enrich-write loop, citations, forward linking, and the never-blind-overwrite rule. Always-on; read before any brain interaction.
triggers:
  - any brain read, write, lookup, or citation
---

# Brain operations — the always-on context layer

The brain is not an archive. It is a live context membrane that every
interaction flows through, in both directions. This skill is the discipline that
keeps that membrane honest. It runs on every turn — it is not triggered.

> **Conventions:** `skills/conventions/brain-first.md` (the lookup chain),
> `skills/conventions/quality.md` (citations, linking, the notability gate),
> `skills/conventions/graph-and-links.md` (the edge forms),
> `skills/conventions/capabilities.md` (the harness contract).

## Capabilities

`brain-search`, `brain-read`, `brain-write`, `spawn-subagent` (for
non-blocking enrichment), `user-model-query` (consulted when a question
is about your human's taste rather than the science). `brain-search` is
optional with degraded keyword fallback.

## What this guarantees

- The brain is consulted before any external research (brain-first).
- Every inbound signal runs the read → enrich → write loop.
- Every outbound answer is checked against the brain for context.
- Every fact written carries a citation or an honest `[needs-citation]` flag.
- A page is never blind-overwritten.

## Brain-first lookup

Before researching anything externally — a paper, a method, a person, a thread —
search the brain first. The lookup chain is in `skills/conventions/brain-first.md`:
`brain-search` → read the page → follow the graph → only then go external.
The brain almost always already holds something; external research fills the
gap, it does not start from scratch.

One split matters: the **brain** holds the *work* — papers, methods, hypotheses,
grants, threads. **`user-model-query`** returns the model of *your human* — their
taste, blind spots, how to engage them — from `USER.md` at the brain root.
A question about the science goes to the brain; a question about how your human
thinks goes to the user-model capability.

## On every inbound signal: read → enrich → write

Every message, meeting, or document that touches the research program:

1. **Detect** — what papers, methods, concepts, hypotheses, people, institutions
   does this signal name?
2. **Read** — load the existing pages for context before responding.
3. **Identify the delta** — what does this signal add that the page does not
   already hold?
4. **Write it back** — update the page with the new information and an inline
   citation; create the page if the subject is notable and none exists.

your human's direct statements are the highest-authority source. Capture them to the
page promptly, attributed: `[Source: your-human, <context>, YYYY-MM-DD]`.

## On every outbound response: pull context

Before answering a question about anything in the research program, read the
relevant brain pages and answer *with* that context. Do not answer from general
knowledge when a brain page covers the subject — the brain is what makes the
answer specific, grounded, and continuous with past conversations.

## Ambient enrichment

Enrichment is the default, not a mode. Everything your human says is a potential
ingest event. When a signal names something worth a page, enrich it — but:

- **Never block the conversation.** Spawn a sub-agent for anything that would
  slow the response.
- **Never announce it.** Do not say "I'm updating the brain" — just do it.
- **Respect the notability gate** (`skills/conventions/quality.md`). A one-off mention
  is not a page.

## Writing a page

- **Cite or flag.** Every substantive claim carries a source or `[needs-citation]`
  — the `SOUL.md` spine, applied to the page (`skills/conventions/quality.md`).
- **Link forward.** Add `[[kind/slug]]` wikilinks in prose and typed edges in
  frontmatter. Never hand-write a backlinks section — backlinks are derived
  (`skills/conventions/graph-and-links.md`).
- **Never blind-overwrite.** Read the page's current state first. If it was
  edited very recently — your human may have just touched it in Obsidian — append or
  hold rather than clobbering (`VISION.md` §4.1, `DESIGN.md` §9.4).
- **File by subject.** The primary subject sets the kind, not the format the
  content arrived in (`_brain-filing-rules.md`).

## Anti-patterns

- Answering from general knowledge when a brain page exists.
- Going external before searching the brain.
- Writing a fact with neither a citation nor a `[needs-citation]` flag.
- Blocking the response to enrich, or announcing the enrichment.
- Overwriting your human's own words with a lower-authority source.
- Creating a page for a non-notable one-off mention.
