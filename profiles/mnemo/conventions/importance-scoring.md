# Convention: importance scoring

Each page carries an `importance` score in `[0, 1]` — its **research salience**.
The score drives ranking in search and in the attention contract: a higher score
means a page surfaces sooner and is harder to bury. Authoritative source:
`DESIGN.md` §2.5.

## What the score is computed from

`importance` is derived from signals already present in the page — it is not a
hand-set opinion field:

- **Tag boost** over a research-relevant tag set: `controversy`,
  `novel-finding`, `methods-paper`, `seminal`, `contradicts-existing`,
  `key-citation`, `under-review`, `replication-target`. A page carrying these
  tags scores higher.
- **Annotation density and weight** — how much of Bryan's own thinking is on the
  page. A page he has argued with is more salient than a bare stub.
- **Graph centrality** — how connected the page is in the link graph
  (see `graph-and-links.md`). A hub page outranks a leaf.

## It is a maintenance pass, not hand-set

`importance` is **recomputed**, not authored. When a page is created, set a
reasonable initial value (or leave it for the recompute); the score is then
refreshed as a periodic maintenance pass over the whole corpus.

The mind owns no code, so the recompute is performed by the harness or by a
maintenance skill — an LLM pass that reads the signals above and writes the
score back to frontmatter. Treat the value in any given page as the last
recompute's output, not ground truth between passes.
