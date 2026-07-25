-- Migration 014: Add workflow_checkpoints table
-- Supports pause/resume/recover for workflow executions.

CREATE TABLE IF NOT EXISTS workflow_checkpoints (
    workflow_id TEXT PRIMARY KEY,
    correlation_id TEXT NOT NULL,
    current_step TEXT,
    completed_steps TEXT DEFAULT '[]',
    pending_steps TEXT DEFAULT '[]',
    evidence_ids TEXT DEFAULT '[]',
    payload TEXT DEFAULT '{}',
    retry_count INTEGER DEFAULT 0,
    timestamp TEXT DEFAULT (datetime('now')),
    status TEXT DEFAULT 'RUNNING' CHECK(status IN ('RUNNING','PAUSED','COMPLETED','FAILED'))
);

CREATE INDEX idx_checkpoints_status ON workflow_checkpoints(status);
CREATE INDEX idx_checkpoints_correlation ON workflow_checkpoints(correlation_id);
