---
name: entity-resolution
description: >
  Find pages and ledger entries that denote the same real-world thing and
  propose the merge — and split an entry that has silently fused two distinct
  people. The dedup pass for the identity-keyed kinds (papers, people,
  institutions, methods) and the author ledger. Runs standalone ("find
  duplicates", "audit the ledger") or as rem-cycle phase 3.
triggers:
  - "find duplicate pages"
  - "dedupe the brain"
  - "audit the author ledger"
  - "resolve entities"
  - "are these two the same"
---

# Entity resolution — one real-world thing, one node

Growth accretes duplicates: the same paper ingested twice under two slugs, one
author split across two ledger entries, a method named two ways. Each duplicate
splits a graph that should converge. This pass finds nodes that denote the same
real-world thing and proposes the merge — and catches the mirror failure, a
single node that has silently fused two distinct people.

> **Conventions:** `rem-cycle-contract.md` (tiers, the phase result),
> `author-ledger.md` (the ledger schema, ORCID disambiguation, the collision
> rules this audits), `graph-and-links.md` (folding edges, forward-only, derived
> backlinks), `frontmatter.md` (the identity keys — `doi`/`pmid`/`orcid`),
> `conventions/quality.md` (the notability gate). The merge mechanism and the
> MECE line both come from `concept-synthesis` — see *Scope* below.

## Capabilities

`brain-search`, `brain-read`, `brain-write`. `brain-write` is used **auto** only
for exact-duplicate ledger cleanup (validated + diffed); every page merge and
every split is *proposed*, not executed here.

## Scope — and the line against `concept-synthesis`

`concept-synthesis` dedupes `concept` and `note` pages — Bryan's evolving ideas —
and owns the merge mechanism: fold the duplicate's wikilinks and typed edges into
one canonical page, preserve alternate names in an `aliases:` frontmatter list,
never hand-write a backlink. This skill reuses that mechanism on a different
domain: the **identity-keyed** kinds — `paper` (key `doi`/`pmid`), `person` (key
`orcid`), `institution`, `method` — and the **author ledger**
(`people/_ledger.yaml`). A duplicate `concept` → `concept-synthesis`; a duplicate
paper, author, institution, or ledger entry → here.

## What this guarantees

- **Distinguish name-identity from name-similarity.** Two nodes whose names are
  the **same normalized token multiset reordered** — a permutation, `crotty-shane`
  ↔ `shane-crotty`, modulo middle initials — denote the same person: **propose the
  merge on the permutation alone** (confidence scaled by how common the name is).
  Coincidental **name-similarity** — a shared string across *different* token
  sets, or a common name with no permutation ("John Smith (investor)" vs
  "(contractor)") — still requires an identity key (`doi`, `orcid`) or
  corroboration (affiliation, co-authors). Never auto-merge either; both propose.
- **A page merge is proposed, never auto-executed — except same-DOI true
  duplicates.** Two `papers/` pages with an identical `doi` (verified pairwise
  by re-reading both frontmatters) auto-merge per Bryan's standing grant
  (2026-08-04, `rem-cycle-contract.md` § Graduated autonomy). Everything else —
  name permutations, name-similarity with corroboration, key-conflicts — still
  proposes. Folding N inbound `[[slug]]` references is a corpus-wide rewrite
  (`graph-and-links.md`); for non-same-DOI cases it is a judgment call. Only
  exact-duplicate *ledger* cleanup auto-commits besides.
- **The ledger is high-risk** (Bryan-owned, corruption-prone). Before any ledger
  write: round-trip load the YAML (parse → re-serialize; it must stay
  well-formed), run `.github/scripts/lint-frontmatter.py` (it parses the ledger),
  and diff to confirm **only** the intended entries changed. Abort on any surprise.
- Every merge, split, or key-conflict proposal carries evidence: the shared key,
  or the conflicting one.

## The two directions

### Merge — one thing, many nodes

1. **Cluster (cheap).** Group `paper` pages by `doi`/`pmid`; `person` pages and
   ledger entries by `orcid`; all kinds by normalized slug/name; add
   `brain-search` neighbours and shared-neighbour pairs. This is the shortlist.
2. **Adjudicate (shortlist).** Exact key match (same `doi`, same `orcid`) → high
   confidence, same entity. **Same-name permutation** (reordered identical token
   multiset) → propose on that alone (see *What this guarantees*). Coincidental
   name/neighbour match with no key and no permutation → require corroboration;
   absent that, do not propose. Same key but **conflicting** referents (two
   titles on one `doi`, two names on one `orcid`) is a **key-conflict**, not a
   merge — see below.
3. **Propose the merge** with a structured plan, not prose. Choose the canonical
   by priority: (1) the **paged** node over a ledger entry or stub; (2) the node
   whose identity key is **correct/consistent** over one with a known defect (a
   slug whose year contradicts its `doi`); (3) the **fuller / more inbound-linked**
   node (this also minimizes the rewrite). Emit `canonical`, `duplicate` (or
   `sources: [...]`), `rewrite_refs: N` (the inbound `[[duplicate]]` count — the
   blast radius), and the fold plan: fold the duplicate's `authors:` / `cites:` /
   `links:` and body wikilinks into canonical, add its title and slug to canonical
   `aliases:`, rewrite the inbound references (forward-only — never a hand-written
   backlink). If the chosen canonical carries a **known defect** (e.g. wrong-year
   slug), emit a follow-up `key-conflict` alongside — a merge must not silently
   enshrine a bad key.
   - **Exception — exact-duplicate ledger entries** (two entries under the *same*
     slug, or byte-identical entries): **auto** — union the `citations:`
     (deduped), keep one under the canonical slug, drop the other; validate per
     *What this guarantees* first. This is the `ovchinnikov` / `cho-yehlin`
     corruption class. A same-`orcid`/*different*-slug pair, or a same-name
     permutation, is still **proposed** (choosing the canonical slug is a
     judgment).

### Split — many things, one node

A ledger entry or `person` page whose citations span **conflicting** ORCIDs or
affiliations has fused two people — the author-ledger's feared failure, where a
promotion fires on a non-person. Detect it and **propose** a split into
disambiguated slugs (`<surname-first>-orcid-<orcid>`, or an institutional tail,
per `author-ledger.md`) — emit `into: [slugA, slugB]`. Both members get
disambiguated together, never one bare.

### Key conflict — one identifier, two referents

The mirror of a duplicate: one `doi` / `pmid` / `orcid` attached to **two
distinct** real-world things (two papers sharing a `doi`; two people sharing an
`orcid`). This is a **mis-assigned key**, not a merge and not a split — merging
would fuse two real things. Detect it (same key, conflicting titles / names) and
**propose a `key-conflict`**, routing the wrong key to `frontmatter-guard` /
`citation-fixer` for re-resolution.

## As a rem-cycle phase

Under the orchestrator (`rem-cycle-contract.md`): the orchestrator passes `mode`
(dry-run | normal); emit the fenced-yaml phase result — `committed[]`
(exact-duplicate ledger cleanup only), `proposed[]` (every page merge, split, and
key-conflict, with evidence, confidence, `target_exists`, and the
merge/split/key fields above), `metrics` (`clusters_examined`, `merges_proposed`,
`splits_proposed`, `key_conflicts`, `ledger_dedups`). Cheap clustering scans all
identity keys; the expensive adjudication respects the mutation budget — process
the highest-confidence clusters first and report the rest in `skipped[]`. No
`cursor` (clustering is a full-key scan, not a rotation). No chaining — the
orchestrator routes.

**Promotion gate.** If a merge lifts a unified ledger entry's `len(citations)`
past the `≥ 5` threshold (`author-ledger.md`), do **not** promote — that is
`enrich`'s job. Flag promotion-eligibility in the proposal and stay in-lane.

## Output

- **As a phase:** the fenced-yaml phase result.
- **Standalone:** the merges and splits proposed inline for Bryan, plus any
  exact-duplicate ledger cleanup applied — with the diff shown.

## Anti-patterns

- Merging on *coincidental* name similarity (different token sets, or a common
  name) with no key or corroboration — but note a same-name **permutation** (an
  identical name reordered) *is* propose-eligible on its own.
- Auto-executing a page merge — the reference rewrite is corpus-wide; propose it.
- Writing `people/_ledger.yaml` without validating the YAML and diffing first.
- Deduping `concept` / `note` pages here — that is `concept-synthesis`.
- Hand-writing a backlinks section when folding edges — inbound edges are derived.
- Splitting or merging a person with no ORCID/affiliation evidence — a guess
  corrupts the authorship graph.
- Mixing a disambiguated slug with a bare one for the same collision pair
  (`author-ledger.md`).
