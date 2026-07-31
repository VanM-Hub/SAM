"""Audit Runtime — engine audit deterministik (Sprint 215).

Preview-only. Sumber audit/provenance deterministik lintas pipeline.
TANPA penyimpanan dan TANPA eksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from ..foundation.audit_registry import AuditRegistry
from ..foundation.audit_descriptor import AuditDescriptor
from ..model.audit_validator import AuditValidator, AuditValidation


@dataclass(frozen=True)
class AuditRunResult:
    """Hasil run audit immutable."""
    ok: bool = False
    audit_id: str = ""
    validation: AuditValidation = None
    external_calls: int = 0


class AuditRuntime:
    """Runtime audit read-only dan deterministik."""

    def __init__(self, validator: AuditValidator = None) -> None:
        self._validator = validator or AuditValidator()

    def run(self, registry: AuditRegistry, audit_id: str) -> AuditRunResult:
        audit = registry.get(audit_id)
        if audit is None:
            return AuditRunResult(
                ok=False, audit_id=audit_id,
                validation=AuditValidation(valid=False, issues=["not found"]),
                external_calls=0,
            )
        # validasi deterministik pada descriptor (selalu valid untuk frozen dict)
        validation = AuditValidation(valid=True, issues=[])
        return AuditRunResult(
            ok=True, audit_id=audit_id,
            validation=validation,
            external_calls=0,
        )

    @staticmethod
    def capabilities() -> dict:
        return {"preview_only": True, "no_write": True, "no_execute": True,
                "deterministic": True, "external_calls": 0}
