"""Connector Snapshot — DTO snapshot kondisi connector.

Sprint 120 — Connector Monitoring.
Snapshot kondisi connector pada satu titik (immutable).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class ConnectorSnapshot:
    """Snapshot kondisi seorang connector."""
    connector_id: str
    state: str = "unknown"
    health: str = "unknown"
    bound: bool = False
    session_count: int = 0
    extras: Dict[str, str] = field(default_factory=dict)
