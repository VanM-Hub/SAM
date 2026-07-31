"""Model Contract — kontrak unit model (Sprint 239).

Program B — Model Runtime Integration.
Immutable, deterministik, preview-only.
"""
from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ModelContract:
    """Kontrak model (immutable). Read-only, deterministik."""
    contract_id: str
    owner_id: str = ""
    operations: List[str] = field(default_factory=list)
    preview_only: bool = True
    external_calls: int = 0
    version: str = "25.0.0"

    def hash(self) -> str:
        payload = (
            f"{self.contract_id}|{self.owner_id}|"
            f"{'|'.join(sorted(self.operations))}|{self.external_calls}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def as_dict(self) -> dict:
        return {
            "contract_id": self.contract_id,
            "owner_id": self.owner_id,
            "operations": list(self.operations),
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
            "version": self.version,
            "hash": self.hash(),
        }
