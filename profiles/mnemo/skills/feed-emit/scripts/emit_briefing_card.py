#!/usr/bin/env python3
"""feed-emit: daily-briefing summary card producer.

Reads the rolling BRIEFING.md at the vault root and writes one summary card
to the instance's feed outbox. The briefing prose stays canonical in the
vault; the card is the glance layer (spec §11).

Dismissal is content-addressed: a dismissed briefing stays hidden until the
briefing *content* changes (next day's brief reappears on its own). The
marker lives in the outbox .state/dismissed.json, written by mailbox-drain.

If BRIEFING.md does not exist, any stale briefing card is removed from the
outbox so the syncer tombstones it.

Environment:
  VAULT_ROOT       vault root (required)
  FEED_INSTANCE    instance name (default: brain.yaml `name:` at vault root)
  FEED_OUTBOX_DIR  outbox dir (default: <vault>/feed-outbox)
  BRIEFING_PATH    default: <vault>/BRIEFING.md
"""
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import sys

BODY_CAP = 3500  # under the 4000 contract cap, leaving room for the header
DISMISS_FILE = ".state/dismissed.json"


def instance_name(vault):
    env = os.environ.get("FEED_INSTANCE")
    if env:
        return env
    for fname in ("instance.yaml", "brain.yaml"):  # brain.yaml = legacy name
        contract = vault / fname
        if contract.exists():
            m = re.search(r"^name:\s*(\S+)", contract.read_text(), re.M)
            if m:
                return m.group(1)
    return vault.name


def main():
    vault = pathlib.Path(os.environ["VAULT_ROOT"])
    outbox = pathlib.Path(
        os.environ.get("FEED_OUTBOX_DIR", vault / "feed-outbox"))
    briefing = pathlib.Path(
        os.environ.get("BRIEFING_PATH", vault / "BRIEFING.md"))
    inst = instance_name(vault)
    card_id = f"{inst}/briefing/daily"
    out = outbox / (card_id.replace("/", "__") + ".json")
    outbox.mkdir(parents=True, exist_ok=True)

    if not briefing.exists():
        if out.exists():
            out.unlink()
            print("feed-emit(briefing): no BRIEFING.md — card withdrawn")
        else:
            print("feed-emit(briefing): no BRIEFING.md — nothing to emit")
        return 0

    text = briefing.read_text()
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
        body = body[:BODY_CAP].rsplit("\n", 1)[0] + "\n\n*(truncated — full brief in BRIEFING.md)*"

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
    out.write_text(json.dumps(card, indent=1) + "\n")
    print(f"feed-emit(briefing): {date} -> {out.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
