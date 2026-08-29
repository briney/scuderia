# The agora: inter-agent collaboration contract

Status: **DRAFT** (2026-08-24). Contract reviewed by the human; the pilot
that validates it is planned but not run.

A scuderia agent is one agent per instance. But agents of *different kinds* can
collaborate: a knowledge agent (e.g. a mnemo instance) holds what is known;
a doer agent (e.g. an ergon instance) holds what can be done. The **agora**
is where they meet: a shared artifact store plus the message conventions
that surround it.

This document is the harness-neutral contract. Transports are bound per
harness in `docs/harnesses/`; the capabilities named here are added to
`core/capabilities.md`.

## Principles

1. **Contract is harness-neutral; transport is harness-bound.** Message
   shapes, store layout, and write rules are defined here once. How a
   message physically travels (Hermes Bot Chat, a future harness's
   equivalent) is an adapter-doc concern.
2. **Small messages, big payloads by reference.** Messages carry
   questions, statuses, and `agora://` pointers. Structured data —
   sequences, residue lists, task inputs — is written to the store as a
   *bundle*; the message carries the path, never the payload.
3. **No agent writes into another agent's repo.** The unit of privacy is
   the repo (scuderia's load-bearing rule). If a doer's output is worth
   remembering, the knowledge agent ingests it through its own skills.
   The agora is the *only* shared writable surface.
4. **Truth/fidelity split.** The requesting agent guarantees the input
   bundle is correct. The executing agent guarantees the transformation
   is faithful and *verified* — never reports success without real
   output. When execution fails, the report says what was tried and
   what is missing.
5. **Craft state, not domain data.** A doer's persistent state is its
   capability library, its artifact registry, and its craft knowledge
   (tool quirks, environment facts). Domain facts are requested from
   the knowledge agent every time — cached domain data goes stale, and
   the knowledge agent's store is the single source of truth.

## The store

The agora lives on a **synced shared filesystem** reachable by every
participating agent *and* by the human (the human opens artifacts
interactively — this constraint rules out object-storage-as-primary).
Reference substrate: a cloud-drive folder (Dropbox) pinned
available-offline on agent hosts. Sync is **not backup** — deletions
propagate; a scheduled mirror to object storage (e.g. R2) is the
recommended assurance layer.

Each host configures an absolute **`AGORA_ROOT`** path. Messages use
`agora://` URIs, resolved per machine against the local root — paths
are never transmitted as absolute host paths. `AGORA_ROOT` must be an
absolute, fully spelled-out path: never `~`-relative (agent shells may
run with a shimmed `$HOME`), and quoted carefully if it contains
spaces.

### Layout

```
agora/
  bundles/                          # data payloads: requester → doer
    <date>-<slug>/
      bundle.json                   # the structured ask
      ...payload files
  artifacts/                        # products: doer → world
    <date>-<slug>/
      manifest.json                 # written LAST — see write rules
      ...output files
  proposals/                        # doers' gated skill-creation proposals
    <date>-<slug>.md
  projects/                         # live human ↔ doer workspaces — see "Projects"
    INDEX.md                        # registry, generated from state.json files
    _inbox/                         # raw drops land here: <slug>/ + brief.md
    <date>-<slug>/
      brief.md  inputs/  work/  outputs/  log.md  state.json
```

### Write rules

These rules exist because the substrate syncs asynchronously and does
not merge. They reduce sync pathology to approximately zero:

1. **Write-temp-then-rename.** Content is written to a temporary name
   inside the destination directory and atomically renamed when
   complete. No reader ever sees a partial file.
2. **Write-once.** Every deposit is a new immutable directory
   (`<date>-<slug>/`). A revision gets a new slug, never an overwrite.
3. **Manifest last.** `manifest.json` is the final file written in an
   artifact directory. *Manifest exists ⇒ artifact complete.* This is
   the readiness signal; readers must check for it, not guess.

Rule 2 applies to `bundles/`, `artifacts/`, and `proposals/`.
`projects/` is the documented exception — a mutable, human-co-edited
surface with its own per-file rules, defined in "Projects" below. Rules
1 and 3 apply everywhere, including inside a project's `outputs/`.

### What the agora is not

The agora is **not an instance store**. No frontmatter, no page kinds,
no linting, no indexing, no wikilinks. It is a working surface shared
across agents. Content that proves load-bearing is promoted into an
instance by that instance's own ingest skills; the agora copy remains as
the file the human can touch.

## Projects

A **project** is a live, mutable workspace shared by the human and one
doer — the only place in the agora where the write-once rule does not
apply at the directory level. It exists for iterative work: the human
drops raw inputs plus instructions, the doer intakes and runs a first
pass, and both refine the results over multiple sessions.

Anatomy of `projects/<date>-<slug>/`:

- `brief.md` — the ask, in prose; edited as the work evolves.
- `inputs/` — the dropped files, hashed at intake, frozen thereafter.
- `work/` — the doer's scratch: scripts, intermediates.
- `outputs/` — finished artifacts only; write rules 1 and 3 apply within
  it (temp-then-rename, `manifest.json` last, hashes recorded).
- `log.md` — running journal: what ran, what was corrected, what is next.
- `state.json` — `{status, created, last_activity, open_questions}` with
  `status ∈ {inbox, active, dormant, complete}`.

Rules:

1. `inputs/` is immutable after intake. New data mid-project arrives via
   `_inbox/` and is folded in by the doer.
2. `outputs/` entries are versioned — a revised figure is a new file,
   never an overwrite.
3. `INDEX.md` is generated from the `state.json` files, never
   hand-edited.
4. A project belongs to exactly one doer instance. A sibling agent
   participates by commissioning the doer, never by writing into the
   project.

Intake is **notify-and-confirm**: detection machinery is harness-bound,
but the contract requires that the doer restate its understanding of the
brief and the planned first pass, and receive human confirmation, before
intake runs.

## Capabilities

Three new named capabilities (full contracts in `core/capabilities.md`):

- **`agent-message`** — send a message to a sibling agent; receive its
  reply asynchronously.
- **`agora-deposit`** — create a bundle or artifact directory under the
  write rules above.
- **`agora-resolve`** — resolve an `agora://` URI to a local path and
  check readiness (manifest presence for artifacts).

## Message shapes

Messages are short prose plus a small JSON block. Every message opens
with a sender prefix (`Message from <instance>:`) so the receiving agent
knows who is talking. Three types:

- **Query** (doer → knowledge agent): a question, an optional
  `agora://` bundle pointer for structured context, and the expected
  reply shape. The knowledge agent answers from its own store and
  deposits any structured payload as a reply bundle.
- **Commission** (human or knowledge agent → doer): a task
  specification, a bundle pointer with inputs, and the expected
  artifact description (formats, verification expectations).
- **Report** (doer → requester): `status` ∈ {complete, blocked,
  failed}, artifact pointers, the verification performed, and — for
  blocked/failed — what was tried and what is missing. Failure reports
  are the feedstock for skill proposals.

## bundle.json

```json
{
  "id": "<date>-<slug>",
  "created": "<ISO-8601>",
  "from": "<requesting instance>",
  "to": "<executing instance>",
  "type": "query | commission",
  "question": "…",
  "payload": ["relative paths of files in this bundle"],
  "context": "…why, constraints, deadlines…",
  "expects": { "reply_shape": "…", "artifact": "…" }
}
```

## manifest.json

Written last in every artifact directory. The provenance record:

```json
{
  "id": "<date>-<slug>",
  "created": "<ISO-8601>",
  "creator": "<executing instance>",
  "commission": "agora://bundles/<date>-<slug>",
  "inputs": [{"path": "…", "sha256": "…"}],
  "tools": [{"name": "…", "version": "…"}],
  "commands": ["…exact commands run…"],
  "verification": [{"check": "…", "result": "pass|fail", "detail": "…"}],
  "outputs": [{"path": "…", "sha256": "…"}]
}
```

Any artifact answers: what request made you, from what inputs, with
what tools, and how were you verified.

## The proposal flow (skill governance interlock)

Doers learn, but creation is gated. The full policy lives in the doer
profile; the interlock with the agora is:

1. A doer hits a capability gap mid-task. It may write **one-off
   scripts freely** in scratch space — that is doing its job.
2. **Promotion to skill is gated**: the doer stops (or completes the
   task ad hoc) and writes a proposal to `agora://proposals/` — scope,
   the motivating task, and the demonstrated script as evidence.
3. The human approves or rejects. Only then is the skill crystallized
   (authored as a proper SKILL.md, marked with agent provenance so the
   harness's skill curator manages it as an auditable class).

## Failure reporting

A blocked/failed report names: the attempted approach, the failing
step, the error evidence, and what capability or input would unblock
it. "I couldn't" without those four elements is not a report.

## Open items

- Per-harness bindings: Hermes first (`docs/harnesses/hermes.md`).
- Kanban-style durable task queues as the commission transport:
  deferred until message volume justifies the machinery.
- Doer-initiated messages (e.g. "a stored artifact's upstream data was
  deprecated"): out of scope for v1; doers are reactive.
- `docs/north-star/DESIGN.md` integration: once the pilot validates
  this contract, the north-star blueprint gains a multi-agent section.
