"""
ExperienceContext — satu konteks untuk seluruh Desktop Console.

Setiap halaman menerima ExperienceContext yang sama.
Tidak ada halaman yang query Runtime secara independen.
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
# ExperienceContext — satu konteks untuk semua halaman
# ============================================================================

@dataclass
class ExperienceContext:
    """Konteks operasional yang sama untuk semua halaman.

    Tidak ada halaman yang query Runtime secara independen.
    Semua data berasal dari Experience Engine → Narrative Engine.
    """
    # Mission
    mission_name: str = "Protect OpenClaw Runtime"
    mission_status: str = "active"

    # Status
    status_label: str = "Healthy"      # "Healthy" | "Attention" | "Problem" | "Recovering"
    status_color: str = "#4ae04a"      # Hijau / Kuning / Merah
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


class ExperienceContextBuilder:
    """Membangun ExperienceContext dari Experience Engine."""

    def __init__(self, experience_engine):
        self._ee = experience_engine
        self._time = HumanTimeFormatter()

    def build(self) -> ExperienceContext:
        """Bangun konteks terkini."""
        try:
            home = self._ee.build_home()
            narrative = self._ee.build_narrative_home()
            work = self._ee.build_work()

            # Status
            status = home.health.status.value if home.health else "healthy"
            status_map = {
                "healthy": ("Healthy", "#4ae04a"),
                "recovering": ("Recovering", "#e0c06a"),
                "attention": ("Attention", "#e0c06a"),
                "problem": ("Problem", "#e06a6a"),
                "learning": ("Learning", "#6aaae0"),
            }
            status_label, status_color = status_map.get(status, ("Healthy", "#4ae04a"))

            # Attention
            att_count = narrative.attention_count if narrative else 0
            att_msg = ""
            att_reason = ""
            if home.attention and home.attention.needs_attention:
                att_msg = home.attention.message or ""
                att_reason = home.attention.reason or ""

            # Last activity
            last_time = ""
            last_desc = ""
            try:
                activity = self._ee.build_activity()
                if activity and activity.groups:
                    entries = activity.groups[0].entries
                    if entries:
                        last_entry = entries[0]
                        last_time = last_entry.time
                        last_desc = last_entry.description
            except Exception:
                pass

            # Work
            active_count = 0
            pending_approval = 0
            if work and work.items:
                for w in work.items:
                    if w.status == "running":
                        active_count += 1
                    if w.approval_needed:
                        pending_approval += 1

            # Notifications
            unread = 0
            notif_items = []
            try:
                notif_model = self._ee.build_notifications()
                if notif_model and notif_model.items:
                    for n in notif_model.items[:5]:
                        if n.type != "info" or n.message != "No notifications":
                            notif_items.append(n)
                    unread = len(notif_items)
            except Exception:
                pass

            return ExperienceContext(
                mission_name="Protect OpenClaw Runtime",
                mission_status="active",
                status_label=status_label,
                status_color=status_color,
                status_detail=home.health.detail if home.health else "",
                attention_count=att_count + pending_approval,
                attention_message=att_msg,
                attention_reason=att_reason,
                last_activity_time=last_time,
                last_activity_description=last_desc,
                active_work_count=active_count,
                pending_approval_count=pending_approval,
                unread_count=unread,
                recent_notifications=notif_items,
                health_score=home.health.health_score if home.health else 100.0,
                protection_level=getattr(home.health, 'protection_level', ''),
                protection_summary=getattr(home.health, 'protection_summary', ''),
            )

        except Exception as e:
            return ExperienceContext(
                status_label="Unknown",
                status_color="#606070",
                status_detail=f"Unable to retrieve runtime information.",
            )
