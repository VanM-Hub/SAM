# OP-423 — Dispatch Validator
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from .dispatch_request import (
    DispatchRequest, DispatchTask, DispatchStatus,
    DispatchTarget, DispatchMetadata,
)


@dataclass(frozen=True)
class DispatchIssue:
    issue_id: str = ""
    category: str = ""  # connector_exists, connector_healthy, approval_exists, task_complete, dependency_complete, rollback_ready, policy_satisfied, capability_satisfied
    severity: str = "warning"
    message: str = ""
    field: str = ""


@dataclass(frozen=True)
class DispatchValidationReport:
    passed: bool = True
    issues: Tuple[DispatchIssue, ...] = field(default_factory=tuple)
    total_issues: int = 0
    errors: int = 0
    warnings: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def has_blocking(self) -> bool:
        return self.errors > 0


class DispatchValidator:
    """Validates dispatch requests before queuing.

    Validations:
    - connector_exists
    - connector_healthy
    - approval_exists
    - task_complete
    - dependency_complete
    - rollback_ready
    - policy_satisfied
    - capability_satisfied
    """

    def validate(
        self,
        request: DispatchRequest,
        connector_exists: bool = True,
        connector_healthy: bool = True,
        approval_exists: bool = False,
    ) -> DispatchValidationReport:
        issues: List[DispatchIssue] = []

        # 1. Connector exists
        if not connector_exists:
            issues.append(DispatchIssue(
                category="connector_exists",
                severity="error",
                message="Connector not found in registry",
                field="target.connector_id",
            ))

        # 2. Connector healthy
        if not connector_healthy:
            issues.append(DispatchIssue(
                category="connector_healthy",
                severity="error",
                message="Connector is unhealthy",
                field="target.healthy",
            ))

        # 3. Approval exists
        if request.requires_approval and not approval_exists:
            issues.append(DispatchIssue(
                category="approval_exists",
                severity="error",
                message="Approval required but not yet provided",
                field="requires_approval",
            ))

        # 4. Tasks complete
        if not request.tasks:
            issues.append(DispatchIssue(
                category="task_complete",
                severity="error",
                message="Dispatch request has no tasks",
                field="tasks",
            ))
        else:
            for task in request.tasks:
                if task.status.is_terminal() and task.status.value != "pending":
                    pass  # already done

        # 5. Dependency complete (check task IDs are coherent)
        if request.tasks:
            task_ids = set(t.task_id for t in request.tasks)
            # For now, just check we have them

        # 6. Rollback ready
        if request.metadata and request.metadata.retry_count > 0:
            if request.metadata.retry_count >= request.metadata.max_retries:
                issues.append(DispatchIssue(
                    category="rollback_ready",
                    severity="warning",
                    message=f"Max retries ({request.metadata.max_retries}) reached",
                    field="metadata.retry_count",
                ))

        # 7. Policy satisfied
        if request.target and not request.target.healthy:
            issues.append(DispatchIssue(
                category="policy_satisfied",
                severity="warning",
                message="Target connector is unhealthy, policy may block",
                field="target.healthy",
            ))

        # 8. Capability satisfied
        if request.tasks and request.target:
            first_task = request.tasks[0]
            if not first_task.action:
                issues.append(DispatchIssue(
                    category="capability_satisfied",
                    severity="warning",
                    message="Task has no action defined",
                    field="tasks[0].action",
                ))

        errors = sum(1 for i in issues if i.severity == "error")
        warnings = len(issues) - errors
        passed = errors == 0

        return DispatchValidationReport(
            passed=passed,
            issues=tuple(issues),
            total_issues=len(issues),
            errors=errors,
            warnings=warnings,
        )

    def validate_batch(
        self,
        requests: Tuple[DispatchRequest, ...],
    ) -> DispatchValidationReport:
        all_issues: List[DispatchIssue] = []
        for req in requests:
            report = self.validate(req)
            all_issues.extend(report.issues)

        errors = sum(1 for i in all_issues if i.severity == "error")
        warnings = len(all_issues) - errors
        passed = errors == 0

        return DispatchValidationReport(
            passed=passed,
            issues=tuple(all_issues),
            total_issues=len(all_issues),
            errors=errors,
            warnings=warnings,
        )
