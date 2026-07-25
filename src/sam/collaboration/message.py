"""Message Model — Sprint 26 Fase 2.

Defines the communication primitives for multi-agent collaboration:
MessageType, MessagePriority, and Message with full lifecycle tracking.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class MessageType(str, Enum):
    """Types of messages exchanged between agents."""
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"
    BROADCAST = "BROADCAST"
    KNOWLEDGE_SHARE = "KNOWLEDGE_SHARE"
    TASK_DELEGATE = "TASK_DELEGATE"
    HEARTBEAT = "HEARTBEAT"
    ERROR = "ERROR"


class MessagePriority(str, Enum):
    """Priority levels for agent messages."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


MESSAGE_STATUSES = frozenset({"SENT", "DELIVERED", "READ", "FAILED"})


class Message:
    """A message exchanged between agents in the SAM collaboration ecosystem.

    Supports request-response correlation, broadcast (receiver_id=None),
    priority-based delivery, and status lifecycle: SENT → DELIVERED → READ / FAILED.
    """

    def __init__(
        self,
        id: str,
        type: MessageType,
        sender_id: str,
        payload: Dict[str, Any],
        receiver_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        timestamp: Optional[datetime] = None,
        status: str = "SENT",
    ) -> None:
        if status not in MESSAGE_STATUSES:
            raise ValueError(
                f"Invalid status '{status}'. Must be one of {sorted(MESSAGE_STATUSES)}"
            )
        self.id = id
        self.type = type if isinstance(type, MessageType) else MessageType(type)
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.correlation_id = correlation_id or id
        self.priority = priority if isinstance(priority, MessagePriority) else MessagePriority(priority)
        self.payload = payload
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "correlation_id": self.correlation_id,
            "priority": self.priority.value,
            "payload": json.dumps(self.payload),
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Message:
        return cls(
            id=data["id"],
            type=MessageType(data["type"]),
            sender_id=data["sender_id"],
            receiver_id=data.get("receiver_id"),
            correlation_id=data.get("correlation_id", data["id"]),
            priority=MessagePriority(data.get("priority", "NORMAL")),
            payload=_parse_json_dict(data.get("payload", "{}")),
            timestamp=_parse_dt(data.get("timestamp")),
            status=data.get("status", "SENT"),
        )

    def __repr__(self) -> str:
        return (
            f"Message(id={self.id!r}, type={self.type.value!r}, "
            f"sender={self.sender_id!r}, receiver={self.receiver_id!r}, "
            f"status={self.status!r})"
        )


def _parse_json_dict(val: Any) -> Dict[str, Any]:
    if val is None:
        return {}
    if isinstance(val, dict):
        return val
    try:
        parsed = json.loads(val)
        return parsed if isinstance(parsed, dict) else {}
    except (ValueError, TypeError):
        return {}


def _parse_dt(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None
