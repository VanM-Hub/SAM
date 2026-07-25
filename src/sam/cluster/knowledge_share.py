"""Cluster Knowledge Share — Sprint 30.

Publish/subscribe knowledge, patterns, and recommendations across nodes.
Periodic pull/push synchronization.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional

import structlog

logger = structlog.get_logger()

MAX_KNOWLEDGE_TTL = 86400  # 24 hours
DEFAULT_TTL = 3600  # 1 hour


@dataclass
class SharedKnowledge:
    """A knowledge item shared across the cluster.

    Attributes:
        id: Unique identifier.
        source_node_id: Node that published this.
        knowledge_type: KNOWLEDGE, PATTERN, or RECOMMENDATION.
        content: Arbitrary content dict.
        confidence: 0.0–1.0.
        timestamp: When published.
        ttl: Time-to-live in seconds.
    """
    id: str = ""
    source_node_id: str = ""
    knowledge_type: str = "KNOWLEDGE"
    content: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.8
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ttl: int = DEFAULT_TTL

    def __post_init__(self) -> None:
        if not self.id:
            object.__setattr__(self, "id", f"sk_{uuid.uuid4().hex[:12]}")

    @property
    def expired(self) -> bool:
        if self.ttl <= 0:
            return False
        elapsed = (datetime.now(timezone.utc) - self.timestamp).total_seconds()
        return elapsed > self.ttl

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_node_id": self.source_node_id,
            "knowledge_type": self.knowledge_type,
            "content": self.content,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "ttl": self.ttl,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> SharedKnowledge:
        return cls(
            id=d.get("id", ""),
            source_node_id=d.get("source_node_id", ""),
            knowledge_type=d.get("knowledge_type", "KNOWLEDGE"),
            content=d.get("content", {}),
            confidence=float(d.get("confidence", 0.8)),
            timestamp=_parse_dt(d.get("timestamp")) or datetime.now(timezone.utc),
            ttl=int(d.get("ttl", DEFAULT_TTL)),
        )


def _parse_dt(val: Any) -> Optional[datetime]:
    if val is None or isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


class ClusterKnowledgeShare:
    """Manages knowledge sharing across cluster nodes.

    Nodes can publish knowledge, subscribe to types, pull from peers.
    """

    def __init__(self) -> None:
        self._knowledge: Dict[str, SharedKnowledge] = {}
        self._subscriptions: Dict[str, List[str]] = {}  # type -> node_ids
        self._peers: Dict[str, List[SharedKnowledge]] = {}
        self.logger = logger.bind(component="ClusterKnowledgeShare")

    async def publish(self, knowledge: SharedKnowledge) -> None:
        """Publish knowledge to the cluster.

        Stores locally and marks for pull by peers.
        """
        self._knowledge[knowledge.id] = knowledge
        # Notify subscribers
        subscribers = self._subscriptions.get(knowledge.knowledge_type, [])
        for node_id in subscribers:
            if node_id not in self._peers:
                self._peers[node_id] = []
            self._peers[node_id].append(knowledge)
        self.logger.debug(
            "Knowledge published",
            id=knowledge.id,
            type=knowledge.knowledge_type,
            source=knowledge.source_node_id,
        )

    async def subscribe(
        self,
        knowledge_type: str,
        node_id: str,
    ) -> None:
        """Subscribe a node to a knowledge type.

        Args:
            knowledge_type: KNOWLEDGE, PATTERN, RECOMMENDATION.
            node_id: Subscribing node ID.
        """
        if knowledge_type not in self._subscriptions:
            self._subscriptions[knowledge_type] = []
        if node_id not in self._subscriptions[knowledge_type]:
            self._subscriptions[knowledge_type].append(node_id)

    async def pull(
        self,
        node_id: str,
        since: Optional[datetime] = None,
    ) -> List[SharedKnowledge]:
        """Pull pending knowledge for a node.

        Args:
            node_id: Requesting node ID.
            since: Only return knowledge after this timestamp.

        Returns:
            List of knowledge items, newest first.
        """
        pending = self._peers.pop(node_id, [])
        if since is not None:
            pending = [k for k in pending if k.timestamp > since]
        return pending

    async def get_shared(
        self,
        knowledge_type: str,
        limit: int = 100,
    ) -> List[SharedKnowledge]:
        """Get knowledge by type, newest first, filtered."""
        result = [
            k for k in self._knowledge.values()
            if k.knowledge_type == knowledge_type and not k.expired
        ]
        result.sort(key=lambda k: k.timestamp, reverse=True)
        return result[:limit]

    async def get_by_id(self, knowledge_id: str) -> Optional[SharedKnowledge]:
        return self._knowledge.get(knowledge_id)

    async def count(self) -> int:
        return len(self._knowledge)

    async def clear(self) -> None:
        self._knowledge.clear()
        self._subscriptions.clear()
        self._peers.clear()
