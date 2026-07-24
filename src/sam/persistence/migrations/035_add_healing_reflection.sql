-- Sprint 28 Fase 2 — Healing Reflection + Operational Confidence
-- Reflection records for self-healing loop analysis
-- Operational confidence history for tracking system trust level

CREATE TABLE IF NOT EXISTS reflection_records (
    id TEXT PRIMARY KEY,
    cycle_id TEXT NOT NULL,
    symptom TEXT NOT NULL,
    hypothesis TEXT NOT NULL DEFAULT '',
    action_taken TEXT NOT NULL DEFAULT '',
    expected_outcome TEXT NOT NULL DEFAULT '',
    actual_outcome TEXT NOT NULL DEFAULT '',
    gap_analysis TEXT NOT NULL DEFAULT '',
    lessons TEXT NOT NULL DEFAULT '[]',
    confidence REAL NOT NULL DEFAULT 0.0 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    success BOOLEAN NOT NULL DEFAULT 0,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    metadata TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS operational_confidence_history (
    id TEXT PRIMARY KEY,
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    health_status TEXT NOT NULL DEFAULT 'unknown',
    success_rate REAL NOT NULL DEFAULT 1.0 CHECK (success_rate >= 0.0 AND success_rate <= 1.0),
    failure_rate REAL NOT NULL DEFAULT 0.0 CHECK (failure_rate >= 0.0 AND failure_rate <= 1.0),
    rollback_rate REAL NOT NULL DEFAULT 0.0 CHECK (rollback_rate >= 0.0 AND rollback_rate <= 1.0),
    pending_approvals INTEGER NOT NULL DEFAULT 0,
    runtime_stability REAL NOT NULL DEFAULT 1.0 CHECK (runtime_stability >= 0.0 AND runtime_stability <= 1.0),
    resource_pressure REAL NOT NULL DEFAULT 0.0 CHECK (resource_pressure >= 0.0 AND resource_pressure <= 1.0),
    cluster_stability REAL NOT NULL DEFAULT 1.0 CHECK (cluster_stability >= 0.0 AND cluster_stability <= 1.0),
    knowledge_freshness REAL NOT NULL DEFAULT 0.0 CHECK (knowledge_freshness >= 0.0 AND knowledge_freshness <= 1.0),
    reasoning_confidence REAL NOT NULL DEFAULT 0.0 CHECK (reasoning_confidence >= 0.0 AND reasoning_confidence <= 1.0),
    component_breakdown TEXT NOT NULL DEFAULT '{}',
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_reflection_cycle ON reflection_records(cycle_id);
CREATE INDEX idx_reflection_timestamp ON reflection_records(timestamp);
CREATE INDEX idx_confidence_timestamp ON operational_confidence_history(timestamp);
CREATE INDEX idx_confidence_score ON operational_confidence_history(score);
