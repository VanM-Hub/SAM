"""Docker Compose Request — frozen DTO request compose (preview).

Sprint 148 — Docker Provider.
Representasi request compose tanpa eksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ComposeRequest:
    """Request compose (immutable, preview-only)."""
    request_id: str
    project: str
    operation: str = "compose_up"
    services: List[str] = field(default_factory=list)

    def is_valid(self) -> bool:
        return bool(self.request_id) and bool(self.project)
