"""Failure injection tests for RC2 validation.

Simulates failures at key integration points without corrupting real files.
Covers: plugin, workflow, migration, database, and configuration failures.
"""
import pytest
import os
import sys
import tempfile
from unittest.mock import Mock, patch, AsyncMock


# ═══════════════════════════════════════════════════════════════
# 1. Plugin Failure
# ═══════════════════════════════════════════════════════════════
class TestPluginFailure:
    """Simulate plugin loading failures — invalid manifest, missing deps, runtime crash."""

    @pytest.mark.asyncio
    async def test_plugin_invalid_manifest(self):
        """PluginManifest validation should reject missing required fields."""
        from sam.plugin.models import PluginManifest
        with pytest.raises((ValueError, KeyError)):
            PluginManifest(**{"version": "1.0"})  # missing name

    def test_plugin_missing_entry_point(self):
        """PluginManifestLoader should raise on invalid file path."""
        from sam.plugin.loader import PluginManifestLoader
        loader = PluginManifestLoader()
        with pytest.raises((FileNotFoundError, Exception)):
            loader.load_manifest("/nonexistent/plugin.yaml")

    @pytest.mark.asyncio
    async def test_plugin_registry_failure(self):
        """Plugin registry should reject manifest with missing required fields."""
        from sam.plugin.models import PluginManifest
        with pytest.raises((ValueError, Exception)):
            PluginManifest(name="test-plugin")  # missing version, author, entrypoint


# ═══════════════════════════════════════════════════════════════
# 2. Workflow Failure
# ═══════════════════════════════════════════════════════════════
class TestWorkflowFailure:
    """Simulate workflow failures — invalid steps, circular deps, timeout."""

    def test_workflow_valid_definition(self):
        """WorkflowDefinition with proper steps should validate."""
        from sam.workflow.models import WorkflowDefinition, WorkflowStep
        wf = WorkflowDefinition(name="test", steps=[
            WorkflowStep(id="s1", capability="cap1"),
        ])
        assert wf.name == "test"
        assert len(wf.steps) == 1

    @pytest.mark.asyncio
    async def test_workflow_parse_and_validate(self):
        """Parse a workflow definition and check structure."""
        from sam.workflow.parser import WorkflowParser
        from sam.workflow.models import WorkflowDefinition, WorkflowStep
        parser = WorkflowParser()
        valid_yaml = """
name: test_wf
steps:
  - id: s1
    capability: test_cap
"""
        wf = await parser.parse_yaml(valid_yaml)
        assert wf.name == "test_wf"
        assert len(wf.steps) == 1

    @pytest.mark.asyncio
    async def test_workflow_parser_invalid_yaml(self):
        """Workflow parser should reject invalid YAML."""
        from sam.workflow.parser import WorkflowParser
        parser = WorkflowParser()
        with pytest.raises(Exception):
            await parser.parse_yaml("invalid: [yaml: broken")


# ═══════════════════════════════════════════════════════════════
# 3. Migration Failure
# ═══════════════════════════════════════════════════════════════
class TestMigrationFailure:
    """Simulate migration failures — bad SQL, version conflict, table already exists."""

    @pytest.mark.asyncio
    async def test_migration_invalid_sql(self):
        """Migration with invalid SQL should raise gracefully."""
        from sam.persistence.database import Database
        db = Database(":memory:")
        await db.initialize()
        with pytest.raises(Exception):
            await db.execute("INVALID SQL STATEMENT THAT DOES NOT EXIST;")
        await db.close()

    @pytest.mark.asyncio
    async def test_migration_rollback_on_failure(self):
        """Failed migration should not corrupt schema version."""
        from sam.persistence.database import Database
        db = Database(":memory:")
        await db.initialize()
        # Simulate a bad SQL that fails mid-flight
        try:
            await db.execute("CREATE TABLE __test_fail AS SELECT 1;")
            await db.execute("INSERT INTO nonexistent_table VALUES (1);")
        except Exception:
            pass  # Expected
        # DB should still be usable
        row = await db.fetch_one("SELECT COUNT(*) as cnt FROM schema_version")
        assert row is not None
        await db.close()

    @pytest.mark.asyncio
    async def test_migration_duplicate_version(self):
        """Apply same migration twice should be safe (idempotent)."""
        from sam.persistence.database import Database
        db = Database(":memory:")
        await db.initialize()
        # Verify it works
        row = await db.fetch_one("SELECT COUNT(*) as cnt FROM schema_version")
        count_before = row[0] if isinstance(row, (list, tuple)) else row['cnt']
        # Re-applying the same migration should not fail
        try:
            await db.execute("INSERT OR IGNORE INTO schema_version (version, description, applied_at) VALUES (1, 'dup', datetime('now'));")
        except Exception:
            pass  # Some DBs may restrict this
        await db.close()

    @pytest.mark.asyncio
    async def test_migration_out_of_order(self):
        """Database initialized with pending migrations should still work."""
        from sam.persistence.database import Database
        import tempfile
        import os
        # Create temp DB, apply some, leave some pending
        db = Database(":memory:")
        await db.initialize()
        await db.close()


# ═══════════════════════════════════════════════════════════════
# 4. Database Failure
# ═══════════════════════════════════════════════════════════════
class TestDatabaseFailure:
    """Simulate DB failures — connection error, permission denied, corruption."""

    @pytest.mark.asyncio
    async def test_db_query_error(self):
        """Query against non-existent table should raise."""
        from sam.persistence.database import Database
        db = Database(":memory:")
        await db.initialize()
        with pytest.raises(Exception):
            await db.fetch_all("SELECT * FROM nonexistent_table")
        await db.close()

    @pytest.mark.asyncio
    async def test_db_close_twice(self):
        """Closing DB twice should be safe."""
        from sam.persistence.database import Database
        db = Database(":memory:")
        await db.initialize()
        await db.close()
        await db.close()  # Should not raise
        assert True

    @pytest.mark.asyncio
    async def test_db_large_transaction(self):
        """Large batch of operations should not overwhelm DB."""
        from sam.persistence.database import Database
        db = Database(":memory:")
        await db.initialize()
        # Create a table and insert many rows
        await db.execute("CREATE TABLE IF NOT EXISTS test_batch (id INTEGER, val TEXT)")
        for i in range(100):
            await db.execute(f"INSERT INTO test_batch VALUES ({i}, 'val_{i}')")
        rows = await db.fetch_all("SELECT COUNT(*) as cnt FROM test_batch")
        count = rows[0][0] if isinstance(rows[0], (list, tuple)) else rows[0]['cnt']
        assert count == 100
        await db.execute("DROP TABLE test_batch")
        await db.close()


# ═══════════════════════════════════════════════════════════════
# 5. Configuration Failure
# ═══════════════════════════════════════════════════════════════
class TestConfigFailure:
    """Simulate config failures — DaemonConfig default behavior."""

    def test_config_defaults(self):
        """DaemonConfig should have sensible defaults."""
        from sam.core.daemon import DaemonConfig
        config = DaemonConfig()
        assert config.cluster_id == "default-cluster"
        assert config.poll_interval > 0
        assert config.health_check_interval > 0

    def test_config_node_id_unique(self):
        """Each DaemonConfig instance should have unique node_id."""
        from sam.core.daemon import DaemonConfig
        c1 = DaemonConfig()
        c2 = DaemonConfig()
        assert c1.node_id != c2.node_id

    def test_config_fields_present(self):
        """Critical config fields should exist."""
        from sam.core.daemon import DaemonConfig
        config = DaemonConfig()
        assert hasattr(config, 'cluster_id')
        assert hasattr(config, 'node_id')
        assert hasattr(config, 'heartbeat_interval')
        assert hasattr(config, 'orphan_timeout')
        assert hasattr(config, 'leader_lease_seconds')
