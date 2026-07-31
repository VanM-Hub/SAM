"""Docker Container Request — frozen DTO request container (preview).

Sprint 148 — Docker Provider.
Representasi request container tanpa eksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class ContainerRequest:
    """Request container (immutable, preview-only)."""
    request_id: str
    image: str
    name: Optional[str] = None
    operation: str = "container_create"
    ports: List[str] = field(default_factory=list)
    env: List[str] = field(default_factory=list)

    def is_valid(self) -> bool:
        return bool(self.request_id) and bool(self.image)
