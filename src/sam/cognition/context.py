"""Context Window — Sprint 29 Fase 4.

Manages what SAM is currently "thinking about": which context items
are active, which can be forgotten (expired/low importance), and
what must be retained during a cognitive session.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger()

DEFAULT_CONTEXT_TTL = 300  # 5 minutes
DEFAULT_MAX_ITEMS = 50
PRUNE_IMPORTANCE_THRESHOLD = 0.1


@dataclass
class ContextItem:
    """A single item in the context window.

    Attributes:
        id: Unique identifier.
        key: Descriptive key (e.g. "current_symptom", "active_hypothesis").
        value: Any JSON-serializable value.
        importance: 0.0 (forgettable) to 1.0 (must retain).
        ttl: Time-to-live in seconds (0 = no expiry).
        created_at: When the item was created.
        expires_at: When the item expires (None if no expiry).
    """
    id: str = ""
    key: str = ""
    value: Any = None
    importance: float = 0.5
    ttl: int = DEFAULT_CONTEXT_TTL
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.id:
            object.__setattr__(self, "id", f"ci_{uuid.uuid4().hex[:12]}")
        if self.expires_at is None and self.ttl > 0:
            object.__setattr__(
                self, "expires_at",
                self.created_at + timedelta(seconds=self.ttl),
            )

    @property
    def expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) >= self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "key": self.key,
            "value": json.dumps(self.value, default=str),
            "importance": self.importance,
            "ttl": self.ttl,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ContextItem:
        raw_value = data.get("value", None)
        if isinstance(raw_value, str):
            try:
                raw_value = json.loads(raw_value)
            except (ValueError, TypeError):
                pass
        expires_raw = data.get("expires_at")
        expires_at = _parse_dt(expires_raw) if expires_raw else None
        created = _parse_dt(data.get("created_at")) or datetime.now(timezone.utc)
        item = cls(
            id=data.get("id", ""),
            key=data.get("key", ""),
            value=raw_value,
            importance=float(data.get("importance", 0.5)),
            ttl=int(data.get("ttl", DEFAULT_CONTEXT_TTL)),
            created_at=created,
        )
        if expires_at is not None:
            object.__setattr__(item, "expires_at", expires_at)
        return item


def _parse_dt(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


# ── Context Window ────────────────────────────────────────────────


class ContextWindow:
    """Manages the active context items with TTL, importance, and pruning.

    This is SAM's "what am I thinking about right now" — symptom context,
    pending decisions, active hypotheses, etc.
    """

    def __init__(
        self,
        max_items: int = DEFAULT_MAX_ITEMS,
        default_ttl: int = DEFAULT_CONTEXT_TTL,
    ) -> None:
        self._items: Dict[str, ContextItem] = {}  # key -> ContextItem
        self._max_items = max_items
        self._default_ttl = default_ttl
        self.logger = logger.bind(component="ContextWindow")

    async def set(
        self,
        key: str,
        value: Any,
        importance: float = 0.5,
        ttl: Optional[int] = None,
    ) -> None:
        """Set a context item. Updates existing key or creates new.

        If at capacity and key is new, the lowest-importance item is evicted.
        """
        effective_ttl = ttl if ttl is not None else self._default_ttl

        if key in self._items:
            # Update existing
            item = self._items[key]
            item.value = value
            item.importance = max(0.0, min(1.0, importance))
            item.ttl = effective_ttl
            if effective_ttl > 0:
                object.__setattr__(
                    item, "expires_at",
                    datetime.now(timezone.utc) + timedelta(seconds=effective_ttl),
                )
            else:
                object.__setattr__(item, "expires_at", None)
        else:
            # If at capacity, evict lowest importance non-expired item
            if len(self._items) >= self._max_items:
                await self._evict_lowest_importance()
            item = ContextItem(
                key=key,
                value=value,
                importance=max(0.0, min(1.0, importance)),
                ttl=effective_ttl,
            )
            self._items[key] = item

        self.logger.debug("Context item set", key=key, importance=importance, ttl=effective_ttl)

    async def get(self, key: str) -> Optional[Any]:
        """Get a context item value by key. Returns None if missing or expired."""
        item = self._items.get(key)
        if item is None:
            return None
        if item.expired:
            del self._items[key]
            return None
        return item.value

    async def delete(self, key: str) -> None:
        """Delete a context item by key."""
        self._items.pop(key, None)

    async def list(
        self,
        min_importance: float = 0.0,
    ) -> List[ContextItem]:
        """List active (non-expired) context items filtered by minimum importance."""
        self._purge_expired()
        result = []
        for item in self._items.values():
            if item.importance >= min_importance:
                result.append(item)
        return result

    async def prune(self) -> int:
        """Remove expired items and items with very low importance (< 0.1).

        Returns:
            Number of items removed.
        """
        before = len(self._items)
        keys_to_remove = []
        for key, item in self._items.items():
            if item.expired or item.importance < PRUNE_IMPORTANCE_THRESHOLD:
                keys_to_remove.append(key)
        for k in keys_to_remove:
            del self._items[k]
        removed = before - len(self._items)
        if removed:
            self.logger.debug("Context pruned", removed=removed)
        return removed

    async def snapshot(self) -> Dict[str, Any]:
        """Return all non-expired items as a key-value dict."""
        self._purge_expired()
        return {key: item.value for key, item in self._items.items()}

    async def get_item(self, key: str) -> Optional[ContextItem]:
        """Get the full ContextItem by key (not just value)."""
        item = self._items.get(key)
        if item is None:
            return None
        if item.expired:
            del self._items[key]
            return None
        return item

    async def count(self) -> int:
        """Number of active (non-expired) items."""
        self._purge_expired()
        return len(self._items)

    async def clear(self) -> None:
        """Remove all items."""
        self._items.clear()

    # ── Internal ──────────────────────────────────────────────────

    def _purge_expired(self) -> None:
        """Remove expired items in-place."""
        expired = [k for k, v in self._items.items() if v.expired]
        for k in expired:
            del self._items[k]

    async def _evict_lowest_importance(self) -> None:
        """Remove the active item with lowest importance to make room."""
        if not self._items:
            return
        lowest_key = min(self._items, key=lambda k: self._items[k].importance)
        evicted = self._items.pop(lowest_key)
        self.logger.debug(
            "Evicted context item",
            key=lowest_key,
            importance=evicted.importance,
        )
