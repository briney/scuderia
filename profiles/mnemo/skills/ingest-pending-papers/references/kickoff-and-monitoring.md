# Queue kickoff and monitoring

For an ordinary queue run:

```text
Run ingest-pending-papers for a bounded group of queued papers. Load its current
instructions and paper-ingest. Use the named YAML scanner, current runtime
schema and child ceiling. Workers stage; the parent verifies source evidence,
publishes, completes shared wiring and closes verified units through git-ops.
Report every input and all remaining work. Do not expand an explicit selection.
```

Check the tool stream and durable artifacts:

- Selected inputs appear in a dispatched wave or a specific hold/defer record.
  Inline execution is valid when chosen; narration is not proof of delegation.
- Workers do manuscript reading and stage only their assigned paper. The parent
  reads returned draft/review/source artifacts, publishes and owns shared writes.
- PAGE_READY points to an external draft. Do not expect the live page to change
  before publication. Inspect runtime status even if a child summary is missing.
- Completion requires runtime complete, required integration, a remote archive
  pointer and verified Git closeout. An interrupted provider message or push
  failure calls for artifact reconciliation, not another source/model pass.

An explicit corpus-refresh selection is separate from the ordinary stub queue.
Never run both primaries concurrently against shared author/graph files.
