-- scuderia feed — D1 schema (authoritative copy; supersedes the spike's).
-- D1 holds ONLY the card outbox and the decisions mailbox. Never raw brain
-- content; the syncer (single writer) enforces the field allowlist + caps.

CREATE TABLE IF NOT EXISTS cards (
  card_id TEXT PRIMARY KEY,           -- <instance>/<producer>/<slot>
  instance TEXT NOT NULL,
  profile TEXT NOT NULL,
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT,
  salience REAL DEFAULT 0.5,
  created TEXT NOT NULL,
  refreshed TEXT NOT NULL,
  expires TEXT,
  source_ref TEXT,
  items TEXT,                         -- JSON array, review cards only
  actions TEXT,                       -- JSON array, card-level actions
  state TEXT DEFAULT 'active',        -- active | snoozed | empty | tombstoned
  snooze_until TEXT,
  schema_version INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  card_id TEXT NOT NULL,
  item_id TEXT,
  action TEXT NOT NULL,               -- approve | reject | snooze | dismiss
  payload TEXT,                       -- v2 respond(text); v1: snooze duration
  instance TEXT NOT NULL,
  ts TEXT NOT NULL,
  status TEXT DEFAULT 'pending',      -- pending | applied | superseded | flagged
  resolved_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_decisions_status ON decisions(status);
CREATE INDEX IF NOT EXISTS idx_decisions_target
  ON decisions(card_id, item_id, status);

-- Migration from the spike schema (already applied to the soma-feed DB):
--   ALTER TABLE cards ADD COLUMN snooze_until TEXT;
-- Retention (enforced in the push route, piggybacked on writes):
--   tombstoned cards deleted after 7 days; acked decisions after 30.
