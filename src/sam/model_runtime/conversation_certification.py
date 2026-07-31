"""Conversation Certification — bridge conversation <-> model cert (Sprint 248).

Program B — Model Runtime Integration.
Read-only bridge; sertifikasi, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .model_certifier import ModelCertifier
from .model_manifest import ModelManifest
from .model_cert_report import ModelCertificationReport


@dataclass(frozen=True)
class ConversationCertificationResult:
    """Hasil sertifikasi pada konteks percakapan (immutable)."""
    conversation_id: str
    report: ModelCertificationReport
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "report": self.report.as_dict(),
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }


class ConversationCertification:
    """Bridge conversation <-> model certification. Read-only."""

    def __init__(self, certifier: ModelCertifier | None = None) -> None:
        self._certifier = certifier or ModelCertifier()

    def certify(self, conversation_id: str, manifest: ModelManifest) -> ConversationCertificationResult:
        report = self._certifier.certify(manifest)
        return ConversationCertificationResult(
            conversation_id=conversation_id,
            report=report,
            preview_only=True,
            external_calls=0,
        )
