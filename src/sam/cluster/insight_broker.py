"""Cluster Insight Broker — Sprint 30.

Manages insights from all nodes. Each insight has type, content, confidence,
and tracks which nodes have read it.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger()


@dataclass
class Insight:
    """An insight registered by a node.

    Attributes:
        id: Unique identifier.
        node_id: Originating node.
        insight_type: Category (e.g. "perf_bottleneck", "healing_pattern").
        content: Insight payload.
        confidence: 0.0–1.0.
        timestamp: When created.
        read_by: Set of node IDs that have read this insight.
    """
    id: str = ""
    node_id: str = ""
    insight_type: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.8
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    read_by: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            object.__setattr__(self, "id", f"ins_{uuid.uuid4().hex[:12]}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "node_id": self.node_id,
            "insight_type": self.insight_type,
            "content": self.content,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "read_by": self.read_by,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Insight:
        return cls(
            id=d.get("id", ""),
            node_id=d.get("node_id", ""),
            insight_type=d.get("insight_type", ""),
            content=d.get("content", {}),
            confidence=float(d.get("confidence", 0.8)),
            timestamp=_parse_dt(d.get("timestamp")) or datetime.now(timezone.utc),
            read_by=d.get("read_by", []),
        )


def _parse_dt(val: Any) -> Optional[datetime]:
    if val is None or isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


class InsightBroker:
    """Manages insights from all cluster nodes.

    Each insight can be registered, queried by node/type/time,
    and tracked for read status.
    """

    def __init__(self) -> None:
        self._insights: Dict[str, Insight] = {}
        self.logger = logger.bind(component="InsightBroker")

    async def register_insight(self, insight: Insight) -> None:
        """Register a new insight from a node."""
        self._insights[insight.id] = insight
        self.logger.debug(
            "Insight registered",
            id=insight.id,
            node=insight.node_id,
            type=insight.insight_type,
        )

    async def get_insights(
        self,
        node_id: Optional[str] = None,
        insight_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Insight]:
        """Query insights with optional filters.

        Results sorted newest first.
        """
        result = list(self._insights.values())
        if node_id is not None:
            result = [i for i in result if i.node_id == node_id]
        if insight_type is not None:
            result = [i for i in result if i.insight_type == insight_type]
        result.sort(key=lambda i: i.timestamp, reverse=True)
        return result[:limit]

    async def get_latest_insights(
        self,
        node_id: str,
        count: int = 10,
    ) -> List[Insight]:
        """Get the most recent insights from a specific node."""
        result = [
            i for i in self._insights.values()
            if i.node_id == node_id
        ]
        result.sort(key=lambda i: i.timestamp, reverse=True)
        return result[:count]

    async def mark_as_read(self, insight_id: str, node_id: str) -> None:
        """Mark an insight as read by a node."""
        insight = self._insights.get(insight_id)
        if insight is None:
            return
        if node_id not in insight.read_by:
            insight.read_by.append(node_id)

    async def get_unread_count(self, node_id: str) -> int:
        """Count insights not yet read by a node."""
        count = 0
        for insight in self._insights.values():
            if node_id not in insight.read_by:
                count += 1
        return count

    async def get_by_id(self, insight_id: str) -> Optional[Insight]:
        return self._insights.get(insight_id)

    async def count(self) -> int:
        return len(self._insights)

    async def clear(self) -> None:
        self._insights.clear()
