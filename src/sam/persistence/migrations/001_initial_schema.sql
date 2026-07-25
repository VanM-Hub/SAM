-- Migration 001: Initial Schema
-- Creates all core tables for SAM persistence layer

-- Schema version table (will be created by MigrationManager, but included for reference)
-- CREATE TABLE IF NOT EXISTS schema_version (
--     version INTEGER PRIMARY KEY,
--     description TEXT NOT NULL,
--     applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- Evidence table
CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,
    capability_id TEXT,
    execution_id TEXT,
    type TEXT,
    confidence REAL,
    payload TEXT,
    timestamp TEXT
);

-- Knowledge table
CREATE TABLE IF NOT EXISTS knowledge (
    id TEXT PRIMARY KEY,
    capability_id TEXT,
    status TEXT,
    source TEXT,
    confidence REAL,
    payload TEXT,
    timestamp TEXT
);

-- Pattern detections table
CREATE TABLE IF NOT EXISTS patterns (
    id TEXT PRIMARY KEY,
    rule_id TEXT,
    severity TEXT,
    message TEXT,
    metadata TEXT,
    timestamp TEXT
);

-- Recommendations table
CREATE TABLE IF NOT EXISTS recommendations (
    id TEXT PRIMARY KEY,
    rule_id TEXT,
    pattern_detection_id TEXT,
    severity TEXT,
    title TEXT,
    description TEXT,
    action_hint TEXT,
    status TEXT,
    metadata TEXT,
    timestamp TEXT
);

-- Approvals table
CREATE TABLE IF NOT EXISTS approvals (
    id TEXT PRIMARY KEY,
    recommendation_id TEXT,
    severity TEXT,
    title TEXT,
    description TEXT,
    action_hint TEXT,
    status TEXT,
    decision TEXT,
    decided_by TEXT,
    decided_at TEXT,
    metadata TEXT,
    timestamp TEXT
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_evidence_capability ON evidence(capability_id);
CREATE INDEX IF NOT EXISTS idx_evidence_execution ON evidence(execution_id);
CREATE INDEX IF NOT EXISTS idx_evidence_timestamp ON evidence(timestamp);

CREATE INDEX IF NOT EXISTS idx_knowledge_capability ON knowledge(capability_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_status ON knowledge(status);
CREATE INDEX IF NOT EXISTS idx_knowledge_timestamp ON knowledge(timestamp);

CREATE INDEX IF NOT EXISTS idx_patterns_rule ON patterns(rule_id);
CREATE INDEX IF NOT EXISTS idx_patterns_severity ON patterns(severity);
CREATE INDEX IF NOT EXISTS idx_patterns_timestamp ON patterns(timestamp);

CREATE INDEX IF NOT EXISTS idx_recommendations_rule ON recommendations(rule_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_severity ON recommendations(severity);
CREATE INDEX IF NOT EXISTS idx_recommendations_status ON recommendations(status);
CREATE INDEX IF NOT EXISTS idx_recommendations_timestamp ON recommendations(timestamp);

CREATE INDEX IF NOT EXISTS idx_approvals_recommendation ON approvals(recommendation_id);
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);
CREATE INDEX IF NOT EXISTS idx_approvals_timestamp ON approvals(timestamp);