-- Sprint 24 – Migration 026: Add healing_actions and degradation_history tables.
-- Supports Fase 3: Predictive Self-Healing & Graceful Degradation.

-- Healing actions registry
CREATE TABLE IF NOT EXISTS healing_actions (
    id TEXT PRIMARY KEY,
    trigger TEXT NOT NULL,
    strategy TEXT NOT NULL DEFAULT 'repair',
    action_graph TEXT NOT NULL DEFAULT '[]',
    precondition TEXT,
    cooldown INTEGER NOT NULL DEFAULT 300,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_run_at TEXT,
    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_healing_actions_trigger ON healing_actions(trigger);

-- Degradation audit history
CREATE TABLE IF NOT EXISTS degradation_history (
    id TEXT PRIMARY KEY,
    previous_level TEXT NOT NULL,
    new_level TEXT NOT NULL,
    reason TEXT NOT NULL,
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_degradation_history_ts ON degradation_history(timestamp DESC);
