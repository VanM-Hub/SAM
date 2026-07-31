"""Connector Manifest — DTO manifest connector.

Sprint 122 — Connector Certification.
Manifest mendeklarasikan komposisi connector runtime (immutable).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ConnectorManifest:
    """Manifest connector runtime."""
    manifest_id: str = "connectors.v1"
    version: str = "1.0.0"
    subsystems: List[str] = field(default_factory=lambda: [
        "foundation", "discovery", "capability", "binding", "session",
        "routing", "translation", "preview", "monitoring", "runtime",
        "certification",
    ])
