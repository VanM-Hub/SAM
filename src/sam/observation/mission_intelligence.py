"""Mission Operational Intelligence - Workstream C1.

Observability mendalam terhadap Mission Runtime:
- C1.2 Mission Timeline (checkpoints dari mission_timeline)
- C1.3 Mission Status (state mission_status)
- C1.4 Mission Progress (progress dari timeline checkpoints)
- C1.5 Mission Health (state mission_health)

READ-ONLY. Membaca DTO Mission yang sudah dipublikasikan runtime.
Tidak mengubah Mission, tidak menambah runtime, tidak menyentuh governance.
Sesuai constraint AP-2C-001: observe, never govern.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════
# C1.2 Mission Timeline
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class MissionCheckpointView:
    """Satu checkpoint mission timeline (immutable, read-only)."""
    checkpoint_id: str = ""
    order: int = 0
    label: str = ""

    def as_dict(self) -> dict:
        return {
            "checkpoint_id": self.checkpoint_id,
            "order": self.order,
            "label": self.label,
        }


@dataclass(frozen=True)
class MissionTimelineView:
    """Timeline mission yang diamati (immutable)."""
    mission_id: str = ""
    checkpoints: Tuple[MissionCheckpointView, ...] = field(default_factory=tuple)

    @property
    def checkpoint_count(self) -> int:
        return len(self.checkpoints)

    def as_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "checkpoint_count": self.checkpoint_count,
            "checkpoints": [c.as_dict() for c in self.checkpoints],
        }


# ═══════════════════════════════════════════════════════════════════════
# C1.3 Mission Status
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class MissionStatusView:
    """Status mission yang diamati (immutable)."""
    mission_id: str = ""
    state: str = "unknown"
    ready: bool = False

    def as_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "state": self.state,
            "ready": self.ready,
        }


# ═══════════════════════════════════════════════════════════════════════
# C1.4 Mission Progress
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class MissionProgressView:
    """Progress mission dari timeline (immutable)."""
    mission_id: str = ""
    total_checkpoints: int = 0
    active_checkpoints: int = 0
    completed_checkpoints: int = 0
    progress_ratio: float = 0.0  # 0.0 .. 1.0

    def as_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "total_checkpoints": self.total_checkpoints,
            "active_checkpoints": self.active_checkpoints,
            "completed_checkpoints": self.completed_checkpoints,
            "progress_ratio": round(self.progress_ratio, 3),
        }


# ═══════════════════════════════════════════════════════════════════════
# C1.5 Mission Health
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class MissionHealthView:
    """Health mission yang diamati (immutable)."""
    mission_id: str = ""
    state: str = "unknown"   # healthy | degraded | critical | unknown
    healthy: bool = False
    critical: bool = False
    check_count: int = 0

    def as_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "state": self.state,
            "healthy": self.healthy,
            "critical": self.critical,
            "check_count": self.check_count,
        }


# ═══════════════════════════════════════════════════════════════════════
# C1.1 Mission Dashboard (agregat C1.2-C1.5)
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class MissionIntelligenceReport:
    """Dashboard intelligence satu mission (immutable)."""
    mission_id: str = ""
    timeline: Optional[MissionTimelineView] = None
    status: Optional[MissionStatusView] = None
    progress: Optional[MissionProgressView] = None
    health: Optional[MissionHealthView] = None

    def as_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "timeline": self.timeline.as_dict() if self.timeline else None,
            "status": self.status.as_dict() if self.status else None,
            "progress": self.progress.as_dict() if self.progress else None,
            "health": self.health.as_dict() if self.health else None,
        }


# ═══════════════════════════════════════════════════════════════════════
# C1 Observer
# ═══════════════════════════════════════════════════════════════════════

class MissionIntelligenceObserver:
    """Observer Mission - membaca publikasi Mission Runtime (read-only).

    Menggunakan kelas Mission yang sudah dipublikasikan oleh mission_runtime:
    - MissionTimeline / TimelineCheckpoint / TimelineBuilder
    - MissionStatus
    - MissionHealth
    Jika class runtime tidak tersedia, turun ke data publikasi registry
    (PublicationRegistry) sebagai fallback yang aman dan read-only.
    """

    def __init__(self, registry) -> None:
        """registry = PublicationRegistry (opsional untuk fallback observasi)."""
        self._registry = registry

    # C1.2
    def timeline(self, mission_id: str = "mission") -> MissionTimelineView:
        """Ambil timeline mission dari mission_runtime (read-only)."""
        try:
            from sam.mission_runtime.timeline_builder import TimelineBuilder
            builder = TimelineBuilder()
            mt = builder.build(mission_id=mission_id, labels=("plan", "approve", "execute", "review", "close"))
            checkpoints = tuple(
                MissionCheckpointView(
                    checkpoint_id=cp.checkpoint_id,
                    order=cp.order,
                    label=cp.label,
                )
                for cp in mt.checkpoints
            )
            return MissionTimelineView(mission_id=mt.mission_id, checkpoints=checkpoints)
        except Exception:
            # Fallback: durasi publikasi mission dari registry
            pub = self._publication_for("mission")
            return MissionTimelineView(
                mission_id=mission_id,
                checkpoints=tuple(
                    MissionCheckpointView(checkpoint_id="cp{0}".format(idx), order=idx, label="stage")
                    for idx in range(max(0, pub.timeline_events))
                ) if pub else (),
            )

    # C1.3
    def status(self, mission_id: str = "mission") -> MissionStatusView:
        """Ambil status mission dari mission_runtime (read-only)."""
        try:
            from sam.mission_runtime.mission_status import MissionStatus
            st = MissionStatus()
            return MissionStatusView(mission_id=mission_id, state=st.state, ready=st.is_ready)
        except Exception:
            pub = self._publication_for("mission")
            state = pub.operational_state if pub else "unknown"
            return MissionStatusView(mission_id=mission_id, state=state, ready=state == "ready")

    # C1.4
    def progress(self, mission_id: str = "mission") -> MissionProgressView:
        """Hitung progress mission dari timeline checkpoints (read-only)."""
        tl = self.timeline(mission_id)
        total = tl.checkpoint_count
        completed = sum(1 for c in tl.checkpoints if c.label in ("close", "done", "complete"))
        ratio = (completed / total) if total > 0 else 0.0
        return MissionProgressView(
            mission_id=mission_id,
            total_checkpoints=total,
            active_checkpoints=max(0, total - completed),
            completed_checkpoints=completed,
            progress_ratio=ratio,
        )

    # C1.5
    def health(self, mission_id: str = "mission") -> MissionHealthView:
        """Ambil health mission dari mission_runtime (read-only)."""
        try:
            from sam.mission_runtime.mission_health import MissionHealth
            mh = MissionHealth(mission_id=mission_id)
            return MissionHealthView(
                mission_id=mission_id,
                state=mh.state,
                healthy=mh.is_healthy,
                critical=mh.is_critical,
                check_count=len(mh.checks),
            )
        except Exception:
            pub = self._publication_for("mission")
            state = pub.health_state if pub else "unknown"
            return MissionHealthView(
                mission_id=mission_id,
                state=state,
                healthy=state == "healthy",
                critical=state == "critical",
                check_count=pub.health_check_count if pub else 0,
            )

    # C1.1
    def dashboard(self, mission_id: str = "mission") -> MissionIntelligenceReport:
        """Agregasi seluruh observasi mission menjadi satu laporan (read-only)."""
        return MissionIntelligenceReport(
            mission_id=mission_id,
            timeline=self.timeline(mission_id),
            status=self.status(mission_id),
            progress=self.progress(mission_id),
            health=self.health(mission_id),
        )

    # ── helper ──
    def _publication_for(self, runtime_id: str):
        if self._registry is None:
            return None
        try:
            for pub in self._registry.observe_all().publications:
                if pub.runtime_id == runtime_id:
                    return pub
        except Exception:
            return None
        return None
