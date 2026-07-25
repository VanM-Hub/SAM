-- Sprint 26 – Migration 030: Add message tables for Agent Communication Protocol.
-- Fase 2: Multi-Agent Collaboration — Agent Communication Protocol.

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL
        CHECK(type IN ('REQUEST', 'RESPONSE', 'BROADCAST',
                       'KNOWLEDGE_SHARE', 'TASK_DELEGATE', 'HEARTBEAT', 'ERROR')),
    sender_id TEXT NOT NULL,
    receiver_id TEXT,
    correlation_id TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'NORMAL'
        CHECK(priority IN ('LOW', 'NORMAL', 'HIGH', 'CRITICAL')),
    payload TEXT NOT NULL DEFAULT '{}',
    timestamp TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'SENT'
        CHECK(status IN ('SENT', 'DELIVERED', 'READ', 'FAILED')),
    FOREIGN KEY (sender_id) REFERENCES agents(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES agents(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_receiver ON messages(receiver_id);
CREATE INDEX IF NOT EXISTS idx_messages_correlation ON messages(correlation_id);
CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
