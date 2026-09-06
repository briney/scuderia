# Axis-reframed semantic probe (the harness-probe pattern)

Session detail for literature-dive Phase 6 Prong 2b. Captured
2026-09-05, autoresearch dive 3.

## The situation

Two completed dives (33 papers, AIRA/AIRA₂-seeded; 12 papers,
SENPAI-seeded) had produced an applications-heavy corpus. Bryan
reframed: "I'm more interested in HARNESSES — the technical
infrastructure and design patterns used to create a system like SENPAI
(GitHub as communication backbone, W&B as logging hub), not the
problems they solve by using them."

The reframing question: *is there anything in the concept page that
can guide a better search?*

## What worked

**1. The concept page already held the axis — it just had never been
used as query vocabulary.** The substrate axis (state
externalization), the deployment spectrum, and the
execution-infrastructure gap were all in `concepts/autoresearch-
frameworks.md`, but no search had ever been framed on them.

**2. The missing term was the field's own name for itself.** The
highest-yield search term — "agent harness" / "harness engineering" —
was in neither the concept page nor any ingested paper. Found by
running one exploratory query and reading titles, then mining the
anchor paper's related-work section, which cites the industry posts
that coined the practice (OpenAI's "harness engineering," Anthropic's
harness-design post, LangChain, browser-use's "bitter lesson of agent
harnesses"). Machinery-layer vocabulary often originates in industry
blog posts, not papers.

**3. The queries (8, paperclip -s arxiv, plain language):**

1. agent harness design patterns for autonomous research
2. git commits and pull requests as the communication backbone between autonomous agents
3. durable experiment tracking and observability for long-running autonomous research agents
4. sandboxed execution infrastructure for autonomous coding and research agents
5. infrastructure and platform architecture for deploying LLM agents on compute clusters
6. externalizing agent state and memory to databases or files for long-horizon autonomy
7. software design patterns for building reliable LLM agent systems
8. human oversight and approval gates for autonomous research agents in production

**4. Output parsing gotcha.** paperclip prints a numbered table
("1. Title\n author?\n arx_XXXX · arXiv · 2026 · N citations"), NOT a
list of paths. A parser looking for lines starting with /papers/ gets
0 hits and looks like a failed search — verify with one raw query
before writing a batch parser. Parse with regex over the `arx_<id> ·
arXiv · <year> · <cites>` lines and block-split on blank lines.

**5. Dedup + quantification closes the argument.** Grep each surfaced
arXiv ID against papers/*.md (arXiv number substring match suffices).
Result here: 113 unique, 111 not in the vault (only MemAct and
AISCIENTIST overlapped). A >90% new fraction is the signal the
initial dives had a structural blind spot, not just incomplete
coverage.

## Why the initial dives missed it (structural, not sloppiness)

- Both dives were seeded by *systems* papers whose bibliographies
  cite application results. Systems authors under-cite infrastructure
  work their designs implicitly re-implement (SENPAI cites the agents
  it orchestrates, not the runtime literature).
- Semantic search framed on system capabilities ("autonomous research
  framework") does not retrieve infrastructure papers that never use
  those words. Query framing, not corpus absence, was the binding
  constraint.

## Downstream

- Candidate list: `working-docs/harness-engineering-dive3-candidates.md`
  (cluster-organized, 7 clusters).
- Concept-page split BEFORE dispatch: autoresearch-harnesses
  (infrastructure view) split from autoresearch-frameworks
  (applications view) — see Phase 7 split protocol.
- The dive: anchor (Agentic Harness Engineering, 54 cites) ingested
  directly; 45 papers delegated in 15 batches of 3.
