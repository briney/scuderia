// GET /feed — cards for the renderer. Reader key.
// Active cards plus snoozed cards whose snooze has elapsed; expired cards die.
import { json, checkKey } from "./_shared.js";

export async function onRequestGet({ request, env }) {
  if (!checkKey(request, env, "read")) return json({ error: "unauthorized" }, 401);

  const now = new Date().toISOString();
  const { results } = await env.soma_feed
    .prepare(
      `SELECT * FROM cards
       WHERE state = 'active'
          OR (state = 'snoozed' AND (snooze_until IS NULL OR snooze_until <= ?))
       ORDER BY salience DESC, refreshed DESC`
    )
    .bind(now)
    .all();

  const cards = [];
  for (const c of results) {
    if (c.expires && c.expires < now) continue; // expired cards die
    c.items = c.items ? JSON.parse(c.items) : null;
    c.actions = c.actions ? JSON.parse(c.actions) : null;
    cards.push(c);
  }
  return json(cards);
}
