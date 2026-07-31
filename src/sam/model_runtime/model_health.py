"""Model Health — kesehatan model untuk sertifikasi (Sprint 248).

Program B — Model Runtime Integration.
Kesehatan read-only, deterministik, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelCertHealth:
    """Kesehatan model (immutable)."""
    healthy: bool = True
    detail: str = "ok"
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "healthy": self.healthy,
            "detail": self.detail,
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }
