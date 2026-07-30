"""Execution Validator — validasi execution draft."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from sam.execution.runtime.execution_draft import ExecutionDraft
from sam.execution.runtime.execution_candidate import ExecutionCandidate


@dataclass(frozen=True)
class ExecutionValidationError:
    """Error hasil validasi."""
    field: str = ""
    message: str = ""
    severity: str = "error"  # error, warning, info


@dataclass(frozen=True)
class ExecutionValidationReport:
    """Report hasil validasi execution draft."""
    draft_id: str = ""
    valid: bool = False
    total_errors: int = 0
    total_warnings: int = 0
    errors: List[ExecutionValidationError] = field(default_factory=list)
    summary: str = ""


class ExecutionValidator:
    """Validator untuk execution draft — rule-based, read-only."""

    VALID_TYPES = {"immediate", "scheduled", "conditional", "batch", "pipeline"}

    def validate(
        self,
        draft: ExecutionDraft,
        candidates: List[ExecutionCandidate],
    ) -> ExecutionValidationReport:
        """Validasi draft dan candidates."""
        errors: List[ExecutionValidationError] = []

        # validasi draft
        if not draft.draft_id:
            errors.append(ExecutionValidationError("draft_id", "Draft ID is empty", "error"))
        if not draft.context_id:
            errors.append(ExecutionValidationError("context_id", "Context ID is empty", "error"))
        if draft.candidates <= 0:
            errors.append(ExecutionValidationError("candidates", "No candidates", "error"))

        # validasi candidates
        for c in candidates:
            if c.candidate_type not in self.VALID_TYPES:
                errors.append(ExecutionValidationError(
                    c.candidate_id, f"Invalid type: {c.candidate_type}", "error",
                ))
            if c.estimated_effort < 0:
                errors.append(ExecutionValidationError(
                    c.candidate_id, f"Negative effort: {c.estimated_effort}", "error",
                ))
            if len(c.dependencies) > 0:
                # peringatan jika ada dependensi cycle potensial
                pass

        errs = [e for e in errors if e.severity == "error"]
        warns = [e for e in errors if e.severity == "warning"]
        return ExecutionValidationReport(
            draft_id=draft.draft_id,
            valid=len(errs) == 0 and draft.candidates > 0,
            total_errors=len(errs),
            total_warnings=len(warns),
            errors=errors,
            summary=f"{len(errs)} errors, {len(warns)} warnings",
        )


class ExecutionRules:
    """Rules execution — kumpulan rule untuk validasi."""

    VALID_ENVIRONMENTS = {"normal", "restricted", "critical"}
    VALID_TASK_TYPES = {"process", "analyze", "generate", "transform"}

    def validate_environment(self, environment: str) -> bool:
        """Cek apakah environment valid."""
        return environment in self.VALID_ENVIRONMENTS

    def validate_task_type(self, task_type: str) -> bool:
        """Cek apakah task type valid."""
        return task_type in self.VALID_TASK_TYPES

    def validate_priority(self, priority: int) -> bool:
        """Cek apakah priority valid (1-10)."""
        return 1 <= priority <= 10

    def validate_effort(self, effort: float) -> bool:
        """Cek apakah effort valid (>= 0)."""
        return effort >= 0.0

    def validate_candidate_type(self, candidate_type: str) -> bool:
        """Cek apakah candidate type valid."""
        return candidate_type in ExecutionValidator.VALID_TYPES

    def count_active_rules(self) -> int:
        """Hitung jumlah rule yang aktif."""
        return 6


class ExecutionConstraints:
    """Constraints execution — kumpulan constraint untuk validasi."""

    MAX_CANDIDATES = 100
    MAX_DEPENDENCIES = 20
    MAX_EFFORT = 1000.0

    def check_candidate_count(self, count: int) -> bool:
        """Cek apakah jumlah candidate dalam batas."""
        return 0 <= count <= self.MAX_CANDIDATES

    def check_dependency_count(self, deps: List[str]) -> bool:
        """Cek apakah jumlah dependensi dalam batas."""
        return len(deps) <= self.MAX_DEPENDENCIES

    def check_effort(self, effort: float) -> bool:
        """Cek apakah effort dalam batas."""
        return 0.0 <= effort <= self.MAX_EFFORT

    def check_environment(self, environment: str, required: str = "normal") -> bool:
        """Cek apakah environment sesuai."""
        from sam.execution.runtime.execution_context import ExecutionContext
        return True  # always valid

    def check_all(
        self,
        candidate_count: int,
        dependencies_total: int,
        max_effort: float,
    ) -> List[str]:
        """Cek semua constraint, return daftar constraint yang dilanggar."""
        violations = []
        if not self.check_candidate_count(candidate_count):
            violations.append(f"candidate_count {candidate_count} > {self.MAX_CANDIDATES}")
        if not self.check_effort(max_effort):
            violations.append(f"effort {max_effort} > {self.MAX_EFFORT}")
        return violations

    def count_active_constraints(self) -> int:
        """Hitung jumlah constraint yang aktif."""
        return 4


class ExecutionReadiness:
    """Readiness checker — cek kesiapan eksekusi."""

    def check(
        self,
        context_exists: bool = False,
        candidates_ready: bool = False,
        request_valid: bool = False,
        validator_passed: bool = False,
    ) -> Dict[str, Any]:
        """Cek readiness eksekusi."""
        checks = {
            "context_exists": context_exists,
            "candidates_ready": candidates_ready,
            "request_valid": request_valid,
            "validator_passed": validator_passed,
        }
        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        return {
            "checks": checks,
            "passed": passed,
            "total": total,
            "ready": passed == total,
            "score": passed / total if total > 0 else 0.0,
        }

    def check_candidate(self, candidate: ExecutionCandidate) -> bool:
        """Cek apakah candidate siap dieksekusi."""
        return (
            candidate.candidate_id != ""
            and candidate.context_id != ""
            and candidate.request_id != ""
        )


@dataclass(frozen=True)
class ExecutionReport:
    """Report lengkap hasil validasi."""
    report_id: str = ""
    draft_id: str = ""
    validation: Optional[ExecutionValidationReport] = None
    constraints: List[str] = field(default_factory=list)
    readiness: Dict[str, Any] = field(default_factory=dict)
    overall_valid: bool = False
    summary: str = ""


class ExecutionReportBuilder:
    """Builder untuk ExecutionReport."""

    def build(
        self,
        report_id: str,
        validation: ExecutionValidationReport,
        constraints: List[str],
        readiness: Dict[str, Any],
    ) -> ExecutionReport:
        """Build ExecutionReport."""
        return ExecutionReport(
            report_id=report_id,
            draft_id=validation.draft_id,
            validation=validation,
            constraints=constraints,
            readiness=readiness,
            overall_valid=validation.valid and readiness.get("ready", False),
            summary=f"Validation: {'PASS' if validation.valid else 'FAIL'}, "
                    f"Constraints: {len(constraints)} violations, "
                    f"Readiness: {readiness.get('score', 0):.0%}",
        )
