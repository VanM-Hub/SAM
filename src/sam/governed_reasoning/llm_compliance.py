"""LLM Compliance - WP-09 (MISSION-4.4 / IP-4.4-001).

Memastikan integrasi LLM mematuhi Foundation & Governance: tidak ada bypass
Governance, credential leakage, provider-specific dependency, atau authority
leakage.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


FORBIDDEN_IMPORTS = (
    "requests",
    "httpx",
    "openai",
    "anthropic",
    "google.generativeai",
)

FORBIDDEN_PATTERNS = (
    ".execute(",
    ".approve(",
    "bypass_approval",
    "grant_privilege",
    "os.system",
    "subprocess",
    "print(secret)",
)


@dataclass(frozen=True)
class LLMComplianceResult:
    """Hasil compliance LLM."""

    passed: bool
    checks: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"passed": self.passed, "checks": list(self.checks)}


class GovernanceVerification:
    """Verifikasi tidak ada bypass governance (execution/approval)."""

    @staticmethod
    def verify(
        *, bypass_execution: bool = False, bypass_approval: bool = False
    ) -> Dict[str, Any]:
        passed = not (bypass_execution or bypass_approval)
        return {
            "code": "GOVERNANCE",
            "passed": passed,
            "detail": "bypass_execution" if bypass_execution else (
                "bypass_approval" if bypass_approval else "ok"
            ),
        }


class CredentialLeakageVerification:
    """Verifikasi tidak ada credential leakage (secret di source)."""

    @staticmethod
    def verify(source: str = "") -> Dict[str, Any]:
        leaked = False
        for pattern in (
            "api_key =",
            "secret_key =",
            "openai.api_key",
            "sk-",
        ):
            if pattern in source:
                leaked = True
                break
        return {
            "code": "CREDENTIAL_LEAKAGE",
            "passed": not leaked,
            "detail": "secret pattern found" if leaked else "ok",
        }


class ProviderSpecificVerification:
    """Verifikasi tidak ada provider-specific dependency."""

    @staticmethod
    def verify(source: str = "") -> Dict[str, Any]:
        import ast as _ast

        if not source:
            return {"code": "PROVIDER_AGNOSTIC", "passed": True}
        try:
            tree = _ast.parse(source)
        except SyntaxError:
            return {"code": "PROVIDER_AGNOSTIC", "passed": False, "detail": "syntax"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if any(alias.name == f or alias.name.startswith(f + ".") for f in FORBIDDEN_IMPORTS):
                        return {
                            "code": "PROVIDER_SPECIFIC",
                            "passed": False,
                            "detail": f"forbidden import: {alias.name}",
                        }
            elif isinstance(node, ast.ImportFrom) and node.module:
                if any(node.module == f or node.module.startswith(f + ".") for f in FORBIDDEN_IMPORTS):
                    return {
                        "code": "PROVIDER_SPECIFIC",
                        "passed": False,
                        "detail": f"forbidden import: {node.module}",
                    }
        return {"code": "PROVIDER_AGNOSTIC", "passed": True}


class ForbiddenPatternCheck:
    """Deteksi pola terlarang dalam source."""

    @staticmethod
    def check(source: str) -> LLMComplianceResult:
        findings = []
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in source:
                findings.append({"pattern": pattern})
        return LLMComplianceResult(
            passed=not findings,
            checks=(tuple({"code": "FORBIDDEN", "passed": not findings, "detail": findings}),),
        )


class LLMComplianceChecker:
    """Checker compliance terpadu untuk integrasi LLM."""

    def certify(
        self,
        *,
        source: str = "",
        bypass_execution: bool = False,
        bypass_approval: bool = False,
    ) -> Dict[str, Any]:
        governance = GovernanceVerification.verify(
            bypass_execution=bypass_execution,
            bypass_approval=bypass_approval,
        )
        credential = CredentialLeakageVerification.verify(source)
        provider = ProviderSpecificVerification.verify(source)
        forbidden = ForbiddenPatternCheck.check(source)
        passed = bool(
            governance["passed"]
            and credential["passed"]
            and provider["passed"]
            and forbidden.passed
        )
        return {
            "component": "governed_llm",
            "passed": passed,
            "certified": passed,
            "checks": {
                "governance": governance,
                "credential_leakage": credential,
                "provider_agnostic": provider,
                "forbidden": forbidden.as_dict(),
            },
        }
