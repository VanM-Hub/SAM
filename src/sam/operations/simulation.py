"""
Simulation Mode — semua executor berjalan virtual.

Menghasilkan:
  ExecutionPlan (tidak berubah)
  Predicted outcome (prediksi hasil)
  Simulated verification (verifikasi simulasi)
  Simulated audit (audit simulasi)

Tidak menyentuh sistem nyata.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from .execution_plan import ExecutionPlan, ExecutionPlanBuilder, PlanStatus, VerificationStep
from .verification import VerificationOutcome, VerificationResult, Evidence
from .audit import AuditEventType, get_audit_trail
from .execution_policy import ExecutionPolicy


@dataclass
class SimulationResult:
    """Hasil simulasi — prediksi + verification + audit."""
    plan_id: str
    plan_title: str

    predicted_success: bool
    predicted_duration_ms: int
    predicted_evidence_count: int

    # Detail
    action_results: List[Dict[str, Any]] = field(default_factory=list)
    verifications: List[Any] = field(default_factory=list)

    # Audit
    audit_entries: List[str] = field(default_factory=list)

    # Policy
    policy_decisions: List[Any] = field(default_factory=list)

    def to_text(self) -> str:
        lines = [
            "=== Simulation: {} ===".format(self.plan_title),
            "Predicted: {} | Duration: {}ms | Evidence: {}".format(
                "SUCCESS" if self.predicted_success else "FAILURE",
                self.predicted_duration_ms,
                self.predicted_evidence_count,
            ),
        ]
        if self.action_results:
            lines.append("Actions:")
            for r in self.action_results:
                lines.append("  [{status}] {title} ({duration_ms}ms)".format(**r))
        if self.verifications:
            for v in self.verifications:
                lines.append("  Verify: {}".format(v.to_text() if hasattr(v, 'to_text') else str(v)))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "plan_title": self.plan_title,
            "predicted_success": self.predicted_success,
            "predicted_duration_ms": self.predicted_duration_ms,
            "predicted_evidence_count": self.predicted_evidence_count,
            "action_results": self.action_results,
            "policy_decisions": [d.to_dict() if hasattr(d, 'to_dict') else {} for d in self.policy_decisions],
        }


class SimulationEngine:
    """Simulation engine — semua virtual.

    Method utama: simulate(plan) -> SimulationResult
    """

    def __init__(self, policy: Optional[ExecutionPolicy] = None):
        self._policy = policy or ExecutionPolicy()

    def simulate(self, plan: ExecutionPlan) -> SimulationResult:
        """Simulasi satu ExecutionPlan.

        Args:
            plan: ExecutionPlan — rencana eksekusi

        Returns:
            SimulationResult — prediksi + verification + audit
        """
        # 1. Policy evaluation (simulasi mode)
        policy_decisions = self._policy.evaluate(plan, simulation_mode=True)

        # 2. Simulate each action
        action_results = []
        total_duration = 0
        all_success = True

        for i, action in enumerate(plan.actions):
            title = getattr(action, 'title', 'Action {}'.format(i))
            duration = getattr(action, 'estimated_duration_seconds', 10) * 10  # simulate ms
            action_success = True  # Default in simulation

            action_results.append({
                "index": i,
                "title": title,
                "duration_ms": duration,
                "status": "completed" if action_success else "failed",
            })
            total_duration += duration
            if not action_success:
                all_success = False

        # 3. Simulate verification
        verifications = []
        for step in plan.verification_steps:
            verifications.append(VerificationOutcome(
                step_index=step.action_index,
                expected_state=step.expected_state,
                check_method=step.check_method,
                result=VerificationResult.PASSED,
                evidence=[
                    Evidence(
                        key="simulated_" + step.expected_state[:20],
                        expected="pass",
                        actual="pass",
                        source="simulation",
                    )
                ],
                duration_ms=10,
            ))

        # 4. Audit
        audit = get_audit_trail()
        audit_entries = []
        e = audit.record(
            AuditEventType.AUDIT_LOG,
            plan.plan_id, "simulation",
            "Simulated: {}".format(plan.source_decision_title or plan.plan_id),
            description="Simulation mode — no real execution",
            actor="simulation",
        )
        audit_entries.append(e.id)

        return SimulationResult(
            plan_id=plan.plan_id,
            plan_title=plan.source_decision_title or plan.plan_id,
            predicted_success=all_success,
            predicted_duration_ms=total_duration,
            predicted_evidence_count=len(plan.verification_steps) + len(plan.actions),
            action_results=action_results,
            verifications=verifications,
            audit_entries=audit_entries,
            policy_decisions=policy_decisions,
        )

    def simulate_with_plan(self, proposal) -> SimulationResult:
        """Simulasi langsung dari DecisionProposal.

        Args:
            proposal: DecisionProposal

        Returns:
            SimulationResult
        """
        plan = ExecutionPlanBuilder.from_decision_proposal(proposal)
        return self.simulate(plan)
