-- Migration 012: Add Job Queue Tables
-- Creates tables for persistent Job Queue with SQLite backend

-- Jobs table (immutable job definition)
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    payload TEXT DEFAULT '{}',
    priority INTEGER DEFAULT 0,
    correlation_id TEXT,
    created_at TEXT NOT NULL,
    scheduled_at TEXT,
    timeout_seconds INTEGER,
    max_attempts INTEGER DEFAULT 3
);

-- Job records table (mutable status tracking)
CREATE TABLE IF NOT EXISTS job_records (
    job_id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'pending',
    started_at TEXT,
    completed_at TEXT,
    error TEXT,
    attempts INTEGER DEFAULT 0,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_job_records_status ON job_records(status);
CREATE INDEX IF NOT EXISTS idx_job_records_priority ON job_records(job_id, status);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_correlation ON jobs(correlation_id);
