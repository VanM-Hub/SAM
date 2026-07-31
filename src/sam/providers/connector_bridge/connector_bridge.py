"""Connector Provider Bridge — pasangkan Connector Runtime + ProviderIntegration.

Menghubungkan legacy ConnectorRuntime (Phase XI) dengan ProviderIntegration
(Program A) secara read-only. Tidak mengubah legacy.
Preview-only, immutable, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from ...connectors.runtime import ConnectorRuntime, RuntimeReadiness
from ...connectors.connector_descriptor import ConnectorDescriptor
from ...connectors.connector_capability import ConnectorCapability


@dataclass(frozen=True)
class ConnectorProviderLink:
    """Pemasangan satu connector ke provider (immutable)."""
    connector_id: str
    provider_id: Optional[str] = None
    linked: bool = False
    mode: str = "preview"
    external_calls: int = 0


@dataclass(frozen=True)
class ConnectorReadynessReport:
    """Laporan readiness gabungan (immutable)."""
    connector_ready: bool = False
    provider_count: int = 0
    connector_count: int = 0
    links: Tuple[ConnectorProviderLink, ...] = field(default_factory=tuple)

    @property
    def ready(self) -> bool:
        return self.connector_ready and self.provider_count > 0


class ConnectorProviderBridge:
    """Bridge read-only antara ConnectorRuntime dan ProviderIntegration."""

    def __init__(
        self,
        connector_runtime: ConnectorRuntime,
        provider_ids: Optional[Tuple[str, ...]] = None,
    ) -> None:
        self._connector_runtime = connector_runtime
        self._provider_ids = provider_ids or tuple()

    def attach_providers(self, provider_ids: Tuple[str, ...]) -> None:
        self._provider_ids = tuple(provider_ids)

    def connector_readiness(self) -> RuntimeReadiness:
        return self._connector_runtime.readiness()

    def connector_list(self) -> List[str]:
        return self._connector_runtime._registry.list_ids()  # read-only legacy access

    def links(self) -> Tuple[ConnectorProviderLink, ...]:
        """Pasangkan connector (legacy) dengan provider (Program A) generik."""
        connector_ids = self.connector_list()
        links = []
        for cid in connector_ids:
            # Konvensi: connector yang namanya cocok dengan provider_id dikaitkan.
            matched = cid if cid in self._provider_ids else None
            links.append(
                ConnectorProviderLink(
                    connector_id=cid,
                    provider_id=matched,
                    linked=matched is not None,
                    mode="preview",
                    external_calls=0,
                )
            )
        return tuple(links)

    def report(self) -> ConnectorReadynessReport:
        rd = self.connector_readiness()
        return ConnectorReadynessReport(
            connector_ready=rd.ready,
            provider_count=len(self._provider_ids),
            connector_count=len(self.connector_list()),
            links=self.links(),
        )
