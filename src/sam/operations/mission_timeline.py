"""
OP-124 — Mission Timeline.

Timeline immutable. Append only.
Setiap event punya timestamp + description.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass(frozen=True)
class TimelineEvent:
    """Satu event dalam timeline. Immutable."""
    event_type: str         # "MISSION_STARTED", "RECOMMENDATION", "APPROVED", dll
    description: str         # Deskripsi singkat
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "description": self.description,
            "timestamp": self.timestamp,
        }


@dataclass
class MissionTimeline:
    """Timeline untuk satu mission. Append-only.

    Tidak bisa dihapus atau diubah.
    """
    mission_id: str
    events: List[TimelineEvent] = field(default_factory=list)

    def add(self, event_type: str, description: str) -> TimelineEvent:
        """Tambah event. Append only."""
        event = TimelineEvent(
            event_type=event_type,
            description=description,
        )
        self.events.append(event)
        return event

    @property
    def count(self) -> int:
        return len(self.events)

    @property
    def last_event(self) -> Optional[TimelineEvent]:
        if self.events:
            return self.events[-1]
        return None

    def get_by_type(self, event_type: str) -> List[TimelineEvent]:
        """Filter event by type."""
        return [e for e in self.events if e.event_type == event_type]

    def to_dict(self) -> list:
        return [e.to_dict() for e in self.events]

    def to_text(self) -> str:
        lines = ["Timeline for {}:".format(self.mission_id)]
        for e in self.events:
            t = e.timestamp[11:19] if len(e.timestamp) > 19 else e.timestamp  # HH:MM:SS
            lines.append("  {}  {}  — {}".format(t, e.event_type.ljust(20), e.description))
        return "\n".join(lines)


class TimelineStore:
    """Store untuk semua timeline.

    Method:
      get_or_create(mission_id) -> MissionTimeline
      add_event(mission_id, event_type, description) -> bool
      get_timeline(mission_id) -> Optional[MissionTimeline]
      remove(mission_id) -> bool  # hanya jika mission sudah terminal
    """

    def __init__(self):
        self._timelines: Dict[str, MissionTimeline] = {}

    def get_or_create(self, mission_id: str) -> MissionTimeline:
        """Dapatkan timeline. Buat baru jika belum ada."""
        if mission_id not in self._timelines:
            self._timelines[mission_id] = MissionTimeline(mission_id=mission_id)
        return self._timelines[mission_id]

    def add_event(self, mission_id: str, event_type: str,
                  description: str) -> bool:
        """Tambah event ke timeline."""
        tl = self.get_or_create(mission_id)
        tl.add(event_type, description)
        return True

    def get_timeline(self, mission_id: str) -> Optional[MissionTimeline]:
        return self._timelines.get(mission_id)

    def remove(self, mission_id: str) -> bool:
        """Hapus timeline."""
        if mission_id in self._timelines:
            del self._timelines[mission_id]
            return True
        return False

    def list_all(self) -> List[str]:
        return list(self._timelines.keys())

    def reset(self):
        self._timelines.clear()
