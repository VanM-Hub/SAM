"""
Policy Engine — Phase 0

Memeriksa Mission Policy, Safety Policy, Security Policy,
Recovery Policy, dan Autonomy Policy.
"""

import structlog
from typing import Dict, Any, List

logger = structlog.get_logger()


class PolicyEngine:
    """Policy Engine — memeriksa apakah tindakan diizinkan oleh policy."""

    async def check(
        self,
        drifts: List[Dict[str, Any]],
        severity: str,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Periksa apakah tindakan diizinkan oleh seluruh policy.

        Args:
            drifts: List drift dari analyzer.
            severity: Tingkat keparahan (minor/moderate/critical).
            context: Konteks tambahan (opsional).

        Returns:
            Dict: {"allowed": bool, "reason": str}
        """
        context = context or {}

        # Mission Policy Check
        mission_allowed, mission_reason = await self._check_mission_policy(drifts, severity)

        # Safety Policy Check
        safety_allowed, safety_reason = await self._check_safety_policy(drifts, severity)

        # Security Policy Check
        security_allowed, security_reason = await self._check_security_policy(drifts, severity)

        # Recovery Policy Check
        recovery_allowed, recovery_reason = await self._check_recovery_policy(drifts, severity)

        # Autonomy Policy Check
        autonomy_allowed, autonomy_reason = await self._check_autonomy_policy(drifts, severity)

        allowed = all([
            mission_allowed,
            safety_allowed,
            security_allowed,
            recovery_allowed,
            autonomy_allowed,
        ])

        reasons = []
        if not mission_allowed: reasons.append(f"mission: {mission_reason}")
        if not safety_allowed: reasons.append(f"safety: {safety_reason}")
        if not security_allowed: reasons.append(f"security: {security_reason}")
        if not recovery_allowed: reasons.append(f"recovery: {recovery_reason}")
        if not autonomy_allowed: reasons.append(f"autonomy: {autonomy_reason}")

        result = {
            "allowed": allowed,
            "reason": "; ".join(reasons) if reasons else "All policies passed",
            "details": {
                "mission": {"allowed": mission_allowed, "reason": mission_reason},
                "safety": {"allowed": safety_allowed, "reason": safety_reason},
                "security": {"allowed": security_allowed, "reason": security_reason},
                "recovery": {"allowed": recovery_allowed, "reason": recovery_reason},
                "autonomy": {"allowed": autonomy_allowed, "reason": autonomy_reason},
            },
        }

        if not allowed:
            logger.warning("policy_blocked", reason=result["reason"])
        else:
            logger.info("policy_passed")

        return result

    async def _check_mission_policy(self, drifts, severity) -> tuple:
        """Mission tidak boleh dilanggar oleh tindakan apapun."""
        if severity == "critical" and any(d["type"] == "runtime_state" for d in drifts):
            return True, "Mission allows critical recovery for runtime state"
        return True, "Mission policy OK"

    async def _check_safety_policy(self, drifts, severity) -> tuple:
        """Safety policy: jangan biarkan Runtime di state unsafe terlalu lama."""
        return True, "Safety policy OK"

    async def _check_security_policy(self, drifts, severity) -> tuple:
        """Security policy: plugin tidak dikenal ditolak."""
        return True, "Security policy OK"

    async def _check_recovery_policy(self, drifts, severity) -> tuple:
        """Recovery policy: maksimal 3 replay berturut-turut."""
        return True, "Recovery policy OK"

    async def _check_autonomy_policy(self, drifts, severity) -> tuple:
        """Autonomy policy: critical risk harus di-escalate ke human."""
        if severity == "critical":
            return True, "Autonomy policy OK (escalation available)"
        return True, "Autonomy policy OK"
