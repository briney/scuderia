#!/usr/bin/env python3
"""feed-emit: daily-briefing summary card producer (committed content only).

Reads the rolling BRIEFING.md **as committed at the feed revision** and writes
one summary card to the instance's feed outbox. The briefing prose stays
canonical in the vault; the card is the glance layer (spec §11).

Since 2026-09-16 (git-ops migration) the producer is **read-only over Git**:

  - The feed revision is resolved ONCE per run: ``git rev-parse --verify
    HEAD`` (never the index, never the worktree).
  - BRIEFING.md, instance.yaml and brain.yaml are read from that commit's
    tree (``git ls-tree`` + ``git cat-file``), so dirty / staged /
    untracked content is invisible to the feed. If the vault sits below the
    repo toplevel, paths are resolved relative to the toplevel, so a path
    can never escape the committed tree.
  - A path absent from the committed tree means the old card is withdrawn
    (same semantics the file being absent on disk used to have).
  - Any Git or read error (unborn repo, corrupt objects, invalid plumbing
    output) PRESERVES the existing card and exits nonzero, so the feed-sync
    wrapper skips the sync step and the last pushed card stands. There is
    never a fallback to the worktree.
  - A symlink blob at the briefing path is rejected rather than followed.

Identity: the committed instance.yaml / brain.yaml ``name:`` wins; the
``FEED_INSTANCE`` env var overrides it.

Dismissal is content-addressed: a dismissed briefing stays hidden until the
briefing *content* changes (next day's brief reappears on its own). The
marker lives in the outbox .state/dismissed.json, written by mailbox-drain.

The card file is written atomically: JSON is staged to a temp file in the
outbox dir and os.replace()d into place, so the syncer never sees a torn
card.

Environment:
  VAULT_ROOT       vault root (required) — must live inside a Git work tree
  FEED_INSTANCE    instance name (overrides committed instance.yaml/brain.yaml)
  FEED_OUTBOX_DIR  outbox dir (default: <vault>/feed-outbox)
"""

import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

BODY_CAP = 3500  # under the 4000 contract cap, leaving room for the header
DISMISS_FILE = ".state/dismissed.json"
GIT_TIMEOUT = 60  # seconds; local plumbing should never take this long


class FeedEmitError(Exception):
    """Raised when the committed feed revision cannot be read safely."""


# --- read-only Git plumbing -------------------------------------------------

def _run_git(repo, args):
    """Run one read-only Git command; raise FeedEmitError on any failure."""
    cmd = ["git", "-C", str(repo)] + args
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=GIT_TIMEOUT)
    except subprocess.TimeoutExpired:
        raise FeedEmitError(f"git {args[0]} timed out after {GIT_TIMEOUT}s")
    except OSError as exc:
        raise FeedEmitError(f"git could not run: {exc}") from None
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise FeedEmitError(
            f"git {' '.join(args)} failed (rc={proc.returncode}): "
            f"{detail[:300]}")
    return proc.stdout


def repo_toplevel(repo):
    """Resolve repo to its absolute, symlink-resolved toplevel.

    Raises FeedEmitError if the path is not inside a work tree at all.
    """
    try:
        top = _run_git(repo, ["rev-parse", "--show-toplevel"]).strip()
    except FeedEmitError as exc:
        raise FeedEmitError(f"not a Git work tree: {repo}: {exc}") from None
    if not top:
        raise FeedEmitError(f"git returned no toplevel for {repo}")
    return pathlib.Path(os.path.realpath(top))


def rev_parse_head(repo):
    """Return the resolved HEAD commit id, or raise FeedEmitError.

    An unborn repo (fresh `git init`, no commits) deliberately fails here:
    there is no committed feed revision, so per contract the old card is
    preserved and the wrapper skips sync rather than emit uncommitted
    content.
    """
    return _run_git(repo, ["rev-parse", "--verify", "HEAD"]).strip()


def ls_tree_entry(repo, rev, path):
    """Return the tree entry dict for an exact path at a revision, or None.

    Uses the :(literal) pathspec so `*`, `?`, `..` are treated as literal
    name characters, never as glob/escape syntax. None means the path is
    absent from the committed tree — deliberately distinguishable from a
    Git error (which raises FeedEmitError).
    """
    out = _run_git(repo, ["ls-tree", rev, "--", f":(literal){path}"]).strip()
    if not out:
        return None
    if "\n" in out:
        raise FeedEmitError(f"ls-tree returned multiple entries for {path!r}")
    meta, _, name = out.partition("\t")
    parts = meta.split()
    if len(parts) != 3 or name != path:
        raise FeedEmitError(f"unexpected ls-tree output for {path!r}: {out!r}")
    return {"mode": parts[0], "type": parts[1], "oid": parts[2], "path": name}


def read_committed_blob(repo, rev, path):
    """Return the committed blob text for an exact path at a revision.

    Raises FeedEmitError for non-blob entries, symlink blobs (mode 120000),
    and unreadable objects. No worktree fallback exists by design.
    """
    entry = ls_tree_entry(repo, rev, path)
    if entry is None:
        raise FeedEmitError(f"read_committed_blob: {path!r} absent at {rev}")
    if entry["type"] != "blob":
        raise FeedEmitError(
            f"{path!r} is a {entry['type']}, not a blob — refusing")
    if entry["mode"] == "120000":
        raise FeedEmitError(f"{path!r} is a symlink blob — refusing to follow")
    return _run_git(repo, ["cat-file", "blob", entry["oid"]])


# --- identity ---------------------------------------------------------------

def instance_name(vault, git_read):
    """Instance name: FEED_INSTANCE env, else committed instance/brain.yaml."""
    env = os.environ.get("FEED_INSTANCE")
    if env:
        return env
    for fname in ("instance.yaml", "brain.yaml"):  # brain.yaml = legacy name
        data = git_read(fname)  # None is absent; Git failures must stop sync.
        if data is not None:
            m = re.search(r"^name:\s*(\S+)", data, re.M)
            if m:
                return m.group(1)
    return vault.name


# --- card assembly ----------------------------------------------------------

def _write_card_atomic(outbox, card_path, payload):
    """Write card JSON to card_path atomically (temp + os.replace)."""
    outbox.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(outbox), prefix=".card-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        os.replace(tmp, card_path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def main():
    raw_vault = os.environ.get("VAULT_ROOT", "")
    if not raw_vault:
        print("feed-emit(briefing): VAULT_ROOT is required", file=sys.stderr)
        return 2
    vault = pathlib.Path(raw_vault)
    if not vault.is_dir():
        print(f"feed-emit(briefing): VAULT_ROOT is not a directory: {vault!r}",
              file=sys.stderr)
        return 2
    outbox = pathlib.Path(
        os.environ.get("FEED_OUTBOX_DIR") or vault / "feed-outbox")

    # -- resolve the committed feed revision (worktree never consulted) ----
    try:
        top = repo_toplevel(vault)
        vault_resolved = vault.resolve()
        try:
            rel = vault_resolved.relative_to(top)
        except ValueError:
            raise FeedEmitError(
                f"VAULT_ROOT {vault} escapes its repository toplevel {top}")
        prefix = str(rel)
        rev = rev_parse_head(top)

        def committed(path):
            """Committed text at rev, or None when the path is absent."""
            full = f"{prefix}/{path}" if prefix and prefix != "." else path
            entry = ls_tree_entry(top, rev, full)
            if entry is None:
                return None
            return read_committed_blob(top, rev, full)

        inst = instance_name(vault, committed)
        briefing_text = committed("BRIEFING.md")
    except FeedEmitError as exc:
        print(f"feed-emit(briefing): git read failed — existing card "
              f"preserved, sync skipped: {exc}", file=sys.stderr)
        return 3

    card_id = f"{inst}/briefing/daily"
    out = outbox / (card_id.replace("/", "__") + ".json")

    # -- withdrawal: path absent from the committed tree -------------------
    if briefing_text is None:
        if out.exists():
            out.unlink()
            print("feed-emit(briefing): no BRIEFING.md — card withdrawn")
        else:
            print("feed-emit(briefing): no BRIEFING.md — nothing to emit")
        return 0

    text = briefing_text
    digest = hashlib.sha256(text.encode()).hexdigest()[:16]

    dismissed = {}
    try:
        dismissed = json.loads((outbox / DISMISS_FILE).read_text())
    except Exception:
        pass
    if dismissed.get(card_id) == digest:
        out.unlink(missing_ok=True)
        print("feed-emit(briefing): dismissed and unchanged — card held back")
        return 0

    date = dt.date.today().isoformat()
    m = re.search(r"\b(20\d\d-\d\d-\d\d)\b", text[:500])
    if m:
        date = m.group(1)

    body = text.strip()
    if len(body) > BODY_CAP:
        body = body[:BODY_CAP].rsplit("\n", 1)[0] + \
            "\n\n*(truncated — full brief in BRIEFING.md)*"

    card = {
        "card_id": card_id,
        "instance": inst,
        "profile": "mnemo",
        "type": "summary",
        "title": f"daily briefing — {date}",
        "body": body,
        "salience": 0.6,
        "source_ref": "BRIEFING.md",
        "actions": ["dismiss"],
        "state": "active",
    }
    try:
        _write_card_atomic(outbox, out, json.dumps(card, indent=1) + "\n")
    except OSError as exc:
        print(f"feed-emit(briefing): cannot write card: {exc}",
              file=sys.stderr)
        return 4
    print(f"feed-emit(briefing): {date} -> {out.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
