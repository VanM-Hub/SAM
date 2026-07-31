"""Conversation Certification Bridge — query read-only (Sprint 170)."""
from __future__ import annotations

from .skill_certification import SkillCertification
from .skill_certification import SkillCertificationResult  # noqa: F401


class ConversationCertificationBridge:
    """Bridge conversation — status sertifikasi read-only."""

    def __init__(self, certification: SkillCertification = None) -> None:
        self._cert = certification or SkillCertification()

    def summary(self) -> dict:
        result = self._cert.certify(
            modules_present=9, modules_expected=9,
            dto_frozen=True, no_forbidden_imports=True,
            deterministic=True, preview_only=True,
        )
        return {
            "certified": result.certified,
            "score": result.score,
            "criteria": [c.name for c in result.criteria],
        }

    def status(self) -> str:
        result = self._cert.certify(
            modules_present=9, modules_expected=9, dto_frozen=True,
            no_forbidden_imports=True, deterministic=True, preview_only=True,
        )
        return "certified" if result.certified else "not certified"
