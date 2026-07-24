"""Runtime Node Model — entitas kelas satu dalam cluster SAM."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class NodeStatus(str, enum.Enum):
    """Status lifecycle untuk runtime node."""

    INITIALIZING = "INITIALIZING"
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    UNHEALTHY = "UNHEALTHY"


class NodeCapabilities(str, enum.Enum):
    """Kemampuan yang dimiliki sebuah node."""

    SCHEDULER = "SCHEDULER"
    WORKER = "WORKER"
    PLUGIN_HOST = "PLUGIN_HOST"
    KNOWLEDGE_HOST = "KNOWLEDGE_HOST"
    API_GATEWAY = "API_GATEWAY"


class RuntimeNode(BaseModel):
    """Model untuk sebuah runtime node dalam cluster SAM."""

    node_id: str
    cluster_id: str
    hostname: str
    status: NodeStatus = NodeStatus.INITIALIZING
    capabilities: List[NodeCapabilities] = Field(default_factory=list)
    version: str = ""
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)
    health: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    labels: Dict[str, str] = Field(default_factory=dict)

    class Config:
        use_enum_values = True
        extra = "forbid"

    @property
    def is_online(self) -> bool:
        return self.status == NodeStatus.ONLINE

    @property
    def is_alive(self, timeout_seconds: int = 30) -> bool:
        """Check apakah node masih hidup berdasarkan last_heartbeat."""
        elapsed = (datetime.utcnow() - self.last_heartbeat).total_seconds()
        return elapsed < timeout_seconds

    def has_capability(self, capability: NodeCapabilities) -> bool:
        return capability in self.capabilities
