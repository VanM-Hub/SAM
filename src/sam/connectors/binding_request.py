"""Binding Request — DTO permintaan binding connector.

Sprint 115 — Connector Binding.
Binding = menghubungkan connector dengan kombinasi kapabilitas yang dibutuhkan.
Preview-only — tidak ada eksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class BindingRequest:
    """Permintaan binding connector."""
    request_id: str
    connector_id: str
    capability_ids: List[str] = field(default_factory=list)
    purpose: str = "generic"
