"""Context Builder — membangun konteks memori (Sprint 174).

Phase XVII — Memory Runtime.
Builder hanya membangun DTO. Tidak menyimpan, tidak execute.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass(frozen=True)
class MemoryContext:
    """Konteks memori (immutable, build-only)."""
    context_id: str
    memory_id: str = ""
    values: Dict[str, Any] = field(default_factory=dict)
    readonly: bool = True


class ContextBuilder:
    """Builder konteks memori. Deterministik."""

    def build(
        self, context_id: str, memory_id: str = "",
        values: Dict[str, Any] = None,
    ) -> MemoryContext:
        return MemoryContext(
            context_id=context_id, memory_id=memory_id,
            values=dict(values or {}),
        )
