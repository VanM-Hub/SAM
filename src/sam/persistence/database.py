"""Simple persistence layer using sqlite3 with async-friendly wrappers.

This avoids requiring external deps by using sqlite3 + asyncio.to_thread.
"""
import sqlite3
import json
import os
import asyncio
from typing import Any, Callable, List, Optional, TypeVar
import structlog


# ── Python 3.8 polyfill (hapus setelah migrasi ke 3.12) ───────────
T = TypeVar("T")

if not hasattr(asyncio, "to_thread"):
    async def _to_thread(fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Fallback for Python < 3.9."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))
    asyncio.to_thread = _to_thread  # type: ignore[attr-defined]

from .migrations import MigrationManager

logger = structlog.get_logger()


class Database:
    """Lightweight database wrapper around sqlite3 offering async helpers.

    The wrapper uses asyncio.to_thread to avoid blocking the event loop.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = os.path.abspath(db_path)
        db_dir = os.path.dirname(self._db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        # Use check_same_thread=False because we'll access connection from threads
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        # Return rows as dict
        self._conn.row_factory = sqlite3.Row
        logger.debug("Database initialized", path=db_path)

    async def initialize(self) -> None:
        """Create tables if they do not exist, then run migrations."""
        # Run migrations (this also ensures schema_version table exists)
        migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
        manager = MigrationManager(self, migrations_dir)
        await manager.migrate()

        logger.info("Database schema initialized and migrated")

    async def close(self) -> None:
        def _close():
            try:
                self._conn.commit()
                self._conn.close()
            except Exception:
                pass

        await asyncio.to_thread(_close)
        logger.debug("Database closed")

    async def execute(self, query: str, params: Optional[List[Any]] = None) -> None:
        """Execute a write query (INSERT/UPDATE/CREATE)."""
        def _exec():
            cur = self._conn.cursor()
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            self._conn.commit()
            cur.close()

        await asyncio.to_thread(_exec)

    async def executescript(self, script: str) -> None:
        """Execute a multi-statement SQL script using sqlite3.executescript().

        This is the correct way to run DDL that contains triggers,
        virtual table creation, or any multi-statement blocks where
        splitting by semicolon would break trigger BEGIN/END bodies.
        """
        def _exec():
            self._conn.executescript(script)
            self._conn.commit()

        await asyncio.to_thread(_exec)

    async def fetch_all(self, query: str, params: Optional[List[Any]] = None) -> List[dict]:
        """Fetch multiple rows as list of dicts."""
        def _fetch():
            cur = self._conn.cursor()
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            rows = [dict(r) for r in cur.fetchall()]
            cur.close()
            return rows

        rows = await asyncio.to_thread(_fetch)
        return rows

    async def fetch_one(self, query: str, params: Optional[List[Any]] = None) -> Optional[dict]:
        def _fetch():
            cur = self._conn.cursor()
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            row = cur.fetchone()
            cur.close()
            return dict(row) if row else None

        return await asyncio.to_thread(_fetch)