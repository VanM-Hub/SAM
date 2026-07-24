-- Migration 017: Add cluster_leader table for lease-based leader election

CREATE TABLE IF NOT EXISTS cluster_leader (
    leader_id         TEXT NOT NULL,
    cluster_id        TEXT NOT NULL PRIMARY KEY,
    term              INTEGER NOT NULL DEFAULT 1,
    lease_expires_at  TEXT NOT NULL,
    elected_at        TEXT NOT NULL
);
