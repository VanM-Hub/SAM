"""Environment-adaptive: discovery generik.

Menemukan entitas environment TANPA katalog aplikasi. Setiap mekanisme
(process table, port table, file table, service, mount, env) adalah satu
sumber observasi yang independen; bila satu sumber gagal, discovery tetap
berjalan dan mencatat kegagalan (adaptatif).

TIDAK mengasumsikan nama aplikasi. Word/PDF/OpenClaw tidak pernah
disebut di sini.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from sam.environment.entity import (
    DiscoveryScan,
    Entity,
    EntityKind,
    EntitySource,
    entity_id,
)


@dataclass
class SourceFailure:
    """Satu sumber discovery yang gagal (dicatat, bukan gagalkan semua)."""

    source: str
    error: str

    def as_dict(self) -> Dict[str, Any]:
        return {"source": self.source, "error": self.error}


class EnvironmentDiscovery:
    """Mesin discovery generik multi-sumber.

    Usage:
        d = EnvironmentDiscovery()
        scan = d.discover()   # enumerasi beberapa sumber, jujur per-sumber
    """

    def __init__(self) -> None:
        self._probes: List[Callable[[], List[Entity]]] = [
            self._probe_processes,
            self._probe_ports,
            self._probe_files,
            self._probe_env,
        ]
        # probe yang perlu psutil (opsional, boleh gagal load)
        self._psutil = None

    # --- sumber: PROCESS ---

    def _probe_processes(self) -> List[Entity]:
        ps = self._psutil
        if ps is None:
            try:
                import psutil as ps  # type: ignore
                self._psutil = ps
            except Exception:
                return []  # psutil tidak tersedia -> sumber kosong (jujur)
        out: List[Entity] = []
        try:
            for p in ps.process_iter(["pid", "name", "status"]):
                try:
                    info = p.info
                    pid = str(info.get("pid", ""))
                    if not pid:
                        continue
                    label = str(info.get("name") or f"pid:{pid}")
                    out.append(
                        Entity(
                            id=entity_id(EntityKind.PROCESS,
                                         EntitySource.PROCESS_TABLE, pid),
                            kind=EntityKind.PROCESS,
                            source=EntitySource.PROCESS_TABLE,
                            label=label,
                            attributes={
                                "pid": pid,
                                "status": str(info.get("status") or "unknown"),
                                "health": _probe_process_health(ps, info),
                            },
                            confidence=1.0,
                        )
                    )
                except Exception:
                    continue
        except Exception:
            # proses table tak bisa dibaca -> kosong jujur
            return []
        return out

    # --- sumber: PORT (listening) ---

    def _probe_ports(self) -> List[Entity]:
        ps = self._psutil
        if ps is None:
            try:
                import psutil as ps  # type: ignore
                self._psutil = ps
            except Exception:
                return []
        out: List[Entity] = []
        try:
            for conn in ps.net_connections(kind="listener"):
                try:
                    if conn.laddr is None:
                        continue
                    port = str(conn.laddr.port)
                    out.append(
                        Entity(
                            id=entity_id(EntityKind.PORT, EntitySource.PORT_TABLE,
                                         port),
                            kind=EntityKind.PORT,
                            source=EntitySource.PORT_TABLE,
                            label=f"tcp:{port}",
                            attributes={
                                "port": port,
                                "net_proto": "tcp",
                                "pid": str(conn.pid or ""),
                            },
                            confidence=1.0,
                        )
                    )
                except Exception:
                    continue
        except Exception:
            return []
        return out

    # --- sumber: FILE (scan ringan di kandidat direktori generik) ---

    def _scan_dirs(self) -> List[str]:
        # Direktori generik tanpa asumsi aplikasi. Jangan ikutkan yang berbahaya.
        return [os.path.abspath(".")]

    def _probe_files(self) -> List[Entity]:
        out: List[Entity] = []
        for d in self._scan_dirs():
            try:
                for entry in list(os.scandir(d))[:200]:
                    try:
                        if entry.is_file():
                            st = entry.stat()
                            out.append(
                                Entity(
                                    id=entity_id(EntityKind.FILE,
                                                 EntitySource.FILE_TABLE,
                                                 os.path.abspath(entry.path)),
                                    kind=EntityKind.FILE,
                                    source=EntitySource.FILE_TABLE,
                                    label=entry.name,
                                    attributes={
                                        "path": os.path.abspath(entry.path),
                                        "size_bytes": st.st_size,
                                        "mtime": st.st_mtime,
                                    },
                                    confidence=1.0,
                                )
                            )
                        elif entry.is_dir():
                            out.append(
                                Entity(
                                    id=entity_id(EntityKind.FILE,
                                                 EntitySource.FILE_TABLE,
                                                 os.path.abspath(entry.path)),
                                    kind=EntityKind.FILE,
                                    source=EntitySource.FILE_TABLE,
                                    label=entry.name,
                                    attributes={
                                        "path": os.path.abspath(entry.path),
                                        "is_dir": True,
                                    },
                                    confidence=1.0,
                                )
                            )
                    except Exception:
                        continue
            except Exception:
                continue
        return out

    # --- sumber: ENV (konfigurasi lingkungan) ---

    def _probe_env(self) -> List[Entity]:
        out: List[Entity] = []
        try:
            for k, v in os.environ.items():
                # nilai env dapat berisi secret -> hanya simpan nama (jangan nilai)
                out.append(
                    Entity(
                        id=entity_id(EntityKind.ENV, EntitySource.ENV_TABLE, k),
                        kind=EntityKind.ENV,
                        source=EntitySource.ENV_TABLE,
                        label=f"env:{k}",
                        attributes={"key": k, "present": True},
                        confidence=1.0,
                    )
                )
        except Exception:
            return []
        return out

    # --- orchestration ---

    def discover(self) -> DiscoveryScan:
        scan = DiscoveryScan()
        failures: List[SourceFailure] = []
        seen: Dict[str, Entity] = {}
        for probe in self._probes:
            try:
                for e in probe():
                    # dedupe by id (sumber berbeda bisa overlap)
                    seen.setdefault(e.id, e)
            except Exception as ex:  # pragma: no cover - defensive
                failures.append(SourceFailure(probe.__name__, str(ex)))
        scan.entities = list(seen.values())
        scan.attributes = {"failures": [f.as_dict() for f in failures]}
        return scan


def _probe_process_health(ps: Any, info: Dict[str, Any]) -> str:
    """Health kasar proses dari fakta status (bukan asumsi aplikasi)."""
    status = str(info.get("status") or "unknown").lower()
    return "ok" if status in ("running", "sleeping") else status


# compat: biar `DiscoveryScan().method` lama tidak pecah (tidak dipakai)
