-- Migration 037: Add evolutionary architecture tables
--
-- Creates:
--   architecture_snapshots   — snapshots of evolutionary architecture state
--   template_variants        — tracked variants of evolutionary templates

-- ═══════════════════════════════════════════════════════════════════
-- 1. architecture_snapshots
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS architecture_snapshots (
    id              TEXT PRIMARY KEY,
    version         TEXT NOT NULL DEFAULT '1.0.0',
    components      TEXT NOT NULL DEFAULT '{}',         -- JSON list of component descriptors
    dependencies    TEXT NOT NULL DEFAULT '{}',         -- JSON dependency graph
    constraints     TEXT NOT NULL DEFAULT '{}',         -- JSON architectural constraints
    timestamp       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_as_version
    ON architecture_snapshots (version);

CREATE INDEX IF NOT EXISTS idx_as_ts
    ON architecture_snapshots (timestamp);


-- ═══════════════════════════════════════════════════════════════════
-- 2. template_variants
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS template_variants (
    id              TEXT PRIMARY KEY,
    template_id     TEXT NOT NULL,
    variant_type    TEXT NOT NULL DEFAULT 'aggressive',  -- aggressive, conservative, custom
    config_delta    TEXT NOT NULL DEFAULT '{}',           -- JSON diff from base template
    performance     TEXT NOT NULL DEFAULT '{}',           -- JSON performance metrics
    applied_count   INTEGER NOT NULL DEFAULT 0,
    success_rate    REAL NOT NULL DEFAULT 0.0,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_tv_template
    ON template_variants (template_id);

CREATE INDEX IF NOT EXISTS idx_tv_type
    ON template_variants (variant_type);
