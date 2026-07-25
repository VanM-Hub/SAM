-- Sprint 26 – Migration 031: Add delegation and collaboration workflow tables.
-- Fase 3: Multi-Agent Collaboration — Collaboration Workflows & Task Delegation.

CREATE TABLE IF NOT EXISTS delegation_requests (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    sender_agent_id TEXT NOT NULL,
    target_agent_id TEXT NOT NULL,
    capability TEXT NOT NULL,
    payload TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'REQUESTED'
        CHECK(status IN ('REQUESTED', 'ACCEPTED', 'REJECTED',
                         'IN_PROGRESS', 'COMPLETED', 'FAILED', 'TIMEOUT')),
    timeout_seconds INTEGER NOT NULL DEFAULT 60,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    result TEXT,
    error TEXT,
    FOREIGN KEY (sender_agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    FOREIGN KEY (target_agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS collaboration_workflows (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    steps TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK(status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_delegation_sender ON delegation_requests(sender_agent_id);
CREATE INDEX IF NOT EXISTS idx_delegation_target ON delegation_requests(target_agent_id);
CREATE INDEX IF NOT EXISTS idx_delegation_status ON delegation_requests(status);
CREATE INDEX IF NOT EXISTS idx_delegation_task ON delegation_requests(task_id);
CREATE INDEX IF NOT EXISTS idx_workflow_status ON collaboration_workflows(status);
