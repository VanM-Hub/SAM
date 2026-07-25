-- Sprint 25 – Migration 027: Add institutional memory and lessons tables.
-- Fase 1: Institutional Intelligence — Institutional Memory.

-- Institutional memory: stores knowledge, patterns, recommendations, lessons
-- that persist across workflows and clusters.
CREATE TABLE IF NOT EXISTS institutional_memory (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK(type IN ('KNOWLEDGE', 'PATTERN', 'RECOMMENDATION', 'LESSON')),
    content TEXT NOT NULL DEFAULT '{}',
    source TEXT NOT NULL DEFAULT '',
    confidence REAL NOT NULL DEFAULT 1.0 CHECK(confidence >= 0.0 AND confidence <= 1.0),
    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    last_used_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_institutional_memory_type ON institutional_memory(type);
CREATE INDEX IF NOT EXISTS idx_institutional_memory_confidence ON institutional_memory(confidence DESC);
CREATE INDEX IF NOT EXISTS idx_institutional_memory_last_used ON institutional_memory(last_used_at DESC);

-- Lessons learned from intent execution history.
CREATE TABLE IF NOT EXISTS lessons (
    id TEXT PRIMARY KEY,
    intent_id TEXT NOT NULL,
    graph_id TEXT NOT NULL,
    what_worked TEXT NOT NULL DEFAULT '',
    what_failed TEXT NOT NULL DEFAULT '',
    insight TEXT NOT NULL DEFAULT '',
    confidence REAL NOT NULL DEFAULT 1.0 CHECK(confidence >= 0.0 AND confidence <= 1.0),
    evidence_ids TEXT NOT NULL DEFAULT '[]',
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_lessons_intent_id ON lessons(intent_id);
CREATE INDEX IF NOT EXISTS idx_lessons_graph_id ON lessons(graph_id);
CREATE INDEX IF NOT EXISTS idx_lessons_timestamp ON lessons(timestamp DESC);
