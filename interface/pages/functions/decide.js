// POST /decide — append a decision to the mailbox. Reader key.
// Server-side validation (spec §8): action in vocabulary, card exists,
// item exists in the card, no duplicate pending decision for the same target.
import { json, checkKey, VOCAB, LIMITS } from "./_shared.js";

export async function onRequestPost({ request, env }) {
  if (!checkKey(request, env, "read")) return json({ error: "unauthorized" }, 401);

  let d;
  try {
    d = await request.json();
  } catch {
    return json({ error: "body must be JSON" }, 400);
  }

  if (!VOCAB.includes(d.action))
    return json({ error: `unknown action; v1 vocabulary: ${VOCAB.join(", ")}` }, 400);
  if (typeof d.card_id !== "string" || !d.card_id)
    return json({ error: "missing card_id" }, 400);
  if (d.item_id != null && typeof d.item_id !== "string")
    return json({ error: "item_id must be a string" }, 400);
  if (d.payload != null &&
      (typeof d.payload !== "string" || d.payload.length > LIMITS.payload))
    return json({ error: `payload must be a string <= ${LIMITS.payload} chars` }, 400);

  // Card must exist and be live.
  const card = await env.soma_feed
    .prepare("SELECT card_id, instance, items, state FROM cards WHERE card_id = ?")
    .bind(d.card_id)
    .first();
  if (!card) return json({ error: "unknown card" }, 404);
  if (card.state === "tombstoned") return json({ error: "card is tombstoned" }, 410);

  // Item-level decisions require the item to exist in the card's stack.
  if (d.item_id) {
    const items = card.items ? JSON.parse(card.items) : [];
    if (!items.some((it) => it.item_id === d.item_id))
      return json({ error: "unknown item for this card" }, 404);
  }

  // Duplicate-decision guard: one pending decision per (card, item) target.
  const dupe = await env.soma_feed
    .prepare(
      `SELECT COUNT(*) AS n FROM decisions
       WHERE card_id = ? AND IFNULL(item_id, '') = IFNULL(?, '') AND status = 'pending'`
    )
    .bind(d.card_id, d.item_id ?? null)
    .first();
  if (dupe.n > 0) return json({ error: "decision already pending" }, 409);

  const now = new Date().toISOString();
  const r = await env.soma_feed
    .prepare(
      `INSERT INTO decisions (card_id, item_id, action, payload, instance, ts)
       VALUES (?,?,?,?,?,?)`
    )
    .bind(d.card_id, d.item_id ?? null, d.action, d.payload ?? null, card.instance, now)
    .run();
  return json({ ok: true, decision_id: r.meta.last_row_id, ts: now });
}
