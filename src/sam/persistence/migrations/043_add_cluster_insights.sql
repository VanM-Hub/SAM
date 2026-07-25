-- Migration 043: Add cluster insights table
--
-- Creates:
--   cluster_insights   — insights shared across all nodes

-- ═══════════════════════════════════════════════════════════════════
-- 1. cluster_insights
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS cluster_insights (
    id              TEXT PRIMARY KEY,
    node_id         TEXT NOT NULL,
    insight_type    TEXT NOT NULL DEFAULT '',
    content         TEXT NOT NULL DEFAULT '{}',       -- JSON
    confidence      REAL NOT NULL DEFAULT 0.8,
    timestamp       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    read_by         TEXT NOT NULL DEFAULT '[]',       -- JSON list of node IDs
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_ci_node
    ON cluster_insights (node_id);

CREATE INDEX IF NOT EXISTS idx_ci_type
    ON cluster_insights (insight_type);

CREATE INDEX IF NOT EXISTS idx_ci_ts
    ON cluster_insights (timestamp);
