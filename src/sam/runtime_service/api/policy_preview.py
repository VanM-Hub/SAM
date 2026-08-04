"""Policy Preview Consumer (Session 09 - Policy & Audit Activation).

AD-ENG-002 Activation Pattern Standard:
  Conversation -> RuntimeService -> ExecutionRuntime(preview)
  -> PolicyPreviewConsumer -> PolicyRegistry -> ConversationPolicyBridge -> STOP.

Wire Policy di entry via jalur resmi, pakai PolicyRegistry + ConversationPolicyBridge +
ConversationIntegrationBridge yang SUDAH ADA. Policy jadi capability governance aktif.
Tanpa Governance/PolicyEngine/Compliance/Security/Runtime baru; tanpa ubah
ExecutionRuntime/RuntimeService/internal policy_runtime; tanpa integrasi terlarang.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from sam.policy_runtime.foundation.policy_registry import PolicyRegistry
from sam.policy_runtime.foundation.conversation_policy import (
    ConversationPolicyBridge,
)
from sam.policy_runtime.integration.conversation_integration import (
    ConversationIntegrationBridge,
)


@dataclass(frozen=True)
class PolicyPreview:
    """Snapshot policy (immutable, read-only). Preview-only, no evaluate/decision."""
    policy_id: str
    found: bool = False
    name: str = ""
    category: str = ""
    description: str = ""
    integrated_runtimes: List[str] = field(default_factory=list)
    status: str = ""
    integration_ok: bool = False
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "policy_id": self.policy_id,
            "found": self.found,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "integrated_runtimes": list(self.integrated_runtimes),
            "status": self.status,
            "integration_ok": self.integration_ok,
            "external_calls": self.external_calls,
        }


class PolicyPreviewConsumer:
    """Consumer Policy via jalur Conversation -> RuntimeService.

    READ-ONLY: resolve policy dari registry (yang sudah ada), via bridge.
    Policy jadi capability governance operasional. BUKAN pipeline internal;
    tidak mengubah ExecutionRuntime/RuntimeService/policy_runtime.
    """

    def __init__(self, registry: Optional[PolicyRegistry] = None) -> None:
        self._registry = registry or PolicyRegistry()
        self._bridge = ConversationPolicyBridge(self._registry)
        self._integ = ConversationIntegrationBridge(self._registry)

    @property
    def registry(self) -> PolicyRegistry:
        return self._registry

    def list_policies(self) -> List[str]:
        """Daftar id policy (read-only)."""
        return [d.id for d in self._registry.all()]

    def resolve_policy(self, policy_id: str) -> PolicyPreview:
        """Resolve satu policy via bridge (read-only, no evaluate/decision)."""
        if not self._registry.exists(policy_id):
            return PolicyPreview(policy_id=policy_id, found=False)
        d = self._registry.get(policy_id)
        run = self._integ.query_3_pipeline(policy_id)
        return PolicyPreview(
            policy_id=policy_id,
            found=True,
            name=d.name,
            category=d.category,
            description=d.description,
            integrated_runtimes=list(d.integrated_runtimes),
            status=self._bridge.status(policy_id),
            integration_ok=bool(run.get("ok")),
            external_calls=0,
        )

    def summary(self) -> dict:
        """Ringkasan policy registry (read-only)."""
        return self._bridge.summary()
