-- Sprint 25 – Migration 028: Add template evolution table.
-- Fase 2: Institutional Intelligence — Template Evolution.

CREATE TABLE IF NOT EXISTS template_evolutions (
    id TEXT PRIMARY KEY,
    template_id TEXT NOT NULL,
    original_version TEXT NOT NULL,
    new_version TEXT NOT NULL,
    changes TEXT NOT NULL DEFAULT '[]',
    reason TEXT NOT NULL DEFAULT '',
    evidence TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'PROPOSED'
        CHECK(status IN ('PROPOSED', 'APPROVED', 'REJECTED', 'APPLIED', 'ROLLED_BACK')),
    proposed_at TEXT NOT NULL,
    applied_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tmpl_evolutions_template_id ON template_evolutions(template_id);
CREATE INDEX IF NOT EXISTS idx_tmpl_evolutions_status ON template_evolutions(status);
CREATE INDEX IF NOT EXISTS idx_tmpl_evolutions_proposed ON template_evolutions(proposed_at DESC);
