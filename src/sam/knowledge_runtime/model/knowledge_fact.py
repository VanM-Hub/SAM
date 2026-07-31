"""Knowledge Fact — fakta knowledge (immutable DTO, Sprint 181).

Phase XVIII — Knowledge Runtime.
Fact adalah unit dasar pengetahuan. Tidak inferensi.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class KnowledgeFact:
    """Fakta knowledge (immutable)."""
    fact_id: str
    subject: str = ""
    predicate: str = "is"
    obj: str = ""
    source: Optional[str] = None
    preview_only: bool = True

    def is_valid(self) -> bool:
        return bool(self.fact_id) and bool(self.subject)
