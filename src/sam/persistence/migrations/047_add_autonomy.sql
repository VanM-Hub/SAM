-- Migration 047: Add autonomy tables
--
-- Creates:
--   autonomy_history     — autonomy level changes
--   guardrails           — guardrail rules
--   escalations          — human escalation requests
--   degradation_history  — degradation/upgrade events

-- ═══════════════════════════════════════════════════════════════════
-- 1. autonomy_history
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS autonomy_history (
    id              TEXT PRIMARY KEY,
    old_level       TEXT NOT NULL,
    new_level       TEXT NOT NULL,
    reason          TEXT NOT NULL DEFAULT '',
    confidence      REAL NOT NULL DEFAULT 100.0,
    timestamp       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_ah_ts
    ON autonomy_history (timestamp);


-- ═══════════════════════════════════════════════════════════════════
-- 2. guardrails
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS guardrails (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL DEFAULT '',
    description     TEXT NOT NULL DEFAULT '',
    condition       TEXT NOT NULL DEFAULT '{}',      -- JSON
    on_violation    TEXT NOT NULL DEFAULT 'block',
    enabled         INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);


-- ═══════════════════════════════════════════════════════════════════
-- 3. escalations
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS escalations (
    id              TEXT PRIMARY KEY,
    issue           TEXT NOT NULL DEFAULT '',
    reason          TEXT NOT NULL DEFAULT '',
    context         TEXT NOT NULL DEFAULT '{}',      -- JSON
    status          TEXT NOT NULL DEFAULT 'PENDING',
    decision        TEXT NOT NULL DEFAULT '',
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    resolved_at     TEXT,
    ttl             INTEGER NOT NULL DEFAULT 3600
);

CREATE INDEX IF NOT EXISTS idx_esc_status
    ON escalations (status);


-- ═══════════════════════════════════════════════════════════════════
-- 4. degradation_history
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS degradation_history (
    id              TEXT PRIMARY KEY,
    old_level       TEXT NOT NULL,
    new_level       TEXT NOT NULL,
    reason          TEXT NOT NULL DEFAULT '',
    change_type     TEXT NOT NULL DEFAULT 'degrade',  -- degrade or upgrade
    timestamp       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_dh_ts
    ON degradation_history (timestamp);
