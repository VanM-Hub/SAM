"""
OP-252 — Multi-Source Observer.

Gathers read-only operational snapshots from multiple sources
and merges them into a single ObservationSnapshot.

All sources are operational: Mission, Approval, Timeline, Audit,
Trust, Queue, WorkspaceLock, Notification, Replay, Benchmark,
Learning, Health.

Sources are equal — no priority.
If a source times out, it is skipped and recorded; other sources continue.
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class SourceResult:
    """Result from a single operational source."""

    source_name: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0

    def __repr__(self) -> str:
        status = "OK" if self.success else f"FAIL({self.error})"
        return f"SourceResult({self.source_name}: {status}, {self.duration_ms:.0f}ms)"


@dataclass
class MultiSourceSnapshot:
    """Aggregated snapshot from all operational sources."""

    timestamp: float
    sources: Dict[str, SourceResult] = field(default_factory=dict)
    merged_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def all_ok(self) -> bool:
        """True if every source succeeded."""
        return all(r.success for r in self.sources.values())

    @property
    def failed_sources(self) -> List[str]:
        """Names of sources that failed."""
        return [
            name for name, r in self.sources.items()
            if not r.success
        ]

    @property
    def ok_sources(self) -> List[str]:
        """Names of sources that succeeded."""
        return [
            name for name, r in self.sources.items()
            if r.success
        ]

    def __repr__(self) -> str:
        return (
            f"MultiSourceSnapshot("
            f"{len(self.ok_sources)} ok / {len(self.sources)} total, "
            f"failed={self.failed_sources})"
        )


# ── Source definitions ────────────────────────────────────────────────

_SOURCE_TIMEOUT = 30.0  # seconds per source


def _safe_collect(
    source_name: str,
    collector: Callable[[], Any],
) -> SourceResult:
    """Collect from one source with timeout."""
    start = time.time()
    try:
        result: Any = None
        thread_result: List[Any] = []
        thread_error: List[Optional[str]] = [None]

        def _run() -> None:
            try:
                thread_result.append(collector())
            except Exception as e:
                thread_error[0] = str(e)

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=_SOURCE_TIMEOUT)

        elapsed = (time.time() - start) * 1000

        if t.is_alive():
            return SourceResult(
                source_name=source_name,
                success=False,
                error="TIMEOUT",
                duration_ms=elapsed,
            )
        if thread_error[0] is not None:
            return SourceResult(
                source_name=source_name,
                success=False,
                error=thread_error[0],
                duration_ms=elapsed,
            )

        return SourceResult(
            source_name=source_name,
            success=True,
            data=thread_result[0] if thread_result else None,
            duration_ms=elapsed,
        )
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return SourceResult(
            source_name=source_name,
            success=False,
            error=str(e),
            duration_ms=elapsed,
        )


# ── Individual source collectors ──────────────────────────────────────


def _collect_mission() -> Dict[str, Any]:
    from sam.operations.mission_query import (
        get_active_missions_count,
        get_failed_missions_count,
    )
    return {
        "active": get_active_missions_count(),
        "failed": get_failed_missions_count(),
    }


def _collect_approval() -> Dict[str, Any]:
    from sam.operations.approval import get_pending_count
    return {"pending": get_pending_count()}


def _collect_timeline() -> Dict[str, Any]:
    from sam.operations.timeline_query import get_recent_events
    events = get_recent_events(limit=20)
    return {"recent_events": len(events)}


def _collect_audit() -> Dict[str, Any]:
    from sam.operations.audit import get_recent_audit_entries
    entries = get_recent_audit_entries(limit=20)
    return {"recent_entries": len(entries)}


def _collect_trust() -> Dict[str, Any]:
    from sam.operations.trust import get_trust_summary
    return dict(get_trust_summary())


def _collect_queue() -> Dict[str, Any]:
    from sam.operations.providers.queue import QueueProvider
    q = QueueProvider()
    return {
        "size": q.size() if hasattr(q, "size") else 0,
    }


def _collect_workspace_lock() -> Dict[str, Any]:
    from sam.operations.workspace_lock import get_active_lock_count
    return {"locks_held": get_active_lock_count()}


def _collect_notification() -> Dict[str, Any]:
    from sam.operations.notification import get_notification_summary
    return dict(get_notification_summary())


def _collect_replay() -> Dict[str, Any]:
    try:
        from sam.operations.replay import get_replay_status
        return get_replay_status()
    except Exception:
        return {"active": False}


def _collect_benchmark() -> Dict[str, Any]:
    try:
        from sam.operations.benchmark import get_latest_benchmark
        return get_latest_benchmark()
    except Exception:
        return {"latest": None}


def _collect_learning() -> Dict[str, Any]:
    try:
        from sam.operations.brain.pattern_miner import count_patterns
        return {"total_patterns": count_patterns()}
    except Exception:
        return {"total_patterns": 0}


def _collect_health() -> Dict[str, Any]:
    try:
        from sam.operations.health import get_platform_health
        return get_platform_health()
    except Exception:
        return {"status": "unknown"}


# ── Source registry ───────────────────────────────────────────────────

_SOURCES: Dict[str, Callable[[], Any]] = {
    "mission": _collect_mission,
    "approval": _collect_approval,
    "timeline": _collect_timeline,
    "audit": _collect_audit,
    "trust": _collect_trust,
    "queue": _collect_queue,
    "workspace_lock": _collect_workspace_lock,
    "notification": _collect_notification,
    "replay": _collect_replay,
    "benchmark": _collect_benchmark,
    "learning": _collect_learning,
    "health": _collect_health,
}


class MultiSourceObserver:
    """Gathers operational data from all registered sources.

    Each source is collected independently with timeout.
    All results merged into a single MultiSourceSnapshot.
    """

    def __init__(self) -> None:
        self._last_snapshot: Optional[MultiSourceSnapshot] = None

    @property
    def last_snapshot(self) -> Optional[MultiSourceSnapshot]:
        return self._last_snapshot

    def observe_all(self) -> MultiSourceSnapshot:
        """Collect from every registered source."""
        results: Dict[str, SourceResult] = {}
        for name, collector in _SOURCES.items():
            results[name] = _safe_collect(name, collector)

        merged: Dict[str, Any] = {}
        for name, result in results.items():
            if result.success and result.data is not None:
                merged[name] = result.data
            else:
                merged[name] = {"error": result.error or "no_data"}

        self._last_snapshot = MultiSourceSnapshot(
            timestamp=time.time(),
            sources=results,
            merged_data=merged,
        )
        return self._last_snapshot

    def observe_sources(
        self,
        source_names: List[str],
    ) -> MultiSourceSnapshot:
        """Collect from a subset of sources."""
        results: Dict[str, SourceResult] = {}
        for name in source_names:
            collector = _SOURCES.get(name)
            if collector is None:
                results[name] = SourceResult(
                    source_name=name,
                    success=False,
                    error="UNKNOWN_SOURCE",
                )
                continue
            results[name] = _safe_collect(name, collector)

        merged: Dict[str, Any] = {}
        for name, result in results.items():
            if result.success and result.data is not None:
                merged[name] = result.data
            else:
                merged[name] = {"error": result.error or "no_data"}

        self._last_snapshot = MultiSourceSnapshot(
            timestamp=time.time(),
            sources=results,
            merged_data=merged,
        )
        return self._last_snapshot

    def register_source(
        self,
        name: str,
        collector: Callable[[], Any],
    ) -> None:
        """Register a custom operational source."""
        _SOURCES[name] = collector


# ── Convenience functions ─────────────────────────────────────────────


def observe_all() -> MultiSourceSnapshot:
    """One-shot: collect from all sources."""
    return MultiSourceObserver().observe_all()


def observe_sources(source_names: List[str]) -> MultiSourceSnapshot:
    """One-shot: collect from named sources."""
    return MultiSourceObserver().observe_sources(source_names)
