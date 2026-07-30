"""
Gateway Router.

Rule-based routing for approval requests.
Provider agnostic. Deterministic.
"""

from typing import Dict, Any, List
from .submission_plan import ApprovalSubmissionPlan


class GatewayRouter:
    """Routes approval requests to appropriate destinations."""

    SUPPORTED_ROUTES = ["default", "manual", "fast_track", "escalation"]

    def __init__(self) -> None:
        self._routes_used: Dict[str, int] = {r: 0 for r in self.SUPPORTED_ROUTES}

    def route(self, plan: ApprovalSubmissionPlan) -> str:
        """Determine route based on plan properties."""
        if not plan.ready:
            route = "manual"
        elif plan.metadata and plan.metadata.priority >= 3:
            route = "fast_track"
        elif plan.metadata and plan.metadata.priority >= 1:
            route = "default"
        else:
            route = "default"

        self._routes_used[route] = self._routes_used.get(route, 0) + 1
        return route

    @property
    def routes_used(self) -> Dict[str, int]:
        return dict(self._routes_used)

    @property
    def supported_routes(self) -> List[str]:
        return list(self.SUPPORTED_ROUTES)
