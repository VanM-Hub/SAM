-- Migration 039: Add attention management tables
--
-- Creates:
--   attention_profiles   — history of SAM's attentional focus decisions

-- ═══════════════════════════════════════════════════════════════════
-- 1. attention_profiles
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS attention_profiles (
    id              TEXT PRIMARY KEY,
    primary_focus   TEXT NOT NULL DEFAULT 'balanced',
    secondary_focus TEXT,                                    -- nullable
    weights         TEXT NOT NULL DEFAULT '{}',              -- JSON weight dict
    reason          TEXT NOT NULL DEFAULT '',
    confidence      REAL NOT NULL DEFAULT 1.0,
    timestamp       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_attention_ts
    ON attention_profiles (timestamp);

CREATE INDEX IF NOT EXISTS idx_attention_focus
    ON attention_profiles (primary_focus);
