"""
Deployment Rollback — Manifest/Index.

Indeks riwayat deployment & pointer aktif, untuk melokasi snapshot yang
dapat di-rollback. Menangani file korup/missing dengan exception eksplisit.

H3/Program D — menutup gap D3-G1 (High): artefak rollback deployment
terstandar (riwayat deployment + pointer aktif).
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Sequence

from .state import DeploymentSnapshot, DeploymentVersion


class DeploymentNotFound(Exception):
    """Snapshot deployment dengan id/versi yang diminta tidak ada."""


class CorruptDeploymentError(Exception):
    """Snapshot deployment korup (JSON tidak valid / checksum tidak cocok)."""


class DeploymentIndex:
    """Manajemen riwayat deployment di dalam sebuah state_dir.

    Layout:
        <state_dir>/<artifact_id (sanitized)>/<version>.json
    Pointer aktif disimpan sebagai marker `active` di dalam file snapshot
    (satu-satunya snapshot aktif per artefak).

    Nama folder disanitasi (karakter seperti ':' diganti '_') agar aman
    lintas filesystem; artifact_id asli tetap disimpan di metadata.
    """

    _SAFE_CHARS = str.maketrans(
        {":": "_", "/": "_", "\\": "_", "\"": "_", "<": "_", ">": "_", "|": "_", "?": "_", "*": "_"}
    )

    def __init__(self, state_dir: str) -> None:
        self._dir = state_dir
        self._deployment_state_filename = "deployments.json"
        os.makedirs(self._dir, exist_ok=True)

    @staticmethod
    def _safe_dir(artifact_id: str) -> str:
        return artifact_id.translate(DeploymentIndex._SAFE_CHARS)

    def _deployment_state_path(self) -> str:
        return os.path.join(self._dir, self._deployment_state_filename)

    def list_artifacts(self) -> List[str]:
        """Daftar artifact_id (asli) yang memiliki riwayat deployment."""
        out = []
        for entry in os.listdir(self._dir):
            full = os.path.join(self._dir, entry)
            if os.path.isdir(full) and not entry.startswith("."):
                # ambil artifact_id asli dari metadata snapshot aktif/pertama
                versions = [n for n in os.listdir(full) if n.endswith(".json")]
                if versions:
                    try:
                        with open(os.path.join(full, versions[0]), "r", encoding="utf-8") as f:
                            data = f.read()
                        import json
                        aid = json.loads(data).get("artifact_id")
                        if aid:
                            out.append(aid)
                            continue
                    except Exception:
                        pass
                out.append(entry)
        return sorted(out)

    def _versions(self, artifact_id: str) -> List["tuple[str, str]"]:
        """(version, fullpath) untuk satu artefak, diurutkan ascending."""
        artifact_dir = self._artifact_path(artifact_id)
        if not os.path.isdir(artifact_dir):
            return []
        versions = []
        for name in os.listdir(artifact_dir):
            if name.endswith(".json") and not name.startswith("."):
                version = name[: -len(".json")]
                versions.append((version, os.path.join(artifact_dir, name)))
        # urutkan berdasarkan DeploymentVersion
        versions.sort(key=lambda vp: (DeploymentVersion.parse(vp[0]).major,
                                      DeploymentVersion.parse(vp[0]).minor,
                                      DeploymentVersion.parse(vp[0]).patch))
        return versions

    def _artifact_path(self, artifact_id: str) -> str:
        return os.path.join(self._dir, self._safe_dir(artifact_id))

    def load(self, artifact_id: str, version: str) -> DeploymentSnapshot:
        """Muat snapshot; raise jika tidak ada / korup."""
        artifact_dir = self._artifact_path(artifact_id)
        path = os.path.join(artifact_dir, f"{version}.json")
        if not os.path.isfile(path):
            raise DeploymentNotFound(
                f"deployment {artifact_id}@{version} tidak ditemukan"
            )
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            raise CorruptDeploymentError(
                f"snapshot {artifact_id}@{version} korup: {exc}"
            ) from exc
        if not isinstance(data, dict):
            raise CorruptDeploymentError(f"snapshot {artifact_id}@{version} bukan object json")
        return DeploymentSnapshot(
            artifact_id=data.get("artifact_id", artifact_id),
            version=data.get("version", version),
            created_at=data.get("created_at", ""),
            state=data.get("state", {}),
            active=bool(data.get("active", False)),
        )

    def latest(self, artifact_id: str) -> DeploymentSnapshot:
        """Snapshot dengan versi tertinggi untuk artefak."""
        versions = self._versions(artifact_id)
        if not versions:
            raise DeploymentNotFound(f"tidak ada deployment untuk {artifact_id}")
        _, path = versions[-1]
        return self._load_path(artifact_id, path)

    def active(self, artifact_id: str) -> Optional[DeploymentSnapshot]:
        """Snapshot yang ditandai aktif (pointer aktif), None jika tidak ada."""
        versions = self._versions(artifact_id)
        for _, path in versions:
            snap = self._load_path(artifact_id, path)
            if snap.active:
                return snap
        return None

    def _load_path(self, artifact_id: str, path: str) -> DeploymentSnapshot:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            raise CorruptDeploymentError(
                f"snapshot {os.path.basename(path)} korup: {exc}"
            ) from exc
        if not isinstance(data, dict):
            raise CorruptDeploymentError(f"snapshot {os.path.basename(path)} bukan object json")
        return DeploymentSnapshot(
            artifact_id=data.get("artifact_id", artifact_id),
            version=os.path.basename(path)[: -len(".json")],
            created_at=data.get("created_at", ""),
            state=data.get("state", {}),
            active=bool(data.get("active", False)),
        )

    def list_versions(self, artifact_id: str) -> List[str]:
        """Versi yang tersedia untuk artefak, ascending."""
        return [v for v, _ in self._versions(artifact_id)]

    def __contains__(self, item: str) -> bool:
        """`artifact_id in index` -> ada riwayat."""
        return item in self.list_artifacts()
