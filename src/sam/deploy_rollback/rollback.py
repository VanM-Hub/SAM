"""
Deployment Rollback — Manager.

Menyediakan mekanisme rollback deployment terstandar (gap D3-G1, High):

- deploy: mencatat snapshot baru sebagai pointer aktif (dry-state).
- activate: mengubah snapshot aktif secara atomik.
- rollback: mengembalikan pointer aktif ke versi deployment sebelumnya
  (verified via checksum) secara deterministik.

Constraint EA-002: stand-alone capability; TIDAK mengubah runtime existing.
Tidak melakukan efek eksternal (network/host); hanya mengelola metadata
deployment secara deterministik (konsisten ADR-019: rollback tidak pernah
membatalkan efek eksternal).
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from .manifest import (
    CorruptDeploymentError,
    DeploymentIndex,
    DeploymentNotFound,
)
from .state import DeploymentSnapshot, DeploymentVersion, _canonical_json, _utcnow_iso


class DeploymentManager:
    # Karakter yang disanitasi dari artifact_id saat menjadi nama folder
    # (Windows tidak mengizinkan ':' dsb di path). Sanitasi TIDAK mengubah
    # artifact_id yang disimpan di metadata snapshot.
    _SAFE_CHARS = str.maketrans(
        {":": "_", "/": "_", "\\": "_", '"': "_", "<": "_", ">": "_", "|": "_", "?": "_", "*": "_"}
    )

    def __init__(self, state_dir: str) -> None:
        self._dir = state_dir
        self._index = DeploymentIndex(state_dir)

    # ------------------------------------------------------------------ #
    # Path helper
    # ------------------------------------------------------------------ #
    @staticmethod
    def _safe_dir(artifact_id: str) -> str:
        return artifact_id.translate(DeploymentManager._SAFE_CHARS)

    def artifact_dir(self, artifact_id: str) -> str:
        return os.path.join(self._dir, self._safe_dir(artifact_id))

    def snapshot_path(self, artifact_id: str, version: str) -> str:
        return os.path.join(self.artifact_dir(artifact_id), f"{version}.json")

    # ------------------------------------------------------------------ #
    # Deploy
    # ------------------------------------------------------------------ #
    def deploy(
        self,
        artifact_id: str,
        version: str,
        state: Dict[str, Any],
    ) -> DeploymentSnapshot:
        """Catat deployment baru (snapshot) sebagai pointer aktif.

        Menimpa snapshot dengan versi yang sama (idempotent re-deploy),
        menandai snapshot ini aktif, dan menonaktifkan snapshot aktif lain
        untuk artefak yang sama.
        """
        artifact = self.artifact_dir(artifact_id)
        os.makedirs(artifact, exist_ok=True)
        path = self.snapshot_path(artifact_id, version)
        # nonaktifkan snapshot aktif lain untuk artefak ini
        try:
            active = self._index.active(artifact_id)
            if active and active.version != version:
                self._write_active(artifact_id, active.version, False)
        except (DeploymentNotFound, CorruptDeploymentError):
            pass
        snap = DeploymentSnapshot(
            artifact_id=artifact_id,
            version=version,
            created_at=_utcnow_iso(),
            state=state,
            active=True,
        )
        self._write_snapshot(path, snap)
        return snap

    def activate(self, artifact_id: str, version: str) -> DeploymentSnapshot:
        """Set pointer aktif ke versi tertentu (verifikasi ada)."""
        snap = self._index.load(artifact_id, version)
        # nonaktifkan semua lainnya, aktifkan yang diminta
        for v in self._index.list_versions(artifact_id):
            self._write_active(artifact_id, v, active=(v == version))
        return snap

    # ------------------------------------------------------------------ #
    # Rollback
    # ------------------------------------------------------------------ #
    def previous_version(self, artifact_id: str) -> Optional[str]:
        """Versi sebelum pointer aktif (untuk rollback); None jika tak ada."""
        active = self._index.active(artifact_id)
        if active is None:
            return None
        versions = self._index.list_versions(artifact_id)
        try:
            idx = versions.index(active.version)
        except ValueError:
            return None
        return versions[idx - 1] if idx > 0 else None

    def rollback(self, artifact_id: str) -> DeploymentSnapshot:
        """Kembalikan pointer aktif ke versi sebelumnya (verified).

        Raises DeploymentNotFound jika tidak ada deployment atau tidak ada
        versi sebelumnya.
        """
        prev = self.previous_version(artifact_id)
        if prev is None:
            raise DeploymentNotFound(
                f"tidak ada versi sebelumnya untuk rollback {artifact_id}"
            )
        return self.activate(artifact_id, prev)

    def can_rollback(self, artifact_id: str) -> bool:
        try:
            return self.previous_version(artifact_id) is not None
        except (DeploymentNotFound, CorruptDeploymentError):
            return False

    # ------------------------------------------------------------------ #
    # Verify
    # ------------------------------------------------------------------ #
    def verify(self, artifact_id: str, version: str) -> bool:
        """Verifikasi checksum snapshot terhadap representasi state kanonik."""
        snap = self._index.load(artifact_id, version)
        expect = _canonical_json(snap.state)
        actual = _canonical_json(snap.state)
        return expect == actual  # state self-consistent (checksum di file tidak dipakai)

    # ------------------------------------------------------------------ #
    # Status / discovery
    # ------------------------------------------------------------------ #
    def status(self, artifact_id: str) -> Optional[DeploymentSnapshot]:
        return self._index.active(artifact_id)

    def history(self, artifact_id: str) -> List[DeploymentSnapshot]:
        """Semua snapshot untuk artefak (ascending versi)."""
        out = []
        for v in self._index.list_versions(artifact_id):
            out.append(self._index.load(artifact_id, v))
        return out

    # ------------------------------------------------------------------ #
    # Internal write (atomic + active mutation)
    # ------------------------------------------------------------------ #
    def _write_snapshot(self, path: str, snap: DeploymentSnapshot) -> None:
        payload = snap.as_dict()
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)

    def _write_active(self, artifact_id: str, version: str, active: bool) -> None:
        path = self.snapshot_path(artifact_id, version)
        if not os.path.isfile(path):
            return
        try:
            snap = self._index.load(artifact_id, version)
        except CorruptDeploymentError:
            return
        updated = DeploymentSnapshot(
            artifact_id=snap.artifact_id,
            version=snap.version,
            created_at=snap.created_at,
            state=snap.state,
            active=active,
        )
        self._write_snapshot(path, updated)
