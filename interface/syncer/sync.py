#!/usr/bin/env python3
"""soma feed syncer — the single writer to the feed service.

Reads the instance's local outbox (a directory of card JSON files written by
producers), validates every card against the contract (field allowlist, size
caps — the D1 invariant enforced before anything leaves the machine), and
pushes diffs to the publisher. Cards whose outbox file vanished are
tombstoned.

Environment:
  FEED_URL         e.g. https://soma-feed.pages.dev   (required)
  FEED_PUSH_KEY    writer credential                  (required)
  FEED_OUTBOX_DIR  directory of <card>.json files     (required)
  FEED_STATE_FILE  diff-cache path                    (required)

no_agent-cron friendly: silent when nothing changed, one line per pushed or
tombstoned card otherwise, non-zero exit on failure. Never prints card
content — titles at most.

Spike lessons honored here:
  - explicit User-Agent (Cloudflare 403s python-urllib's default before the
    request ever reaches the app)
  - retry with backoff (edge TLS/propagation lag after first deploy)
  - this is a *file* the cron invokes, never an inline payload
"""
import hashlib
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

UA = "soma-feed-syncer/1.0"
VOCAB = {"approve", "reject", "snooze", "dismiss"}
CARD_FIELDS = {
    "card_id", "instance", "profile", "type", "title", "body",
    "salience", "created", "refreshed", "expires", "source_ref",
    "items", "actions", "state", "snooze_until", "schema_version",
}
ITEM_FIELDS = {"item_id", "title", "body", "source_ref", "available_actions"}
LIMITS = {
    "title": 200, "body": 4000, "item_title": 300, "item_body": 1000,
    "items_per_card": 50, "source_ref": 300, "card_id": 200,
}


class Reject(Exception):
    pass


def validate_card(c, fname):
    """Mirror of functions/_shared.js validateCard — keep in sync."""
    if not isinstance(c, dict):
        raise Reject(f"{fname}: not a JSON object")
    unknown = set(c) - CARD_FIELDS
    if unknown:
        raise Reject(f"{fname}: unknown fields: {sorted(unknown)}")
    for f in ("card_id", "instance", "profile", "type", "title"):
        if not isinstance(c.get(f), str) or not c[f]:
            raise Reject(f"{fname}: missing/invalid required field: {f}")
    if len(c["card_id"]) > LIMITS["card_id"]:
        raise Reject(f"{fname}: card_id too long")
    if len(c["title"]) > LIMITS["title"]:
        raise Reject(f"{fname}: title over {LIMITS['title']} chars")
    if c.get("body") is not None:
        if not isinstance(c["body"], str):
            raise Reject(f"{fname}: body must be a string")
        if len(c["body"]) > LIMITS["body"]:
            raise Reject(f"{fname}: body over {LIMITS['body']} chars")
    if c.get("salience") is not None:
        s = c["salience"]
        if not isinstance(s, (int, float)) or isinstance(s, bool) or not (0 <= s <= 1):
            raise Reject(f"{fname}: salience must be in [0,1]")
    if c.get("source_ref") and len(c["source_ref"]) > LIMITS["source_ref"]:
        raise Reject(f"{fname}: source_ref too long")
    if c.get("actions") is not None:
        if not isinstance(c["actions"], list) or not set(c["actions"]) <= VOCAB:
            raise Reject(f"{fname}: actions outside v1 vocabulary")
    if c.get("state") is not None and c["state"] not in {
        "active", "snoozed", "empty", "tombstoned",
    }:
        raise Reject(f"{fname}: bad state")
    items = c.get("items")
    if items is not None:
        if not isinstance(items, list):
            raise Reject(f"{fname}: items must be an array")
        if len(items) > LIMITS["items_per_card"]:
            raise Reject(f"{fname}: over {LIMITS['items_per_card']} items")
        seen = set()
        for i, it in enumerate(items):
            if not isinstance(it, dict):
                raise Reject(f"{fname}: items[{i}] not an object")
            iu = set(it) - ITEM_FIELDS
            if iu:
                raise Reject(f"{fname}: items[{i}] unknown fields: {sorted(iu)}")
            if not isinstance(it.get("item_id"), str) or not it["item_id"]:
                raise Reject(f"{fname}: items[{i}] missing item_id")
            if it["item_id"] in seen:
                raise Reject(f"{fname}: duplicate item_id {it['item_id']}")
            seen.add(it["item_id"])
            if not isinstance(it.get("title"), str) or not it["title"]:
                raise Reject(f"{fname}: items[{i}] missing title")
            if len(it["title"]) > LIMITS["item_title"]:
                raise Reject(f"{fname}: items[{i}] title too long")
            if it.get("body") is not None and (
                not isinstance(it["body"], str)
                or len(it["body"]) > LIMITS["item_body"]
            ):
                raise Reject(f"{fname}: items[{i}] body too long")
            if it.get("source_ref") and len(it["source_ref"]) > LIMITS["source_ref"]:
                raise Reject(f"{fname}: items[{i}] source_ref too long")
            if it.get("available_actions") is not None and (
                not isinstance(it["available_actions"], list)
                or not set(it["available_actions"]) <= VOCAB
            ):
                raise Reject(f"{fname}: items[{i}] actions outside vocabulary")
    return c


def request(path, body, key, retries=4):
    """POST JSON with explicit UA and backoff. Returns parsed JSON."""
    data = json.dumps(body).encode()
    delay = 2.0
    for attempt in range(retries):
        req = urllib.request.Request(
            path, data=data, method="POST",
            headers={
                "x-feed-key": key,
                "content-type": "application/json",
                "user-agent": UA,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            detail = e.read().decode()[:200]
            if e.code in (401, 403):
                raise Reject(f"auth failed ({e.code}) — check FEED_PUSH_KEY")
            if attempt == retries - 1:
                raise Reject(f"POST {path} failed: HTTP {e.code} {detail}")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt == retries - 1:
                raise Reject(f"POST {path} failed: {e}")
        time.sleep(delay)
        delay *= 2


def main():
    url = os.environ.get("FEED_URL", "").rstrip("/")
    key = os.environ.get("FEED_PUSH_KEY", "")
    outbox = pathlib.Path(os.environ.get("FEED_OUTBOX_DIR", ""))
    state_file = pathlib.Path(os.environ.get("FEED_STATE_FILE", ""))
    if not all([url, key, str(outbox), str(state_file)]):
        print("feed-sync: FEED_URL / FEED_PUSH_KEY / FEED_OUTBOX_DIR / "
              "FEED_STATE_FILE are all required", file=sys.stderr)
        return 2
    if not outbox.is_dir():
        # No outbox yet = no producers have run. Not an error.
        return 0

    try:
        state = json.loads(state_file.read_text()) if state_file.exists() else {}
    except json.JSONDecodeError:
        state = {}

    cards = {}
    for f in sorted(outbox.glob("*.json")):
        if f.name.startswith("."):
            continue  # producer state files (snoozes, dismissals), not cards
        try:
            cards[f.stem] = validate_card(json.loads(f.read_text()), f.name)
        except (json.JSONDecodeError, Reject) as e:
            # A bad card must never reach D1 — skip it, say so, keep going.
            print(f"feed-sync: REJECTED {e}")
    # keyed by card_id (file stem and card_id should agree; card_id wins)
    by_id = {c["card_id"]: c for c in cards.values()}

    pushed, tombstoned = [], []
    for cid, card in by_id.items():
        digest = hashlib.sha256(
            json.dumps(card, sort_keys=True).encode()
        ).hexdigest()
        if state.get(cid) == digest:
            continue
        request(f"{url}/push", card, key)
        state[cid] = digest
        pushed.append(cid)

    for cid in set(state) - set(by_id):
        request(f"{url}/push",
                {"card_id": cid, "instance": "-", "profile": "-",
                 "type": "summary", "title": "(tombstoned)",
                 "state": "tombstoned"}, key)
        del state[cid]
        tombstoned.append(cid)

    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=1))

    for cid in pushed:
        print(f"feed-sync: pushed {cid}")
    for cid in tombstoned:
        print(f"feed-sync: tombstoned {cid}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Reject as e:
        print(f"feed-sync: {e}", file=sys.stderr)
        sys.exit(1)
