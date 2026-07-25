-- Migration 018 — Distribution tables
-- Tracks job and workflow assignments to cluster nodes
-- Only the leader node runs the distributor; assignments persist in DB
-- for audit and recovery.

-- Job assignments — tracks which node is executing which job
CREATE TABLE IF NOT EXISTS job_assignments (
    job_id TEXT NOT NULL PRIMARY KEY,
    assigned_node_id TEXT NOT NULL,
    assigned_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK(status IN ('PENDING', 'ASSIGNED', 'RUNNING', 'COMPLETED', 'FAILED')),
    attempts INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    completed_at TEXT
);

-- Workflow assignments — tracks which node is executing which workflow
CREATE TABLE IF NOT EXISTS workflow_assignments (
    workflow_id TEXT NOT NULL PRIMARY KEY,
    assigned_node_id TEXT NOT NULL,
    assigned_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK(status IN ('PENDING', 'ASSIGNED', 'RUNNING', 'COMPLETED', 'FAILED')),
    attempts INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    completed_at TEXT
);

-- Index for querying assignments by node
CREATE INDEX IF NOT EXISTS idx_job_assignments_node ON job_assignments(assigned_node_id);
CREATE INDEX IF NOT EXISTS idx_workflow_assignments_node ON workflow_assignments(assigned_node_id);

-- Index for querying assignments by status
CREATE INDEX IF NOT EXISTS idx_job_assignments_status ON job_assignments(status);
CREATE INDEX IF NOT EXISTS idx_workflow_assignments_status ON workflow_assignments(status);
