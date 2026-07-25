-- Migration 019 — Execution Graph tables
-- Stores execution graphs and their constituent nodes for the
-- Execution Graph Runtime (Sprint 20).

-- Execution graphs — top-level execution units
CREATE TABLE IF NOT EXISTS execution_graphs (
    id TEXT NOT NULL PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'CREATED'
        CHECK(status IN ('CREATED', 'RUNNING', 'COMPLETED', 'FAILED', 'PAUSED', 'COMPENSATED')),
    correlation_id TEXT NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Execution nodes — individual capability invocations within a graph
CREATE TABLE IF NOT EXISTS execution_nodes (
    id TEXT NOT NULL PRIMARY KEY,
    graph_id TEXT NOT NULL,
    capability_id TEXT NOT NULL,
    inputs TEXT NOT NULL DEFAULT '{}',
    outputs TEXT,
    dependencies TEXT NOT NULL DEFAULT '[]',
    retry_policy TEXT NOT NULL DEFAULT '{}',
    compensation_policy TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK(status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'COMPENSATED', 'SKIPPED')),
    evidence_ids TEXT NOT NULL DEFAULT '[]',
    started_at TEXT,
    completed_at TEXT,
    FOREIGN KEY (graph_id) REFERENCES execution_graphs(id)
);

-- Index: lookup nodes by graph
CREATE INDEX IF NOT EXISTS idx_execution_nodes_graph ON execution_nodes(graph_id);

-- Index: lookup nodes by status within a graph
CREATE INDEX IF NOT EXISTS idx_execution_nodes_graph_status ON execution_nodes(graph_id, status);

-- Index: lookup graphs by correlation
CREATE INDEX IF NOT EXISTS idx_execution_graphs_correlation ON execution_graphs(correlation_id);

-- Index: lookup graphs by status
CREATE INDEX IF NOT EXISTS idx_execution_graphs_status ON execution_graphs(status);
