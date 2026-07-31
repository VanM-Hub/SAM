"""Memory Entry — entri memori (immutable DTO, Sprint 173).

Phase XVII — Memory Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MemoryEntry:
    """Entri memori (immutable)."""
    entry_id: str
    record_id: str = ""
    key: str = ""
    value: Any = None
    readonly: bool = True
