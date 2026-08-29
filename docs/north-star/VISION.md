# VISION.md — the scuderia platform

> **Status: v1.0 — the platform vision.** This is the big-picture vision for
> what a **scuderia** *is for*: a stable of AI agents, each built for its
> discipline, each driven by a human. It is deliberately
> implementation-light — the blueprint is `DESIGN.md` in this directory.
> Where the two disagree, *this* document is the intent and `DESIGN.md` is
> brought into line.
>
> The north-star documents are layered. *This* pair describes the platform:
> the stable, the driver, the machinery every agent shares. Each **profile**
> carries its own north-star pair describing its archetype — what that kind
> of agent is and how it is built (`profiles/<name>/VISION.md` and
> `DESIGN.md`; mnemo's is the flagship and the reference). Platform
> decisions live in §9 here; archetype decisions live with the profiles.
>
> Lineage: this document was split out of the mnemo archetype vision
> (2026-08-28), which had accreted the platform's claims by patch note.
> The split is itself a ratified decision — see §9.

---

## 0. What this document is

A vision, not a spec. It fixes *what a scuderia is for* and *how the human
relates to it* — the shape of the thing — before the argument about
profiles, contracts, and capability wiring begins. Implementation detail is
explicitly deferred to `DESIGN.md`.

---

## 1. The name, stated once

*Scuderia* is Italian for the stable a racing team fields: a roster of
finely tuned, high-performance cars, each built for its discipline — and
each, no matter how brilliant its engineering, driven by a human.

The metaphor is load-bearing in exactly one place, and it is stated here
once, plainly, so the rest of the document can get on with it: **the human
drives.** Everything else the metaphor offers — mechanical independence,
team coordination, room for a pit crew — is developed where it earns its
keep (§2, §3, §7).

---

## 2. The driver

This is the non-negotiable center of the platform, and it is meant
literally: **the human is the driver; the scuderia is an extension of the
human, never a replacement for one.**

The goal is not an autonomous system. A scuderia lets its human operate at
a tempo and a breadth that would otherwise be impossible — several agents
running in parallel, work continuing overnight, the literature swept while
the human sleeps — but speed is the means, not the end. The end is a human
whose reach is amplified: their program, their taste, their call.

Concretely, the driver owns:

- **The program.** What the work is *for* — the research directions, the
  priorities, what is in scope and what is out. Agents execute the program;
  they do not set it.
- **The user model.** The `USER/` spine that tells each agent who the
  driver is and how to work with them. Authored and refreshed by the
  human's hand.
- **Structural decisions.** New profiles, schema changes, skill
  crystallization from a doer's proposal, repo-level moves. Agents
  recommend; the driver decides.
- **Coordination.** Which agent runs what, when, and in what order. Agents
  may commission execution from one another through the agora (§6); they
  do not set one another's goals. One car drafts another because the
  team decided it — the cars do not conspire.

Agents do act unattended between sessions — scheduled jobs, ambient
capture, proactive notification. That is the engine, not the steering. A
car that drives itself to a destination it chose is not the product; it is
a different product, and not one this platform builds. Remove the driver
and the stable should not merely slow down — it should have nowhere to go.

---

## 3. The thesis: a stable, not a singleton

One agent that does everything is the obvious design, and it is wrong for
the same reason that three disconnected tools are wrong.

The mnemo archetype proved the first half: **within an agent, integration
is the product.** One mind with global context — the ideas, the
literature, the grants, the deadlines — is better at each of its jobs for
seeing the others. That collapse is real and it stays.

But the collapse has a boundary, and the boundary is what makes this a
platform. Different kinds of work want different *state shapes* (a
knowledge graph is not a capability library), different *characters* (a
thought partner's brutal honesty is not a craftsman's verification
discipline), and different *scopes of privacy and access*. Stretching one
agent across all of them produces a mediocre generalist with a muddled
soul. So the second half: **across agents, disciplined separation is the
product.**

Separation here is mechanical, not aspirational. Pressing the accelerator
in one car moves only that car: each agent's state, skills, and character
are entirely its own; no agent writes into another agent's repository;
there is no shared mutable state anywhere in the platform. What the agents
share is machinery (this kit), a driver, and one disciplined meeting place
(§6) — nothing else.

And separation is what lets each agent be *excellent*: a stable of
specialists, each tuned for its discipline, coordinated by the driver,
outperforms both the singleton generalist and the pile of disconnected
tools. The team is the product.

---

## 4. What an agent is

The platform's general category is the **agent**: a named instance of a
profile, run by a harness. An agent decomposes into four layers:

1. **Character** — who the agent *is*: voice, posture, the inviolable
   spine. Pure prose (`SOUL.md`).
2. **Skills** — how the agent *works* on a recognizable job. Markdown
   procedures.
3. **Capabilities** — what the agent *can do*: tool bindings, provided by
   the harness, named by skills.
4. **State** — what the agent *holds*: persistent markdown. **The shape of
   state is profile-defined** — a mnemo instance's state is a knowledge
   graph (a brain); an ergon instance's state is a capability library, a
   run log, and craft knowledge.

Vocabulary, ratified: **mind** is mnemo's self-description — a mnemo agent
is a mind because a thinker is what it is. **Doer** is ergon's. Not every
agent is mind-shaped, and the platform never uses one profile's
self-description as a general term.

**The cross-stable invariant is the spine.** Every agent, of any profile,
has a thin set of inviolable rules — absolute, script-like, never yielding
to the flow of a task — beneath a rich body of internalized dispositions.
The spine's *content* is the profile's own (a mind swears cite-or-flag; a
doer swears verify-every-artifact), but the *form* is platform law:
trustworthy first, brilliant second, and the spine never bends to preserve
rapport or to close a ticket. A stable is only as useful as its least
trustworthy agent's "done."

---

## 5. The stable today

Three profiles, at three different altitudes — which is itself a platform
value (below):

- **mnemo** — the *mind*: a scientific thought partner that also writes
  the grants and keeps research logistics on track. The flagship profile;
  its north-star pair (`profiles/mnemo/VISION.md`, `DESIGN.md`) is the
  reference for what a mature archetype looks like. First instance:
  atticus.
- **ergon** — the *doer*: a master craftsman. Holds no domain data;
  produces verified, provenance-carrying artifacts on commission. First
  instance: faber.
- **oiko** — the lab manager: budgets, compliance, procurement. A **stub
  by design**.

**Stub-by-design is platform law.** A profile template is built only when
someone is ready to run an instance of it — half-real templates rot, and a
rotted template is worse than none because it looks load-bearing. oiko's
README is the model: a stub names the archetype, states what a real
template must ship, and stops. Profiles are earned by a live instance,
never speculated into existence.

---

## 6. The agora — where the team meets

Agents of different kinds collaborate: a mind holds what is known, a doer
holds what can be done, and real work needs both. The **agora** is the one
place they meet — a shared artifact store plus the message conventions
around it, specified in `core/agora.md`.

The agora is designed so that collaboration never compromises separation:

- **The only shared writable surface.** No agent writes into another
  agent's repo, ever. If a doer's output is worth remembering, the mind
  ingests it through its own skills.
- **Artifacts, not state.** Agents exchange immutable, provenance-carrying
  deposits — what request made this, from what inputs, with what tools,
  how verified. Small messages carry pointers; big payloads travel by
  reference. Even here, there is no shared mutable state.
- **Truth/fidelity split.** The requester guarantees the input is correct;
  the executor guarantees the transformation is faithful and verified.
- **The driver stays in the loop.** Commissions flow from the human, or
  from an agent within a program the human set. Skill creation is gated on
  human approval through the proposal flow.

If the cars are mechanically independent, the agora is the team radio and
the pit lane — the channel through which driver-led coordination happens,
and the only one.

---

## 7. Room on the team

A race team is more than cars and a driver: pit crew, race engineers,
strategists — roles that keep the cars tuned and the campaign pointed at
wins. This vision deliberately leaves room for the stable to grow into a
full team, and is opinionated about *how* growth happens so the team stays
coherent:

- **A new kind of work — one with its own state shape, scope, and
  character — is a new profile.** Not a new mode on an existing agent;
  there are no modes (that is mnemo's settled law, and it generalizes).
  New profiles arrive as stubs and are fleshed out when an instance is
  ready (§5).
- **A new procedure inside an existing agent's job is a skill.** Skills
  are cheap, layered, and owned by the agent whose job they serve.
- **Machinery every agent shares is platform core.** The instance
  contract, the capability contract, the agora, the feed, the CLI.
- **Nothing grows by scope creep.** An agent that absorbs work outside
  its archetype is not being helpful; it is becoming a worse car.

Multi-instance is in scope from the start: instances are named; templates
are not. One driver may run several instances of one profile; the platform
does not assume one human per stable, only that every stable has a driver.

---

## 8. Privacy and ownership

**The unit of privacy is the repo.** The platform repo is public — it
holds no instance content at any point, by construction. Instance repos
are private forever. The agora is the controlled interface between agents,
and the driver's own sync fabric (§6 of `DESIGN.md`) is the only path
content takes between machines. Templates say "your human" and
`<instance>`, never a real instance's name, data, or paths.

---

## 9. Decision log

1. **A stable, not a singleton super-agent.** ✓ Resolved (§3): within an
   agent, integration is the product; across agents, disciplined
   separation is the product. Separation is mechanical — no shared mutable
   state, no cross-repo writes.
2. **Driver primacy.** ✓ Resolved (§2): the platform amplifies the human;
   it does not replace or route around them. Unattended operation is the
   engine, never the steering. Driverless is a non-goal.
3. **Platform vocabulary.** ✓ Resolved (2026-08-24): the general category
   is the **agent**; **mind** and **doer** are profile self-descriptions
   (mnemo's and ergon's), never platform terms. The instance contract file
   is `instance.yaml`.
4. **Profile-pluggable, not scope-extended.** ✓ Resolved (§5, §7): new
   kinds of work are new profiles; the platform machinery is
   profile-agnostic. oiko exists as the proof of the seam.
5. **Stub-by-design.** ✓ Resolved (§5): profiles are earned by a live
   instance; half-real templates rot.
6. **Privacy by repo.** ✓ Resolved (§8): the platform repo is public;
   instance repos are private forever; the agora is the only shared
   writable surface.
7. **The north-star documents are layered.** ✓ Resolved (2026-08-28):
   platform vision/blueprint at `docs/north-star/`; each profile carries
   its own pair. The previous single-pair arrangement — a mnemo-shaped
   vision genericized by patch notes — was straining under every platform
   decision; the split keeps each document's context tight and its
   revision cadence honest.

---

## 10. The shape, in one paragraph

A scuderia is a stable of AI agents — a mind that thinks, a doer that
makes, room for more — each mechanically independent, each excellent at
its discipline, each driven by the same human. The agents share machinery
and meet in one disciplined place; they never share state and never set
their own program. The bet is the team's: a driver with a stable of
specialists goes faster, further, than any single car — and the driver,
not the machinery, is always the one driving.
