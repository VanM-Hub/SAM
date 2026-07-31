"""Binding Result — DTO hasil binding.

Sprint 115 — Connector Binding.
Hasil binding immutable, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class BindingResult:
    """Hasil binding connector."""
    binding_id: str
    connector_id: str
    success: bool = False
    message: str = ""
    bound_capabilities: List[str] = field(default_factory=list)
