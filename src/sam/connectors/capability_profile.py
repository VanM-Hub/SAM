"""Capability Profile — DTO profil kapabilitas connector.

Sprint 114 — Connector Capability.
Profil kapabilitas murni, provider-agnostic, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class CapabilityProfile:
    """Profil kapabilitas seorang connector."""
    profile_id: str
    connector_id: str
    capability_ids: List[str] = field(default_factory=list)
    category: str = "generic"
    strength: float = 0.0  # 0.0 - 1.0 (deterministik)
