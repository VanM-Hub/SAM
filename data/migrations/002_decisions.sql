-- OP-134, OP-135: Decision, Approval, Audit schemas

CREATE TABLE IF NOT EXISTS decisions (
    decision_id TEXT PRIMARY KEY,
    intent TEXT NOT NULL DEFAULT '',
    context_json TEXT DEFAULT '{}',
    reasoning_json TEXT DEFAULT '{}',
    confidence REAL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'proposed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_decisions_status ON decisions(status);
CREATE INDEX idx_decisions_created ON decisions(created_at);

CREATE TABLE IF NOT EXISTS decision_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT NOT NULL REFERENCES decisions(decision_id),
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dh_decision ON decision_history(decision_id);

CREATE TABLE IF NOT EXISTS execution_plans (
    plan_id TEXT PRIMARY KEY,
    decision_id TEXT REFERENCES decisions(decision_id),
    steps_json TEXT DEFAULT '[]',
    rationale TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alternatives (
    alternative_id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT NOT NULL REFERENCES decisions(decision_id),
    label TEXT NOT NULL,
    description TEXT DEFAULT '',
    impact_json TEXT DEFAULT '{}',
    score REAL DEFAULT 0.0
);

CREATE INDEX idx_alt_decision ON alternatives(decision_id);

CREATE TABLE IF NOT EXISTS approvals (
    approval_id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT REFERENCES decisions(decision_id),
    action_id TEXT NOT NULL,
    requestor TEXT DEFAULT 'SAM',
    status TEXT NOT NULL DEFAULT 'pending',
    reviewer TEXT DEFAULT '',
    reason TEXT DEFAULT '',
    comment TEXT DEFAULT '',
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE INDEX idx_approvals_status ON approvals(status);
CREATE INDEX idx_approvals_decision ON approvals(decision_id);

CREATE TABLE IF NOT EXISTS approvals_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    approval_id INTEGER NOT NULL REFERENCES approvals(approval_id),
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ah_approval ON approvals_history(approval_id);

CREATE TABLE IF NOT EXISTS audit_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL DEFAULT 'system',
    action TEXT NOT NULL,
    actor TEXT DEFAULT 'SAM',
    target_type TEXT DEFAULT '',
    target_id TEXT DEFAULT '',
    detail_json TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_source ON audit_events(source);
CREATE INDEX idx_audit_action ON audit_events(action);
CREATE INDEX idx_audit_actor ON audit_events(actor);
CREATE INDEX idx_audit_target ON audit_events(target_type, target_id);
CREATE INDEX idx_audit_created ON audit_events(created_at);
