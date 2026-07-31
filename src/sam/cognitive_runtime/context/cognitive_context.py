"""Cognitive Context — konteks kognitif (Sprint 189)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass(frozen=True)
class CognitiveContext:
    """Konteks kognitif konsolidasi (immutable).

    Mengonsolidasikan input runtime menjadi representasi deterministik.
    Bukan LLM, tidak melakukan inferensi.
    """
    cognitive_id: str = ""
    scope: str = "mission"
    entries: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    preview_only: bool = True

    def entry_count(self) -> int:
        return len(self.entries)
