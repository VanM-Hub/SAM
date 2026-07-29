"""
OP-342 — Execution Readiness Evaluator

Evaluasi readiness operasi sebelum dieksekusi.
7 dimensi penilaian → output READY/BLOCKED/WAITING/REVIEW/DENIED.
Immutable DTO. Synchronous only.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum


class ReadinessLevel(str, Enum):
    """Tingkat readiness operasi."""
    READY = "ready"
    WAITING = "waiting"
    REVIEW = "review"
    BLOCKED = "blocked"
    DENIED = "denied"


@dataclass(frozen=True)
class ReadinessCheck:
    """Hasil pengecekan satu dimensi readiness."""
    dimension: str
    passed: bool
    level: ReadinessLevel
    score: float = 0.0
    detail: str = ""
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "passed": self.passed,
            "level": self.level.value,
            "score": self.score,
            "detail": self.detail,
            "recommendation": self.recommendation,
        }


@dataclass(frozen=True)
class ExecutionReadiness:
    """Hasil evaluasi readiness lengkap."""
    readiness_id: str
    overall_level: ReadinessLevel
    checks: Tuple[ReadinessCheck, ...] = field(default_factory=tuple)
    overall_score: float = 0.0
    summary: str = ""
    blocking_dimensions: Tuple[str, ...] = field(default_factory=tuple)
    recommendations: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def ready(self) -> bool:
        return self.overall_level == ReadinessLevel.READY

    @property
    def check_count(self) -> int:
        return len(self.checks)

    @property
    def passed_checks(self) -> List[ReadinessCheck]:
        return [c for c in self.checks if c.passed]

    @property
    def failed_checks(self) -> List[ReadinessCheck]:
        return [c for c in self.checks if not c.passed]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "readiness_id": self.readiness_id,
            "overall_level": self.overall_level.value,
            "overall_score": self.overall_score,
            "ready": self.ready,
            "check_count": self.check_count,
            "blocking_dimensions": list(self.blocking_dimensions),
            "recommendations": list(self.recommendations),
            "summary": self.summary,
        }


# ── Dimensi ──

DIMENSIONS = [
    "approval", "policy", "confidence", "evidence",
    "guardian_health", "conflict", "dependency",
]


class ExecutionReadinessEvaluator:
    """Evaluator readiness 7 dimensi.

    7 dimensi:
      1. approval_lengkap
      2. policy_lolos
      3. confidence_cukup
      4. evidence_cukup
      5. guardian_healthy
      6. conflict_tidak_ada
      7. dependency_selesai

    Hanya evaluasi. Synchronous.
    """

    def __init__(self) -> None:
        self._evaluation_count = 0

    @property
    def evaluation_count(self) -> int:
        return self._evaluation_count

    def evaluate(
        self,
        approval_complete: bool = True,
        approval_rate: float = 1.0,
        policy_passed: bool = True,
        policy_violations: int = 0,
        confidence_score: float = 1.0,
        confidence_threshold: float = 0.7,
        evidence_count: int = 1,
        evidence_minimum: int = 1,
        guardian_healthy: bool = True,
        guardian_score: float = 1.0,
        conflict_detected: bool = False,
        conflict_count: int = 0,
        dependency_complete: bool = True,
        dependency_pending: int = 0,
        readiness_id: Optional[str] = None,
        **kwargs: Any,
    ) -> ExecutionReadiness:
        """Evaluasi 7 dimensi readiness.

        Args:
            approval_complete: Semua approval lengkap.
            approval_rate: Persentase approval granted (0.0-1.0).
            policy_passed: Semua policy lolos.
            policy_violations: Jumlah pelanggaran policy.
            confidence_score: Confidence score (0.0-1.0).
            confidence_threshold: Minimum confidence threshold.
            evidence_count: Jumlah evidence tersedia.
            evidence_minimum: Minimum evidence dibutuhkan.
            guardian_healthy: Guardian dalam kondisi sehat.
            guardian_score: Guardian health score (0.0-1.0).
            conflict_detected: Apakah conflict terdeteksi.
            conflict_count: Jumlah conflict.
            dependency_complete: Semua dependency selesai.
            dependency_pending: Jumlah dependency pending.

        Returns:
            ExecutionReadiness immutable.
        """
        import uuid
        rid = readiness_id or f"er-{uuid.uuid4().hex[:8]}"
        self._evaluation_count += 1
        checks: List[ReadinessCheck] = []
        all_recommendations: List[str] = []
        blocking: List[str] = []

        # 1. Approval
        approval_ok = approval_complete and approval_rate >= 1.0
        if not approval_ok:
            if not approval_complete:
                blocking.append("approval")
                all_recommendations.append("Lengkapi semua approval sebelum eksekusi")
            elif approval_rate < 1.0:
                all_recommendations.append(f"Approval rate {approval_rate:.0%} — target 100%")
        checks.append(ReadinessCheck(
            dimension="approval", passed=approval_ok,
            level=ReadinessLevel.READY if approval_ok else ReadinessLevel.WAITING,
            score=approval_rate,
            detail="Approval complete" if approval_ok else "Approval incomplete",
            recommendation="All approvals granted" if approval_ok else "Pending approvals",
        ))

        # 2. Policy
        policy_ok = policy_passed and policy_violations == 0
        if not policy_ok:
            blocking.append("policy")
            all_recommendations.append(f"Perbaiki {policy_violations} policy violation(s)")
        checks.append(ReadinessCheck(
            dimension="policy", passed=policy_ok,
            level=ReadinessLevel.READY if policy_ok else ReadinessLevel.DENIED,
            score=1.0 if policy_ok else max(0.0, 1.0 - policy_violations * 0.3),
            detail="All policies passed" if policy_ok else f"{policy_violations} violations",
            recommendation="Policy compliance confirmed" if policy_ok else "Policy violations must be resolved",
        ))

        # 3. Confidence
        confidence_ok = confidence_score >= confidence_threshold
        if not confidence_ok:
            blocking.append("confidence")
            all_recommendations.append(f"Confidence {confidence_score:.2f} < threshold {confidence_threshold}")
        checks.append(ReadinessCheck(
            dimension="confidence", passed=confidence_ok,
            level=ReadinessLevel.REVIEW if not confidence_ok else ReadinessLevel.READY,
            score=confidence_score,
            detail=f"Confidence {confidence_score:.2f} ≥ {confidence_threshold}" if confidence_ok
                   else f"Confidence {confidence_score:.2f} < {confidence_threshold}",
            recommendation="Confidence sufficient" if confidence_ok else "Improve confidence",
        ))

        # 4. Evidence
        evidence_ok = evidence_count >= evidence_minimum
        if not evidence_ok:
            blocking.append("evidence")
            all_recommendations.append(f"Tambahkan {evidence_minimum - evidence_count} evidence lagi")
        checks.append(ReadinessCheck(
            dimension="evidence", passed=evidence_ok,
            level=ReadinessLevel.WAITING if not evidence_ok else ReadinessLevel.READY,
            score=min(1.0, evidence_count / max(1, evidence_minimum)),
            detail=f"{evidence_count}/{evidence_minimum} evidence" if not evidence_ok
                   else f"Evidence sufficient ({evidence_count})",
            recommendation="Evidence adequate" if evidence_ok else "Gather more evidence",
        ))

        # 5. Guardian Health
        health_ok = guardian_healthy and guardian_score >= 0.5
        if not health_ok:
            blocking.append("guardian_health")
            all_recommendations.append("Guardian health perlu diperbaiki sebelum eksekusi")
        checks.append(ReadinessCheck(
            dimension="guardian_health", passed=health_ok,
            level=ReadinessLevel.READY if health_ok else ReadinessLevel.BLOCKED,
            score=guardian_score,
            detail=f"Guardian score: {guardian_score:.2f}" if guardian_healthy
                   else "Guardian unhealthy",
            recommendation="Guardian healthy" if health_ok else "Resolve guardian health issues",
        ))

        # 6. Conflict
        conflict_ok = not conflict_detected and conflict_count == 0
        if not conflict_ok:
            blocking.append("conflict")
            all_recommendations.append(f"Resolve {conflict_count} conflict(s)")
        checks.append(ReadinessCheck(
            dimension="conflict", passed=conflict_ok,
            level=ReadinessLevel.READY if conflict_ok else ReadinessLevel.BLOCKED,
            score=1.0 if conflict_ok else max(0.0, 1.0 - conflict_count * 0.3),
            detail="No conflicts" if conflict_ok else f"{conflict_count} conflict(s)",
            recommendation="No conflicts detected" if conflict_ok else "Resolve conflicts",
        ))

        # 7. Dependency
        dep_ok = dependency_complete and dependency_pending == 0
        if not dep_ok:
            blocking.append("dependency")
            all_recommendations.append(f"Selesaikan {dependency_pending} dependency pending")
        checks.append(ReadinessCheck(
            dimension="dependency", passed=dep_ok,
            level=ReadinessLevel.READY if dep_ok else ReadinessLevel.WAITING,
            score=1.0 if dep_ok else max(0.0, 1.0 - dependency_pending * 0.2),
            detail="All dependencies complete" if dep_ok
                   else f"{dependency_pending} pending",
            recommendation="Dependencies satisfied" if dep_ok else "Complete pending dependencies",
        ))

        # ── Overall ──
        failed = [c for c in checks if not c.passed]
        overall_score = sum(c.score for c in checks) / len(checks) if checks else 0.0
        denied_dims = {"policy"}
        blocked_dims = {"guardian_health", "conflict"}
        waiting_dims = {"approval", "evidence", "dependency"}
        review_dims = {"confidence"}

        if any(c.dimension in denied_dims for c in failed):
            overall_level = ReadinessLevel.DENIED
        elif any(c.dimension in blocked_dims for c in failed):
            overall_level = ReadinessLevel.BLOCKED
        elif any(c.dimension in waiting_dims for c in failed):
            overall_level = ReadinessLevel.WAITING
        elif any(c.dimension in review_dims for c in failed):
            overall_level = ReadinessLevel.REVIEW
        else:
            overall_level = ReadinessLevel.READY

        # Summary
        if overall_level == ReadinessLevel.READY:
            summary = "Operasi siap dijalankan"
        elif overall_level == ReadinessLevel.BLOCKED:
            summary = f"Operasi diblokir: {', '.join(blocking)}"
        elif overall_level == ReadinessLevel.WAITING:
            summary = f"Operasi menunggu: {', '.join(blocking)}"
        elif overall_level == ReadinessLevel.DENIED:
            summary = "Operasi ditolak: policy violation"
        else:
            summary = f"Operasi perlu review: {', '.join(blocking)}"

        return ExecutionReadiness(
            readiness_id=rid,
            overall_level=overall_level,
            checks=tuple(checks),
            overall_score=overall_score,
            summary=summary,
            blocking_dimensions=tuple(blocking),
            recommendations=tuple(all_recommendations),
        )
