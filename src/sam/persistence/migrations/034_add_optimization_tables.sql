-- Sprint 28 Fase 1 — optimization tables
-- Optimizable Parameters + Optimization History

CREATE TABLE IF NOT EXISTS optimizable_params (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    current_value TEXT NOT NULL,
    min_value TEXT,
    max_value TEXT,
    step TEXT,
    category TEXT NOT NULL CHECK (category IN ('RANKING', 'SCHEDULER', 'RETRY', 'BUDGET', 'TEMPLATE')),
    description TEXT NOT NULL DEFAULT '',
    last_updated TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS optimization_history (
    id TEXT PRIMARY KEY,
    param_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    evidence TEXT NOT NULL DEFAULT '[]',
    confidence REAL NOT NULL DEFAULT 1.0 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    applied_at TEXT NOT NULL DEFAULT (datetime('now')),
    success_metric REAL
);

CREATE INDEX idx_opt_params_category ON optimizable_params(category);
CREATE INDEX idx_opt_params_name ON optimizable_params(name);
CREATE INDEX idx_opt_history_param ON optimization_history(param_name);
CREATE INDEX idx_opt_history_applied ON optimization_history(applied_at);
