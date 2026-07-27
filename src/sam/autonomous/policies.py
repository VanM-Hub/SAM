"""
Safety Policy — Phase 1

Kebijakan keamanan untuk tindakan otomatis (auto-approve rules,
risk assessment, guardrails).
"""

import structlog
from typing import Dict, Tuple
from .models import AutonomousAction, ActionType, RiskLevel, AutonomousActionStatus

logger = structlog.get_logger()

# Risk matrix: (action_type, target) -> risk_level
RISK_MATRIX: Dict[Tuple[str, str], RiskLevel] = {
    (ActionType.RESTART.value, "plugin"): RiskLevel.LOW,
    (ActionType.RESTART.value, "worker"): RiskLevel.MEDIUM,
    (ActionType.RESTART.value, "gateway"): RiskLevel.HIGH,
    (ActionType.RESTART.value, "runtime"): RiskLevel.CRITICAL,
    (ActionType.RECOVER.value, "workflow"): RiskLevel.MEDIUM,
    (ActionType.RECOVER.value, "session"): RiskLevel.MEDIUM,
    (ActionType.RESUME.value, "workflow"): RiskLevel.LOW,
    (ActionType.ISOLATE.value, "plugin"): RiskLevel.MEDIUM,
    (ActionType.ISOLATE.value, "worker"): RiskLevel.HIGH,
    (ActionType.ESCALATE.value, "operator"): RiskLevel.LOW,
    (ActionType.ESCALATE.value, "admin"): RiskLevel.MEDIUM,
}

# Default risk jika tidak ada di matrix
DEFAULT_RISK = RiskLevel.MEDIUM


class SafetyPolicy:
    """Kebijakan keamanan untuk tindakan otomatis."""

    AUTO_APPROVE_RISKS = {RiskLevel.LOW, RiskLevel.MEDIUM}
    MIN_CONFIDENCE_FOR_AUTO = 0.7

    REQUIRE_APPROVAL_RISKS = {RiskLevel.HIGH, RiskLevel.CRITICAL}

    # Tindakan yang DILARANG auto-execute
    BLOCKED_ACTIONS: Dict[Tuple[str, str], str] = {
        (ActionType.ISOLATE.value, "runtime"): "Isolating runtime is prohibited",
        (ActionType.RESTART.value, "runtime"): "Restarting runtime requires manual approval",
    }

    @classmethod
    def can_auto_approve(cls, action: AutonomousAction) -> bool:
        """Periksa apakah tindakan dapat auto-approve.

        Syarat:
        - Risk level LOW atau MEDIUM
        - Confidence >= 0.7
        - Tidak masuk daftar BLOCKED_ACTIONS
        """
        # Cek BLOCKED_ACTIONS
        key = (action.action_type.value, action.target)
        if key in cls.BLOCKED_ACTIONS:
            logger.warning(
                "action_blocked",
                action_id=action.id,
                reason=cls.BLOCKED_ACTIONS[key],
            )
            return False

        # Cek risk + confidence
        if action.risk_level in cls.AUTO_APPROVE_RISKS and action.confidence >= cls.MIN_CONFIDENCE_FOR_AUTO:
            logger.info(
                "auto_approve_allowed",
                action_id=action.id,
                risk=action.risk_level.value,
                confidence=action.confidence,
            )
            return True

        logger.warning(
            "auto_approve_denied",
            action_id=action.id,
            risk=action.risk_level.value,
            confidence=action.confidence,
        )
        return False

    @classmethod
    def requires_approval(cls, action: AutonomousAction) -> bool:
        """Periksa apakah tindakan membutuhkan persetujuan manusia."""
        # Always require for blocked actions
        key = (action.action_type.value, action.target)
        if key in cls.BLOCKED_ACTIONS:
            return True

        return action.risk_level in cls.REQUIRE_APPROVAL_RISKS

    @classmethod
    def get_risk(cls, action_type: str, target: str) -> RiskLevel:
        """Dapatkan tingkat risiko berdasarkan aksi dan target."""
        key = (action_type, target)
        return RISK_MATRIX.get(key, DEFAULT_RISK)

    @classmethod
    def is_action_allowed(cls, action_type: str, target: str) -> bool:
        """Periksa apakah tipe aksi terhadap target diizinkan."""
        key = (action_type, target)
        return key not in cls.BLOCKED_ACTIONS
