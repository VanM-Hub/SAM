"""store.py — Persistensi ringan berbasis file utk state mission (M10-007).

Tujuan: restart SAM TIDAK menghilangkan operational truth. State mission
(request / understanding / plan / approval / execution / evidence / audit /
observability) dipersist keras ke disk pada tiap mutasi dan di-reload saat
service di-`__init__`. Tanpa database eksternal — cukup JSON atomik.

Konten yang disimpan TIDAK pernah memuat secret (UxMissionState.as_dict()
sudah menscrub / hanya memuat masked, evidence url, tanpa token). Audit juga
sanitized (boundary).
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional


def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    """Tulis JSON secara atomik (tulis temp lalu rename) utk hindari korupsi
    bila proses crash di tengah penulisan."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".sam_ux_", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, str(path))
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


class MissionStore:
    """Persist state mission ke satu file JSON atomik.

    - load()  : baca state dari disk bila ada (recovery saat restart).
    - save()  : tulis snapshot state mental (request, plan, state, audit).
    - clear() : hapus file (reset, mis. utk test).
    """

    def __init__(self, path: Optional[str] = None, enabled: bool = False) -> None:
        # Default: di dalam repo, folder laporan eng. Boleh di-override utk test.
        default = str(
            Path("docs") / "engineering" / "state" / "ux_mission_state.json"
        )
        self._path = Path(path or default)
        # PERSISTENCE OPT-IN (M10-007): default OFF. Produksi harus mengaktifkan
        # via `enable()` / `enabled=True`. Ini mencegah file state lintas-run
        # mengontaminasi environment dev/test yang memakai service default.
        self._enabled = bool(enabled)

    def enable(self) -> "MissionStore":
        self._enabled = True
        return self

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> Optional[Dict[str, Any]]:
        """Kembalikan dict state yang di-persist, atau None bila tidak ada."""
        if not self._path.exists():
            return None
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def save(self, payload: Dict[str, Any]) -> None:
        if not self._enabled:
            return
        _atomic_write_json(self._path, payload)

    def clear(self) -> None:
        if self._path.exists():
            self._path.unlink()
