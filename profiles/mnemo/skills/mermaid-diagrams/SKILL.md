---
name: mermaid-diagrams
description: Use when a process should be drawn, not written.
triggers:
  - "make a diagram"
  - "draw this out"
  - "flowchart"
  - "visualize the pipeline"
  - "mermaid"
eval_contract:
  goal: |
    A Mermaid block in a brain page that renders correctly in Obsidian and actually
    clarifies the thing it was asked to draw — the chosen diagram type fits the
    relationship, the syntax is valid, and labels are terse enough to scan.
  dimensions:
    - "DIAGRAM_TYPES — does the diagram type fit the relationship shown?"
    - "SYNTAX_VALID — does the block render without a parse error in Obsidian?"
    - "LABEL_TERSENESS — are node labels short, detail pushed into prose?"
    - "CLARITY_GAIN — does the diagram show structure prose did not already make obvious?"
  hard_fails:
    - "A block that won't render (invalid syntax) = automatic failure."
    - "A diagram that merely restates prose = failure."
---

# Mermaid diagrams — render structure as a code block

Mermaid (https://mermaid.js.org) turns a small text DSL into a diagram. Obsidian
renders it natively: a fenced block with the `mermaid` language tag. This skill is
the craft reference for when a node-and-edge picture beats a paragraph in a brain
page.

> **Conventions:** `skills/conventions/page-kinds.md` (where the page goes),
> `skills/conventions/graph-and-links.md` (wikilinks vs. a diagram's own edges —
> the two must not be confused), `skills/conventions/quality.md` (the notability
> gate: do not diagram something that did not need one).

## Capabilities

`brain-write`. Sidecar to the brain-writing skills — invoked by them when a
page's content is better shown than told. Universal.

## The one rule that governs everything

**A diagram earns its place only when it shows a structure the prose did not
already make obvious.** A flowchart that three bullets already conveyed is noise.
Draw only when the *spatial* or *branching* relationship carries the meaning: a
decision tree, a pipeline, a state machine, a class hierarchy, a contrast between
two pathways. One such structure per diagram — do not cram.

## The fenced block

Obsidian renders a fenced block with the `mermaid` language tag (three backticks
opening and closing):

    ```mermaid
    flowchart TD
        A[Antigen] --> B{Bind?}
        B -->|yes| C[Neutralize]
        B -->|no| D[No effect]
    ```

## Choosing the diagram type

Match the type to the relationship, not the other way around:

| Relationship | Diagram type | Directive |
|---|---|---|
| Branching / decisions / a pipeline's flow of steps | Flowchart | `flowchart TD` (top-down) or `LR` (left-right) |
| Participants exchanging messages over time | Sequence | `sequenceDiagram` |
| A thing with distinct states and transitions | State | `stateDiagram-v2` |
| Type / class hierarchy, is-a and has-a relations | Class | `classDiagram` |

Flowchart covers most brain pages. Sequence is for protocols and interaction
timelines; state for lifecycle; class for taxonomies. If none fits naturally, the
content likely does not want a diagram at all — say so.

## Syntax essentials (flowchart)

- **Nodes:** `A[rectangle]`, `B(rounded)`, `C((circle))`, `D{branch}`,
  `E[text with spaces]`. The id (letter) precedes the bracket; the label is
  inside the bracket.
- **Edges:** `A --> B` (arrow), `A -->|label| B` (labeled arrow), `A -.-> B`
  (dotted, for weak/inferred links), `A -- B` (plain line).
- **Terminal nodes:** rounded parentheses for Start and End, diamonds for
  branches.
- **Direction:** `TD`/`TB` (top-down), `LR` (left-right), `RL`/`BT` when a
  page's column layout wants horizontal flow. Default to `TD`.
- **Subgraphs** group related nodes: `subgraph title ... end`.

## Craft rules

- **Terse labels.** Two-to-five word node labels; push the detail into the
  surrounding prose. A node label is a signpost, not a sentence.
- **Cite or flag inside the block, not just around it.** If a specific edge or
  node is a substantive claim, give it a source in the prose beneath the block
  — the same spine that governs prose governs diagrams
  (`skills/conventions/quality.md`). Do not hang a citation off a bare arrow
  with no prose anchor.
- **Do not cross the streams.** A diagram's arrows encode *flow or relation
  within the picture*. A `[[wikilink]]` encodes a *graph edge* to another brain
  page (`skills/conventions/graph-and-links.md`). A node label may be a
  wikilink, but a diagram edge is never a substitute for a page link — link the
  pages in the prose or frontmatter independently.
- **Keep it small.** If a flowchart exceeds ~15 nodes or the text is wrapping
  harder than the prose would, it has outgrown a diagram. Split it or fold it
  back into prose.

## Workflow

1. Decide whether the relationship is structural enough to *need* a picture.
   If three bullets carry it, stop.
2. Pick the diagram type from the table above.
3. Write the block with terse labels and the right direction.
4. Verify syntax by eye against the essentials above — an unrendered block is
   worse than no block (check unmatched brackets, missing `end`, IDs used
   before declared in state diagrams).
5. Anchor any substantive nodes/edges to a source in the prose beneath.

## Output

A correctly-fenced `mermaid` block, the right diagram type for the relationship,
terse labels, and any substantive claims cited in the prose below the block.

## Anti-patterns

- Emitting a diagram for something prose already made clear.
- Mismatching the diagram type to the relationship (a state machine drawn as a
  flowchart, a taxonomy drawn as a sequence diagram).
- Node labels that are full sentences or carry the whole claim instead of a
  signpost.
- An invalid block — unmatched brackets, a forgotten `end`, an unsupported
  directive — that silently fails to render in Obsidian.
- Treating a diagram edge as a graph wikilink; a diagram does not create page
  links.
- A diagram so large it is harder to read than the paragraph it replaced.
