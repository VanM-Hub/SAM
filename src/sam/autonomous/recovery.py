"""
Auto Recovery — Phase 1

Recovery otomatis dari insiden menggunakan strategi bertingkat.
"""

import structlog
from typing import Dict, Any, Optional
from .models import AutonomousAction, ActionType, RiskLevel

logger = structlog.get_logger()


class AutoRecovery:
    """Auto Recovery — execute recovery strategies berdasarkan insiden."""

    def __init__(self, coordinator):
        self.coordinator = coordinator

    async def recover_from_incident(self, incident_id: str, cause: str) -> AutonomousAction:
        """Recovery otomatis dari suatu insiden.

        Args:
            incident_id: ID insiden.
            cause: Deskripsi penyebab.

        Returns:
            AutonomousAction yang di-execute.
        """
        strategy = self._select_strategy(cause)

        action = AutonomousAction(
            action_type=strategy["action_type"],
            target=strategy["target"],
            reason="Auto-recovery from incident {0}: {1}".format(incident_id, cause),
            confidence=strategy.get("confidence", 0.6),
            risk_level=strategy.get("risk", RiskLevel.MEDIUM),
            steps=strategy.get("steps", []),
            incident_id=incident_id,
        )

        executor = self.coordinator.action_executor
        result = await executor.execute(action)

        logger.info(
            "auto_recovery_completed",
            incident_id=incident_id,
            action_id=action.id,
            status=result.status.value,
        )
        return result

    def _select_strategy(self, cause: str) -> Dict[str, Any]:
        """Pilih strategi recovery berdasarkan penyebab."""
        cause_lower = cause.lower()

        if "worker" in cause_lower or "plugin" in cause_lower:
            return {
                "action_type": ActionType.RESTART,
                "target": "worker",
                "confidence": 0.8,
                "risk": RiskLevel.MEDIUM,
                "steps": ["Stop worker", "Verify stop", "Start worker", "Verify health"],
            }

        if "memory" in cause_lower or "disk" in cause_lower:
            return {
                "action_type": ActionType.RECOVER,
                "target": "runtime",
                "confidence": 0.6,
                "risk": RiskLevel.HIGH,
                "steps": ["Evacuate workflows", "Free resources", "Resume workflows", "Verify"],
            }

        if "auth" in cause_lower or "credential" in cause_lower:
            return {
                "action_type": ActionType.ESCALATE,
                "target": "operator",
                "confidence": 0.9,
                "risk": RiskLevel.LOW,
                "steps": ["Notify operator", "Provide diagnostic info", "Wait for resolution"],
            }

        # Default: restart target umum
        return {
            "action_type": ActionType.RESTART,
            "target": "runtime",
            "confidence": 0.5,
            "risk": RiskLevel.HIGH,
            "steps": ["Check state", "Restart runtime", "Verify", "Run guardian cycle"],
        }
