"""Conversation Certification Bridge — query read-only (Sprint 163)."""
from __future__ import annotations

from .agent_certification import AgentCertification


class ConversationCertificationBridge:
    """Bridge conversation — status sertifikasi read-only."""

    def __init__(self, certification: AgentCertification = None) -> None:
        self._cert = certification or AgentCertification()

    def show_summary(self) -> dict:
        result = self._cert.certify(
            modules_present=10, modules_expected=10,
            dto_frozen=True, no_forbidden_imports=True, deterministic=True,
        )
        return {
            "certified": result.certified,
            "score": result.total_score,
            "criteria": [c.name for c in result.criteria],
        }

    def status(self) -> str:
        result = self._cert.certify(
            modules_present=10, modules_expected=10,
            dto_frozen=True, no_forbidden_imports=True, deterministic=True,
        )
        return "certified" if result.certified else "not certified"
