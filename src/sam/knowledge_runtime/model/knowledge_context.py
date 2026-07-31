"""Knowledge Context — konteks knowledge (immutable DTO, Sprint 181).

Phase XVIII — Knowledge Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class KnowledgeContext:
    """Konteks knowledge (immutable)."""
    context_id: str
    knowledge_id: str = ""
    values: Dict[str, Any] = field(default_factory=dict)
    readonly: bool = True
