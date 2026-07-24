-- Sprint 26 – Migration 029: Add agent registry table.
-- Fase 1: Multi-Agent Collaboration — Agent Registry & Discovery.

CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    capabilities TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'ONLINE'
        CHECK(status IN ('ONLINE', 'OFFLINE', 'BUSY', 'IDLE')),
    endpoint TEXT NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}',
    last_heartbeat TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_name ON agents(name);
