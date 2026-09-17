# EMFILE recovery

Load only after an actual “Too many open files” failure.

Historical macOS shard runs observed both parallel file-call failures and
host-wide file/shell/process failures lasting minutes. Individual retries
sometimes worked; some persistent-connection tools remained available.
Those observations do not guarantee recovery or establish a universal order.

Retry the failed operation once sequentially. If it recovers, keep file
operations sequential and verify any earlier write before repeating it.
For host-wide failure, make a bounded trivial `terminal("true")` probe after
30–60 seconds, only while time remains; stop after a few minutes at most.
Do not launch more workers or keep retrying indefinitely.

On exhaustion, record actual completed work and unfinished pages as partial.
If result-file writing is also blocked, return the entries and error to the
parent and state that no result file was saved. Do not bypass tool refusals
or use shell heredocs to evade the supported file-writing tools.
