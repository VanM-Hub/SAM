"""Approval Operational Intelligence - Workstream C3.

Observability mendalam terhadap Approval Subsystem:
- C3.1 Approval Queue (antrean intake approval)
- C3.5 Decision History (riwayat keputusan approval)
- C3.6 Approval Metrics (ringkasan metrik approval)

READ-ONLY. Membaca data Approval yang sudah dipublikasikan runtime.
TIDAK memanggil record/execute/approve/reject. Hanya membaca registry/history.
Sesuai constraint AP-2C-001: observe, never govern.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════
# C3.1 Approval Queue
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ApprovalQueueEntry:
    """Satu antrean approval (immutable)."""
    record_id: str = ""
    timestamp: float = 0.0
    certified: bool = False
    readiness_score: float = 0.0
    status: str = "pending"   # pending | certified | duplicate

    def as_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "timestamp": self.timestamp,
            "certified": self.certified,
            "readiness_score": round(self.readiness_score, 3),
            "status": self.status,
        }


@dataclass(frozen=True)
class ApprovalQueue:
    """Antrean approval (immutable)."""
    total: int = 0
    pending: int = 0
    certified: int = 0
    duplicates: int = 0
    entries: Tuple[ApprovalQueueEntry, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "pending": self.pending,
            "certified": self.certified,
            "duplicates": self.duplicates,
            "entries": [e.as_dict() for e in self.entries],
        }


# ═══════════════════════════════════════════════════════════════════════
# C3.5 Decision History
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class DecisionHistoryEntry:
    """Satu entri riwayat keputusan (immutable)."""
    approval_id: str = ""
    phase: str = ""
    actor: str = ""
    reason: str = ""

    def as_dict(self) -> dict:
        return {
            "approval_id": self.approval_id,
            "phase": self.phase,
            "actor": self.actor,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class DecisionHistory:
    """Riwayat keputusan approval (immutable)."""
    total: int = 0
    entries: Tuple[DecisionHistoryEntry, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "entries": [e.as_dict() for e in self.entries],
        }


# ═══════════════════════════════════════════════════════════════════════
# C3.6 Approval Metrics
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ApprovalMetric:
    """Satu metrik approval (immutable)."""
    name: str = ""
    value: float = 0.0
    unit: str = ""

    def as_dict(self) -> dict:
        return {"name": self.name, "value": self.value, "unit": self.unit}


@dataclass(frozen=True)
class ApprovalMetrics:
    """Ringkasan metrik approval (immutable)."""
    queue_size: int = 0
    history_entries: int = 0
    duplicate_count: int = 0
    metrics: Tuple[ApprovalMetric, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "queue_size": self.queue_size,
            "history_entries": self.history_entries,
            "duplicate_count": self.duplicate_count,
            "metrics": [m.as_dict() for m in self.metrics],
        }


# ═══════════════════════════════════════════════════════════════════════
# C3 report agregat
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ApprovalIntelligenceReport:
    """Laporan intelligence approval (immutable)."""
    queue: Optional[ApprovalQueue] = None
    history: Optional[DecisionHistory] = None
    metrics: Optional[ApprovalMetrics] = None

    def as_dict(self) -> dict:
        return {
            "queue": self.queue.as_dict() if self.queue else None,
            "history": self.history.as_dict() if self.history else None,
            "metrics": self.metrics.as_dict() if self.metrics else None,
        }


# ═══════════════════════════════════════════════════════════════════════
# C3 Observer
# ═══════════════════════════════════════════════════════════════════════

class ApprovalIntelligenceObserver:
    """Observer Approval - membaca publikasi approval (read-only).

    Menerima IntakeRegistry + HistoryEngine opsional (di-inject dari wiring)
    agar dapat membaca data yang SUDAH terdaftar tanpa mutasi.
    Observer TIDAK memanggil record(), hanya membaca.
    """

    def __init__(self, publication_registry=None,
                 intake_registry=None, history_engine=None) -> None:
        self._pub_registry = publication_registry
        self._intake = intake_registry
        self._history = history_engine

    # C3.1
    def queue(self) -> ApprovalQueue:
        entries: List[ApprovalQueueEntry] = []
        total = pending = certified = duplicates = 0
        if self._intake is not None:
            try:
                total = self._intake.count()
                duplicates = self._intake.duplicates()
                for rec in self._intake.list_all():
                    cert = bool(getattr(rec, "certified", False))
                    if cert:
                        certified += 1
                    else:
                        pending += 1
                    entries.append(ApprovalQueueEntry(
                        record_id=getattr(rec, "record_id", ""),
                        timestamp=float(getattr(rec, "timestamp", 0.0) or 0.0),
                        certified=cert,
                        readiness_score=float(getattr(rec, "readiness_score", 0.0) or 0.0),
                        status="certified" if cert else "pending",
                    ))
            except Exception:
                pass
        else:
            pub = self._publication_for("approval")
            if pub:
                total = pub.dashboard_count
        return ApprovalQueue(
            total=total, pending=pending, certified=certified,
            duplicates=duplicates, entries=tuple(entries),
        )

    # C3.5
    def history(self) -> DecisionHistory:
        entries: List[DecisionHistoryEntry] = []
        if self._history is not None:
            try:
                all_hist = self._history.get_all()
                for e in getattr(all_hist, "entries", []) or []:
                    entries.append(DecisionHistoryEntry(
                        approval_id=getattr(e, "approval_id", ""),
                        phase=getattr(e, "phase", ""),
                        actor=getattr(e, "actor", ""),
                        reason=getattr(e, "reason", ""),
                    ))
            except Exception:
                pass
        return DecisionHistory(total=len(entries), entries=tuple(entries))

    # C3.6
    def metrics(self) -> ApprovalMetrics:
        q = self.queue()
        h = self.history()
        return ApprovalMetrics(
            queue_size=q.total,
            history_entries=h.total,
            duplicate_count=q.duplicates,
            metrics=tuple([
                ApprovalMetric(name="queue_size", value=q.total, unit="count"),
                ApprovalMetric(name="pending", value=q.pending, unit="count"),
                ApprovalMetric(name="certified", value=q.certified, unit="count"),
                ApprovalMetric(name="duplicates", value=q.duplicates, unit="count"),
                ApprovalMetric(name="history_entries", value=h.total, unit="count"),
            ]),
        )

    # C3 report
    def report(self) -> ApprovalIntelligenceReport:
        return ApprovalIntelligenceReport(
            queue=self.queue(),
            history=self.history(),
            metrics=self.metrics(),
        )

    # ── helper ──
    def _publication_for(self, runtime_id: str):
        if self._pub_registry is None:
            return None
        try:
            for pub in self._pub_registry.observe_all().publications:
                if pub.runtime_id == runtime_id:
                    return pub
        except Exception:
            return None
        return None
