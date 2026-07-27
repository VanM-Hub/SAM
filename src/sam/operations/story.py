"""
Activity Story Builder — Mission-Centric.

Cerita tentang perubahan pada Mission Target.
BUKAN tentang SAM.

Contoh:
  'Workspace deployment completed successfully.'
  'A new deployment pattern was identified.'
  'A failure was prevented. Rollback completed automatically.'
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class StoryType(str, Enum):
    DEPLOYMENT_COMPLETE = "deployment_complete"
    DEPLOYMENT_FAILED = "deployment_failed"
    PROTECTION_TRIGGERED = "protection_triggered"
    ROLLBACK_COMPLETED = "rollback_completed"
    PATTERN_IDENTIFIED = "pattern_identified"
    APPROVAL_NEEDED = "approval_needed"
    PLUGIN_UPDATE = "plugin_update"
    SYSTEM_EVENT = "system_event"


STORY_TITLES = {
    StoryType.DEPLOYMENT_COMPLETE: "{} completed successfully.",
    StoryType.DEPLOYMENT_FAILED: "{} could not be completed.",
    StoryType.PROTECTION_TRIGGERED: "A failure was prevented.",
    StoryType.ROLLBACK_COMPLETED: "Automatic rollback completed successfully.",
    StoryType.PATTERN_IDENTIFIED: "A new deployment pattern was identified.",
    StoryType.APPROVAL_NEEDED: "Approval required to continue.",
    StoryType.PLUGIN_UPDATE: "Plugin update completed.",
    StoryType.SYSTEM_EVENT: "System event recorded.",
}


@dataclass
class Story:
    """Satu cerita tentang perubahan pada Mission Target."""
    story_type: StoryType
    title: str
    summary: str
    target: str = ""                 # "workspace deployment", "plugin"
    duration: str = ""
    status: str = "success"
    icon: str = "\u2705"
    event_count: int = 1
    details: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class StoryBuilder:
    """Membangun cerita tentang Mission Target — bukan tentang SAM."""

    def build_stories(self, activity_model) -> List[Story]:
        """Bangun cerita dari Activity Model."""
        stories = []

        if not activity_model or not activity_model.groups:
            return stories

        for group in activity_model.groups[:5]:
            entries = group.entries
            if not entries:
                continue

            grouped = self._group_by_target(entries)
            for target_name, event_list in grouped.items():
                story = self._build(target_name, event_list)
                if story:
                    stories.append(story)

        return stories

    @staticmethod
    def _group_by_target(entries) -> dict:
        groups = {}
        for entry in entries:
            desc = entry.description if hasattr(entry, 'description') else str(entry)
            name = desc.split()[0] if desc else "unknown"
            if name not in groups:
                groups[name] = []
            groups[name].append(entry)
        return groups

    @staticmethod
    def _build(target_name: str, events: list) -> Optional[Story]:
        if not events:
            return None

        has_error = False
        has_recovery = False
        descriptions = []

        for e in events:
            desc = e.description if hasattr(e, 'description') else str(e)
            descriptions.append(desc)
            if any(w in desc.lower() for w in ["failed", "error", "rollback", "crash"]):
                has_error = True
            if any(w in desc.lower() for w in ["recovery", "restart", "restored"]):
                has_recovery = True

        if has_error and has_recovery:
            st = StoryType.PROTECTION_TRIGGERED
            icon = "\U0001f504"
            status = "recovery"
        elif has_error:
            st = StoryType.DEPLOYMENT_FAILED
            icon = "\u274c"
            status = "failed"
        else:
            st = StoryType.DEPLOYMENT_COMPLETE
            icon = "\u2705"
            status = "success"

        target = target_name.lower()
        title = STORY_TITLES[st].format(target.capitalize()) if "{}" in STORY_TITLES[st] else STORY_TITLES[st]
        summary = title

        return Story(
            story_type=st,
            title=title,
            summary=summary,
            target=target,
            status=status,
            icon=icon,
            event_count=len(events),
        )
