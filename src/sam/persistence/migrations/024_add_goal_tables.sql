-- Sprint 24 – Migration 024: Add goal and goal_relationship tables.
-- These tables support the Goal Tree feature — storing discrete goals
-- and their parent-child relationships for hierarchical progress tracking.

-- Goals table
CREATE TABLE IF NOT EXISTS goals (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    target_state TEXT NOT NULL DEFAULT '{}',
    metrics TEXT NOT NULL DEFAULT '[]',
    autonomy_level INTEGER NOT NULL DEFAULT 2,
    priority INTEGER NOT NULL DEFAULT 5,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Goal hierarchy relationships
CREATE TABLE IF NOT EXISTS goal_relationships (
    parent_id TEXT NOT NULL,
    child_id TEXT NOT NULL UNIQUE,
    PRIMARY KEY (parent_id, child_id),
    FOREIGN KEY (parent_id) REFERENCES goals(id) ON DELETE CASCADE,
    FOREIGN KEY (child_id) REFERENCES goals(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_goal_relationships_child ON goal_relationships(child_id);
CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);
CREATE INDEX IF NOT EXISTS idx_goals_priority ON goals(priority);
