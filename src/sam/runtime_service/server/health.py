"""ServerHealth (Sprint 268).

Program D - Runtime Services & Deployment.
Health server (immutable).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ServerHealth:
    """Health server (immutable)."""
    status: str = "healthy"
    checks: List[str] = field(default_factory=list)

    def is_healthy(self) -> bool:
        return self.status == "healthy"


def build_server_health(server) -> ServerHealth:
    """Bangun health dari ServerRuntime."""
    if server.all_ready():
        checks = [c.name for c in server.components()]
        return ServerHealth(status="healthy", checks=checks)
    return ServerHealth(status="degraded",
                        checks=[c.name for c in server.components()])
