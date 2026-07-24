"""Knowledge Sovereignty — Sprint 31.

Each cluster can control what knowledge it shares and under what conditions.
Supports PUBLIC, INTERNAL, and RESTRICTED sharing policies.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger()


POLICY_PUBLIC = "PUBLIC"
POLICY_INTERNAL = "INTERNAL"
POLICY_RESTRICTED = "RESTRICTED"


@dataclass
class SovereigntyPolicy:
    """Sharing policy for a knowledge type or category.

    Attributes:
        id: Unique policy ID.
        cluster_id: Cluster this policy applies to.
        knowledge_type: PATTERN, RECOMMENDATION, STRATEGY, etc.
        sharing_policy: PUBLIC, INTERNAL, or RESTRICTED.
        allowed_clusters: Whitelist for RESTRICTED sharing.
        max_confidence_to_share: Max confidence to share (0.0-1.0; 1.0 = share all).
        created_at: When this policy was created.
    """
    id: str = ""
    cluster_id: str = ""
    knowledge_type: str = ""
    sharing_policy: str = POLICY_PUBLIC
    allowed_clusters: List[str] = field(default_factory=list)
    max_confidence_to_share: float = 1.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.id:
            object.__setattr__(self, "id", f"sp_{uuid.uuid4().hex[:12]}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "cluster_id": self.cluster_id,
            "knowledge_type": self.knowledge_type,
            "sharing_policy": self.sharing_policy,
            "allowed_clusters": self.allowed_clusters,
            "max_confidence_to_share": self.max_confidence_to_share,
        }


@dataclass
class SharingPolicy:
    """Simplified access control for a single knowledge item."""
    can_view: bool = True
    can_copy: bool = True
    can_redistribute: bool = False
    requires_attribution: bool = True


class SovereigntyManager:
    """Manages sharing policies and sovereignty rules per cluster."""

    DEFAULT_INTERNAL_POLICY = SovereigntyPolicy(
        id="default_internal",
        sharing_policy=POLICY_INTERNAL,
        knowledge_type="ALL",
        max_confidence_to_share=0.8,
    )
    DEFAULT_PUBLIC_POLICY = SovereigntyPolicy(
        id="default_public",
        sharing_policy=POLICY_PUBLIC,
        knowledge_type="ALL",
    )

    def __init__(self) -> None:
        self._policies: Dict[str, SovereigntyPolicy] = {}
        self._default_policy = self.DEFAULT_PUBLIC_POLICY
        self.logger = logger.bind(component="SovereigntyManager")

    async def set_policy(self, policy: SovereigntyPolicy) -> None:
        """Set a sovereignty policy."""
        self._policies[policy.id] = policy
        self.logger.debug("Sovereignty policy set", id=policy.id, policy=policy.sharing_policy)

    async def get_policy(self, policy_id: str) -> Optional[SovereigntyPolicy]:
        return self._policies.get(policy_id)

    async def get_policies_for_cluster(
        self,
        cluster_id: str,
    ) -> List[SovereigntyPolicy]:
        """Get all policies for a cluster."""
        return [p for p in self._policies.values() if p.cluster_id == cluster_id]

    async def check_access(
        self,
        knowledge_type: str,
        requesting_cluster_id: str,
        policy_id: Optional[str] = None,
    ) -> SharingPolicy:
        """Check if a cluster can access a knowledge type.

        Args:
            knowledge_type: Type of knowledge requested.
            requesting_cluster_id: The cluster requesting access.
            policy_id: Specific policy to check (optional).

        Returns:
            SharingPolicy with access rights.
        """
        if policy_id and policy_id in self._policies:
            policy = self._policies[policy_id]
        else:
            # Find matching policy by type, or use default
            matching = [p for p in self._policies.values()
                        if p.knowledge_type == knowledge_type]
            policy = matching[0] if matching else self._default_policy

        if policy.sharing_policy == POLICY_PUBLIC:
            return SharingPolicy(can_view=True, can_copy=True, can_redistribute=True)

        elif policy.sharing_policy == POLICY_INTERNAL:
            return SharingPolicy(can_view=True, can_copy=True, can_redistribute=False)

        elif policy.sharing_policy == POLICY_RESTRICTED:
            allowed = requesting_cluster_id in policy.allowed_clusters
            return SharingPolicy(
                can_view=allowed,
                can_copy=allowed,
                can_redistribute=False,
                requires_attribution=True,
            )

        return SharingPolicy(can_view=True)

    async def set_default_policy(self, policy: SovereigntyPolicy) -> None:
        self._default_policy = policy

    async def list_policies(self) -> List[SovereigntyPolicy]:
        return list(self._policies.values())

    async def clear(self) -> None:
        self._policies.clear()
