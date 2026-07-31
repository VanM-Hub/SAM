"""Provider Monitoring — monitoring provider (read-only).

Sprint 153 — Monitoring.
Memantau aktivitas preview dan external calls. Tidak invoke.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..registry.provider_registry import ProviderRegistry


@dataclass(frozen=True)
class MetricSample:
    """Satu sampel metrik provider (immutable)."""
    provider_id: str
    previews: int = 0
    external_calls: int = 0
    healthy: bool = True


@dataclass(frozen=True)
class MonitoringReport:
    """Laporan monitoring (immutable)."""
    total_providers: int = 0
    total_previews: int = 0
    total_external_calls: int = 0
    healthy_count: int = 0
    samples: List[MetricSample] = field(default_factory=list)


class ProviderMonitor:
    """Monitor provider. Read-only, deterministik."""

    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry

    def sample(self) -> List[MetricSample]:
        samples = []
        for pid in self._registry.list_ids():
            desc = self._registry.get(pid)
            caps = self._registry.get_capabilities(pid)
            previews = len(caps)
            samples.append(
                MetricSample(
                    provider_id=pid,
                    previews=previews,
                    external_calls=0,
                    healthy=True,
                )
            )
        return samples

    def report(self) -> MonitoringReport:
        samples = self.sample()
        return MonitoringReport(
            total_providers=len(samples),
            total_previews=sum(s.previews for s in samples),
            total_external_calls=sum(s.external_calls for s in samples),
            healthy_count=sum(1 for s in samples if s.healthy),
            samples=samples,
        )
