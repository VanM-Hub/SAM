"""Knowledge Provenance — Sprint 31.

Every insight has an origin, confidence, evidence trail,
cluster of origin, and signature.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger()


@dataclass
class Provenance:
    """Provenance metadata for any insight or knowledge.

    Attributes:
        origin_cluster_id: Cluster where this knowledge originated.
        origin_node_id: Node within the origin cluster (if applicable).
        evidence_ids: List of evidence/reflection IDs supporting this knowledge.
        timestamp: When the knowledge was created.
        signature: Verification signature (future use).
        confidence_at_origin: Confidence when first created.
        transmission_path: List of cluster IDs this passed through.
    """
    origin_cluster_id: str = ""
    origin_node_id: str = ""
    evidence_ids: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    signature: str = ""
    confidence_at_origin: float = 1.0
    transmission_path: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "origin_cluster_id": self.origin_cluster_id,
            "origin_node_id": self.origin_node_id,
            "evidence_ids": self.evidence_ids,
            "timestamp": self.timestamp.isoformat(),
            "signature": self.signature,
            "confidence_at_origin": self.confidence_at_origin,
            "transmission_path": self.transmission_path,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Provenance:
        return cls(
            origin_cluster_id=d.get("origin_cluster_id", ""),
            origin_node_id=d.get("origin_node_id", ""),
            evidence_ids=d.get("evidence_ids", []),
            timestamp=_parse_dt(d.get("timestamp")) or datetime.now(timezone.utc),
            signature=d.get("signature", ""),
            confidence_at_origin=float(d.get("confidence_at_origin", 1.0)),
            transmission_path=d.get("transmission_path", []),
        )


def _parse_dt(val: Any) -> Optional[datetime]:
    if val is None or isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


class ProvenanceManager:
    """Tracks provenance for all federated insights."""

    def __init__(self) -> None:
        self._provenances: Dict[str, Provenance] = {}
        self.logger = logger.bind(component="ProvenanceManager")

    async def register(
        self,
        insight_id: str,
        provenance: Provenance,
    ) -> None:
        """Register provenance for an insight."""
        self._provenances[insight_id] = provenance
        self.logger.debug("Provenance registered", insight_id=insight_id)

    async def get(self, insight_id: str) -> Optional[Provenance]:
        return self._provenances.get(insight_id)

    async def verify(self, insight_id: str) -> bool:
        """Verify that provenance exists (signature verification is future work)."""
        return insight_id in self._provenances

    async def count(self) -> int:
        return len(self._provenances)

    async def clear(self) -> None:
        self._provenances.clear()
