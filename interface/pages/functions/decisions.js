// GET /decisions — read the mailbox. Reader key; ?status=pending filter.
import { json, checkKey } from "./_shared.js";

export async function onRequestGet({ request, env }) {
  if (!checkKey(request, env, "read")) return json({ error: "unauthorized" }, 401);

  const url = new URL(request.url);
  const status = url.searchParams.get("status");
  if (status && !["pending", "applied", "superseded", "flagged"].includes(status))
    return json({ error: "bad status filter" }, 400);

  const q = status
    ? env.soma_feed.prepare("SELECT * FROM decisions WHERE status = ? ORDER BY id").bind(status)
    : env.soma_feed.prepare("SELECT * FROM decisions ORDER BY id");
  const { results } = await q.all();
  return json(results);
}
