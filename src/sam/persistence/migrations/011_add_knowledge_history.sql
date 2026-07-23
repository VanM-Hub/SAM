-- Migration 011: Add knowledge versioning and history
-- Adds previous_version column and knowledge_history table

-- Add previous_version column to knowledge table
-- Note: SQLite doesn't support ALTER TABLE ADD COLUMN with DEFAULT for existing rows easily
-- We add it without default, then UPDATE existing rows
ALTER TABLE knowledge ADD COLUMN previous_version INTEGER DEFAULT NULL;

-- Create knowledge_history table
CREATE TABLE IF NOT EXISTS knowledge_history (
    id TEXT PRIMARY KEY,
    knowledge_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    payload_snapshot TEXT NOT NULL,
    changed_by TEXT NOT NULL,
    changed_at TEXT NOT NULL DEFAULT (datetime('now')),
    change_type TEXT NOT NULL, -- 'created', 'updated', 'deleted'
    FOREIGN KEY (knowledge_id) REFERENCES knowledge(id) ON DELETE CASCADE
);

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_knowledge_history_knowledge_id ON knowledge_history(knowledge_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_history_changed_at ON knowledge_history(changed_at);
CREATE INDEX IF NOT EXISTS idx_knowledge_history_version ON knowledge_history(version);

-- Migration version record
INSERT OR REPLACE INTO schema_version (version, applied_at, description)
VALUES (11, datetime('now'), 'Add knowledge versioning and history table');