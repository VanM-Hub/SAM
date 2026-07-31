"""Connector Score — DTO & engine skor connector.

Sprint 122 — Connector Certification.
Skor kesiapan connector (immutable, deterministik).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from .connector_registry import ConnectorRegistry


@dataclass(frozen=True)
class ConnectorScore:
    """Skor per connector."""
    connector_id: str
    score: float = 0.0
    dimensions: Dict[str, float] = field(default_factory=dict)


class ConnectorScorer:
    """Hitung skor connector."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    def score(self, connector_id: str) -> ConnectorScore:
        caps = self._registry.get_capabilities(connector_id)
        cap_score = min(100.0, len(caps) * 50.0) if caps else 0.0
        dimensions = {
            "capability": cap_score,
            "discovery": 100.0 if self._registry.get(connector_id) else 0.0,
            "preview": 100.0 if caps else 0.0,
        }
        total = sum(dimensions.values()) / len(dimensions)
        return ConnectorScore(connector_id, round(total, 1), dimensions)
