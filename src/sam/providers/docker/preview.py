"""Docker Preview — preview aksi docker tanpa eksekusi.

Sprint 148 — Docker Provider.
Menghasilkan preview operasi docker (simulasi). Tidak menjalankan apa pun.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class DockerPreview:
    """Preview operasi docker (immutable)."""
    request_id: str
    kind: str  # container | image | compose
    name: str
    operation: str
    preview: bool = True
    executed: bool = False
    engine_contacted: bool = False
    external_calls: int = 0
    notes: List[str] = field(default_factory=list)


class DockerPreviewEngine:
    """Preview docker — external_calls selalu 0, engine tidak dihubungi."""

    def preview(self, kind: str, name: str, operation: str, request_id: str) -> DockerPreview:
        return DockerPreview(
            request_id=request_id,
            kind=kind,
            name=name,
            operation=operation,
            preview=True,
            executed=False,
            engine_contacted=False,
            external_calls=0,
            notes=["dry-run: docker engine not contacted"],
        )
