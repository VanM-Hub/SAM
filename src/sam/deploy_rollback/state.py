"""
Deployment Rollback — DTO.

DTO immutable (ADR-023) untuk snapshot/artefak deployment dalam mekanisme
rollback deployment terstandar. H3/Program D — menutup gap D3-G1 (High):
tidak ada prosedur/artefak rollback deployment terstandar.

Snapshot deployment menyimpan metadata artefak + representasi kanonik state
yang di-backup saat deploy, sehingga deployment berikutnya dapat di-rollback
ke snapshot sebelumnya secara deterministik & terverifikasi.

Tidak menyimpan credential/rahasia; hanya data deployment (versi, pointer,
representasi state). Payload state di luar DTO ini (lihat snapshot.py).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


def _canonical_json(value: Any) -> str:
    """Representasi JSON kanonik (terurut, ASCII) untuk checksum deterministik."""
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


@dataclass(frozen=True)
class DeploymentVersion:
    """Versi deployment (semantic-ish)."""

    major: int
    minor: int = 0
    patch: int = 0

    @classmethod
    def parse(cls, text: str) -> "DeploymentVersion":
        parts = text.strip().lstrip("v").split(".")
        nums = [0, 0, 0]
        for i, p in enumerate(parts[:3]):
            try:
                nums[i] = int(p)
            except ValueError:
                nums[i] = 0
        return cls(major=nums[0], minor=nums[1], patch=nums[2])

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


@dataclass(frozen=True)
class DeploymentSnapshot:
    """Snapshot immutable dari satu deployment.

    - artifact_id: unik per artefak yang di-deploy.
    - version: versi deployment.
    - created_at: timestamp pembuatan (ISO UTC).
    - state: representasi kanonik state deployment (disimpan ke disk).
    - active: menandai apakah snapshot ini adalah pointer aktif saat ini.
    """

    artifact_id: str
    version: str
    created_at: str
    state: Dict[str, Any] = field(default_factory=dict)
    active: bool = False

    def compute_checksum(self) -> str:
        """SHA-256 dari representasi kanonik state."""
        return hashlib.sha256(_canonical_json(self.state).encode("utf-8")).hexdigest()

    def as_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "version": self.version,
            "created_at": self.created_at,
            "state": self.state,
            "active": self.active,
        }


def _utcnow_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()
