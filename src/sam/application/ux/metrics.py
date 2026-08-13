"""metrics.py — Metrics Registry ringan untuk M12-008 Observability.

Counter sederhana (thread-safe) yang diekspos via GET /metrics dalam format
Prometheus text. Tanpa dependensi eksternal (tidak menambah prometheus_client).

Telemetri nyata yang dilacak (dipanggil dari service/persistence/runner):
  - mission_received        : jumlah request submit masuk
  - mission_blocked         : jumlah mission ditolak (fail-closed / produksi down)
  - mission_approved        : jumlah approve (decide APPROVE)
  - mission_rejected        : jumlah reject (decide REJECT)
  - execution_started       : jumlah eksekusi mulai
  - execution_completed     : jumlah eksekusi selesai
  - execution_failed        : jumlah eksekusi gagal
  - idempotency_conflict    : jumlah retry dgn key sama tapi teks beda / reuse
  - idempotency_replay      : jumlah retry dgn key sama (dikembalikan state sama)
  - persistence_error       : jumlah error persistence (repo/PG)
  - observation_total       : total seluruh event (bounded / tetap terikat)

Semua counter monotonik (integers) & dibuffer terbatas — tanpa unbounded growth.
"""
from __future__ import annotations

import threading
from typing import Dict


class Metrics:
    """Registry counter telemetri thread-safe (M12-008)."""

    _HELP = {
        "sam_mission_received": "Jumlah request mission yang diterima (submit)",
        "sam_mission_blocked": "Jumlah mission yang ditolak (fail-closed produksi down)",
        "sam_mission_approved": "Jumlah mission disetujui (approve)",
        "sam_mission_rejected": "jumlah mission ditolak user (reject)",
        "sam_execution_started": "Jumlah eksekusi yang mulai berjalan",
        "sam_execution_completed": "Jumlah eksekusi selesai sukses",
        "sam_execution_failed": "Jumlah eksekusi gagal",
        "sam_idempotency_conflict": "Jumlah retry key sama namun teks berbeda (misuse)",
        "sam_idempotency_replay": "Jumlah retry key sama di mana state yang sama dikembalikan",
        "sam_persistence_error": "Jumlah error persistence (repo / PostgreSQL)",
    }

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: Dict[str, int] = {
            "sam_mission_received": 0,
            "sam_mission_blocked": 0,
            "sam_mission_approved": 0,
            "sam_mission_rejected": 0,
            "sam_execution_started": 0,
            "sam_execution_completed": 0,
            "sam_execution_failed": 0,
            "sam_idempotency_conflict": 0,
            "sam_idempotency_replay": 0,
            "sam_persistence_error": 0,
        }

    def inc(self, name: str, by: int = 1) -> None:
        if name not in self._counters:
            return
        with self._lock:
            self._counters[name] += by

    def get(self, name: str) -> int:
        with self._lock:
            return self._counters.get(name, 0)

    def snapshot(self) -> Dict[str, int]:
        with self._lock:
            return dict(self._counters)

    def render_prometheus(self) -> str:
        """Render ke format Prometheus text (bounded, tanpa unbounded labels)."""
        lines: list[str] = []
        with self._lock:
            items = sorted(self._counters.items())
        for name, value in items:
            lines.append(f"# HELP {name} {self._HELP.get(name, '')}")
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")
        return "\n".join(lines) + "\n"


# Singleton proses (satu per server — sesuai composition root).
metrics = Metrics()
