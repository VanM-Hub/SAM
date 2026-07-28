-- Initial schema: Missions, Timeline, Checkpoints, Workspace Locks, Scheduler Queue
-- OP-133: Mission Persistence

CREATE TABLE IF NOT EXISTS missions (
    mission_id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL DEFAULT 'CREATED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata_json TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS mission_timeline (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id TEXT NOT NULL REFERENCES missions(mission_id),
    event_type TEXT NOT NULL,
    description TEXT DEFAULT '',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_timeline_mission ON mission_timeline(mission_id);
CREATE INDEX idx_timeline_type ON mission_timeline(event_type);
CREATE INDEX idx_timeline_ts ON mission_timeline(timestamp);

CREATE TABLE IF NOT EXISTS mission_checkpoints (
    checkpoint_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id TEXT NOT NULL REFERENCES missions(mission_id),
    step_index INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL DEFAULT 'CREATED',
    note TEXT DEFAULT '',
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cp_mission ON mission_checkpoints(mission_id);

CREATE TABLE IF NOT EXISTS workspace_locks (
    lock_id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource TEXT NOT NULL,
    mission_id TEXT NOT NULL,
    reason TEXT DEFAULT '',
    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    timeout_minutes INTEGER DEFAULT 5,
    UNIQUE(resource)
);

CREATE INDEX idx_locks_mission ON workspace_locks(mission_id);

CREATE TABLE IF NOT EXISTS scheduler_queue (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'NORMAL',
    resources TEXT DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'pending',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_queue_status ON scheduler_queue(status);
CREATE INDEX idx_queue_priority ON scheduler_queue(priority);
