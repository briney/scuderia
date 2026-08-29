# AGENTS.md — working in {{INSTANCE_NAME}}

{{INSTANCE_NAME}} is a **mnemo instance**: a pure-markdown research brain — a
knowledge graph, a character, and a set of skills — running on the scuderia
platform. A harness loads this directory and runs it; when it does, it *is*
{{INSTANCE_NAME}}.

This file carries only instance-level orientation. Platform-level norms (the
privacy rule, the capability contract, how profiles and templates work) live
in the scuderia repo's `AGENTS.md` — read it when working on the platform itself.

## The layers

| Layer | What it is | Where |
|---|---|---|
| **Character** | Who {{INSTANCE_NAME}} is | `SOUL.md`, `STYLE.md` |
| **User model** | Who your human is — owned and hand-maintained by them | `USER/<name>.md` (declared spine) + `USER/OBSERVATIONS.md` (derived) + `USER/VOICE.md` (derived) |
| **Program state** | The research program: domains, threads, funding | `RESEARCH.md` (read explicitly when a task needs program context) |
| **Brain** | The knowledge graph | the page directories |
| **Skills** | How {{INSTANCE_NAME}} works on a recognizable job | bound from the profile — see below |

## The brain

Every page is one markdown file with YAML frontmatter, filed by kind into the
page directories (`papers/`, `concepts/`, `grants/`, …). The conventions are
authoritative and live in the **mnemo profile** (`profiles/mnemo/conventions/`
in the bound scuderia checkout): page kinds, frontmatter schema, graph and links,
importance scoring. `instance.yaml` at this root declares the binding; `scuderia
doctor` validates it.

Skills are layered — platform < profile template < instance (`skills/` here,
for instance-private skills) — merged by name. How they reach the session is
harness-specific: see `docs/harnesses/<your-harness>.md` in the scuderia
checkout. The profile's `skills/RESOLVER.md` routes a request to a skill.

## Norms

- Never blind-overwrite a file: read current state first; if it was edited
  very recently, append or hold rather than clobbering.
- Commit finished units of work promptly with descriptive messages.
- `USER/<name>.md` is human-owned: never write it. Candidate observations go
  to `USER/OBSERVATIONS.md` via the `user-model-reflect` skill, on manual
  invocation only.
- Scope: this brain's domain is the research program. What is out of scope is
  defined in `USER/<name>.md` and enforced structurally by the absence of a page
  kind for it.
