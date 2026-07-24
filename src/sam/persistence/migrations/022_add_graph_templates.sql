-- ============================================================================
-- Migration 022: Add graph templates table
-- Sprint 22 – Reasoning Runtime, Fase 2: Planning Engine
-- ============================================================================
--
-- Purpose:
--   graph_templates – stores reusable execution graph templates that
--   the Planning Engine uses to translate Intents into Execution Graphs.
--

CREATE TABLE IF NOT EXISTS graph_templates (
    id                  TEXT NOT NULL PRIMARY KEY,
    intent_type         TEXT NOT NULL,     -- DIAGNOSE, REPAIR, OPTIMIZE, MONITOR, DEPLOY, ROLLBACK, SCALE, CUSTOM
    name                TEXT NOT NULL,
    description         TEXT NOT NULL DEFAULT '',
    nodes_json          TEXT NOT NULL DEFAULT '[]',
    dependencies_json   TEXT NOT NULL DEFAULT '[]',
    retry_policy_json   TEXT DEFAULT NULL,
    compensation_policy_json TEXT DEFAULT NULL,
    metadata_json       TEXT NOT NULL DEFAULT '{}',
    created_at          TEXT NOT NULL,
    updated_at          TEXT DEFAULT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_graph_templates_intent_type
    ON graph_templates (intent_type);

CREATE INDEX IF NOT EXISTS idx_graph_templates_name
    ON graph_templates (name);
