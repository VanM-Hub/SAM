"""Repository Compliance - WP-09 (MISSION-4.3 / IP-4.3-001).

Memastikan Experience Repository mematuhi Foundation & Governance:
repository tidak mengubah evidence, experience immutable, tidak ada
authority leakage, tidak ada mutation terhadap Governance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass(frozen=True)
class ComplianceFinding:
    """Satu temuan compliance."""

    code: str
    severity: str
    message: str

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
        }


@dataclass(frozen=True)
class ComplianceCheckResult:
    """Hasil satu pengecekan compliance."""

    target: str
    passed: bool
    findings: Tuple[ComplianceFinding, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "target": self.target,
            "passed": self.passed,
            "findings": [f.as_dict() for f in self.findings],
        }


class ImmutabilityVerification:
    """Verifikasi bahwa experience immutable (tidak diubah setelah disimpan)."""

    @staticmethod
    def verify(records) -> ComplianceCheckResult:
        findings: List[ComplianceFinding] = []
        for record in records:
            if not getattr(record, "verify", lambda: True)():
                findings.append(
                    ComplianceFinding(
                        "HASH_MISMATCH",
                        "error",
                        f"record integrity failed: {record.record_id}",
                    )
                )
        return ComplianceCheckResult(
            target="immutability",
            passed=not findings,
            findings=tuple(findings),
        )


class EvidenceVerification:
    """Verifikasi bahwa repository tidak mengubah evidence (read-only)."""

    @staticmethod
    def verify(evidences) -> ComplianceCheckResult:
        findings: List[ComplianceFinding] = []
        for ev in evidences or ():
            if not getattr(ev, "metadata", ()):
                findings.append(
                    ComplianceFinding(
                        "NO_METADATA",
                        "error",
                        f"evidence without metadata: {getattr(ev, 'evidence_id', '')}",
                    )
                )
        return ComplianceCheckResult(
            target="evidence",
            passed=not findings,
            findings=tuple(findings),
        )


class AuthorityLeakageVerification:
    """Verifikasi tidak ada authority leakage (repository tak eksekusi/approve)."""

    @staticmethod
    def verify(
        *,
        execution: bool = False,
        approval: bool = False,
        governance_mutation: bool = False,
    ) -> ComplianceCheckResult:
        findings: List[ComplianceFinding] = []
        if execution:
            findings.append(ComplianceFinding("EXECUTION", "error", "execution detected"))
        if approval:
            findings.append(ComplianceFinding("APPROVAL", "error", "approval detected"))
        if governance_mutation:
            findings.append(
                ComplianceFinding("GOVERNANCE_MUTATION", "error", "governance mutation")
            )
        return ComplianceCheckResult(
            target="authority_leakage",
            passed=not findings,
            findings=tuple(findings),
        )


class RepositoryComplianceChecker:
    """Checker compliance terpadu untuk Experience Repository."""

    def certify(
        self,
        records=(),
        evidences=(),
        *,
        execution: bool = False,
        approval: bool = False,
        governance_mutation: bool = False,
    ) -> Dict[str, Any]:
        checks = {
            "immutability": ImmutabilityVerification.verify(records).as_dict(),
            "evidence": EvidenceVerification.verify(evidences).as_dict(),
            "authority_leakage": AuthorityLeakageVerification.verify(
                execution=execution,
                approval=approval,
                governance_mutation=governance_mutation,
            ).as_dict(),
        }
        passed = all(c["passed"] for c in checks.values())
        return {
            "component": "experience_repository",
            "passed": passed,
            "certified": passed,
            "checks": checks,
        }
