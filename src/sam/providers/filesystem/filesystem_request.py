"""Filesystem Request — frozen DTO request filesystem (preview).

Sprint 145 — Filesystem Provider.
Representasi request tanpa eksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class FilesystemRequest:
    """Request operasi filesystem (immutable, preview-only)."""
    request_id: str
    operation: str  # read | write | copy | move | delete | exists | list | mkdir | preview
    path: str
    target_path: Optional[str] = None
    content: Optional[str] = None  # untuk write
    recursive: bool = False

    def is_valid(self) -> bool:
        return bool(self.request_id) and bool(self.operation) and bool(self.path)
