"""
Activity Story Builder — event groups jadi CERITA, bukan daftar.

Contoh:
  Workflow Started + Task Created + Plugin Loaded + Task Finished + Workflow Finished
  → "Deploy completed. Duration 2m 14s. Everything completed successfully."

BUKAN lima event.
SATU cerita.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional
from enum import Enum

from ..narrative.models import Narrative, NarrativeImportance, NarrativeType


class StoryType(str, Enum):
    WORKFLOW_COMPLETE = "workflow_complete"
    WORKFLOW_FAILED = "workflow_failed"
    PROTECTION_TRIGGERED = "protection_triggered"
    ROLLBACK_COMPLETED = "rollback_completed"
    LEARNING_DISCOVERY = "learning_discovery"
    APPROVAL_NEEDED = "approval_needed"
    PLUGIN_UPDATE = "plugin_update"
    SYSTEM_HEALTH = "system_health"
    GENERAL_ACTIVITY = "general_activity"


@dataclass
class ActivityStory:
    """Satu cerita dari sekelompok event."""
    story_type: StoryType
    title: str                      # "Deploy completed"
    summary: str                    # "Duration 2m 14s. Everything completed successfully."
    details: str = ""               # Level 2 (diklik)
    duration: str = ""              # "2m 14s"
    status: str = "success"         # success | failed | recovery | info
    icon: str = "\u2705"
    narrative: Optional[Narrative] = None
    event_count: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


STORY_SIGNATURES = {
    # (keywords) -> (StoryType, title_template, icon)
    "workflow_complete": (["workflow", "finished", "completed"], StoryType.WORKFLOW_COMPLETE, 1),
    "workflow_failed": (["workflow", "failed", "error", "rollback"], StoryType.WORKFLOW_FAILED, 0),
    "protection": (["protection", "guardian", "recovery", "restart"], StoryType.PROTECTION_TRIGGERED, 2),
    "learning": (["learned", "knowledge", "pattern", "insight"], StoryType.LEARNING_DISCOVERY, 3),
    "approval": (["approval", "approve", "review"], StoryType.APPROVAL_NEEDED, 4),
    "plugin": (["plugin", "update", "load", "unload"], StoryType.PLUGIN_UPDATE, 5),
}

DURATION_PATTERNS = [
    "duration", "took", "completed in", "finished in",
]


class ActivityStoryBuilder:
    """Mengelompokkan event menjadi cerita."""

    def __init__(self):
        pass

    def build_stories(self, activity_model) -> List[ActivityStory]:
        """Bangun cerita dari Activity Model."""
        stories = []

        if not activity_model or not activity_model.groups:
            return stories

        for group in activity_model.groups[:5]:
            entries = group.entries
            if not entries:
                continue

            # Coba kelompokkan
            grouped = self._group_entries(entries)
            for title, event_list in grouped.items():
                story = self._build_single_story(title, event_list)
                if story:
                    stories.append(story)

        return stories

    def _group_entries(self, entries) -> dict:
        """Kelompokkan event berdasarkan kemiripan judul."""
        groups = {}
        for entry in entries:
            desc = entry.description.lower() if hasattr(entry, 'description') else str(entry).lower()
            # Cari nama workflow/project dari deskripsi
            name = self._extract_name(entry)
            if name not in groups:
                groups[name] = []
            groups[name].append(entry)
        return groups

    def _extract_name(self, entry) -> str:
        """Ekstrak nama dari entry."""
        desc = entry.description if hasattr(entry, 'description') else str(entry)
        # Ambil kata setelah 'workflow' atau sebelum 'started/finished'
        words = desc.split()
        for i, w in enumerate(words):
            if w.lower() == "workflow" and i + 1 < len(words):
                return words[i + 1].strip("'\".")
            if w.lower() in ("started", "create", "load") and i > 0:
                return words[i - 1].strip("'\".")
        return desc[:20]

    def _build_single_story(self, name: str, events: list) -> Optional[ActivityStory]:
        """Buat satu cerita dari grup event."""
        if not events:
            return None

        descriptions = []
        has_error = False
        has_recovery = False
        timestamps = []

        for e in events:
            desc = e.description if hasattr(e, 'description') else str(e)
            descriptions.append(desc.lower())

            if hasattr(e, 'time'):
                timestamps.append(e.time)

            if any(w in desc.lower() for w in ["failed", "error", "rollback", "crash"]):
                has_error = True
            if any(w in desc.lower() for w in ["recovery", "restart", "restored", "resume"]):
                has_recovery = True

        # Durasi
        duration = ""
        for e in events:
            desc = e.description if hasattr(e, 'description') else str(e)
            for pattern in DURATION_PATTERNS:
                if pattern in desc.lower():
                    # Ekstrak angka setelah pattern
                    rest = desc.lower().split(pattern, 1)[-1].strip()
                    duration = rest.split()[0] if rest else ""
                    break
            if duration:
                break

        # Tentukan jenis cerita
        if has_error and has_recovery:
            story_type = StoryType.PROTECTION_TRIGGERED
            status = "recovery"
            icon = "\U0001f504"
            title = "A failure was prevented."
            summary = "Rollback completed successfully. No manual action required."
            details = "An issue was detected and automatically recovered.\n\nEvents:\n" + "\n".join(
                "  - {}".format(e.description if hasattr(e, 'description') else str(e)[:60])
                for e in events
            )

        elif has_error:
            story_type = StoryType.WORKFLOW_FAILED
            status = "failed"
            icon = "\u274c"
            title = "One operation could not be completed."
            summary = "Recovery has already started."
            details = "Failed events:\n" + "\n".join(
                "  - {}".format(e.description if hasattr(e, 'description') else str(e)[:60])
                for e in events
            )

        elif has_recovery:
            story_type = StoryType.PROTECTION_TRIGGERED
            status = "recovery"
            icon = "\u2705"
            title = "A service was recovered."
            summary = "Everything is stable again."
            details = "Recovery events:\n" + "\n".join(
                "  - {}".format(e.description if hasattr(e, 'description') else str(e)[:60])
                for e in events
            )

        else:
            story_type = StoryType.WORKFLOW_COMPLETE
            status = "success"
            icon = "\u2705"
            title = "{} completed".format(name)
            summary = "Everything completed successfully."
            if duration:
                summary = "Duration {}. Everything completed successfully.".format(duration)
            details = "Completed events:\n" + "\n".join(
                "  - {}".format(e.description if hasattr(e, 'description') else str(e)[:60])
                for e in events
            )

        narrative = Narrative(
            title=title,
            summary=summary,
            details=details,
            importance=(
                NarrativeImportance.ATTENTION
                if story_type in (StoryType.WORKFLOW_FAILED, StoryType.PROTECTION_TRIGGERED)
                else NarrativeImportance.INFORMATION
            ),
            narrative_type=NarrativeType.INCIDENT
            if story_type in (StoryType.WORKFLOW_FAILED, StoryType.PROTECTION_TRIGGERED)
            else NarrativeType.TASK_UPDATE,
        )

        return ActivityStory(
            story_type=story_type,
            title=title,
            summary=summary,
            details=details,
            duration=duration,
            status=status,
            icon=icon,
            narrative=narrative,
            event_count=len(events),
        )
