-- Migration 010: Add FTS5 virtual table for knowledge search
-- Fixed: use actual columns from knowledge table (id, capability_id, status, source, confidence, payload, timestamp, correlation_id)
-- FTS5 uses payload (main text content), source, and status as searchable columns.

CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
    payload,
    source,
    status
);

-- Populate initial data if knowledge exists
INSERT OR IGNORE INTO knowledge_fts(rowid, payload, source, status)
SELECT rowid, payload, source, status FROM knowledge;

-- Triggers to keep FTS in sync
DROP TRIGGER IF EXISTS knowledge_fts_insert;
CREATE TRIGGER knowledge_fts_insert AFTER INSERT ON knowledge
BEGIN
    INSERT INTO knowledge_fts(rowid, payload, source, status)
    VALUES (NEW.rowid, NEW.payload, NEW.source, NEW.status);
END;

DROP TRIGGER IF EXISTS knowledge_fts_update;
CREATE TRIGGER knowledge_fts_update AFTER UPDATE ON knowledge
BEGIN
    UPDATE knowledge_fts
    SET payload = NEW.payload,
        source = NEW.source,
        status = NEW.status
    WHERE rowid = OLD.rowid;
END;

DROP TRIGGER IF EXISTS knowledge_fts_delete;
CREATE TRIGGER knowledge_fts_delete AFTER DELETE ON knowledge
BEGIN
    DELETE FROM knowledge_fts WHERE rowid = OLD.rowid;
END;
