"""Federation Manager — Sprint 31.

Manages relationships between clusters: registration, lifecycle,
connection pooling, and cluster discovery.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger()


CLUSTER_STATUS_ONLINE = "ONLINE"
CLUSTER_STATUS_OFFLINE = "OFFLINE"
CLUSTER_STATUS_SUSPENDED = "SUSPENDED"
CLUSTER_STATUS_DECOMMISSIONED = "DECOMMISSIONED"


@dataclass
class FederatedCluster:
    """A remote cluster participating in the federation.

    Attributes:
        id: Unique cluster identifier.
        name: Human-readable name.
        endpoint: Connection endpoint (URL / address).
        status: ONLINE, OFFLINE, SUSPENDED, DECOMMISSIONED.
        trust_score: Current trust score (0.0–1.0).
        capabilities: List of knowledge types this cluster can provide.
        last_seen: Last heartbeat / contact timestamp.
        metadata: Additional info (version, region, owner, etc.).
    """
    id: str = ""
    name: str = ""
    endpoint: str = ""
    status: str = CLUSTER_STATUS_ONLINE
    trust_score: float = 0.5
    capabilities: List[str] = field(default_factory=list)
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            object.__setattr__(self, "id", f"fc_{uuid.uuid4().hex[:12]}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "endpoint": self.endpoint,
            "status": self.status,
            "trust_score": self.trust_score,
            "capabilities": self.capabilities,
            "last_seen": self.last_seen.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> FederatedCluster:
        return cls(
            id=d.get("id", ""),
            name=d.get("name", ""),
            endpoint=d.get("endpoint", ""),
            status=d.get("status", CLUSTER_STATUS_ONLINE),
            trust_score=float(d.get("trust_score", 0.5)),
            capabilities=d.get("capabilities", []),
            last_seen=_parse_dt(d.get("last_seen")) or datetime.now(timezone.utc),
            metadata=d.get("metadata", {}),
        )


def _parse_dt(val: Any) -> Optional[datetime]:
    if val is None or isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


class FederationManager:
    """Manages the lifecycle of federated cluster relationships."""

    def __init__(self, local_cluster_id: str = "") -> None:
        self._local_id = local_cluster_id or f"cluster_{uuid.uuid4().hex[:8]}"
        self._clusters: Dict[str, FederatedCluster] = {}
        self._blacklist: set = set()
        self.logger = logger.bind(component="FederationManager")

    async def register_cluster(
        self,
        cluster_id: str,
        name: str,
        endpoint: str,
        capabilities: Optional[List[str]] = None,
    ) -> FederatedCluster:
        """Register or update a remote cluster."""
        cluster = FederatedCluster(
            id=cluster_id,
            name=name,
            endpoint=endpoint,
            capabilities=capabilities or [],
            status=CLUSTER_STATUS_ONLINE,
            trust_score=0.5,
        )
        self._clusters[cluster_id] = cluster
        self.logger.info("Cluster registered", cluster_id=cluster_id, name=name)
        return cluster

    async def unregister_cluster(self, cluster_id: str) -> None:
        """Remove a cluster from the federation."""
        self._clusters.pop(cluster_id, None)
        self.logger.info("Cluster unregistered", cluster_id=cluster_id)

    async def get_cluster(self, cluster_id: str) -> Optional[FederatedCluster]:
        return self._clusters.get(cluster_id)

    async def list_clusters(
        self,
        status: Optional[str] = None,
        min_trust: float = 0.0,
    ) -> List[FederatedCluster]:
        """List clusters with optional filters."""
        result = list(self._clusters.values())
        if status is not None:
            result = [c for c in result if c.status == status]
        if min_trust > 0:
            result = [c for c in result if c.trust_score >= min_trust]
        return result

    async def update_heartbeat(self, cluster_id: str) -> None:
        """Record a heartbeat from a cluster."""
        cluster = self._clusters.get(cluster_id)
        if cluster:
            cluster.last_seen = datetime.now(timezone.utc)
            cluster.status = CLUSTER_STATUS_ONLINE

    async def mark_offline(self, cluster_id: str) -> None:
        cluster = self._clusters.get(cluster_id)
        if cluster:
            cluster.status = CLUSTER_STATUS_OFFLINE

    async def blacklist_cluster(self, cluster_id: str) -> None:
        self._blacklist.add(cluster_id)

    async def is_blacklisted(self, cluster_id: str) -> bool:
        return cluster_id in self._blacklist

    async def get_local_cluster_id(self) -> str:
        return self._local_id

    async def count(self) -> int:
        return len(self._clusters)

    async def clear(self) -> None:
        self._clusters.clear()
        self._blacklist.clear()
