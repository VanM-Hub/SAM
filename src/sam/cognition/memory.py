"""Working Memory — Sprint 29 Fase 1.

WorkingMemoryManager provides a key-value store with TTL expiry,
session scoping, and snapshot capability.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger()

# Default TTL in seconds (5 minutes)
DEFAULT_TTL = 300


class WorkingMemoryEntry:
    """A single entry in working memory with TTL.

    Attributes:
        key: Entry key.
        value: Any JSON-serializable value.
        ttl: Time-to-live in seconds (0 = no expiry).
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    def __init__(
        self,
        key: str,
        value: Any,
        ttl: int = DEFAULT_TTL,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        self.key = key
        self.value = value
        self.ttl = ttl
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    @property
    def expired(self) -> bool:
        """Check if this entry has expired based on TTL."""
        if self.ttl <= 0:
            return False
        elapsed = (datetime.now(timezone.utc) - self.updated_at).total_seconds()
        return elapsed > self.ttl

    def touch(self) -> None:
        """Refresh the updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": json.dumps(self.value, default=str),
            "ttl": self.ttl,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class WorkingMemory:
    """Scoped working memory container.

    Attributes:
        id: Unique identifier (UUID).
        session_id: Session this working memory belongs to.
        entries: Dict of key -> WorkingMemoryEntry.
    """

    def __init__(
        self,
        id: str = "",
        session_id: str = "",
    ) -> None:
        self.id = id or f"wm_{uuid.uuid4().hex[:12]}"
        self.session_id = session_id
        self._entries: Dict[str, WorkingMemoryEntry] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get a value by key. Returns None if missing or expired."""
        entry = self._entries.get(key)
        if entry is None:
            return None
        if entry.expired:
            del self._entries[key]
            return None
        entry.touch()
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value with optional TTL override."""
        if key in self._entries:
            entry = self._entries[key]
            entry.value = value
            entry.ttl = ttl if ttl is not None else entry.ttl
            entry.touch()
        else:
            effective_ttl = ttl if ttl is not None else DEFAULT_TTL
            self._entries[key] = WorkingMemoryEntry(
                key=key, value=value, ttl=effective_ttl,
            )

    def delete(self, key: str) -> None:
        """Delete an entry by key. No-op if missing."""
        self._entries.pop(key, None)

    def clear(self) -> None:
        """Remove all entries from this working memory."""
        self._entries.clear()

    def snapshot(self) -> Dict[str, Any]:
        """Return all non-expired entries as a plain dict."""
        result: Dict[str, Any] = {}
        expired_keys: List[str] = []
        for key, entry in self._entries.items():
            if entry.expired:
                expired_keys.append(key)
            else:
                result[key] = entry.value
        # Clean up expired
        for k in expired_keys:
            del self._entries[k]
        return result

    @property
    def entry_count(self) -> int:
        """Number of non-expired entries."""
        return len(self.snapshot())

    def keys(self) -> List[str]:
        """Return all non-expired keys."""
        return list(self.snapshot().keys())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "entries": json.dumps(self.snapshot(), default=str),
        }


class WorkingMemoryManager:
    """Manages multiple WorkingMemory instances per session.

    Provides session-scoped key-value operations with TTL support.
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, WorkingMemory] = {}
        self.logger = logger.bind(component="WorkingMemoryManager")

    def _get_or_create_session(
        self,
        session_id: str,
    ) -> WorkingMemory:
        """Get or create a WorkingMemory for the given session."""
        if session_id not in self._sessions:
            self._sessions[session_id] = WorkingMemory(
                session_id=session_id,
            )
        return self._sessions[session_id]

    async def set(
        self,
        key: str,
        value: Any,
        session_id: str = "default",
        ttl: Optional[int] = None,
    ) -> None:
        """Set a value in the specified session's working memory."""
        wm = self._get_or_create_session(session_id)
        wm.set(key, value, ttl=ttl)

    async def get(
        self,
        key: str,
        session_id: str = "default",
    ) -> Optional[Any]:
        """Get a value from the specified session's working memory."""
        wm = self._sessions.get(session_id)
        if wm is None:
            return None
        return wm.get(key)

    async def delete(self, key: str, session_id: str = "default") -> None:
        """Delete a key from the specified session."""
        wm = self._sessions.get(session_id)
        if wm is not None:
            wm.delete(key)

    async def clear(self, session_id: str = "default") -> None:
        """Clear all entries from a session's working memory."""
        wm = self._sessions.get(session_id)
        if wm is not None:
            wm.clear()

    async def clear_all(self) -> None:
        """Clear ALL working memory across all sessions."""
        for wm in self._sessions.values():
            wm.clear()
        self._sessions.clear()

    async def snapshot(self, session_id: str = "default") -> Dict[str, Any]:
        """Return snapshot of a session's working memory."""
        wm = self._sessions.get(session_id)
        if wm is None:
            return {}
        return wm.snapshot()

    async def snapshot_all(self) -> Dict[str, Dict[str, Any]]:
        """Return snapshots of all sessions."""
        return {
            sid: wm.snapshot()
            for sid, wm in self._sessions.items()
        }

    async def list_sessions(self) -> List[str]:
        """Return list of all session IDs."""
        return list(self._sessions.keys())

    async def get_session_entry_count(self, session_id: str) -> int:
        """Number of entries in a session."""
        wm = self._sessions.get(session_id)
        if wm is None:
            return 0
        return wm.entry_count

    async def entry_exists(self, key: str, session_id: str = "default") -> bool:
        """Check if a key exists and is not expired."""
        val = await self.get(key, session_id)
        return val is not None
