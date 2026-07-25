-- Migration 038: Add cognitive state tables
--
-- Creates:
--   cognitive_state_history   — snapshots of SAM's cognitive state
--   working_memory            — per-session key-value working memory

-- ═══════════════════════════════════════════════════════════════════
-- 1. cognitive_state_history
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS cognitive_state_history (
    id              TEXT PRIMARY KEY,
    state           TEXT NOT NULL DEFAULT '{}',   -- JSON-encoded CognitiveState
    timestamp       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_cog_state_ts
    ON cognitive_state_history (timestamp);


-- ═══════════════════════════════════════════════════════════════════
-- 2. working_memory
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS working_memory (
    id              TEXT PRIMARY KEY,
    session_id      TEXT NOT NULL DEFAULT 'default',
    key             TEXT NOT NULL,
    value           TEXT NOT NULL DEFAULT '',     -- JSON-encoded value
    ttl             INTEGER NOT NULL DEFAULT 300, -- seconds; 0 = no expiry
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_wm_session
    ON working_memory (session_id);

CREATE INDEX IF NOT EXISTS idx_wm_session_key
    ON working_memory (session_id, key);
