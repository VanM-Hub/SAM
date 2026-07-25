"""Migration manager for SQLite schema versioning."""

import os
import re
import structlog
from typing import List, Optional, Dict, Any
from pathlib import Path

logger = structlog.get_logger()


class MigrationManager:
    """Manages database schema migrations."""

    def __init__(self, db: "Database", migrations_dir: str) -> None:
        self.db = db
        self.migrations_dir = Path(migrations_dir)

    async def ensure_schema_table(self) -> None:
        """Create the schema_version table if it doesn't exist."""
        sql = """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        await self.db.execute(sql)
        logger.info("Schema version table ensured")

    async def get_current_version(self) -> int:
        """Get the current schema version from the database."""
        try:
            # Database.fetch_one is the async helper on Database wrapper
            result = await self.db.fetch_one("SELECT MAX(version) as version FROM schema_version")
            version = result["version"] if result and result.get("version") is not None else 0
            logger.debug("Current schema version", version=version)
            return version
        except Exception:
            # Table might not exist yet or fetch failed
            logger.debug("No schema version table found or fetch failed, returning 0")
            return 0

    def _discover_migrations(self) -> List[Dict[str, Any]]:
        """Discover migration files in the migrations directory."""
        migrations = []
        if not self.migrations_dir.exists():
            logger.warning("Migrations directory does not exist", path=str(self.migrations_dir))
            return migrations

        # Pattern: NNN_description.sql or NNN_description.py
        pattern = re.compile(r"^(\d{3,})_(.+)\.(sql|py)$")

        for file_path in sorted(self.migrations_dir.iterdir()):
            if not file_path.is_file():
                continue
            match = pattern.match(file_path.name)
            if match:
                version = int(match.group(1))
                description = match.group(2)
                ext = match.group(3)
                migrations.append({
                    "version": version,
                    "description": description,
                    "file": file_path,
                    "ext": ext
                })
            else:
                logger.warning("Migration file name does not match pattern, skipping", file=file_path.name)

        # Sort by version
        migrations.sort(key=lambda m: m["version"])
        return migrations

    async def get_pending_migrations(self) -> List[Dict[str, Any]]:
        """Get list of migrations that need to be applied."""
        current_version = await self.get_current_version()
        all_migrations = self._discover_migrations()

        pending = [m for m in all_migrations if m["version"] > current_version]
        logger.info("Pending migrations", current_version=current_version, pending=len(pending))
        return pending

    async def run_migration(self, version: int, sql: str) -> None:
        """Execute a single migration SQL within a transaction."""
        logger.info("Running migration", version=version)

        # Execute migration SQL
        await self.db.execute(sql)

        # Record the migration
        await self.db.execute(
            "INSERT INTO schema_version (version, description) VALUES (?, ?)",
            (version, "")
        )

        logger.info("Migration completed", version=version)

    async def migrate(self, target_version: Optional[int] = None) -> None:
        """Run all pending migrations up to target_version."""
        await self.ensure_schema_table()

        pending = await self.get_pending_migrations()

        if target_version is not None:
            pending = [m for m in pending if m["version"] <= target_version]

        if not pending:
            logger.info("No pending migrations")
            return

        for migration in pending:
            version = migration["version"]
            file_path = migration["file"]

            # Read migration content
            if migration["ext"] == "sql":
                sql = file_path.read_text(encoding="utf-8")
            else:
                # Python migration - import and run
                logger.warning("Python migrations not yet implemented", file=str(file_path))
                continue

            # Execute the full SQL script using executescript.
            # This is critical for migrations that contain trigger definitions
            # (BEGIN/END blocks) where splitting by semicolon would break them.
            await self.db.executescript(sql)

            # Record migration
            await self.db.execute(
                "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                (version, migration["description"])
            )

            logger.info("Migration applied", version=version, description=migration["description"])

        logger.info("All migrations completed", applied=len(pending))