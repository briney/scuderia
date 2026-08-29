# DESIGN.md — the scuderia platform

> **The platform implementation blueprint.** This is the technical
> companion to the platform `VISION.md` in this directory. Where
> `VISION.md` renders what a scuderia *is* and *is for*, this document is
> the blueprint one layer down — how the platform machinery is built. It
> is descriptive, not a plan: present-tense, no phases, no to-do list, no
> roadmap. `VISION.md` is the oracle. Where the two disagree, *this*
> document is wrong and is brought into line — never the reverse.
>
> The blueprint is layered like the vision. *This* document covers
> **platform machinery**: profiles, instances, the harness seam, skills,
> capabilities, the agora, the feed. Each profile carries its own
> `DESIGN.md` covering its archetype — page kinds, state shape, character
> files, job clusters (`profiles/<name>/DESIGN.md`; mnemo's is the
> reference). Where both layers touch the same machinery, this document is
> the general contract and the profile document is the binding of it.

---

## 0. What this document is

A blueprint, not a vision, and the platform half of a layered pair. It
fixes how the platform's shape is realized: the repo's layout, the profile
and instance contracts, the seam to the harness, the skill and capability
discipline, and the two pieces of cross-agent machinery (agora, feed).

It describes the designed system in the present tense — the way a
blueprint draws a house that is not yet built. A reader who opens a
checkout today may find construction in progress; this document describes
the structure that construction converges on, not its current partial
state.

Every section here has a parent in the platform `VISION.md` and cites it.
The per-archetype *how* — mnemo's page taxonomy, ergon's run lifecycle —
lives with the profiles.

---

## 1. Architecture at a glance

*Implements `VISION.md` §3, §4.*

scuderia is a **kit, not a runtime**: conventions + schema-driven tools +
profile templates + a setup CLI. No plugin registries, no discovery, no
framework. A new harness needs one adapter doc, not a port; a new profile
needs one directory, not a fork.

```
core/            capability contract, the agora contract, schema-driven
                 tools (frontmatter linter), platform-level skills
interface/       the feed: card renderer + syncer (publisher-agnostic)
profiles/
  <name>/        one directory per archetype: schema.yaml, manifest.yaml,
                 conventions/, skills/, SOUL.md / STYLE.md / USER/
                 templates, example-instance/, VISION.md + DESIGN.md
docs/
  north-star/    the platform VISION and DESIGN (this pair)
  harnesses/     per-harness capability bindings (adapter docs)
setup/           the scuderia CLI: init / doctor / adopt / skill-check
```

Every agent decomposes into the four layers of `VISION.md` §4 —
**character, skills, capabilities, state**. The first two and the fourth
are markdown, owned by the instance; capabilities are tool bindings, owned
by the harness. What varies per profile is the *shape of the state*: a
mnemo brain is a knowledge graph of typed pages; an ergon doer's state is
a capability library, run log, and craft notes. The platform machinery
below is indifferent to that shape — it knows that instances are markdown
trees with a contract file at the root, and no more.

**The unit of privacy is the repo** (`VISION.md` §8). The platform repo is
public and holds no instance content; instance repos are private sibling
checkouts, never subdirectories or submodules of the platform or of each
other.

---

## 2. Profiles — the template contract

*Implements `VISION.md` §4, §5, §7.*

A **profile** is the template for a kind of agent. One directory under
`profiles/`, five required parts:

1. **`schema.yaml`** — the machine-readable taxonomy: the profile's page
   kinds (or their analog in a non-graph state shape) and their
   frontmatter contract. The frontmatter linter
   (`core/tools/lint-frontmatter.py`) is schema-driven: it validates an
   instance against its bound profile's schema, so the platform tooling
   needs no per-profile code.
2. **`manifest.yaml`** — the install contract, *Layer 0 of setup*. It
   declares, as data, the directories an instance must have and the
   template files copied at scaffold time (with `{{INSTANCE_NAME}}` /
   `{{CREATED}}` substitution). "Installed" is defined here so the two
   entry paths — the `scuderia` CLI and an agent-guided install — can
   never drift.
3. **Character templates** — `SOUL.md` (required: every agent has a
   spine — `VISION.md` §4), plus `STYLE.md` and `USER/` templates where
   the archetype wants them. The spine's content is the profile's own;
   the spine's existence is platform law.
4. **`skills/` + `conventions/`** — the profile's job set and
   cross-cutting rules, as markdown procedures (§4).
5. **`example-instance/`** — a minimal valid instance, exercised in CI:
   `scuderia init` scaffolds it, `scuderia doctor` validates it. The
   example is the contract made executable.

A profile that earns a north-star pair carries `VISION.md` and
`DESIGN.md` at its root (mnemo does). A profile that has not yet earned
them ships a stub README instead — **stub-by-design** (`VISION.md` §5):
the stub names the archetype, lists these five parts as the bar, and
stops. Half-real templates rot; a rotted template is worse than none
because it looks load-bearing.

---

## 3. Instances — the instance contract

*Implements `VISION.md` §3, §4, §7.*

An **instance** is one agent: a private repo of actual content, bound to a
profile, run by a harness. Instances are named; templates are not.

The contract is one file at the instance root, **`instance.yaml`**:
`name`, `profile`, `profile_version`, `schema_version`, `created`. That
file plus the profile's `manifest.yaml` is the whole binding.

The **CLI** (`setup/scuderia`; stdlib + PyYAML, run in place from the
checkout) operates the contract:

- `scuderia init --profile <p> --name <n> --path <dir>` — scaffold a new
  instance from the manifest.
- `scuderia adopt --path <dir>` — generate `instance.yaml` for a
  pre-existing markdown vault and validate it.
- `scuderia doctor --path <dir>` — the shared definition of done: the
  contract file parses, every declared directory exists, version pins are
  satisfiable. Exits nonzero with one complaint per failure; idempotent;
  prints the harness-binding reminders it deliberately does not perform
  (§6).
- `scuderia skill-check [--strict]` — platform-level skill hygiene: no
  frontmatter `name:` collisions across skill roots, no patch-marker
  sprawl (§4).

Harness-side bindings (symlinks, cwd) are performed once per host by the
operator, per `SETUP.md` and `docs/harnesses/<harness>.md` — the CLI
touches only scuderia-owned things.

---

## 4. Skills — how agents work

*Implements `VISION.md` §4, §7.*

A skill is a fat markdown file under a `skills/` directory — a procedure
for one recognizable job. Skills are tool-agnostic prose: they name
*capabilities* (§5), not tools. A skill is the character operationalized
for one situation, and the load-bearing discipline holds platform-wide:
**skills reference the character, they never restate it.**

Skills are **layered**, three deep:

```
platform core skills  <  profile template skills  <  instance-private skills
```

merged by name, the nearer layer winning. Platform core skills
(`core/skills/`) are the ones every agent can need (today: the agora
exchange). The binding is a harness concern; on the reference harness it
is one symlinked category per layer (`docs/harnesses/hermes.md`).

Routing is the profile's business: each profile ships a `RESOLVER.md` (or
routes through its `AGENTS.md`) mapping an incoming request to its skill.
`scuderia skill-check` guards the hygiene the layering depends on — name
collisions across roots are how resolver deadlocks start.

---

## 5. Capabilities — what agents can do

*Implements `VISION.md` §4.*

Capabilities are tool bindings — *not* markdown — and the harness provides
them. Skills name capabilities by contract (input shape, output shape,
error behavior), so a skill runs under any harness that binds the
capabilities it names, and refuses cleanly — never fabricates — under one
that does not. The tiers:

- **Universal** — fetch a URL, read/write files, spawn a subagent,
  schedule a job, send a notification, search the instance's state. Any
  reasonable harness provides these.
- **Open-API research** — PubMed, arXiv, CrossRef and friends: auth-free
  HTTP, so the API knowledge lives in skill markdown and runs through
  `fetch`. Zero code.
- **Authenticated / infrastructural** — email, calendar, messaging
  gateways (OAuth, body-owned by nature). Skills name and depend on these
  directly; a harness that lacks them degrades honestly.

The capability contract is **engineering hygiene, not iron law**: prefer
naming a capability because loose coupling keeps skills readable and
resilient — but bind directly the moment a specific tool's surface makes
the agent meaningfully better. The authoritative capability list — every
named capability, its contract, the substitution rules, and the agora
capabilities (§7) — is `core/capabilities.md`.

---

## 6. The agent–harness seam

*Implements `VISION.md` §3, §4.*

A harness loads an instance and becomes the agent. The ratified split:

- **The instance owns**: the state, the character, the skills — pure
  markdown, a movable directory.
- **The harness owns**: the live LLM loop, scheduling/cron, the terminal
  UI, messaging gateways, voice transcription, OAuth and credentials,
  proactive delivery, and the derived search index (§8) — every mechanic.

Consequence: any instance-side mechanical stack (in-process scheduler,
server transport, autopilot daemon, a required database engine) is not the
instance's to own. Where the harness already provides the mechanism, the
instance's version is deleted, not adapted.

**The instance side of the seam contract is exactly a set of file
conventions** — `instance.yaml` plus the character files at the root, the
layered `skills/` tree with its routing table, the state tree validated
against the profile's `schema.yaml`. Any harness that honors those
conventions can host any scuderia agent: the seam is profile-general, and
a harness loading an ergon instance becomes a doer by the same mechanism
that turns a mnemo instance into a mind. `scuderia doctor` validates the
contract.

**Hermes is the reference harness** and the most fully capable one.
Per-harness adapter docs in `docs/harnesses/` map each named capability
(§5) to that harness's actual mechanism and call out the skills left
degraded or unavailable — harness parity is stated, never assumed.

The live seam runs one direction: **the agent generates, the harness
delivers.** The brain composes the morning brief; the harness pushes it to
the messaging channel at 7am. The instance never owns a transport.

---

## 7. Cross-agent machinery

*Implements `VISION.md` §6.*

### 7.1 The agora

The agora is the platform's one shared writable surface — a synced shared
filesystem, reachable by every participating agent and by the human, with
per-host `AGORA_ROOT` and `agora://` URIs so absolute paths never cross
machines. The contract (`core/agora.md`, authoritative) fixes:

- **Layout** — `bundles/` (requester → doer payloads), `artifacts/`
  (doer → world products), `proposals/` (gated skill-creation), and
  `projects/` (the documented exception: live, mutable human ↔ doer
  workspaces with their own per-file rules).
- **Write rules** — write-temp-then-rename (no reader sees a partial
  file), write-once deposits (`<date>-<slug>/`; revisions get new slugs),
  manifest last (`manifest.json` exists ⇒ artifact complete). The rules
  exist because the substrate syncs asynchronously and does not merge;
  they reduce sync pathology to approximately zero.
- **Message shapes** — query, commission, report: short prose plus a
  small JSON block, payloads by reference. Reports carry verification
  evidence; "I couldn't" without approach, failing step, error evidence,
  and unblock condition is not a report.
- **The proposal interlock** — doers learn, but skill crystallization is
  gated on human approval (`VISION.md` §2: the driver owns structural
  decisions).
- **Capabilities** — `agent-message`, `agora-deposit`, `agora-resolve`,
  specified with the rest in `core/capabilities.md`.

The agora is **not an instance store**: no frontmatter, no page kinds, no
linting. Content that proves load-bearing is promoted into an instance by
that instance's own ingest skills.

### 7.2 The feed

The feed (`interface/`) is the glance layer: per-instance **cards**,
rendered on a single multi-instance surface. It is publisher-agnostic
platform machinery — the schema-driven card contract, a renderer
(`interface/pages/`, Cloudflare Pages + D1), and a single-writer syncer
(`interface/syncer/`) that validates cards against the schema and pushes
diffs. What cards *exist* — a briefing card, a budget card — is
profile-defined, declared in the profile's schema. One feed can show
several instances' cards; each instance's content space is still one
undifferentiated whole.

Deployed resource names (the D1 database, the Pages project) are infra
identifiers and are not part of the contract; they may differ from
current platform vocabulary without the design changing.

---

## 8. Instance-general patterns

*Implements `VISION.md` §3, §8.*

Four patterns were designed for mnemo and are specified here once, because
any profile may adopt them. Each profile's `DESIGN.md` states which it
adopts and binds them to its archetype; mnemo's §7–§9 is the reference
binding.

- **The user-model directory (`USER/`).** A small directory at the
  instance root modeling the driver: a declared spine (`USER/<name>.md`,
  human-owned, always loaded), an observed staging surface
  (`USER/OBSERVATIONS.md`, never consulted in conversation), and a derived
  writing fingerprint (`USER/VOICE.md`). Human-owned files, harness-
  independent by nature — every harness gets the same user model because
  the user model is files on disk.
- **The sync fabric.** The harness host holds the canonical instance and
  stays headless; Syncthing propagates it to the human's laptop(s) over a
  Tailscale mesh; host-side git pushes to a private GitHub repo for
  change-attribution, history, backup, and the iOS review bridge. The
  phone is a consumption surface, not a generation surface; the conflict
  story stays small by construction (two writers, and the agent never
  blind-overwrites).
- **The raw-source archive.** Non-markdown primary sources (PDFs, DOCX)
  go to an S3-compatible object store (Cloudflare R2), write-once and
  content-addressed, with a lightweight pointer committed to git. Nothing
  binary lands in the instance repo; the archive is the layer the markdown
  is distilled from, kept so the state can be re-derived as models
  improve. Ingest is poll-not-watch: a cron job polls the drop folder; a
  harness with filesystem events may bind `watch-path` and skip the poll.
- **The derived search index.** The markdown corpus is canonical; any
  search index over it is a disposable, rebuildable cache — git-ignored,
  never synced, harness-owned. After a write, the page is on disk
  immediately but searchable only after the next reindex; skills that
  write-then-query read directly.

---

## 9. What the platform does not own

*Implements `VISION.md` §2, §3.*

- **The program.** No platform machinery sets an agent's direction; that
  is the driver's.
- **Runtime mechanics.** The platform is a kit; the harness is the body.
- **Shared state.** There is none, by construction — the agora's
  write-once deposits are as close as the platform gets, and they are
  immutable.
- **Profile content.** The platform knows that instances have a contract
  file and a schema; it does not know what a "paper" or a "protocol" is.
