"""
Narrative Engine — Layer yang mengubah Experience Model menjadi cerita.

Runtime tidak berubah.
Telemetry tidak berubah.
Experience Engine tidak berubah.

Yang berubah: bagaimana informasi disampaikan.

Prinsip:
    Jangan tampilkan apa yang diketahui Runtime.
    Tampilkan apa yang dibutuhkan manusia.

Narrative Engine adalah single source untuk semua user-facing language:
Desktop, CLI, Web, Email, Notifications, Voice, future LLM.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# ============================================================================
# Importance — UX concepts, bukan Runtime severity
# ============================================================================

class NarrativeImportance(str, Enum):
    """Tingkat kepentingan dari perspektif manusia.

    BUKAN Runtime severity. Ini adalah UX concept.
    """
    INFORMATION = "information"       # "FYI, nothing to do"
    ATTENTION = "attention"            # "You should know this"
    ACTION_REQUIRED = "action_required"  # "You need to do something"
    CRITICAL = "critical"              # "Stop what you're doing"


# ============================================================================
# Narrative Types
# ============================================================================

class NarrativeType(str, Enum):
    DAILY_SUMMARY = "daily_summary"
    INCIDENT = "incident"
    RECOVERY = "recovery"
    WARNING = "warning"
    RECOMMENDATION = "recommendation"
    LEARNING = "learning"
    APPROVAL_NEEDED = "approval_needed"
    MISSION_UPDATE = "mission_update"
    HEALTH_UPDATE = "health_update"
    TASK_UPDATE = "task_update"


# ============================================================================
# Narrative — Immutable Model
# ============================================================================

@dataclass(frozen=True)
class Narrative:
    """Sebuah cerita.

    Attributes:
        title: Judul — 3-8 kata, langsung bisa dipahami
        summary: Ringkasan — 1-2 kalimat, inti cerita
        details: Detail opsional — muncul saat user klik
        importance: INFORMATION | ATTENTION | ACTION_REQUIRED | CRITICAL
        narrative_type: Jenis cerita (daily_summary, incident, etc.)
        action_required: Apakah user harus melakukan sesuatu?
        recommended_action: Apa yang harus dilakukan? (None jika tidak perlu)
        estimated_impact: Dampak yang diperkirakan
        estimated_time: Perkiraan waktu
        confidence: Keyakinan (0.0 - 1.0)
        related_items: Item terkait (ID)
        created_at: Waktu cerita dibuat
    """
    title: str
    summary: str
    details: str = ""
    importance: NarrativeImportance = NarrativeImportance.INFORMATION
    narrative_type: NarrativeType = NarrativeType.HEALTH_UPDATE
    action_required: bool = False
    recommended_action: str = ""
    estimated_impact: str = ""
    estimated_time: str = ""
    confidence: float = 1.0
    related_items: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================================================
# NarrativeBundle — Kumpulan narrative untuk satu konteks
# ============================================================================

@dataclass(frozen=True)
class NarrativeBundle:
    """Kumpulan narrative untuk satu tampilan.

    Contoh: Daily briefing berisi beberapa Narrative.
    """
    primary: Optional[Narrative] = None
    supporting: List[Narrative] = field(default_factory=list)
    attention_count: int = 0
    action_count: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================================================
# Briefing Types
# ============================================================================

@dataclass(frozen=True)
class DailyBriefing:
    """Briefing pagi — apa yang perlu diketahui hari ini."""
    greeting: str  # "Good morning."
    health_summary: str  # "Everything is healthy."
    yesterday_recap: str  # "Yesterday SAM automatically recovered..."
    action_summary: str  # "No action is required."
    schedule: List[str] = field(default_factory=list)  # "• Backup 14:00"
    narratives: List[Narrative] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True)
class SituationBrief:
    """Situasi saat ini — apa yang sedang terjadi."""
    summary: str  # "Everything is operating normally."
    health_statement: str  # "Runtime healthy."
    knowledge_statement: str  # "Knowledge synchronized."
    incident_statement: str  # "No incidents detected."
    work_statement: str  # "2 workflows currently running."
    narratives: List[Narrative] = field(default_factory=list)


@dataclass(frozen=True)
class IncidentStory:
    """Cerita insiden — kronologi manusia, bukan log."""
    title: str
    what_happened: str  # "At 14:22, OpenClaw stopped responding."
    what_sam_did: str  # "SAM retried three times."
    outcome: str  # "Recovery succeeded after 17 seconds."
    current_state: str  # "Service is healthy again."
    narrative: Optional[Narrative] = None


@dataclass(frozen=True)
class RecommendationStory:
    """Rekomendasi — narasi, bukan angka."""
    situation: str  # "Memory usage has slowly increased..."
    risk: str  # "No risk exists today."
    recommendation: str  # "SAM recommends restarting OpenClaw tonight..."
    narrative: Optional[Narrative] = None
