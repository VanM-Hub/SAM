-- ============================================================================
-- Migration 020: Add governance tables
-- Sprint 21 – Governance Engine
-- ============================================================================
--
-- Purpose:
--   governance_rules  – registered governance rules (conditions, overrides)
--   governance_results – evaluation outcomes keyed by graph_id
--

-- Governance Rules table
CREATE TABLE IF NOT EXISTS governance_rules (
    id               TEXT    NOT NULL PRIMARY KEY,
    name             TEXT    NOT NULL,
    evaluator_type   TEXT    NOT NULL,  -- RISK, APPROVAL, MAINTENANCE, CLUSTER, RESOURCE, CAPABILITY, POLICY
    condition        TEXT    NOT NULL DEFAULT '',
    decision_override TEXT   DEFAULT NULL,  -- optional: overrides natural evaluator decision
    enabled          INTEGER NOT NULL DEFAULT 1,
    metadata_json    TEXT    NOT NULL DEFAULT '{}',
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL
);

-- Governance Results table
CREATE TABLE IF NOT EXISTS governance_results (
    id                  TEXT NOT NULL PRIMARY KEY,
    graph_id            TEXT NOT NULL,
    decision            TEXT NOT NULL,  -- ALLOW, ALLOW_WITH_WARNING, WAIT, REQUIRE_APPROVAL, REJECT, ESCALATE
    reason              TEXT NOT NULL DEFAULT '',
    warnings_json       TEXT NOT NULL DEFAULT '[]',
    required_approvals_json TEXT NOT NULL DEFAULT '[]',
    evaluator_results_json TEXT NOT NULL DEFAULT '{}',
    suggested_delay     INTEGER DEFAULT NULL,
    metadata_json       TEXT NOT NULL DEFAULT '{}',
    created_at          TEXT NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_governance_results_graph_id
    ON governance_results (graph_id);

CREATE INDEX IF NOT EXISTS idx_governance_results_decision
    ON governance_results (decision);

CREATE INDEX IF NOT EXISTS idx_governance_rules_evaluator_type
    ON governance_rules (evaluator_type);

CREATE INDEX IF NOT EXISTS idx_governance_rules_enabled
    ON governance_rules (enabled);
