-- Migration 013: runtime_state_store
-- Stores snapshots of runtime component states (Daemon, Service, Workflow, Job, Plugin)
-- Enables full state recovery after restart.

CREATE TABLE IF NOT EXISTS runtime_state_store (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    data TEXT DEFAULT '{}',
    updated_at TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    -- name must be unique per type (workflow "scan-plugin" can coexist with job "scan-plugin")
    UNIQUE(type, name)
);

CREATE INDEX IF NOT EXISTS idx_runtime_state_type ON runtime_state_store(type);
CREATE INDEX IF NOT EXISTS idx_runtime_state_status ON runtime_state_store(status);
CREATE INDEX IF NOT EXISTS idx_runtime_state_updated ON runtime_state_store(updated_at);
