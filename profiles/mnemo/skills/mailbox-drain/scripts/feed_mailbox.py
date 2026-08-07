#!/usr/bin/env python3
"""feed mailbox client — fetch pending decisions, ack resolved ones.

HTTP helper for the mailbox-drain skill. Judgment (validate against current
brain state, apply, record) lives in the skill/agent; this script only talks
to the feed service.

Usage:
  feed_mailbox.py pending            # print pending decisions as JSON
  feed_mailbox.py ack <id> <status>  # status: applied | superseded | flagged

Environment:
  FEED_URL          e.g. https://soma-feed.pages.dev
  FEED_READER_KEY   for `pending`
  FEED_PUSH_KEY     for `ack`

Explicit User-Agent: Cloudflare 403s python-urllib's default before the
request ever reaches the app (spike finding).
"""
import json
import os
import sys
import urllib.error
import urllib.request

UA = "soma-feed-drain/1.0"
ACK_STATES = {"applied", "superseded", "flagged"}


def req(url, key, method="GET", body=None):
    r = urllib.request.Request(
        url,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "x-feed-key": key,
            "content-type": "application/json",
            "user-agent": UA,
        },
    )
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.load(resp)


def main():
    base = os.environ.get("FEED_URL", "").rstrip("/")
    if not base:
        print("feed-mailbox: FEED_URL is required", file=sys.stderr)
        return 2
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""

    if cmd == "pending":
        key = os.environ.get("FEED_READER_KEY") or os.environ.get("FEED_PUSH_KEY")
        print(json.dumps(req(f"{base}/decisions?status=pending", key), indent=1))
        return 0

    if cmd == "ack":
        if len(sys.argv) != 4 or sys.argv[3] not in ACK_STATES:
            print("usage: feed_mailbox.py ack <id> <applied|superseded|flagged>",
                  file=sys.stderr)
            return 2
        key = os.environ.get("FEED_PUSH_KEY")
        out = req(f"{base}/ack", key, "POST",
                  {"id": int(sys.argv[2]), "status": sys.argv[3]})
        print(json.dumps(out))
        return 0

    print("usage: feed_mailbox.py pending | ack <id> <status>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except urllib.error.HTTPError as e:
        print(f"feed-mailbox: HTTP {e.code}: {e.read().decode()[:200]}",
              file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"feed-mailbox: {e}", file=sys.stderr)
        sys.exit(1)
