# DESIGN.md

> **The implementation blueprint.** This is the technical companion to
> `VISION.md`. Where `VISION.md` renders what a mnemo mind *is* and *is for*,
> this document is the blueprint one layer down — how that vision is built. It
> is descriptive, not a plan: present-tense, no phases, no to-do list, no
> roadmap. `VISION.md` is the oracle. Where the two disagree, *this* document
> is wrong and is brought into line — never the reverse. The two are paired
> core documents and evolve together.
>
> v1.2 note: genericized for the scuderia platform split, as `VISION.md` was —
> "the mind" is a mnemo instance, "your human" is whoever runs one.
>
> v1.3 note: **vocabulary split** (see `VISION.md` v1.3). The platform's
> general category is the **agent**; **mind** is mnemo's self-description.
> This blueprint describes the mnemo agent — its page kinds, its knowledge
> graph, its character. Other profiles build other kinds of agents (ergon:
> a doer whose persistent state is a capability library); the *machinery*
> here (schema-driven pages, the instance contract, the harness seam) is
> profile-general, and the seam (§6) works the same for a non-mind agent.
> The instance contract file is `instance.yaml` (renamed from
> `brain.yaml`). Inter-agent collaboration: `core/agora.md`.

---

## 0. What this document is

A blueprint, not a vision. `VISION.md` fixes the shape of the thing — one
collaborator, several jobs, brain-backed, speaking through a harness. This
document fixes *how that shape is realized*: the layers a mnemo system
decomposes into, the file formats and directory structure, the page taxonomy
and frontmatter schema, the seam to the harness, the substrate stores, and the
sync architecture.

It describes the designed system in the present tense — the way a blueprint
draws a house that is not yet built. A reader who opens an instance today may
find construction in progress; this document describes the structure that
construction converges on, not its current partial state.

Every section here has a parent in `VISION.md` and cites it. If you want the
*why*, read the vision; this document is the *how*.

---

## 1. Architecture at a glance

A mnemo system decomposes into **four layers** (`VISION.md` §3.1). Three of
them are pure markdown — portable by nature, a movable directory. The fourth
is tool bindings and belongs to the body.

| Layer | What it is | Form | Owned by |
|---|---|---|---|
| **Character** | Who the mind *is* — voice, posture, the inviolable spine | Markdown (`SOUL.md`, `STYLE.md`) | the brain |
| **Skills** | How the mind *works* on a job | Markdown procedures (`skills/`) | the brain (template + instance layers) |
| **Capabilities** | What the mind *can do* — fetch, read mail, send | Tool bindings | the harness |
| **Brain** | What the mind *knows* — the knowledge graph | Markdown vault | the brain |

**The brain side is the knowledge graph, the character, and the skills** — and
nothing else. As far as possible it is *pure markdown*: a directory of files,
durable and portable. **The harness is the body and the voice** — it owns
every mechanic (the live LLM loop, scheduling, the terminal UI, messaging
gateways, voice, OAuth, proactive delivery). The harness loads the brain,
character, and skills and in doing so *becomes* the mind. Your human talks to
the mind by name; the process running is the harness (`VISION.md` §3).
**Hermes is the reference harness** and the most fully capable one; Claude
Code and other harnesses are supported to the extent that their capability
sets (§5) overlap with what each skill needs — see `docs/harnesses/` for
per-harness adapters.

The substrate is **two harness-independent stores**, neither tied to any
particular harness:

1. **The markdown brain** — your human's work and knowledge (§2). The model of
   your human lives in the `USER/` directory at the root of the brain (§7) —
   a declared spine (`USER/<name>.md`) plus derived siblings
   (`USER/OBSERVATIONS.md`, `USER/VOICE.md`) for the `user-model-reflect`
   skill and the writing fingerprint; only the spine is consulted in
   conversation.
2. **The raw-source archive** — the original documents the brain is distilled
   from, in object storage (§8).

The overriding design principle (`VISION.md` §3.2): **build the best possible
mind.** Portability is a consideration, not a constraint. The markdown
corpus stays a movable directory and the harness stays swappable — that is
all the portability that is paid for. Where binding tightly to excellent
infrastructure makes the mind better, it binds; the honest asymmetry that
follows is that some skills are fully functional only under harnesses that
provide their required capabilities (e.g., research-logistics needs
`gmail-read` and `calendar-read`; these are body-owned by nature).

---

## 2. The brain — the markdown knowledge graph

*Implements `VISION.md` §3.1 layer 4, §3.3, §4.1.*

The brain is what the mind knows. It is a tree of markdown files — inert,
portable data. There is **one undifferentiated content space**: a page is
identified by its `slug` alone; there is no multi-source or multi-brain axis
within an instance. (Multiple instances are a platform-level concern — one
feed can show several instances' cards; each brain is still one space.)

### 2.1 Directory layout

The brain is a single directory. That directory *is* an Obsidian vault (§9.1)
and *is* a git repository (§9.2).

```
brain/
├── instance.yaml        # the instance contract — name, profile, version pins
├── AGENTS.md            # orientation for any agent/human entering the vault
├── SOUL.md              # character — who the mind is (§3.1)
├── STYLE.md             # scientific-writing voice (§3.2)
├── USER/                # the user model — spine + derived siblings (§7)
│   ├── <name>.md          #   declared spine (§7.1)
│   ├── SKELETON.md        #   template skeleton (never loaded)
│   ├── OBSERVATIONS.md    #   observed layer
│   └── VOICE.md           #   derived writing fingerprint
├── RESEARCH.md          # state of the research program (§2.6)
├── skills/              # instance-private skill layer (template skills are
│                        #   bound from the profile — §4.3)
├── papers/              # ─┐
├── methods/             #  │
├── concepts/            #  │  page directories,
├── hypotheses/          #  ├─ one per page kind (§2.2)
├── projects/            #  │
├── grants/              #  │
├── interactions/        #  │
├── people/              #  │
├── institutions/        #  │
├── notes/               #  │
├── tasks/               # ─┘
├── working-docs/        # transitory working docs — NOT brain pages (§2.1.1)
├── _drop/               # raw-source ingest folder — git-ignored (§8.4)
├── .obsidian/           # vault UI config
└── .git/
```

A page is one markdown file: `papers/<slug>.md`. The `slug` is the identity.
The derived search index (§2.7) and any local database files live in
git-ignored, Syncthing-ignored paths — they are disposable, never canonical.

### 2.1.1 Working documents — outside the knowledge graph

`working-docs/` holds transitory artifacts produced during sessions:
feasibility assessments, scoring tables, subagent research outputs. These
documents inform the brain but are **not** part of the knowledge graph. They
carry no frontmatter, are not indexed by the search layer (§2.7), are not
linked with wikilinks, and have no lifecycle expectations — they may be
deleted at any time. If a working doc's content is load-bearing for the
research program, it should be summarized into the relevant brain page; the
brain page is the canonical source and the working doc is the scratch pad.
The full convention lives in `working-docs/README.md`.

### 2.2 Page kinds

A mnemo brain is **literature-native**: papers, methods, concepts, and
hypotheses are first-class; people are real but de-emphasized (`VISION.md`
§2.4, and the research framing throughout §2).

| Kind | Holds |
|---|---|
| `paper` | A research article — peer-reviewed or a preprint; the `status` field records which |
| `method` | An experimental or computational technique |
| `concept` | A scientific principle or framework |
| `hypothesis` | A testable claim the mind tracks, with evidence pro and con |
| `project` | A multi-paper research thread (a concrete `RESEARCH.md` domain) |
| `grant` | A funding application or active award |
| `interaction` | A documented interaction event — a lab meeting, 1:1, conference talk, email thread, or call |
| `note` | First-person thinking — a reflection, a brainstorm capture |
| `task` | A tracked to-do with a deadline |
| `person` | A collaborator, student, postdoc, or paper author |
| `institution` | A lab, university, consortium, or funder |

The kind determines the page's directory and its frontmatter schema (§2.3).
The authoritative, machine-readable form of this taxonomy is the profile's
`schema.yaml`; the prose form is `skills/conventions/frontmatter.md` and
`page-kinds.md`.

### 2.3 Frontmatter schema

Every page opens with a YAML frontmatter block, then a markdown body. The
frontmatter is the page's structured data; the body is its prose. A `paper`:

```yaml
---
kind: paper
slug: paired-antibody-lm-scaling
title: "Scaling paired antibody language models"
status: published         # published | preprint | unknown
doi: 10.1234/example.5678
pmid: 39876543
authors: [people/alice-example, people/a-collaborator]
venue: Nature Immunology
year: 2026
importance: 0.82          # research-salience score (§2.5)
links: [methods/preferential-masking, concepts/repertoire-drift]
tags: [methods-paper, key-citation]
---
```

Identifiers (`doi`, `pmid`, `pmcid`, `arxiv`, `biorxiv`) are first-class fields
so a page resolves to a real-world object — `doi` is the primary key. A `paper`
also carries `status` (`published`, `preprint`, or `unknown` for ingester
pages that need disambiguation): review status is a frontmatter field, not a
separate kind, so a preprint that is later published is a one-line
flip with no file move and no inbound-link rewrite. Schema is per-kind but shares
this spine: `kind`, `slug`, `title`, `importance`, `links`, `tags`. The schema is a
*convention enforced by skills and lint*, not a database constraint — the files
remain plain markdown that any tool can read. The linter is schema-driven
(`core/tools/lint-frontmatter.py` reads the profile's `schema.yaml`).

### 2.4 The graph layer

The brain is a graph. Edges are expressed in two markdown-native ways:

- **Wikilinks** in body prose — `[[methods/preferential-masking]]` — the
  Obsidian-native form, so the graph is navigable in the vault directly.
- **Typed links** in frontmatter — the `links:` list, and edge-typed lists such
  as `cites:` on a paper. Typed edges (`cites`, `refutes`, `supports`) carry the
  citation graph and the hypothesis evidence graph.

Backlinks are derived, not stored: a page's inbound edges are computed by
scanning the corpus. Link and timeline extraction over the corpus is a
mechanical pass (a body capability, §5), not a property the markdown must
maintain by hand.

### 2.5 Importance scoring

Each page carries an `importance` score in `[0, 1]` — its **research salience**.
The mind owns no code, so the score is not computed mechanically. It is
**recomputed by the `maintain` skill as an LLM pass** over signals already on
the page: a tag boost over a research-relevant tag set (`controversy`,
`novel-finding`, `methods-paper`, `seminal`, `contradicts-existing`,
`key-citation`, `under-review`, `replication-target`), the density and weight
of the user's own annotations, and graph centrality (read off the link layer,
§2.4). The authoritative rubric — what each signal contributes and how they
combine — lives in `skills/conventions/importance-scoring.md`; the `maintain`
skill operates the rubric. The score drives ranking in search (§2.7) and in
the attention contract (§4.5).

### 2.6 RESEARCH.md

`RESEARCH.md` is a single root file holding the **state of the research
program** — the active domains, the threads in flight, the funding context, the
publication pipeline. It is the *work*, not a model of the person (that is
`USER/<name>.md`, §7) and not a model of the mind (that is `SOUL.md`, §3). Skills
read it for thread context: a grant drafter resolves domain references
against it; the attention contract reads its funding context for deadline
awareness.

### 2.7 Search and retrieval

The markdown corpus is canonical. Search runs over a **rebuildable index
derived from it** — never the reverse. The index is a harness capability (§5):
the harness owns the index machinery, and the reference implementation is
**qmd** — a bundled local engine providing hybrid vector + keyword retrieval
with a reranker, exposed as the `brain-search` capability (§5.1). The index
is disposable: git-ignored, never synced, regenerable from the markdown at
any time.

qmd does **not** auto-reindex on file change. A `qmd embed` reindex is
scheduled by the harness on an interval (a cron job; see §8.4 for the
related polling note). After a brain write, the new page is on disk
immediately but searchable only after the next reindex — skills that write
and then immediately query the same page must read it directly rather than
rely on search.

This separation is what keeps the corpus portable (`VISION.md` §3.2) and
re-derivable (`VISION.md` §4.2): the brain is the markdown files; the index is
a cache. Transplanting a brain to a new harness means copying the directory
and letting the new harness rebuild its own index — qmd, ripgrep, or
whatever the new harness provides for `brain-search`.

---

## 3. The character — who the mind is

*Implements `VISION.md` §2.5, §3.1 layer 1.*

The character is who the mind is regardless of task. It is pure prose, portable
by nature, and it is authored by *disposition*, not by script.

### 3.1 SOUL.md

`SOUL.md` is one file at the root of the corpus. The name is deliberate: "soul"
names what the file holds more honestly than "character" or "config" would. It
has two layers, both necessary (`VISION.md` §2.5):

- **A thin spine of inviolable rules** — absolute, script-like, never yielding
  to the flow of a conversation: *cite-or-flag*; *no fabricated confidence*;
  *never suppress a substantive flaw to preserve rapport*. The spine is what
  makes the mind trustworthy.
- **A rich body of internalized dispositions** — the cognitive patterns,
  register fluidity, scientific taste, the build-with reflex. Dispositions shape
  every response without being rules. They are what make the mind brilliant.

`SOUL.md` §3 is the **authoritative set of cognitive patterns** — the thinking
instincts of a scientific collaborator (mechanism hunger, the discriminating
experiment, confound scan, the novelty premium, and the rest). `VISION.md`
§2.5 reproduces them verbatim; if the set evolves, both move together.

The harness loads `SOUL.md` as the character layer at the start of every
session — it is in context for every response. Dispositions are *internalized,
never narrated*: the mind does not announce which instinct it is applying.

### 3.2 STYLE.md

`STYLE.md` is the scientific-writing companion to `SOUL.md` — the character
applied to the page. It codifies your human's learned voice, the **single-
reader model** (every application written for one smart scientist whose
expertise sits adjacent to the proposal), and the discipline that keeps
finished prose free of machine-writing tells (`VISION.md` §2.2). Where
`SOUL.md` governs how the mind *thinks*, `STYLE.md` governs how it *writes*.
Grant-writing skills (§4.2) load it; other skills do not.

### 3.3 The character / skill separation

The test for character versus skill (`VISION.md` §3.1): if you cannot name a
triggering situation, it is character; if it activates in response to a
recognizable task, it is a skill. The load-bearing discipline: **skills
*reference* the character, they never *restate* it.** A skill says "apply
cite-or-flag here"; it does not re-describe what cite-or-flag means. This keeps
the character single-sourced and the skills thin.

---

## 4. Skills — how the mind works

*Implements `VISION.md` §2.1–2.3, §3.1 layer 2, §5.*

### 4.1 Skills as markdown procedures

A skill is a fat markdown file under a `skills/` directory — a procedure for
one recognizable job. Skills are tool-agnostic prose: they prefer to name a
*capability* ("ground this claim in the primary literature") over a specific
*tool*, so they stay readable and survive churn (§5.2). A skill is the character
*operationalized* for one situation.

Skills are **layered**: platform-generic skills < profile-template skills (the
mnemo corpus) < instance-private skills (the brain's own `skills/` dir),
merged by name, instance overriding template. The binding is a harness
concern; on the reference harness it is one symlinked category per layer
(`docs/harnesses/hermes.md`).

### 4.2 The three jobs as skill clusters

The three jobs (`VISION.md` §2) are **not personas and not modes**. They
are one mind — and at the implementation level, three clusters of skills over
the same brain, character, and capabilities. There is no mode to invoke and no
generator/critic toggle (`VISION.md` §2.5, decision log §8.1–8.2).

- **Thought-partner skills** — running a brainstorm, sharpening a hypothesis,
  reviewing evidence. Output is open-ended: a hypothesis, a set of experiments,
  a paper outline, a better question. These lean on `SOUL.md` and the
  user-model files (§7).
- **Grant-writing skills** — drafting a section, checking cross-section
  coherence, managing citations. These additionally load `STYLE.md` (§3.2) and
  hold the whole application in view; cite-or-flag is non-negotiable here.
- **Research-logistics skills** — the attention contract (§4.5).

### 4.3 Routing

`skills/RESOLVER.md` is the routing table — it maps an incoming request to the
skill that handles it (`AGENTS.md` is also accepted as the routing entry
point). When a request matches a skill, that skill is invoked first.
`skills/conventions/` holds cross-cutting rules; shared references
(`_brain-filing-rules.md`, `_output-rules.md`) are referenced, not duplicated.

### 4.4 Literature-grounded competence

Being current on the literature is an always-on property of the substrate, not
a persona (`VISION.md` §2.4). It is implemented as **open-API research skills**.
PubMed, arXiv, bioRxiv, CrossRef, and NIH RePORTER expose auth-free HTTP APIs;
the API knowledge therefore lives entirely in skill markdown and runs through
the universal `fetch` capability — **zero code** (`VISION.md` §3.2). A skill
that needs a paper's metadata describes the PubMed E-utilities call in prose and
the harness executes the fetch. New literature sources are new markdown, not new
software.

### 4.5 The attention contract

The research-logistics job is an **editorial mandate**, not a list-printer
(`VISION.md` §5). It is implemented as a cluster of skills with four properties:

- **A relevance bar drawn from the user model.** What matters *to your human
  specifically* comes from `USER/<name>.md` (§7), not a global heuristic.
- **A default of silence.** Nothing surfaces unless it clears the bar. The
  filter suppresses noise as actively as it surfaces signal.
- **Escalation that scales with stakes and proximity.** A grant deadline at
  T-90 is a whisper; at T-7 it is insistent. Deadlines flow from `grant` and
  `task` page frontmatter and `RESEARCH.md` funding context.
- **An auditable ignore-report.** A regular, explicit "here is what I decided
  you could ignore," so the filter is legible and your human can correct it. A
  black-box filter cannot earn trust.

The bar for this layer is trust: it succeeds only if your human can stop
compulsively checking their own inbox.

---

## 5. Capabilities — what the mind can do

*Implements `VISION.md` §3.1 layer 3, §3.2.*

### 5.1 The capability tiers

Capabilities are tool bindings — *not* markdown — and the harness provides
them. They fall in three tiers (`VISION.md` §3.2):

- **Universal** — fetch a URL, read/write files, spawn a subagent, schedule a
  job, send a notification, search the brain. Always present.
- **Open-API research** — PubMed, arXiv, bioRxiv, CrossRef, NIH RePORTER:
  auth-free HTTP, so they need no binding beyond `fetch` (§4.4).
- **Authenticated / infrastructural** — Gmail, Calendar, Telegram (OAuth,
  body-owned). Skills name and depend on these directly.

This produces an honest asymmetry (`VISION.md` §3.2): thought-partner and
grant-writing work is largely harness-agnostic; research-logistics has a hard
dependency on the body's authenticated integrations, because email and calendar
access is a body function by nature.

The authoritative capability list — every named capability, its contract, and
the substitution rules — is `core/capabilities.md`.

### 5.2 The capability contract

The contract is **engineering hygiene, not iron law**. Skills should *prefer* to
name a capability over a specific tool, because loose coupling keeps them
readable and resilient. But the rule yields the moment a direct binding makes
the mind meaningfully better. Build the best possible mind first; keep the
coupling loose where loose coupling costs nothing.

---

## 6. The mind–harness seam

*Implements `VISION.md` §3, §3.2.*

### 6.1 The split

A harness loads a mnemo brain and becomes the mind. The reference harness is
**Hermes** — a fat harness that ships its own scheduler, skill system,
cross-session memory, MCP-client support, and a messaging gateway. Other
harnesses (Claude Code, future) have different capability sets; the brain
side of the seam is the same. The split is ratified (`VISION.md` §3):

- **The brain owns**: the knowledge graph, the character, the skills — pure
  markdown.
- **The harness owns**: the live LLM loop, scheduling, the terminal UI, any
  messaging gateways, voice transcription, OAuth and credential handling,
  proactive-message delivery, and the derived search index (§2.7).

Per-harness adapter docs in `docs/harnesses/` map each capability
(§5.1) to that harness's actual mechanism — qmd vs ripgrep for `brain-search`,
cron vs scheduled-wakeup for `schedule-job`, and so on — and call out the
skills that depend on capabilities a given harness does not provide.
`user-model-query` is the same on every harness (§7); it always returns
`{declared: USER/<name>.md}`.

### 6.2 How a harness becomes the mind

The harness points at the brain directory. It loads `SOUL.md`, `STYLE.md`,
`USER/<name>.md`, and `AGENTS.md` as the always-on layer, discovers the layered
`skills/`, reads `skills/RESOLVER.md` for routing, and builds (or borrows) a
search index over the page tree. With those loaded, the running harness
process *is* the mind. The **instance side of the seam contract** is exactly
this set of file conventions — `instance.yaml` plus the character files and
`RESEARCH.md` at the root, the layered `skills/` tree with `RESOLVER.md`,
the page directories with their frontmatter schema. Any harness that honors
those conventions can host a mnemo brain. The seam is profile-general: a
harness loading an ergon instance becomes a doer agent by the same mechanism
— the file-convention set differs per profile (each profile's `manifest.yaml`
declares it). `scuderia doctor` validates the
contract.

### 6.3 The mind generates, the harness delivers

The live seam runs one direction: **the mind generates, the harness
delivers**. The morning brief is composed by a skill against the brain; the
harness is what pushes it to the messaging channel at 7am. A deadline nudge is
decided by the attention contract (§4.5); the harness is the channel it rides.
The brain never owns a transport.

### 6.4 What this means for brain-side machinery

The brain owns no runtime mechanics. There is no brain-side scheduler, no
brain-side server transport, no autopilot daemon, and no database engine
that the brain *requires* to exist. Where the harness already provides a
mechanism, the brain does not carry its own. The search index (§2.7) is the
one piece of heavy machinery near the brain, and it is harness-owned and
disposable — a cache over the markdown, not a component of the brain.

---

## 7. The model of your human — the `USER/` directory

*Implements `VISION.md` §3.3, and the theory-of-your-human in §2.1 and §5.*

### 7.1 The user model is a directory of siblings

A *Power of Two* partnership needs a theory of your human — their taste,
intellectual style, recurring blind spots, what excites or bores them. That
theory lives in a small **`USER/` directory** at the root of the brain
(alongside `SOUL.md` and `STYLE.md`), always loaded for the declared spine,
harness-independent by nature. Three files, three roles:

- **`USER/<name>.md`** — the **declared** spine. Holds what your human
  says about themselves — research priors, working style, named blind spots,
  how they want to be engaged, what's in and out of scope, and a "writing
  voice" section of argument-level judgment. Named for the person, not the
  role; the root `SOUL.md` is named for the role (the mind). Your human
  owns it; the mind may propose edits in conversation but does not
  auto-write to it. Your human refreshes it by hand, typically in
  response to discrete forcing functions (a grant reviewer critique, a
  periodic review, a stretch of work that shifted their thinking).
- **`USER/OBSERVATIONS.md`** — the **observed** layer. A staging surface
  for the `user-model-reflect` skill (§7.3): candidate observations about
  how your human works. Not always loaded; not consulted in conversation.
- **`USER/VOICE.md`** — the **derived** layer. A measured writing
  fingerprint (sentence length, tell-frequency, signature moves) computed
  from your human's own preserved prose. Consulted only when producing
  documents in your human's voice, never in conversation.

The generic `USER/SKELETON.md` ships with the template and is **never
loaded**; at setup it is copied to `USER/<name>.md`, filled in, and left
pristine for reference. This splits the user model by *mode* — declared vs.
observed vs. derived — while keeping it one directory and keeping the
declared spine the only layer always loaded.

The reason `USER/<name>.md` is the only always-consulted layer is parity:
every harness gets the same user model, because the user model is files on
disk. An earlier design used a third-party inferred layer, which made
harness parity structurally impossible; it was removed in favor of these
human-owned/derived files.

This produces a clean tetrad — four subjects, four homes, no overlap:

- **The `USER/` directory models your human** — the person and thinker, as
  they declare themselves (spine) and as their work measures (derived)
  (§7.2).
- **The markdown brain holds the work** — papers, methods, hypotheses,
  grants, `RESEARCH.md` (§2.6).
- **`SOUL.md` models the mind** — who the mind is being (§3.1).
- **`STYLE.md` models the page** — how the mind writes finished prose (§3.2).

### 7.2 How the mind uses the user-model layer

`user-model-query` is the named capability skills depend on (§5.1). It
returns the declared spine on every harness:

```
{ declared: USER/<name>.md }
```

The derived files (`OBSERVATIONS.md`, `VOICE.md`) are read directly by
the skills that produce or consume them, not routed through this
capability. The thought partner consults the spine to know how to engage
your human and where their blind spots lie; the attention contract (§4.5)
consults it for the relevance bar; document-producing skills consult
`VOICE.md` for the measured fingerprint.

### 7.3 Enrichment — manual, on demand

`USER/<name>.md` is always loaded and current by definition: your human owns
it and edits it directly, and that is the rhythm by which the user model
evolves. A skill — **`user-model-reflect`** — exists to help your human see
what would be worth adding. It reads recent session transcripts via
`read-conversation-history` and appends a dated block of candidate
observations to `USER/OBSERVATIONS.md`. The skill never writes to
`USER/<name>.md` and never duplicates content already there. If the harness
does not expose conversational history, the skill writes a no-op stub for
the date and surfaces the missing capability cleanly.

**No schedule is wired by default.** The skill is invokable on demand
("run user-model-reflect", "reflect on what I've been working on"). Running
on a cadence is possible — `cron` under Hermes, the `schedule` skill /
`CronCreate` under Claude Code — but the design choice is to wait until
periodic reflection proves useful enough to be worth automating. The skill
is fully usable without it.

`USER/VOICE.md` is produced by its own producer on demand, not on a
schedule: it re-measures your human's `## Verbatim` prose (the preserved
submitted corpus in ingested grants and papers) into a fingerprint, and
writes only to the derived file — never to the spine. Where a measured
fact in `VOICE.md` conflicts with a generic default in `STYLE.md`, the
measured fact wins.

Promotion stays with your human: they read `USER/OBSERVATIONS.md` when they
want to refresh the spine, edit the relevant section of `USER/<name>.md` to
absorb what is durable, and prune the promoted entry from the sidecar. There
is no skill that promotes for them — the spine of the user model stays under
your human's hand, the same way `SOUL.md` does.

---

## 8. The raw-source archive and ingest

*Implements `VISION.md` §3.2, §4.2.*

### 8.1 Object storage

The markdown brain is a *distillation*. Behind it sits primary-source material
that is not markdown and never will be: papers as PDFs, past grants and reviewer
critiques as PDF or DOCX, other documents your human feeds in. These are the
ground truth and must never be lost. They live in an **S3-compatible object
store (Cloudflare R2)**, **write-once and content-addressed**, with **no
file-size limits**. Every binary source lands in R2; nothing binary lands in
git.

### 8.2 Git pointers

What git keeps is a lightweight **pointer per archived file** — a content hash,
the R2 storage key, the original filename, and provenance. The pointer is
committed so history records that a source existed and how to fetch it; it is
referenced from the brain pages distilled from that source. Binaries never bloat
a clone or a Syncthing transfer.

### 8.3 Why immutable and content-addressed

The archive is the layer the brain is *derived from*. Keeping the originals
untouched means the brain can be re-derived — re-chunked, re-embedded,
re-summarized — whenever models improve. A distillation is only as safe as the
source it can fall back to.

### 8.4 The ingest pipeline

Sources get in through a **drop folder** inside the vault (`_drop/`,
git-ignored). The pipeline:

1. Your human drops a PDF or DOCX into `_drop/` (on a laptop, or via a
   messaging attachment that the harness routes to the same folder as a
   capture fallback).
2. Syncthing (§9.2) carries it to the harness host. **The host has no
   filesystem watcher** — the reference harness does not ship one, and
   harness-side filesystem events are not part of the seam (§6). Instead, a
   cron job polls `_drop/` on an interval (the polling cadence is a
   harness-side configuration choice — see `SETUP.md`); when it finds a new
   file, it triggers the ingest skill.
3. The mind ingests it — extracts text, chunks it, and files brain pages with
   citations.
4. The original is uploaded to R2 (§8.1); a git pointer is committed (§8.2).
5. The file is cleared from `_drop/`.

The poll-not-watch substitution costs latency (a file dropped sits until the
next poll fires) but no correctness — the ingest is the same once it
triggers. A harness that *does* provide filesystem events is free to bind a
`watch-path` capability and skip the poll.

Non-markdown formats are *sources*, never brain pages: the mind reads a DOCX,
but the DOCX itself stays in the archive and only its distillation is
committed.

---

## 9. Sync and the writing environment

*Implements `VISION.md` §4.1.*

### 9.1 Obsidian over the brain directory

The brain is already a tree of markdown files, so the writing environment is
not a separate system — it is a view onto the brain. The brain directory
**is** an Obsidian vault: "documents" and "brain pages" are the same objects.
Your human edits a grant draft in Obsidian; the file changes on disk; the
harness picks it up on its next poll (§8.4 — same poll-not-watch
substitution). The end-to-end edit-detection latency is the same as the
`_drop/` polling cadence. The mind writes a page and it appears in Obsidian.
There is no "did your human edit a document" problem to solve — editing a
document and editing the brain are one act.

### 9.2 Three-layer sync

Three mechanisms, because device-propagation, change-history, and the iOS
bridge are three different needs:

- **The harness host holds the canonical vault** and stays headless and
  Obsidian-free. The mind reads and writes the markdown files directly — plain
  file IO, no Obsidian process on the host.
- **Syncthing** propagates the vault between the host and your human's
  laptop(s) — continuous, peer-to-peer, over a Tailscale mesh, no cloud
  middleman. Its ignore file excludes `.git`, the search index, harness
  capture artifacts (e.g. `voice/`), and `.obsidian/workspace.json`; the
  rest of `.obsidian/` may sync so your human's setup matches across laptops.
  **`_drop/` is deliberately *not* in the ignore list** — it is the ingest
  channel (§8.4), and Syncthing is what carries dropped files from laptop
  to host. The `.gitignore` keeps `_drop/` contents out of git; Syncthing
  carries them anyway.
- **Host-side git, pushed to a private GitHub repo.** The host auto-commits and
  auto-pushes the vault. This gives change-attribution (a precise diff of what
  your human changed), version history, an off-site backup, and the iOS
  bridge.

### 9.3 The iOS bridge

Syncthing on iOS is weak, so the phone reaches the brain through GitHub instead.
The GitHub iOS app renders formatted markdown and commit diffs well. The
harness sends messages with commit-pinned GitHub permalinks to notable
just-committed files, so your human taps straight to the thing — and can review
exactly what the mind changed — rather than scrolling a directory.

### 9.4 The conflict story

The phone is a **consumption and review surface, not a generation surface**
(`VISION.md` §4.1). Your human does not draft significant text on the phone;
quick feedback flows through the messaging channel, not by editing markdown.
The phone is therefore effectively read-only on the vault.

That leaves only two writers: the mind (on the host) and your human (via
Obsidian on a laptop → Syncthing → host). They mostly touch different files.
The one case that matters — a live grant draft — is handled by a behavioral
rule, not by sync tech: **the mind never blind-overwrites a file.** It reads
current state, the host auto-commits, then the mind writes its change as a
clean commit on top; if your human edited a file very recently, the mind holds
or appends rather than clobbering.

**Privacy note.** Syncthing-over-Tailscale touches no third party. GitHub (the
markdown brain) and R2 (the raw sources) are deliberate, accepted exceptions —
GitHub for the iOS bridge, R2 for the archive. The platform repo itself holds
no brain content at any point: the unit of privacy is the repo.

---

## 10. Interaction surfaces

*Implements `VISION.md` §4.*

The mind is reachable through three surfaces, each matched to the job it is
good at. The surfaces are harness capabilities (§5); the mind generates, the
harness delivers (§6.3).

- **Terminal (SSH over Tailscale)** — full-power, synchronous. The home base for
  deep work: long brainstorms, grant-drafting sessions.
- **Messaging (e.g. Telegram)** — asynchronous, lightweight. Excellent for
  *capture* (a voice memo of an idea, a "remind me about X") and
  *notification* (the morning brief, a deadline nudge). The ambient,
  always-in-pocket channel.
- **Obsidian** — the document-centric surface for grant drafting and
  project-scoped brainstorm threads, a direct view onto the brain (§9.1).

---

## 11. Scope boundary

*Implements `VISION.md` §6.*

A mnemo brain's domain is **your human's research program** — and nothing else.
Two things are out of scope, decided, not deferred: **personal-life content**
and **lab operations** (ordering, equipment logistics, managing the 1:1
cadence). Each is better served by a separate, independent setup. (The
exclusion was narrowed from an earlier "lab-state management" form: lab
capability knowledge — org structure, member expertise, project status — is
in scope as research-program knowledge.)

The boundary is kept structurally, not by a runtime filter: there is no page
kind for personal or lab-admin content (§2.2), and no skill cluster for it
(§4.2). The brain has nowhere to file it and no procedure to act on it. This is
scope discipline in service of quality — one *truly excellent* research
collaborator, not a broad assistant.
