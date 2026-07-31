"""Reference Builder — builder referensi provenance (Sprint 214)."""
from __future__ import annotations

from ..model.audit_reference import AuditReference


class ReferenceBuilder:
    """Builder referensi audit — membentuk DTO saja, tidak menyimpan."""

    def build(self, ref_id: str, kind: str = "provenance",
              source: str = "", commit_hash: str = "") -> AuditReference:
        return AuditReference(
            ref_id=ref_id,
            kind=kind,
            source=source,
            commit_hash=commit_hash,
        )
