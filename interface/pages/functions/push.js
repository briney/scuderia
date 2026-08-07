// POST /push — upsert a card. Push key (harness syncer only; the single writer).
// Validates against the schema allowlist + size caps before anything touches
// D1 — the D1 invariant is enforced here and in the syncer, defense in depth.
// Also the retention hook (piggybacked on writes): acked decisions die after
// 30 days, tombstoned cards after 7.
import { json, checkKey, validateCard, SCHEMA_VERSION } from "./_shared.js";

export async function onRequestPost({ request, env }) {
  if (!checkKey(request, env, "push")) return json({ error: "unauthorized" }, 401);

  let raw;
  try {
    raw = await request.json();
  } catch {
    return json({ error: "body must be JSON" }, 400);
  }

  const v = validateCard(raw);
  if (!v.ok) return json({ error: v.error }, 400);
  const c = v.card;

  const now = new Date().toISOString();
  const state = c.state ?? "active";

  if (state === "tombstoned") {
    await env.soma_feed
      .prepare("UPDATE cards SET state='tombstoned', refreshed=? WHERE card_id=?")
      .bind(now, c.card_id)
      .run();
  } else {
    await env.soma_feed
      .prepare(
        `INSERT INTO cards (card_id, instance, profile, type, title, body, salience,
                            created, refreshed, expires, source_ref, items, actions,
                            state, snooze_until, schema_version)
         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
         ON CONFLICT(card_id) DO UPDATE SET
           title=excluded.title, body=excluded.body, salience=excluded.salience,
           refreshed=excluded.refreshed, expires=excluded.expires,
           source_ref=excluded.source_ref, items=excluded.items,
           actions=excluded.actions, state=excluded.state,
           snooze_until=excluded.snooze_until`
      )
      .bind(
        c.card_id, c.instance, c.profile, c.type, c.title, c.body ?? null,
        c.salience ?? 0.5, c.created ?? now, now, c.expires ?? null,
        c.source_ref ?? null,
        c.items ? JSON.stringify(c.items) : null,
        c.actions ? JSON.stringify(c.actions) : null,
        state, c.snooze_until ?? null, SCHEMA_VERSION
      )
      .run();
  }

  // Retention, piggybacked on writes (spec: tombstones 7d, acked decisions 30d).
  await env.soma_feed
    .prepare(
      `DELETE FROM decisions
       WHERE status != 'pending' AND resolved_at < datetime('now', '-30 days')`
    )
    .run();
  await env.soma_feed
    .prepare(
      `DELETE FROM cards
       WHERE state = 'tombstoned' AND refreshed < datetime('now', '-7 days')`
    )
    .run();

  return json({ ok: true, card_id: c.card_id, refreshed: now });
}
