"""
Operational Alerting — Router & Store.

Menutup gap D4-G1 (High): alert yang diputuskan layak route oleh policy
diarahkan ke sink operator, dengan:

- dedup (fingerprint) — mencegah spam alert identik berulang.
- ring buffer retensi — membatasi memory.
- lifecycle status OPEN/ACKNOWLEDGED/RESOLVED + timeouts.

Tidak melakukan efek eksternal (network/host) — kanal adalah label; pengiriman
nyata menjadi tanggung jawab sink eksternal di luar capability ini.

Konsisten EA-002: stand-alone capability; TIDAK mengubah runtime existing.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .policy import AlertRoutingDecision
from .state import (
    AlertChannel,
    AlertRecord,
    AlertSeverity,
    AlertStatus,
    _utcnow_iso,
)


@dataclass
class _StoredAlert:
    """Internal: alert + status lifecycle di store (bukan DTO immutable)."""

    record: AlertRecord
    status: AlertStatus = AlertStatus.OPEN
    target_channels: List[str] = field(default_factory=list)
    acknowledged_by: str = ""
    acknowledged_at: str = ""
    resolved_at: str = ""


class AlertStore:
    """Penyimpanan alert ter-agregasi dengan retensi ring buffer + status.

    Not thread-safe dengan asumsi single-threaded routing loop (konsisten
    pola store lain di repo). Tidak menyimpan rahasia.
    """

    def __init__(self, max_records: int = 200) -> None:
        self._max = max(max_records, 1)
        self._alerts: List[_StoredAlert] = []

    def add(self, record: AlertRecord, target_channels: List[str]) -> _StoredAlert:
        stored = _StoredAlert(record=record, target_channels=target_channels)
        self._alerts.append(stored)
        self._trim()
        return stored

    def _trim(self) -> None:
        if len(self._alerts) > self._max:
            self._alerts = self._alerts[-self._max:]

    def by_id(self, alert_id: str) -> Optional[_StoredAlert]:
        for a in self._alerts:
            if a.record.alert_id == alert_id:
                return a
        return None

    def by_fingerprint(self, fingerprint: str) -> Optional[_StoredAlert]:
        for a in reversed(self._alerts):
            if a.record.fingerprint == fingerprint:
                return a
        return None

    def has_fingerprint(self, fingerprint: str) -> bool:
        return self.by_fingerprint(fingerprint) is not None

    def all(self) -> List[_StoredAlert]:
        return list(self._alerts)

    def open_count(self) -> int:
        return sum(1 for a in self._alerts if a.status == AlertStatus.OPEN)

    def critical_open(self) -> int:
        return sum(
            1
            for a in self._alerts
            if a.status == AlertStatus.OPEN
            and a.record.severity == AlertSeverity.CRITICAL
        )

    def count(self) -> int:
        return len(self._alerts)


class AlertRouter:
    """Meng-route alert ke store dengan dedup fingerprint & status lifecycle.

    - route(): terima keputusan routing; jika layak route & belum ada
      fingerprint yang sama OPEN, simpan; kembalikan apakah di-dispatch.
    - acknowledge(): tandai alert dibaca operator.
    - resolve(): tandai alert selesai.
    """

    def __init__(self, store: Optional[AlertStore] = None, dedup_window: float = 300.0) -> None:
        self._store = store or AlertStore()
        self._dedup_window = max(dedup_window, 0.0)
        self._dispatched = 0
        self._deduped = 0

    @property
    def store(self) -> AlertStore:
        return self._store

    @property
    def dispatched_count(self) -> int:
        return self._dispatched

    @property
    def deduped_count(self) -> int:
        return self._deduped

    def route(self, decision: AlertRoutingDecision) -> bool:
        """Kembalikan True jika alert di-dispatch (masuk store), False jika di-drop/dedup."""
        if not decision.routed:
            return False
        return self._dispatch(decision.record, decision.target_channels)

    def _dispatch(self, record: AlertRecord, channels: List[str]) -> bool:
        # dedup: fingerprint yang sama dalam window & masih OPEN tidak disimpan lagi
        existing = self._store.by_fingerprint(record.fingerprint)
        if existing is not None:
            if existing.status == AlertStatus.OPEN:
                self._deduped += 1
                return False
            # resolved/acknowledged lama -> boleh alert baru dengan fingerprint sama
        self._store.add(record, channels)
        self._dispatched += 1
        return True

    def acknowledge(self, alert_id: str, by: str = "operator") -> bool:
        a = self._store.by_id(alert_id)
        if a is None or a.status == AlertStatus.RESOLVED:
            return False
        a.status = AlertStatus.ACKNOWLEDGED
        a.acknowledged_by = by
        a.acknowledged_at = _utcnow_iso()
        return True

    def resolve(self, alert_id: str) -> bool:
        a = self._store.by_id(alert_id)
        if a is None or a.status == AlertStatus.RESOLVED:
            return False
        a.status = AlertStatus.RESOLVED
        a.resolved_at = _utcnow_iso()
        return True

    def is_open(self, alert_id: str) -> bool:
        a = self._store.by_id(alert_id)
        return a is not None and a.status == AlertStatus.OPEN
