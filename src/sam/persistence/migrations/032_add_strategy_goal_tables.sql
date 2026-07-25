-- Sprint 27 – Migration 032: Add strategic goal and long-term objective tables.
-- Fase 1: Strategic Planning — Strategic Goal & Long-Term Objective.

CREATE TABLE IF NOT EXISTS strategic_goals (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    horizon TEXT NOT NULL DEFAULT 'LONG_TERM'
        CHECK(horizon IN ('SHORT_TERM', 'MEDIUM_TERM', 'LONG_TERM')),
    target_metrics TEXT NOT NULL DEFAULT '{}',
    current_metrics TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK(status IN ('ACTIVE', 'PAUSED', 'COMPLETED', 'FAILED', 'ARCHIVED')),
    priority INTEGER NOT NULL DEFAULT 5 CHECK(priority >= 1 AND priority <= 10),
    parent_goal_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (parent_goal_id) REFERENCES strategic_goals(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS long_term_objectives (
    id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    strategic_goal_ids TEXT NOT NULL DEFAULT '[]',
    timeline TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK(status IN ('ACTIVE', 'ACHIEVED', 'ABANDONED')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sg_status ON strategic_goals(status);
CREATE INDEX IF NOT EXISTS idx_sg_priority ON strategic_goals(priority);
CREATE INDEX IF NOT EXISTS idx_sg_parent ON strategic_goals(parent_goal_id);
CREATE INDEX IF NOT EXISTS idx_sg_horizon ON strategic_goals(horizon);
CREATE INDEX IF NOT EXISTS idx_lto_status ON long_term_objectives(status);
