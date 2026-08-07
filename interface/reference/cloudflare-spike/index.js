// soma feed spike — minimal card contract server
// Routes:
//   GET  /            HTML dashboard (key via ?key=, kept in localStorage)
//   GET  /feed        JSON cards            (reader key)
//   POST /push        upsert card           (push key)
//   POST /decide      append decision       (reader key)
//   GET  /decisions   list mailbox          (reader key; ?status=pending)
//   POST /ack         mark decision status  (push key) {id, status}

const json = (d, s = 200) =>
  new Response(JSON.stringify(d, null, 2), {
    status: s,
    headers: { "content-type": "application/json" },
  });

function keyOf(request) {
  const url = new URL(request.url);
  return (
    request.headers.get("x-feed-key") ||
    url.searchParams.get("key") ||
    ""
  );
}

function checkKey(request, env, kind) {
  const k = keyOf(request);
  if (kind === "push") return k && k === env.PUSH_KEY;
  return k && (k === env.FEED_KEY || k === env.PUSH_KEY);
}

const PAGE = `<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>soma feed (spike)</title>
<style>
 body{font-family:-apple-system,system-ui,sans-serif;background:#0f1115;color:#e8e8ec;max-width:36em;margin:1.5em auto;padding:0 1em}
 .card{background:#1a1d26;border:1px solid #2a2e3d;border-radius:12px;padding:1em 1.2em;margin:1em 0}
 .tag{display:inline-block;font-size:.72em;letter-spacing:.08em;text-transform:uppercase;padding:.15em .6em;border-radius:999px;margin-bottom:.5em}
 .mnemo{background:#1e2a4a;color:#7ea4ff}.oiko{background:#14342a;color:#5fd6a2}
 .meta{color:#8a8f9e;font-size:.85em;margin-top:.6em}
 .item{border-top:1px solid #2a2e3d;padding:.8em 0}
 button{font-size:1em;border:0;border-radius:8px;padding:.45em 1em;margin-right:.5em;cursor:pointer}
 .ok{background:#2e7d5b;color:#fff}.no{background:#8a3a4a;color:#fff}
 .sent{opacity:.55}
 h1{font-size:1.25em}
</style></head><body>
<h1>soma — feed (spike)</h1>
<div id="out">loading…</div>
<script>
const params=new URLSearchParams(location.search);
if(params.get("key")){localStorage.setItem("feed_key",params.get("key"));}
const KEY=localStorage.getItem("feed_key")||"";
const H={"x-feed-key":KEY};
async function load(){
  const r=await fetch("/feed",{headers:H});
  if(!r.ok){document.getElementById("out").textContent="auth failed ("+r.status+") — add ?key=… to the URL";return;}
  const cards=await r.json();
  const out=document.getElementById("out");out.innerHTML="";
  for(const c of cards){
    const el=document.createElement("div");el.className="card";
    let h='<span class="tag '+c.profile+'">'+c.profile+" · "+c.type+"</span><div><b>"+c.title+"</b></div>";
    if(c.body)h+='<div class="meta">'+c.body+"</div>";
    for(const it of (c.items||[])){
      h+='<div class="item" id="it-'+it.item_id+'"><div>'+it.title+'</div>'
        +'<div class="meta">'+it.source_ref+"</div>"
        +'<div style="margin-top:.5em"><button class="ok" onclick="decide(this,\\''+c.card_id+'\\',\\''+it.item_id+'\\',\\'approve\\')">approve</button>'
        +'<button class="no" onclick="decide(this,\\''+c.card_id+'\\',\\''+it.item_id+'\\',\\'reject\\')">reject</button></div></div>';
    }
    h+='<div class="meta">'+c.card_id+" · refreshed "+c.refreshed+"</div>";
    el.innerHTML=h;out.appendChild(el);
  }
  if(!cards.length)out.textContent="(no cards yet)";
}
async function decide(btn,card_id,item_id,action){
  btn.parentElement.parentElement.classList.add("sent");
  const r=await fetch("/decide",{method:"POST",headers:{...H,"content-type":"application/json"},
    body:JSON.stringify({card_id,item_id,action})});
  btn.parentElement.innerHTML=r.ok?("<span class='meta'>decision recorded: "+action+"</span>"):("failed: "+r.status);
}
load();
</script></body></html>`;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    if (path === "/" && request.method === "GET") {
      return new Response(PAGE, { headers: { "content-type": "text/html" } });
    }

    if (path === "/feed" && request.method === "GET") {
      if (!checkKey(request, env, "read")) return json({ error: "unauthorized" }, 401);
      const { results } = await env.soma_feed
        .prepare("SELECT * FROM cards WHERE state != 'tombstoned' ORDER BY salience DESC, refreshed DESC")
        .all();
      for (const c of results) {
        c.items = c.items ? JSON.parse(c.items) : null;
        c.actions = c.actions ? JSON.parse(c.actions) : null;
      }
      return json(results);
    }

    if (path === "/push" && request.method === "POST") {
      if (!checkKey(request, env, "push")) return json({ error: "unauthorized" }, 401);
      const c = await request.json();
      const now = new Date().toISOString();
      await env.soma_feed
        .prepare(
          `INSERT INTO cards (card_id, instance, profile, type, title, body, salience, created, refreshed, expires, source_ref, items, actions, state, schema_version)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?, 'active', 1)
           ON CONFLICT(card_id) DO UPDATE SET
             title=excluded.title, body=excluded.body, salience=excluded.salience,
             refreshed=excluded.refreshed, expires=excluded.expires,
             source_ref=excluded.source_ref, items=excluded.items, actions=excluded.actions`
        )
        .bind(
          c.card_id, c.instance, c.profile, c.type, c.title, c.body ?? null,
          c.salience ?? 0.5, c.created ?? now, now, c.expires ?? null,
          c.source_ref ?? null,
          c.items ? JSON.stringify(c.items) : null,
          c.actions ? JSON.stringify(c.actions) : null
        )
        .run();
      return json({ ok: true, card_id: c.card_id, refreshed: now });
    }

    if (path === "/decide" && request.method === "POST") {
      if (!checkKey(request, env, "read")) return json({ error: "unauthorized" }, 401);
      const d = await request.json();
      if (!["approve", "reject", "snooze", "dismiss"].includes(d.action))
        return json({ error: "unknown action" }, 400);
      // reject duplicate pending decisions for the same item
      const dupe = await env.soma_feed
        .prepare("SELECT COUNT(*) AS n FROM decisions WHERE card_id=? AND IFNULL(item_id,'')=IFNULL(?, '') AND status='pending'")
        .bind(d.card_id, d.item_id ?? null)
        .first();
      if (dupe.n > 0) return json({ error: "decision already pending" }, 409);
      const now = new Date().toISOString();
      const r = await env.soma_feed
        .prepare("INSERT INTO decisions (card_id, item_id, action, payload, instance, ts) VALUES (?,?,?,?,?,?)")
        .bind(d.card_id, d.item_id ?? null, d.action, d.payload ?? null, d.instance ?? "example-instance", now)
        .run();
      return json({ ok: true, decision_id: r.meta.last_row_id, ts: now });
    }

    if (path === "/decisions" && request.method === "GET") {
      if (!checkKey(request, env, "read")) return json({ error: "unauthorized" }, 401);
      const status = url.searchParams.get("status");
      const q = status
        ? env.soma_feed.prepare("SELECT * FROM decisions WHERE status=? ORDER BY id").bind(status)
        : env.soma_feed.prepare("SELECT * FROM decisions ORDER BY id");
      const { results } = await q.all();
      return json(results);
    }

    if (path === "/ack" && request.method === "POST") {
      if (!checkKey(request, env, "push")) return json({ error: "unauthorized" }, 401);
      const a = await request.json();
      if (!["applied", "superseded", "flagged"].includes(a.status))
        return json({ error: "bad status" }, 400);
      await env.soma_feed
        .prepare("UPDATE decisions SET status=?, resolved_at=? WHERE id=? AND status='pending'")
        .bind(a.status, new Date().toISOString(), a.id)
        .run();
      return json({ ok: true });
    }

    return json({ error: "not found" }, 404);
  },
};
