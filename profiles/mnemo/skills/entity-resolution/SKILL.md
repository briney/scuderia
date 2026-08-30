---
name: entity-resolution
description: >
  Find pages and ledger entries that denote the same real-world thing and
  merge verified duplicates — and split an entry that has silently fused two
  distinct people when the disambiguation is mechanical. The dedup pass for
  the identity-keyed kinds (papers, people, institutions, methods) and the
  author ledger. Runs standalone ("find duplicates", "audit the ledger") or
  as rem-cycle phase 3.
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
> `skills/conventions/quality.md` (the notability gate). The merge mechanism and the
> MECE line both come from `concept-synthesis` — see *Scope* below.

## Capabilities

`brain-search`, `brain-read`, `brain-write`. Under the binary gate
(`rem-cycle-contract.md`, 2026-08-15), `brain-write` is used for **verified**
identity operations: pairwise-verified same-key merges, exact-duplicate ledger
cleanup, and mechanically unambiguous splits. Anything short of verified
**drops** (counted) or becomes a `notable:` signal — there is no propose lane.

## Scope — and the line against `concept-synthesis`

`concept-synthesis` dedupes `concept` and `note` pages — your human's evolving ideas —
and owns the merge mechanism: fold the duplicate's wikilinks and typed edges into
one canonical page, preserve alternate names in an `aliases:` frontmatter list,
never hand-write a backlink. This skill reuses that mechanism on a different
domain: the **identity-keyed** kinds — `paper` (key `doi`/`pmid`), `person` (key
`orcid`), `institution`, `method` — and the **author ledger**
(`people/_ledger.yaml`). A duplicate `concept` → `concept-synthesis`; a duplicate
paper, author, institution, or ledger entry → here.

## What this guarantees

- **Verified identity commits; unverified identity drops.** A merge commits when
  identity is *verified*: an exact key match (identical `doi`/`pmid`/`orcid`),
  confirmed by re-reading both frontmatters — any key difference, even
  formatting, is NOT verified. A same-name **permutation** (reordered identical
  token multiset, `crotty-shane` ↔ `shane-crotty`, modulo middle initials)
  commits only with corroboration on the pages (shared affiliation or
  co-authors); a bare permutation with no corroboration, and coincidental
  **name-similarity** (different token sets), drop — or become a `notable:`
  entry when both nodes are heavily linked and the pair looks important.
- **Same-DOI true duplicates are the common case.** Two `papers/` pages with an
  identical `doi` (verified pairwise) merge in-phase: fold aliases, union
  edges/tags, rewrite inbound references vault-wide, append a dated merge note,
  remove the duplicate page. Folding N inbound `[[slug]]` references is a
  corpus-wide rewrite (`graph-and-links.md`) — git-reversible, and part of the
  same commit.
- **The ledger is high-risk** (your human-owned, corruption-prone). Before any ledger
  write: round-trip load the YAML (parse → re-serialize; it must stay
  well-formed), run `lint-frontmatter.py --instance <brain> --paths people/_ledger.yaml`
  (the linter parses the ledger),
  and diff to confirm **only** the intended entries changed. Abort on any surprise.
- Every committed merge/split carries evidence: the shared key, verified.

## The two directions

### Merge — one thing, many nodes

1. **Cluster (cheap).** Group `paper` pages by `doi`/`pmid`; `person` pages and
   ledger entries by `orcid`; all kinds by normalized slug/name; add
   `brain-search` neighbours and shared-neighbour pairs. This is the shortlist.
2. **Adjudicate (shortlist).** Exact key match (same `doi`, same `orcid`),
   re-verified by reading both frontmatters → same entity, commit-eligible.
   **Same-name permutation** (reordered identical token multiset) →
   commit-eligible only with on-page corroboration (affiliation, co-authors);
   bare permutation → drop or `notable:`. Coincidental name/neighbour match
   with no key and no permutation → drop. Same key but **conflicting**
   referents (two titles on one `doi`, two names on one `orcid`) is a
   **key-conflict**, not a merge — see below.
3. **Commit the merge** (verified pairs only). Choose the canonical
   by priority: (1) the **paged** node over a ledger entry or stub; (2) the node
   whose identity key is **correct/consistent** over one with a known defect (a
   slug whose year contradicts its `doi`); (3) the **fuller / more inbound-linked**
   node (this also minimizes the rewrite). Fold the duplicate's `authors:` /
   `cites:` / `links:` and body wikilinks into canonical, add its title and slug
   to canonical `aliases:`, rewrite the inbound references (forward-only —
   never a hand-written backlink), append a dated `## Merge note`, remove the
   duplicate page, and validate the merged frontmatter parses — all in one
   commit. Record `canonical`, `duplicate`, and `rewrite_refs: N` in the
   `committed[]` entry. If the chosen canonical carries a **known defect**
   (e.g. wrong-year slug), emit a `notable:` key-conflict alongside — a merge
   must not silently enshrine a bad key.
   - **Exact-duplicate ledger entries** (two entries under the *same* slug, or
     byte-identical entries): commit — union the `citations:` (deduped), keep
     one under the canonical slug, drop the other; validate per *What this
     guarantees* first. This is the `ovchinnikov` / `cho-yehlin` corruption
     class. A same-`orcid`/*different*-slug pair without corroboration drops
     or goes `notable:`.

### Split — many things, one node

A ledger entry or `person` page whose citations span **conflicting** ORCIDs or
affiliations has fused two people — the author-ledger's feared failure, where a
promotion fires on a non-person. **Commit the split only when the
disambiguation is mechanical** — the citations partition cleanly by
ORCID/affiliation with no residue — into disambiguated slugs
(`<surname-first>-orcid-<orcid>`, or an institutional tail, per
`author-ledger.md`); record `into: [slugA, slugB]` in `committed[]`. Both
members get disambiguated together, never one bare. Any residue or guesswork →
`notable:` (a fused person is worth attention) — never split on a guess.

### Key conflict — one identifier, two referents

The mirror of a duplicate: one `doi` / `pmid` / `orcid` attached to **two
distinct** real-world things (two papers sharing a `doi`; two people sharing an
`orcid`). This is a **mis-assigned key**, not a merge and not a split — merging
would fuse two real things. Correcting it needs an external lookup (waking
work), so a key-conflict is always a `notable:` entry naming the conflicting
referents — never a page edit.

## As a rem-cycle phase

Runs as its own cron job under `rem-cycle-contract.md` (binary gate). Emit the
fenced-yaml phase result — `committed[]` (verified merges, mechanical splits,
exact-duplicate ledger cleanup, each with evidence), `notable[]` (unverifiable-
but-important pairs, key-conflicts, promotion-eligible ledger entries),
`metrics` (`clusters_examined`, `merges_committed`, `splits_committed`,
`key_conflicts`, `ledger_dedups`, `dropped`). Cheap clustering scans all
identity keys; the expensive adjudication respects the mutation budget —
process the highest-certainty clusters first and report the rest in
`skipped[]`. No `cursor` (clustering is a full-key scan, not a rotation). No
chaining.

**Promotion gate.** If a merge lifts a unified ledger entry's `len(citations)`
past the `≥ 5` threshold (`author-ledger.md`), do **not** promote — that is
`enrich`'s job. Emit a `notable:` entry for promotion-eligibility and stay
in-lane.

## Output

- **As a phase:** the fenced-yaml phase result.
- **Standalone:** the verified merges/splits committed (with the diff shown),
  and the notable observations reported inline.

## Anti-patterns

- Merging on *coincidental* name similarity (different token sets, or a common
  name) with no key or corroboration — drop it.
- Committing a merge you have NOT verified pairwise by re-reading both
  frontmatters — an unverified merge is a drop, not a commit.
- Writing `people/_ledger.yaml` without validating the YAML and diffing first.
- Deduping `concept` / `note` pages here — that is `concept-synthesis`.
- Hand-writing a backlinks section when folding edges — inbound edges are derived.
- Splitting or merging a person with no ORCID/affiliation evidence — a guess
  corrupts the authorship graph.
- Mixing a disambiguated slug with a bare one for the same collision pair
  (`author-ledger.md`).
