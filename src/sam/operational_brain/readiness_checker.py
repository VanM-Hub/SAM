"""Readiness Checker — memeriksa apakah SAM siap menerima pekerjaan.

Readiness checks bersifat read-only dan tidak melakukan eksekusi.
Semua check memberikan hasil berupa skor dan alasan.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Tuple

from sam.operational_brain.operational_context import OperationalContext


class ReadinessStatus(Enum):
    """Status kesiapan."""
    READY = auto()
    DEGRADED = auto()
    BLOCKED = auto()
    MAINTENANCE = auto()
    UNKNOWN = auto()


@dataclass(frozen=True)
class ReadinessCheck:
    """Hasil satu check kesiapan — immutable."""
    check_id: str
    name: str
    passed: bool
    score: float                   # 0.0–1.0
    status: ReadinessStatus
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReadinessReport:
    """Report kesiapan keseluruhan — immutable."""
    overall_score: float           # 0.0–1.0
    overall_status: ReadinessStatus
    checks: Tuple[ReadinessCheck, ...] = field(default_factory=tuple)
    passed: int = 0
    total: int = 0
    summary: str = ""


class ReadinessChecker:
    """Checker for readiness. 8 kategori check."""

    def __init__(self):
        self._checks: List[ReadinessCheck] = []
        self._categories = [
            "resources", "decisions", "approvals", "constraints",
            "missions", "workload", "stability", "readiness",
        ]

    @property
    def categories(self) -> List[str]:
        return list(self._categories)

    def check_all(self, ctx: OperationalContext) -> ReadinessReport:
        """Run all 8 readiness checks."""
        checks = [
            self.check_resources(ctx),
            self.check_decisions(ctx),
            self.check_approvals(ctx),
            self.check_constraints(ctx),
            self.check_missions(ctx),
            self.check_workload(ctx),
            self.check_stability(ctx),
            self.check_readiness(ctx),
        ]
        self._checks = checks
        total = len(checks)
        passed = sum(1 for c in checks if c.passed)
        scores = [c.score for c in checks]
        overall_score = round(sum(scores) / total, 4) if total else 0.0

        if passed == total:
            overall_status = ReadinessStatus.READY
            summary = "All checks passed"
        elif passed >= total / 2:
            overall_status = ReadinessStatus.DEGRADED
            summary = f"{passed}/{total} checks passed — degraded"
        elif overall_score == 0:
            overall_status = ReadinessStatus.UNKNOWN
            summary = "No checks passed"
        else:
            overall_status = ReadinessStatus.BLOCKED
            summary = f"{passed}/{total} checks passed — blocked"

        return ReadinessReport(
            overall_score=overall_score,
            overall_status=overall_status,
            checks=tuple(checks),
            passed=passed,
            total=total,
            summary=summary,
        )

    def check_resources(self, ctx: OperationalContext) -> ReadinessCheck:
        if ctx.available_resources > 0:
            return ReadinessCheck("R01", "Available Resources", True, 1.0, ReadinessStatus.READY, f"{ctx.available_resources} resources available")
        return ReadinessCheck("R01", "Available Resources", False, 0.0, ReadinessStatus.BLOCKED, "No resources available")

    def check_decisions(self, ctx: OperationalContext) -> ReadinessCheck:
        if ctx.pending_decisions == 0:
            return ReadinessCheck("R02", "Pending Decisions", True, 1.0, ReadinessStatus.READY, "No pending decisions")
        if ctx.pending_decisions <= 3:
            return ReadinessCheck("R02", "Pending Decisions", True, 0.7, ReadinessStatus.DEGRADED, f"{ctx.pending_decisions} pending decisions")
        return ReadinessCheck("R02", "Pending Decisions", False, 0.3, ReadinessStatus.DEGRADED, f"{ctx.pending_decisions} pending decisions (high)")

    def check_approvals(self, ctx: OperationalContext) -> ReadinessCheck:
        if ctx.pending_approvals == 0:
            return ReadinessCheck("R03", "Pending Approvals", True, 1.0, ReadinessStatus.READY, "No pending approvals")
        if ctx.pending_approvals <= 2:
            return ReadinessCheck("R03", "Pending Approvals", True, 0.6, ReadinessStatus.DEGRADED, f"{ctx.pending_approvals} pending approvals")
        return ReadinessCheck("R03", "Pending Approvals", False, 0.2, ReadinessStatus.BLOCKED, f"{ctx.pending_approvals} pending approvals (high)")

    def check_constraints(self, ctx: OperationalContext) -> ReadinessCheck:
        n = len(ctx.active_constraints)
        if n == 0:
            return ReadinessCheck("R04", "Active Constraints", True, 1.0, ReadinessStatus.READY, "No active constraints")
        if n <= 2:
            return ReadinessCheck("R04", "Active Constraints", True, 0.6, ReadinessStatus.DEGRADED, f"{n} active constraints")
        return ReadinessCheck("R04", "Active Constraints", False, 0.2, ReadinessStatus.BLOCKED, f"{n} active constraints (high)")

    def check_missions(self, ctx: OperationalContext) -> ReadinessCheck:
        n = len(ctx.active_missions)
        if n == 0:
            return ReadinessCheck("R05", "Active Missions", True, 0.8, ReadinessStatus.DEGRADED, "No active missions — idle")
        if n <= 3:
            return ReadinessCheck("R05", "Active Missions", True, 1.0, ReadinessStatus.READY, f"{n} active missions")
        return ReadinessCheck("R05", "Active Missions", True, 0.7, ReadinessStatus.DEGRADED, f"{n} active missions (many)")

    def check_workload(self, ctx: OperationalContext) -> ReadinessCheck:
        pending = ctx.pending_decisions + ctx.pending_approvals
        if pending == 0:
            return ReadinessCheck("R06", "Workload", True, 1.0, ReadinessStatus.READY, "No pending work")
        if pending <= 3:
            return ReadinessCheck("R06", "Workload", True, 0.7, ReadinessStatus.DEGRADED, f"{pending} items pending")
        return ReadinessCheck("R06", "Workload", False, 0.3, ReadinessStatus.BLOCKED, f"{pending} items pending (overloaded)")

    def check_stability(self, ctx: OperationalContext) -> ReadinessCheck:
        env = ctx.environment
        if env in ("normal", "idle"):
            return ReadinessCheck("R07", "Environment", True, 1.0, ReadinessStatus.READY, f"Environment is {env}")
        if env == "busy":
            return ReadinessCheck("R07", "Environment", True, 0.6, ReadinessStatus.DEGRADED, "Environment is busy")
        return ReadinessCheck("R07", "Environment", False, 0.1, ReadinessStatus.BLOCKED, f"Environment is {env}")

    def check_readiness(self, ctx: OperationalContext) -> ReadinessCheck:
        # composite readiness based on all factors
        if ctx.environment in ("normal", "idle") and ctx.available_resources > 0 and ctx.pending_decisions == 0:
            return ReadinessCheck("R08", "Overall Readiness", True, 1.0, ReadinessStatus.READY, "System ready")
        if ctx.available_resources > 0:
            return ReadinessCheck("R08", "Overall Readiness", True, 0.5, ReadinessStatus.DEGRADED, "System degraded but operable")
        return ReadinessCheck("R08", "Overall Readiness", False, 0.0, ReadinessStatus.BLOCKED, "System blocked — no resources")

    def report_dict(self, ctx: OperationalContext) -> Dict[str, Any]:
        report = self.check_all(ctx)
        return {
            "overall_score": round(report.overall_score, 4),
            "overall_status": report.overall_status.name,
            "summary": report.summary,
            "passed": report.passed,
            "total": report.total,
            "checks": [
                {
                    "check_id": c.check_id,
                    "name": c.name,
                    "passed": c.passed,
                    "score": c.score,
                    "status": c.status.name,
                    "message": c.message,
                }
                for c in report.checks
            ],
        }
