-- Migration 004: Add executions table for tracking capability/workflow executions
-- Version: 4
-- Description: Create executions table to track capability and workflow executions

CREATE TABLE IF NOT EXISTS executions (
    id TEXT PRIMARY KEY,
    correlation_id TEXT,
    capability_id TEXT,
    workflow_id TEXT,
    step_name TEXT,
    status TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    inputs TEXT,  -- JSON
    result TEXT,  -- JSON
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_executions_correlation_id ON executions(correlation_id);
CREATE INDEX IF NOT EXISTS idx_executions_capability_id ON executions(capability_id);
CREATE INDEX IF NOT EXISTS idx_executions_workflow_id ON executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_executions_status ON executions(status);
CREATE INDEX IF NOT EXISTS idx_executions_started_at ON executions(started_at);