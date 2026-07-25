-- Migration 044: Add strategy proposals table
--
-- Creates:
--   strategy_proposals   — cross-cluster strategy proposals with voting

-- ═══════════════════════════════════════════════════════════════════
-- 1. strategy_proposals
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS strategy_proposals (
    id              TEXT PRIMARY KEY,
    proposer_node_id TEXT NOT NULL DEFAULT '',
    strategy        TEXT NOT NULL DEFAULT '{}',       -- JSON
    votes           TEXT NOT NULL DEFAULT '[]',       -- JSON list of {node_id, vote, reason}
    status          TEXT NOT NULL DEFAULT 'PROPOSED',
    timestamp       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_sp_status
    ON strategy_proposals (status);

CREATE INDEX IF NOT EXISTS idx_sp_ts
    ON strategy_proposals (timestamp);
