-- Sprint 24 – Migration 025: Add autonomy_configs and cognitive_budgets tables.
-- Supports Fase 2: Autonomy Levels & Cognitive Budget.

-- Autonomy configuration per goal
CREATE TABLE IF NOT EXISTS autonomy_configs (
    goal_id TEXT PRIMARY KEY,
    min_autonomy_level TEXT NOT NULL DEFAULT 'observe_only',
    max_autonomy_level TEXT NOT NULL DEFAULT 'full_autonomy',
    override_rules TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Cognitive budget definitions
CREATE TABLE IF NOT EXISTS cognitive_budgets (
    id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL DEFAULT '__system__',
    reasoning_cycles INTEGER NOT NULL DEFAULT 5,
    planning_attempts INTEGER NOT NULL DEFAULT 3,
    revision_count INTEGER NOT NULL DEFAULT 3,
    learning_iterations INTEGER NOT NULL DEFAULT 10,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cognitive_budgets_goal ON cognitive_budgets(goal_id);
