-- Migration 040: Add arbitration tables
--
-- Creates:
--   arbitration_history   — record of goal arbitration decisions

-- ═══════════════════════════════════════════════════════════════════
-- 1. arbitration_history
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS arbitration_history (
    id              TEXT PRIMARY KEY,
    selected_goal   TEXT NOT NULL,
    reason          TEXT NOT NULL DEFAULT '',
    confidence      REAL NOT NULL DEFAULT 0.0,
    scores          TEXT NOT NULL DEFAULT '{}',      -- JSON dict of goal -> score
    runner_up       TEXT,                            -- nullable
    timestamp       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_arbitration_ts
    ON arbitration_history (timestamp);
