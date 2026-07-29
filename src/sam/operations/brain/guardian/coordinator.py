"""
OP-311 — GuardianCoordinator

Mengorkestrasi pipeline:
  Observation → Reasoning → Decision → Recommendation → Mission Proposal → Approval → Dashboard

Tidak boleh menjalankan mission.
Hanya koordinasi.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class GuardianPipelineResult:
    pipeline_id: str
    started_at: str
    completed_at: str
    observation_passed: bool
    reasoning_passed: bool
    decision_passed: bool
    recommendation_passed: bool
    proposal_passed: bool
    approval_passed: bool
    dashboard_passed: bool
    gate_result: Optional[Any] = None
    errors: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "observation_passed": self.observation_passed,
            "reasoning_passed": self.reasoning_passed,
            "decision_passed": self.decision_passed,
            "recommendation_passed": self.recommendation_passed,
            "proposal_passed": self.proposal_passed,
            "approval_passed": self.approval_passed,
            "dashboard_passed": self.dashboard_passed,
            "gate_result": self.gate_result.to_dict() if hasattr(self.gate_result, "to_dict") else str(self.gate_result),
            "errors": list(self.errors),
        }


class GuardianCoordinator:
    """
    Mengorkestrasi pipeline guardian.

    Pipeline:
      Observation → Reasoning → Decision → Recommendation
      → Mission Proposal → Approval → Dashboard

    Tidak menjalankan mission.
    """

    def __init__(self, gate: Any, audit: Any, state: Any):
        self._gate = gate
        self._audit = audit
        self._state = state
        self._pipeline_count: int = 0

    def run_pipeline(
        self,
        observation: Any,
        reasoning_context: Any,
        decision_context: Any,
        evaluator: Any,
        alternative_gen: Any,
        package_builder: Any,
        approval_builder: Any,
        conversation: Any,
        dashboard_service: Any,
    ) -> GuardianPipelineResult:
        """
        Jalankan pipeline lengkap.
        Semua parameter adalah instance yang sudah diinisialisasi.
        """
        pid = f"gp-{datetime.now().timestamp():.0f}-{self._pipeline_count}"
        self._pipeline_count += 1
        started = datetime.now().isoformat(timespec="seconds")
        errors: List[str] = []

        # Stage 1: Observation
        obs_pass = observation is not None
        if not obs_pass:
            errors.append("Observation stage failed: no observation provided")

        # Stage 2: Reasoning
        reasoning_pass = reasoning_context is not None
        if not reasoning_pass:
            errors.append("Reasoning stage failed: no reasoning context")

        # Stage 3: Decision
        decision_pass = decision_context is not None and evaluator is not None
        if not decision_pass:
            errors.append("Decision stage failed: missing context or evaluator")

        # Stage 4: Recommendation / Alternatives
        rec_pass = alternative_gen is not None
        if not rec_pass:
            errors.append("Recommendation stage failed: no alternative generator")

        # Stage 5: Mission Proposal
        proposal_pass = package_builder is not None
        if not proposal_pass:
            errors.append("Proposal stage failed: no package builder")

        # Stage 6: Approval
        approval_pass = approval_builder is not None
        if not approval_pass:
            errors.append("Approval stage failed: no approval builder")

        # Stage 7: Dashboard
        dash_pass = dashboard_service is not None
        if not dash_pass:
            errors.append("Dashboard stage failed: no dashboard service")

        # Stage 8: Gate — evaluate all stages
        gate_result = None
        if obs_pass and reasoning_pass and decision_pass and rec_pass:
            if proposal_pass and approval_pass:
                try:
                    gate_result = self._gate.evaluate(
                        observation=observation,
                        reasoning_context=reasoning_context,
                        decision_context=decision_context,
                        evaluation=evaluator,
                        alternatives=alternative_gen,
                        package=package_builder,
                        approval=approval_builder,
                    )
                except Exception as e:
                    errors.append(f"Gate evaluation error: {e}")

        # Audit trail
        try:
            self._audit.log_gate_passed(pid, gate_result)
        except Exception as e:
            errors.append(f"Audit error: {e}")

        completed = datetime.now().isoformat(timespec="seconds")

        return GuardianPipelineResult(
            pipeline_id=pid,
            started_at=started,
            completed_at=completed,
            observation_passed=obs_pass,
            reasoning_passed=reasoning_pass,
            decision_passed=decision_pass,
            recommendation_passed=rec_pass,
            proposal_passed=proposal_pass,
            approval_passed=approval_pass,
            dashboard_passed=dash_pass,
            gate_result=gate_result,
            errors=tuple(errors),
        )
