// POST /ack — mark a decision applied | superseded | flagged. Push key
// (the drain on the harness; it, not readers, resolves mailbox rows).
import { json, checkKey, ACK_STATES } from "./_shared.js";

export async function onRequestPost({ request, env }) {
  if (!checkKey(request, env, "push")) return json({ error: "unauthorized" }, 401);

  let a;
  try {
    a = await request.json();
  } catch {
    return json({ error: "body must be JSON" }, 400);
  }
  if (!ACK_STATES.includes(a.status))
    return json({ error: `bad status; one of: ${ACK_STATES.join(", ")}` }, 400);
  if (typeof a.id !== "number")
    return json({ error: "missing numeric decision id" }, 400);

  const r = await env.soma_feed
    .prepare(
      `UPDATE decisions SET status = ?, resolved_at = ?
       WHERE id = ? AND status = 'pending'`
    )
    .bind(a.status, new Date().toISOString(), a.id)
    .run();
  if (r.meta.changes === 0)
    return json({ error: "no pending decision with that id" }, 404);
  return json({ ok: true });
}
