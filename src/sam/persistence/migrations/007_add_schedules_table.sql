-- Migration 007: Add schedules table
-- Date: 2026-07-23

CREATE TABLE IF NOT EXISTS schedules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    workflow_file TEXT NOT NULL,
    schedule_type TEXT NOT NULL,  -- 'once', 'interval', 'cron'
    cron_expression TEXT,         -- for cron type
    delay_seconds INTEGER,        -- for interval type (repeat interval)
    max_retries INTEGER DEFAULT 3,
    retry_delay INTEGER DEFAULT 60,
    enabled INTEGER DEFAULT 1,    -- 1 = true, 0 = false
    status TEXT DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'disabled'
    last_run TEXT,                -- ISO timestamp
    next_run TEXT,                -- ISO timestamp
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    run_count INTEGER DEFAULT 0,
    last_error TEXT,
    metadata TEXT DEFAULT '{}'    -- JSON
);

CREATE INDEX IF NOT EXISTS idx_schedules_enabled ON schedules(enabled);
CREATE INDEX IF NOT EXISTS idx_schedules_status ON schedules(status);
CREATE INDEX IF NOT EXISTS idx_schedules_next_run ON schedules(next_run);