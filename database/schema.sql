PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS products (
  hs6 TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  family TEXT NOT NULL,
  hs_version TEXT NOT NULL DEFAULT 'HS2022',
  strategic_relevance TEXT,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS india_tariff_lines (
  code TEXT PRIMARY KEY,
  parent_hs6 TEXT NOT NULL,
  name TEXT NOT NULL,
  itchs_version TEXT NOT NULL,
  valid_from TEXT,
  valid_to TEXT,
  unit TEXT,
  source TEXT,
  FOREIGN KEY(parent_hs6) REFERENCES products(hs6)
);
CREATE TABLE IF NOT EXISTS trade_flows (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  period TEXT NOT NULL,
  frequency TEXT NOT NULL,
  classification TEXT NOT NULL,
  hs_code TEXT NOT NULL,
  reporter_code TEXT NOT NULL,
  reporter_name TEXT NOT NULL,
  partner_code TEXT NOT NULL,
  partner_name TEXT NOT NULL,
  flow TEXT NOT NULL CHECK(flow IN ('import','export')),
  trade_value_usd REAL,
  net_weight_kg REAL,
  quantity REAL,
  quantity_unit TEXT,
  source_dataset TEXT NOT NULL,
  ingested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(period,frequency,classification,hs_code,reporter_code,partner_code,flow,source_dataset)
);
CREATE INDEX IF NOT EXISTS idx_trade_product_period ON trade_flows(hs_code,period);
CREATE INDEX IF NOT EXISTS idx_trade_reporter_partner ON trade_flows(reporter_code,partner_code);
CREATE TABLE IF NOT EXISTS supply_chain_edges (
  upstream_hs TEXT NOT NULL,
  downstream_hs TEXT NOT NULL,
  relationship_type TEXT NOT NULL,
  confidence TEXT NOT NULL CHECK(confidence IN ('high','medium','low')),
  evidence_source TEXT NOT NULL,
  notes TEXT,
  PRIMARY KEY(upstream_hs,downstream_hs,relationship_type)
);
CREATE TABLE IF NOT EXISTS data_manifests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  extracted_at TEXT NOT NULL,
  period_scope TEXT,
  classification TEXT,
  row_count_received INTEGER,
  row_count_accepted INTEGER,
  validation_status TEXT,
  processing_version TEXT,
  raw_object_key TEXT
);
