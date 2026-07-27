"""
DesktopContext — konteks Desktop dari Conversation, bukan ExperienceEngine.

Setiap halaman menerima Conversation (dari sam.observe()).
Tidak ada halaman yang query Runtime secara independen.
Semua data berasal dari Conversation.answer() dan Conversation.recommendations() dll.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime, timezone


# ============================================================================
# HumanTimeFormatter — "2 minutes ago", bukan timestamp
# ============================================================================

class HumanTimeFormatter:
    @staticmethod
    def format(dt: object) -> str:
        """Ubah datetime/timestamp ke bahasa manusia.

        Contoh: "Just now", "2 minutes ago", "Today", "Yesterday", "Monday"
        """
        if not dt:
            return ""

        # Jika string ISO
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                return dt

        now = datetime.now(timezone.utc) if dt.tzinfo else datetime.now()
        diff = now - dt

        if diff.total_seconds() < 10:
            return "Just now"
        if diff.total_seconds() < 60:
            return "Just now"
        if diff.total_seconds() < 3600:
            mins = int(diff.total_seconds() / 60)
            return f"{mins} minute{'s' if mins > 1 else ''} ago"
        if diff.total_seconds() < 7200:
            return "1 hour ago"
        if diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hours ago"

        # Cek Today/Yesterday
        today = now.date()
        if isinstance(dt, datetime):
            dt_date = dt.date()
        else:
            dt_date = dt.date() if hasattr(dt, 'date') else today

        if dt_date == today:
            return "Today"
        if dt_date == today.replace(day=today.day - 1):
            return "Yesterday"

        # Hari dalam minggu ini
        days_ago = (today - dt_date).days
        if days_ago < 7:
            return dt.strftime("%A")  # Monday, Tuesday, etc.

        return dt.strftime("%d %b")  # "28 Jul"


# ============================================================================
# DesktopContext — konteks desktop dari Conversation
# ============================================================================

@dataclass
class DesktopContext:
    """Konteks operasional untuk Desktop Console.

    Dibangun dari Conversation — bukan dari ExperienceEngine.
    """
    # Mission
    mission_name: str = "Protect OpenClaw Runtime"
    mission_status: str = "active"

    # Status
    status_label: str = "Healthy"
    status_color: str = "#4ae04a"
    status_detail: str = "Everything is operating normally."

    # Attention
    attention_count: int = 0
    attention_message: str = ""
    attention_reason: str = ""

    # Activity
    last_activity_time: str = ""
    last_activity_description: str = ""

    # Work
    active_work_count: int = 0
    pending_approval_count: int = 0

    # Notifications
    unread_count: int = 0
    recent_notifications: list = field(default_factory=list)

    # Health
    health_score: float = 100.0
    protection_level: str = "healthy"
    protection_summary: str = "All systems healthy."

    # Timestamps
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def needs_attention(self) -> bool:
        return self.attention_count > 0 or self.pending_approval_count > 0


class DesktopContextBuilder:
    """Membangun DesktopContext dari Conversation — bukan ExperienceEngine."""

    def __init__(self, conversation):
        self._conversation = conversation
        self._time = HumanTimeFormatter()

    def build(self) -> DesktopContext:
        """Bangun konteks terkini dari Conversation."""
        try:
            # ================================================================
            # SATU SUMBER — Conversation.answer() dan recommendations()
            # ================================================================

            # Overview — status sistem
            overview = self._conversation.answer("What's happening?")
            health = self._conversation.health()
            recs = self._conversation.recommendations()
            user_actions = self._conversation.actions()

            # Status
            title_lower = (overview.title or "").lower()
            status_map = [
                ("action", ("Action Required", "#e06a6a")),
                ("attention", ("Attention", "#e0c06a")),
                ("approval", ("Attention", "#e0c06a")),
                ("recovery", ("Recovering", "#e0a06a")),
                ("progress", ("Deploying", "#6aaae0")),
                ("learning", ("Learning", "#6aaae0")),
                ("normal", ("Healthy", "#4ae04a")),
            ]
            status_label, status_color = "Healthy", "#4ae04a"
            for key, val in status_map:
                if key in title_lower:
                    status_label, status_color = val
                    break

            # Attention count
            att_count = 1 if any(
                s in title_lower for s in ["action", "attention", "approval", "required"]
            ) else 0
            att_msg = (
                overview.user_action_needed
                or (user_actions.actions[0] if user_actions and user_actions.actions else "")
            )
            att_reason = overview.summary or ""

            # Active work / pending approval dari recommendations
            active_count = 0
            pending_approval = 0
            if recs:
                active_count = len(recs.recommendations) if recs.recommendations else 0
                for rec in (recs.recommendations or []):
                    if "approve" in rec.lower():
                        pending_approval += 1

            # Notifications
            unread = 0
            if overview and overview.badges:
                unread = len([b for b in overview.badges if "action" in b[0].lower()])

            return DesktopContext(
                mission_name="Protect OpenClaw Runtime",
                mission_status="active",
                status_label=status_label,
                status_color=status_color,
                status_detail=overview.summary or "",
                attention_count=att_count + pending_approval,
                attention_message=att_msg,
                attention_reason=att_reason,
                last_activity_time="",
                last_activity_description=(
                    overview.sections[0][1][:50] if overview.sections
                    else (overview.summary or "")[:50]
                ),
                active_work_count=active_count,
                pending_approval_count=pending_approval,
                unread_count=unread,
                recent_notifications=[],
                health_score=health.severity_score if hasattr(health, 'severity_score') else 100.0,
                protection_summary=health.summary or "All systems healthy.",
            )

        except Exception as e:
            return DesktopContext(
                status_label="Unknown",
                status_color="#606070",
                status_detail=f"Unable to retrieve runtime information: {str(e)}",
            )
