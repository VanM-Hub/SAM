"""
OP-347 — Guardian Dashboard V3

8 DTO immutable cards untuk governance monitoring.
Frozen dataclass. Synchronous only.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ── DTO Cards ──

@dataclass(frozen=True)
class GovernanceCard:
    """Status governance pipeline."""
    governance_id: str
    overall_status: str
    overall_score: float
    approved: bool
    stage_count: int
    failed_stages: Tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "governance_id": self.governance_id,
            "overall_status": self.overall_status,
            "overall_score": self.overall_score,
            "approved": self.approved,
            "stage_count": self.stage_count,
            "failed_stages": list(self.failed_stages),
            "summary": self.summary,
        }


@dataclass(frozen=True)
class RiskCard:
    """Ringkasan risk assessment."""
    overall_level: str
    overall_score: float
    is_safe: bool
    top_risks: Tuple[str, ...] = field(default_factory=tuple)
    mitigations: Tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_level": self.overall_level,
            "overall_score": self.overall_score,
            "is_safe": self.is_safe,
            "top_risks": list(self.top_risks),
            "mitigations": list(self.mitigations),
            "summary": self.summary,
        }


@dataclass(frozen=True)
class ReadinessCard:
    """Status readiness eksekusi."""
    overall_level: str
    overall_score: float
    ready: bool
    blocking_dimensions: Tuple[str, ...] = field(default_factory=tuple)
    recommendations: Tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_level": self.overall_level,
            "overall_score": self.overall_score,
            "ready": self.ready,
            "blocking_dimensions": list(self.blocking_dimensions),
            "recommendations": list(self.recommendations),
            "summary": self.summary,
        }


@dataclass(frozen=True)
class PolicyCard:
    """Status policy compliance."""
    policy_passed: bool
    policy_violations: int
    policy_score: float
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_passed": self.policy_passed,
            "policy_violations": self.policy_violations,
            "policy_score": self.policy_score,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class GuardianSummaryCard:
    """Ringkasan guardian health."""
    guardian_healthy: bool
    guardian_score: float
    system_health: str = "unknown"
    coordination_engines: int = 0
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "guardian_healthy": self.guardian_healthy,
            "guardian_score": self.guardian_score,
            "system_health": self.system_health,
            "coordination_engines": self.coordination_engines,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class BlockedMissionsCard:
    """Misi yang diblokir."""
    blocked_count: int
    blocked_missions: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "blocked_count": self.blocked_count,
            "blocked_missions": list(self.blocked_missions),
            "summary": self.summary,
        }


@dataclass(frozen=True)
class PendingApprovalCard:
    """Approval yang masih pending."""
    pending_count: int
    approval_required: int = 0
    approval_granted: int = 0
    approvals: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pending_count": self.pending_count,
            "approval_required": self.approval_required,
            "approval_granted": self.approval_granted,
            "approvals": list(self.approvals),
            "summary": self.summary,
        }


@dataclass(frozen=True)
class OperationalStatusCard:
    """Status operasional keseluruhan."""
    governance_status: str = "unknown"
    readiness_level: str = "unknown"
    risk_level: str = "none"
    overall_score: float = 0.0
    system_ready: bool = False
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "governance_status": self.governance_status,
            "readiness_level": self.readiness_level,
            "risk_level": self.risk_level,
            "overall_score": self.overall_score,
            "system_ready": self.system_ready,
            "summary": self.summary,
        }


# ── Dashboard Service ──

class GuardianDashboardV3Service:
    """Dashboard V3 — governance monitoring cards. Read-only. Synchronous."""

    def __init__(
        self,
        governance: Any = None,
        readiness: Any = None,
        risk_assessment: Any = None,
        explanation: Any = None,
    ):
        self._governance = governance
        self._readiness = readiness
        self._risk_assessment = risk_assessment
        self._explanation = explanation

    def build_governance_card(self, **kwargs: Any) -> GovernanceCard:
        """Bangun GovernanceCard dari governance engine."""
        if self._governance:
            try:
                r = self._governance.evaluate(**kwargs)
                return GovernanceCard(
                    governance_id=(r.governance_id if hasattr(r, "governance_id") else "gov-0"),
                    overall_status=r.overall_status.value,
                    overall_score=r.overall_score,
                    approved=r.approved,
                    stage_count=r.stage_count,
                    failed_stages=tuple(r.failed_stages),
                    summary=r.summary,
                )
            except Exception:
                pass
        return GovernanceCard(
            governance_id="gov-0", overall_status="unknown",
            overall_score=0.0, approved=False, stage_count=0,
            summary="Engine unavailable",
        )

    def build_risk_card(self, **kwargs: Any) -> RiskCard:
        """Bangun RiskCard dari risk assessment."""
        if self._risk_assessment:
            try:
                r = self._risk_assessment.assess(**kwargs)
                return RiskCard(
                    overall_level=r.overall_level.value,
                    overall_score=r.overall_score,
                    is_safe=r.is_safe,
                    top_risks=tuple(r.top_risks),
                    mitigations=tuple(r.mitigations),
                    summary=r.summary,
                )
            except Exception:
                pass
        return RiskCard(overall_level="unknown", overall_score=0.0,
                        is_safe=False, summary="Engine unavailable")

    def build_readiness_card(self, **kwargs: Any) -> ReadinessCard:
        """Bangun ReadinessCard dari readiness evaluator."""
        if self._readiness:
            try:
                r = self._readiness.evaluate(**kwargs)
                return ReadinessCard(
                    overall_level=r.overall_level.value,
                    overall_score=r.overall_score,
                    ready=r.ready,
                    blocking_dimensions=tuple(r.blocking_dimensions),
                    recommendations=tuple(r.recommendations),
                    summary=r.summary,
                )
            except Exception:
                pass
        return ReadinessCard(overall_level="unknown", overall_score=0.0,
                             ready=False, summary="Engine unavailable")

    def build_policy_card(self, **kwargs: Any) -> PolicyCard:
        """Bangun PolicyCard dari governance + readiness."""
        violations = 0
        passed = True
        score = 1.0

        if self._readiness:
            try:
                r = self._readiness.evaluate(**kwargs)
                for c in r.checks:
                    if c.dimension == "policy":
                        passed = c.passed
                        score = c.score
                        violations = 0 if passed else 1
            except Exception:
                pass

        return PolicyCard(
            policy_passed=passed,
            policy_violations=violations,
            policy_score=score,
            summary="All policies passed" if passed else f"{violations} policy violation(s)",
        )

    def build_guardian_summary_card(self, **kwargs: Any) -> GuardianSummaryCard:
        """Bangun GuardianSummaryCard."""
        engine_count = sum(1 for e in [
            self._governance, self._readiness,
            self._risk_assessment, self._explanation,
        ] if e is not None)
        score = 1.0

        if self._governance:
            try:
                r = self._governance.evaluate(**kwargs)
                score = r.overall_score
            except Exception:
                pass

        return GuardianSummaryCard(
            guardian_healthy=engine_count >= 3,
            guardian_score=score,
            system_health="healthy" if score >= 0.7 else (
                "degraded" if score >= 0.4 else "critical"),
            coordination_engines=engine_count,
            summary=f"{engine_count} engine(s) active, score: {score:.2f}",
        )

    def build_blocked_missions_card(self, **kwargs: Any) -> BlockedMissionsCard:
        """Bangun BlockedMissionsCard."""
        blocked = []
        if self._readiness:
            try:
                r = self._readiness.evaluate(**kwargs)
                for c in r.checks:
                    if not c.passed:
                        blocked.append({
                            "dimension": c.dimension,
                            "level": c.level.value,
                            "detail": c.detail,
                            "recommendation": c.recommendation,
                        })
            except Exception:
                pass
        return BlockedMissionsCard(
            blocked_count=len(blocked),
            blocked_missions=tuple(blocked),
            summary=f"{len(blocked)} blocking dimension(s)",
        )

    def build_pending_approval_card(self, **kwargs: Any) -> PendingApprovalCard:
        """Bangun PendingApprovalCard."""
        required = kwargs.get("approval_required", 0)
        granted = kwargs.get("approval_granted", 0)
        pending = max(0, required - granted)
        return PendingApprovalCard(
            pending_count=pending,
            approval_required=required,
            approval_granted=granted,
            summary=f"{granted}/{required} approvals granted"
                    if required > 0 else "No approvals required",
        )

    def build_operational_status_card(self, **kwargs: Any) -> OperationalStatusCard:
        """Bangun OperationalStatusCard — ringkasan keseluruhan."""
        gov_status = "unknown"
        ready_level = "unknown"
        risk_level = "none"
        scores: list = []

        if self._governance:
            try:
                r = self._governance.evaluate(**kwargs)
                gov_status = r.overall_status.value
                scores.append(r.overall_score)
            except Exception:
                pass

        if self._readiness:
            try:
                r = self._readiness.evaluate(**kwargs)
                ready_level = r.overall_level.value
                scores.append(r.overall_score)
            except Exception:
                pass

        if self._risk_assessment:
            try:
                r = self._risk_assessment.assess(**kwargs)
                risk_level = r.overall_level.value
            except Exception:
                pass

        overall = sum(scores) / len(scores) if scores else 0.0
        system_ready = (gov_status == "approved" and ready_level == "ready"
                        and risk_level in ("none", "low"))

        return OperationalStatusCard(
            governance_status=gov_status,
            readiness_level=ready_level,
            risk_level=risk_level,
            overall_score=overall,
            system_ready=system_ready,
            summary="System ready" if system_ready
                    else f"Gov: {gov_status}, Readiness: {ready_level}, Risk: {risk_level}",
        )
