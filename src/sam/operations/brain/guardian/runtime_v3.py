"""
OP-348 — Runtime Integration V3

Pipeline lengkap:
  Observation → Reasoning → Decision → Guardian → Governance → Readiness → Dashboard → Conversation

Tidak menjalankan mission. Tidak ada eksekusi. Synchronous.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class V3IntegrationResult:
    """Hasil lengkap pipeline V3."""
    pipeline_id: str
    success: bool
    observation_ok: bool = True
    reasoning_ok: bool = True
    decision_ok: bool = True
    guardian_ok: bool = True
    governance_ok: bool = True
    readiness_ok: bool = True
    dashboard_ok: bool = True
    conversation_ok: bool = True
    errors: Tuple[str, ...] = field(default_factory=tuple)
    started_at: str = ""
    completed_at: str = ""

    @property
    def all_passed(self) -> bool:
        return all([self.observation_ok, self.reasoning_ok,
                    self.decision_ok, self.guardian_ok,
                    self.governance_ok, self.readiness_ok,
                    self.dashboard_ok, self.conversation_ok])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "success": self.success,
            "all_passed": self.all_passed,
            "stages": {
                "observation": self.observation_ok,
                "reasoning": self.reasoning_ok,
                "decision": self.decision_ok,
                "guardian": self.guardian_ok,
                "governance": self.governance_ok,
                "readiness": self.readiness_ok,
                "dashboard": self.dashboard_ok,
                "conversation": self.conversation_ok,
            },
            "errors": list(self.errors),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class GuardianRuntimeV3Integration:
    """Runtime Integration V3 — Pipeline 8-stage synchronous.

    Pipeline:
      Observation → Reasoning → Decision → Guardian → Governance → Readiness → Dashboard → Conversation

    Tidak ada eksekusi. Hanya evaluasi.
    """

    def __init__(
        self,
        observation: Any = None,
        reasoning: Any = None,
        decision: Any = None,
        guardian: Any = None,
        governance: Any = None,
        readiness: Any = None,
        risk_assessment: Any = None,
        dashboard_v3: Any = None,
        conversation_governance: Any = None,
    ):
        self._observation = observation
        self._reasoning = reasoning
        self._decision = decision
        self._guardian = guardian
        self._governance = governance
        self._readiness = readiness
        self._risk_assessment = risk_assessment
        self._dashboard_v3 = dashboard_v3
        self._conversation_governance = conversation_governance
        self._pipeline_count = 0

    @property
    def pipeline_count(self) -> int:
        return self._pipeline_count

    def run(self, **kwargs: Any) -> V3IntegrationResult:
        """Jalankan pipeline 8-stage. Synchronous. Read-only."""
        pid = f"v3-{datetime.now().strftime('%H%M%S')}-{self._pipeline_count}"
        started_at = datetime.now().isoformat(timespec="seconds")
        self._pipeline_count += 1
        errors: List[str] = []
        pipeline_data: Dict[str, Any] = {}

        # Stage 1: Observation
        obs_ok = True
        if self._observation:
            try:
                obs = self._observation.observe(**kwargs) if hasattr(
                    self._observation, "observe") else self._observation(**kwargs)
                pipeline_data["observation"] = {"collected": True}
            except Exception as e:
                errors.append(f"observation: {e}")
                obs_ok = False

        # Stage 2: Reasoning
        reas_ok = True
        if self._reasoning:
            try:
                reas = self._reasoning.reason(**kwargs) if hasattr(
                    self._reasoning, "reason") else self._reasoning(**kwargs)
                pipeline_data["reasoning"] = {"completed": True}
            except Exception as e:
                errors.append(f"reasoning: {e}")
                reas_ok = False

        # Stage 3: Decision
        dec_ok = True
        if self._decision:
            try:
                dec = self._decision.decide(**kwargs) if hasattr(
                    self._decision, "decide") else self._decision(**kwargs)
                pipeline_data["decision"] = {"completed": True}
            except Exception as e:
                errors.append(f"decision: {e}")
                dec_ok = False

        # Stage 4: Guardian
        guard_ok = True
        if self._guardian:
            try:
                guard = self._guardian.run(**kwargs) if hasattr(
                    self._guardian, "run") else self._guardian(**kwargs)
                guard_ok = getattr(guard, "success", True) if True else True
                pipeline_data["guardian"] = {"completed": True}
            except Exception as e:
                errors.append(f"guardian: {e}")
                guard_ok = False

        # Stage 5: Governance
        gov_ok = True
        if self._governance:
            try:
                gov = self._governance.evaluate(**kwargs)
                gov_ok = gov.approved
                pipeline_data["governance"] = {
                    "status": gov.overall_status.value,
                    "score": gov.overall_score,
                }
            except Exception as e:
                errors.append(f"governance: {e}")
                gov_ok = False

        # Stage 6: Readiness
        ready_ok = True
        if self._readiness:
            try:
                ready = self._readiness.evaluate(**kwargs)
                ready_ok = ready.ready
                pipeline_data["readiness"] = {
                    "level": ready.overall_level.value,
                    "ready": ready.ready,
                }
            except Exception as e:
                errors.append(f"readiness: {e}")
                ready_ok = False

        # Stage 7: Dashboard
        dash_ok = True
        if self._dashboard_v3:
            try:
                dash_cards = {
                    "governance": self._dashboard_v3.build_governance_card(**kwargs),
                    "risk": self._dashboard_v3.build_risk_card(**kwargs),
                    "readiness": self._dashboard_v3.build_readiness_card(**kwargs),
                    "policy": self._dashboard_v3.build_policy_card(**kwargs),
                    "guardian": self._dashboard_v3.build_guardian_summary_card(**kwargs),
                    "blocked": self._dashboard_v3.build_blocked_missions_card(**kwargs),
                    "approvals": self._dashboard_v3.build_pending_approval_card(**kwargs),
                    "operational": self._dashboard_v3.build_operational_status_card(**kwargs),
                }
                pipeline_data["dashboard"] = {
                    k: v.to_dict() for k, v in dash_cards.items()
                }
            except Exception as e:
                errors.append(f"dashboard: {e}")
                dash_ok = False

        # Stage 8: Conversation
        conv_ok = True
        if self._conversation_governance:
            try:
                conv = self._conversation_governance.query("governance_report", **kwargs)
                conv_ok = conv.success
                pipeline_data["conversation"] = {"report_generated": conv.success}
            except Exception as e:
                errors.append(f"conversation: {e}")
                conv_ok = False

        completed_at = datetime.now().isoformat(timespec="seconds")
        success = len(errors) == 0

        return V3IntegrationResult(
            pipeline_id=pid,
            success=success,
            observation_ok=obs_ok,
            reasoning_ok=reas_ok,
            decision_ok=dec_ok,
            guardian_ok=guard_ok,
            governance_ok=gov_ok,
            readiness_ok=ready_ok,
            dashboard_ok=dash_ok,
            conversation_ok=conv_ok,
            errors=tuple(errors),
            started_at=started_at,
            completed_at=completed_at,
        )
