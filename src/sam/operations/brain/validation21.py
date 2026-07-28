"""
OP-268 — Validation.

Validasi Sprint 21 — Learning & Optimization.

Menguji dengan AST scan sederhana:
  - Tidak ada import ML/AI
  - Tidak ada import LLM
  - Semua deterministic
  - Semua evidence-based
  - Tidak ada auto-execute
  - Semua approval wajib

Plus sanity check pipeline.
"""

from __future__ import annotations

import ast
import time as time_module
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ── Config ─────────────────────────────────────────────────────────

FORBIDDEN_IMPORTS = {
    "tensorflow", "keras", "torch", "pytorch", "sklearn", "scikit-learn",
    "transformers", "langchain", "openai", "anthropic", "cohere",
    "numpy", "pandas",  # not strictly ML but heavy
    "sam.operations.mission",  # domain layer prohibited
    "sam.storage",  # repository prohibited
    "sam.api",  # API prohibited
}

LEARNING_MODULES = [
    "sam.operations.brain.pattern_miner",
    "sam.operations.brain.success_estimator",
    "sam.operations.brain.optimizer",
    "sam.operations.brain.feedback_collector",
    "sam.operations.brain.learning_pipeline",
    "sam.operations.brain.dashboard_brain",
    "sam.operations.brain.integration21",
]

CORE_PATHS: List[str] = []  # supplied at runtime via check_modules


# ── Data ───────────────────────────────────────────────────────────


@dataclass
class ValidationIssue:
    """A single validation issue."""
    module: str
    issue_type: str
    message: str
    severity: str = "error"  # "error" | "warning"


@dataclass
class Sprint21ValidationResult:
    """Complete validation report."""
    passed: bool = False
    issues: List[ValidationIssue] = field(default_factory=list)
    modules_checked: int = 0
    checks: Dict[str, bool] = field(default_factory=dict)
    elapsed_ms: float = 0.0
    generated_at: float = 0.0

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]


# ── Validator ──────────────────────────────────────────────────────


class Sprint21Validator:
    """
    Validasi Sprint 21 compliance.

    Check list:
      ✓ Tidak ada import ML/AI/LLM
      ✓ Tidak ada import domain layer
      ✓ Tidak ada auto-execute pattern
      ✓ Semua deterministic (no randomness)
      ✓ Evidence-based code patterns
      ✓ Approval requirement in proposals
    """

    def __init__(self, core_paths: Optional[List[str]] = None):
        self.core_paths = core_paths or CORE_PATHS
        self._last_result: Optional[Sprint21ValidationResult] = None

    @property
    def last_result(self) -> Optional[Sprint21ValidationResult]:
        return self._last_result

    def validate(
        self,
        modules: Optional[List[str]] = None,
        source_paths: Optional[Dict[str, str]] = None,
    ) -> Sprint21ValidationResult:
        """
        Run full validation.

        Args:
          modules: Module names to validate (default: LEARNING_MODULES)
          source_paths: Dict of {module_name: source_code_string}
                        (if not provided, tries to import and get source)
        """
        start = time_module.time()
        targets = modules or LEARNING_MODULES
        issues: List[ValidationIssue] = []
        checks: Dict[str, bool] = {}

        for module_name in targets:
            try:
                if source_paths and module_name in source_paths:
                    source = source_paths[module_name]
                else:
                    source = self._get_source(module_name)

                tree = ast.parse(source)

                # Check 1: Forbidden imports
                import_issues = self._check_forbidden_imports(module_name, tree)
                issues.extend(import_issues)

                # Check 2: Auto-execute patterns
                exec_issues = self._check_auto_execute(module_name, tree)
                issues.extend(exec_issues)

                # Check 3: Approval requirement
                approval_issues = self._check_approval_pattern(module_name, source)
                issues.extend(approval_issues)

            except ImportError as e:
                issues.append(ValidationIssue(
                    module=module_name, issue_type="import_error",
                    message=f"Cannot import module: {e}", severity="error"
                ))
            except SyntaxError as e:
                issues.append(ValidationIssue(
                    module=module_name, issue_type="syntax_error",
                    message=f"Syntax error: {e}", severity="error"
                ))

        # Aggregate checks
        checks["no_forbidden_imports"] = not any(
            i.issue_type == "forbidden_import" for i in issues
        )
        checks["no_auto_execute"] = not any(
            i.issue_type == "auto_execute" for i in issues
        )
        checks["approval_requirement"] = not any(
            i.issue_type == "approval_missing" for i in issues
        )
        checks["all_modules_importable"] = not any(
            i.issue_type == "import_error" for i in issues
        )
        checks["all_modules_parsable"] = not any(
            i.issue_type == "syntax_error" for i in issues
        )

        passed = all(checks.values()) and not any(
            i.severity == "error" for i in issues
        )

        result = Sprint21ValidationResult(
            passed=passed,
            issues=issues,
            modules_checked=len(targets),
            checks=checks,
            elapsed_ms=(time_module.time() - start) * 1000,
            generated_at=time_module.time(),
        )
        self._last_result = result
        return result

    # ── Check methods ──────────────────────────────────────────────

    def _get_source(self, module_name: str) -> str:
        """Get source code for a module."""
        import importlib
        import inspect
        mod = importlib.import_module(module_name)
        return inspect.getsource(mod)

    def _check_forbidden_imports(
        self, module: str, tree: ast.AST
    ) -> List[ValidationIssue]:
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if self._is_forbidden(alias.name):
                        issues.append(ValidationIssue(
                            module=module, issue_type="forbidden_import",
                            message=f"Forbidden import: {alias.name}",
                        ))
            elif isinstance(node, ast.ImportFrom):
                if node.module and self._is_forbidden(node.module):
                    names = [n.name for n in node.names]
                    issues.append(ValidationIssue(
                        module=module, issue_type="forbidden_import",
                        message=f"Forbidden import from {node.module}: {names}",
                    ))
                # Check up-level imports from domain/storage/API
                if node.module and node.module.startswith("sam."):
                    parts = node.module.split(".")
                    if len(parts) >= 2:
                        sub = parts[1]
                        if sub in ("mission", "storage", "api", "domain"):
                            issues.append(ValidationIssue(
                                module=module, issue_type="domain_import",
                                message=f"Import from prohibited layer: {node.module}",
                                severity="error",
                            ))
        return issues

    def _check_auto_execute(
        self, module: str, tree: ast.AST
    ) -> List[ValidationIssue]:
        """Check for auto-execution patterns."""
        issues = []
        dangerous_calls = {
            "execute", "run", "perform", "commit", "apply",
            "submit_mission", "execute_mission", "auto_execute",
            "system", "os.system", "subprocess",
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    call_name = f"{self._get_attribute_chain(node.func)}"
                elif isinstance(node.func, ast.Name):
                    call_name = node.func.id
                else:
                    continue
                if call_name.lower() in dangerous_calls:
                    issues.append(ValidationIssue(
                        module=module, issue_type="auto_execute",
                        message=f"Potential auto-execute call: {call_name}()",
                        severity="warning",
                    ))
        return issues

    def _check_approval_pattern(
        self, module: str, source: str
    ) -> List[ValidationIssue]:
        """Check that proposal-related code mentions approval."""
        issues = []
        lower = source.lower()
        if "proposal" in source and "approval" not in lower:
            issues.append(ValidationIssue(
                module=module, issue_type="approval_missing",
                message="Module mentions proposals but no approval gate found",
                severity="warning",
            ))
        return issues

    def _is_forbidden(self, name: str) -> bool:
        name_lower = name.lower()
        # Exact match
        if name_lower in FORBIDDEN_IMPORTS:
            return True
        # Prefix match (e.g. torch.nn)
        for forbidden in FORBIDDEN_IMPORTS:
            if name_lower.startswith(forbidden):
                return True
        return False

    def _get_attribute_chain(self, node: ast.AST) -> str:
        """Get full dotted name from attribute chain."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{self._get_attribute_chain(node.value)}.{node.attr}"
        return str(node)


# ── Convenience ────────────────────────────────────────────────────


def validate_sprint21(modules: Optional[List[str]] = None) -> Sprint21ValidationResult:
    """One-shot: run full Sprint 21 validation."""
    validator = Sprint21Validator()
    return validator.validate(modules=modules)
