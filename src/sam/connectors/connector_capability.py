"""Connector Capability — frozen DTOs untuk kapabilitas connector.

Sprint 112 — Connector Foundation.
Kapabilitas dideklarasikan secara murni (preview-only); tidak ada eksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ConnectorCapability:
    """Kapabilitas yang didukung oleh sebuah connector.

    Provider-agnostic: kapabilitas dinyatakan dalam istilah generik
    (mis. 'read', 'write', 'stream'), bukan API spesifik provider.
    """
    capability_id: str
    connector_id: str
    name: str
    category: str = "generic"
    description: str = ""
    supported_operations: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CapabilityKind:
    """Jenis kapabilitas (enum-like, immutable)."""
    kind_id: str
    label: str
    operations: List[str] = field(default_factory=list)
