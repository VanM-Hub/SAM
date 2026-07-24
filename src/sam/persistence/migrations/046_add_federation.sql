-- Migration 046: Add federation tables
--
-- Creates:
--   federated_insights   — insights shared between federated clusters
--   cluster_trust        — trust scores per cluster
--   federation_config    — federation configuration

-- ═══════════════════════════════════════════════════════════════════
-- 1. federated_insights
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS federated_insights (
    id              TEXT PRIMARY KEY,
    source_cluster  TEXT NOT NULL DEFAULT '',
    insight_type    TEXT NOT NULL DEFAULT 'KNOWLEDGE',
    content         TEXT NOT NULL DEFAULT '{}',        -- JSON
    confidence      REAL NOT NULL DEFAULT 0.8,
    trust_required  REAL NOT NULL DEFAULT 0.3,
    sovereignty     TEXT NOT NULL DEFAULT 'PUBLIC',
    ttl             INTEGER NOT NULL DEFAULT 86400,
    freshness       REAL NOT NULL DEFAULT 1.0,
    provenance      TEXT NOT NULL DEFAULT '{}',        -- JSON Provenance
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_fi_type
    ON federated_insights (insight_type);

CREATE INDEX IF NOT EXISTS idx_fi_source
    ON federated_insights (source_cluster);

CREATE INDEX IF NOT EXISTS idx_fi_ts
    ON federated_insights (created_at);


-- ═══════════════════════════════════════════════════════════════════
-- 2. cluster_trust
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS cluster_trust (
    cluster_id          TEXT PRIMARY KEY,
    trust_score         REAL NOT NULL DEFAULT 0.5,
    interactions        INTEGER NOT NULL DEFAULT 0,
    successful_interactions INTEGER NOT NULL DEFAULT 0,
    last_interaction    TEXT,
    history             TEXT NOT NULL DEFAULT '[]',     -- JSON list
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);


-- ═══════════════════════════════════════════════════════════════════
-- 3. federation_config
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS federation_config (
    id              TEXT PRIMARY KEY,
    local_cluster_id TEXT NOT NULL DEFAULT '',
    auto_sync       INTEGER NOT NULL DEFAULT 1,
    sync_interval   INTEGER NOT NULL DEFAULT 60,
    max_peers       INTEGER NOT NULL DEFAULT 10,
    min_trust_for_accept REAL NOT NULL DEFAULT 0.3,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
