-- Migration 016: Create cluster_nodes table for Runtime Node Registry.
-- Sprint 18 – Node Runtime & Cluster Identity.

CREATE TABLE IF NOT EXISTS cluster_nodes (
    node_id TEXT PRIMARY KEY,
    cluster_id TEXT NOT NULL,
    hostname TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'INITIALIZING',
    capabilities TEXT NOT NULL DEFAULT '[]',  -- JSON list of NodeCapabilities
    version TEXT NOT NULL DEFAULT '',
    started_at DATETIME NOT NULL,
    last_heartbeat DATETIME NOT NULL,
    health TEXT NOT NULL DEFAULT '{}',        -- JSON: load, queue_count, etc.
    metadata TEXT NOT NULL DEFAULT '{}',      -- JSON
    labels TEXT NOT NULL DEFAULT '{}'         -- JSON object of k:v
);

CREATE INDEX idx_cluster_nodes_status ON cluster_nodes(status);
CREATE INDEX idx_cluster_nodes_cluster ON cluster_nodes(cluster_id);
