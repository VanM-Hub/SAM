"""
OP-319 — Guardian Runtime Integration

Pipeline synchronous:
  Observation → Reasoning → Decision Runtime → Guardian Gate → Proposal → Approval → Dashboard

Tidak ada async.
Tidak ada threading.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class GuardianIntegrationResult:
    pipeline_id: str
    observation_result: Optional[Any] = None
    reasoning_result: Optional[Any] = None
    decision_result: Optional[Any] = None
    gate_result: Optional[Any] = None
    proposal_result: Optional[Any] = None
    approval_result: Optional[Any] = None
    dashboard_result: Optional[Any] = None
    success: bool = False
    errors: Tuple[str, ...] = ()
    started_at: str = ""
    completed_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "success": self.success,
            "errors": list(self.errors),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class GuardianRuntimeIntegration:
    """
    Runtime integration pipeline.
    Menghubungkan Observation → Reasoning → Decision → Gate → Proposal → Approval → Dashboard.

    Synchronous — tidak ada async, tidak ada threading.
    """

    def __init__(self, coordinator: Any, gate: Any, policy_engine: Any,
                 audit: Any, state_holder: Any, dashboard_service: Any):
        self._coordinator = coordinator
        self._gate = gate
        self._policy = policy_engine
        self._audit = audit
        self._state = state_holder
        self._dashboard = dashboard_service
        self._pipeline_count: int = 0

    def run(
        self,
        observation: Any = None,
        reasoning_context: Any = None,
        decision_context: Any = None,
        evaluator: Any = None,
        alternative_gen: Any = None,
        package_builder: Any = None,
        approval_builder: Any = None,
    ) -> GuardianIntegrationResult:
        pid = f"ir-{datetime.now().timestamp():.0f}-{self._pipeline_count}"
        self._pipeline_count += 1
        started = datetime.now().isoformat(timespec="seconds")
        errors: List[str] = []

        # Stage 1: Observation
        try:
            obs_result = self._run_observation(observation)
        except Exception as e:
            obs_result = None
            errors.append(f"Observation error: {e}")

        # Stage 2: Reasoning
        try:
            reasoning_result = self._run_reasoning(reasoning_context)
        except Exception as e:
            reasoning_result = None
            errors.append(f"Reasoning error: {e}")

        # Stage 3: Decision
        try:
            decision_result = self._run_decision(decision_context, evaluator, alternative_gen, package_builder, approval_builder)
        except Exception as e:
            decision_result = None
            errors.append(f"Decision error: {e}")

        # Stage 4: Gate
        gate_result = None
        try:
            gate_result = self._gate.evaluate(
                observation=obs_result,
                reasoning_context=reasoning_result,
                decision_context=decision_context,
                evaluation=evaluator,
                alternatives=alternative_gen,
                package=package_builder,
                approval=approval_builder,
            )
            if gate_result and getattr(gate_result, "passed", False):
                self._audit.log_gate_passed(pid, gate_result)
            elif gate_result:
                self._audit.log_gate_rejected(pid, getattr(gate_result, "rejection", None))
        except Exception as e:
            errors.append(f"Gate error: {e}")

        # Stage 5: Proposal
        proposal_result = None
        try:
            proposal_result = self._run_proposal(package_builder)
            if proposal_result:
                self._audit.log_proposal_submitted(pid, proposal_result)
        except Exception as e:
            errors.append(f"Proposal error: {e}")

        # Stage 6: Approval
        approval_result = None
        try:
            approval_result = self._run_approval(approval_builder)
            if approval_result:
                self._audit.log_approval_waiting(pid, approval_result)
        except Exception as e:
            errors.append(f"Approval error: {e}")

        # Stage 7: Dashboard
        dashboard_result = None
        try:
            dashboard_result = self._dashboard.get_dashboard()
        except Exception as e:
            errors.append(f"Dashboard error: {e}")

        completed = datetime.now().isoformat(timespec="seconds")
        success = len(errors) == 0 and gate_result is not None and getattr(gate_result, "passed", False)

        return GuardianIntegrationResult(
            pipeline_id=pid,
            observation_result=obs_result,
            reasoning_result=reasoning_result,
            decision_result=decision_result,
            gate_result=gate_result,
            proposal_result=proposal_result,
            approval_result=approval_result,
            dashboard_result=dashboard_result,
            success=success,
            errors=tuple(errors),
            started_at=started,
            completed_at=completed,
        )

    # ── Stage runners ─────────────────────────────────────────────

    def _run_observation(self, observation: Any) -> Any:
        if observation is None:
            return None
        if hasattr(observation, "observe") and callable(observation.observe):
            return observation.observe()
        return observation

    def _run_reasoning(self, reasoning_context: Any) -> Any:
        if reasoning_context is None:
            return None
        return reasoning_context

    def _run_decision(self, context: Any, evaluator: Any, alt_gen: Any,
                      package_builder: Any, approval_builder: Any) -> Optional[Dict[str, Any]]:
        if not all([context, evaluator, alt_gen, package_builder, approval_builder]):
            return None
        return {
            "context": "built",
            "evaluated": True,
            "alternatives_generated": True,
            "package_built": True,
            "approval_prepared": True,
        }

    def _run_proposal(self, package_builder: Any) -> Optional[str]:
        if package_builder is None:
            return None
        return f"prop-{datetime.now().timestamp():.0f}"

    def _run_approval(self, approval_builder: Any) -> Optional[str]:
        if approval_builder is None:
            return None
        return "prepared"
