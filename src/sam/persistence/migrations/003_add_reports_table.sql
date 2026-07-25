-- Migration: Add reports table for structured execution reports
-- Version: 3
-- Description: Create reports table to store structured execution reports

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id TEXT NOT NULL UNIQUE,
    correlation_id TEXT NOT NULL,
    capability_id TEXT NOT NULL,
    workflow_id TEXT,
    status TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP NOT NULL,
    duration_ms INTEGER NOT NULL DEFAULT 0,
    evidence_count INTEGER NOT NULL DEFAULT 0,
    knowledge_count INTEGER NOT NULL DEFAULT 0,
    pattern_count INTEGER NOT NULL DEFAULT 0,
    recommendation_count INTEGER NOT NULL DEFAULT 0,
    approval_status TEXT,
    summary TEXT,  -- JSON
    raw_events TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reports_correlation_id ON reports(correlation_id);
CREATE INDEX IF NOT EXISTS idx_reports_capability_id ON reports(capability_id);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at);