"""
Action — model domain untuk unit eksekusi terkecil.

Immutable.
Belum ada executor.
Belum ada execute().
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass(frozen=True)
class Action:
    """Unit terkecil dari eksekusi.

    Immutable — tidak bisa diubah setelah dibuat.
    Hanya bisa dibaca oleh Conversation.
    """

    id: str
    title: str
    description: str = ""
    category: str = "general"        # system, database, network, filesystem, container
    severity: str = "information"     # information, warning, critical

    estimated_duration_seconds: int = 30
    requires_confirmation: bool = True
    rollback_available: bool = True
    verification_required: bool = True

    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_text(self) -> str:
        lines = [
            "Action: {}".format(self.title),
            "  Category: {} | Severity: {}".format(self.category, self.severity),
            "  Duration: ~{}s".format(self.estimated_duration_seconds),
            "  Requires confirmation: {}".format(self.requires_confirmation),
            "  Rollback available: {}".format(self.rollback_available),
            "  Verification required: {}".format(self.verification_required),
        ]
        if self.description:
            lines.append("  Description: {}".format(self.description))
        if self.tags:
            lines.append("  Tags: {}".format(", ".join(self.tags)))
        if self.id:
            lines.append("  ID: {}".format(self.id))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "severity": self.severity,
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "requires_confirmation": self.requires_confirmation,
            "rollback_available": self.rollback_available,
            "verification_required": self.verification_required,
            "tags": self.tags,
            "metadata": self.metadata,
        }


# Factory untuk Action standar
class ActionFactory:

    @staticmethod
    def restart_service(name: str = "web") -> Action:
        return Action(
            id="",
            title="Restart {} service".format(name),
            description="Graceful restart of {} service — connections drained first".format(name),
            category="system",
            severity="warning",
            estimated_duration_seconds=30,
            requires_confirmation=True,
            rollback_available=True,
            verification_required=True,
            tags=["restart", name],
        )

    @staticmethod
    def free_disk_space(min_mb: int = 500) -> Action:
        return Action(
            id="",
            title="Free up disk space ({} MB+)".format(min_mb),
            description="Remove temporary files and old logs to reclaim {} MB".format(min_mb),
            category="filesystem",
            severity="warning",
            estimated_duration_seconds=60,
            requires_confirmation=True,
            rollback_available=False,   # cannot undo deletion
            verification_required=True,
            tags=["cleanup", "disk"],
        )

    @staticmethod
    def clear_cache() -> Action:
        return Action(
            id="",
            title="Clear system cache",
            description="Flush outdated cache entries — expects temporary performance degradation",
            category="system",
            severity="warning",
            estimated_duration_seconds=10,
            requires_confirmation=True,
            rollback_available=False,
            verification_required=True,
            tags=["cache", "cleanup"],
        )

    @staticmethod
    def restart_database() -> Action:
        return Action(
            id="",
            title="Restart database connection",
            description="Force restart database connection — ~5s interruption for active queries",
            category="database",
            severity="critical",
            estimated_duration_seconds=10,
            requires_confirmation=True,
            rollback_available=True,
            verification_required=True,
            tags=["database", "restart"],
        )

    @staticmethod
    def scale_workers(count: int = 2) -> Action:
        return Action(
            id="",
            title="Scale workers to {}".format(count),
            description="Increase worker pool to {} to handle queue growth".format(count),
            category="system",
            severity="information",
            estimated_duration_seconds=15,
            requires_confirmation=True,
            rollback_available=True,
            verification_required=True,
            tags=["scaling", "workers"],
        )

    @staticmethod
    def investigate_anomaly(anomaly_type: str = "") -> Action:
        return Action(
            id="",
            title="Investigate anomaly: {}".format(anomaly_type),
            description="Collect diagnostic data for {}".format(anomaly_type),
            category="general",
            severity="information",
            estimated_duration_seconds=120,
            requires_confirmation=False,
            rollback_available=False,
            verification_required=False,
            tags=["investigate", anomaly_type],
        )
