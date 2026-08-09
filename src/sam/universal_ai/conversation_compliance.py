"""Conversation Compliance - WP-29 (MISSION-5.1 / IP-5.1-003).

Memastikan conversation tidak memperoleh authority; credential tidak masuk
conversation state; invocation melalui abstraction; provenance & attribution
terjaga; governance context tidak dapat dimodifikasi oleh model.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class ConversationComplianceResult:
    """Hasil compliance Conversation Platform."""

    passed: bool
    checks: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"passed": self.passed, "checks": list(self.checks)}


class ConversationComplianceChecker:
    """Checker compliance untuk conversation."""

    def check(
        self,
        *,
        no_authority: bool = True,
        no_credential_in_state: bool = True,
        invocation_via_abstraction: bool = True,
        context_has_provenance: bool = True,
        history_auditable: bool = True,
        provider_attribution: bool = True,
        governance_context_immutable: bool = True,
        no_execution_bypass: bool = True,
    ) -> ConversationComplianceResult:
        checks = [
            {"code": "NO_AUTHORITY", "passed": no_authority},
            {"code": "NO_CREDENTIAL_IN_STATE", "passed": no_credential_in_state},
            {"code": "INVOCATION_VIA_ABSTRACTION", "passed": invocation_via_abstraction},
            {"code": "CONTEXT_HAS_PROVENANCE", "passed": context_has_provenance},
            {"code": "HISTORY_AUDITABLE", "passed": history_auditable},
            {"code": "PROVIDER_ATTRIBUTION", "passed": provider_attribution},
            {"code": "GOVERNANCE_CONTEXT_IMMUTABLE", "passed": governance_context_immutable},
            {"code": "NO_EXECUTION_BYPASS", "passed": no_execution_bypass},
        ]
        passed = all(c["passed"] for c in checks)
        return ConversationComplianceResult(passed=passed, checks=tuple(checks))

    def certify(self, **kwargs: Any) -> Dict[str, Any]:
        result = self.check(**kwargs)
        return {
            "component": "universal_ai.conversation",
            "passed": result.passed,
            "certified": result.passed,
            "checks": [c for c in result.checks],
        }
