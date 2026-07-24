-- Migration 041: Add context window table
--
-- Creates:
--   context_window   — SAM's runtime context items (TTL-based, importance-filtered)

-- ═══════════════════════════════════════════════════════════════════
-- 1. context_window
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS context_window (
    id              TEXT PRIMARY KEY,
    key             TEXT NOT NULL UNIQUE,
    value           TEXT NOT NULL DEFAULT '',      -- JSON-encoded value
    importance      REAL NOT NULL DEFAULT 0.5,
    ttl             INTEGER NOT NULL DEFAULT 300,  -- seconds; 0 = no expiry
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    expires_at      TEXT                           -- nullable; ISO-8601 UTC
);

CREATE INDEX IF NOT EXISTS idx_cw_key
    ON context_window (key);

CREATE INDEX IF NOT EXISTS idx_cw_expires
    ON context_window (expires_at);

CREATE INDEX IF NOT EXISTS idx_cw_importance
    ON context_window (importance);
