"""Execution Operational Intelligence - Workstream C4.

Observability mendalam terhadap Execution Runtime:
- C4.1 Live Execution (descriptor execution yang terdaftar)
- C4.2 Runtime Timeline (history eksekusi end-to-end)
- C4.6 Execution Analytics (ringkasan total/completed/failed)

READ-ONLY. Membaca data Execution yang sudah dipublikasikan runtime.
TIDAK mengeksekusi, tidak mengubah history, tidak menyentuh governance.
Sesuai constraint AP-2C-001: observe, never govern.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════
# C4.1 Live Execution
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ExecutionView:
    """Satu unit eksekusi yang diamati (immutable)."""
    execution_id: str = ""
    name: str = ""
    operation: str = ""
    provider: str = "generic"
    mode: str = "preview"      # preview | execute | rollback
    category: str = "execution"
    requires_approval: bool = True
    tags: Tuple[str, ...] = field(default_factory=tuple)
    health: str = "healthy"    # healthy | degraded | down

    def as_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "name": self.name,
            "operation": self.operation,
            "provider": self.provider,
            "mode": self.mode,
            "category": self.category,
            "requires_approval": self.requires_approval,
            "tags": list(self.tags),
            "health": self.health,
        }


# ═══════════════════════════════════════════════════════════════════════
# C4.2 Runtime Timeline
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ExecutionTimelineEntry:
    """Satu entri timeline eksekusi (immutable)."""
    entry_id: str = ""
    execution_id: str = ""
    status: str = "pending"
    provider_id: str = ""
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "execution_id": self.execution_id,
            "status": self.status,
            "provider_id": self.provider_id,
            "external_calls": self.external_calls,
        }


@dataclass(frozen=True)
class ExecutionTimeline:
    """Timeline eksekusi (immutable)."""
    total: int = 0
    entries: Tuple[ExecutionTimelineEntry, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "entries": [e.as_dict() for e in self.entries],
        }


# ═══════════════════════════════════════════════════════════════════════
# C4.6 Execution Analytics
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ExecutionAnalytics:
    """Ringkasan analitik eksekusi (immutable)."""
    total: int = 0
    completed: int = 0
    failed: int = 0
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "external_calls": self.external_calls,
        }


# ═══════════════════════════════════════════════════════════════════════
# C4 report agregat
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ExecutionIntelligenceReport:
    """Laporan intelligence execution (immutable)."""
    executions: Tuple[ExecutionView, ...] = field(default_factory=tuple)
    timeline: Optional[ExecutionTimeline] = None
    analytics: Optional[ExecutionAnalytics] = None

    def as_dict(self) -> dict:
        return {
            "execution_count": len(self.executions),
            "executions": [e.as_dict() for e in self.executions],
            "timeline": self.timeline.as_dict() if self.timeline else None,
            "analytics": self.analytics.as_dict() if self.analytics else None,
        }


# ═══════════════════════════════════════════════════════════════════════
# C4 Observer
# ═══════════════════════════════════════════════════════════════════════

class ExecutionIntelligenceObserver:
    """Observer Execution - membaca publikasi execution (read-only).

    Menerima ExecutionRegistry + ExecutionHistory opsional (di-inject dari
    wiring) agar dapat membaca data yang SUDAH terdaftar tanpa mutasi.
    Observer TIDAK memanggil record(), hanya membaca.
    """

    def __init__(self, publication_registry=None,
                 execution_registry=None, execution_history=None) -> None:
        self._pub_registry = publication_registry
        self._reg = execution_registry
        self._history = execution_history

    def executions(self) -> Tuple[ExecutionView, ...]:
        views: List[ExecutionView] = []
        if self._reg is not None:
            try:
                for d in self._reg.all():
                    eid = getattr(d, "id", getattr(d, "execution_id", "unknown"))
                    views.append(ExecutionView(
                        execution_id=eid,
                        name=getattr(d, "name", eid),
                        operation=getattr(d, "operation", ""),
                        provider=getattr(d, "provider", "generic"),
                        mode=getattr(d, "mode", "preview"),
                        category=getattr(d, "category", "execution"),
                        requires_approval=bool(getattr(d, "requires_approval", True)),
                        tags=tuple(getattr(d, "tags", []) or []),
                        health=self._health_for(),
                    ))
            except Exception:
                pass
        else:
            pub = self._publication_for("execution")
            if pub:
                views.append(ExecutionView(
                    execution_id="execution",
                    name="Execution Runtime",
                    operation="observe",
                    health=pub.health_state,
                ))
        return tuple(views)

    def timeline(self) -> ExecutionTimeline:
        entries: List[ExecutionTimelineEntry] = []
        if self._history is not None:
            try:
                for e in self._history.all():
                    entries.append(ExecutionTimelineEntry(
                        entry_id=getattr(e, "entry_id", ""),
                        execution_id=getattr(e, "execution_id", ""),
                        status=getattr(e, "status", "pending"),
                        provider_id=getattr(e, "provider_id", ""),
                        external_calls=int(getattr(e, "external_calls", 0) or 0),
                    ))
            except Exception:
                pass
        return ExecutionTimeline(total=len(entries), entries=tuple(entries))

    def analytics(self) -> ExecutionAnalytics:
        tl = self.timeline()
        completed = sum(1 for e in tl.entries if e.status in ("completed", "success"))
        failed = sum(1 for e in tl.entries if e.status in ("failed", "error"))
        ext = sum(e.external_calls for e in tl.entries)
        return ExecutionAnalytics(
            total=len(tl.entries),
            completed=completed,
            failed=failed,
            external_calls=ext,
        )

    def report(self) -> ExecutionIntelligenceReport:
        return ExecutionIntelligenceReport(
            executions=self.executions(),
            timeline=self.timeline(),
            analytics=self.analytics(),
        )

    # ── helper ──
    def _health_for(self) -> str:
        pub = self._publication_for("execution")
        return pub.health_state if pub else "healthy"

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
