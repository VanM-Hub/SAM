-- OP-137: Trust, Benchmark, Failure Pattern, Quality schemas

CREATE TABLE IF NOT EXISTS trust_scores (
    score_id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT,
    score REAL NOT NULL DEFAULT 0.0,
    grade TEXT DEFAULT 'C',
    components_json TEXT DEFAULT '{}',
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trust_decision ON trust_scores(decision_id);
CREATE INDEX idx_trust_time ON trust_scores(calculated_at);

CREATE TABLE IF NOT EXISTS trust_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    score_id INTEGER REFERENCES trust_scores(score_id),
    decision_id TEXT,
    previous_score REAL,
    new_score REAL,
    previous_grade TEXT,
    new_grade TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_th_decision ON trust_history(decision_id);

CREATE TABLE IF NOT EXISTS benchmark_results (
    benchmark_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    metrics_json TEXT DEFAULT '{}',
    overall_grade TEXT DEFAULT 'C',
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_benchmark_time ON benchmark_results(executed_at);

CREATE TABLE IF NOT EXISTS failure_patterns (
    pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_type TEXT NOT NULL,
    frequency INTEGER DEFAULT 0,
    description TEXT DEFAULT '',
    trend TEXT DEFAULT 'stable',
    recommendation TEXT DEFAULT '',
    last_observed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fp_type ON failure_patterns(pattern_type);

CREATE TABLE IF NOT EXISTS decision_quality (
    quality_id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT,
    metrics_json TEXT DEFAULT '{}',
    overall_score REAL DEFAULT 0.0,
    assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dq_decision ON decision_quality(decision_id);

CREATE TABLE IF NOT EXISTS replay_results (
    replay_id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT,
    result_json TEXT DEFAULT '{}',
    replayed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rr_decision ON replay_results(decision_id);
