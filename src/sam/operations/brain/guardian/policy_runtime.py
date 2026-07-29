"""
OP-324 — Guardian Policy Evaluator

Evaluasi seluruh policy runtime.
  - NoAutoExecution
  - ApprovalRequired
  - ConversationOnly
  - ReadOnly
  - EvidenceRequired
  - TrustThreshold
  - ProviderHealthy
  - MissionAllowed

Output: PolicyViolation, PolicyResult
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class PolicyViolation:
    policy: str
    severity: str  # low, medium, high, critical
    message: str
    detail: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy": self.policy,
            "severity": self.severity,
            "message": self.message,
            "detail": self.detail,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class PolicyResult:
    policy: str
    passed: bool
    score: float = 1.0
    detail: str = ""
    violations: Tuple[PolicyViolation, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy": self.policy,
            "passed": self.passed,
            "score": self.score,
            "detail": self.detail,
            "violations": [v.to_dict() for v in self.violations],
        }


class GuardianPolicyEvaluator:
    """
    Mengevaluasi policy runtime Guardian.
    Hanya evaluasi — tidak mengubah state.
    """

    def __init__(self) -> None:
        self._results: List[PolicyResult] = []

    def evaluate_no_auto_execution(
        self, has_auto_execution: bool = False
    ) -> PolicyResult:
        violations: List[PolicyViolation] = []
        if has_auto_execution:
            violations.append(PolicyViolation(
                policy="NoAutoExecution",
                severity="critical",
                message="Auto-execution detected",
                detail="Pipeline attempted automatic execution without approval",
                timestamp=datetime.now().isoformat(timespec="seconds"),
            ))
        return PolicyResult(
            policy="NoAutoExecution",
            passed=not has_auto_execution,
            score=0.0 if has_auto_execution else 1.0,
            detail="Auto-execution must not occur" if has_auto_execution else "Passed",
            violations=tuple(violations),
        )

    def evaluate_approval_required(
        self, has_approval: bool = False, pending_approvals: int = 0
    ) -> PolicyResult:
        violations: List[PolicyViolation] = []
        if not has_approval:
            violations.append(PolicyViolation(
                policy="ApprovalRequired",
                severity="high",
                message="No approval mechanism found",
                detail="Pipeline must have approval step",
                timestamp=datetime.now().isoformat(timespec="seconds"),
            ))
        score = 1.0
        if pending_approvals > 20:
            score = 0.3
        elif pending_approvals > 10:
            score = 0.6
        return PolicyResult(
            policy="ApprovalRequired",
            passed=has_approval,
            score=score,
            detail="Approval backlog: {}".format(pending_approvals),
            violations=tuple(violations),
        )

    def evaluate_conversation_only(
        self, has_conversation: bool = False
    ) -> PolicyResult:
        violations: List[PolicyViolation] = []
        if not has_conversation:
            violations.append(PolicyViolation(
                policy="ConversationOnly",
                severity="high",
                message="No conversation interface",
                detail="Pipeline must communicate via conversation",
                timestamp=datetime.now().isoformat(timespec="seconds"),
            ))
        return PolicyResult(
            policy="ConversationOnly",
            passed=has_conversation,
            score=1.0 if has_conversation else 0.0,
            detail="Passed" if has_conversation else "Missing conversation interface",
            violations=tuple(violations),
        )

    def evaluate_read_only(
        self, is_read_only: bool = True
    ) -> PolicyResult:
        violations: List[PolicyViolation] = []
        if not is_read_only:
            violations.append(PolicyViolation(
                policy="ReadOnly",
                severity="critical",
                message="Mutating operation detected in read-only context",
                timestamp=datetime.now().isoformat(timespec="seconds"),
            ))
        return PolicyResult(
            policy="ReadOnly",
            passed=is_read_only,
            score=1.0 if is_read_only else 0.0,
            detail="Passed" if is_read_only else "Read-only violation",
            violations=tuple(violations),
        )

    def evaluate_evidence_required(
        self, has_evidence: bool = False, evidence_quality: float = 0.0
    ) -> PolicyResult:
        violations: List[PolicyViolation] = []
        if not has_evidence:
            violations.append(PolicyViolation(
                policy="EvidenceRequired",
                severity="high",
                message="No evidence provided",
                detail="Decision must include evidence basis",
                timestamp=datetime.now().isoformat(timespec="seconds"),
            ))
        elif evidence_quality < 0.5:
            violations.append(PolicyViolation(
                policy="EvidenceRequired",
                severity="medium",
                message="Evidence quality below threshold",
                detail="Quality: {}".format(round(evidence_quality, 2)),
                timestamp=datetime.now().isoformat(timespec="seconds"),
            ))
        score = evidence_quality if has_evidence else 0.0
        return PolicyResult(
            policy="EvidenceRequired",
            passed=has_evidence,
            score=score,
            detail="Evidence quality: {}".format(round(score, 2)),
            violations=tuple(violations),
        )

    def evaluate_trust_threshold(
        self, trust_level: float = 1.0, threshold: float = 0.5
    ) -> PolicyResult:
        violations: List[PolicyViolation] = []
        if trust_level < threshold:
            violations.append(PolicyViolation(
                policy="TrustThreshold",
                severity="high",
                message="Trust level below threshold",
                detail="{:.2f} < {:.2f}".format(trust_level, threshold),
                timestamp=datetime.now().isoformat(timespec="seconds"),
            ))
        return PolicyResult(
            policy="TrustThreshold",
            passed=trust_level >= threshold,
            score=trust_level,
            detail="Trust: {:.2f}, threshold: {:.2f}".format(trust_level, threshold),
            violations=tuple(violations),
        )

    def evaluate_provider_healthy(
        self, providers_healthy: int = 0, providers_total: int = 0
    ) -> PolicyResult:
        violations: List[PolicyViolation] = []
        passed = True
        score = 1.0
        if providers_total == 0:
            passed = False
            score = 0.0
            violations.append(PolicyViolation(
                policy="ProviderHealthy",
                severity="critical",
                message="No providers available",
                timestamp=datetime.now().isoformat(timespec="seconds"),
            ))
        elif providers_healthy == 0:
            passed = False
            score = 0.0
            violations.append(PolicyViolation(
                policy="ProviderHealthy",
                severity="critical",
                message="All providers unhealthy",
                detail="{}/{} healthy".format(providers_healthy, providers_total),
                timestamp=datetime.now().isoformat(timespec="seconds"),
            ))
        elif providers_healthy < providers_total:
            score = providers_healthy / max(providers_total, 1)
            violations.append(PolicyViolation(
                policy="ProviderHealthy",
                severity="medium",
                message="Some providers unhealthy",
                detail="{}/{} healthy".format(providers_healthy, providers_total),
                timestamp=datetime.now().isoformat(timespec="seconds"),
            ))
        return PolicyResult(
            policy="ProviderHealthy",
            passed=passed,
            score=score,
            detail="{}/{} providers healthy".format(providers_healthy, providers_total),
            violations=tuple(violations),
        )

    def evaluate_mission_allowed(
        self, missions_active: int = 0, missions_max: int = 10
    ) -> PolicyResult:
        violations: List[PolicyViolation] = []
        passed = missions_active <= missions_max
        score = max(0.0, 1.0 - (missions_active / max(missions_max, 1)))
        if not passed:
            violations.append(PolicyViolation(
                policy="MissionAllowed",
                severity="high",
                message="Mission capacity exceeded",
                detail="{}/{} active".format(missions_active, missions_max),
                timestamp=datetime.now().isoformat(timespec="seconds"),
            ))
        return PolicyResult(
            policy="MissionAllowed",
            passed=passed,
            score=score,
            detail="{}/{} missions active".format(missions_active, missions_max),
            violations=tuple(violations),
        )

    def evaluate_all(
        self,
        has_auto_execution: bool = False,
        has_approval: bool = True,
        pending_approvals: int = 0,
        has_conversation: bool = True,
        is_read_only: bool = True,
        has_evidence: bool = True,
        evidence_quality: float = 1.0,
        trust_level: float = 1.0,
        trust_threshold: float = 0.5,
        providers_healthy: int = 1,
        providers_total: int = 1,
        missions_active: int = 0,
        missions_max: int = 10,
    ) -> List[PolicyResult]:
        results = [
            self.evaluate_no_auto_execution(has_auto_execution),
            self.evaluate_approval_required(has_approval, pending_approvals),
            self.evaluate_conversation_only(has_conversation),
            self.evaluate_read_only(is_read_only),
            self.evaluate_evidence_required(has_evidence, evidence_quality),
            self.evaluate_trust_threshold(trust_level, trust_threshold),
            self.evaluate_provider_healthy(providers_healthy, providers_total),
            self.evaluate_mission_allowed(missions_active, missions_max),
        ]
        self._results = results
        return results

    @property
    def results(self) -> List[PolicyResult]:
        return list(self._results)

    @property
    def all_passed(self) -> bool:
        return all(r.passed for r in self._results)

    @property
    def violations(self) -> List[PolicyViolation]:
        vs: List[PolicyViolation] = []
        for r in self._results:
            vs.extend(r.violations)
        return vs
