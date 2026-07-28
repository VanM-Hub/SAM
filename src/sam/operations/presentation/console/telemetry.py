"""ConsoleTelemetry — Performance and usage telemetry for the Console.

Records: startup time, render duration, refresh duration, command latency,
screen switches, errors, memory snapshots.
For profiling console performance — NOT for SAM system telemetry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import time


@dataclass(frozen=True)
class TelemetrySnapshot:
    """A point-in-time performance snapshot (immutable)."""
    timestamp: str
    uptime_seconds: float = 0.0
    render_count: int = 0
    refresh_count: int = 0
    command_count: int = 0
    screen_switch_count: int = 0
    error_count: int = 0
    avg_render_ms: float = 0.0
    avg_refresh_ms: float = 0.0
    avg_command_ms: float = 0.0
    notification_count: int = 0
    unread_notifications: int = 0
    active_strategy: str = "retry"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "uptime_seconds": self.uptime_seconds,
            "render_count": self.render_count,
            "refresh_count": self.refresh_count,
            "command_count": self.command_count,
            "screen_switch_count": self.screen_switch_count,
            "error_count": self.error_count,
            "avg_render_ms": round(self.avg_render_ms, 2),
            "avg_refresh_ms": round(self.avg_refresh_ms, 2),
            "avg_command_ms": round(self.avg_command_ms, 2),
            "notification_count": self.notification_count,
            "unread_notifications": self.unread_notifications,
        }


class ConsoleTelemetry:
    """Performance and usage telemetry for the SAM Console.

    Records timing, counts, and snapshots for profiling.
    NOT for SAM system telemetry — purely for Console runtime analysis.

    Usage:
        telemetry = ConsoleTelemetry(start_time=time.time())
        telemetry.record_render(0.045)  # 45ms
        telemetry.record_refresh(0.120) # 120ms
        telemetry.record_command("approve", 0.030)  # 30ms
        snapshot = telemetry.snapshot()
    """

    def __init__(self, start_time: Optional[float] = None) -> None:
        self._start_time = start_time or time.time()
        self._snapshots: List[TelemetrySnapshot] = []

        # Counters
        self._render_count: int = 0
        self._refresh_count: int = 0
        self._command_count: int = 0
        self._screen_switch_count: int = 0
        self._error_count: int = 0

        # Timing accumulators (in seconds)
        self._render_total: float = 0.0
        self._refresh_total: float = 0.0
        self._command_total: float = 0.0

        # Command breakdown
        self._commands_by_type: Dict[str, int] = {}

    # ── Recording ─────────────────────────────────────────────────────

    def record_render(self, duration_seconds: float) -> None:
        """Record a render operation duration."""
        self._render_count += 1
        self._render_total += duration_seconds

    def record_refresh(self, duration_seconds: float) -> None:
        """Record a refresh operation duration."""
        self._refresh_count += 1
        self._refresh_total += duration_seconds

    def record_command(self, command_type: str,
                       duration_seconds: float) -> None:
        """Record a command execution duration."""
        self._command_count += 1
        self._command_total += duration_seconds
        self._commands_by_type[command_type] = (
            self._commands_by_type.get(command_type, 0) + 1
        )

    def record_screen_switch(self) -> None:
        """Record a screen navigation event."""
        self._screen_switch_count += 1

    def record_error(self) -> None:
        """Record a runtime error."""
        self._error_count += 1

    # ── Query ─────────────────────────────────────────────────────────

    @property
    def render_count(self) -> int:
        return self._render_count

    @property
    def refresh_count(self) -> int:
        return self._refresh_count

    @property
    def command_count(self) -> int:
        return self._command_count

    @property
    def error_count(self) -> int:
        return self._error_count

    @property
    def avg_render_ms(self) -> float:
        if self._render_count == 0:
            return 0.0
        return (self._render_total / self._render_count) * 1000.0

    @property
    def avg_refresh_ms(self) -> float:
        if self._refresh_count == 0:
            return 0.0
        return (self._refresh_total / self._refresh_count) * 1000.0

    @property
    def avg_command_ms(self) -> float:
        if self._command_count == 0:
            return 0.0
        return (self._command_total / self._command_count) * 1000.0

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self._start_time

    @property
    def commands_by_type(self) -> Dict[str, int]:
        return dict(self._commands_by_type)

    # ── Snapshots ─────────────────────────────────────────────────────

    def snapshot(self, notification_count: int = 0,
                 unread_notifications: int = 0,
                 active_strategy: str = "retry") -> TelemetrySnapshot:
        """Create a snapshot of current telemetry state.

        Args:
            notification_count: Total notifications in queue.
            unread_notifications: Unread notification count.
            active_strategy: Current error recovery strategy.

        Returns a frozen TelemetrySnapshot.
        """
        snapshot = TelemetrySnapshot(
            timestamp=datetime.now().isoformat(),
            uptime_seconds=self.uptime_seconds,
            render_count=self._render_count,
            refresh_count=self._refresh_count,
            command_count=self._command_count,
            screen_switch_count=self._screen_switch_count,
            error_count=self._error_count,
            avg_render_ms=self.avg_render_ms,
            avg_refresh_ms=self.avg_refresh_ms,
            avg_command_ms=self.avg_command_ms,
            notification_count=notification_count,
            unread_notifications=unread_notifications,
            active_strategy=active_strategy,
        )
        self._snapshots.append(snapshot)
        return snapshot

    @property
    def snapshots(self) -> Tuple[TelemetrySnapshot, ...]:
        return tuple(self._snapshots)

    def clear_snapshots(self) -> None:
        """Clear accumulated snapshots (keep counters)."""
        self._snapshots.clear()

    def reset_all(self) -> None:
        """Reset all counters and snapshots."""
        self._render_count = 0
        self._refresh_count = 0
        self._command_count = 0
        self._screen_switch_count = 0
        self._error_count = 0
        self._render_total = 0.0
        self._refresh_total = 0.0
        self._command_total = 0.0
        self._commands_by_type.clear()
        self._snapshots.clear()
        self._start_time = time.time()

    def format_summary(self) -> str:
        """Format a human-readable summary string."""
        s = self.snapshot()
        lines = [
            f"SAM Console Telemetry",
            f"  Uptime:           {s.uptime_seconds:.1f}s",
            f"  Renders:          {s.render_count} (avg {s.avg_render_ms:.1f}ms)",
            f"  Refreshes:        {s.refresh_count} (avg {s.avg_refresh_ms:.1f}ms)",
            f"  Commands:         {s.command_count} (avg {s.avg_command_ms:.1f}ms)",
            f"  Screen switches:  {s.screen_switch_count}",
            f"  Errors:           {s.error_count}",
        ]
        return "\n".join(lines)
