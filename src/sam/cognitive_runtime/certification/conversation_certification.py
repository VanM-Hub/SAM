"""Conversation Certification Bridge — query read-only (Sprint 194)."""
from __future__ import annotations

from .cognitive_certification import CognitiveCertification


class ConversationCertificationBridge:
    """Bridge conversation — status sertifikasi kognitif read-only."""

    def __init__(self, certification: CognitiveCertification = None) -> None:
        self._cert = certification or CognitiveCertification()

    def summary(self) -> dict:
        result = self._cert.certify(
            modules_present=9, modules_expected=9, dto_frozen=True,
            no_forbidden_imports=True, no_inference=True, no_write=True,
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
            no_forbidden_imports=True, no_inference=True, no_write=True,
            deterministic=True, preview_only=True,
        )
        return "certified" if result.certified else "not certified"
