"""
Integration tests for PersistentPluginRegistry and CLI commands.

Tests cover:
- Repository CRUD operations with temporary database
- PersistentPluginRegistry lifecycle operations
- Cache behavior (TTL, invalidation)
- CLI command invocation using Typer's CliRunner
"""

import asyncio
import tempfile
import time
import aiosqlite
from pathlib import Path
from uuid import uuid4

import pytest
from typer.testing import CliRunner

from sam.plugin import (
    PluginManifest,
    PluginManifestLoader,
    PluginRepository,
    PersistentPluginRegistry,
    PluginStatus,
    create_plugin_registry,
)


async def create_plugins_table(db_path: str):
    """Create just the plugins table for testing."""
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS plugins (
                plugin_id TEXT PRIMARY KEY,
                workflow_id TEXT,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                manifest_yaml TEXT NOT NULL,
                manifest_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'installed',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_plugins_workflow_id ON plugins(workflow_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_plugins_status ON plugins(status)")
        await conn.commit()


@pytest.fixture
async def temp_db_path():
    """Create a temporary database file path with plugins table."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # Create plugins table
    await create_plugins_table(db_path)

    yield db_path

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_manifest():
    """Create a sample plugin manifest for testing."""
    return PluginManifest(
        id=str(uuid4()),
        name="Test Plugin",
        version="1.0.0",
        author="Test Author",
        description="A test plugin",
        entrypoint="test.plugin.main",
        capabilities=["test.capability"],
        dependencies=[],
        permissions=[],
    )


@pytest.fixture
def sample_manifest_yaml(tmp_path):
    """Create a sample manifest.yaml file for CLI testing."""
    manifest_dir = tmp_path / "test-plugin"
    manifest_dir.mkdir()
    manifest_file = manifest_dir / "manifest.yaml"
    manifest_content = """
id: cli-test-plugin
name: CLI Test Plugin
version: 2.0.0
author: CLI Test
description: Plugin for CLI testing
entrypoint: cli.test.plugin.main
capabilities:
  - cli.test.capability
dependencies: []
permissions:
  - read:workspace
  - read:configuration
"""
    manifest_file.write_text(manifest_content.strip())
    return str(manifest_dir)


class TestPluginRepository:
    """Tests for PluginRepository CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_and_get(self, temp_db_path, sample_manifest):
        """Test creating and retrieving a plugin."""
        repo = PluginRepository(temp_db_path)

        # Create plugin
        plugin_id = await repo.create(sample_manifest)
        assert plugin_id == sample_manifest.id

        # Get plugin
        retrieved = await repo.get(plugin_id)
        assert retrieved is not None
        assert retrieved.id == sample_manifest.id
        assert retrieved.name == sample_manifest.name
        assert retrieved.version == sample_manifest.version
        assert retrieved.status == "installed"  # Normalized to lowercase

    @pytest.mark.asyncio
    async def test_get_by_name(self, temp_db_path, sample_manifest):
        """Test retrieving plugin by name."""
        repo = PluginRepository(temp_db_path)
        await repo.create(sample_manifest)

        retrieved = await repo.get_by_name(sample_manifest.name)
        assert retrieved is not None
        assert retrieved.name == sample_manifest.name

    @pytest.mark.asyncio
    async def test_list_all(self, temp_db_path, sample_manifest):
        """Test listing all plugins."""
        repo = PluginRepository(temp_db_path)
        await repo.create(sample_manifest)

        plugins = await repo.list()
        assert len(plugins) == 1
        assert plugins[0].id == sample_manifest.id

    @pytest.mark.asyncio
    async def test_list_with_status_filter(self, temp_db_path, sample_manifest):
        """Test listing plugins filtered by status."""
        repo = PluginRepository(temp_db_path)
        await repo.create(sample_manifest)

        # Filter by INSTALLED
        plugins = await repo.list(PluginStatus.INSTALLED)
        assert len(plugins) == 1

        # Filter by non-existent status
        plugins = await repo.list(PluginStatus.ENABLED)
        assert len(plugins) == 0

    @pytest.mark.asyncio
    async def test_update_status(self, temp_db_path, sample_manifest):
        """Test updating plugin status."""
        repo = PluginRepository(temp_db_path)
        await repo.create(sample_manifest)

        # Update status
        await repo.update(plugin_id=sample_manifest.id, updates={"status": PluginStatus.ENABLED})

        # Verify status changed
        retrieved = await repo.get(sample_manifest.id)
        assert retrieved.status == "enabled"

    @pytest.mark.asyncio
    async def test_delete(self, temp_db_path, sample_manifest):
        """Test deleting a plugin."""
        repo = PluginRepository(temp_db_path)
        await repo.create(sample_manifest)

        # Delete plugin
        await repo.delete(sample_manifest.id)

        # Verify deleted
        retrieved = await repo.get(sample_manifest.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_status_normalization(self, temp_db_path, sample_manifest):
        """Test that status is normalized to lowercase."""
        repo = PluginRepository(temp_db_path)
        await repo.create(sample_manifest)

        # Update with uppercase status
        await repo.update(plugin_id=sample_manifest.id, updates={"status": "ENABLED"})

        # Retrieve and verify lowercase
        retrieved = await repo.get(sample_manifest.id)
        assert retrieved.status == "enabled"


class TestPersistentPluginRegistry:
    """Tests for PersistentPluginRegistry."""

    @pytest.mark.asyncio
    async def test_register_and_get(self, temp_db_path, sample_manifest):
        """Test registering and retrieving a plugin."""
        registry = await create_plugin_registry(temp_db_path, cache_ttl=None)

        plugin_id = await registry.register(sample_manifest)
        assert plugin_id == sample_manifest.id

        retrieved = await registry.get(plugin_id)
        assert retrieved is not None
        assert retrieved.name == sample_manifest.name

    @pytest.mark.asyncio
    async def test_get_descriptor(self, temp_db_path, sample_manifest):
        """Test getting plugin descriptor with status."""
        registry = await create_plugin_registry(temp_db_path, cache_ttl=None)
        await registry.register(sample_manifest)

        descriptor = await registry.get_descriptor(sample_manifest.id)
        assert descriptor is not None
        assert descriptor.manifest.id == sample_manifest.id
        assert descriptor.status == PluginStatus.INSTALLED

    @pytest.mark.asyncio
    async def test_lifecycle_operations(self, temp_db_path, sample_manifest):
        """Test full lifecycle: enable, disable, uninstall."""
        registry = await create_plugin_registry(temp_db_path, cache_ttl=None)
        await registry.register(sample_manifest)

        # Enable
        await registry.enable(sample_manifest.id)
        descriptor = await registry.get_descriptor(sample_manifest.id)
        assert descriptor.status == PluginStatus.ENABLED

        # Disable
        await registry.disable(sample_manifest.id)
        descriptor = await registry.get_descriptor(sample_manifest.id)
        assert descriptor.status == PluginStatus.DISABLED

        # Uninstall
        await registry.uninstall(sample_manifest.id)
        retrieved = await registry.get(sample_manifest.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_list_plugins(self, temp_db_path, sample_manifest):
        """Test listing plugins with status filter."""
        registry = await create_plugin_registry(temp_db_path, cache_ttl=None)
        await registry.register(sample_manifest)

        all_plugins = await registry.list()
        assert len(all_plugins) == 1

        enabled_plugins = await registry.list(PluginStatus.ENABLED)
        assert len(enabled_plugins) == 0

    @pytest.mark.asyncio
    async def test_get_by_capability(self, temp_db_path, sample_manifest):
        """Test finding plugins by capability."""
        registry = await create_plugin_registry(temp_db_path, cache_ttl=None)
        await registry.register(sample_manifest)

        found = await registry.get_by_capability("test.capability")
        assert len(found) == 1
        assert found[0].manifest.id == sample_manifest.id

        not_found = await registry.get_by_capability("nonexistent")
        assert len(not_found) == 0


class TestPersistentPluginRegistryCache:
    """Tests for PersistentPluginRegistry cache behavior."""

    @pytest.mark.asyncio
    async def test_cache_hit_miss(self, temp_db_path, sample_manifest):
        """Test cache hit and miss behavior."""
        registry = await create_plugin_registry(temp_db_path, cache_ttl=60)
        await registry.register(sample_manifest)

        # First get - cache miss
        start = time.time()
        plugin1 = await registry.get(sample_manifest.id)
        t1 = time.time() - start

        # Second get - cache hit (should be faster)
        start = time.time()
        plugin2 = await registry.get(sample_manifest.id)
        t2 = time.time() - start

        assert plugin1 is not None
        assert plugin2 is not None
        assert plugin1.id == plugin2.id
        # Cache hit should be very fast (typically < 1ms)
        assert t2 < t1

    @pytest.mark.asyncio
    async def test_cache_expiration(self, temp_db_path, sample_manifest):
        """Test cache expiration after TTL."""
        registry = await create_plugin_registry(temp_db_path, cache_ttl=1)
        await registry.register(sample_manifest)

        # First get
        plugin1 = await registry.get(sample_manifest.id)
        assert plugin1 is not None

        # Wait for cache to expire
        await asyncio.sleep(1.2)

        # Second get - should be cache miss
        plugin2 = await registry.get(sample_manifest.id)
        assert plugin2 is not None
        assert plugin1.id == plugin2.id

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_update(self, temp_db_path, sample_manifest):
        """Test cache invalidation when plugin is updated."""
        registry = await create_plugin_registry(temp_db_path, cache_ttl=60)
        await registry.register(sample_manifest)

        # Get plugin to populate cache
        plugin1 = await registry.get(sample_manifest.id)
        assert plugin1 is not None

        # Update status
        await registry.enable(sample_manifest.id)

        # Get again - should be cache miss (new status)
        plugin2 = await registry.get(sample_manifest.id)
        assert plugin2 is not None

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_delete(self, temp_db_path, sample_manifest):
        """Test cache invalidation when plugin is deleted."""
        registry = await create_plugin_registry(temp_db_path, cache_ttl=60)
        await registry.register(sample_manifest)

        # Get plugin to populate cache
        plugin1 = await registry.get(sample_manifest.id)
        assert plugin1 is not None

        # Delete plugin
        await registry.uninstall(sample_manifest.id)

        # Get again - should return None
        plugin2 = await registry.get(sample_manifest.id)
        assert plugin2 is None

    @pytest.mark.asyncio
    async def test_list_cache(self, temp_db_path, sample_manifest):
        """Test list operation caching."""
        registry = await create_plugin_registry(temp_db_path, cache_ttl=60)
        await registry.register(sample_manifest)

        # First list
        start = time.time()
        plugins1 = await registry.list()
        t1 = time.time() - start

        # Second list - cache hit
        start = time.time()
        plugins2 = await registry.list()
        t2 = time.time() - start

        assert len(plugins1) == 1
        assert len(plugins2) == 1
        assert t2 < t1

    @pytest.mark.asyncio
    async def test_no_cache_when_ttl_none(self, temp_db_path, sample_manifest):
        """Test that no caching occurs when TTL is None."""
        registry = await create_plugin_registry(temp_db_path, cache_ttl=None)
        await registry.register(sample_manifest)

        # Multiple gets should all hit database
        plugin1 = await registry.get(sample_manifest.id)
        plugin2 = await registry.get(sample_manifest.id)

        assert plugin1 is not None
        assert plugin2 is not None
        assert plugin1.id == plugin2.id


class TestPluginCLI:
    """Integration tests for CLI commands using CliRunner."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def cli_db_path(self, tmp_path):
        db_path = str(tmp_path / "cli_test.db")
        # Create plugins table for this test database
        import asyncio
        import aiosqlite
        
        async def init_db():
            async with aiosqlite.connect(db_path) as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS plugins (
                        plugin_id TEXT PRIMARY KEY,
                        workflow_id TEXT,
                        name TEXT NOT NULL,
                        version TEXT NOT NULL,
                        manifest_yaml TEXT NOT NULL,
                        manifest_json TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'installed',
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                """)
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_plugins_workflow_id ON plugins(workflow_id)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_plugins_status ON plugins(status)")
                await conn.commit()
        
        asyncio.run(init_db())
        return db_path

    @pytest.fixture
    def plugin_dir(self, tmp_path):
        """Create a plugin directory with manifest.yaml."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        manifest = plugin_dir / "manifest.yaml"
        manifest.write_text("""
id: cli-test-plugin
name: CLI Test Plugin
version: 2.0.0
author: CLI Test
description: Plugin for CLI testing
entrypoint: cli.test.plugin.main
capabilities:
  - cli.test.capability
dependencies: []
permissions:
  - read:workspace
  - read:configuration
""".strip())
        return str(plugin_dir)

    def test_plugin_install(self, runner, cli_db_path, plugin_dir):
        """Test plugin install command."""
        # We need to patch the DB_PATH in the CLI module
        import sam.cli.main as cli_main
        original_db = cli_main.DB_PATH
        cli_main.DB_PATH = cli_db_path

        try:
            result = runner.invoke(cli_main.app, ["plugin", "install", plugin_dir])
            assert result.exit_code == 0
            assert "Installed plugin" in result.output
            assert "CLI Test Plugin" in result.output
        finally:
            cli_main.DB_PATH = original_db

    def test_plugin_list(self, runner, cli_db_path, plugin_dir):
        """Test plugin list command."""
        import sam.cli.main as cli_main
        original_db = cli_main.DB_PATH
        cli_main.DB_PATH = cli_db_path

        try:
            # First install a plugin
            runner.invoke(cli_main.app, ["plugin", "install", plugin_dir])

            # Then list
            result = runner.invoke(cli_main.app, ["plugin", "list"])
            assert result.exit_code == 0
            assert "Plugins (1)" in result.output
            assert "CLI Test Plugin" in result.output
            assert "2.0.0" in result.output
        finally:
            cli_main.DB_PATH = original_db

    def test_plugin_list_with_status_filter(self, runner, cli_db_path, plugin_dir):
        """Test plugin list with status filter."""
        import sam.cli.main as cli_main
        original_db = cli_main.DB_PATH
        cli_main.DB_PATH = cli_db_path

        try:
            runner.invoke(cli_main.app, ["plugin", "install", plugin_dir])

            # Enable the plugin first
            runner.invoke(cli_main.app, ["plugin", "enable", "cli-test-plugin"])

            # List with enabled filter
            result = runner.invoke(cli_main.app, ["plugin", "list", "--status", "enabled"])
            assert result.exit_code == 0
            assert "Plugins (1)" in result.output

            # List with installed filter (should be 0 since we enabled)
            result = runner.invoke(cli_main.app, ["plugin", "list", "--status", "installed"])
            assert result.exit_code == 0
            assert "Plugins (0)" in result.output
        finally:
            cli_main.DB_PATH = original_db

    def test_plugin_enable_disable(self, runner, cli_db_path, plugin_dir):
        """Test plugin enable and disable commands."""
        import sam.cli.main as cli_main
        original_db = cli_main.DB_PATH
        cli_main.DB_PATH = cli_db_path

        try:
            runner.invoke(cli_main.app, ["plugin", "install", plugin_dir])

            # Enable
            result = runner.invoke(cli_main.app, ["plugin", "enable", "cli-test-plugin"])
            assert result.exit_code == 0
            assert "enabled" in result.output.lower()

            # Disable
            result = runner.invoke(cli_main.app, ["plugin", "disable", "cli-test-plugin"])
            assert result.exit_code == 0
            assert "disabled" in result.output.lower()
        finally:
            cli_main.DB_PATH = original_db

    def test_plugin_uninstall(self, runner, cli_db_path, plugin_dir):
        """Test plugin uninstall command."""
        import sam.cli.main as cli_main
        original_db = cli_main.DB_PATH
        cli_main.DB_PATH = cli_db_path

        try:
            runner.invoke(cli_main.app, ["plugin", "install", plugin_dir])

            # Uninstall
            result = runner.invoke(cli_main.app, ["plugin", "uninstall", "cli-test-plugin"])
            assert result.exit_code == 0
            assert "uninstalled" in result.output.lower()

            # Verify it's gone
            result = runner.invoke(cli_main.app, ["plugin", "list"])
            assert result.exit_code == 0
            assert "No plugins installed" in result.output
        finally:
            cli_main.DB_PATH = original_db

    def test_plugin_health(self, runner, cli_db_path, plugin_dir):
        """Test plugin health command."""
        import sam.cli.main as cli_main
        original_db = cli_main.DB_PATH
        cli_main.DB_PATH = cli_db_path

        try:
            runner.invoke(cli_main.app, ["plugin", "install", plugin_dir])

            # Check health of specific plugin
            result = runner.invoke(cli_main.app, ["plugin", "health", "cli-test-plugin"])
            assert result.exit_code == 0
            assert "CLI Test Plugin" in result.output or "cli-test-plugin" in result.output
            assert "Status:" in result.output

            # Check health of all plugins
            result = runner.invoke(cli_main.app, ["plugin", "health"])
            assert result.exit_code == 0
            assert "Health status" in result.output
        finally:
            cli_main.DB_PATH = original_db

    def test_plugin_discover(self, runner, cli_db_path, tmp_path):
        """Test plugin discover command."""
        import sam.cli.main as cli_main
        original_db = cli_main.DB_PATH
        cli_main.DB_PATH = cli_db_path

        try:
            # Create plugins directory
            plugins_dir = tmp_path / "plugins"
            plugins_dir.mkdir()
            plugin_dir = plugins_dir / "discovered-plugin"
            plugin_dir.mkdir()
            manifest = plugin_dir / "manifest.yaml"
            manifest.write_text("""
id: discovered-plugin
name: Discovered Plugin
version: 1.0.0
author: Test
description: Auto-discovered plugin
entrypoint: discovered.plugin.main
capabilities:
  - discovered.capability
dependencies: []
permissions: []
""".strip())

            # Discover
            result = runner.invoke(cli_main.app, ["plugin", "discover", str(plugins_dir)])
            assert result.exit_code == 0
            assert "Discovered and installed" in result.output
            assert "Discovered Plugin" in result.output
        finally:
            cli_main.DB_PATH = original_db


class TestEndToEndPersistence:
    """End-to-end tests verifying persistence across registry instances."""

    @pytest.mark.asyncio
    async def test_persistence_across_instances(self, temp_db_path, sample_manifest):
        """Test that plugins persist across registry instances."""
        # First registry instance
        registry1 = await create_plugin_registry(temp_db_path, cache_ttl=None)
        await registry1.register(sample_manifest)
        await registry1.enable(sample_manifest.id)

        # Second registry instance (simulating restart)
        registry2 = await create_plugin_registry(temp_db_path, cache_ttl=None)

        # Verify plugin exists and has correct status
        plugin = await registry2.get(sample_manifest.id)
        assert plugin is not None
        assert plugin.name == sample_manifest.name

        descriptor = await registry2.get_descriptor(sample_manifest.id)
        assert descriptor is not None
        assert descriptor.status == PluginStatus.ENABLED

    @pytest.mark.asyncio
    async def test_multiple_plugins(self, temp_db_path):
        """Test handling multiple plugins."""
        registry = await create_plugin_registry(temp_db_path, cache_ttl=None)

        # Create multiple plugins
        plugins = []
        for i in range(3):
            manifest = PluginManifest(
                id=f"plugin-{i}",
                name=f"Plugin {i}",
                version="1.0.0",
                author="Test",
                description=f"Plugin {i}",
                entrypoint=f"plugin.{i}.main",
                capabilities=[f"capability.{i}"],
                dependencies=[],
                permissions=[],
            )
            plugins.append(manifest)
            await registry.register(manifest)

        # List all
        all_plugins = await registry.list()
        assert len(all_plugins) == 3

        # List by capability
        for i in range(3):
            found = await registry.get_by_capability(f"capability.{i}")
            assert len(found) == 1
            assert found[0].manifest.id == f"plugin-{i}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])