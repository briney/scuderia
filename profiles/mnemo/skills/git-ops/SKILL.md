---
name: git-ops
description: Use when closing a verified work unit or saving reviewed edits.
triggers:
  - "commit and push this work"
  - "save my edits"
  - "review uncommitted changes"
  - a completed persistent-writing operation with no parent closeout owner
eval_contract:
  goal: |
    Preserve each coherent, verified work unit in an informative commit and
    publish only authorized history, without including unrelated edits.
  dimensions:
    - "OWNERSHIP — do staged paths and hunks belong to this operation?"
    - "COHERENCE — is the unit complete, validated, and independently understandable?"
    - "HISTORY — does the message explain the change without rewriting existing commits?"
    - "PUBLICATION — is the intended commit verified on the authorized remote?"
  hard_fails:
    - Committing unrelated, unfinished, private-to-another-repo, or unreviewed human edits.
    - A child worker changing the shared index, branch, or remote.
    - Claiming publication without remote verification.
    - Automatic history rewriting, destructive recovery, or broad staging.
---

# Git operations

The caller owns the work, its completion boundary, and domain validation.
This skill owns Git closeout. Load it at a persistent-writing boundary, not
for every read. It does not grant permission to edit, commit, or publish:
follow the repository's standing authorization and the current request.

## Input and owner

The caller supplies the repository, exact changed paths (and hunks if mixed),
completed unit, validation results, message, and execution mode.

- **Standalone:** the invoking agent owns closeout.
- **Child or nested skill:** return changed paths, evidence, and remaining
  obligations to the parent. Do not stage, commit, pull, push, or change branches.
- **Orchestrated campaign:** the parent closes each coherent verified unit;
  a dispatch batch alone is not a completion boundary. Complete parent-owned
  author/link/index updates first. Synthesis may be a separate later commit.
- **Scheduled phase:** the phase primary closes its edits plus result file;
  an aggregator closes only its reports/state. Follow the phase's scope rules.

One Git writer at a time per shared checkout. Wait for other writers; never
stage while your workers are changing the unit's files. Independent sessions
must coordinate exclusive Git access or use isolated worktrees. An index lock
on one Git command is not ownership of the whole closeout. If exclusivity or
same-file ownership is uncertain, stop rather than stage somebody else's work.

## Procedure

1. **Establish scope.** Resolve the actual repository root, branch, upstream,
   and approved remote. Record HEAD, staged changes, and pre-existing worktree
   changes at operation start; re-read before closeout. Follow repo privacy
   rules. Never collect every dirty file merely because it is present.
2. **Verify the unit.** Run the caller's checks on its actual output. A rename
   includes repaired references; ingestion includes required wiring. Preserve
   pilot/review gates. A failed check holds the unit, not just the bad file.
   Record unrelated baseline failures separately; never call a failed check passed.
3. **Review and stage narrowly.** Inspect diffs for owned paths. Exclude caches,
   raw sources, secrets, and unrelated edits. Stage explicit paths or reviewed
   hunks; never `git add .`, unscoped `git add -A`, or `git commit -a`. If the
   index contains unrelated changes, do not commit or unstage them. Coordinate
   with their owner. Re-read files changed since validation; validate again.
4. **Inspect the staged result.** Check the entire staged diff and path list,
   including deletions, not only a stat. Run `git diff --cached --check`.
   For hunk-only staging, validate the staged version as well as the worktree:
   their content differs. Any unexpected path or hunk holds the commit.
5. **Commit.** Use the message format below. Read back the new commit's hash,
   subject, and diff; confirm it includes exactly the reviewed unit. No diff
   means no commit. Do not amend old commits to improve their messages.
6. **Publish when authorized.** Fetch the approved upstream and inspect the
   entire unpublished range. A push publishes ancestor commits too; hold if
   that range contains unrelated/unapproved work. Push the explicit branch
   to its approved remote without force. On divergence, preserve the local
   commit and report the block; no automatic pull/rebase, stash, or reset in
   a dirty shared checkout. Resolve integration deliberately in isolated work.
7. **Verify and report.** Read the remote branch back. Confirm it contains the
   intended commit (exact tip or verified ancestor if it advanced). Report
   written/validated/committed/pushed separately, with hash and meaningful
   limitations. A failed push leaves a valid local commit; retry publication,
   not the content edit or commit. No scheduled snapshotter finishes the job.

All Git-changing commands are conditional on successful preceding checks;
never use `;` to commit through a failed validation. Do not restore shared
files wholesale to HEAD as generic error recovery. Preserve current bytes
and recover only proven damaged changes with their owner's authorization.

## Messages

Subject: `operation(scope): concrete change`, concise enough to scan in a log.
Use ordinary operations such as ingest, update, fix, synthesize, refactor,
and maintain; the vocabulary is not a rigid enum. Scope names the subject
or subsystem. State the result, not "update files" or a timestamp.

Examples (illustrative, not execution records):

- `ingest(paper): add study and its required graph links`
- `fix(author-ledger): separate same-name authors by affiliation`
- `update(grant-aims): make the second aim independently executable`
- `refactor(paper-ingest): centralize author-ledger updates`

For a nontrivial change, add a short body: why it was needed; material scope
and deliberate exclusions; checks actually run; any relevant limitation.
Do not paste tool logs or claim unrun tests. Tiny corrections need no
boilerplate body. Run dates/counts belong in artifacts or the body when useful;
they are not a substitute for describing the result. Related files can share
one commit; independent operations should not be bundled for convenience.

## Saving human edits

On "save my edits", inspect the diff without rewriting it. Group related
changes and propose subjects and paths. Do not infer who wrote a hunk from
mtime. Get approval for the proposed groups unless the request already names
and authorizes the exact changes. Then validate and close those groups.
Protected human-owned files may be committed as reviewed human edits but must
not be rewritten by the agent. Mixed or ambiguous changes remain untouched.
Never run this mode on a timer. A backup or read-only dirty-tree reminder is
separate from committing; this skill installs neither.

## Scope and verification

The caller supplies domain tests, frontmatter lint, source/read-back checks,
and any pre-push repository gate. Git success is not content verification.
Feed publication, indexing, messaging, and backups have separate owners;
this skill neither invokes them nor treats their failures as Git failures.

Edits to this skill require a read-back against these rules and a disposable
Git-repository exercise: narrow staging, unrelated-dirt preservation, no-op,
commit read-back, rejected publication, and remote verification. Never test
recovery or force-push behavior against the live vault.
