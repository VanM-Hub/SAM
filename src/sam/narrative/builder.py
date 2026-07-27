"""
Narrative Builder — Menerjemahkan Experience Model menjadi Narrative.

Input: Experience Models (dari Experience Engine)
Output: Narrative, DailyBriefing, SituationBrief, IncidentStory, dll.

Tidak membaca Runtime.
Tidak membaca Telemetry.
HANYA membaca Experience Model.
"""

from typing import List, Optional
from datetime import datetime

from .models import (
    Narrative, NarrativeBundle, NarrativeImportance, NarrativeType,
    DailyBriefing, SituationBrief, IncidentStory, RecommendationStory,
)

# ============================================================================
# Helper — Templat Bahasa Manusia
# ============================================================================

IMPORTANCE_MAP = {
    "healthy": NarrativeImportance.INFORMATION,
    "attention": NarrativeImportance.ATTENTION,
    "problem": NarrativeImportance.ACTION_REQUIRED,
    "critical": NarrativeImportance.CRITICAL,
}

SEVERITY_MAP = {
    "info": NarrativeImportance.INFORMATION,
    "warning": NarrativeImportance.ATTENTION,
    "error": NarrativeImportance.ACTION_REQUIRED,
    "critical": NarrativeImportance.CRITICAL,
}


def _time_ago(created_at: str) -> str:
    """Ubah timestamp jadi kata-kata manusia."""
    try:
        dt = datetime.fromisoformat(created_at)
        now = datetime.now()
        diff = now - dt

        if diff.total_seconds() < 60:
            return "just now"
        if diff.total_seconds() < 3600:
            mins = int(diff.total_seconds() / 60)
            return f"{mins} minute{'s' if mins > 1 else ''} ago"
        if diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        days = int(diff.total_seconds() / 86400)
        return f"{days} day{'s' if days > 1 else ''} ago"
    except Exception:
        return ""


# ============================================================================
# Narrative Builder
# ============================================================================

class NarrativeBuilder:
    """Membangun Narrative dari Experience Model.

    Rule:
    - Never expose CPU%, stacktrace, UUID, Python module names
    - 3-8 lines max
    - Understand within 5 seconds
    - Link to Explanation (not duplicate)
    """

    def __init__(self):
        pass

    # ======================================================================
    # Build dari Home Experience
    # ======================================================================

    def build_from_home(self, home_model) -> NarrativeBundle:
        """Buat narrative dari Home Experience."""
        narratives = []

        # Health narrative
        health_narrative = self._build_health_narrative(home_model.health)
        if health_narrative:
            narratives.append(health_narrative)

        # Attention narrative
        if home_model.attention and home_model.attention.needs_attention:
            att_narrative = self._build_attention_narrative(home_model.attention)
            if att_narrative:
                narratives.append(att_narrative)

        # Recommendation narratives
        for rec in home_model.recommendations:
            if rec.message and rec.message != "Nothing recommended.":
                rec_narrative = Narrative(
                    title=rec.message[:50],
                    summary=rec.message,
                    importance=(
                        NarrativeImportance.ATTENTION
                        if rec.confidence and rec.confidence > 0.7
                        else NarrativeImportance.INFORMATION
                    ),
                    narrative_type=NarrativeType.RECOMMENDATION,
                    confidence=rec.confidence or 0.0,
                )
                narratives.append(rec_narrative)

        # Current activity narrative
        if home_model.current_activity and home_model.current_activity.title:
            act_narrative = Narrative(
                title=home_model.current_activity.title,
                summary="Currently: {}".format(home_model.current_activity.title),
                importance=NarrativeImportance.INFORMATION,
                narrative_type=NarrativeType.TASK_UPDATE,
            )
            narratives.append(act_narrative)

        # Hitung attention/action
        attention_count = sum(
            1 for n in narratives
            if n.importance in (NarrativeImportance.ATTENTION, NarrativeImportance.ACTION_REQUIRED)
        )
        action_count = sum(
            1 for n in narratives
            if n.action_required
        )

        primary = self._pick_primary(narratives)

        return NarrativeBundle(
            primary=primary,
            supporting=[n for n in narratives if n != primary],
            attention_count=attention_count,
            action_count=action_count,
        )

    # ======================================================================
    # Health Narrative
    # ======================================================================

    def _build_health_narrative(self, health) -> Optional[Narrative]:
        if not health:
            return None

        status = health.status.value if hasattr(health.status, 'value') else str(health.status)

        # Pilih bahasa manusia
        if status == "healthy":
            title = "Everything is operating normally."
            summary = "All systems healthy. No issues detected."
            importance = NarrativeImportance.INFORMATION
        elif status == "recovering":
            title = "The system is recovering from a recent issue."
            summary = "Systems are stabilizing. Monitoring continues."
            importance = NarrativeImportance.ATTENTION
        elif status in ("problem", "attention"):
            title = "The system needs your attention."
            summary = health.message or "One or more systems require review."
            importance = NarrativeImportance.ACTION_REQUIRED
        else:
            title = "The system is operating."
            summary = health.message or "Status unknown."
            importance = NarrativeImportance.INFORMATION

        # Tambahkan detail dari health
        detail = health.detail or ""
        protection = getattr(health, 'protection_summary', '')
        if protection:
            detail = detail or protection

        return Narrative(
            title=title,
            summary=summary,
            details=detail,
            importance=importance,
            narrative_type=NarrativeType.HEALTH_UPDATE,
        )

    # ======================================================================
    # Attention Narrative
    # ======================================================================

    def _build_attention_narrative(self, attention) -> Optional[Narrative]:
        if not attention or not attention.needs_attention:
            return None

        return Narrative(
            title="Attention required.",
            summary=attention.message or "Something needs your attention.",
            details=attention.reason or "",
            importance=NarrativeImportance.ATTENTION,
            narrative_type=NarrativeType.WARNING,
            action_required=True,
        )

    # ======================================================================
    # Build dari Activity Experience
    # ======================================================================

    def build_from_activity(self, activity_model) -> List[Narrative]:
        """Buat narrative dari Activity Timeline."""
        narratives = []

        if not activity_model or not activity_model.groups:
            return narratives

        # Ambil group terbaru
        latest = activity_model.groups[0] if activity_model.groups else None
        if not latest:
            return narratives

        for entry in latest.entries[:3]:
            narrative = Narrative(
                title=entry.description[:50],
                summary=entry.description,
                importance=NarrativeImportance.INFORMATION,
                narrative_type=NarrativeType.TASK_UPDATE,
            )
            narratives.append(narrative)

        return narratives

    # ======================================================================
    # Build dari Work Experience
    # ======================================================================

    def build_from_work(self, work_model) -> List[Narrative]:
        """Buat narrative dari Work items."""
        narratives = []

        if not work_model or not work_model.items:
            # Tidak ada pekerjaan
            narratives.append(Narrative(
                title="No active work.",
                summary="All tasks are completed. Nothing requires your attention.",
                importance=NarrativeImportance.INFORMATION,
                narrative_type=NarrativeType.TASK_UPDATE,
            ))
            return narratives

        # Approval needed
        for item in work_model.items[:3]:
            if item.approval_needed:
                narratives.append(Narrative(
                    title="Approval is needed to continue.",
                    summary="{} needs review.".format(item.title),
                    details=item.approval_reason or "",
                    importance=NarrativeImportance.ACTION_REQUIRED,
                    narrative_type=NarrativeType.APPROVAL_NEEDED,
                    action_required=True,
                    recommended_action="Approve or review in Work section.",
                    estimated_impact="No execution will continue until approval is given.",
                    estimated_time="About 2 minutes.",
                ))

            elif item.status == "running":
                progress = ""
                if item.progress:
                    progress = "Step {} of {} — {}% complete.".format(
                        item.progress.current_step,
                        item.progress.total_steps,
                        item.progress.percent,
                    )
                narratives.append(Narrative(
                    title="{} is in progress.".format(item.title),
                    summary=progress or "Work is ongoing.",
                    importance=NarrativeImportance.INFORMATION,
                    narrative_type=NarrativeType.TASK_UPDATE,
                ))

        return narratives

    # ======================================================================
    # Build Daily Briefing
    # ======================================================================

    def build_daily_briefing(self, home_model=None, activity_model=None,
                             work_model=None) -> DailyBriefing:
        """Briefing pagi."""
        narratives = []

        # Health
        if home_model and home_model.health:
            health_narrative = self._build_health_narrative(home_model.health)
            if health_narrative:
                narratives.append(health_narrative)

        # Work (scheduled)
        schedule = []
        if work_model and work_model.items:
            for item in work_model.items[:5]:
                if item.progress and item.progress.estimated_remaining:
                    schedule.append("• {} — {}".format(
                        item.title,
                        item.progress.estimated_remaining,
                    ))
                else:
                    schedule.append("• {}".format(item.title))

        # Greeting
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good morning."
        elif hour < 18:
            greeting = "Good afternoon."
        else:
            greeting = "Good evening."

        # Health summary
        healthy = (home_model and home_model.health.status.value == "healthy")
        if healthy:
            health_summary = "Everything is healthy."
        else:
            health_summary = "The system requires your attention."

        # Yesterday recap — dari activity model
        yesterday_recap = "No significant events from yesterday."
        if activity_model and activity_model.groups:
            yesterday_label = activity_model.groups[0].label if activity_model.groups else ""
            if "yesterday" in yesterday_label.lower() or "today" in yesterday_label.lower():
                entries = activity_model.groups[0].entries[:3]
                if entries:
                    yesterday_recap = "Recent activity:\n" + "\n".join(
                        "• {}".format(e.description) for e in entries
                    )

        # Action summary
        action_count = sum(1 for n in narratives if n.action_required)
        if action_count > 0:
            action_summary = "{} action{} require{} your attention.".format(
                action_count,
                "s" if action_count > 1 else "",
                "" if action_count == 1 else "",
            )
        else:
            action_summary = "No action is required."

        return DailyBriefing(
            greeting=greeting,
            health_summary=health_summary,
            yesterday_recap=yesterday_recap,
            action_summary=action_summary,
            schedule=schedule,
            narratives=narratives,
        )

    # ======================================================================
    # Build Situation Brief
    # ======================================================================

    def build_current_situation(self, home_model=None, work_model=None,
                                knowledge_model=None) -> SituationBrief:
        """Situasi saat ini."""
        narratives = []

        healthy = (home_model and home_model.health.status.value == "healthy")
        if healthy:
            summary = "Everything is operating normally."
            health_statement = "Runtime healthy."
        else:
            summary = "The system requires review."
            health_statement = "Runtime requires attention."

        # Knowledge
        knowledge_statement = "Knowledge synchronized."
        if knowledge_model and knowledge_model.items:
            knowledge_statement = "{} learning points recorded.".format(
                len(knowledge_model.items)
            )

        # Incidents
        incidents = []
        if home_model and home_model.attention and home_model.attention.needs_attention:
            incidents.append(home_model.attention.message)

        incident_statement = "No incidents detected."
        if incidents:
            incident_statement = "Incident: {}".format(incidents[0])

        # Work
        active_count = 0
        if work_model and work_model.items:
            active_count = sum(1 for w in work_model.items
                               if w.status == "running")
        work_statement = "{} workflow{} currently running.".format(
            active_count or "No",
            "s" if active_count != 1 else "",
        )

        return SituationBrief(
            summary=summary,
            health_statement=health_statement,
            knowledge_statement=knowledge_statement,
            incident_statement=incident_statement,
            work_statement=work_statement,
            narratives=narratives,
        )

    # ======================================================================
    # Build Incident Story
    # ======================================================================

    def build_incident_story(self, title: str, what_happened: str,
                             what_sam_did: str, outcome: str,
                             current_state: str) -> IncidentStory:
        """Cerita insiden."""
        narrative = Narrative(
            title=title,
            summary="{} {} {}".format(what_happened, what_sam_did, outcome),
            details="{} Current state: {}".format(outcome, current_state),
            importance=NarrativeImportance.ATTENTION,
            narrative_type=NarrativeType.INCIDENT,
        )
        return IncidentStory(
            title=title,
            what_happened=what_happened,
            what_sam_did=what_sam_did,
            outcome=outcome,
            current_state=current_state,
            narrative=narrative,
        )

    # ======================================================================
    # Build Recommendation Story
    # ======================================================================

    def build_recommendation(self, situation: str, risk: str,
                             recommendation: str,
                             importance=NarrativeImportance.ATTENTION) -> RecommendationStory:
        """Rekomendasi."""
        narrative = Narrative(
            title=recommendation[:50],
            summary="{} {} {}".format(situation, risk, recommendation),
            details="Risk: {}\nRecommendation: {}".format(risk, recommendation),
            importance=importance,
            narrative_type=NarrativeType.RECOMMENDATION,
            recommended_action=recommendation,
        )
        return RecommendationStory(
            situation=situation,
            risk=risk,
            recommendation=recommendation,
            narrative=narrative,
        )

    # ======================================================================
    # Build dari Knowledge
    # ======================================================================

    def build_from_knowledge(self, knowledge_model) -> List[Narrative]:
        """Apa yang SAM pelajari."""
        narratives = []

        if knowledge_model and knowledge_model.items:
            for item in knowledge_model.items[:5]:
                importance = NarrativeImportance.INFORMATION
                if getattr(item, 'severity', '') in ("warning", "recommendation"):
                    importance = NarrativeImportance.ATTENTION

                title = item.title
                if len(title) > 50:
                    title = title[:47] + "..."

                narratives.append(Narrative(
                    title=title,
                    summary=item.title,
                    importance=importance,
                    narrative_type=NarrativeType.LEARNING,
                    confidence=getattr(item, 'confidence', 0.0) or 0.0,
                ))

        return narratives

    # ======================================================================
    # Build dari Notifications
    # ======================================================================

    def build_from_notifications(self, notif_model) -> List[Narrative]:
        """Setiap notifikasi jadi Narrative."""
        narratives = []

        if notif_model and notif_model.items:
            for item in notif_model.items[:10]:
                if item.type == "info" and item.message == "No notifications":
                    continue

                imp_map = {
                    "approval": NarrativeImportance.ACTION_REQUIRED,
                    "recommendation": NarrativeImportance.ATTENTION,
                    "policy": NarrativeImportance.ATTENTION,
                    "update": NarrativeImportance.INFORMATION,
                    "recovery": NarrativeImportance.INFORMATION,
                }
                type_map = {
                    "approval": NarrativeType.APPROVAL_NEEDED,
                    "recommendation": NarrativeType.RECOMMENDATION,
                    "policy": NarrativeType.WARNING,
                    "update": NarrativeType.MISSION_UPDATE,
                    "recovery": NarrativeType.RECOVERY,
                }

                narratives.append(Narrative(
                    title=item.message[:50],
                    summary=item.message,
                    importance=imp_map.get(item.type, NarrativeImportance.INFORMATION),
                    narrative_type=type_map.get(item.type, NarrativeType.HEALTH_UPDATE),
                    action_required=(item.type == "approval"),
                ))

        return narratives

    # ======================================================================
    # Internal: Pilih primary narrative
    # ======================================================================

    @staticmethod
    def _pick_primary(narratives: List[Narrative]) -> Optional[Narrative]:
        """Pilih narrative paling penting untuk jadi primary."""
        if not narratives:
            return None

        order = {
            NarrativeImportance.CRITICAL: 0,
            NarrativeImportance.ACTION_REQUIRED: 1,
            NarrativeImportance.ATTENTION: 2,
            NarrativeImportance.INFORMATION: 3,
        }

        # Pilih yang paling penting
        best = narratives[0]
        for n in narratives[1:]:
            if order.get(n.importance, 99) < order.get(best.importance, 99):
                best = n

        return best
