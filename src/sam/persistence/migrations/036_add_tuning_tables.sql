-- Migration 036: Add tuning tables for Performance Autotuning
--
-- Creates:
--   performance_metrics      — sampled runtime metrics (CPU, memory, queue, etc.)
--   tuning_history           — record of applied tuning changes

-- ═══════════════════════════════════════════════════════════════════
-- 1. performance_metrics
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS performance_metrics (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    value           REAL NOT NULL,
    timestamp       TEXT NOT NULL,  -- ISO-8601 UTC
    source          TEXT NOT NULL DEFAULT '',
    metadata        TEXT NOT NULL DEFAULT '{}',  -- JSON
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_perf_metrics_name
    ON performance_metrics (name);

CREATE INDEX IF NOT EXISTS idx_perf_metrics_timestamp
    ON performance_metrics (timestamp);

CREATE INDEX IF NOT EXISTS idx_perf_metrics_name_ts
    ON performance_metrics (name, timestamp);


-- ═══════════════════════════════════════════════════════════════════
-- 2. tuning_history
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS tuning_history (
    id              TEXT PRIMARY KEY,
    param_name      TEXT NOT NULL,
    old_value       TEXT NOT NULL DEFAULT '',   -- JSON-encoded old value
    new_value       TEXT NOT NULL DEFAULT '',   -- JSON-encoded new value
    reason          TEXT NOT NULL DEFAULT '',
    confidence      REAL NOT NULL DEFAULT 0.0,
    risk_level      TEXT NOT NULL DEFAULT 'low',
    success         INTEGER NOT NULL DEFAULT 1, -- 1 = success, 0 = rollback
    applied_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    suggestion_id   TEXT,                       -- FK to proposals table (optional)
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_tuning_history_param
    ON tuning_history (param_name);

CREATE INDEX IF NOT EXISTS idx_tuning_history_applied
    ON tuning_history (applied_at);
