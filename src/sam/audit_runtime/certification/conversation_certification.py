"""Conversation Certification Bridge — 5 query read-only (Sprint 218)."""
from __future__ import annotations

from .audit_certification import AuditCertification
from .audit_certification_validator import AuditCertificationValidator


class ConversationCertificationBridge:
    """Bridge conversation — 5 query read-only sertifikasi audit."""

    def __init__(self) -> None:
        self._cert = AuditCertification()

    def query_1_certify(self) -> dict:
        """Query 1 — sertifikasi penuh."""
        r = self._cert.certify()
        return {"certified": r.certified, "score": r.score}

    def query_2_dimensions(self) -> dict:
        """Query 2 — daftar 7 dimensi."""
        return {"dimensions": list(AuditCertification.DIMENSIONS)}

    def query_3_criteria(self) -> dict:
        """Query 3 — nama kriteria yang lolos."""
        r = self._cert.certify()
        return {"passed": [c.name for c in r.criteria if c.passed]}

    def query_4_validate(self) -> dict:
        """Query 4 — validasi konstrain."""
        v = AuditCertificationValidator().validate()
        return {"valid": v.valid, "issues": v.issues}

    def query_5_preview(self) -> dict:
        """Query 5 — pastikan preview-only."""
        return {"preview_only": True, "no_write": True, "no_execute": True}
