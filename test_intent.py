"""
Test Intent Models – Sprint 22 Fase 1

Covers:
- IntentType enum values
- IntentStatus enum values
- Intent model creation, defaults, state transitions, is_terminal
- IntentParser rule-based parsing (keyword matching, target extraction, parameter extraction)
- Persistence via migration 021
"""

import asyncio
import pytest
import sqlite3
import os
from datetime import datetime
from typing import Optional

from src.sam.reasoning.intent import (
    Intent,
    IntentType,
    IntentStatus,
    IntentParser,
)


# ── Test Data ────────────────────────────────────────────────────────


def _make_db(path: str) -> sqlite3.Connection:
    """Create an in-memory SQLite database with migration 021 applied."""
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    migration_path = os.path.join(
        os.path.dirname(__file__),
        "src", "sam", "persistence", "migrations",
        "021_add_intent_tables.sql",
    )
    with open(migration_path, "r", encoding="utf-8") as f:
        sql = f.read()
    db.executescript(sql)
    db.commit()
    return db


# ── 1. IntentType Enum ───────────────────────────────────────────────


class TestIntentType:
    """Test IntentType enum values."""

    def test_all_values(self):
        expected = {
            "DIAGNOSE", "REPAIR", "OPTIMIZE", "MONITOR",
            "DEPLOY", "ROLLBACK", "SCALE", "CUSTOM",
        }
        actual = {t.value for t in IntentType}
        assert actual == expected

    def test_values_are_distinct(self):
        values = [t.value for t in IntentType]
        assert len(values) == len(set(values))


# ── 2. IntentStatus Enum ─────────────────────────────────────────────


class TestIntentStatus:
    """Test IntentStatus enum values."""

    def test_all_values(self):
        expected = {
            "PENDING", "PLANNING", "APPROVED",
            "EXECUTING", "COMPLETED", "FAILED",
        }
        actual = {s.value for s in IntentStatus}
        assert actual == expected


# ── 3. Intent Model ──────────────────────────────────────────────────


class TestIntentModel:
    """Test Intent creation, defaults, transitions, and terminal states."""

    def test_default_values(self):
        intent = Intent()
        assert intent.id != ""
        assert len(intent.id) == 36  # UUID
        assert intent.type == IntentType.CUSTOM
        assert intent.target == ""
        assert intent.description == ""
        assert intent.parameters == {}
        assert intent.context == {}
        assert intent.correlation_id == ""
        assert intent.status == IntentStatus.PENDING
        assert isinstance(intent.created_at, datetime)

    def test_full_creation(self):
        intent = Intent(
            id="abc-123",
            type=IntentType.DIAGNOSE,
            target="provider:nvidia",
            description="Check NVIDIA provider health",
            parameters={"verbose": True, "timeout": 30},
            context={"workspace": "default"},
            correlation_id="corr-001",
            status=IntentStatus.PENDING,
        )
        assert intent.id == "abc-123"
        assert intent.type == IntentType.DIAGNOSE
        assert intent.target == "provider:nvidia"
        assert intent.description == "Check NVIDIA provider health"
        assert intent.parameters == {"verbose": True, "timeout": 30}
        assert intent.context == {"workspace": "default"}
        assert intent.correlation_id == "corr-001"
        assert intent.status == IntentStatus.PENDING

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValueError):
            Intent(extra_field="not allowed")

    def test_mark_planning(self):
        intent = Intent()
        assert intent.status == IntentStatus.PENDING
        intent.mark_planning()
        assert intent.status == IntentStatus.PLANNING
        assert intent.updated_at is not None

    def test_mark_approved(self):
        intent = Intent()
        intent.mark_approved()
        assert intent.status == IntentStatus.APPROVED

    def test_mark_executing(self):
        intent = Intent()
        intent.mark_executing()
        assert intent.status == IntentStatus.EXECUTING

    def test_mark_completed(self):
        intent = Intent()
        intent.mark_completed()
        assert intent.status == IntentStatus.COMPLETED

    def test_mark_failed(self):
        intent = Intent()
        intent.mark_failed()
        assert intent.status == IntentStatus.FAILED

    def test_is_terminal_completed(self):
        intent = Intent(status=IntentStatus.COMPLETED)
        assert intent.is_terminal() is True

    def test_is_terminal_failed(self):
        intent = Intent(status=IntentStatus.FAILED)
        assert intent.is_terminal() is True

    def test_is_terminal_false_for_active(self):
        for status in [
            IntentStatus.PENDING,
            IntentStatus.PLANNING,
            IntentStatus.APPROVED,
            IntentStatus.EXECUTING,
        ]:
            intent = Intent(status=status)
            assert intent.is_terminal() is False, f"{status} should not be terminal"

    def test_updated_at_is_none_by_default(self):
        intent = Intent()
        assert intent.updated_at is None

    def test_updated_at_set_after_transition(self):
        intent = Intent()
        intent.mark_executing()
        assert intent.updated_at is not None


# ── 4. IntentParser ──────────────────────────────────────────────────


class TestIntentParser:
    """Test IntentParser rule-based parsing."""

    @pytest.fixture(autouse=True)
    def setup_parser(self):
        self.parser = IntentParser()

    @pytest.mark.asyncio
    async def test_empty_text_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            await self.parser.parse("")

    @pytest.mark.asyncio
    async def test_whitespace_text_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            await self.parser.parse("   ")

    # ── Keyword → Type Mapping ──────────────────────────────────

    @pytest.mark.asyncio
    async def test_diagnose_keyword(self):
        intent = await self.parser.parse("diagnose provider nvidia")
        assert intent.type == IntentType.DIAGNOSE

    @pytest.mark.asyncio
    async def test_diagnostic_keyword(self):
        intent = await self.parser.parse("diagnostic check on cluster")
        assert intent.type == IntentType.DIAGNOSE

    @pytest.mark.asyncio
    async def test_check_keyword(self):
        intent = await self.parser.parse("check workspace default")
        assert intent.type == IntentType.DIAGNOSE

    @pytest.mark.asyncio
    async def test_repair_keyword(self):
        intent = await self.parser.parse("repair provider nvidia")
        assert intent.type == IntentType.REPAIR

    @pytest.mark.asyncio
    async def test_fix_keyword(self):
        intent = await self.parser.parse("fix the broken plugin")
        assert intent.type == IntentType.REPAIR

    @pytest.mark.asyncio
    async def test_restore_keyword(self):
        intent = await self.parser.parse("restore service after crash")
        assert intent.type == IntentType.REPAIR

    @pytest.mark.asyncio
    async def test_optimize_keyword(self):
        intent = await self.parser.parse("optimize memory usage")
        assert intent.type == IntentType.OPTIMIZE

    @pytest.mark.asyncio
    async def test_optimise_uk_spelling(self):
        intent = await self.parser.parse("optimise disk space")
        assert intent.type == IntentType.OPTIMIZE

    @pytest.mark.asyncio
    async def test_tune_keyword(self):
        intent = await self.parser.parse("tune the scheduler")
        assert intent.type == IntentType.OPTIMIZE

    @pytest.mark.asyncio
    async def test_monitor_keyword(self):
        intent = await self.parser.parse("monitor cluster health")
        assert intent.type == IntentType.MONITOR

    @pytest.mark.asyncio
    async def test_watch_keyword(self):
        intent = await self.parser.parse("watch for errors")
        assert intent.type == IntentType.MONITOR

    @pytest.mark.asyncio
    async def test_deploy_keyword(self):
        intent = await self.parser.parse("deploy plugin sample-plugin")
        assert intent.type == IntentType.DEPLOY

    @pytest.mark.asyncio
    async def test_install_keyword(self):
        intent = await self.parser.parse("install new capability")
        assert intent.type == IntentType.DEPLOY

    @pytest.mark.asyncio
    async def test_rollback_keyword(self):
        intent = await self.parser.parse("rollback provider nvidia")
        assert intent.type == IntentType.ROLLBACK

    @pytest.mark.asyncio
    async def test_revert_keyword(self):
        intent = await self.parser.parse("revert last deployment")
        assert intent.type == IntentType.ROLLBACK

    @pytest.mark.asyncio
    async def test_undo_keyword(self):
        intent = await self.parser.parse("undo changes")
        assert intent.type == IntentType.ROLLBACK

    @pytest.mark.asyncio
    async def test_scale_keyword(self):
        intent = await self.parser.parse("scale up the cluster")
        assert intent.type == IntentType.SCALE

    @pytest.mark.asyncio
    async def test_grow_keyword(self):
        intent = await self.parser.parse("grow the workspace pool")
        assert intent.type == IntentType.SCALE

    @pytest.mark.asyncio
    async def test_shrink_keyword(self):
        intent = await self.parser.parse("shrink deployment size")
        assert intent.type == IntentType.SCALE

    @pytest.mark.asyncio
    async def test_custom_fallback(self):
        intent = await self.parser.parse("do something weird")
        assert intent.type == IntentType.CUSTOM

    @pytest.mark.asyncio
    async def test_highest_priority_wins(self):
        """When multiple keywords match, highest priority wins."""
        intent = await self.parser.parse("monitor and diagnose the plugin")
        # Both "monitor" (5) and "diagnose" (5); first found wins in dict order
        assert intent.type in (IntentType.DIAGNOSE, IntentType.MONITOR)

    @pytest.mark.asyncio
    async def test_case_insensitive(self):
        intent = await self.parser.parse("MONITOR Provider NVIDIA")
        assert intent.type == IntentType.MONITOR

    # ── Target Extraction ───────────────────────────────────────

    @pytest.mark.asyncio
    async def test_extract_provider_target(self):
        intent = await self.parser.parse("diagnose provider nvidia")
        assert intent.target == "provider:nvidia"

    @pytest.mark.asyncio
    async def test_extract_provider_with_colon(self):
        intent = await self.parser.parse("check provider:nvidia health")
        assert intent.target == "provider:nvidia"

    @pytest.mark.asyncio
    async def test_extract_workspace_target(self):
        intent = await self.parser.parse("repair workspace default")
        assert intent.target == "workspace:default"

    @pytest.mark.asyncio
    async def test_extract_plugin_target(self):
        intent = await self.parser.parse("deploy plugin sample-plugin")
        assert intent.target == "plugin:sample-plugin"

    @pytest.mark.asyncio
    async def test_extract_cluster_target(self):
        intent = await self.parser.parse("monitor cluster prod-01")
        assert intent.target == "cluster:prod-01"

    @pytest.mark.asyncio
    async def test_extract_service_target(self):
        intent = await self.parser.parse("restore service auth-service")
        assert intent.target == "service:auth-service"

    @pytest.mark.asyncio
    async def test_extract_node_target(self):
        intent = await self.parser.parse("diagnose node worker-3")
        assert intent.target == "node:worker-3"

    @pytest.mark.asyncio
    async def test_no_target(self):
        intent = await self.parser.parse("optimize everything")
        assert intent.target == ""

    @pytest.mark.asyncio
    async def test_first_target_wins(self):
        """When multiple targets match, first one wins."""
        intent = await self.parser.parse("diagnose provider nvidia on workspace staging")
        assert intent.target == "provider:nvidia"

    # ── Parameter Extraction ────────────────────────────────────

    @pytest.mark.asyncio
    async def test_extract_key_equals_value(self):
        intent = await self.parser.parse("deploy plugin x version=2.0 timeout=30")
        assert intent.parameters.get("version") == "2.0"
        assert intent.parameters.get("timeout") == 30

    @pytest.mark.asyncio
    async def test_extract_boolean_value_true(self):
        intent = await self.parser.parse("repair service x dry_run=true")
        assert intent.parameters["dry_run"] is True

    @pytest.mark.asyncio
    async def test_extract_boolean_value_false(self):
        intent = await self.parser.parse("repair service x confirm=no")
        assert intent.parameters["confirm"] is False

    @pytest.mark.asyncio
    async def test_extract_integer_value(self):
        intent = await self.parser.parse("scale cluster count=5")
        assert intent.parameters["count"] == 5

    @pytest.mark.asyncio
    async def test_extract_float_value(self):
        intent = await self.parser.parse("optimize threshold=0.75")
        # Floats stay as strings (version-style values)
        assert intent.parameters["threshold"] == "0.75"

    @pytest.mark.asyncio
    async def test_extract_quoted_string(self):
        intent = await self.parser.parse("deploy name='my plugin'")
        assert intent.parameters["name"] == "my plugin"

    @pytest.mark.asyncio
    async def test_extract_double_quoted_string(self):
        intent = await self.parser.parse("deploy name=\"production env\"")
        assert intent.parameters["name"] == "production env"

    @pytest.mark.asyncio
    async def test_extract_multiple_parameters(self):
        intent = await self.parser.parse(
            "scale cluster count=3 dry_run=true threshold=0.5"
        )
        assert intent.parameters["count"] == 3
        assert intent.parameters["dry_run"] is True
        assert intent.parameters["threshold"] == "0.5"

    @pytest.mark.asyncio
    async def test_no_parameters(self):
        intent = await self.parser.parse("monitor cluster")
        assert intent.parameters == {}

    # ── Context Propagation ─────────────────────────────────────

    @pytest.mark.asyncio
    async def test_context_is_passed_through(self):
        ctx = {"workspace_id": "ws-1", "user": "admin"}
        intent = await self.parser.parse("diagnose provider nvidia", context=ctx)
        assert intent.context == ctx

    @pytest.mark.asyncio
    async def test_context_defaults_to_empty(self):
        intent = await self.parser.parse("deploy plugin x")
        assert intent.context == {}

    # ── Description ─────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_description_is_original_text(self):
        intent = await self.parser.parse("diagnose provider nvidia")
        assert intent.description == "diagnose provider nvidia"

    @pytest.mark.asyncio
    async def test_description_trimmed(self):
        intent = await self.parser.parse("  monitor cluster  ")
        assert intent.description == "monitor cluster"


# ── 5. Persistence (Migration 021) ───────────────────────────────────


class TestIntentPersistence:
    """Test that the intents table from migration 021 works."""

    def test_table_exists(self):
        db = _make_db(":memory:")
        cursor = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='intents'"
        )
        assert cursor.fetchone() is not None
        db.close()

    def test_insert_and_read_intent(self):
        db = _make_db(":memory:")
        now = datetime.utcnow().isoformat()
        db.execute(
            """INSERT INTO intents
               (id, type, target, description, parameters_json, context_json,
                correlation_id, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                "int-001",
                "DIAGNOSE",
                "provider:nvidia",
                "Check NVIDIA health",
                '{"verbose":true}',
                '{"workspace":"default"}',
                "corr-001",
                "PENDING",
                now,
            ],
        )
        db.commit()

        row = db.execute("SELECT * FROM intents WHERE id = ?", ["int-001"]).fetchone()
        assert row is not None
        assert row["type"] == "DIAGNOSE"
        assert row["target"] == "provider:nvidia"
        assert row["description"] == "Check NVIDIA health"
        assert row["status"] == "PENDING"
        assert row["correlation_id"] == "corr-001"
        db.close()

    def test_default_values(self):
        db = _make_db(":memory:")
        now = datetime.utcnow().isoformat()
        db.execute(
            """INSERT INTO intents (id, type, created_at) VALUES (?, ?, ?)""",
            ["int-002", "CUSTOM", now],
        )
        db.commit()

        row = db.execute("SELECT * FROM intents WHERE id = ?", ["int-002"]).fetchone()
        assert row["target"] == ""
        assert row["description"] == ""
        assert row["parameters_json"] == "{}"
        assert row["context_json"] == "{}"
        assert row["correlation_id"] == ""
        assert row["status"] == "PENDING"
        db.close()

    def test_update_status(self):
        db = _make_db(":memory:")
        now = datetime.utcnow().isoformat()
        db.execute(
            "INSERT INTO intents (id, type, created_at) VALUES (?, ?, ?)",
            ["int-003", "DIAGNOSE", now],
        )
        db.commit()

        updated = datetime.utcnow().isoformat()
        db.execute(
            "UPDATE intents SET status = ?, updated_at = ? WHERE id = ?",
            ["EXECUTING", updated, "int-003"],
        )
        db.commit()

        row = db.execute("SELECT * FROM intents WHERE id = ?", ["int-003"]).fetchone()
        assert row["status"] == "EXECUTING"
        assert row["updated_at"] == updated
        db.close()

    def test_indexes_exist(self):
        db = _make_db(":memory:")
        indexes = db.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_intents%'"
        ).fetchall()
        index_names = {r["name"] for r in indexes}
        expected = {
            "idx_intents_type",
            "idx_intents_status",
            "idx_intents_correlation_id",
            "idx_intents_target",
        }
        assert index_names == expected
        db.close()

    def test_multiple_intents(self):
        db = _make_db(":memory:")
        now = datetime.utcnow().isoformat()
        db.execute(
            "INSERT INTO intents (id, type, created_at) VALUES (?, ?, ?)",
            ["a", "DIAGNOSE", now],
        )
        db.execute(
            "INSERT INTO intents (id, type, created_at) VALUES (?, ?, ?)",
            ["b", "REPAIR", now],
        )
        db.execute(
            "INSERT INTO intents (id, type, created_at) VALUES (?, ?, ?)",
            ["c", "DEPLOY", now],
        )
        db.commit()

        count = db.execute("SELECT COUNT(*) as cnt FROM intents").fetchone()["cnt"]
        assert count == 3
        db.close()

    def test_query_by_status(self):
        db = _make_db(":memory:")
        now = datetime.utcnow().isoformat()
        db.execute(
            "INSERT INTO intents (id, type, status, created_at) VALUES (?, ?, ?, ?)",
            ["a", "DIAGNOSE", "PENDING", now],
        )
        db.execute(
            "INSERT INTO intents (id, type, status, created_at) VALUES (?, ?, ?, ?)",
            ["b", "REPAIR", "COMPLETED", now],
        )
        db.commit()

        pending = db.execute(
            "SELECT COUNT(*) as cnt FROM intents WHERE status = 'PENDING'"
        ).fetchone()["cnt"]
        assert pending == 1

        completed = db.execute(
            "SELECT COUNT(*) as cnt FROM intents WHERE status = 'COMPLETED'"
        ).fetchone()["cnt"]
        assert completed == 1
        db.close()

    def test_null_updated_at(self):
        db = _make_db(":memory:")
        now = datetime.utcnow().isoformat()
        db.execute(
            "INSERT INTO intents (id, type, created_at) VALUES (?, ?, ?)",
            ["null-test", "CUSTOM", now],
        )
        db.commit()

        row = db.execute("SELECT * FROM intents WHERE id = ?", ["null-test"]).fetchone()
        assert row["updated_at"] is None
        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
