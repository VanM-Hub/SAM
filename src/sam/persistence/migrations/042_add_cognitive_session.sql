-- Migration 042: Add cognitive session table
--
-- Creates:
--   cognitive_sessions   — per-reasoning-cycle session tracking

-- ═══════════════════════════════════════════════════════════════════
-- 1. cognitive_sessions
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS cognitive_sessions (
    id                      TEXT PRIMARY KEY,
    goal_id                 TEXT,
    intent_id               TEXT,
    state                   TEXT NOT NULL DEFAULT '{}',              -- JSON CognitiveState
    working_memory_snapshot TEXT NOT NULL DEFAULT '{}',              -- JSON dict
    reflection_ids          TEXT NOT NULL DEFAULT '[]',              -- JSON list of IDs
    decisions               TEXT NOT NULL DEFAULT '[]',              -- JSON list of dicts
    status                  TEXT NOT NULL DEFAULT 'ACTIVE',          -- ACTIVE|COMPLETED|ABANDONED
    started_at              TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    ended_at                TEXT,                                    -- nullable
    created_at              TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_cs_status
    ON cognitive_sessions (status);

CREATE INDEX IF NOT EXISTS idx_cs_started
    ON cognitive_sessions (started_at);
