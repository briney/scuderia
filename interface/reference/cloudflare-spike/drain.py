#!/usr/bin/env python3
"""soma spike drain: apply pending decisions against current brain state.

For each pending decision:
  - item still open in QUEUE.md (- [ ])  -> apply (tick box), ack 'applied'
  - item already resolved (- [x] / gone) -> ack 'superseded', do not touch
"""
import json, re, urllib.request, pathlib

W = "https://soma-feed-spike.soma-feed.workers.dev"
KEYS = dict(
    line.split("=", 1)
    for line in pathlib.Path("/tmp/soma-spike/.keys").read_text().splitlines()
)
QUEUE = pathlib.Path(
    os.environ.get("QUEUE_PATH", "<brain-root>/docs/rem-cycle/QUEUE.md")
)


def req(path, key, method="GET", body=None):
    r = urllib.request.Request(
        W + path,
        method=method,
        data=json.dumps(body).encode() if body else None,
        headers={
            "x-feed-key": key,
            "content-type": "application/json",
            "user-agent": "soma-drain/0.1 (spike)",
        },
    )
    return json.load(urllib.request.urlopen(r))


pending = req("/decisions?status=pending", KEYS["FEED_KEY"])
queue_text = QUEUE.read_text()
results = []

for d in pending:
    item = d["item_id"]
    m = re.search(rf"^- \[( |x)\] `{item}`", queue_text, re.M)
    if m and m.group(1) == " ":
        # still open -> apply: tick the box
        queue_text = queue_text.replace(f"- [ ] `{item}`", f"- [x] `{item}`", 1)
        status = "applied"
    else:
        # already resolved (or vanished) while the decision was in flight
        status = "superseded"
    req("/ack", KEYS["PUSH_KEY"], "POST", {"id": d["id"], "status": status})
    results.append((d["id"], item, d["action"], status))

QUEUE.write_text(queue_text)
for r in results:
    print(f"decision {r[0]}: {r[1]} {r[2]} -> {r[3]}")
