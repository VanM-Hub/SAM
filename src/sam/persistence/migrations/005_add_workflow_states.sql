-- Migration 005: Add workflow_states table for tracking workflow execution state
-- Version: 5
-- Description: Create workflow_states table to track workflow execution state

CREATE TABLE IF NOT EXISTS workflow_states (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    definition TEXT NOT NULL,  -- JSON serialized WorkflowDefinition
    current_step TEXT,  -- Current step ID being executed
    status TEXT NOT NULL,  -- running, paused, completed, failed
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,  -- Nullable
    metadata TEXT,  -- JSON metadata (e.g., error info)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_workflow_states_workflow_id ON workflow_states(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_states_correlation_id ON workflow_states(correlation_id);
CREATE INDEX IF NOT EXISTS idx_workflow_states_status ON workflow_states(status);
CREATE INDEX IF NOT EXISTS idx_workflow_states_started_at ON workflow_states(started_at);