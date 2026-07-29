"""
OP-375 — Startup Report

DTO untuk pelaporan startup:

  StartupReport     — laporan lengkap
  StageResult       — status per stage
  StartupIssue      — peringatan/error
  StartupSummary    — ringkasan
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class IssueSeverity(Enum):
    """Severity level for startup issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class StageResult:
    """Result of a single pipeline stage."""

    stage: str
    success: bool
    duration_ms: float = 0.0
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "success": self.success,
            "duration_ms": self.duration_ms,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class StartupIssue:
    """An issue encountered during startup."""

    stage: str
    severity: IssueSeverity
    message: str
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "severity": self.severity.value,
            "message": self.message,
            "recommendation": self.recommendation,
        }


@dataclass(frozen=True)
class StartupSummary:
    """Summary of the startup process."""

    total_stages: int = 0
    passed: int = 0
    failed: int = 0
    total_duration_ms: float = 0.0
    success: bool = False
    issues_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_stages": self.total_stages,
            "passed": self.passed,
            "failed": self.failed,
            "total_duration_ms": self.total_duration_ms,
            "success": self.success,
            "issues_count": self.issues_count,
        }


@dataclass(frozen=True)
class StartupReport:
    """Full startup report."""

    stages: List[StageResult] = field(default_factory=list)
    total_duration_ms: float = 0.0
    success: bool = True
    issues: List[StartupIssue] = field(default_factory=list)
    summary: Optional[StartupIssue] = None

    @property
    def summary_dto(self) -> StartupSummary:
        passed = sum(1 for s in self.stages if s.success)
        failed = sum(1 for s in self.stages if not s.success)
        return StartupSummary(
            total_stages=len(self.stages),
            passed=passed,
            failed=failed,
            total_duration_ms=self.total_duration_ms,
            success=self.success,
            issues_count=len(self.issues),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "total_duration_ms": self.total_duration_ms,
            "stages": [s.to_dict() for s in self.stages],
            "issues": [i.to_dict() for i in self.issues],
            "summary": self.summary.to_dict() if self.summary else None,
            "summary_dto": self.summary_dto.to_dict(),
        }
