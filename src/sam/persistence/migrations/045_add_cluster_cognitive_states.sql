-- Migration 045: Add cluster cognitive states table
--
-- Creates:
--   cluster_cognitive_states   — aggregated cognitive state snapshots

-- ═══════════════════════════════════════════════════════════════════
-- 1. cluster_cognitive_states
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS cluster_cognitive_states (
    id                  TEXT PRIMARY KEY,
    cluster_id          TEXT NOT NULL DEFAULT '',
    node_states         TEXT NOT NULL DEFAULT '{}',       -- JSON dict node_id → state
    aggregated_confidence REAL NOT NULL DEFAULT 0.0,
    dominant_focus      TEXT NOT NULL DEFAULT 'balanced',
    avg_autonomy_level  REAL NOT NULL DEFAULT 0.0,
    node_count          INTEGER NOT NULL DEFAULT 0,
    timestamp           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_ccs_cluster
    ON cluster_cognitive_states (cluster_id);

CREATE INDEX IF NOT EXISTS idx_ccs_ts
    ON cluster_cognitive_states (timestamp);
