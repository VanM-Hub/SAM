-- Migration 002: Add correlation_id columns to core tables
-- This migration adds correlation tracking to all persistent entities

-- Add correlation_id to evidence table
ALTER TABLE evidence ADD COLUMN correlation_id TEXT;

-- Add correlation_id to knowledge table
ALTER TABLE knowledge ADD COLUMN correlation_id TEXT;

-- Add correlation_id to patterns table
ALTER TABLE patterns ADD COLUMN correlation_id TEXT;

-- Add correlation_id to recommendations table
ALTER TABLE recommendations ADD COLUMN correlation_id TEXT;

-- Add correlation_id to approvals table
ALTER TABLE approvals ADD COLUMN correlation_id TEXT;

-- Add correlation_id to executions table (if exists)
-- Note: execution table might not exist in 001, add if needed

-- Indexes for correlation_id queries
CREATE INDEX IF NOT EXISTS idx_evidence_correlation ON evidence(correlation_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_correlation ON knowledge(correlation_id);
CREATE INDEX IF NOT EXISTS idx_patterns_correlation ON patterns(correlation_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_correlation ON recommendations(correlation_id);
CREATE INDEX IF NOT EXISTS idx_approvals_correlation ON approvals(correlation_id);