"""
Decision Engine — Phase 0

Membuat keputusan berdasarkan GDP:
    Observe → Normalize → Evaluate → Policy Check →
    Risk Assessment → Plan → Approve → Execute → Verify → Audit
"""

import structlog
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

logger = structlog.get_logger()


class GuardianDecision(BaseModel):
    """Model keputusan Guardian yang di-audit."""
    decision_id: str
    event_id: str = ""
    mission_id: str = "mission-001"
    severity: str = "minor"
    risk: str = "low"
    action_plan: List[str] = Field(default_factory=list)
    approved: bool = False
    executed: bool = False
    verified: bool = False
    duration_ms: int = 0
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class DecisionEngine:
    """Decision Engine — jantung GDP (Evaluate → Plan → Approve → Execute → Verify → Audit)."""

    def __init__(self, policy_engine, action_engine):
        self.policy_engine = policy_engine
        self.action_engine = action_engine

    async def make_decision(
        self,
        drifts: List[Dict[str, Any]],
        mission_id: str = "mission-001",
    ) -> GuardianDecision:
        """Proses satu siklus keputusan Guardian.

        Args:
            drifts: List drift dari analyzer.
            mission_id: Mission ID yang berlaku.

        Returns:
            GuardianDecision lengkap dengan status audit.
        """
        import time
        start = time.time()
        decision_id = str(uuid.uuid4())[:8]
        event_id = str(uuid.uuid4())

        logger.info("decision_started", decision_id=decision_id, drift_count=len(drifts))

        # 1. Evaluate — tentukan severity dari drifts
        severity = self._evaluate_severity(drifts)

        # 2. Policy Check — apakah tindakan diizinkan?
        policy_result = await self.policy_engine.check(drifts, severity)
        if not policy_result["allowed"]:
            logger.warning("decision_blocked_by_policy",
                decision_id=decision_id,
                reason=policy_result["reason"],
            )
            elapsed_ms = int((time.time() - start) * 1000)
            return GuardianDecision(
                decision_id=decision_id,
                event_id=event_id,
                mission_id=mission_id,
                severity=severity,
                risk="unknown",
                action_plan=[],
                approved=False,
                executed=False,
                verified=False,
                duration_ms=elapsed_ms,
            )

        # 3. Risk Assessment
        risk = self._assess_risk(drifts)

        # 4. Plan — buat action plan berdasarkan drift
        action_plan = await self._create_plan(drifts)

        # 5. Approve — sesuai risk level
        approved = await self._approve(action_plan, severity, risk)

        # 6. Execute
        executed = False
        if approved:
            executed = await self.action_engine.execute(action_plan)
        else:
            logger.info("decision_not_approved",
                decision_id=decision_id,
                reason="Requires human approval for risk level",
            )

        # 7. Verify
        verified = False
        if executed:
            verified = await self.action_engine.verify(action_plan)

        elapsed_ms = int((time.time() - start) * 1000)

        # 8. Audit — tercatat via logger
        logger.info("decision_completed",
            decision_id=decision_id,
            severity=severity,
            risk=risk,
            approved=approved,
            executed=executed,
            verified=verified,
            duration_ms=elapsed_ms,
        )

        return GuardianDecision(
            decision_id=decision_id,
            event_id=event_id,
            mission_id=mission_id,
            severity=severity,
            risk=risk,
            action_plan=action_plan,
            approved=approved,
            executed=executed,
            verified=verified,
            duration_ms=elapsed_ms,
        )

    def _evaluate_severity(self, drifts: List[Dict]) -> str:
        """Tentukan severity dari drifts yang terdeteksi."""
        if any(d.get("severity") == "critical" for d in drifts):
            return "critical"
        if any(d.get("severity") == "moderate" for d in drifts):
            return "moderate"
        return "minor"

    def _assess_risk(self, drifts: List[Dict]) -> str:
        """Tentukan risk level berdasarkan drifts."""
        if any(d.get("severity") == "critical" for d in drifts):
            return "high"
        if any(d.get("severity") == "moderate" for d in drifts):
            return "medium"
        return "low"

    async def _create_plan(self, drifts: List[Dict]) -> List[str]:
        """Buat action plan dari daftar drift yang terdeteksi."""
        plan = []
        for drift in drifts:
            dtype = drift.get("type", "unknown")
            expected = drift.get("expected", "?")
            if dtype == "runtime_state":
                plan.append(f"transition_to({expected})")
            elif dtype == "plugins":
                plan.append(f"discover_and_load_plugins")
            elif dtype == "knowledge":
                plan.append("reload_knowledge")
            elif dtype == "memory":
                plan.append("restore_memory")
            elif dtype == "health":
                plan.append("run_health_recovery")
            else:
                plan.append(f"investigate_drift({dtype})")
        return plan

    async def _approve(self, action_plan: List[str], severity: str, risk: str) -> bool:
        """Approve action plan sesuai autonomy level.

        Aturan (Phase 0):
        - low risk → auto-approve
        - medium risk → auto-approve (kecuali severity critical)
        - high risk → butuh human approval (return False)
        """
        if risk == "low":
            return True
        if risk == "medium" and severity != "critical":
            return True
        # high risk atau critical severity → escalation
        return False
