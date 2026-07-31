"""Connector Metrics — engine metrik connector.

Sprint 120 — Connector Monitoring.
Metrik agregat connector (read-only, deterministik).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class ConnectorMetrics:
    """Metrik connector."""
    connector_id: str
    bindings: int = 0
    sessions: int = 0
    previews: int = 0
    routes: int = 0
    extra: Dict[str, int] = field(default_factory=dict)
