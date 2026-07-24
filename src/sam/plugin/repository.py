from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, List, Dict
from uuid import uuid4
import json

import aiosqlite

from .models import PluginManifest, PluginStatus


def _normalize_status(status: str) -> str:
    """Normalize status to lowercase for consistency."""
    return status.lower() if status else PluginStatus.INSTALLED.value


def _manifest_from_row(row: aiosqlite.Row) -> PluginManifest:
    """Construct PluginManifest from DB row, normalizing status."""
    data = json.loads(row["manifest_json"])
    # Ensure status in manifest matches DB (normalized to lowercase)
    data["status"] = _normalize_status(row["status"])
    return PluginManifest(**data)


class PluginRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def create(self, plugin: PluginManifest) -> str:
        plugin_id = plugin.id
        now = datetime.utcnow().isoformat()

        manifest_json = plugin.model_dump_json()

        async with aiosqlite.connect(self.db_path, check_same_thread=False) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute(
                """
                INSERT INTO plugins (plugin_id, workflow_id, name, version, manifest_yaml, manifest_json, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plugin_id,
                    plugin.workflow_id,
                    plugin.name,
                    plugin.version,
                    manifest_json,
                    manifest_json,
                    PluginStatus.INSTALLED.value,
                    now,
                    now,
                ),
            )
            await conn.commit()

        return plugin_id

    async def get(self, plugin_id: str) -> Optional[PluginManifest]:
        async with aiosqlite.connect(self.db_path, check_same_thread=False) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT manifest_json, status FROM plugins WHERE plugin_id = ?", (plugin_id,)
            )
            row = await cursor.fetchone()
            if row:
                return _manifest_from_row(row)
        return None

    async def get_by_name(self, name: str) -> Optional[PluginManifest]:
        async with aiosqlite.connect(self.db_path, check_same_thread=False) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT manifest_json, status FROM plugins WHERE name = ?",
                (name,),
            )
            row = await cursor.fetchone()
            if row:
                return _manifest_from_row(row)
        return None

    async def list(self, status: Optional[PluginStatus] = None) -> List[PluginManifest]:
        async with aiosqlite.connect(self.db_path, check_same_thread=False) as conn:
            conn.row_factory = aiosqlite.Row
            if status:
                cursor = await conn.execute(
                    "SELECT manifest_json, status FROM plugins WHERE LOWER(status) = ?",
                    (status.value,),
                )
            else:
                cursor = await conn.execute(
                    "SELECT manifest_json, status FROM plugins"
                )
            rows = await cursor.fetchall()
            return [_manifest_from_row(row) for row in rows]

    async def update(self, plugin_id: str, updates: Dict[str, Any]) -> None:
        # First get the current manifest to update it
        current = await self.get(plugin_id)
        if not current:
            raise ValueError(f"Plugin {plugin_id} not found")

        # Apply updates to the manifest object
        for key, value in updates.items():
            if key == "status" and isinstance(value, PluginStatus):
                value = value.value
            setattr(current, key, value)

        # Save updated manifest
        manifest_json = current.model_dump_json()
        now = datetime.utcnow().isoformat()
        db_status = _normalize_status(current.status)

        async with aiosqlite.connect(self.db_path, check_same_thread=False) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute(
                "UPDATE plugins SET manifest_json = ?, status = ?, updated_at = ? WHERE plugin_id = ?",
                (manifest_json, db_status, now, plugin_id),
            )
            await conn.commit()

    async def delete(self, plugin_id: str) -> None:
        async with aiosqlite.connect(self.db_path, check_same_thread=False) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute("DELETE FROM plugins WHERE plugin_id = ?", (plugin_id,))
            await conn.commit()