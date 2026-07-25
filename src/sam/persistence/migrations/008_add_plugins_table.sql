-- Migration 008: Add plugins table
-- Applied: 2026-07-24

CREATE TABLE IF NOT EXISTS plugins (
    plugin_id TEXT PRIMARY KEY,
    workflow_id TEXT,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    manifest_yaml TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'INSTALLED',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (workflow_id) REFERENCES workflow_states(workflow_id)
);

CREATE INDEX IF NOT EXISTS idx_plugins_workflow_id ON plugins(workflow_id);
CREATE INDEX IF NOT EXISTS idx_plugins_status ON plugins(status);