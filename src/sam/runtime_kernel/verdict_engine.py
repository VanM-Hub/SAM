"""Sprint 106 — Security Verdict engine ringkas."""
from sam.runtime_kernel.runtime_security import SecurityVerdict


class VerdictEngine:
    """Engine keputusan keamanan — preview-only."""

    @staticmethod
    def allow(verdict_id: str, reason: str = "allowed") -> SecurityVerdict:
        return SecurityVerdict(verdict_id, True, reason)

    @staticmethod
    def deny(verdict_id: str, reason: str = "denied") -> SecurityVerdict:
        return SecurityVerdict(verdict_id, False, reason)

    @staticmethod
    def is_allowed(verdict: SecurityVerdict) -> bool:
        return verdict.allowed
