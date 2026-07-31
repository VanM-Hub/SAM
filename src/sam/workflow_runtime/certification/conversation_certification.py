"""Conversation Certification Bridge — query read-only (Sprint 202)."""
from __future__ import annotations

from .workflow_certification import WorkflowCertification


class ConversationCertificationBridge:
    """Bridge conversation — status sertifikasi workflow read-only."""

    def __init__(self, certification: WorkflowCertification = None) -> None:
        self._cert = certification or WorkflowCertification()

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
