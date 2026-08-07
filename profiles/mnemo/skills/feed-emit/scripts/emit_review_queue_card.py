#!/usr/bin/env python3
"""feed-emit: rem-cycle review-queue card producer.

Reads QUEUE.md (the rem-cycle review surface) and writes one review card to
the instance's feed outbox. The syncer (soma interface/syncer) validates and
pushes it; this script never talks to the network.

Contract notes:
  - item_id is the queue qid — already a stable hash, already what Bryan
    recognizes. Re-emitting an unchanged qid updates in place; an item that
    leaves the queue (drained, resolved) leaves the card on next sync.
  - Unchecked items (- [ ]) only. Checked/rejected lines are history.
  - Snoozed items (outbox .state/snoozes.json, written by mailbox-drain) are
    held out of the stack until their snooze elapses.
  - Empty queue = empty stack, not an absent card (dashboard stability).

Environment (all have sane defaults relative to VAULT_ROOT):
  VAULT_ROOT       vault root (required)
  FEED_INSTANCE    instance name (default: brain.yaml `name:` at vault root)
  FEED_OUTBOX_DIR  outbox dir (default: <vault>/feed-outbox)
  QUEUE_PATH       default: <vault>/docs/rem-cycle/QUEUE.md
"""
import datetime as dt
import json
import os
import pathlib
import re
import sys

ITEM_RE = re.compile(r"^- \[(?P<box>[ x~])\] `(?P<qid>[0-9a-f]{4})` \*\*(?P<kind>[^*]+)\*\* · (?P<text>.*)$")
SNOOZE_FILE = ".state/snoozes.json"


def instance_name(vault):
    env = os.environ.get("FEED_INSTANCE")
    if env:
        return env
    brain = vault / "brain.yaml"
    if brain.exists():
        m = re.search(r"^name:\s*(\S+)", brain.read_text(), re.M)
        if m:
            return m.group(1)
    return vault.name


def load_snoozes(outbox):
    f = outbox / SNOOZE_FILE
    try:
        return json.loads(f.read_text())
    except Exception:
        return {}


def parse_queue(queue_path):
    """Return list of (qid, kind, text, body, lineno) for unchecked items."""
    lines = queue_path.read_text().splitlines()
    items = []
    i = 0
    while i < len(lines):
        m = ITEM_RE.match(lines[i])
        if not m:
            i += 1
            continue
        body_lines = []
        j = i + 1
        while j < len(lines) and lines[j].startswith("      "):
            body_lines.append(lines[j].strip(" ·"))
            j += 1
        items.append((m.group("qid"), m.group("kind"), m.group("text"),
                      "\n".join(body_lines), i + 1, m.group("box")))
        i = j
    return items


def main():
    vault = pathlib.Path(os.environ["VAULT_ROOT"])
    outbox = pathlib.Path(
        os.environ.get("FEED_OUTBOX_DIR", vault / "feed-outbox"))
    queue_path = pathlib.Path(
        os.environ.get("QUEUE_PATH", vault / "docs/rem-cycle/QUEUE.md"))
    inst = instance_name(vault)
    card_id = f"{inst}/remcycle/review-queue"
    outbox.mkdir(parents=True, exist_ok=True)

    if not queue_path.exists():
        print(f"feed-emit(queue): no QUEUE.md at {queue_path}", file=sys.stderr)
        return 1

    now = dt.datetime.now(dt.timezone.utc)
    snoozes = load_snoozes(outbox)

    items = []
    seen_qids = set()
    for qid, kind, text, body, lineno, box in parse_queue(queue_path):
        if box != " ":
            continue  # checked/rejected lines are history, not stack items
        seen_qids.add(qid)
        until = snoozes.get(qid)
        if until and until > now.isoformat():
            continue  # snoozed — held out of the stack
        title = f"{kind}: {text}"
        items.append({
            "item_id": qid,
            "title": title[:297] + "..." if len(title) > 300 else title,
            "body": body[:1000] if body else None,
            "source_ref": f"docs/rem-cycle/QUEUE.md#L{lineno}",
            "available_actions": ["approve", "reject", "snooze"],
        })
    for it in items:
        if it["body"] is None:
            del it["body"]

    n = len(items)
    card = {
        "card_id": card_id,
        "instance": inst,
        "profile": "mnemo",
        "type": "review",
        "title": (f"rem-cycle review queue — {n} pending item{'s' if n != 1 else ''}"
                  if n else "rem-cycle review queue — clear"),
        "body": ("Proposals from the latest rem-cycle run. Approve to apply, "
                 "reject to drop, snooze to hide for 3 days."
                 if n else "Queue clear. New proposals appear after the next run."),
        "salience": 0.8,
        "source_ref": "docs/rem-cycle/QUEUE.md",
        "actions": ["dismiss"],
        "items": items,
        "state": "active",
    }
    out = outbox / (card_id.replace("/", "__") + ".json")
    out.write_text(json.dumps(card, indent=1) + "\n")
    print(f"feed-emit(queue): {n} item(s) -> {out.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
