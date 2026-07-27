"""
Experience Engine — layer ViewModel antara Operations Engine dan UI.

UI TIDAK boleh membaca Runtime atau Telemetry langsung.
UI hanya membaca Experience.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# ============================================================================
# ViewModel — Bahasa Manusia
# ============================================================================

class SystemStatus(str, Enum):
    HEALTHY = "healthy"
    ATTENTION = "attention"
    PROBLEM = "problem"
    RECOVERING = "recovering"
    LEARNING = "learning"


@dataclass(frozen=True)
class SystemHealth:
    """Apakah sistem sehat?"""
    status: SystemStatus
    message: str  # "SAM is Healthy"
    detail: str   # "Everything is operating normally."
    health_score: float = 100.0


@dataclass(frozen=True)
class ActivityItem:
    """Aktivitas yang baru terjadi."""
    time: str  # "09:31"
    description: str  # "Started monitoring OpenClaw"


@dataclass(frozen=True)
class CurrentActivity:
    """Apa yang sedang terjadi?"""
    title: str  # "Monitoring Runtime"
    description: str = ""
    activity_log: List[ActivityItem] = field(default_factory=list)


@dataclass(frozen=True)
class AttentionItem:
    """Apakah saya harus melakukan sesuatu?"""
    needs_attention: bool
    message: str  # "No action required" or "Approval required"
    action: Optional[str] = None  # "Review", "Approve", "Restart"
    reason: Optional[str] = None


@dataclass(frozen=True)
class RecommendationItem:
    """Apa rekomendasi berikutnya?"""
    message: str  # "Nothing recommended."
    confidence: Optional[float] = None
    action: Optional[str] = None


@dataclass(frozen=True)
class Purpose:
    """Tujuan sistem."""
    name: str  # "Protect OpenClaw Workspace"
    status: str = "active"


@dataclass(frozen=True)
class HomeExperience:
    """Ringkasan halaman Home."""
    health: SystemHealth
    purpose: Purpose
    current_activity: CurrentActivity
    attention: AttentionItem
    recommendations: List[RecommendationItem]


@dataclass(frozen=True)
class TimelineEntry:
    """Satu baris timeline."""
    time: str  # "09:31"
    description: str  # "Started monitoring OpenClaw"
    details: Optional[str] = None  # muncul saat klik "More details"


@dataclass(frozen=True)
class TimelineGroup:
    """Kelompok timeline per hari."""
    label: str  # "Today", "Yesterday", "Earlier"
    entries: List[TimelineEntry]


@dataclass(frozen=True)
class ActivityExperience:
    """Halaman Activity — Timeline."""
    groups: List[TimelineGroup]


@dataclass(frozen=True)
class WorkStep:
    """Satu langkah pekerjaan."""
    name: str
    active: bool = False
    completed: bool = False


@dataclass(frozen=True)
class WorkProgress:
    """Progress pekerjaan."""
    current_step: int
    total_steps: int
    percent: int
    estimated_remaining: Optional[str] = None  # "2 minutes remaining"


@dataclass(frozen=True)
class WorkItem:
    """Satu pekerjaan."""
    title: str  # "Recover OpenClaw"
    status: str  # "Running", "Completed", "Failed", "Review required"
    progress: WorkProgress
    steps: List[WorkStep]
    approval_needed: bool = False
    approval_reason: Optional[str] = None


@dataclass(frozen=True)
class WorkExperience:
    """Halaman Work."""
    items: List[WorkItem]


@dataclass(frozen=True)
class LearnedItem:
    """Satu hal yang SAM pelajari."""
    title: str
    confidence: Optional[float] = None  # 93%
    severity: str = "info"  # "info", "warning", "recommendation"
    timestamp: Optional[str] = None  # "Today", "Yesterday"


@dataclass(frozen=True)
class KnowledgeExperience:
    """Halaman Knowledge — Things SAM Learned."""
    items: List[LearnedItem]


@dataclass(frozen=True)
class HistoryStory:
    """Satu cerita dalam history."""
    label: str  # "Yesterday", "2 days ago"
    events: List[str]  # ["Recovered OpenClaw", "Saved new lesson", ...]


@dataclass(frozen=True)
class HistoryExperience:
    """Halaman History."""
    stories: List[HistoryStory]


@dataclass(frozen=True)
class SettingsGroup:
    """Kelompok pengaturan."""
    name: str  # "Runtime", "Guardian", "Safety", etc.
    settings: Dict[str, str]  # {"Mode": "Autonomous", "Level": "3"}
    editable: bool = True


@dataclass(frozen=True)
class SettingsExperience:
    """Halaman Settings."""
    groups: List[SettingsGroup]


@dataclass(frozen=True)
class NotificationItem:
    """Satu notifikasi."""
    type: str  # "approval", "recommendation", "policy", "update", "recovery"
    message: str
    timestamp: str  # "09:31"
    action: Optional[str] = None


@dataclass(frozen=True)
class NotificationExperience:
    """Halaman Notification — Inbox."""
    items: List[NotificationItem]


@dataclass(frozen=True)
class AssistantAnswer:
    """Satu jawaban dari Assistant."""
    question: str
    answer: str
    details: Optional[str] = None
    action: Optional[str] = None


@dataclass(frozen=True)
class AssistantExperience:
    """Halaman Assistant."""
    answers: List[AssistantAnswer]
