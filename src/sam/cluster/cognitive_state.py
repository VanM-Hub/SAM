"""Cluster Cognitive State — Sprint 30.

Share cognitive state across nodes. Each node publishes its cognitive state
and can view the aggregated cluster cognitive state.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.cognition.state import CognitiveState
from sam.cognition.attention import FocusArea

logger = structlog.get_logger()


@dataclass
class ClusterCognitiveState:
    """Aggregated cognitive state of the entire cluster.

    Attributes:
        cluster_id: Cluster identifier.
        node_states: Dict of node_id → CognitiveState.
        aggregated_confidence: Mean confidence across nodes.
        dominant_focus: Most common FocusArea.
        avg_autonomy_level: Mean autonomy level.
        node_count: Number of nodes that reported state.
        timestamp: When this aggregate was computed.
    """
    cluster_id: str = ""
    node_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    aggregated_confidence: float = 0.0
    dominant_focus: str = "balanced"
    avg_autonomy_level: float = 0.0
    node_count: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.cluster_id:
            object.__setattr__(self, "cluster_id", f"ccs_{uuid.uuid4().hex[:12]}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "node_states": self.node_states,
            "aggregated_confidence": self.aggregated_confidence,
            "dominant_focus": self.dominant_focus,
            "avg_autonomy_level": self.avg_autonomy_level,
            "node_count": self.node_count,
            "timestamp": self.timestamp.isoformat(),
        }


class ClusterCognitiveStateManager:
    """Manages cognitive state sharing across cluster nodes."""

    def __init__(self) -> None:
        self._node_states: Dict[str, CognitiveState] = {}
        self._state_history: Dict[str, List[CognitiveState]] = {}
        self._cluster_state: Optional[ClusterCognitiveState] = None
        self.logger = logger.bind(component="ClusterCognitiveStateManager")

    async def publish_state(self, node_id: str, state: CognitiveState) -> None:
        """Publish a node's cognitive state to the cluster."""
        self._node_states[node_id] = state

        # Record history
        if node_id not in self._state_history:
            self._state_history[node_id] = []
        self._state_history[node_id].append(state)
        if len(self._state_history[node_id]) > 1000:
            self._state_history[node_id] = self._state_history[node_id][-500:]

        # Recompute aggregate
        self._cluster_state = self._compute_aggregate()

        self.logger.debug(
            "Node state published",
            node=node_id,
            focus=state.focus,
        )

    async def get_cluster_state(self) -> ClusterCognitiveState:
        """Get the aggregated cluster cognitive state."""
        if self._cluster_state is None:
            self._cluster_state = ClusterCognitiveState(
                node_count=0,
                aggregated_confidence=100.0,
                dominant_focus="balanced",
                avg_autonomy_level=2.0,
            )
        return self._cluster_state

    async def get_node_state(self, node_id: str) -> Optional[CognitiveState]:
        """Get the latest cognitive state of a specific node."""
        return self._node_states.get(node_id)

    async def get_state_history(
        self,
        node_id: str,
        limit: int = 50,
    ) -> List[CognitiveState]:
        """Get state history for a specific node."""
        history = self._state_history.get(node_id, [])
        history = list(history)
        history.reverse()
        return history[:limit]

    async def get_active_node_count(self) -> int:
        return len(self._node_states)

    async def clear(self) -> None:
        self._node_states.clear()
        self._state_history.clear()
        self._cluster_state = None

    def _compute_aggregate(self) -> ClusterCognitiveState:
        """Compute aggregate from all published node states."""
        if not self._node_states:
            return ClusterCognitiveState(
                node_count=0,
                aggregated_confidence=100.0,
                dominant_focus="balanced",
                avg_autonomy_level=2.0,
            )

        confidences = []
        focuses: Dict[str, int] = {}
        autonomy_levels = []
        node_states_raw: Dict[str, Dict[str, Any]] = {}

        for nid, state in self._node_states.items():
            confidences.append(state.confidence)
            focuses[state.focus] = focuses.get(state.focus, 0) + 1
            autonomy_levels.append(state.autonomy_level)
            node_states_raw[nid] = state.to_dict()

        avg_conf = sum(confidences) / len(confidences)
        avg_auto = sum(autonomy_levels) / len(autonomy_levels)
        dominant = max(focuses, key=focuses.get)

        return ClusterCognitiveState(
            node_states=node_states_raw,
            aggregated_confidence=round(avg_conf, 1),
            dominant_focus=dominant,
            avg_autonomy_level=round(avg_auto, 2),
            node_count=len(self._node_states),
        )
