import structlog
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = structlog.get_logger()


@dataclass(frozen=True)
class RuntimeContext:
    """Current runtime context."""
    mission_name: str
    workspace: str
    cluster: Optional[str]
    operator: Optional[str]
    mode: str  # production, development, testing


class ContextEngine:
    """Engine untuk menyediakan context operasional."""

    def __init__(self):
        self._context = RuntimeContext(
            mission_name="Protect OpenClaw Runtime",
            workspace="default",
            cluster=None,
            operator=None,
            mode="production"
        )

    def get_context(self) -> RuntimeContext:
        """Get current runtime context."""
        return self._context

    def update_mission(self, mission_name: str) -> None:
        """Update mission name."""
        self._context = RuntimeContext(
            mission_name=mission_name,
            workspace=self._context.workspace,
            cluster=self._context.cluster,
            operator=self._context.operator,
            mode=self._context.mode
        )
        logger.info("context_updated", mission=mission_name)

    def update_operator(self, operator: str) -> None:
        """Update operator name."""
        self._context = RuntimeContext(
            mission_name=self._context.mission_name,
            workspace=self._context.workspace,
            cluster=self._context.cluster,
            operator=operator,
            mode=self._context.mode
        )
        logger.info("context_updated", operator=operator)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dict."""
        return {
            "mission_name": self._context.mission_name,
            "workspace": self._context.workspace,
            "cluster": self._context.cluster,
            "operator": self._context.operator,
            "mode": self._context.mode,
        }
