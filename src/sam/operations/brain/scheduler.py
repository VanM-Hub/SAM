"""
OP-251 — Observation Scheduler.

Periodic observation engine with configurable interval, manual trigger,
debounce, pause/resume, and snapshot versioning.

Design:
  - Lightweight thread-based timer (not asyncio, not Qt timer)
  - Thread-safe via threading.Event for pause/resume
  - Snapshot versioning = monotonic counter per collect
  - Debounce = skip collect if last collect was < min_interval seconds ago
  - All observation sources wrapped by MultiSourceObserver (OP-252)
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple


# ── Types ──────────────────────────────────────────────────────────

SnapshotCollector = Callable[[], "ObservationSnapshot"]
OnSnapshot = Callable[["VersionedSnapshot"], None]


# ── Data ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class VersionedSnapshot:
    """Observation snapshot with version counter and metadata."""

    version: int
    snapshot: "ObservationSnapshot"
    collected_at: float  # time.time()
    elapsed_ms: float  # time to collect in ms
    sources: Tuple[str, ...] = ("observation_engine",)


# Global version counter (thread-safe via increment)
_SNAPSHOT_COUNTER: int = 0
_COUNTER_LOCK: threading.Lock = threading.Lock()


def _next_version() -> int:
    global _SNAPSHOT_COUNTER
    with _COUNTER_LOCK:
        _SNAPSHOT_COUNTER += 1
        return _SNAPSHOT_COUNTER


@dataclass
class SchedulerConfig:
    """Configuration for ObservationScheduler."""

    interval_seconds: float = 30.0  # default: every 30s
    min_interval_seconds: float = 5.0  # debounce minimum
    debounce_enabled: bool = True
    auto_start: bool = False  # start on create


@dataclass
class SchedulerState:
    """Current state of the scheduler."""

    running: bool = False
    paused: bool = False
    last_collect_at: Optional[float] = None
    last_version: int = 0
    total_collected: int = 0
    total_elapsed_ms: float = 0.0
    errors: int = 0
    last_error: Optional[str] = None


# ── Scheduler ──────────────────────────────────────────────────────


class ObservationScheduler:
    """
    Periodic observation engine.

    Usage:
        scheduler = ObservationScheduler(collector_fn, on_snapshot)
        scheduler.begin(interval=15.0)
        ...
        scheduler.pause()
        scheduler.resume()
        scheduler.stop()
    """

    def __init__(
        self,
        collector: SnapshotCollector,
        on_snapshot: Optional[OnSnapshot] = None,
        config: Optional[SchedulerConfig] = None,
    ):
        self._collector = collector
        self._on_snapshot = on_snapshot
        self._config = config or SchedulerConfig()
        self._state = SchedulerState()

        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # not paused initially
        self._thread: Optional[threading.Thread] = None

        if self._config.auto_start:
            self.begin()

    # ── Public API ─────────────────────────────────────────────────

    @property
    def state(self) -> SchedulerState:
        return self._state

    @property
    def config(self) -> SchedulerConfig:
        return self._config

    @config.setter
    def config(self, cfg: SchedulerConfig) -> None:
        self._config = cfg

    def begin(self, interval: Optional[float] = None) -> None:
        """Begin periodic collection."""
        if self._state.running:
            return
        if interval is not None:
            self._config.interval_seconds = interval
        self._state.running = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop,
            daemon=True,
            name="obs-scheduler",
        )
        _th_start = self._thread.start
        _th_start()

    def stop(self) -> None:
        """Stop periodic collection."""
        self._state.running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None
        self._state.paused = False

    def pause(self) -> None:
        """Pause periodic collection (manual trigger still works)."""
        self._state.paused = True
        self._pause_event.clear()

    def resume(self) -> None:
        """Resume periodic collection."""
        self._state.paused = False
        self._pause_event.set()

    def trigger(self) -> Optional[VersionedSnapshot]:
        """
        Manually trigger collection, bypassing debounce when force=True.
        Returns the snapshot or None on error.
        """
        snap = self._do_collect()
        if snap is not None and self._on_snapshot:
            self._on_snapshot(snap)
        return snap

    def trigger_force(self) -> Optional[VersionedSnapshot]:
        """
        Trigger collection bypassing debounce entirely.
        """
        return self.trigger()

    def reconfigure(self, **kwargs) -> None:
        """Update config fields at runtime."""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)

    def is_running(self) -> bool:
        return self._state.running

    def is_paused(self) -> bool:
        return self._state.paused

    def reset_stats(self) -> None:
        self._state.total_collected = 0
        self._state.total_elapsed_ms = 0.0
        self._state.errors = 0
        self._state.last_error = None

    # ── Internal ───────────────────────────────────────────────────

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            # Wait for resume if paused
            if self._state.paused:
                self._pause_event.wait(timeout=0.5)
                if self._stop_event.is_set():
                    break
                continue

            # Debounce check
            if self._config.debounce_enabled and self._state.last_collect_at:
                elapsed = time.time() - self._state.last_collect_at
                if elapsed < self._config.min_interval_seconds:
                    time.sleep(0.25)
                    continue

            snap = self._do_collect()
            if snap is not None and self._on_snapshot:
                self._on_snapshot(snap)

            # Wait for next interval
            self._stop_event.wait(timeout=self._config.interval_seconds)

    def _do_collect(self) -> Optional[VersionedSnapshot]:
        start = time.time()
        try:
            snapshot = self._collector()
            elapsed = (time.time() - start) * 1000
            versioned = VersionedSnapshot(
                version=_next_version(),
                snapshot=snapshot,
                collected_at=start,
                elapsed_ms=round(elapsed, 1),
            )
            self._state.last_collect_at = start
            self._state.last_version = versioned.version
            self._state.total_collected += 1
            self._state.total_elapsed_ms += elapsed
            return versioned
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            self._state.errors += 1
            self._state.last_error = str(e)
            return None

    def __enter__(self) -> "ObservationScheduler":
        return self

    def __exit__(self, *args) -> None:
        self.stop()


# ── Convenience ────────────────────────────────────────────────────


def create_scheduler(
    collector: SnapshotCollector,
    interval: float = 30.0,
    auto_start: bool = True,
) -> ObservationScheduler:
    """Create and optionally start a scheduler."""
    config = SchedulerConfig(interval_seconds=interval, auto_start=auto_start)
    return ObservationScheduler(collector, config=config)


