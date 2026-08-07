CREATE TABLE IF NOT EXISTS cards (
  card_id TEXT PRIMARY KEY,
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
  items TEXT,
  actions TEXT,
  state TEXT DEFAULT 'active',
  schema_version INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  card_id TEXT NOT NULL,
  item_id TEXT,
  action TEXT NOT NULL,
  payload TEXT,
  instance TEXT NOT NULL,
  ts TEXT NOT NULL,
  status TEXT DEFAULT 'pending',
  resolved_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_decisions_status ON decisions(status);
