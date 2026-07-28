"""
OP-251 — Observation Scheduler.

Triggers ObservationEngine.run() on a configurable interval.
Does NOT perform observations — only scheduling.
Runtime component: no state persistence.
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional


class SchedulerState(Enum):
    """Lifecycle states of the scheduler."""

    IDLE = "idle"
    RUNNING = "running"
    STOPPING = "stopping"  # in-progress cycle, stop requested
    STOPPED = "stopped"


@dataclass
class SchedulerConfig:
    """Configuration for the observation scheduler."""

    interval_seconds: int = 300  # default: 5 minutes
    enabled: bool = True


@dataclass
class VersionedSnapshot:
    """A snapshot with a sequence number for ordering."""

    sequence: int
    timestamp: float
    snapshot: object  # ObservationSnapshot

    def __repr__(self) -> str:
        return (
            f"VersionedSnapshot(seq={self.sequence}, "
            f"ts={self.timestamp:.2f})"
        )


class ObservationScheduler:
    """Periodically triggers observation via a provided callback.

    Responsibilities:
      - Run callback on configured interval (seconds/minutes/hours).
      - Support graceful stop (finish current cycle).
      - Track sequence numbers for versioned snapshots.

    Does NOT persist state: restart = create new scheduler.
    Does NOT observe anything — delegates to callback.
    """

    def __init__(
        self,
        callback: Callable[[], object],
        config: Optional[SchedulerConfig] = None,
    ) -> None:
        self._callback = callback
        self._config = config or SchedulerConfig()
        self._state = SchedulerState.IDLE
        self._thread: Optional[threading.Thread] = None
        self._sequence = 0
        self._last_snapshot: Optional[VersionedSnapshot] = None
        self._lock = threading.Lock()
        self._timer: Optional[threading.Timer] = None

    # ── Properties ─────────────────────────────────────────────────

    @property
    def state(self) -> SchedulerState:
        return self._state

    @property
    def config(self) -> SchedulerConfig:
        return self._config

    @property
    def last_snapshot(self) -> Optional[VersionedSnapshot]:
        return self._last_snapshot

    @property
    def sequence(self) -> int:
        return self._sequence

    # ── Lifecycle ──────────────────────────────────────────────────

    def start(self) -> None:
        """Start the scheduler.

        If already running, this is a no-op.
        """
        with self._lock:
            if self._state in (SchedulerState.RUNNING, SchedulerState.STOPPING):
                return
            self._state = SchedulerState.RUNNING
            self._sequence = 0
        self._schedule_next()

    def stop(self, wait: bool = True) -> None:
        """Request graceful stop.

        If a cycle is in progress, it completes before stopping.
        Sets state to STOPPING, then STOPPED when cycle finishes.
        """
        with self._lock:
            if self._state != SchedulerState.RUNNING:
                self._state = SchedulerState.STOPPED
                return
            self._state = SchedulerState.STOPPING

        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

        if wait and self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=30)

        with self._lock:
            if self._state == SchedulerState.STOPPING:
                self._state = SchedulerState.STOPPED

    def run_once(self) -> VersionedSnapshot:
        """Execute one observation cycle now.

        Useful for manual/on-demand observation outside schedule.
        """
        with self._lock:
            self._sequence += 1
            seq = self._sequence
        snapshot_obj = self._callback()
        vs = VersionedSnapshot(
            sequence=seq,
            timestamp=time.time(),
            snapshot=snapshot_obj,
        )
        self._last_snapshot = vs
        return vs

    # ── Internal ───────────────────────────────────────────────────

    def _schedule_next(self) -> None:
        """Schedule the next observation cycle."""
        with self._lock:
            if self._state != SchedulerState.RUNNING:
                return
        self._timer = threading.Timer(
            self._config.interval_seconds, self._run_cycle
        )
        self._timer.daemon = True
        self._timer.start()

    def _run_cycle(self) -> None:
        """Execute one observation cycle.

        If STOPPING was requested during callback, transitions to STOPPED.
        """
        self._thread = threading.current_thread()
        try:
            self.run_once()
        except Exception:
            pass  # observation engine handles its own errors

        with self._lock:
            if self._state == SchedulerState.STOPPING:
                self._state = SchedulerState.STOPPED
                return

        self._schedule_next()

    def __repr__(self) -> str:
        return (
            f"ObservationScheduler(state={self._state.value}, "
            f"interval={self._config.interval_seconds}s, "
            f"seq={self._sequence})"
        )


# ── Convenience factory ───────────────────────────────────────────────


def create_scheduler(
    callback: Callable[[], object],
    interval_seconds: int = 300,
) -> ObservationScheduler:
    """Create a configured scheduler with a single callback.

    Example:
        engine = ObservationEngine()
        sched = create_scheduler(engine.collect, interval_seconds=60)
        sched.start()
    """
    config = SchedulerConfig(interval_seconds=interval_seconds)
    return ObservationScheduler(callback=callback, config=config)
