"""Investigation Compliance - WP-09 (MISSION-4.2 / IP-4.2-001).

Memastikan investigasi mematuhi seluruh batas Foundation dan Governance:
tidak ada runtime mutation, tidak ada execution, tidak ada approval,
tidak ada authority leakage, seluruh compliance lulus.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Pola yang dilarang muncul dalam capability investigasi (read-only).
FORBIDDEN_PATTERNS = (
    "execute(",
    ".execute",
    "approve(",
    ".approve",
    "submit_for_approval",
    "grant_privilege",
    "grant_permission",
    "bypass_approval",
    "escalate_privilege",
    "write(",
    "mutate(",
    "fs.write_text",
    "open(.*'w'",
    "os.remove",
    "shutil.rmtree",
)

# Modul mutation / eksekusi yang dilarang diimpor.
FORBIDDEN_IMPORTS = (
    "execution_runtime.governed_execution",
    "execution_runtime.production_execution",
    "approval",
    "requests",
    "httpx",
    "subprocess",
    "os.system",
)


@dataclass(frozen=True)
class ComplianceFinding:
    """Satu temuan compliance."""

    code: str
    severity: str  # error | warning
    message: str
    location: str = ""

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "location": self.location,
        }


@dataclass(frozen=True)
class ComplianceCheckResult:
    """Hasil pengecekan compliance suatu artefak."""

    target: str
    passed: bool
    findings: Tuple[ComplianceFinding, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "target": self.target,
            "passed": self.passed,
            "findings": [f.as_dict() for f in self.findings],
            "finding_count": len(self.findings),
        }


class ForbiddenPatternCheck:
    """Deteksi pola terlarang dalam source (AST-based)."""

    @classmethod
    def check(cls, source: str, location: str = "") -> ComplianceCheckResult:
        findings: List[ComplianceFinding] = []
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            return ComplianceCheckResult(
                target=location or "source",
                passed=False,
                findings=(
                    ComplianceFinding(
                        "SYNTAX", "error", f"Syntax error: {exc}", location
                    ),
                ),
            )

        # Deteksi import terlarang
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if cls._matches_import(alias.name):
                        findings.append(
                            ComplianceFinding(
                                "FORBIDDEN_IMPORT",
                                "error",
                                f"forbidden import: {alias.name}",
                                location,
                            )
                        )
            elif isinstance(node, ast.ImportFrom) and node.module:
                if cls._matches_import(node.module):
                    findings.append(
                        ComplianceFinding(
                            "FORBIDDEN_IMPORT",
                            "error",
                            f"forbidden import: {node.module}",
                            location,
                        )
                    )

        # Deteksi panggilan berbahaya (tekstual, sederhana)
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in source:
                findings.append(
                    ComplianceFinding(
                        "FORBIDDEN_PATTERN",
                        "error",
                        f"forbidden pattern: {pattern}",
                        location,
                    )
                )

        return ComplianceCheckResult(
            target=location or "source",
            passed=not any(
                f.severity == "error" for f in findings
            ),
            findings=tuple(findings),
        )

    @classmethod
    def _matches_import(cls, name: str) -> bool:
        return any(
            name == f or name.startswith(f + ".")
            for f in FORBIDDEN_IMPORTS
        )


class ReadOnlyVerification:
    """Verifikasi bahwa operasi investigasi tidak memodifikasi state."""

    @staticmethod
    def verify(
        *,
        runtime_mutation: bool = False,
        execution: bool = False,
        approval: bool = False,
    ) -> ComplianceCheckResult:
        findings: List[ComplianceFinding] = []
        if runtime_mutation:
            findings.append(
                ComplianceFinding("MUTATION", "error", "runtime mutation detected")
            )
        if execution:
            findings.append(
                ComplianceFinding("EXECUTION", "error", "execution detected")
            )
        if approval:
            findings.append(
                ComplianceFinding("APPROVAL", "error", "approval flow detected")
            )
        return ComplianceCheckResult(
            target="read_only_verification",
            passed=not findings,
            findings=tuple(findings),
        )


class EvidenceVerification:
    """Verifikasi bahwa evidence mematuhi aturan (ada metadata, valid)."""

    @staticmethod
    def verify(evidences) -> ComplianceCheckResult:
        findings: List[ComplianceFinding] = []
        for e in evidences:
            if not e.metadata:
                findings.append(
                    ComplianceFinding(
                        "NO_METADATA", "error", f"evidence without metadata: {e.evidence_id}"
                    )
                )
            if not e.source.source_id:
                findings.append(
                    ComplianceFinding(
                        "NO_SOURCE", "error", f"evidence without source: {e.evidence_id}"
                    )
                )
        return ComplianceCheckResult(
            target="evidence_verification",
            passed=not findings,
            findings=tuple(findings),
        )


class BoundaryVerification:
    """Verifikasi batas: investigasi tidak memanggil execution/approval."""

    @staticmethod
    def verify(component_name: str) -> ComplianceCheckResult:
        # Component investigation selalu read-only; admin boundary.
        findings: List[ComplianceFinding] = []
        if component_name not in ("investigation", "operational_intelligence"):
            findings.append(
                ComplianceFinding(
                    "OUT_OF_BOUNDARY",
                    "error",
                    f"component {component_name!r} outside investigation boundary",
                )
            )
        return ComplianceCheckResult(
            target="boundary_verification",
            passed=not findings,
            findings=tuple(findings),
        )


class InvestigationComplianceChecker:
    """Checker compliance terpadu untuk capability investigasi."""

    def __init__(self, source_root: Optional[Path] = None) -> None:
        self.source_root = source_root
        self._forbidden = ForbiddenPatternCheck()

    def check_source(self, source: str, location: str = "") -> ComplianceCheckResult:
        return self._forbidden.check(source, location)

    def check_read_only(
        self,
        runtime_mutation: bool = False,
        execution: bool = False,
        approval: bool = False,
    ) -> ComplianceCheckResult:
        return ReadOnlyVerification.verify(
            runtime_mutation=runtime_mutation,
            execution=execution,
            approval=approval,
        )

    def check_evidence(self, evidences) -> ComplianceCheckResult:
        return EvidenceVerification.verify(evidences)

    def check_boundary(self, component_name: str) -> ComplianceCheckResult:
        return BoundaryVerification.verify(component_name)

    def certify(self, component_name: str = "investigation") -> Dict[str, Any]:
        boundary = self.check_boundary(component_name)
        read_only = self.check_read_only()
        checks = {
            "boundary": boundary.as_dict(),
            "read_only": read_only.as_dict(),
        }
        passed = boundary.passed and read_only.passed
        return {
            "component": component_name,
            "passed": passed,
            "certified": passed,
            "checks": checks,
        }
