"""Graceful Degradation — Sprint 32.

Lower autonomy level when confidence drops or risk increases.
Provides smooth transitions rather than abrupt changes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.autonomy.models import AutonomyLevel

logger = structlog.get_logger()

DEGRADE_STEP = 1  # Number of levels to drop
UPGRADE_STEP = 1  # Number of levels to raise
MIN_LEVEL = AutonomyLevel.OBSERVE
MAX_LEVEL = AutonomyLevel.AUTONOMOUS


class GracefulDegradation:
    """Manages graceful autonomy degradation and recovery."""

    def __init__(self) -> None:
        self._history: List[Dict[str, Any]] = []
        self._degraded_since: Optional[datetime] = None
        self._recovery_attempts: int = 0
        self.logger = logger.bind(component="GracefulDegradation")

    async def degrade(
        self,
        current_level: AutonomyLevel,
        reason: str = "",
        steps: int = DEGRADE_STEP,
    ) -> AutonomyLevel:
        """Lower autonomy level by steps.

        Args:
            current_level: Current level.
            reason: Why degradation is needed.
            steps: Number of levels to drop (default 1).

        Returns:
            The new (lower) autonomy level.
        """
        current_numeric = current_level.numeric
        new_numeric = max(MIN_LEVEL.numeric, current_numeric - steps)
        new_level = AutonomyLevel.from_numeric(new_numeric)

        if new_level != current_level:
            if self._degraded_since is None:
                self._degraded_since = datetime.now(timezone.utc)
            self._recovery_attempts = 0
            self._record(current_level, new_level, reason, "degrade")
            self.logger.info(
                "Autonomy degraded",
                old=current_level.value,
                new=new_level.value,
                reason=reason,
            )

        return new_level

    async def upgrade(
        self,
        current_level: AutonomyLevel,
        reason: str = "",
        steps: int = UPGRADE_STEP,
    ) -> AutonomyLevel:
        """Raise autonomy level by steps.

        Args:
            current_level: Current level.
            reason: Why upgrade is possible.
            steps: Number of levels to raise (default 1).

        Returns:
            The new (higher) autonomy level.
        """
        current_numeric = current_level.numeric
        new_numeric = min(MAX_LEVEL.numeric, current_numeric + steps)
        new_level = AutonomyLevel.from_numeric(new_numeric)

        if new_level != current_level:
            self._recovery_attempts += 1
            # Only clear degraded_since if we've recovered to ASSIST or higher
            if new_level.numeric >= AutonomyLevel.ASSIST.numeric:
                self._degraded_since = None
            self._record(current_level, new_level, reason, "upgrade")
            self.logger.info(
                "Autonomy upgraded",
                old=current_level.value,
                new=new_level.value,
                reason=reason,
            )

        return new_level

    async def get_degradation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        history = list(self._history)
        history.reverse()
        return history[:limit]

    async def is_degraded(self) -> bool:
        """Check if the system is currently in a degraded state."""
        return self._degraded_since is not None

    async def get_degraded_duration(self) -> Optional[float]:
        """Seconds since degradation started (or None if not degraded)."""
        if self._degraded_since is None:
            return None
        return (datetime.now(timezone.utc) - self._degraded_since).total_seconds()

    async def get_recovery_attempts(self) -> int:
        return self._recovery_attempts

    async def reset(self) -> None:
        self._history.clear()
        self._degraded_since = None
        self._recovery_attempts = 0

    def _record(
        self,
        old: AutonomyLevel,
        new: AutonomyLevel,
        reason: str,
        change_type: str,
    ) -> None:
        self._history.append({
            "old_level": old.value,
            "new_level": new.value,
            "reason": reason,
            "change_type": change_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        if len(self._history) > 10_000:
            self._history = self._history[-5000:]
