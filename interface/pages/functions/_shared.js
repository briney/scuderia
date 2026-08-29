// scuderia feed — shared helpers for the Pages Functions.
// Contract: card model + decision/mailbox protocol (see interface/README.md).
// Instance-specific values (keys, D1 binding) come from env, never code.

export const SCHEMA_VERSION = 1;

// v1 action vocabulary (respond(text) is v2; mailbox.payload carries it later).
export const VOCAB = ["approve", "reject", "snooze", "dismiss"];

// Terminal states a decision can be acked with.
export const ACK_STATES = ["applied", "superseded", "flagged"];

// Field allowlists — the D1 invariant made mechanical. Anything outside these
// lists is rejected, so raw brain content cannot be pushed by construction.
export const CARD_FIELDS = [
  "card_id", "instance", "profile", "type", "title", "body",
  "salience", "created", "refreshed", "expires", "source_ref",
  "items", "actions", "state", "snooze_until", "schema_version",
];
export const ITEM_FIELDS = [
  "item_id", "title", "body", "source_ref", "available_actions",
];

// Glanceable is a constraint, not a suggestion.
export const LIMITS = {
  title: 200,
  body: 4000,
  item_title: 300,
  item_body: 1000,
  items_per_card: 50,
  source_ref: 300,
  card_id: 200,
  payload: 2000,
};

export function json(data, status = 200) {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: { "content-type": "application/json" },
  });
}

export function keyOf(request) {
  const url = new URL(request.url);
  return (
    request.headers.get("x-feed-key") ||
    url.searchParams.get("key") ||
    ""
  );
}

// kind "push" = writer (harness); "read" = reader (feed UI, drain poller).
export function checkKey(request, env, kind) {
  const k = keyOf(request);
  if (!k) return false;
  if (kind === "push") return k === env.PUSH_KEY;
  return k === env.FEED_KEY || k === env.PUSH_KEY;
}

const isStr = (v) => typeof v === "string";
const over = (v, n) => isStr(v) && v.length > n;

// Validate + prune a card against the allowlist and caps.
// Returns { ok, card } or { ok: false, error }.
export function validateCard(raw) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw))
    return { ok: false, error: "card must be a JSON object" };

  const unknown = Object.keys(raw).filter((k) => !CARD_FIELDS.includes(k));
  if (unknown.length)
    return { ok: false, error: `unknown card fields: ${unknown.join(", ")}` };

  for (const f of ["card_id", "instance", "profile", "type", "title"]) {
    if (!isStr(raw[f]) || !raw[f])
      return { ok: false, error: `missing/invalid required field: ${f}` };
  }
  if (over(raw.card_id, LIMITS.card_id))
    return { ok: false, error: "card_id too long" };
  if (over(raw.title, LIMITS.title))
    return { ok: false, error: `title exceeds ${LIMITS.title} chars` };
  if (raw.body != null && !isStr(raw.body))
    return { ok: false, error: "body must be a string" };
  if (over(raw.body, LIMITS.body))
    return { ok: false, error: `body exceeds ${LIMITS.body} chars` };
  if (raw.salience != null &&
      (typeof raw.salience !== "number" || raw.salience < 0 || raw.salience > 1))
    return { ok: false, error: "salience must be a number in [0,1]" };
  if (over(raw.source_ref, LIMITS.source_ref))
    return { ok: false, error: "source_ref too long" };
  if (raw.actions != null) {
    if (!Array.isArray(raw.actions) ||
        !raw.actions.every((a) => VOCAB.includes(a)))
      return { ok: false, error: `actions must be drawn from: ${VOCAB.join(", ")}` };
  }
  if (raw.state != null && !["active", "snoozed", "empty", "tombstoned"].includes(raw.state))
    return { ok: false, error: "bad state" };

  if (raw.items != null) {
    if (!Array.isArray(raw.items))
      return { ok: false, error: "items must be an array" };
    if (raw.items.length > LIMITS.items_per_card)
      return { ok: false, error: `more than ${LIMITS.items_per_card} items` };
    const seen = new Set();
    for (const [i, it] of raw.items.entries()) {
      if (!it || typeof it !== "object" || Array.isArray(it))
        return { ok: false, error: `items[${i}] must be an object` };
      const iu = Object.keys(it).filter((k) => !ITEM_FIELDS.includes(k));
      if (iu.length)
        return { ok: false, error: `items[${i}] unknown fields: ${iu.join(", ")}` };
      if (!isStr(it.item_id) || !it.item_id)
        return { ok: false, error: `items[${i}] missing item_id` };
      if (seen.has(it.item_id))
        return { ok: false, error: `duplicate item_id: ${it.item_id}` };
      seen.add(it.item_id);
      if (!isStr(it.title) || !it.title)
        return { ok: false, error: `items[${i}] missing title` };
      if (over(it.title, LIMITS.item_title))
        return { ok: false, error: `items[${i}] title exceeds ${LIMITS.item_title} chars` };
      if (it.body != null && !isStr(it.body))
        return { ok: false, error: `items[${i}] body must be a string` };
      if (over(it.body, LIMITS.item_body))
        return { ok: false, error: `items[${i}] body exceeds ${LIMITS.item_body} chars` };
      if (over(it.source_ref, LIMITS.source_ref))
        return { ok: false, error: `items[${i}] source_ref too long` };
      if (it.available_actions != null &&
          (!Array.isArray(it.available_actions) ||
           !it.available_actions.every((a) => VOCAB.includes(a))))
        return { ok: false, error: `items[${i}] available_actions must be drawn from: ${VOCAB.join(", ")}` };
    }
  }
  return { ok: true, card: raw };
}
