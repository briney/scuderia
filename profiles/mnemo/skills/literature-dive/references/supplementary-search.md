# Supplementary search — the axis-reframing method

Load for literature-dive Phase 6 (Prong 2b especially), or any time a
corpus's orthogonal axis is suspected missing. Core gap criteria, prong
rules, and the human gates stay in SKILL.md; this reference carries the
generalized method and worked example. Generalized from a worked dive
session (2026-09-05); private counts and quotations stay in the
instance record.

## The axis-reframing method

**The situation.** An application-seeded corpus — seeded from papers
about what systems *do* — can be structurally blind on the orthogonal
axis: how the systems are *built*. The reframing question: *is there
anything in the concept page that can guide a better search?*

**What worked:**

1. **The concept page already held the axis — it just had never been
   used as query vocabulary.** The orthogonal axis's concepts were all
   in the existing concept page, but no search had ever been framed on
   them. Read the page as a query seed, not just as a synthesis.
2. **The missing term was the field's own name for itself.** The
   highest-yield search term was in neither the concept page nor any
   ingested paper. Found by running one exploratory query and reading
   titles, then mining the anchor paper's related-work section, which
   cites the industry posts that coined the practice. Machinery-layer
   vocabulary often originates in industry blog posts, not papers.
3. **Run 6–10 plain-language semantic queries** on the reframed
   vocabulary. Example set for an infrastructure axis (adapt to the
   actual domain): agent harness design patterns; durable experiment
   tracking and observability; sandboxed execution infrastructure;
   externalizing agent state to databases or files; human oversight
   gates in production. Each query is phrased in plain language, not
   keyword syntax.
4. **Dedup and quantify.** Resolve source identities and compare exact
   identifiers with parsed paper metadata; substring hits are candidates,
   not final deduplication. Check relevance before measuring new-versus-known.
   A high new fraction can indicate missed coverage, a broadened topic, or
   false positives; read the evidence before attributing it to a structural
   blind spot. Surface the result to your human, who decides whether further
   work on that axis is warranted; the fraction is not an automatic trigger. If the
   new axis has grown to rival the original, propose the concept-page
   split gate (SKILL.md Phase 7) — the human's call, before ingestion
   begins.

**Why the initial pass missed it (structural, not sloppiness):**
application-seeded dives inherit the seed papers' citation biases —
systems authors under-cite infrastructure work their designs
implicitly re-implement. Semantic search framed on system capabilities
does not retrieve infrastructure papers that never use those words.
Query framing, not corpus absence, was the binding constraint.

**Paperclip output parsing.** `paperclip search` stdout is a numbered
human-readable table, not a list of `/papers/` paths — the parsing
contract (block-splitting, the id-line regex, the result-handle
reservation for `map --from`) is owned by the `paperclip-search` skill;
load it before writing any batch parser over search output.
