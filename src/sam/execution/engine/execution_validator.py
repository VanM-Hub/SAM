# OP-413 — Execution Validator
# Python 3.8, frozen DTO, synchronous
# Validates execution packages for dependencies, cycles, duplicates, etc.

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple, Set
from collections import defaultdict

from .execution_task import ExecutionTask, TaskDependency, TaskStatus
from .execution_builder import ExecutionPackage


@dataclass(frozen=True)
class ValidationSeverity:
    value: str = "warning"  # info, warning, error, critical

    @staticmethod
    def info() -> "ValidationSeverity":
        return ValidationSeverity("info")

    @staticmethod
    def warning() -> "ValidationSeverity":
        return ValidationSeverity("warning")

    @staticmethod
    def error() -> "ValidationSeverity":
        return ValidationSeverity("error")

    @staticmethod
    def critical() -> "ValidationSeverity":
        return ValidationSeverity("critical")


@dataclass(frozen=True)
class ValidationIssue:
    issue_id: str = ""
    category: str = ""  # dependency, duplicate, cycle, missing_connector, missing_approval, invalid_capability, risk_mismatch, rollback_completeness
    severity: ValidationSeverity = field(default_factory=ValidationSeverity.info)
    message: str = ""
    task_id: str = ""


@dataclass(frozen=True)
class ValidationReport:
    passed: bool = True
    issues: Tuple[ValidationIssue, ...] = field(default_factory=tuple)
    total_issues: int = 0
    errors: int = 0
    warnings: int = 0
    infos: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def has_errors(self) -> bool:
        return self.errors > 0

    @property
    def has_blocking_issues(self) -> bool:
        return self.errors > 0 or any(
            i.severity.value in ("error", "critical") for i in self.issues
        )


class ExecutionValidator:
    """Validates ExecutionPackage for structural and logical issues.

    Validations:
    - dependency: missing dependency target, circular references
    - duplicate: duplicate task IDs, duplicate names with same target
    - cycle: cycle detection in dependency graph
    - missing connector: tasks with missing connector type info
    - missing approval: high-risk tasks without approval
    - invalid capability: tasks with suspicious action names
    - risk mismatch: risk level vs action type
    - rollback completeness: rollback tasks linked correctly
    """

    def validate(self, package: ExecutionPackage) -> ValidationReport:
        issues: List[ValidationIssue] = []
        task_ids = set()

        # Build dependency graph for cycle detection
        dep_graph: Dict[str, List[str]] = {}
        for task in package.tasks:
            dep_graph[task.task_id] = []
            for dep in task.dependencies:
                dep_graph[task.task_id].append(dep.depends_on)

        # 1. Dependency validation
        for task in package.tasks:
            for dep in task.dependencies:
                if dep.depends_on and dep.depends_on not in task_ids:
                    # Check if refers to a known request_id (not a task_id yet)
                    # This is a warning if task_id doesn't exist
                    issues.append(ValidationIssue(
                        issue_id=f"dep_{task.task_id[:8]}",
                        category="dependency",
                        severity=ValidationSeverity.warning(),
                        message=f"Task '{task.name}' depends on unknown task '{dep.depends_on[:8]}'",
                        task_id=task.task_id,
                    ))

        # 2. Duplicate detection
        seen_names: Dict[str, str] = {}
        for task in package.tasks:
            key = f"{task.connector_type}.{task.action}.{task.target}"
            if key in seen_names:
                issues.append(ValidationIssue(
                    issue_id=f"dup_{task.task_id[:8]}",
                    category="duplicate",
                    severity=ValidationSeverity.warning(),
                    message=f"Duplicate task: {task.name} (same as {seen_names[key][:8]})",
                    task_id=task.task_id,
                ))
            seen_names[key] = task.task_id
            task_ids.add(task.task_id)

        # 3. Cycle detection (DFS)
        visited: Set[str] = set()
        recursion_stack: Set[str] = set()

        def detect_cycle(node: str, path: List[str]) -> bool:
            if node in recursion_stack:
                issues.append(ValidationIssue(
                    issue_id=f"cycle_{node[:8]}",
                    category="cycle",
                    severity=ValidationSeverity.error(),
                    message=f"Circular dependency detected: {' -> '.join(path + [node[:8]])}",
                    task_id=node,
                ))
                return True
            if node in visited:
                return False
            visited.add(node)
            recursion_stack.add(node)
            for neighbor in dep_graph.get(node, []):
                if neighbor in task_ids:
                    detect_cycle(neighbor, path + [node])
            recursion_stack.discard(node)
            return False

        for tid in list(dep_graph.keys()):
            if tid not in visited:
                detect_cycle(tid, [])

        # 4. Missing connector
        for task in package.tasks:
            if not task.connector_type:
                issues.append(ValidationIssue(
                    issue_id=f"conn_{task.task_id[:8]}",
                    category="missing_connector",
                    severity=ValidationSeverity.error(),
                    message=f"Task '{task.name}' has no connector type",
                    task_id=task.task_id,
                ))

        # 5. Missing approval for high risk
        high_risk_actions = {"delete", "execute", "rollback"}
        for task in package.tasks:
            if task.action in high_risk_actions and not task.requires_approval:
                issues.append(ValidationIssue(
                    issue_id=f"appr_{task.task_id[:8]}",
                    category="missing_approval",
                    severity=ValidationSeverity.error(),
                    message=f"High-risk task '{task.name}' missing approval requirement",
                    task_id=task.task_id,
                ))

        # 6. Invalid capability
        valid_actions = {"read", "write", "create", "delete", "execute",
                          "monitor", "approve", "rollback", "search", "notify"}
        for task in package.tasks:
            if task.action and task.action not in valid_actions:
                issues.append(ValidationIssue(
                    issue_id=f"cap_{task.task_id[:8]}",
                    category="invalid_capability",
                    severity=ValidationSeverity.warning(),
                    message=f"Task '{task.name}' has unusual action '{task.action}'",
                    task_id=task.task_id,
                ))

        # 7. Risk mismatch
        action_risk_map = {
            "read": "low", "search": "low", "monitor": "low", "notify": "low",
            "write": "medium", "create": "medium", "approve": "medium",
            "delete": "high", "execute": "high", "rollback": "high",
        }
        risk_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        for task in package.tasks:
            expected = action_risk_map.get(task.action)
            if expected and task.risk:
                actual = task.risk.level
                if risk_order.get(actual, 0) < risk_order.get(expected, 0):
                    issues.append(ValidationIssue(
                        issue_id=f"risk_{task.task_id[:8]}",
                        category="risk_mismatch",
                        severity=ValidationSeverity.warning(),
                        message=f"Task '{task.name}' risk '{actual}' below expected '{expected}'",
                        task_id=task.task_id,
                    ))

        # 8. Rollback completeness
        for task in package.tasks:
            if task.rollback_task_id and task.rollback_task_id not in task_ids:
                issues.append(ValidationIssue(
                    issue_id=f"rb_{task.task_id[:8]}",
                    category="rollback_completeness",
                    severity=ValidationSeverity.warning(),
                    message=f"Task '{task.name}' references missing rollback task '{task.rollback_task_id[:8]}'",
                    task_id=task.task_id,
                ))

        errors = sum(1 for i in issues if i.severity.value in ("error", "critical"))
        warnings = sum(1 for i in issues if i.severity.value == "warning")
        infos = sum(1 for i in issues if i.severity.value == "info")
        passed = errors == 0

        return ValidationReport(
            passed=passed,
            issues=tuple(issues),
            total_issues=len(issues),
            errors=errors,
            warnings=warnings,
            infos=infos,
        )
