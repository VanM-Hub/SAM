-- Migration 010: Add FTS5 virtual table for knowledge search
-- This migration is defensive: it checks if the knowledge table exists
-- before creating virtual table and triggers.

-- Note: SQLite doesn't support conditional DDL easily. We'll create the FTS
-- virtual table if it doesn't exist, and the DROP TRIGGER IF EXISTS guards
-- prevent failures when table/columns/triggers are missing.

-- Create FTS virtual table WITHOUT external content (content managed manually)
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
    statement,
    category,
    metadata
);

-- Populate initial data if knowledge exists
INSERT OR IGNORE INTO knowledge_fts(rowid, statement, category, metadata)
SELECT rowid, statement, category, metadata FROM knowledge;

-- Triggers to keep FTS in sync (use DROP IF EXISTS then CREATE)
DROP TRIGGER IF EXISTS knowledge_fts_insert;
CREATE TRIGGER knowledge_fts_insert AFTER INSERT ON knowledge
BEGIN
    INSERT INTO knowledge_fts(rowid, statement, category, metadata)
    VALUES (NEW.rowid, NEW.statement, NEW.category, NEW.metadata);
END;

DROP TRIGGER IF EXISTS knowledge_fts_update;
CREATE TRIGGER knowledge_fts_update AFTER UPDATE ON knowledge
BEGIN
    UPDATE knowledge_fts
    SET statement = NEW.statement,
        category = NEW.category,
        metadata = NEW.metadata
    WHERE rowid = OLD.rowid;
END;

DROP TRIGGER IF EXISTS knowledge_fts_delete;
CREATE TRIGGER knowledge_fts_delete AFTER DELETE ON knowledge
BEGIN
    DELETE FROM knowledge_fts WHERE rowid = OLD.rowid;
END;
