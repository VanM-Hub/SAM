"""Node Discovery — menemukan dan memfilter node dalam cluster."""

from __future__ import annotations

from typing import List

import structlog

from .node import RuntimeNode, NodeStatus, NodeCapabilities
from .node_registry import NodeRegistry


class NodeDiscovery:
    """Discovery service untuk menemukan peer dalam cluster.

    Membaca dari NodeRegistry yang sudah terisi oleh node-node yang
    mendaftarkan dirinya masing-masing.
    """

    def __init__(self, registry: NodeRegistry):
        self._registry = registry
        self._logger = structlog.get_logger()

    async def discover_peers(self) -> List[RuntimeNode]:
        """Temukan semua node dalam cluster (termasuk diri sendiri)."""
        nodes = await self._registry.list()
        self._logger.debug("peers_discovered", count=len(nodes))
        return nodes

    async def get_active_nodes(self) -> List[RuntimeNode]:
        """Hanya node dengan status ONLINE."""
        return await self._registry.list(status=NodeStatus.ONLINE)

    async def get_nodes_with_capability(
        self, capability: NodeCapabilities
    ) -> List[RuntimeNode]:
        """Filter node yang memiliki capability tertentu.

        Iterasi semua node, filter yang capability-nya mengandung
        `capability` dan status-nya ONLINE.
        """
        all_nodes = await self._registry.list()
        result = [
            n for n in all_nodes
            if n.status == NodeStatus.ONLINE and n.has_capability(capability)
        ]
        self._logger.debug(
            "nodes_with_capability",
            capability=capability.value if isinstance(capability, NodeCapabilities) else capability,
            count=len(result),
        )
        return result
