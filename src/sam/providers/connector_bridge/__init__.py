"""Connector Runtime Integration (Program A, Sprint 236).

Sprint 236 — Connector Runtime Integration (OP-2409).
Menghubungkan ProviderIntegration (Program A) dengan Connector Runtime
(Phase XI, legacy) melalui bridge read-only. TIDAK mengubah legacy.
Preview-only, external_calls=0, immutable.

Prinsip:
- ConnectorRuntime (legacy) dibaca untuk readiness/registry/descriptor.
- ProviderIntegration (Program A) dipakai untuk preview LLM.
- Keduanya dipasangkan tanpa provider-specific logic di Agent/Mission/Workflow.
"""
from .connector_bridge import (
    ConnectorProviderBridge,
    ConnectorProviderLink,
    ConnectorReadynessReport,
)

__all__ = [
    "ConnectorProviderBridge",
    "ConnectorProviderLink",
    "ConnectorReadynessReport",
]
