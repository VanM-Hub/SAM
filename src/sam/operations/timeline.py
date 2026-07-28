"""
TimelineEngine — Kronologi insiden dari semua sumber observasi.

Input: Semua observation timestamp dari Runtime, Queue, Workspace, Telemetry.
Output: Timeline yang menceritakan apa yang terjadi dan kapan.
"""

import structlog
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta


logger = structlog.get_logger()


@dataclass
class TimelineEntry:
    """Satu titik dalam kronologi."""
    time: str           # "08:11"
    event: str          # "CPU increased"
    detail: str = ""    # "from 45% to 78%"
    source: str = ""    # runtime_provider, queue_monitor, workspace_provider
    severity: str = "information"

    def to_text(self) -> str:
        return "{time} {event}{detail}".format(
            time=self.time,
            event=self.event,
            detail=(": " + self.detail) if self.detail else "",
        )


class TimelineEngine:
    """Bangun timeline kronologis dari snapshot real-time."""

    def __init__(self, runtime_provider=None, workspace_provider=None, telemetry_service=None):
        self._rp = runtime_provider
        self._wp = workspace_provider
        self._telemetry = telemetry_service

    def build(self, limit: int = 20) -> List[TimelineEntry]:
        """Bangun timeline dari data yang tersedia.

        Args:
            limit: Maksimal entry dalam timeline

        Returns:
            List TimelineEntry — kronologis dari lama ke baru
        """
        entries = []

        # Telemetry events (paling detail)
        if self._telemetry:
            try:
                events = self._telemetry.get_events(limit=50)
                for ev in events[:limit]:
                    ts = getattr(ev, 'timestamp', '')
                    if ts and hasattr(ts, 'strftime'):
                        time_str = ts.strftime("%H:%M")
                    else:
                        time_str = str(ts)[11:16] if len(str(ts)) > 16 else str(ts)
                    entries.append(TimelineEntry(
                        time=time_str,
                        event=getattr(ev, 'event_type', 'unknown'),
                        detail=getattr(ev, 'description', ''),
                        source="telemetry",
                        severity=getattr(ev, 'severity', 'information'),
                    ))
            except Exception:
                pass

        # Runtime entries
        if self._rp:
            snap = self._rp.get_latest()
            if snap:
                now = datetime.now()
                ts = now.strftime("%H:%M")

                cpu = snap.cpu_percent
                mem = snap.memory_percent
                uptime = snap.uptime_seconds
                depth = snap.queue_depth
                active = snap.active_operations
                status = snap.queue_status
                latency = snap.avg_latency_ms

                if cpu > 80:
                    entries.append(TimelineEntry(
                        time=ts,
                        event="CPU spike",
                        detail="{:.1f}%".format(cpu),
                        source="runtime_provider",
                        severity="warning",
                    ))
                elif cpu > 50:
                    entries.append(TimelineEntry(
                        time=ts,
                        event="CPU increased",
                        detail="{:.1f}%".format(cpu),
                        source="runtime_provider",
                    ))

                if mem > 85:
                    entries.append(TimelineEntry(
                        time=ts,
                        event="Memory high",
                        detail="{:.1f}%".format(mem),
                        source="runtime_provider",
                        severity="warning",
                    ))

                if uptime < 300 and uptime > 0:
                    entries.append(TimelineEntry(
                        time=ts,
                        event="System restarted",
                        detail="{:.0f}s ago".format(uptime),
                        source="runtime_provider",
                        severity="warning",
                    ))

                if status == "overloaded":
                    entries.append(TimelineEntry(
                        time=ts,
                        event="Queue overloaded",
                        detail="{} pending, {} active".format(depth, active),
                        source="queue_monitor",
                        severity="warning",
                    ))
                elif status == "growing":
                    entries.append(TimelineEntry(
                        time=ts,
                        event="Queue growing",
                        detail="{} pending".format(depth),
                        source="queue_monitor",
                    ))
                elif active > 0:
                    entries.append(TimelineEntry(
                        time=ts,
                        event="Queue processing",
                        detail="{} active operations".format(active),
                        source="queue_monitor",
                    ))

                if latency > 2000:
                    entries.append(TimelineEntry(
                        time=ts,
                        event="High queue latency",
                        detail="{:.0f}ms avg".format(latency),
                        source="queue_monitor",
                        severity="warning",
                    ))

        # Workspace entries
        if self._wp:
            ws = self._wp.observe()
            now = datetime.now().strftime("%H:%M")

            if ws.disk.percent > 85:
                entries.append(TimelineEntry(
                    time=now,
                    event="Disk near full",
                    detail="{:.1f}% used".format(ws.disk.percent),
                    source="workspace_provider",
                    severity="warning",
                ))

            if ws.database.status.lower() == "unavailable":
                entries.append(TimelineEntry(
                    time=now,
                    event="Database unavailable",
                    source="workspace_provider",
                    severity="critical",
                ))

            if ws.temp.count > 500:
                entries.append(TimelineEntry(
                    time=now,
                    event="Temp files accumulating",
                    detail="{} files ({:.1f} MB)".format(ws.temp.count, ws.temp.size_mb),
                    source="workspace_provider",
                ))

        # Sort by time ascending — parse time strings
        def _parse_time(e):
            parts = e.time.split(":")
            try:
                return int(parts[0]) * 60 + int(parts[1])
            except (ValueError, IndexError):
                return 0

        entries.sort(key=_parse_time)

        # Deduplikasi: hapus entry yang sama persis dalam 1 menit
        seen = set()
        unique = []
        for e in entries:
            key = (e.time, e.event)
            if key not in seen:
                seen.add(key)
                unique.append(e)

        # Limit
        result = unique[-limit:] if len(unique) > limit else unique

        logger.info("timeline_built",
            entries=len(result),
            sources=list(set(e.source for e in result)),
        )
        return result

    def to_text(self, entries: List[TimelineEntry]) -> str:
        """Render timeline ke teks."""
        if not entries:
            return "No timeline data available."
        return "\n".join(e.to_text() for e in entries)
