"""Audit Preview Consumer (Session 09 - Policy & Audit Activation).

AD-ENG-002 Activation Pattern Standard:
  Conversation -> RuntimeService -> ExecutionRuntime(preview)
  -> AuditPreviewConsumer -> AuditRegistry -> ConversationAuditBridge -> STOP.

Wire Audit di entry via jalur resmi, pakai AuditRegistry + ConversationAuditBridge +
ConversationIntegrationBridge yang SUDAH ADA. Audit jadi capability governance aktif.
Tanpa AuditEngine/Compliance/Security/Runtime baru; tanpa ubah ExecutionRuntime/
RuntimeService/internal audit_runtime; tanpa integrasi terlarang.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

from sam.audit_runtime.foundation.audit_registry import AuditRegistry
from sam.audit_runtime.foundation.conversation_audit import (
    ConversationAuditBridge,
)
from sam.audit_runtime.integration.conversation_integration import (
    ConversationIntegrationBridge,
)


@dataclass(frozen=True)
class AuditPreview:
    """Snapshot audit (immutable, read-only). Preview-only, immutable, no_execute."""
    audit_id: str
    found: bool = False
    category: str = ""
    description: str = ""
    provenance: bool = True
    traceability: bool = True
    integration_ok: bool = False
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "audit_id": self.audit_id,
            "found": self.found,
            "category": self.category,
            "description": self.description,
            "provenance": self.provenance,
            "traceability": self.traceability,
            "integration_ok": self.integration_ok,
            "external_calls": self.external_calls,
        }


class AuditPreviewConsumer:
    """Consumer Audit via jalur Conversation -> RuntimeService.

    READ-ONLY: resolve audit dari registry (yang sudah ada), via bridge.
    Audit jadi capability governance operasional. BUKAN pipeline internal;
    tidak mengubah ExecutionRuntime/RuntimeService/audit_runtime.
    """

    def __init__(self, registry: Optional[AuditRegistry] = None) -> None:
        self._registry = registry or AuditRegistry()
        self._bridge = ConversationAuditBridge(self._registry)
        self._integ = ConversationIntegrationBridge(self._registry)

    @property
    def registry(self) -> AuditRegistry:
        return self._registry

    def list_audits(self) -> List[str]:
        """Daftar id audit (read-only)."""
        return [a.audit_id for a in self._registry.all_entries()]

    def resolve_audit(self, audit_id: str) -> AuditPreview:
        """Resolve satu audit via bridge (read-only, immutable, no-execute)."""
        if not self._registry.exists(audit_id):
            return AuditPreview(audit_id=audit_id, found=False)
        a = self._registry.get(audit_id)
        run = self._integ.query_3_pipeline(audit_id)
        return AuditPreview(
            audit_id=audit_id,
            found=True,
            category=a.category,
            description=a.description,
            provenance=a.provenance,
            traceability=a.traceability,
            integration_ok=bool(run.get("ok")),
            external_calls=0,
        )

    def summary(self) -> dict:
        """Ringkasan audit registry (read-only)."""
        return {
            "total_audit": self._registry.count(),
            "ids": self.list_audits(),
        }
