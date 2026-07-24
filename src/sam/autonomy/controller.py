"""Autonomy Controller — Sprint 32.

Manages the current autonomy level and adjusts it dynamically
based on confidence, risk, and system state.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.autonomy.models import AutonomyLevel, AutonomyConfig

logger = structlog.get_logger()


class AutonomyController:
    """Controls the current autonomy level and adjusts it dynamically."""

    def __init__(self, config: Optional[AutonomyConfig] = None) -> None:
        self._config = config or AutonomyConfig()
        self._current_level: AutonomyLevel = self._config.default_level
        self._history: List[Dict[str, Any]] = []
        self.logger = logger.bind(component="AutonomyController")

    async def get_current_level(self) -> AutonomyLevel:
        return self._current_level

    async def set_level(
        self,
        level: AutonomyLevel,
        reason: str = "",
        confidence: float = 100.0,
    ) -> None:
        """Manually set the autonomy level."""
        old_level = self._current_level
        self._current_level = level
        self._record(old_level, level, reason, confidence)
        self.logger.info(
            "Autonomy level set",
            old=old_level.value,
            new=level.value,
            reason=reason,
        )

    async def adjust_level(
        self,
        confidence: float,
        risk: float,
    ) -> AutonomyLevel:
        """Automatically adjust autonomy level based on confidence and risk.

        High confidence + low risk → increase autonomy.
        Low confidence + high risk → decrease autonomy.
        """
        old_level = self._current_level
        current_numeric = old_level.numeric

        # Determine direction
        if confidence >= self._config.min_confidence_for_autonomous and risk < 0.3:
            # Safe to increase
            new_numeric = min(5, current_numeric + 1)
            reason = f"High confidence ({confidence:.0f}), low risk ({risk:.2f})"
        elif confidence < 50.0 or risk > 0.7:
            # Need to decrease
            new_numeric = max(1, current_numeric - 1)
            reason = f"Low confidence ({confidence:.0f}) or high risk ({risk:.2f})"
        else:
            return self._current_level

        new_level = AutonomyLevel.from_numeric(new_numeric)
        if new_level != old_level:
            self._current_level = new_level
            self._record(old_level, new_level, reason, confidence)
            self.logger.info(
                "Autonomy adjusted",
                old=old_level.value,
                new=new_level.value,
                reason=reason,
            )
        return self._current_level

    async def get_autonomy_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        history = list(self._history)
        history.reverse()
        return history[:limit]

    async def get_config(self) -> AutonomyConfig:
        return self._config

    async def reset_to_default(self) -> None:
        await self.set_level(self._config.default_level, "Reset to default")

    def _record(
        self,
        old: AutonomyLevel,
        new: AutonomyLevel,
        reason: str,
        confidence: float,
    ) -> None:
        self._history.append({
            "old_level": old.value,
            "new_level": new.value,
            "reason": reason,
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        if len(self._history) > 10_000:
            self._history = self._history[-5000:]
