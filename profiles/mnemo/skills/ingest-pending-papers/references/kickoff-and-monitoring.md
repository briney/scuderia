# Running this skill — kickoff and monitoring (for the user)

This reference is for the *user* invoking the drain, not for the
orchestrator running it. The orchestrator already has its instructions in
`ingest-pending-papers/SKILL.md`. Load it when you are the human kicking
off a drain from chat, or watching a running drain's tool stream.

## Kickoff prompt (paste verbatim at session start)

```
Run ingest-pending-papers. Prefer isolated paper workers and the current
runtime schema/ceiling. Read back returned artifacts, including failures and
PAGE_READY results. Complete shared wiring and final checks before clearing
needs-ingest or counting SUCCESS. Report any work deferred by the run budget.
```

Verify execution in the tool stream; a promise of delegation alone does
not establish that a worker ran.

## Monitoring signals from the tool stream

Three observable invariants tell you the orchestrator is doing what it
claims, regardless of what its prose says:

1. **One `delegate_task` call per batch.** The tool-call telemetry is
   authoritative. Every selected item must appear in a dispatched wave
   or an explicit hold/defer record; use the runtime ceiling, not a fixed
   batch-size formula. A drain claiming delegated fills without any
   delegation calls did not execute its contract.
2. **Full extraction stays in workers.** The parent receives result paths
   and reads the evidence needed for verification, rather than duplicating
   each worker's entire extraction conversation. Parent page/source
   read-backs are required verification, not evidence of unnecessary repeated
   extraction; inspect who performed the actual per-paper extraction/write.
3. **Phase 4 read-backs are visible.** After each batch returns, you
   should see `read_file` calls against the just-filled stub pages — one
   per returned item, including PAGE_READY and reported failures. No
   read-back means no verified outcome.

These three signals are independent of model size, prompt fidelity, and
the orchestrator's own narration. When they all hold, the drain is honest.
