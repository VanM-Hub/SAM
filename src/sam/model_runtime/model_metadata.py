"""Model Metadata — metadata unit model (Sprint 239).

Program B — Model Runtime Integration.
Immutable, deterministik, preview-only.
"""
from __future__ import annotations
from datetime import datetime, timezone
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelMetadata:
    """Metadata model (immutable). Read-only."""
    owner_id: str = ""
    created_at: str = ""
    source_runtime: str = "model"
    version: str = "25.0.0"
    preview_only: bool = True
    no_inference: bool = True
    external_calls: int = 0

    def __post_init__(self) -> None:
        if not self.created_at:
            object.__setattr__(
                self, "created_at",
                datetime.now(timezone.utc).isoformat(timespec="seconds")
                .replace("+00:00", "Z"),
            )

    def as_dict(self) -> dict:
        return {
            "owner_id": self.owner_id,
            "created_at": self.created_at,
            "source_runtime": self.source_runtime,
            "version": self.version,
            "preview_only": self.preview_only,
            "no_inference": self.no_inference,
            "external_calls": self.external_calls,
        }
