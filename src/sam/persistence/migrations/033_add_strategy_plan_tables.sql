-- Sprint 27 – Migration 033: Add strategic plan tables.
-- Fase 2: Strategy Planner — Strategic Plan storage.

CREATE TABLE IF NOT EXISTS strategic_plans (
    id TEXT PRIMARY KEY,
    strategic_goal_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    phases TEXT NOT NULL DEFAULT '[]',
    estimated_duration_days INTEGER NOT NULL DEFAULT 30,
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK(status IN ('PENDING', 'ACTIVE', 'COMPLETED', 'FAILED', 'PAUSED')),
    current_phase_index INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (strategic_goal_id) REFERENCES strategic_goals(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sp_goal ON strategic_plans(strategic_goal_id);
CREATE INDEX IF NOT EXISTS idx_sp_status ON strategic_plans(status);

CREATE TABLE IF NOT EXISTS plan_intents (
    id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    phase_index INTEGER NOT NULL,
    intent_data TEXT NOT NULL,
    intent_type TEXT NOT NULL DEFAULT 'CUSTOM',
    target TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK(status IN ('PENDING', 'PLANNING', 'APPROVED', 'EXECUTING', 'COMPLETED', 'FAILED')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (plan_id) REFERENCES strategic_plans(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_pi_plan ON plan_intents(plan_id, phase_index);
CREATE INDEX IF NOT EXISTS idx_pi_status ON plan_intents(status);
