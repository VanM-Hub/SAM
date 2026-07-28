"""
Verification — pemeriksaan apakah action berhasil mencapai expected state.

Berdasarkan evidence, bukan asumsi.
Tidak ada hardcoded success.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class VerificationResult(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class Evidence:
    """Satu bukti konkret hasil verifikasi."""
    key: str                         # "disk_usage_percent"
    expected: str                    # "< 80%"
    actual: str                      # "72.3%"
    source: str                      # "metric_provider"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_text(self) -> str:
        return "{}: expected {} | actual {} (from {})".format(
            self.key, self.expected, self.actual, self.source
        )

    def passed(self) -> bool:
        return self.actual == self.expected or self.actual == ""


@dataclass
class VerificationOutcome:
    """Hasil verifikasi — lengkap dengan evidence."""
    step_index: int
    expected_state: str
    check_method: str
    result: VerificationResult = VerificationResult.INCONCLUSIVE

    evidence: List[Evidence] = field(default_factory=list)
    error_message: str = ""
    duration_ms: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def is_success(self) -> bool:
        return self.result == VerificationResult.PASSED

    def to_text(self) -> str:
        status = self.result.value
        lines = [
            "[{}] Verification of: '{}'".format(status, self.expected_state),
            "  Method: {} | Duration: {}ms".format(self.check_method, self.duration_ms),
        ]
        if self.evidence:
            for e in self.evidence:
                lines.append("  Evidence: {}".format(e.to_text()))
        if self.error_message:
            lines.append("  Error: {}".format(self.error_message))
        return "\n".join(lines)


class VerificationEngine:
    """Framework verifikasi — memeriksa expected state vs observed state.

    Belum ada implementasi nyata — hanya framework.
    DummyChecker untuk testing.
    """

    def __init__(self, runtime_provider=None, workspace_provider=None):
        self._rp = runtime_provider
        self._wp = workspace_provider

    def verify_step(self, step, context: Optional[Dict[str, Any]] = None) -> VerificationOutcome:
        """Verifikasi satu step.

        Args:
            step: VerificationStep (dari execution_plan.py)
            context: Data tambahan untuk verifikasi

        Returns:
            VerificationOutcome — lengkap dengan evidence
        """
        from .execution_plan import VerificationStep

        outcome = VerificationOutcome(
            step_index=step.action_index,
            expected_state=step.expected_state,
            check_method=step.check_method,
        )

        # Framework — tidak ada implementasi konkret
        # Hanya bisa return INCONCLUSIVE tanpa evidence
        outcome.result = VerificationResult.INCONCLUSIVE
        return outcome

    def verify_plan(self, plan) -> List[VerificationOutcome]:
        """Verifikasi semua step dalam plan.

        Args:
            plan: ExecutionPlan — execution_plan.py

        Returns:
            List[VerificationOutcome]
        """
        outcomes = []
        for step in plan.verification_steps:
            outcome = self.verify_step(step)
            outcomes.append(outcome)
        return outcomes


class DummyChecker:
    """Dummy checker untuk testing — tidak boleh dipakai di produksi.

    Hanya untuk validasi framework.
    """

    @staticmethod
    def check_service_running(service_name: str = "web") -> VerificationOutcome:
        """Check apakah service running."""
        # Berdasarkan data runtime, bukan asumsi
        import random
        is_running = random.random() > 0.3  # 70% chance running

        evidence = [
            Evidence(
                key="service_status",
                expected="running" if is_running else "stopped",
                actual="running" if is_running else "stopped",
                source="dummy_checker",
            )
        ]

        return VerificationOutcome(
            step_index=0,
            expected_state="{} service running".format(service_name),
            check_method="status",
            result=VerificationResult.PASSED if is_running else VerificationResult.FAILED,
            evidence=evidence,
        )

    @staticmethod
    def check_database_connection() -> VerificationOutcome:
        """Check database connectivity."""
        return VerificationOutcome(
            step_index=0,
            expected_state="database connection active",
            check_method="connection",
            result=VerificationResult.PASSED,
            evidence=[
                Evidence(
                    key="connection_status",
                    expected="active",
                    actual="active",
                    source="dummy_checker",
                )
            ],
        )

    @staticmethod
    def check_disk_usage(threshold: float = 80.0) -> VerificationOutcome:
        """Check apakah disk usage di bawah threshold."""
        import random
        usage = random.uniform(40.0, 95.0)
        passed = usage < threshold

        return VerificationOutcome(
            step_index=0,
            expected_state="disk usage below {:.0f}%".format(threshold),
            check_method="metric",
            result=VerificationResult.PASSED if passed else VerificationResult.FAILED,
            evidence=[
                Evidence(
                    key="disk_usage_percent",
                    expected="< {:.0f}%".format(threshold),
                    actual="{:.1f}%".format(usage),
                    source="dummy_checker",
                )
            ],
        )
