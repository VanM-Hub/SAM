-- ============================================================================
-- Migration 021: Add intent tables
-- Sprint 22 – Reasoning Runtime, Fase 1
-- ============================================================================
--
-- Purpose:
--   intents – stores structured intents (user requests) that flow through
--             the Reasoning Engine: Intent → Plan → Graph → Governance → Execute.
--

CREATE TABLE IF NOT EXISTS intents (
    id              TEXT     NOT NULL PRIMARY KEY,
    type            TEXT     NOT NULL,  -- DIAGNOSE, REPAIR, OPTIMIZE, MONITOR, DEPLOY, ROLLBACK, SCALE, CUSTOM
    target          TEXT     NOT NULL DEFAULT '',
    description     TEXT     NOT NULL DEFAULT '',
    parameters_json TEXT     NOT NULL DEFAULT '{}',
    context_json    TEXT     NOT NULL DEFAULT '{}',
    correlation_id  TEXT     NOT NULL DEFAULT '',
    status          TEXT     NOT NULL DEFAULT 'PENDING',  -- PENDING, PLANNING, APPROVED, EXECUTING, COMPLETED, FAILED
    created_at      TEXT     NOT NULL,
    updated_at      TEXT     DEFAULT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_intents_type ON intents (type);
CREATE INDEX IF NOT EXISTS idx_intents_status ON intents (status);
CREATE INDEX IF NOT EXISTS idx_intents_correlation_id ON intents (correlation_id);
CREATE INDEX IF NOT EXISTS idx_intents_target ON intents (target);
