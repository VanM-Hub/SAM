"""Knowledge Federation Protocol — Sprint 31.

Defines the message protocol for exchanging insights, patterns,
recommendations, and strategies between federated clusters.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.federation.provenance import Provenance

logger = structlog.get_logger()

MESSAGE_TYPE_OFFER = "OFFER"
MESSAGE_TYPE_REQUEST = "REQUEST"
MESSAGE_TYPE_ACCEPT = "ACCEPT"
MESSAGE_TYPE_REJECT = "REJECT"
MESSAGE_TYPE_ACK = "ACK"


@dataclass
class KnowledgeOffer:
    """An offer to share knowledge with a peer cluster.

    Attributes:
        id: Unique offer ID.
        source_cluster_id: Offering cluster.
        target_cluster_id: Receiving cluster (or ALL).
        insight_type: PATTERN, RECOMMENDATION, STRATEGY, REFLECTION, LESSON.
        content: The knowledge payload.
        confidence: 0.0–1.0.
        trust_required: Minimum trust required to use.
        sovereignty_policy: PUBLIC, INTERNAL, RESTRICTED.
        ttl: Time-to-live in seconds.
        timestamp: When the offer was created.
    """
    id: str = ""
    source_cluster_id: str = ""
    target_cluster_id: str = "ALL"
    insight_type: str = "KNOWLEDGE"
    content: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.8
    trust_required: float = 0.3
    sovereignty_policy: str = "PUBLIC"
    ttl: int = 86400
    freshness: float = 1.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.id:
            object.__setattr__(self, "id", f"ko_{uuid.uuid4().hex[:12]}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_cluster_id": self.source_cluster_id,
            "target_cluster_id": self.target_cluster_id,
            "insight_type": self.insight_type,
            "content": self.content,
            "confidence": self.confidence,
            "trust_required": self.trust_required,
            "sovereignty_policy": self.sovereignty_policy,
            "ttl": self.ttl,
            "freshness": self.freshness,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class KnowledgeRequest:
    """A request for knowledge from a peer cluster.

    Attributes:
        id: Unique request ID.
        requester_cluster_id: Requesting cluster.
        insight_type: Type of knowledge requested.
        min_confidence: Minimum confidence required.
        max_results: Maximum number of results.
    """
    id: str = ""
    requester_cluster_id: str = ""
    insight_type: str = "KNOWLEDGE"
    min_confidence: float = 0.5
    max_results: int = 20

    def __post_init__(self) -> None:
        if not self.id:
            object.__setattr__(self, "id", f"kr_{uuid.uuid4().hex[:12]}")


@dataclass
class FederationMessage:
    """A protocol message between federated clusters.

    Attributes:
        id: Unique message ID.
        message_type: OFFER, REQUEST, ACCEPT, REJECT, ACK.
        source_cluster_id: Sender.
        target_cluster_id: Recipient.
        payload: Message payload.
        timestamp: When sent.
    """
    id: str = ""
    message_type: str = MESSAGE_TYPE_OFFER
    source_cluster_id: str = ""
    target_cluster_id: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.id:
            object.__setattr__(self, "id", f"fm_{uuid.uuid4().hex[:12]}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "message_type": self.message_type,
            "source": self.source_cluster_id,
            "target": self.target_cluster_id,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
        }


class FederationProtocol:
    """Handles message exchange between federated clusters."""

    def __init__(self) -> None:
        self._messages: List[FederationMessage] = []
        self.logger = logger.bind(component="FederationProtocol")

    async def send_offer(self, offer: KnowledgeOffer) -> FederationMessage:
        """Create and record an OFFER message."""
        msg = FederationMessage(
            message_type=MESSAGE_TYPE_OFFER,
            source_cluster_id=offer.source_cluster_id,
            target_cluster_id=offer.target_cluster_id,
            payload=offer.to_dict(),
        )
        self._messages.append(msg)
        return msg

    async def send_request(self, request: KnowledgeRequest) -> FederationMessage:
        """Create and record a REQUEST message."""
        msg = FederationMessage(
            message_type=MESSAGE_TYPE_REQUEST,
            source_cluster_id=request.requester_cluster_id,
            payload={"insight_type": request.insight_type,
                     "min_confidence": request.min_confidence,
                     "max_results": request.max_results},
        )
        self._messages.append(msg)
        return msg

    async def get_messages(
        self,
        target_cluster_id: str,
        limit: int = 100,
    ) -> List[FederationMessage]:
        """Get messages addressed to a cluster."""
        result = [m for m in self._messages
                  if m.target_cluster_id in (target_cluster_id, "ALL")]
        result.sort(key=lambda m: m.timestamp, reverse=True)
        return result[:limit]

    async def clear(self) -> None:
        self._messages.clear()
