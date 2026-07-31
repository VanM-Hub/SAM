"""Cognitive Contract — kontrak unit kognitif (Sprint 188)."""
from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class CognitiveContract:
    """Kontrak kognitif (immutable). Read-only, deterministik."""
    contract_id: str
    owner_id: str = ""
    operations: List[str] = field(default_factory=list)
    preview_only: bool = True
    version: str = "19.0.0"

    def hash(self) -> str:
        payload = f"{self.contract_id}|{self.owner_id}|{'|'.join(sorted(self.operations))}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
