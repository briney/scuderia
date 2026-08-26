---
name: agora-exchange
description: "Use for reads/writes to the agora shared store and for messaging sibling agents."
version: 1.1.0
author: soma
license: MIT
platforms: [macos, linux]
required_environment_variables: [AGORA_ROOT]
metadata:
  hermes:
    tags: [agora, cross-profile, collaboration, shared-storage]
---

# agora-exchange — shared store + sibling-agent messaging

The **agora** is the shared-storage layer for collaboration between agents
(instances of soma profiles on the same host) and their human. It is
**not an instance store**: no frontmatter, no page kinds, no linting, no
indexing. Content that proves load-bearing gets promoted into an instance
via that instance's own ingest skills; files stay put.

**Canonical contract:** `../agora.md` (harness-neutral rules). This skill
is the generic procedure every participating agent loads; where the two
disagree, the contract wins and this skill should be patched.

**Capabilities named:** `agora-deposit`, `agora-resolve`, `agent-message`
(see `capabilities.md`).

## Configuration

`AGORA_ROOT` — the absolute local path of the shared store — comes from
the **environment** (per-harness binding; Hermes: the profile's `.env`).
Never hardcode it, never commit it, never expand `~`-relative forms
(agent shells may run with a shimmed `$HOME`). If `AGORA_ROOT` is unset,
refuse cleanly and tell the human to configure it per
`docs/harnesses/<harness>.md`.

In cross-agent messages, use `agora://<subdir>/<name>` URIs; each machine
resolves against its own `AGORA_ROOT`. Absolute host paths are never
transmitted.

## Layout

```
agora/
  bundles/      # data payloads: requester -> doer (the structured ask)
    <date>-<slug>/bundle.json
  artifacts/    # products: doer -> world
    <date>-<slug>/manifest.json   # written LAST
    <date>-<slug>/...files
  proposals/    # doers' gated skill-creation proposals
  projects/     # live human <-> doer workspaces (mutable — the only exception)
    _inbox/     # raw drops: <slug>/ + brief.md; intake is notify-and-confirm
```

## Write rules (non-negotiable)

1. **Write-temp-then-rename.** Write to a temp name inside the
   destination directory, then atomically rename. Readers may open files
   mid-sync; rename is the only safe publish.
2. **`manifest.json` is written LAST.** "Manifest exists" = "artifact
   complete" — it is the readiness signal. Manifest records requester,
   input bundle path, tool versions, exact commands, content hashes.
3. **Artifacts are write-once.** Every deposit is a new immutable
   `<date>-<slug>/` directory; revisions get a new slug, never an
   overwrite.
4. Deposit **interactive session files** (`.pse`, Chimera sessions, …)
   alongside data files — the human opens artifacts interactively.

## Messaging a sibling agent (`agent-message`)

Transport is bound per harness (`docs/harnesses/<harness>.md`); Hermes
uses Bot Chat. Rules regardless of transport:

- Open with `Message from <instance>:` so the receiver knows who is
  talking.
- Messages are prose + `agora://` pointers. Never paste bulk payloads
  into a message; deposit a bundle and send the pointer.
- Replies are asynchronous — fire, continue other work, handle the reply
  when it lands.

## Synced-filesystem pitfalls

The reference substrate is a cloud-drive folder (e.g. Dropbox) pinned
available-offline on agent hosts:

- **Directory listing can hang** while the sync client is in first-run /
  initial indexing (or materializing dataless dirs). `stat` and writes
  still work. Do NOT retry `ls` in a loop — verify with `stat` plus a
  write probe (`touch .probe && stat .probe`) instead.
- **Online-only placeholders** look present but fail on open — keep the
  store pinned available-offline on agent hosts.
- If the store root path contains spaces, quote it everywhere.
- Sync is **not backup** — deletions propagate. Version history
  mitigates; a scheduled mirror to object storage is the real backup
  layer.

## Provenance discipline

The requesting agent guarantees input *bundles* are correct; the executing
agent guarantees the transformation is faithful and verified. When an
artifact is worth remembering, the requesting instance ingests it — no
agent ever writes into another agent's repo.
