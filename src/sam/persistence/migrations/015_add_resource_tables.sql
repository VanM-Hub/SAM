-- Migration 015: Add runtime_resources table
-- Central resource registry with ownership and lease-based locking.

CREATE TABLE IF NOT EXISTS runtime_resources (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK(type IN ('JOB','WORKFLOW','SERVICE','PLUGIN','KNOWLEDGE')),
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'CREATED' CHECK(status IN ('CREATED','LOADED','ACTIVE','PAUSED','FAILED','RETIRED')),
    owner_node_id TEXT,
    lease_expires_at TEXT,
    heartbeat_interval INTEGER DEFAULT 30,
    data TEXT DEFAULT '{}',
    version INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata TEXT DEFAULT '{}'
);

CREATE INDEX idx_resources_type ON runtime_resources(type);
CREATE INDEX idx_resources_status ON runtime_resources(status);
CREATE INDEX idx_resources_owner ON runtime_resources(owner_node_id);
CREATE INDEX idx_resources_type_name ON runtime_resources(type, name);
