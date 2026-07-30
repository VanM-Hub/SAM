"""
Gateway Registry.

Registry for gateway operations.
Does NOT instantiate Approval Runtime.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from .gateway_request import ApprovalGatewayRequest, GatewayStatistics, GatewaySnapshot


class GatewayRegistry:
    def __init__(self) -> None:
        self._requests: List[ApprovalGatewayRequest] = []
        self._routes: List[str] = []
        self._default_route: str = "default"

    def register(self, request: ApprovalGatewayRequest) -> None:
        self._requests.append(request)

    def record_route(self, route: str) -> None:
        self._routes.append(route)

    @property
    def last_request(self) -> Optional[ApprovalGatewayRequest]:
        return self._requests[-1] if self._requests else None

    @property
    def count(self) -> int:
        return len(self._requests)

    @property
    def default_route(self) -> str:
        return self._default_route

    def lookup(self, request_id: str) -> Optional[ApprovalGatewayRequest]:
        for r in reversed(self._requests):
            if r.request_id == request_id: return r
        return None

    def get_statistics(self) -> GatewayStatistics:
        ready = sum(1 for r in self._requests if r.ready)
        return GatewayStatistics(total=self.count, ready_count=ready,
                                  blocked_count=self.count - ready,
                                  timestamp=datetime.now().timestamp())

    def create_snapshot(self) -> GatewaySnapshot:
        stats = self.get_statistics()
        return GatewaySnapshot(snapshot_id=str(uuid.uuid4()), timestamp=datetime.now().timestamp(),
                                requests=list(self._requests[-20:]), statistics=stats)
