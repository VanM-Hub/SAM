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
                    getattr(plugin, 'workflow_id', None),
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
        # Check if plugin exists
        current = await self.get(plugin_id)
        if not current:
            raise ValueError(f"Plugin {plugin_id} not found")

        now = datetime.utcnow().isoformat()
        
        # Handle status update separately (not part of manifest_json)
        db_status = None
        if "status" in updates:
            status_val = updates["status"]
            if isinstance(status_val, PluginStatus):
                db_status = status_val.value
            else:
                db_status = str(status_val)
        
        async with aiosqlite.connect(self.db_path, check_same_thread=False) as conn:
            conn.row_factory = aiosqlite.Row
            if db_status:
                await conn.execute(
                    "UPDATE plugins SET status = ?, updated_at = ? WHERE plugin_id = ?",
                    (db_status, now, plugin_id),
                )
            else:
                await conn.execute(
                    "UPDATE plugins SET updated_at = ? WHERE plugin_id = ?",
                    (now, plugin_id),
                )
            await conn.commit()

    async def delete(self, plugin_id: str) -> None:
        async with aiosqlite.connect(self.db_path, check_same_thread=False) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute("DELETE FROM plugins WHERE plugin_id = ?", (plugin_id,))
            await conn.commit()