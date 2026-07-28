"""
TimelineQueryEngine — Natural querying of operational timelines.

Answers conversational questions by reading from TimelineStore.
No SQL, no LLM. Deterministic, fast, read-only.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timedelta


@dataclass
class TimelineQueryResult:
    """Structured answer for a timeline query."""
    query_type: str  # "today" | "recent" | "latest" | "changes" | "failures" | "successes"
    events: list[dict] = field(default_factory=list)
    count: int = 0
    summary: str = ""
    period_start: str = ""
    period_end: str = ""


# ── Query patterns ────────────────────────────────────────────────────

_PATTERN_TODAY = [
    "hari ini", "today", "sekarang", "sedang terjadi",
]

_PATTERN_RECENT = [
    "baru saja", "barusan", "recent", "terakhir", "beberapa saat",
]

_PATTERN_LATEST = [
    "yang terakhir", "terakhir dilakukan", "latest", "terbaru",
]

_PATTERN_CHANGES = [
    "berubah", "perubahan", "change", "different", "beda",
]

_PATTERN_FAILURES = [
    "gagal", "failure", "error", "masalah", "problem", "salah",
]

_PATTERN_SUCCESSES = [
    "berhasil", "success", "sukses", "selesai", "done", "completed",
]


class TimelineQueryEngine:
    """Answers conversational timeline queries using structured reads."""

    def __init__(self, timeline_store: Optional[object] = None) -> None:
        self._store = timeline_store

    # ── Query classification ──────────────────────────────────────────

    def classify(self, query: str) -> str:
        """Determine which timeline query type a natural question maps to."""
        q = query.lower().strip()

        for pat in _PATTERN_TODAY:
            if pat in q:
                return "today"
        for pat in _PATTERN_RECENT:
            if pat in q:
                return "recent"
        for pat in _PATTERN_LATEST:
            if pat in q:
                return "latest"
        for pat in _PATTERN_CHANGES:
            if pat in q:
                return "changes"
        for pat in _PATTERN_FAILURES:
            if pat in q:
                return "failures"
        for pat in _PATTERN_SUCCESSES:
            if pat in q:
                return "successes"

        return "recent"  # sensible default

    # ── Execute ───────────────────────────────────────────────────────

    def execute(self, query: str) -> TimelineQueryResult:
        """Classify and execute a natural-language timeline query."""
        qtype = self.classify(query)
        store = self._store

        now = datetime.now()

        if qtype == "today":
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            events = self._fetch_events_since(store, start_of_day) if store else []
            summary = f"{len(events)} events since {start_of_day.strftime('%H:%M')}"

        elif qtype == "recent":
            since = now - timedelta(minutes=30)
            events = self._fetch_events_since(store, since) if store else []
            summary = f"{len(events)} events in the last 30 minutes"

        elif qtype == "latest":
            events = self._fetch_latest_events(store, limit=5) if store else []
            summary = f"{len(events)} most recent events"

        elif qtype == "changes":
            since = now - timedelta(hours=1)
            events = self._fetch_events_since(store, since) if store else []
            # Filter to change-type events
            events = [e for e in events if self._is_change_event(e)]
            summary = f"{len(events)} changes in the last hour"

        elif qtype == "failures":
            since = now - timedelta(hours=24)
            events = self._fetch_events_since(store, since) if store else []
            events = [e for e in events if self._is_failure_event(e)]
            summary = f"{len(events)} failures in the last 24 hours"

        elif qtype == "successes":
            since = now - timedelta(hours=24)
            events = self._fetch_events_since(store, since) if store else []
            events = [e for e in events if self._is_success_event(e)]
            summary = f"{len(events)} successes in the last 24 hours"

        else:
            events = []
            summary = "No matching timeline events found."

        return TimelineQueryResult(
            query_type=qtype,
            events=events,
            count=len(events),
            summary=summary,
            period_start=str(now - timedelta(hours=24)),
            period_end=str(now),
        )

    # ── Internal fetchers (duck-typed against TimelineStore contract) ─

    @staticmethod
    def _fetch_events_since(store: object, since: datetime) -> list[dict]:
        """Try to read events from store; return empty list on failure."""
        try:
            # Attempt common TimelineStore interfaces
            if hasattr(store, "get_events_since"):
                raw = store.get_events_since(since)
            elif hasattr(store, "list_events"):
                raw = store.list_events(since=since)
            elif hasattr(store, "get_all"):
                raw = store.get_all()
            else:
                return []

            # Normalize to list of dicts
            result = []
            for event in (raw or []):
                if isinstance(event, dict):
                    result.append(event)
                elif hasattr(event, "__dict__"):
                    result.append(event.__dict__)
                else:
                    result.append({"id": str(event), "description": str(event)})
            return result
        except Exception:
            return []

    @staticmethod
    def _fetch_latest_events(store: object, limit: int = 5) -> list[dict]:
        try:
            if hasattr(store, "get_latest"):
                raw = store.get_latest(limit)
            elif hasattr(store, "list_events"):
                raw = store.list_events(limit=limit)
            elif hasattr(store, "get_all"):
                raw = store.get_all()[:limit]
            else:
                return []

            result = []
            for event in (raw or []):
                if isinstance(event, dict):
                    result.append(event)
                elif hasattr(event, "__dict__"):
                    result.append(event.__dict__)
                else:
                    result.append({"id": str(event), "description": str(event)})
            return result
        except Exception:
            return []

    # ── Event classifiers ─────────────────────────────────────────────

    @staticmethod
    def _is_change_event(event: dict) -> bool:
        desc = str(event.get("description", "")).lower()
        etype = str(event.get("event_type", "")).lower()
        return any(kw in desc or kw in etype for kw in [
            "change", "berubah", "update", "modified", "config",
        ])

    @staticmethod
    def _is_failure_event(event: dict) -> bool:
        desc = str(event.get("description", "")).lower()
        etype = str(event.get("event_type", "")).lower()
        status = str(event.get("status", "")).lower()
        return any(kw in desc or kw in etype or kw in status for kw in [
            "fail", "gagal", "error", "crash", "timeout", "reject",
        ])

    @staticmethod
    def _is_success_event(event: dict) -> bool:
        desc = str(event.get("description", "")).lower()
        etype = str(event.get("event_type", "")).lower()
        status = str(event.get("status", "")).lower()
        return any(kw in desc or kw in etype or kw in status for kw in [
            "success", "berhasil", "selesai", "completed", "ok",
        ])
