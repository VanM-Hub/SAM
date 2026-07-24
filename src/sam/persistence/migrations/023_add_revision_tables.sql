-- Migration 023: Add graph_revisions and intent_evolutions tables
-- Supports Sprint 23 Fase 3 — Graph Revision & Intent Evolution

-- ── Graph Revisions ───────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS graph_revisions (
    id TEXT PRIMARY KEY,
    graph_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    previous_version INTEGER,
    reason TEXT NOT NULL,
    trigger TEXT NOT NULL DEFAULT 'evidence_change',
    new_nodes TEXT NOT NULL DEFAULT '[]',
    modified_nodes TEXT NOT NULL DEFAULT '[]',
    removed_nodes TEXT NOT NULL DEFAULT '[]',
    snapshot_before TEXT,
    snapshot_after TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_graph_revisions_graph_id
    ON graph_revisions(graph_id);

CREATE INDEX IF NOT EXISTS idx_graph_revisions_created_at
    ON graph_revisions(created_at);

-- ── Intent Evolutions ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS intent_evolutions (
    id TEXT PRIMARY KEY,
    original_intent_id TEXT NOT NULL,
    new_intent_id TEXT NOT NULL,
    evidence_ids TEXT NOT NULL DEFAULT '[]',
    reason TEXT NOT NULL,
    original_type TEXT NOT NULL,
    new_type TEXT NOT NULL,
    original_target TEXT NOT NULL,
    new_target TEXT NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_intent_evolutions_original_intent_id
    ON intent_evolutions(original_intent_id);

CREATE INDEX IF NOT EXISTS idx_intent_evolutions_new_intent_id
    ON intent_evolutions(new_intent_id);

CREATE INDEX IF NOT EXISTS idx_intent_evolutions_timestamp
    ON intent_evolutions(timestamp);
