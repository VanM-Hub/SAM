"""
OP-313 — DecisionGate

Semua proposal harus melewati gate.
Gate memeriksa:
  - approval
  - evidence
  - confidence
  - policy
  - trust
  - mission state

Jika gagal: DecisionRejected
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class DecisionRejected:
    reason: str
    gate_check: str  # approval, evidence, confidence, policy, trust, mission
    detail: str = ""
    rejected_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reason": self.reason,
            "gate_check": self.gate_check,
            "detail": self.detail,
            "rejected_at": self.rejected_at,
        }


@dataclass(frozen=True)
class GateResult:
    passed: bool
    checked_approval: bool = False
    checked_evidence: bool = False
    checked_confidence: bool = False
    checked_policy: bool = False
    checked_trust: bool = False
    checked_mission: bool = False
    rejection: Optional[DecisionRejected] = None
    checked_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "passed": self.passed,
            "checked_approval": self.checked_approval,
            "checked_evidence": self.checked_evidence,
            "checked_confidence": self.checked_confidence,
            "checked_policy": self.checked_policy,
            "checked_trust": self.checked_trust,
            "checked_mission": self.checked_mission,
            "checked_at": self.checked_at,
        }
        if self.rejection:
            result["rejection"] = self.rejection.to_dict()
        return result


class DecisionGate:
    """
    Gate untuk semua proposal.
    Semua proposal harus melewati gate sebelum lanjut.
    """

    def __init__(self, policy_engine: Any):
        self._policy_engine = policy_engine

    def evaluate(
        self,
        observation: Any = None,
        reasoning_context: Any = None,
        decision_context: Any = None,
        evaluation: Any = None,
        alternatives: Any = None,
        package: Any = None,
        approval: Any = None,
        trust_level: float = 0.0,
        mission_state: str = "",
    ) -> GateResult:
        now = datetime.now().isoformat(timespec="seconds")

        # Check 1: Approval
        approved_check = self._check_approval(package, evaluation)
        if not approved_check.passed:
            return GateResult(passed=False, checked_approval=True, rejection=approved_check.rejection, checked_at=now)

        # Check 2: Evidence
        ev_check = self._check_evidence(package, evaluation)
        if not ev_check.passed:
            return GateResult(
                passed=False, checked_approval=True, checked_evidence=True,
                rejection=ev_check.rejection, checked_at=now,
            )

        # Check 3: Confidence
        conf_check = self._check_confidence(evaluation)
        if not conf_check.passed:
            return GateResult(
                passed=False, checked_approval=True, checked_evidence=True, checked_confidence=True,
                rejection=conf_check.rejection, checked_at=now,
            )

        # Check 4: Policy
        policy_check = self._check_policy(package, evaluation, trust_level)
        if not policy_check.passed:
            return GateResult(
                passed=False, checked_approval=True, checked_evidence=True, checked_confidence=True,
                checked_policy=True, rejection=policy_check.rejection, checked_at=now,
            )

        # Check 5: Trust
        trust_check = self._check_trust(trust_level)
        if not trust_check.passed:
            return GateResult(
                passed=False, checked_approval=True, checked_evidence=True, checked_confidence=True,
                checked_policy=True, checked_trust=True, rejection=trust_check.rejection, checked_at=now,
            )

        # Check 6: Mission state
        mission_check = self._check_mission(mission_state)
        if not mission_check.passed:
            return GateResult(
                passed=False, checked_approval=True, checked_evidence=True, checked_confidence=True,
                checked_policy=True, checked_trust=True, checked_mission=True,
                rejection=mission_check.rejection, checked_at=now,
            )

        # All passed
        return GateResult(
            passed=True,
            checked_approval=True, checked_evidence=True, checked_confidence=True,
            checked_policy=True, checked_trust=True, checked_mission=True,
            checked_at=now,
        )

    # ── Internal checks ───────────────────────────────────────────

    def _check_approval(self, package: Any, evaluation: Any) -> _CheckResult:
        if package is None:
            return _CheckResult(False, DecisionRejected(
                reason="No package provided",
                gate_check="approval",
                detail="Package is None",
            ))
        risk = getattr(evaluation, "risk_level", "low") if evaluation else "low"
        needs_approval = getattr(package, "requires_approval", False)
        if risk in ("high", "critical") and needs_approval:
            # Approval required — check if approval exists
            has_approval = getattr(package, "selected_alternative", "") != ""
            if not has_approval:
                return _CheckResult(False, DecisionRejected(
                    reason="High/critical risk requires approval",
                    gate_check="approval",
                    detail=f"Risk: {risk}, approval missing",
                ))
        return _CheckResult(True, None)

    def _check_evidence(self, package: Any, evaluation: Any) -> _CheckResult:
        if package is None:
            return _CheckResult(False, DecisionRejected(
                reason="No package for evidence check",
                gate_check="evidence",
            ))
        alternatives = getattr(package, "alternatives", ())
        has_evidence = any(
            len(getattr(a, "evidence_basis", ())) > 0 for a in alternatives
        )
        if not has_evidence:
            return _CheckResult(False, DecisionRejected(
                reason="No evidence found in any alternative",
                gate_check="evidence",
                detail="All alternatives have empty evidence_basis",
            ))
        return _CheckResult(True, None)

    def _check_confidence(self, evaluation: Any) -> _CheckResult:
        if evaluation is None:
            return _CheckResult(False, DecisionRejected(
                reason="No evaluation for confidence check",
                gate_check="confidence",
            ))
        confidence = getattr(evaluation, "confidence", 1.0)
        if confidence < 0.4:
            return _CheckResult(False, DecisionRejected(
                reason="Confidence below minimum threshold",
                gate_check="confidence",
                detail=f"Confidence: {confidence:.2f}, threshold: 0.4",
            ))
        return _CheckResult(True, None)

    def _check_policy(self, package: Any, evaluation: Any, trust_level: float) -> _CheckResult:
        if self._policy_engine is None:
            return _CheckResult(False, DecisionRejected(
                reason="No policy engine configured",
                gate_check="policy",
            ))
        policy_result = self._policy_engine.evaluate(
            proposal=package,
            evaluation=evaluation,
            trust_level=trust_level,
        )
        if not policy_result.passed:
            violations = "; ".join(v.message for v in policy_result.violations[:3])
            return _CheckResult(False, DecisionRejected(
                reason="Policy violations detected",
                gate_check="policy",
                detail=violations,
            ))
        return _CheckResult(True, None)

    def _check_trust(self, trust_level: float) -> _CheckResult:
        if trust_level < 0.3:
            return _CheckResult(False, DecisionRejected(
                reason="Trust level critically low",
                gate_check="trust",
                detail=f"Trust level: {trust_level:.2f}",
            ))
        return _CheckResult(True, None)

    def _check_mission(self, mission_state: str) -> _CheckResult:
        if mission_state and mission_state not in ("READY", "RUNNING", ""):
            return _CheckResult(False, DecisionRejected(
                reason="Mission in invalid state",
                gate_check="mission",
                detail=f"State: {mission_state}",
            ))
        return _CheckResult(True, None)


# ── Internal helper ───────────────────────────────────────────────

@dataclass
class _CheckResult:
    passed: bool
    rejection: Optional[DecisionRejected] = None
