"""Memory Tag — tag memori (immutable DTO, Sprint 173).

Phase XVII — Memory Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryTag:
    """Tag memori (immutable)."""
    tag_id: str
    name: str = ""
    category: str = "general"
