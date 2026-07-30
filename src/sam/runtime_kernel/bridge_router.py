"""Bridge Router — router bridge."""
from __future__ import annotations
from typing import Dict, List, Optional
from sam.runtime_kernel.runtime_adapter import BridgeRoute


class BridgeRouter:
    """Router bridge — preview-only."""

    def __init__(self) -> None:
        self._routes: Dict[str, BridgeRoute] = {}

    def add(self, route: BridgeRoute) -> None:
        self._routes[route.route_id] = route

    def get(self, route_id: str) -> BridgeRoute | None:
        return self._routes.get(route_id)

    def deactivate(self, route_id: str) -> BridgeRoute | None:
        route = self._routes.get(route_id)
        if not route:
            return None
        r2 = BridgeRoute(route_id=route.route_id, source=route.source,
                         target=route.target, active=False)
        self._routes[route_id] = r2
        return r2

    def list_active(self) -> List[BridgeRoute]:
        return [r for r in self._routes.values() if r.active]

    def count(self) -> int:
        return len(self._routes)
