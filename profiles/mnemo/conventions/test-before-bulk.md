# Convention: test before bulk

Never run a batch operation over the brain without testing one item first.

## The Process

1. **Read the skill first.** Don't improvise. If a skill exists, follow it.
2. **Hone the logic.** Get the page format and the framing right before running anything.
3. **Test on 3-5 items.** Produce the pages but hold the commit.
4. **Check the work yourself.** Read the actual output. Is the quality pristine? Titles sharp? `kind` and frontmatter correct? Links forward-only and resolving? Citations present or honestly flagged?
5. **Fix what's wrong.** Update the skill, not the one-off output. The skill is the durable artifact.
6. **Only then: bulk execute.** Commit in batches so a bad run is easy to revert.

## Why This Matters

One bad bulk run can write 170 mediocre pages that are harder to fix than to do
right the first time. The marginal cost of testing 5 first is near zero. The cost
of cleaning up a bad bulk run is enormous.

## Applies To

- Enrichment passes over many pages
- Brain backfill and migration operations
- Any cron job being scheduled for the first time
- Any new skill being run at scale
- Ingestion of a large `_drop/` batch

## Anti-Patterns

- Improvising instead of following an existing skill
- Running 170 items without testing 5 first
- Skipping the link/citation pass "as a separate step"
- Committing bulk work without reading the output
- "I'll fix the quality later"
